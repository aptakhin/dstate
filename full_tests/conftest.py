from typing import Iterator
from dstate.driver.dummy import (
    InMemoryLockCreator,
    InMemoryPersisterCreators,
    NoLockCreator,
)
from dstate.driver.pymongo import (
    PyMongoOneClientPersisterCreators,
    PyMongoStateMachineRoute,
)
from full_tests.settings import Settings
import pymongo
import pytest

from logging.config import dictConfig

import dstate


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


@pytest.fixture
def settings() -> Iterator[Settings]:
    yield Settings()


class LockType:
    none = 'none'
    lock = 'lock'


@pytest.fixture
def my_driver_world() -> Iterator[dstate.World]:
    world = dstate.World()
    world.persister_creators.register(
        'default',
        InMemoryPersisterCreators(),
    )
    world.lock_creators.register(LockType.lock, InMemoryLockCreator())
    world.lock_creators.register(LockType.none, NoLockCreator())
    yield world


@pytest.fixture
def pymongo_client(settings: Settings) -> Iterator[pymongo.MongoClient]:
    client = pymongo.MongoClient(settings.mongodb_dsn, connectTimeoutMS=3000)
    client.drop_database('test')

    yield client
    client.close()


@pytest.fixture
def pymongo_support(
    my_driver_world: dstate.World,
    pymongo_client: pymongo.MongoClient,
) -> Iterator[None]:
    name = 'pymongo'

    def mapper(ref: dstate.Reference) -> PyMongoStateMachineRoute:
        return PyMongoStateMachineRoute(
            database='test',
            collection=str(ref.cls.__name__),
            ref_keys=['id'],
        )

    my_driver_world.persister_creators.register(
        name,
        PyMongoOneClientPersisterCreators(pymongo_client, mapper=mapper),
    )

    yield

    my_driver_world.persister_creators.unregister(name)
