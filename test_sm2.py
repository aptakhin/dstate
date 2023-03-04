# from typing import Self
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
import threading
import time
from typing import Any, ContextManager, Optional, TypeVar, Union
from statemachine import State, StateMachine


class TrafficLightMachine(StateMachine):
    "A traffic light machine"
    green = State("Green", initial=True)
    yellow = State("Yellow")
    red = State("Red")

    cycle = green.to(yellow) | yellow.to(red) | red.to(green)

    def on_cycle(self, event_data):
        return f"Running {event_data.event} from {event_data.source.id} to {event_data.target.id}"


class Meta(type):
    def __getattribute__(*args):
        print("Metaclass getattribute invoked")
        return type.__getattribute__(*args)


# class TrafficLightMachine2(StateMachine, metaclass=Meta):
#     "A traffic light machine"
#     green = State("Green", initial=True)
#     yellow = State("Yellow")
#     red = State("Red")

#     cycle = green.to(yellow) | yellow.to(red) | red.to(green)

#     def on_cycle(self, event_data):
#         return f"Running {event_data.event} from {event_data.source.id} to {event_data.target.id}"


def dstate_new(cls, *args, **kwargs):
    print('A', cls, args, kwargs)
    x = object.__new__(cls)
    return x


def dstate_init(instance, *args, **kwargs):
    print('B', type(instance), args, kwargs)
    dstate_reference = kwargs.pop('dstate_ref')
    print('ZZ', id(instance), args, kwargs)
    instance.__dstate_old_init__(*args, **kwargs)
    instance._dstate_ref = dstate_reference
    instance._dstate_lock = None

    if hasattr(instance, '__getattr__'):
        print('Ccatr')
        instance.__dstate_old_getattr = instance.__getattr__
    instance.__getattr__ = dstate_getattr

    if hasattr(instance, '__getattribute__'):
        print('Ccatrib')
        instance.__dstate_old_getattribute = instance.__getattribute__
    instance.__getattribute__ = dstate_getattribute

    if hasattr(instance, '__call__'):
        print('Cca')
        instance.__dstate_old_call = instance.__call__
    instance.__call__ = dstate_call

    if hasattr(instance, '__get__'):
        instance.__dstate_old_get = instance.__get__
    instance.__get__ = dstate_get

    # if hasattr(instance, '__call__'):
    # obj.__dstate_old_call = obj.__call__
    # obj.__call__ = dstate_call
    print('ZZc')


def dstate_getattr(instance, *args, **kwargs):
    print('C', type(instance), instance.__getattr__, instance._dstate_old_getattr, args, kwargs)
    return instance.__dstate_old_getattr(*args, **kwargs)

def dstate_getattribute(instance, *args, **kwargs):
    print('D', type(instance), instance.__getattr__, instance._dstate_old_getattr, args, kwargs)
    return instance.__dstate_old_getattribute(*args, **kwargs)

def dstate_call(instance, *args, **kwargs):
    print('E', type(instance), instance.__getattr__, instance.__dstate_old_call, args, kwargs)
    return instance.__dstate_old_call(*args, **kwargs)

def dstate_get(instance, *args, **kwargs):
    print('F', type(instance), instance.__getattr__, instance.__dstate_old_call, args, kwargs)
    return instance.__dstate_old_get(*args, **kwargs)

# class DSyncLock(object):
#     def __init__(self, dreference: 'DReference', impl) -> None:
#         self.reference = dreference
#         self._impl = impl

#     def enter(self):
#         pass

#     def release(self):
#         pass


def dclass_install(cls):
    cls.__dstate_old_new__ = cls.__new__
    cls.__new__ = dstate_new

    cls.__dstate_old_init__ = cls.__init__
    cls.__init__ = dstate_init


def dclass_uninstall(cls):
    cls.__new__ = cls.__dstate_old_new__
    cls.__init__ = cls.__dstate_old_init__


