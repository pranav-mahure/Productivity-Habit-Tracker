from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import sqlite3
import os
from datetime import date
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey"   # change this in production !!

DB_NAME = "tracker.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        # Enable row access by column name for convenience
        db = g._database = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        # Tasks 
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
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


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
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            flash("Registration successful — you can now login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
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
        cur.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
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

    # new task creation
    if request.method == "POST":
        task = request.form.get("task", "").strip()
        category = request.form.get("category", "General").strip()
        notes = request.form.get("notes", "").strip()
        if not task:
            flash("Task name cannot be empty.", "warning")
            return redirect(url_for("dashboard"))
        cur.execute("""
            INSERT INTO tasks (user_id, task, category, notes) VALUES (?, ?, ?, ?)
        """, (session["user_id"], task, category, notes))
        db.commit()
        flash("Task added.", "success")
        return redirect(url_for("dashboard"))

    # Fetch user tasks
    cur.execute("SELECT id, task, category, notes, status, date_completed FROM tasks WHERE user_id=? ORDER BY id DESC", (session["user_id"],))
    tasks = cur.fetchall()

    # Build a pandas DataFrame for analytics (safe even if empty)
    df = pd.DataFrame(tasks, columns=["id","task","category","notes","status","date_completed"])
    if df.empty:
        category_stats = {}
    else:
        # completion rate per category (percentage)
        category_stats = (df.assign(completed=df["status"]=="completed")
                            .groupby("category")["completed"]
                            .apply(lambda s: 100* s.sum()/len(s) if len(s)>0 else 0)
                            .round(1)
                            .to_dict())

    # Simple streak calculation: number of consecutive days with at least one completed task (ending today)
    completed_dates = set()
    if not df.empty:
        completed_dates = set(x for x in df[df["status"]=="completed"]["date_completed"].dropna().tolist())
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
    cur.execute("SELECT id FROM tasks WHERE id=? AND user_id=?", (task_id, session["user_id"]))
    found = cur.fetchone()
    if not found:
        flash("Task not found or not yours.", "danger")
        return redirect(url_for("dashboard"))

    cur.execute("UPDATE tasks SET status='completed', date_completed=? WHERE id=? AND user_id=?", (date.today().isoformat(), task_id, session["user_id"]))
    db.commit()
    flash("Marked as completed.", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
