from flask import Flask, render_template, request, jsonify
from sqlalchemy.pool import StaticPool

from data.datastores.sqlite import SqliteDatastore
from data.engine.sql_alchemy_engine import SqlAlchemyEngine

# create the flask app
app = Flask(__name__)
db = "cells"

# routes home url /
@app.route('/')
def home():
    return render_template('home.html')

# frequencies per sample
@app.route('/api/frequency', methods=['POST'])
def calc_frequency():
    data = request.get_json()
    sample = data.get('sample')

    # if not sample:
    #     return jsonify({"error": "Missing sample id"}), 400

    # pagination params, with sane defaults/bounds
    page = int(data.get('page') or 1)
    page_size = int(data.get('page_size') or 10)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    filter = f"WHERE sample = :sample" if sample else ""
    bindings = {"sample": sample} if sample else {}

    # shared expressions so the count query and the paginated data query
    # both operate on the same computed frequency rows
    ctes = """
    WITH base AS (
        SELECT sample,
               COALESCE(b_cells, 0) AS b_cells,
               COALESCE(cd8_t_cells, 0) AS cd8_t_cells,
               COALESCE(cd4_t_cells, 0) AS cd4_t_cells,
               COALESCE(nk_cells, 0) AS nk_cells,
               COALESCE(monocytes, 0) AS monocytes,
               (COALESCE(b_cells, 0) + COALESCE(cd8_t_cells, 0) + COALESCE(cd4_t_cells, 0) + COALESCE(nk_cells, 0) + COALESCE(monocytes, 0)) AS total_count
        FROM cell_counts
    ),
    freq AS (
        SELECT sample, total_count,
           b_cells, ROUND(b_cells / total_count * 100, 3) AS b_cell_freq,
           cd8_t_cells, ROUND(cd8_t_cells / total_count * 100, 3) AS cd8_t_cells_freq,
           cd4_t_cells, ROUND(cd4_t_cells / total_count * 100, 3) AS cd4_t_cells_freq,
           nk_cells, ROUND(nk_cells / total_count * 100, 3) AS nk_cells_freq,
           monocytes, ROUND(monocytes / total_count * 100, 3) AS monocytes_freq
        FROM base
    )
    """

    # gets total count used for pagination size
    count_query = f"""
    {ctes}
    SELECT COUNT(*) AS total FROM freq {filter};
    """

    # the actual data
    data_query = f"""
    {ctes}
    SELECT * FROM freq
    {filter}
    ORDER BY sample
    LIMIT :limit OFFSET :offset;
    """

    count_result = engine.execute_query(db, count_query, bindings)
    total = [dict(row._mapping) for row in count_result][0]['total']

    data_bindings = dict(bindings)
    data_bindings.update({"limit": page_size, "offset": offset})
    result = engine.execute_query(db, data_query, data_bindings)
    rows = [dict(row._mapping) for row in result]

    total_pages = max((total + page_size - 1) // page_size, 1)

    response = {
        "message": rows,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    }

    return jsonify(response), 201


if __name__ == '__main__':

    # start the db engine
    pool = StaticPool
    ds = SqliteDatastore()

    global engine
    engine = SqlAlchemyEngine(pool, ds, db)

    app.run()