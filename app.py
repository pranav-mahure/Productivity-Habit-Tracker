# app.py — compatible with local SQLite and Render Postgres (Flask 3.x safe)
import os
import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import pandas as pd

# optional: psycopg2 (Postgres)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    psycopg2 = None
    RealDictCursor = None

app = Flask(__name__)
# env var SECRET_KEY in production fallback for local dev
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# DB selection: prefer DATABASE_URL (Postgres). Fall back to local sqlite file.
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_DB")
DB_FILE = "tracker.db"

# normalize postgres URL if needed
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)  # True -> use Postgres, False -> sqlite


# DB helpers
def connect_db_direct():
    """Return a fresh DB connection (not stored in g)."""
    if USE_POSTGRES:
        # psycopg2 is required when using Postgres
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn


def get_db():
    """Get or create a connection stored on flask.g"""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = connect_db_direct()
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def db_execute(query, params=()):
    """
    Execute a query on the active connection.
    - Accepts queries written using SQLite-style '?' placeholders.
    - Converts '?' -> '%s' for psycopg2 when using Postgres.
    Returns the cursor.
    """
    conn = get_db()
    cur = conn.cursor()
    if USE_POSTGRES:
        # convert '?' to '%s' for psycopg2 parameter style
        q = query.replace("?", "%s")
        cur.execute(q, params)
    else:
        cur.execute(query, params)
    return cur


def db_commit():
    conn = get_db()
    conn.commit()


# Schema creation 
def create_tables_if_not_exist():
    """
    Create tables for users and tasks if they don't exist.
    Uses suitable SQL for SQLite and Postgres.
    """
    conn = connect_db_direct()
    cur = conn.cursor()
    if USE_POSTGRES:
        # Postgres compatible schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                task TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                notes TEXT,
                status TEXT DEFAULT 'pending',
                date_completed TEXT
            )
        """)
    else:
        # SQLite schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                notes TEXT,
                status TEXT DEFAULT 'pending',
                date_completed TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
    conn.commit()
    conn.close()


# create tables at import time so Postgres has the schema ready when gunicorn loads module
create_tables_if_not_exist()


#  Routes
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        if not username or not password or not confirm:
            flash("Please fill out all fields.", "warning")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "warning")
            return redirect(url_for("register"))
        if password != confirm:
            flash("Passwords do not match.", "warning")
            return redirect(url_for("register"))

        try:
            db_execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db_commit()
            flash("Registration successful — you can now login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            # For sqlite IntegrityError or Postgres UniqueViolation
            try:
                # rollback if using Postgres or sqlite connection supports rollback
                get_db().rollback()
            except Exception:
                pass
            flash("Username already taken — try another.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return redirect(url_for("login"))

        cur = db_execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()

        if user:
            # psycopg2 returns dict-like if using RealDictCursor only when we set it here fetchone returns tuple or row
            # handle both possibilities
            try:
                uid = user["id"]
            except Exception:
                uid = user[0] if isinstance(user, tuple) else user[0]
            session["user_id"] = uid
            session["username"] = username
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. If you don't have an account, please register.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        flash("Please login first.", "info")
        return redirect(url_for("login"))

    # new task creation
    if request.method == "POST":
        task = request.form.get("task", "").strip()
        category = request.form.get("category", "General").strip()
        notes = request.form.get("notes", "").strip()
        if not task:
            flash("Task name cannot be empty.", "warning")
            return redirect(url_for("dashboard"))

        db_execute("INSERT INTO tasks (user_id, task, category, notes) VALUES (?, ?, ?, ?)",
                   (session["user_id"], task, category, notes))
        db_commit()
        flash("Task added.", "success")
        return redirect(url_for("dashboard"))

    cur = db_execute("SELECT id, task, category, notes, status, date_completed FROM tasks WHERE user_id=? ORDER BY id DESC",
                     (session["user_id"],))
    tasks = cur.fetchall()

    # Build a pandas DataFrame for analytics
    # Convert rows to list-of-tuples consistently
    rows = []
    for r in tasks:
        # r might be sqlite3.Row or psycopg2 tuple/dict
        if isinstance(r, dict):
            rows.append((r.get("id"), r.get("task"), r.get("category"), r.get("notes"), r.get("status"), r.get("date_completed")))
        else:
            # sqlite3.Row supports tuple indexing
            try:
                rows.append((r["id"], r["task"], r["category"], r["notes"], r["status"], r["date_completed"]))
            except Exception:
                rows.append(tuple(r))

    df = pd.DataFrame(rows, columns=["id", "task", "category", "notes", "status", "date_completed"]) if rows else pd.DataFrame()
    if df.empty:
        category_stats = {}
    else:
        category_stats = (df.assign(completed=df["status"] == "completed")
                          .groupby("category")["completed"]
                          .apply(lambda s: 100 * s.sum() / len(s) if len(s) > 0 else 0)
                          .round(1)
                          .to_dict())

    completed_dates = set(df[df["status"] == "completed"]["date_completed"].dropna().tolist()) if not df.empty else set()
    streak = 0
    if completed_dates:
        today = date.today()
        check_day = today
        while check_day.isoformat() in completed_dates:
            streak += 1
            check_day = check_day.fromordinal(check_day.toordinal() - 1)

    return render_template("dashboard.html", username=session["username"], tasks=tasks, category_stats=category_stats, streak=streak)


@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    if "user_id" not in session:
        flash("Please login first.", "info")
        return redirect(url_for("login"))

    cur = db_execute("SELECT id FROM tasks WHERE id=? AND user_id=?", (task_id, session["user_id"]))
    found = cur.fetchone()
    if not found:
        flash("Task not found or not yours.", "danger")
        return redirect(url_for("dashboard"))

    db_execute("UPDATE tasks SET status='completed', date_completed=? WHERE id=? AND user_id=?",
               (date.today().isoformat(), task_id, session["user_id"]))
    db_commit()
    flash("Marked as completed.", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    # ensure local sqlite tables exist (safe no-op on Postgres)
    create_tables_if_not_exist()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
