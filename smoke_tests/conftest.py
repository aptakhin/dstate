from datetime import timedelta
from typing import Iterator
import pytest

from logging.config import dictConfig

import dstate
from dstate.driver.dummy import (
    InMemoryLockCreator,
    InMemoryPersisterCreator,
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
def root_context() -> Iterator[dstate.Context]:
    context = dstate.Context(
        name='root',
        lock_time=timedelta(seconds=3),
        lock_timeout=timedelta(seconds=3),
        persister_name='default',
        lock_name=LockType.lock,
    )
    context.persister_creators.register(
        'default',
        InMemoryPersisterCreator(),
    )
    context.lock_creators.register(LockType.lock, InMemoryLockCreator())
    context.lock_creators.register(LockType.none, NoLockCreator())
    yield context
