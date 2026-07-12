from sqlalchemy.pool import StaticPool

from data.datastores.sqlite import SqliteDatastore
from data.engine.sql_alchemy_engine import SqlAlchemyEngine
from data.engine.sql_engine import SqlEngine
from data.schemas.cell_schema import Base


def load(file_name: str, engine: SqlEngine, db: str):
    if not engine.db_exists(db):
        engine.create_db(db)
    if not engine.table_exists(db, "subjects") or not engine.table_exists(db, "projects") \
            or not engine.table_exists(db, "samples") or not engine.table_exists(db, "cell_counts"):
        load_cell_schemas(engine, db)


def load_cell_schemas(engine: SqlEngine, db: str):
    engine.create_table(db, None, {"base": Base})


if __name__ == '__main__':
    # single thread pool
    pool = StaticPool
    ds = SqliteDatastore()
    engine = SqlAlchemyEngine(pool, ds, None)
    load("samples/cell-count.csv", engine, "cells")
