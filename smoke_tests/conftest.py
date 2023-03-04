from typing import Iterator
import pytest

from logging.config import dictConfig

import dstate
from dstate.driver.dummy import (
    InMemoryLockCreator,
    InMemoryPersisterCreators,
    NoLockCreator,
)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {'format': '[%(levelname)s] %(name)s: %(message)s'},
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {'handlers': ['stdout'], 'level': 'DEBUG', 'propagate': True},
    },
}


@pytest.fixture(autouse=True)
def log():
    dictConfig(LOGGING)
    yield


class LockType:
    none = 'none'
    lock = 'lock'


@pytest.fixture
def my_world() -> Iterator[dstate.World]:
    world = dstate.World()
    world.persister_creators.register(
        'default',
        InMemoryPersisterCreators(),
    )
    world.lock_creators.register(LockType.lock, InMemoryLockCreator())
    world.lock_creators.register(LockType.none, NoLockCreator())
    yield world
