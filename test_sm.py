# from typing import Self
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


class DStateObserver(object):
    def __init__(self) -> None:
        self.dstore = ()


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
    assert False
