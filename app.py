import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from datetime import date
import pandas as pd

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Database URL from Render
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tracker.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    cur = db.cursor()
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Tasks table
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
    db.commit()


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

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            db.commit()
            flash("Registration successful — you can now login.", "success")
            return redirect(url_for("login"))
        except psycopg2.IntegrityError:
            db.rollback()
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

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()

        if user:
            session["user_id"] = user["id"]
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

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        task = request.form.get("task", "").strip()
        category = request.form.get("category", "General").strip()
        notes = request.form.get("notes", "").strip()
        if not task:
            flash("Task name cannot be empty.", "warning")
            return redirect(url_for("dashboard"))

        cur.execute(
            "INSERT INTO tasks (user_id, task, category, notes) VALUES (%s, %s, %s, %s)",
            (session["user_id"], task, category, notes),
        )
        db.commit()
        flash("Task added.", "success")
        return redirect(url_for("dashboard"))

    cur.execute("SELECT id, task, category, notes, status, date_completed FROM tasks WHERE user_id=%s ORDER BY id DESC", (session["user_id"],))
    tasks = cur.fetchall()

    df = pd.DataFrame(tasks) if tasks else pd.DataFrame(columns=["id","task","category","notes","status","date_completed"])
    if df.empty:
        category_stats = {}
    else:
        category_stats = (df.assign(completed=df["status"]=="completed")
                            .groupby("category")["completed"]
                            .apply(lambda s: 100 * s.sum() / len(s) if len(s) > 0 else 0)
                            .round(1)
                            .to_dict())

    completed_dates = set(df[df["status"]=="completed"]["date_completed"].dropna().tolist()) if not df.empty else set()
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

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM tasks WHERE id=%s AND user_id=%s", (task_id, session["user_id"]))
    found = cur.fetchone()
    if not found:
        flash("Task not found or not yours.", "danger")
        return redirect(url_for("dashboard"))

    cur.execute("UPDATE tasks SET status='completed', date_completed=%s WHERE id=%s AND user_id=%s",
                (date.today().isoformat(), task_id, session["user_id"]))
    db.commit()
    flash("Marked as completed.", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
