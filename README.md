# 🔥 Productivity Habit Tracker

A **simple and beginner-friendly web app** to track your daily habits, tasks, and progress, built using **Flask**, **SQLite**, and basic **HTML/CSS**.  

Track tasks, mark them complete, see analytics, and maintain streaks to build consistent habits.  

---

## 🌟 Features

- ✅ **User Authentication** (Register / Login / Logout)  
- ✅ **Add Tasks / Habits** with optional **notes** and **categories**  
- ✅ **Mark Tasks Complete**  
- ✅ **Daily Completion History** and **Streak Tracking**  
- ✅ **Category-wise Completion Analytics**  
- ✅ **Flash messages for errors & success notifications**  
- ✅ **Clean, beginner-friendly interface using HTML & CSS**  

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask  
- **Database:** SQLite  
- **Frontend:** HTML, CSS (`minimal JS, optional`)  
- **Data Analysis:** `pandas` (for simple analytics & completion rates)  

---

## 🚀 Getting Started

### 1️⃣ Clone the repository
```bash
git clone https://github.com/pranav-mahure/Login-page-by-flask.git
cd Login-page-by-flask
```
2️⃣ Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```
3️⃣ Install required packages
```bash
pip install flask pandas
```
4️⃣ Run the app
```bash
python app.py
```
5️⃣ Open in browser
```bash
http://127.0.0.1:5000/
```
<!--
🎬 Demo Workflow

Capture a small GIF showing the app in action: Register → Login → Add Task → Complete Task → View Analytics
-->
---
<!-- Replace this with your GIF link -->
## 📁 Folder Structure
```bash
Login-page-by-flask/
│
├─ app.py
├─ tracker.db          # SQLite database (auto-created)
├─ templates/
│   ├─ base.html
│   ├─ login.html
│   ├─ register.html
│   └─ dashboard.html
├─ static/
│   └─ style.css
└─ assets/
    └─ demo.gif
```
---
## ✅ Usage Notes & Tips

* Passwords are stored as plain text in this beginner version for simplicity. Do not use real passwords here. Next improvement: add hashing with werkzeug.security.generate_password_hash.

* If you see sqlite3.OperationalError on startup, make sure your tracker.db file is writeable in the project folder.

* Flash messages appear at the top of the dashboard/login pages to guide the user (e.g., "Invalid credentials", "Task added", etc.).

## Future Improvements
1.Add visual charts using matplotlib or plotly for habit analytics

2.Password hashing for security

2.Notifications / reminders for tasks

3.Mobile-friendly responsive design

4.Dark mode toggle

---

## 📌 Notes

1.Flash messages are used to guide the user for errors, success, and notifications.

2.Beginner-friendly code structure so you can easily extend or modify the app.

3.You can replace the GIF with actual screenshots or record a live demo for better presentation.

---
## 🤝 Contributing

1.Fork the repo

2.Create a feature branch (`git checkout -b feature/my-feature`)

3.Commit your changes (`git commit -m 'Add feature'`)

4.Push (`git push origin feature/my-feature`) and open a PR

5.Keep changes small and well-commented — this project is designed for learning.

