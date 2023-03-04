# from typing import Self
from contextlib import contextmanager
from typing import Any
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


class DStore(object):
    pass


class DReference(object):
    def __init__(self, state_machine_cls, key: dict[str, Any]):
        self.state_machine_cls = state_machine_cls
        self.key = key


class DLock(object):
    def __init__(self, dreference: DReference) -> None:
        self.reference = dreference

    async def enter(self):
        pass

    async def release(self):
        pass


class DSyncLock(object):
    def __init__(self, dreference: DReference, impl) -> None:
        self.reference = dreference
        self._impl = impl

    def enter(self):
        pass

    def release(self):
        pass


class DStateObserver(object):
    def __init__(self) -> None:
        self.dstore = ()


class DStateMachine(object):
    def __init__(self, reference: DReference) -> None:
        self.reference: DReference = reference
        self.state_machine_adapter: Any = None
        # self.

    @contextmanager
    def sync_lock(self) -> typing.ContextManager[DSyncLock]:
        lock_impl = self._get_lock_impl()
        lock = DSyncLock(self.reference, lock_impl)
        try:
            yield lock
        finally:
            lock.release()

    def _get_lock_impl(self):
        pass


class PyStateMachineFlyweight(StateMachine):
    def __init__(self) -> None:
        pass


class LogObserver(DStateObserver):
    def __init__(self, name) -> None:
        self.name = name

    def after_transition(self, event: str, source: State, target: State):
        print(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target: State, event: str):
        print(f"{self.name} enter: {target.id} from {event}")


def test_sm():
    sm = TrafficLightMachine()
    sm.add_observer(LogObserver("Paulista Avenue"))
    val = sm.cycle()
    print(val)

    dstate = PyStateMachineFlyweight(TrafficLightMachine, {'cross_id': 123})
    with dstate.sync_lock():
        dstate.cycle()

    with dstate.read_lock():
        dstate.cycle()  # Error.

    assert False
