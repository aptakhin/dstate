# from typing import Self
from contextlib import contextmanager
import typing
from statemachine import State, StateMachine


class TrafficLightMachine(StateMachine):
    "A traffic light machine"
    green = State("Green", initial=True)
    yellow = State("Yellow")
    red = State("Red")

    cycle = green.to(yellow) | yellow.to(red) | red.to(green)

    def on_cycle(self, event_data):
        return f"Running {event_data.event} from {event_data.source.id} to {event_data.target.id}"


def dstate_new(cls, *args, **kwargs):
    print('A', cls, args, kwargs)
    x = object.__new__(cls)
    return x

def dstate_init(instance, *args, **kwargs):
    print('B', type(instance), args, kwargs)
    # x = object.__new__(cls)
    dstate_reference = kwargs.pop('dstate_ref')
    print('ZZ', type(instance), args, kwargs)
    # cls.__init__(*args, **kwargs)
    instance._dstate_ref = dstate_reference

    if hasattr(instance, '__getattr__'):
        instance._dstate_old_getattr = instance.__getattr__
        instance.__getattr__ = dstate_getattr

    if hasattr(instance, '__getattribute__'):
        instance._dstate_old_getattribute = instance.__getattribute__
        instance.__getattribute__ = dstate_getattribute


    # instance.

    # return x


def dstate_getattr(instance, *args, **kwargs):
    print('C', type(instance), instance.__getattr__, instance._dstate_old_getattr, args, kwargs)
    return instance._dstate_old_getattr(*args, **kwargs)

def dstate_getattribute(instance, *args, **kwargs):
    print('D', type(instance), instance.__getattr__, instance._dstate_old_getattr, args, kwargs)
    return instance._dstate_old_getattribute(*args, **kwargs)

class DSyncLock(object):
    def __init__(self, dreference: 'DReference', impl) -> None:
        self.reference = dreference
        self._impl = impl

    def enter(self):
        pass

    def release(self):
        pass


@contextmanager
def lock(self) ->  typing.ContextManager[DSyncLock]:
    lock = DSyncLock(self.reference, lock_impl)
    try:
        yield lock
    finally:
        lock.release()


TrafficLightMachine.__new__ = dstate_new
TrafficLightMachine.__init__ = dstate_init
# TrafficLightMachine.__getattr__ = dstate_getattr

x = TrafficLightMachine(dstate_ref={'c': 3})

x.cycle()

with lock(x):
    pass

# with dsm(TrafficLightMachine):
#     reference = {'light_id': 3434}
#     with TrafficLightMachine(reference=reference) as lm:
