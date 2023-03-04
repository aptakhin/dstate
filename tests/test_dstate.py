from dstate import World
from statemachine import State, StateMachine


class TrafficLightMachine(StateMachine):
    """A traffic light machine."""

    green = State('Green', initial=True)
    yellow = State('Yellow')
    red = State('Red')

    cycle = green.to(yellow) | yellow.to(red) | red.to(green)

    def on_cycle(self, event_data):
        return f'Running {event_data.event} from {event_data.source.id} to {event_data.target.id}'


def test_persistance__base():
    world = World()

    with world.lock_and_write_machine(TrafficLightMachine, {'id': 1}) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()


def test_persistance__two_writes():
    world = World()

    with world.lock_and_write_machine(TrafficLightMachine, {'id': 1}) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()
        assert light_machine.current_state.id == 'yellow'

    with world.lock_and_write_machine(TrafficLightMachine, {'id': 1}) as light_machine:
        assert light_machine.current_state.id == 'yellow'
        light_machine.cycle()
        assert light_machine.current_state.id == 'red'
