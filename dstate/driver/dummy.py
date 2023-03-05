from datetime import timedelta
import threading
from typing import Any, Optional
from dstate import (
    Lock,
    LockCreator,
    PersisterCreator,
    Reference,
    StateMachineData,
    StatePersister,
)


class InMemoryPersister(StatePersister):
    def __init__(self, obj: dict[str, Any], key: str) -> None:
        self._obj = obj
        self.key = key
        self.state_field = 'state'
        self.attrs_field = 'attrs'

    def load(self, default_state: Optional[str]) -> StateMachineData:
        key_obj = self._obj.get(self.key, {})
        return StateMachineData(
            state=key_obj.get(self.state_field, default_state),
            attrs=key_obj.get(self.attrs_field),
        )

    def save(self, data: StateMachineData) -> None:
        self._obj.setdefault(self.key, {})
        self._obj[self.key].update({
            self.state_field: data.state,
            self.attrs_field: data.attrs,
        })


class InMemoryPersisterCreator(PersisterCreator):
    def __init__(self) -> None:
        self._obj: dict[str, Any] = {}

    def get_or_create(self, ref: Reference) -> InMemoryPersister:
        return InMemoryPersister(self._obj, key=ref.ref['id'])


class NoLock(Lock):
    def lock(
        self,
        lock_time: timedelta,
        timeout: timedelta,
    ) -> None:
        pass

    def unlock(self) -> None:
        pass

    def allow_change(self, _: dict[str, Any]) -> bool:
        return False


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

    def allow_change(self, _: dict[str, Any]) -> bool:
        return True


class InMemoryLockCreator(LockCreator):
    def __init__(self):
        self._locks: dict[int, InMemoryLock] = {}

    def get_or_create(self, ref: Reference) -> Lock:
        store_id = ref.ref['id']
        self._locks.setdefault(store_id, InMemoryLock())
        return self._locks[store_id]


class NoLockCreator(LockCreator):
    def __init__(self):
        self._no_lock = NoLock()

    def get_or_create(self, ref: Reference) -> Lock:
        return self._no_lock
