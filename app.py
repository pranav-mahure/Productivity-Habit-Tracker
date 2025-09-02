# app.py (SQLAlchemy version — minimal comments)

import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")  # override in prod

# DB config: use DATABASE_URL if present (Postgres on Render), else local sqlite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tracker.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    tasks = db.relationship("Task", backref="user", lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    task = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(120), default="General")
    notes = db.Column(db.String(1000))
    status = db.Column(db.String(20), default="pending")
    date_completed = db.Column(db.String(20))  # ISO date string

# ensure tables exist
@app.before_first_request
def create_tables():
    db.create_all()

# routes (kept behavior similar to your sqlite version)
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

        if User.query.filter_by(username=username).first():
            flash("Username already taken — try another.", "danger")
            return redirect(url_for("register"))

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful — you can now login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return redirect(url_for("login"))

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
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

    if request.method == "POST":
        task_text = request.form.get("task", "").strip()
        category = request.form.get("category", "General").strip()
        notes = request.form.get("notes", "").strip()
        if not task_text:
            flash("Task name cannot be empty.", "warning")
            return redirect(url_for("dashboard"))
        new_task = Task(user_id=session["user_id"], task=task_text, category=category, notes=notes)
        db.session.add(new_task)
        db.session.commit()
        flash("Task added.", "success")
        return redirect(url_for("dashboard"))

    tasks = Task.query.filter_by(user_id=session["user_id"]).order_by(Task.id.desc()).all()

    # prepare analytics via pandas
    rows = [(t.id, t.task, t.category, t.notes, t.status, t.date_completed) for t in tasks]
    df = pd.DataFrame(rows, columns=["id","task","category","notes","status","date_completed"]) if rows else pd.DataFrame()
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

    t = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first()
    if not t:
        flash("Task not found or not yours.", "danger")
        return redirect(url_for("dashboard"))

    t.status = "completed"
    t.date_completed = date.today().isoformat()
    db.session.commit()
    flash("Marked as completed.", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    db.create_all()  # create tables locally if needed
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
