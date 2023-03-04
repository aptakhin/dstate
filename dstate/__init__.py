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
    def __init__(self, state: str) -> None:
        self.state = state


class State(object):
    def __init__(self, state, change_applier):
        self.state = state
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
            self.change_applier({name: value})

        object.__setattr__(self, name, value)

        logger.debug('State machine made change %s %s', name, value)


class DataContainer(object):
    def __init__(self) -> None:
        pass

    def encode(self):
        pass

    def decode(self):
        pass


class StatePersister(ABC):
    @abstractmethod
    def load(self, default_state: str) -> StateMachineData:
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

    def get_or_create_persister(self, name, ref: Reference) -> StatePersister:
        creator = self.get_creator(name)
        return creator.get_or_create(ref)


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

    def get_creator(self, name: str) -> LockCreator:
        return self._creators[name]

    def get_or_create_lock(self, lock_name, ref: Reference) -> Lock:
        creator = self.get_creator(lock_name)
        return creator.get_or_create(ref)


class World(object):
    # events, timers

    def __init__(
        self,
        persister_creators: Optional[WorldPersisterCreators] = None,
        lock_creators: Optional[WorldLockCreators] = None,
    ) -> None:
        self._persister_creators: WorldPersisterCreators = (
            persister_creators or WorldPersisterCreators()
        )
        self._lock_creators: WorldLockCreators = (
            lock_creators or WorldLockCreators()
        )

    @property
    def persister_creators(self) -> WorldPersisterCreators:
        return self._persister_creators

    @property
    def lock_creators(self) -> WorldLockCreators:
        return self._lock_creators

    @contextmanager
    def lock_and_write_machine(
        self,
        machine_cls: MType,
        referancable: dict[str, Any],
        *,
        lock_name: str,
        persister_name: str,
        initial: Optional[str] = None,
        lock_creators: Optional[WorldLockCreators] = None,
        persister_creators: Optional[WorldPersisterCreators] = None,
    ) -> ContextManager[MType]:
        ref = Reference(cls=machine_cls, ref=referancable)

        lock = self._get_lock(
            ref=ref,
            lock_name=lock_name,
            lock_creators=lock_creators or self._lock_creators,
        )
        lock.lock(timeout=timedelta(seconds=3), lock_time=timedelta(seconds=3))

        persister = self._get_persister(
            ref=ref,
            persister_name=persister_name,
            persister_creators=persister_creators or self._persister_creators,
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
        persister_name: str,
        persister_creators: WorldPersisterCreators,
    ) -> StatePersister:
        persister_creators = persister_creators
        persister_creator = persister_creators.get_creator(persister_name)
        return persister_creator.get_or_create(ref)

    def _get_lock(
        self,
        *,
        ref: Reference,
        lock_name: str,
        lock_creators: WorldLockCreators,
    ) -> StatePersister:
        lock_creators = lock_creators or self._lock_creators
        return lock_creators.get_or_create_lock(lock_name, ref)

    def _create_machine(
        self,
        *,
        state_data: StateMachineData,
        ref: Reference,
        lock: Lock,
        persister: StatePersister,
    ) -> MType:
        def change_applier(
            patch: dict[str, Any],
            ref: Reference,
            lock: Lock,
            persister: StatePersister,
        ):
            if not lock.allow_change(patch):
                raise NotAllowedStateMachineChange(patch, ref)

            persister.save(patch)

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
