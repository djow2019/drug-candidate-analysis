from abc import ABC, abstractmethod


class SqlEngine(ABC):

    def __init__(self, pool_class, ds):
        self.pool_class = pool_class
        self.ds = ds

    @abstractmethod
    def db_exists(self, db: str) -> bool:
        pass

    @abstractmethod
    def create_db(self, db: str) -> bool:
        pass

    @abstractmethod
    def table_exists(self, db: str, table: str) -> bool:
        pass

    @abstractmethod
    def create_table(self, db: str, table: str, metadata: dict) -> bool:
        pass

    @abstractmethod
    def upsert(self, db: str, table: str, cols: list, values: list, primary_key: str):
        pass
