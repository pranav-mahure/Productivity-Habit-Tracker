from flask import Flask, render_template, url_for, request, session, redirect,\
      send_from_directory, jsonify
import json                                                                                       
import os

users = {}  # For storing data of new users a global dict is created
 
app = Flask(__name__)
app.secret_key = 'mysecret'

UPLOAD_FOLDER = 'uploads'  # Assigning 'uploads' value to UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True) # will create folder if not exist 'exist_ok' will make sure that it will not throw error if folder is already there

@app.route('/upload', methods =['GET', 'POST'])
def upload():
    filename = None
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'],
                                    file.filename)
            file.save(filepath)
            filename = file.filename
    return render_template('upload.html', filename = filename)


@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
   
    message = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '')

        if os.path.exists('loginData.json') and os.path.getsize('loginData.json')> 0:
            with open('loginData.json', 'r') as f:
                users = json.load(f)       
        else:
            users ={}

        if not username or not password or not confirm_password:
            message = 'Please fill out all fields.'
        elif username in users:
            message = 'Username already taken.'
        elif len(password) < 8:
            message = 'Password must be at least 8 characters.'
        elif password != confirm_password:
            message = 'Passwords do not match.'
         #Loading existing data

        if username in users :
            message = 'Username already Exist , please try another '

        else:
            #  Saving new user 
            users[username ] = password
            with open ('loginData.json', 'w') as f:
                json.dump(users,f)
            session['user'] = username
            return redirect(url_for('dashboard'))
        return render_template('register.html', message=message)        
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == '':
            message = 'Username is required!'
        elif password == '':
            message = 'Password is required!'

         #Loading existing data
        if os.path.exists('loginData.json') and os.path.getsize('loginData.json')> 0:
            with open('loginData.json', 'r') as f:
                users = json.load(f)

        else:
            users ={}
        # Validate users credentials
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))

        else :
            message = 'Invalid credentials! Please try again.'
    return render_template('login.html', message=message)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user= session['user'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)

    return render_template('logout.html')

# Using URL Parameter (Dynamic Routes)
@app.route('/hello/<username>')
def greet_user(username):
    return f"Hello, {username}!"


# Hitting API 
@app.route('/api', methods =['POST'])
def calculate_sum():
    data = request.get_json() # By get_json() we can get the data in json format
    a_val= float(dict(data)['a'])
    b_val= float(dict(data)['b'])
    return jsonify({'sum': a_val + b_val})

if __name__ == '__main__':
    app.run(debug=True)

