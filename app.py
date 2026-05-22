from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder="static")
DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "ekiden.db"),
)

INITIAL_NAMES = [
    "Aaron", "Steph", "Chris", "Colm", "Neeraj", "Kerry",
    "Daniel", "Karolina", "Zenobia", "Isaac", "Eric", "Diana",
    "Rajesh", "Mike", "Sasa", "Thomas",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS assignments "
        "(name TEXT PRIMARY KEY, team INTEGER, leg TEXT)"
    )
    # Migration: add leg column if upgrading from old schema
    try:
        conn.execute("ALTER TABLE assignments ADD COLUMN leg TEXT")
    except Exception:
        pass
    for name in INITIAL_NAMES:
        conn.execute(
            "INSERT OR IGNORE INTO assignments (name, team, leg) VALUES (?, NULL, NULL)",
            (name,),
        )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/state")
def get_state():
    conn = get_db()
    rows = conn.execute(
        "SELECT name, team, leg FROM assignments ORDER BY name"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/assign", methods=["POST"])
def assign():
    data = request.get_json()
    name = data["name"]
    team = data.get("team")   # None = bench
    leg = data.get("leg")     # None = bench
    conn = get_db()
    conn.execute(
        "UPDATE assignments SET team = ?, leg = ? WHERE name = ?", (team, leg, name)
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


init_db()  # runs on import, so gunicorn workers also initialise the DB

if __name__ == "__main__":
    app.run(debug=True, port=5001)
