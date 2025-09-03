# 🔥 Productivity Habit Tracker

A simple, beginner-friendly web app to track daily habits and small tasks — built with **Flask (v3)** and deployed on **Render**.  
Features a task list, categories, optional notes, completion tracking, streaks, and basic category analytics using **pandas**.

---

## 🌟 Live Demo
https://productivity-habit-tracker.onrender.com

---

## ✨ Features

- User registration, login & logout (session-based)  
- Add tasks with **category** and optional **notes**  
- Mark tasks as **completed** (stores completion date)  
- Quick insights: **streaks** and **category completion rates** (via pandas)  
- Works locally with SQLite; in production uses Postgres (via `DATABASE_URL`)  
- Flash messages for user-friendly feedback

---

## 📁 Repo structure
```bash
productivity-habit-tracker/
├─ app.py
├─ requirements.txt
├─ templates/
│     ├─ base.html
│     ├─ login.html
│     ├─ register.html
│     └─ dashboard.html
└─ static/
     └─ style.css
```

---

## 🛠 Tech stack

- Backend: **Flask** (Python)  
- Database: **SQLite** (local dev) / **Postgres** (production via `DATABASE_URL`)  
- Analytics: **pandas**  
- Deployment: **Render** (gunicorn)

---

## 🚀 Quick start (local)

1. Clone:
```bash
git clone https://github.com/<your-username>/Productivity-Habit-Tracker.git
cd Productivity-Habit-Tracker
```
2.Create & activate a virtual environment:
```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
```
3.Install dependencies:
```bash
pip install -r requirements.txt
```
4.Run the app:
```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

---
## ☁️ Deploying to Render (summary)

1.Create a Postgres database on Render (or use Supabase/ElephantSQL). Copy the Internal Database URL.

2.Create a Web Service on Render, connect your GitHub repo and set the Start Command to:
```bash
gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT
```
3.In the Web Service Environment settings, add:

* `DATABASE_URL` → Internal Database URL from your Postgres instance

* `SECRET_KEY` → a long random string

4.Ensure `requirements.txt` is present in repo root (Render installs it during build).

5.Trigger deploy (Render auto-deploys on commit/push).

---
## 🔒 Environment variables

Set these on Render (Web Service → Environment):

* `DATABASE_URL` — Postgres connection string (internal URL if DB in same Render account).

* `SECRET_KEY` — a strong random secret for Flask sessions.

Note: locally, the app falls back to tracker.db SQLite and a dev secret, so you don't have to set these for local testing.

## ✅ Troubleshooting tips

* If Render build fails: check requirements.txt spelling and build logs.

* If you see relation "users" does not exist, ensure tables were created (app creates them at startup; check logs or run a one-time SQL script).

* If tasks are not visible after adding, check Render logs for cursor/row format — the project uses dict-like rows for Postgres.

---
## 🔭 Next steps & ideas

* Add password hashing for extra security.

* Add charts (matplotlib/plotly) for visual analytics.

* Add reminders/notifications and recurring tasks.

* Make UI responsive + add dark mode.

---
## 🤝 Contributing

Contributions welcome! Create a fork → make your changes → open a pull request. Please keep changes small and well-documented.

---
## 📜 License

This project is available under the MIT License.

