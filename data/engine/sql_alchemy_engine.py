import os

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session

from data.engine.sql_engine import SqlEngine


class SqlAlchemyEngine(SqlEngine):

    def __init__(self, pool_class, ds, db):
        super().__init__(pool_class, ds)
        self.engines = {}
        self.db = db

        if db:
            self.create_db(db)

    def db_exists(self, db: str) -> bool:
        if db is None:
            db = self.db
        return os.path.exists(self.ds.connection_url(db))

    def create_db(self, db: str) -> bool:
        if db is None:
            db = self.db
        self.engines[db] = create_engine(
            self.ds.connection_url(db),
            poolclass=self.pool_class,
            connect_args={"check_same_thread": False}
        )

    def table_exists(self, db: str, table: str) -> bool:
        if db is None:
            db = self.db
        if self.engines[db] is None:
            self.create_db(db)

        # Create the inspector object
        return inspect(self.engines[db]).has_table(table)

    def create_table(self, db: str, table: str, metadata: dict) -> bool:
        if self.engines[db] is None:
            self.create_db(db)

        if "base" in metadata:
            metadata["base"].metadata.create_all(self.engines[db])

        elif "col_names" in metadata:
            col_names = metadata["col_names"]
            col_types = metadata["col_types"]
            col_constraints = metadata["col_constraints"]
            schema = ""
            for i in range(len(col_names)):
                schema += f"{col_names[i]} {col_types[i]} {col_constraints[i] if i < len(col_constraints) and col_constraints[i] is not None else ''}"
                if i < len(col_names) - 1:
                    schema += ","

            with self.engines[db].connect() as connection:
                connection.execute(text(f"CREATE TABLE IF NOT EXISTS {table} ({schema})"))

    def upsert(self, db:str, schema, data: list, primary_key: str):
        import importlib

        if self.engines[db] is None:
            self.create_db(db)

        insert = getattr(importlib.import_module(f"sqlalchemy.dialects.{self.ds.name()}"), "insert")
        stmt = insert(schema)

        conflict_set = {}
        for col in list(schema.__table__.columns.keys()):
            conflict_set[col] = stmt.excluded[col]

        stmt = stmt.on_conflict_do_update(index_elements=[primary_key], set_=conflict_set)
        with Session(self.engines[db]) as session:
            session.execute(stmt, data)
            session.commit()

    def execute_query(self, db: str, query: str, bindings: dict):
        if self.engines[db] is None:
            self.create_db(db)
        stmt = text(query)
        with self.engines[db].connect() as connection:
            result = connection.execute(stmt, bindings)
            return result

