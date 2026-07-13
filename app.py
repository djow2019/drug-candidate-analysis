from flask import Flask, render_template, request, jsonify
from sqlalchemy.pool import StaticPool

from data.datastores.sqlite import SqliteDatastore
from data.engine.sql_alchemy_engine import SqlAlchemyEngine
from tests.t_test import T_Test

# create the flask app
app = Flask(__name__)
db = "cells"

# shared CTE that computes cell counts + relative frequencies per sample,
# joined against samples and subjects so callers can filter on columns from
# any of the three tables. {filter} is substituted with a WHERE clause (or "").
FREQUENCY_CTE = """
WITH base AS (
    SELECT cc.sample,
           COALESCE(cc.b_cells, 0) AS b_cells,
           COALESCE(cc.cd8_t_cells, 0) AS cd8_t_cells,
           COALESCE(cc.cd4_t_cells, 0) AS cd4_t_cells,
           COALESCE(cc.nk_cells, 0) AS nk_cells,
           COALESCE(cc.monocytes, 0) AS monocytes,
           (COALESCE(cc.b_cells, 0) + COALESCE(cc.cd8_t_cells, 0) + COALESCE(cc.cd4_t_cells, 0) + COALESCE(cc.nk_cells, 0) + COALESCE(cc.monocytes, 0)) AS total_count
    FROM cell_counts cc
    LEFT JOIN samples s ON s.id = cc.sample
    LEFT JOIN subjects sub ON sub.id = s.subject
    {filter}
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

# maps request field name -> qualified SQL column
# treatment/response now live on subjects; type stays on samples
FILTER_COLUMNS = {
    "sample": "cc.sample",
    "treatment": "sub.treatment",
    "response": "sub.response",
    "type": "s.type",
}


def build_filter(criteria: dict):
    """Build a 'WHERE col = :key AND ...' clause + bindings from a dict of
    field -> value, skipping any falsy values. Only known fields (see
    FILTER_COLUMNS) are considered."""
    conditions = []
    bindings = {}

    for field, value in criteria.items():
        if not value:
            continue
        column = FILTER_COLUMNS[field]
        conditions.append(f"{column} = :{field}")
        bindings[field] = value

    filter_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return filter_sql, bindings


def fetch_rows(query: str, bindings: dict):
    """Run a query and convert the result into a list of plain dicts."""
    result = engine.execute_query(db, query, bindings)
    return [dict(row._mapping) for row in result]


def fetch_distinct_values(table: str, column: str):
    """Return a sorted list of distinct non-null values for a column."""
    query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column};"
    rows = fetch_rows(query, {})
    return [row[column] for row in rows]


# fixed cohort used by the /api/analysis endpoints below: baseline (day 0)
# PBMC samples from melanoma subjects on the miraclib treatment
BASELINE_COHORT_WHERE = """
    WHERE s.type = 'PBMC'
      AND s.time_from_treatment_start = 0
      AND sub.condition = 'melanoma'
      AND sub.treatment = 'miraclib'
