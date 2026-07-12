from abc import ABC, abstractmethod


class ConnectionPool(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass
