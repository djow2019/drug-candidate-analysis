from abc import ABC, abstractmethod


class Datastore(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def connection_url(self, db):
        pass

    @abstractmethod
    def name(self):
        pass