"""


def baseline_cohort_query(select_clause: str, group_by: str = None):
    """Build a query over the fixed baseline cohort (see BASELINE_COHORT_WHERE),
    optionally grouped by a column."""
    query = f"""
    SELECT {select_clause}
    FROM samples s
    JOIN subjects sub ON sub.id = s.subject
    {BASELINE_COHORT_WHERE}
    """
    if group_by:
        query += f" GROUP BY {group_by} ORDER BY {group_by}"
    return query + ";"


# routes home url /
@app.route('/')
def home():
    return render_template('home.html')


# frequencies per sample, optionally filtered to one sample, paginated
@app.route('/api/frequency', methods=['POST'])
def calc_frequency():
    data = request.get_json()
    sample = data.get('sample')

    # pagination params, with sane defaults/bounds
    page = max(int(data.get('page') or 1), 1)
    page_size = min(max(int(data.get('page_size') or 10), 1), 100)
    offset = (page - 1) * page_size

    filter_sql, bindings = build_filter({"sample": sample})
    cte = FREQUENCY_CTE.format(filter=filter_sql)

    count_query = f"{cte} SELECT COUNT(*) AS total FROM freq;"
    data_query = f"{cte} SELECT * FROM freq ORDER BY sample LIMIT :limit OFFSET :offset;"

    total = fetch_rows(count_query, bindings)[0]['total']

    data_bindings = dict(bindings, limit=page_size, offset=offset)
    rows = fetch_rows(data_query, data_bindings)

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


# frequencies filtered by treatment / response (from subjects) and type (from samples)
@app.route('/api/frequency/filter', methods=['POST'])
def calc_frequency_filtered():
    data = request.get_json()

    filter_sql, bindings = build_filter({
        "treatment": data.get('treatment'),
        "response": data.get('response'),
        "type": data.get('type'),
    })
    cte = FREQUENCY_CTE.format(filter=filter_sql)

    query = f"{cte} SELECT * FROM freq ORDER BY sample;"
    rows = fetch_rows(query, bindings)

    return jsonify({"message": rows}), 201


# unique treatment values from the subjects table
@app.route('/api/treatments', methods=['GET'])
def get_treatments():
    treatments = fetch_distinct_values('subjects', 'treatment')
    return jsonify({"message": treatments}), 200


# unique type values from the samples table
@app.route('/api/types', methods=['GET'])
def get_types():
    types = fetch_distinct_values('samples', 'type')
    return jsonify({"message": types}), 200


# 1. count of baseline (day 0) PBMC samples from melanoma subjects on miraclib
@app.route('/api/analysis/pbmc-baseline/count', methods=['GET'])
def pbmc_baseline_count():
    query = baseline_cohort_query("COUNT(*) AS count")
    result = fetch_rows(query, {})[0]
    return jsonify({"message": result}), 200


# 2. same cohort, broken down by project
@app.route('/api/analysis/pbmc-baseline/count-by-project', methods=['GET'])
def pbmc_baseline_count_by_project():
    query = baseline_cohort_query("s.project AS project, COUNT(*) AS count", group_by="s.project")
    rows = fetch_rows(query, {})
    return jsonify({"message": rows}), 200


# 3. same cohort, subjects grouped by response (yes/no)
@app.route('/api/analysis/pbmc-baseline/response-counts', methods=['GET'])
def pbmc_baseline_response_counts():
    query = baseline_cohort_query(
        "sub.response AS response, COUNT(DISTINCT sub.id) AS count",
        group_by="sub.response"
    )
    rows = fetch_rows(query, {})
    return jsonify({"message": rows}), 200


# 4. same cohort, subjects grouped by sex (M/F)
@app.route('/api/analysis/pbmc-baseline/sex-counts', methods=['GET'])
def pbmc_baseline_sex_counts():
    query = baseline_cohort_query(
        "sub.sex AS sex, COUNT(DISTINCT sub.id) AS count",
        group_by="sub.sex"
    )
    rows = fetch_rows(query, {})
    return jsonify({"message": rows}), 200

# 5. same cohort, melanoma males, average B-Cells for responders at t=0
@app.route('/api/analysis/pbmc-baseline/b-counts', methods=['GET'])
def pbmc_baseline_avg_b_counts():
    query = """
    SELECT ROUND(AVG(b_cells), 2) AS avg_b_cells_in_beginning
    FROM cell_counts
    JOIN samples s ON sample = s.id
    JOIN subjects sub ON s.subject = sub.id
    WHERE s.time_from_treatment_start = 0 AND s.type = "PBMC" AND sub.condition = "melanoma" AND sub.sex = "M" AND sub.response = "yes"
    """
    rows = fetch_rows(query, {})
    return jsonify({"message": rows}), 200


# runs a t-test on two groups of sample values
@app.route('/api/statistics/ttest', methods=['POST'])
def ttest():
    data = request.get_json()
    group_a = data.get('group_a')
    group_b = data.get('group_b')
    metadata = data.get('metadata') or {}

    if not isinstance(group_a, list) or not isinstance(group_b, list):
        return jsonify({"error": "group_a and group_b must both be lists of numbers."}), 400

    if len(group_a) < 2 or len(group_b) < 2:
        return jsonify({"error": "Each group needs at least 2 samples to run a t-test."}), 400

    try:
        result = T_Test().test_samples(group_a, group_b, metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": result}), 201


if __name__ == '__main__':

    # start the db engine
    pool = StaticPool
    ds = SqliteDatastore()

    global engine
    engine = SqlAlchemyEngine(pool, ds, db)

    app.run()