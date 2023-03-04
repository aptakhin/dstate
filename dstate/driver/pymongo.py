from dataclasses import dataclass
from typing import Any, Callable
from pymongo import MongoClient
from dstate import (
    PersisterCreator,
    Reference,
    StateMachineData,
    StatePersister,
)


@dataclass
class PyMongoStateMachineRoute:
    database: str
    collection: str
    ref_keys: list[str]


PyMongoMapperType = Callable[[Reference], PyMongoStateMachineRoute]


class PyMongoPersister(StatePersister):
    def __init__(
        self,
        client: MongoClient,
        ref: Reference,
        route: PyMongoStateMachineRoute,
    ) -> None:
        self.client = client
        self.ref = ref
        self.route = route

    def load(self, default_state: str) -> StateMachineData:
        entry_filter = self.make_filter(self.ref)
        document = (
            self.client.get_database(self.route.database)
            .get_collection(self.route.collection)
            .find_one(entry_filter)
        )
        return StateMachineData(
            state=document['state'] if document else default_state,
        )

    def save(self, patch: dict[str, Any]) -> None:
        entry_filter = self.make_filter(self.ref)
        (
            self.client.get_database(self.route.database)
            .get_collection(self.route.collection)
            .update_one(entry_filter, {'$set': patch}, upsert=True)
        )

    def make_filter(self, ref: Reference) -> dict[str, Any]:
        return ref.ref


class PyMongoOneClientPersisterCreators(PersisterCreator):
    def __init__(self, client: MongoClient, mapper: PyMongoMapperType) -> None:
        self.client = client
        self.mapper: PyMongoMapperType = mapper

    def get_or_create(self, ref: Reference) -> PyMongoPersister:
        route = self.mapper(ref)
        return PyMongoPersister(client=self.client, ref=ref, route=route)
