from contextlib import ExitStack
from datetime import timedelta
from dstate.driver.dummy import InMemoryLockCreator, InMemoryPersisterCreator
import pytest

import dstate
from statemachine import State, StateMachine

from smoke_tests.conftest import LockType


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


def test_persistance__base(root_context: dstate.Context):
    with root_context.acquire_machine(
        TrafficLightMachine,
        {'id': 1},
    ) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()


def test_persistance__two_writes(root_context: dstate.Context):
    with root_context.acquire_machine(
        TrafficLightMachine,
        {'id': 1},
    ) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()
        assert light_machine.current_state.id == 'yellow'

    with root_context.acquire_machine(
        TrafficLightMachine,
        {'id': 1},
    ) as light_machine:
        assert light_machine.current_state.id == 'yellow'
        light_machine.cycle()
        assert light_machine.current_state.id == 'red'


def test_persistance__read_exception_on_write(root_context: dstate.Context):
    with root_context.acquire_machine(
        TrafficLightMachine,
        {'id': 1},
        lock_name=LockType.none,
    ) as light_machine:
        assert light_machine.current_state.id == 'green'
        with pytest.raises(dstate.NotAllowedStateMachineChange):
            light_machine.cycle()


def test_new_context(root_context: dstate.Context):
    persister_creator = InMemoryPersisterCreator()

    context = root_context.make_child_context(
        name='context_name',
        # lock_name=LockType.lock,
        # persister_name='default',
        # or
        # lock=InMemoryLock(),
        # lock_creator=InMemoryLockCreator(),
        # persister_creator=persister_creator,
        # lock_timeout=timedelta(seconds=3),
        # lock_time=timedelta(seconds=5),
        lock_time=timedelta(seconds=3),
        lock_timeout=timedelta(seconds=3),
    )

    persister = persister_creator.get_or_create(dstate.Reference(TrafficLightMachine, {'id': 1}))
    m1 = persister.load(None)
    m1.attrs = {
        'neigbour_ids': [2, 3],
    }
    persister.save(m1)

    persister = persister_creator.get_or_create(dstate.Reference(TrafficLightMachine, {'id': 2}))
    m2 = persister.load(None)
    persister.save(m2)

    persister = persister_creator.get_or_create(dstate.Reference(TrafficLightMachine, {'id': 3}))
    m3 = persister.load(None)
    persister.save(m3)


    # with context.acquire_state(TrafficLightMachine, {'id': 1}) as state:
    #     light_machine = TrafficLightMachine(state)
    #     assert light_machine.current_state.id == 'yellow'
    #     light_machine.cycle()
    #     assert light_machine.current_state.id == 'red'

    with context.acquire_machine(TrafficLightMachine, {'id': 1}) as light_machine:
        assert light_machine.current_state.id == 'green'
        light_machine.cycle()
        assert light_machine.current_state.id == 'yellow'

        # with context.acquire_machine(TrafficLightMachine, {'id': light_machine['neigbour']}) as light_machine_neighboar_1:
        #     with context.acquire_machine(TrafficLightMachine, {'id': light_machine['neigbour']}) as light_machine_neighboar_2:
        #         light_machine_neigbour_1.cycle()
        #         light_machine_neigbour_2.cycle()

        neigbour_ids = light_machine.model.data['neigbour_ids']
        with ExitStack() as stack:
            neigbour_machines = [stack.enter_context(context.acquire_machine(TrafficLightMachine, {'id': neigbour_id})) for neigbour_id in neigbour_ids]

            for machine in neigbour_machines:
                machine.cycle()
                assert machine.current_state.id == 'green'
                machine.cycle()
                assert machine.current_state.id == 'yellow'
