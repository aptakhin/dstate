from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
import logging
from typing import Any, ContextManager, Optional, TypeVar


logger = logging.getLogger(__name__)


MType = TypeVar('MType')


@dataclass
class Reference:
    cls: MType
    ref: dict[str, Any]


class CannotUpdateStateMachineChange(RuntimeError):
    def __init__(
        self,
        patch: dict[str, Any],
        ref: Reference,
        *args: object,
    ) -> None:
        self.patch = patch
        self.ref = ref
        super().__init__(*args)


class StateMachineLockExpired(CannotUpdateStateMachineChange):
    pass


class NotAllowedStateMachineChange(CannotUpdateStateMachineChange):
    pass


class StateMachineData(object):
    def __init__(self, state: str, attrs: Optional[dict[str, Any]] = None) -> None:
        self.state = state
        self.attrs: Optional[dict[str, Any]] = attrs


class State(object):
    def __init__(self, state, change_applier):
        self.state = state
        self.data = {}
        self.change_applier = change_applier
        self._state_machine_inited = False

    def make_state_data(self) -> StateMachineData:
        return StateMachineData(state=self.state)

    def __setattr__(self, name: str, value: Any) -> None:
        if (
            not hasattr(self, '_state_machine_inited')
            or not self._state_machine_inited
        ):
            object.__setattr__(self, name, value)
            return

        logger.debug('State machine want change %s %s', name, value)

        if self.change_applier is not None:
            self.change_applier(self.make_state_data())

        object.__setattr__(self, name, value)

        logger.debug('State machine made change %s %s', name, value)


class StatePersister(ABC):
    @abstractmethod
    def load(self, default_state: Optional[str]) -> StateMachineData:
        pass

    @abstractmethod
    def save(self, state: StateMachineData) -> None:
        pass


class PersisterCreator(object):
    @abstractmethod
    def get_or_create(self, machine_cls, ref) -> StatePersister:
        pass


class WorldPersisterCreators(object):
    def __init__(self) -> None:
        self._creators: dict[str, PersisterCreator] = {}

    def register(self, name: str, persister_creator: PersisterCreator) -> None:
        self._creators[name] = persister_creator

    def unregister(self, name: str) -> None:
        del self._creators[name]

    def is_registered(self, name: str) -> bool:
        return name in self._creators

    def get_creator(self, name: str) -> PersisterCreator:
        return self._creators[name]


class Lock(ABC):
    @abstractmethod
    def lock(
        self,
        lock_time: timedelta,
        timeout: timedelta,
    ) -> None:
        pass

    @abstractmethod
    def unlock(self) -> None:
        pass

    @abstractmethod
    def allow_change(self, patch: dict[str, Any]) -> bool:
        pass


class LockCreator(object):
    @abstractmethod
    def get_or_create(self, machine_cls, ref) -> Lock:
        pass


class WorldLockCreators(object):
    def __init__(self) -> None:
        self._creators: dict[str, LockCreator] = {}

    def register(self, name: str, lock_creator: LockCreator) -> None:
        self._creators[name] = lock_creator

    def is_registered(self, name: str) -> bool:
        return name in self._creators

    def get_creator(self, name: str) -> LockCreator:
        return self._creators[name]


