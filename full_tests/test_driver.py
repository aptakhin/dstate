import dstate
from statemachine import State, StateMachine


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


def test_persistance__base(my_driver_world: dstate.World, pymongo_support):
    with my_driver_world.lock_and_write_machine(
        TrafficLightMachine,
        {'id': 1},
        lock_name='lock',
        persister_name='pymongo',
    ) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()