@contextmanager
def dclass(cls) ->  ContextManager:
    dclass_install(cls)
    try:
        yield
    finally:
        dclass_uninstall(cls)


# TrafficLightMachine.__new__ = dstate_new
# TrafficLightMachine.__init__ = dstate_init
# # TrafficLightMachine.__getattr__ = dstate_getattr

# x = TrafficLightMachine(dstate_ref={'c': 3})

# x.cycle()

# with lock(x):
#     pass


class StateMachineData(object):
    def __init__(self, state: str) -> None:
        self.state = state


class DState(object):
    def __init__(self, state, save_here):
        self.state = state
        self.save_here = save_here

    # @property
    # def state(self):
    #     return self._state

    # @state.setter
    # def set_state(self, state: str) -> None:
    #     print('Ch', state)
    #     self._state = state

    def make_state_data(self) -> StateMachineData:
        return StateMachineData(state=self.state)

    def __setattr__(self, name: str, value: Any) -> None:
        print('Ch2', name, value)
        object.__setattr__(self, name, value)

        if hasattr(self, 'save_here') and self.save_here is not None:
            self.save_here(self)
        # if name == 'state':
        #     setattr(self, 'state', value)
        # else:
        #     super().__setattr__(self, name, value)



MType = TypeVar('MType')
# def make(machine_cls: MType, ref: dict[str, Any], initial: Optional[str] = None) -> MType:
#     zs = DState(state=initial)

class DataContainer(object):
    def __init__(self) -> None:
        pass

    def encode():
        pass

    def decode():
        pass


class StatePersister(ABC):
    @abstractmethod
    def load(self, ref: dict[str, Any], default_state: str) -> StateMachineData:
        pass

    @abstractmethod
    def save(self, ref: dict[str, Any], state: StateMachineData) -> None:
        pass


class InMemoryPersister(StatePersister):
    def __init__(self, obj: dict[str, Any]) -> None:
        self._obj = obj

    def load(self, ref: dict[str, Any], default_state: str) -> StateMachineData:
        return StateMachineData(state=self._obj.get(ref['id'], {}).get('state', default_state))

    def save(self, ref: dict[str, Any], state: StateMachineData) -> None:
        self._obj.setdefault(ref['id'], {})
        self._obj[ref['id']]['state'] = state.state


@dataclass
class InMemoryLockEntry(object):
    locked_by: int
    locked_till: datetime

class InMemoryLock(object):
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


class Lock(ABC):
    @abstractmethod
    def lock(
        self,
        id_: int,
        lock_time: timedelta,
        timeout: timedelta,
    ) -> None:
        pass

    @abstractmethod
    def unlock(self, id_: int) -> None:
        pass


class LockCreator(object):
    def create(self, machine_cls, ref) -> Lock:
        pass


class InMemoryLockCreator(LockCreator):
    def __init__(self):
        self._locks: dict[int, InMemoryLock] = {}

    def get_or_create(self, machine_cls, ref) -> Lock:
        store_id = ref['id']
        self._locks.setdefault(store_id, InMemoryLock())
        return self._locks[store_id]


class WorldLockCreators(object):
    def __init__(self) -> None:
        self._creators: dict[str, LockCreator] = {}

    def register(self, name: str, lock_creator: LockCreator) -> None:
        self._creators[name] = lock_creator

    # def create(self, name: str) -> LockCreator:
    #     return self._creators[name]

    def get_or_create_lock(self, lock_name, machine_cls, ref) -> Lock:
        creator = self._creators[lock_name]
        return creator.get_or_create(machine_cls, ref)



