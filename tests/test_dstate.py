import pytest

import dstate
from statemachine import State, StateMachine

from tests.conftest import LockType


class TrafficLightMachine(StateMachine):
    """A traffic light machine."""

    green = State('Green', initial=True)
    yellow = State('Yellow')
    red = State('Red')

    cycle = green.to(yellow) | yellow.to(red) | red.to(green)

    def on_cycle(self, event_data):
        return '{0}: {1} -> {2}'.format(
            event_data.event,
            event_data.source.id,
            event_data.target.id,
        )


def test_persistance__base(my_world: dstate.World):
    with my_world.lock_and_write_machine(
        TrafficLightMachine,
        {'id': 1},
    ) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()


def test_persistance__two_writes(my_world: dstate.World):
    with my_world.lock_and_write_machine(
        TrafficLightMachine,
        {'id': 1},
    ) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()
        assert light_machine.current_state.id == 'yellow'

    with my_world.lock_and_write_machine(
        TrafficLightMachine,
        {'id': 1},
    ) as light_machine:
        assert light_machine.current_state.id == 'yellow'
        light_machine.cycle()
        assert light_machine.current_state.id == 'red'


def test_persistance__read_exception_on_write(my_world: dstate.World):
    with my_world.lock_and_write_machine(
        TrafficLightMachine,
        {'id': 1},
        lock_name=LockType.none,
    ) as light_machine:
        assert light_machine.current_state.id == 'green'
        with pytest.raises(dstate.NotAllowedStateMachineChange):
            light_machine.cycle()