class Context(object):
    def __init__(
        self,
        name: str,
        lock_creator: Optional[LockCreator] = None,
        lock_name: Optional[str] = None,
        lock_timeout: Optional[timedelta] = None,
        lock_time: Optional[timedelta] = None,
        lock_creators: Optional[WorldLockCreators] = None,
        persister_creator: Optional[LockCreator] = None,
        persister_name: Optional[str] = None,
        persister_creators: Optional[WorldPersisterCreators] = None,
        parent: Optional['Context'] = None,
    ) -> None:
        self._name = name
        if lock_creator is not None and lock_name is not None:
            raise ValueError('Only one of lock_creator or lock_name can be set. Got {lock_creator} and {lock_name}'.format(lock_creator=lock_creator, lock_name=lock_name))
        self._lock_creator = lock_creator
        self._lock_name = lock_name
        self._lock_timeout = lock_timeout
        self._lock_time = lock_time
        self._lock_creators: WorldLockCreators = (
            lock_creators or WorldLockCreators()
        )
        if persister_creator is not None and persister_name is not None:
            raise ValueError('Only one of persister_creator or persister_name can be set. Got {persister_creator} and {persister_name}'.format(persister_creator=persister_creator, persister_name=persister_name))
        self._persister_creator = persister_creator
        self._persister_name = persister_name
        self._persister_creators: WorldPersisterCreators = (
            persister_creators or WorldPersisterCreators()
        )

        self._parent = parent
        self._children: dict[str, Context] = {}

    def make_child_context(
        self,
        name: str,
        lock_name: Optional[str] = None,
        lock_timeout: Optional[timedelta] = None,
        lock_time: Optional[timedelta] = None,
        lock_creators: Optional[WorldLockCreators] = None,
        persister_name: Optional[str] = None,
        persister_creators: Optional[WorldPersisterCreators] = None,
    ):
        context = Context(
            name=name,
            lock_name=lock_name,
            lock_timeout=lock_timeout,
            lock_time=lock_time,
            lock_creators=lock_creators,
            persister_name=persister_name,
            persister_creators=persister_creators,
            parent=self,
        )
        self._children[name] = context
        return context

    @property
    def persister_creators(self) -> WorldPersisterCreators:
        return self._persister_creators

    @property
    def lock_creators(self) -> WorldLockCreators:
        return self._lock_creators

    @contextmanager
    def acquire_machine(
        self,
        machine_cls: MType,
        ref: dict[str, Any],
        *,
        lock_name: Optional[str] = None,
        lock_timeout: Optional[timedelta] = None,
        lock_time: Optional[timedelta] = None,
        persister_name: Optional[str] = None,
        initial: Optional[str] = None,
    ) -> ContextManager[MType]:
        ref = Reference(cls=machine_cls, ref=ref)

        lock = self._get_lock(
            ref=ref,
            lock_name=lock_name,
        )

        lock_timeout = self._get_lock_timeout(lock_timeout)
        if lock_timeout is None:
            raise ValueError('lock_timeout is not set for {ref}'.format(ref=ref))

        lock_time = self._get_lock_time(lock_time)
        if lock_time is None:
            raise ValueError('lock_time is not set for {ref}'.format(ref=ref))

        lock.lock(timeout=lock_timeout, lock_time=lock_time)

        persister = self._get_persister(
            ref=ref,
            persister_name=persister_name,
        )
        state_data = persister.load(initial)

        machine = self._create_machine(
            state_data=state_data,
            ref=ref,
            lock=lock,
            persister=persister,
        )

        try:
            yield machine
        finally:
            lock.unlock()

    def _get_persister(
        self,
        *,
        ref: Reference,
        persister_name: Optional[str] = None,
    ) -> StatePersister:
        persister_creator = self._find_persister_by_name_till_parents(persister_name)
        if persister_creator is None:
            raise ValueError('No persister is set for {ref=}!'.format(ref))

        return persister_creator.get_or_create(ref)

    def _find_persister_by_name_till_parents(
        self,
        persister_name: Optional[str],
    ) -> Optional[StatePersister]:
        find_persister_name = persister_name or self._persister_name
        if find_persister_name and self._persister_creators.is_registered(find_persister_name):
            return self._persister_creators.get_creator(find_persister_name)

        if self._parent:
            return self._parent._find_persister_by_name_till_parents(persister_name)

        return None

    def _get_lock(
        self,
        *,
        ref: Reference,
        lock_name: Optional[str],
    ) -> Lock:
        lock_creator = self._find_lock_by_name_till_parents(lock_name)
        if lock_creator is None:
            raise ValueError('No lock is set for {ref}!'.format(ref=ref))

        return lock_creator.get_or_create(ref)

    def _find_lock_by_name_till_parents(
        self,
        lock_name: Optional[str],
    ) -> Optional[Lock]:
        find_lock_name = lock_name or self._lock_name
        if self._lock_creators.is_registered(find_lock_name):
            return self._lock_creators.get_creator(find_lock_name)

        if self._parent:
            return self._parent._find_lock_by_name_till_parents(lock_name)

        return None

    def _get_lock_timeout(self, lock_timeout: Optional[timedelta] = None) -> Optional[timedelta]:
        check = [
            lambda: lock_timeout,
            lambda: self._lock_timeout,
            lambda: self._parent._get_lock_timeout() if self._parent else None,
        ]
        return next((item() for item in check if item() is not None), None)

    def _get_lock_time(self, lock_time: Optional[timedelta] = None) -> Optional[timedelta]:
        check = [
            lambda: lock_time,
            lambda: self._lock_time,
            lambda: self._parent._get_lock_time() if self._parent else None,
        ]
        return next((item() for item in check if item() is not None), None)

    def _create_machine(
        self,
        *,
        state_data: StateMachineData,
        ref: Reference,
        lock: Lock,
        persister: StatePersister,
    ) -> MType:
        def change_applier(
            new_state: StateMachineData,
            ref: Reference,
            lock: Lock,
            persister: StatePersister,
        ):
            if not lock.allow_change(new_state):
                raise NotAllowedStateMachineChange(new_state, ref)

            persister.save(new_state)

        state = State(
            state=state_data.state,
            change_applier=partial(
                change_applier,
                ref=ref,
                lock=lock,
                persister=persister,
            ),
        )

        state_machine = ref.cls(state)
        state._state_machine_inited = True
        return state_machine
