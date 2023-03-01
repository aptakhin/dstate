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
    # return x


TrafficLightMachine.__new__ = dstate_new
TrafficLightMachine.__init__ = dstate_init

x = TrafficLightMachine(dstate_ref={'c': 3})

# with dsm(TrafficLightMachine):
#     reference = {'light_id': 3434}
#     with TrafficLightMachine(reference=reference) as lm:


# # or

# dsm.install(TrafficLightMachine)