class World(object):
    # events, timers

    def __init__(
        self,
        lock_creator: Optional[WorldLockCreators]=None,
    ) -> None:
        self._state_machine_persisters = {}

        self._in_memory_obj = {}

        self._lock_creators: WorldLockCreators = lock_creator or WorldLockCreators()
        self._lock_creators.register('lock', InMemoryLockCreator())

        # self._contexts = {}
        # different locks support pg for row, or redis for row.

    def register_state_machine_persister(self, cls: Any, persister):
        pass

    def register_(self, cls: Any, persister):
        pass

    @contextmanager
    def lock_and_write_machine(
        self,
        machine_cls: MType,
        ref: dict[str, Any],
        initial: Optional[str] = None,
        lock_name: str = 'lock',
        lock_creator: Optional[WorldLockCreators] = None,
    ) -> ContextManager[MType]:
        # lock_creator_name = 'inmemory'
        lock_creators = lock_creator or self._lock_creators
        lock = lock_creators.get_or_create_lock(lock_name, machine_cls, ref)
        # self._lock_pool.lock(ref['id'], timeout=timedelta(seconds=3), lock_time=timedelta(seconds=3))
        lock.lock(timeout=timedelta(seconds=3), lock_time=timedelta(seconds=3))

        persister = self._get_persister(machine_cls, ref)
        state_data = persister.load(ref, initial)

        def notify(dstate, ref, persister):
            state_data = dstate.make_state_data()
            print('Want save', ref, state_data.__dict__)
            persister.save(ref, state_data)

        state = DState(state=state_data.state, save_here=partial(notify, ref=ref, persister=persister))
        # self._contexts[id(state)] = persister
        machine = machine_cls(state)
        try:
            yield machine
        finally:
            # del self._contexts[id(state)]
            print('MF', self._in_memory_obj)
            lock.unlock()

    @contextmanager
    def read_machine(self, machine_cls: MType, ref: dict[str, Any], initial: Optional[str] = None) -> ContextManager[MType]:
        persister = self._get_persister(machine_cls, ref)
        state_data = persister.load(ref, initial)

        state = DState(state=state_data.state, save_here=None)
        # self._contexts[id(state)] = persister
        machine = machine_cls(state)
        yield machine

    def _get_persister(
        self,
        machine_cls: MType,
        ref: dict[str, Any],
    ) -> StatePersister:
        return InMemoryPersister(self._in_memory_obj)



# @contextmanager
# def lock_and_write_machine(machine_cls: MType, ref: dict[str, Any], initial: Optional[str] = None, world: WorldState) -> ContextManager[MType]:
#     # lock()
#     StatePersistance(cls, ref)
#     state = DState(state=initial)
#     machine = machine_cls(state)
#     try:
#         yield machine
#     finally:
#         state.dispose()

# @contextmanager
# def read_machine(machine_cls: MType, ref: dict[str, Any], initial: Optional[str] = None) -> ContextManager[MType]:
#     state = DState(state=initial)
#     machine = machine_cls(state)
#     yield machine


def test_xxx():
    # with dclass(TrafficLightMachine):
    #     x = TrafficLightMachine(dstate_ref={'c': 3})
    #     x.cycle
    #     x.cycle()
    #     print(x, type(x), id(x))

    # y = TrafficLightMachine()
    # y.cycle()

    # zs = DState(state='red')
    # z = TrafficLightMachine(zs)
    # z.cycle()
    # print(z, zs)
    # z.cycle()
    # print(z, zs)
    # z.cycle()
    # print(z, zs)

    world = World()

    with world.lock_and_write_machine(TrafficLightMachine, {'id': 1}) as light_machine:
        light_machine.cycle()
        print(light_machine, light_machine.model)
        light_machine.cycle()
        print(light_machine, light_machine.model)
        light_machine.cycle()
        print(light_machine, light_machine.model)

    with world.lock_and_write_machine(TrafficLightMachine, {'id': 1}) as light_machine:
        print(light_machine, light_machine.model)
        light_machine.cycle()
        print(light_machine, light_machine.model)

    with world.read_machine(TrafficLightMachine, {'id': 2}) as light_machine:
        light_machine.cycle()
        print(light_machine, light_machine.model)

    assert False


# with dsm(TrafficLightMachine):
#     reference = {'light_id': 3434}
#     with TrafficLightMachine(reference=reference) as lm:
