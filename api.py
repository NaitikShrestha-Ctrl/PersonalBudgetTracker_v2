"""
api.py
────────────────────────────────────────────────────────────
REST API for the Personal Budget Tracker.

Run this first:   python api.py
It listens on http://127.0.0.1:5000 and is the ONLY thing that
talks to the SQLite database (pbt.db). The Tkinter GUI
(PersonalBudgetTracker.py) is now just a client that calls
these endpoints over HTTP instead of touching a JSON file.

Endpoints
────────────────────────────────────────────────────────────
Auth
  POST   /api/auth                     {username, password_hash}

Expenses (CRUD)
  GET    /api/expenses                 ?user=<name>  (omit for all)
  POST   /api/expenses                 create
  GET    /api/expenses/<id>            read one
  PUT    /api/expenses/<id>            update one
  DELETE /api/expenses/<id>            delete one
  DELETE /api/expenses                 ?user=<name>  (bulk clear)

Category budgets (CRUD)
  GET    /api/budgets/category         ?user=<name>  (omit for all)
  PUT    /api/budgets/category         upsert {user, category, amount}
  DELETE /api/budgets/category         ?user=&category=

Monthly budgets (CRUD)
  GET    /api/budgets/monthly          ?user=<name>  (omit for all)
  PUT    /api/budgets/monthly          upsert {user, month, amount}
  DELETE /api/budgets/monthly          ?user=&month=
────────────────────────────────────────────────────────────
"""

from flask import Flask, request, jsonify
from database import get_conn, init_db

app = Flask(__name__)


def row_to_expense(r):
    return {
        "id": r["id"],
        "user": r["user"],
        "date": r["date"],
        "category": r["category"],
        "description": r["description"],
        "amount": r["amount"],
        "note": r["note"],
    }


# ════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════
@app.route("/api/auth", methods=["POST"])
def auth():
    """Login if the user exists, auto-signup if not (same behaviour as
    the original app). Also migrates any guest expenses to this user."""
    body = request.get_json(force=True) or {}
    username = (body.get("username") or "").strip()
    pw_hash = body.get("password_hash") or ""

    if not username or not pw_hash:
        return jsonify({"error": "username and password_hash required"}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()

    if row is None:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash),
        )
        status = "created"
    else:
        if row["password_hash"] != pw_hash:
            conn.close()
            return jsonify({"status": "error", "message": "Incorrect password"}), 401
        status = "login"

    # Migrate guest expenses to this account
    cur.execute(
        "UPDATE expenses SET user = ? WHERE user = '__guest__'", (username,)
    )
    migrated = cur.rowcount
    conn.commit()
    conn.close()

    return jsonify({"status": status, "username": username, "migrated": migrated})


