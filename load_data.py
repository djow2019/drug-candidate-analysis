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
    load_cell_data(file_name, engine, db)


def load_cell_schemas(engine: SqlEngine, db: str):
    engine.create_table(db, None, {"base": Base})


def load_cell_data(file_name: str, engine: SqlEngine, db: str):
    import pandas as pd
    from data.schemas.cell_schema import Subjects, Projects, Samples, CellCounts

    chunk_size = 1000
    for chunk in pd.read_csv(file_name, chunksize=chunk_size):
        buf_subjects = []
        buf_projects = []
        buf_samples = []
        buf_counts = []
        for index, row in chunk.iterrows():
            buf_subjects.append({
                "id": row["subject"],
                "condition": row["condition"],
                "age": row["age"],
                "sex": row["sex"],
                "treatment": row["treatment"],
                "response": row["response"]
            })
            buf_projects.append({
                "id": row["project"]
            })
            buf_samples.append({
                "id": row["sample"],
                "project": row["project"],
                "subject": row["subject"],
                "type": row["sample_type"],
                "time_from_treatment_start": row["time_from_treatment_start"]
            })
            buf_counts.append({
                "sample": row["sample"],
                "b_cells": row["b_cell"],
                "cd8_t_cells": row["cd8_t_cell"],
                "cd4_t_cells": row["cd4_t_cell"],
                "nk_cells": row["nk_cell"],
                "monocytes": row["monocyte"]
            })

        engine.upsert(db, Subjects, buf_subjects, "id")
        engine.upsert(db, Projects, buf_projects, "id")
        engine.upsert(db, Samples, buf_samples, "id")
        engine.upsert(db, CellCounts, buf_counts, "sample")


if __name__ == '__main__':
    # single thread, single connection pool
    pool = StaticPool
    ds = SqliteDatastore()
    engine = SqlAlchemyEngine(pool, ds, None)
    load("samples/cell-count.csv", engine, "cells")
