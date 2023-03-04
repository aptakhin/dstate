from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
import threading
from typing import Any, ContextManager, Optional, TypeVar


class StateMachineData(object):
    def __init__(self, state: str) -> None:
        self.state = state


class DState(object):
    def __init__(self, state, save_here):
        self.state = state
        self.save_here = save_here

    def make_state_data(self) -> StateMachineData:
        return StateMachineData(state=self.state)

    def __setattr__(self, name: str, value: Any) -> None:
        print('State machine change', name, value)
        object.__setattr__(self, name, value)

        if hasattr(self, 'save_here') and self.save_here is not None:
            self.save_here(self)


MType = TypeVar('MType')


@dataclass
class DReference:
    cls: MType
    ref: dict[str, Any]


class DataContainer(object):
    def __init__(self) -> None:
        pass

    def encode():
        pass

    def decode():
        pass


class StatePersister(ABC):
    @abstractmethod
    def load(self, default_state: str) -> StateMachineData:
        pass

    @abstractmethod
    def save(self, state: StateMachineData) -> None:
        pass


class InMemoryPersister(StatePersister):
    def __init__(self, obj: dict[str, Any], key: str) -> None:
        self._obj = obj
        self.key = key

    def load(self, default_state: str) -> StateMachineData:
        return StateMachineData(
            state=self._obj.get(self.key, {}).get('state', default_state)
        )

    def save(self, state: StateMachineData) -> None:
        self._obj.setdefault(self.key, {})
        self._obj[self.key]['state'] = state.state


class PersisterCreator(object):
    @abstractmethod
    def get_or_create(self, machine_cls, ref) -> StatePersister:
        pass


class InMemoryPersisterCreators(PersisterCreator):
    def __init__(self) -> None:
        self._obj: dict[str, Any] = {}

    def get_or_create(self, machine_cls, ref) -> InMemoryPersister:
        return InMemoryPersister(self._obj, key=ref['id'])


class WorldPersisterCreators(object):
    def __init__(self) -> None:
        self._creators: dict[str, PersisterCreator] = {}

    def register(self, name: str, persister_creator: PersisterCreator) -> None:
        self._creators[name] = persister_creator

    def get_creator(self, name: str) -> PersisterCreator:
        return self._creators[name]

    def get_or_create_persister(self, name, machine_cls, ref) -> StatePersister:
        creator = self.get_creator(name)
        return creator.get_or_create(machine_cls, ref)


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


class NoLock(Lock):
    def lock(
        self,
        lock_time: timedelta,
        timeout: timedelta,
    ) -> None:
        pass

    def unlock(self) -> None:
        pass


class InMemoryLock(Lock):
    def __init__(self):
        self._lock = threading.Lock()

    def lock(
        self,
        lock_time: timedelta,
        timeout: timedelta,
    ):
        self._lock.acquire(blocking=True, timeout=timeout.total_seconds())

    def unlock(self):
        self._lock.release()


class LockCreator(object):
    @abstractmethod
    def get_or_create(self, machine_cls, ref) -> Lock:
        pass


class InMemoryLockCreator(LockCreator):
    def __init__(self):
        self._locks: dict[int, InMemoryLock] = {}

    def get_or_create(self, machine_cls, ref) -> Lock:
        store_id = ref['id']
        self._locks.setdefault(store_id, InMemoryLock())
        return self._locks[store_id]


class NoLockCreator(LockCreator):
    def __init__(self):
        self._no_lock = NoLock()

    def get_or_create(self, machine_cls, ref) -> Lock:
        return self._no_lock


class WorldLockCreators(object):
    def __init__(self) -> None:
        self._creators: dict[str, LockCreator] = {}

    def register(self, name: str, lock_creator: LockCreator) -> None:
        self._creators[name] = lock_creator

    def get_creator(self, name: str) -> LockCreator:
        return self._creators[name]

    def get_or_create_lock(self, lock_name, machine_cls, ref) -> Lock:
        creator = self.get_creator(lock_name)
        return creator.get_or_create(machine_cls, ref)


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
        self._persister_creators.register('default', InMemoryPersisterCreators())

        self._in_memory_obj = {}

        self._lock_creators: WorldLockCreators = lock_creators or WorldLockCreators()
        self._lock_creators.register('lock', InMemoryLockCreator())
        self._lock_creators.register('none', NoLockCreator())

    @contextmanager
    def lock_and_write_machine(
        self,
        machine_cls: MType,
        ref: dict[str, Any],
        initial: Optional[str] = None,
        lock_name: str = 'lock',
        lock_creators: Optional[WorldLockCreators] = None,
        persister_name: str = 'default',
        persister_creators: Optional[WorldPersisterCreators] = None,
    ) -> ContextManager[MType]:
        lock_creators = lock_creators or self._lock_creators
        lock = lock_creators.get_or_create_lock(lock_name, machine_cls, ref)
        lock.lock(timeout=timedelta(seconds=3), lock_time=timedelta(seconds=3))

        persister_creators = persister_creators or self._persister_creators
        persister_creator = persister_creators.get_creator(persister_name)
        persister = persister_creator.get_or_create(machine_cls, ref)
        state_data = persister.load(initial)

        def notify(dstate, persister):
            state_data = dstate.make_state_data()
            print('Want save', state_data.__dict__)
            persister.save(state_data)

        state = DState(
            state=state_data.state,
            save_here=partial(notify, persister=persister),
        )
        machine = machine_cls(state)
        try:
            yield machine
        finally:
            print('MF', self._in_memory_obj)
            lock.unlock()

    def _get_persister(
        self,
        machine_cls: MType,
        ref: dict[str, Any],
    ) -> StatePersister:
        return InMemoryPersister(self._in_memory_obj)