# ════════════════════════════════════════════════════════
#  EXPENSES — CRUD
# ════════════════════════════════════════════════════════
@app.route("/api/expenses", methods=["GET"])
def list_expenses():
    user = request.args.get("user")
    conn = get_conn()
    cur = conn.cursor()
    if user:
        cur.execute("SELECT * FROM expenses WHERE user = ? ORDER BY date DESC", (user,))
    else:
        cur.execute("SELECT * FROM expenses ORDER BY date DESC")
    rows = [row_to_expense(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/expenses", methods=["POST"])
def create_expense():
    body = request.get_json(force=True) or {}
    required = ["user", "date", "category", "amount"]
    if not all(k in body and body[k] not in (None, "") for k in required):
        return jsonify({"error": f"required fields: {required}"}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO expenses (user, date, category, description, amount, note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            body["user"],
            body["date"],
            body["category"],
            body.get("description", ""),
            round(float(body["amount"]), 2),
            body.get("note", ""),
        ),
    )
    new_id = cur.lastrowid
    conn.commit()
    cur.execute("SELECT * FROM expenses WHERE id = ?", (new_id,))
    row = cur.fetchone()
    conn.close()
    return jsonify(row_to_expense(row)), 201


@app.route("/api/expenses/<int:eid>", methods=["GET"])
def get_expense(eid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE id = ?", (eid,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(row_to_expense(row))


@app.route("/api/expenses/<int:eid>", methods=["PUT"])
def update_expense(eid):
    body = request.get_json(force=True) or {}
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE id = ?", (eid,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "not found"}), 404

    amount = round(float(body.get("amount", row["amount"])), 2)
    category = body.get("category", row["category"])
    description = body.get("description", row["description"])
    exp_date = body.get("date", row["date"])
    note = body.get("note", row["note"])

    cur.execute(
        """UPDATE expenses SET amount=?, category=?, description=?, date=?, note=?
           WHERE id=?""",
        (amount, category, description, exp_date, note, eid),
    )
    conn.commit()
    cur.execute("SELECT * FROM expenses WHERE id = ?", (eid,))
    updated = cur.fetchone()
    conn.close()
    return jsonify(row_to_expense(updated))


@app.route("/api/expenses/<int:eid>", methods=["DELETE"])
def delete_expense(eid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (eid,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if not deleted:
        return jsonify({"error": "not found"}), 404
    return jsonify({"status": "deleted", "id": eid})


@app.route("/api/expenses", methods=["DELETE"])
def clear_expenses():
    """Bulk delete — used by 'Clear My Data'. Requires ?user="""
    user = request.args.get("user")
    if not user:
        return jsonify({"error": "user query param required"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE user = ?", (user,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "count": deleted})


# ════════════════════════════════════════════════════════
#  CATEGORY BUDGETS — CRUD
# ════════════════════════════════════════════════════════
@app.route("/api/budgets/category", methods=["GET"])
def list_category_budgets():
    user = request.args.get("user")
    conn = get_conn()
    cur = conn.cursor()
    if user:
        cur.execute("SELECT * FROM category_budgets WHERE user = ?", (user,))
    else:
        cur.execute("SELECT * FROM category_budgets")
    out = {}
    for r in cur.fetchall():
        out.setdefault(r["user"], {})[r["category"]] = r["amount"]
    conn.close()
    return jsonify(out)


@app.route("/api/budgets/category", methods=["PUT"])
def upsert_category_budget():
    body = request.get_json(force=True) or {}
    user, category, amount = body.get("user"), body.get("category"), body.get("amount")
    if not user or not category or amount is None:
        return jsonify({"error": "user, category, amount required"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO category_budgets (user, category, amount) VALUES (?, ?, ?)
           ON CONFLICT(user, category) DO UPDATE SET amount = excluded.amount""",
        (user, category, round(float(amount), 2)),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "user": user, "category": category, "amount": amount})


@app.route("/api/budgets/category", methods=["DELETE"])
def delete_category_budget():
    user, category = request.args.get("user"), request.args.get("category")
    if not user or not category:
        return jsonify({"error": "user and category query params required"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM category_budgets WHERE user = ? AND category = ?",
        (user, category),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if not deleted:
        return jsonify({"error": "not found"}), 404
    return jsonify({"status": "deleted"})


# ════════════════════════════════════════════════════════
#  MONTHLY BUDGETS — CRUD
# ════════════════════════════════════════════════════════
@app.route("/api/budgets/monthly", methods=["GET"])
def list_monthly_budgets():
    user = request.args.get("user")
    conn = get_conn()
    cur = conn.cursor()
    if user:
        cur.execute("SELECT * FROM monthly_budgets WHERE user = ?", (user,))
    else:
        cur.execute("SELECT * FROM monthly_budgets")
    out = {}
    for r in cur.fetchall():
        out.setdefault(r["user"], {})[r["month"]] = r["amount"]
    conn.close()
    return jsonify(out)


@app.route("/api/budgets/monthly", methods=["PUT"])
def upsert_monthly_budget():
    body = request.get_json(force=True) or {}
    user, month, amount = body.get("user"), body.get("month"), body.get("amount")
    if not user or not month or amount is None:
        return jsonify({"error": "user, month, amount required"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO monthly_budgets (user, month, amount) VALUES (?, ?, ?)
           ON CONFLICT(user, month) DO UPDATE SET amount = excluded.amount""",
        (user, month, round(float(amount), 2)),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "user": user, "month": month, "amount": amount})


@app.route("/api/budgets/monthly", methods=["DELETE"])
def delete_monthly_budget():
    user, month = request.args.get("user"), request.args.get("month")
    if not user or not month:
        return jsonify({"error": "user and month query params required"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM monthly_budgets WHERE user = ? AND month = ?", (user, month)
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if not deleted:
        return jsonify({"error": "not found"}), 404
    return jsonify({"status": "deleted"})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)