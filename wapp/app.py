from logging import error
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, current_app
from wtforms.fields.choices import SelectField
from data import Reports
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

import os
import secrets

app  = Flask(__name__)

#config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'PROJECT'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'myapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init MYSQL
mysql = MySQL(app)

Reports = Reports()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

#all reports
@app.route('/reports')
def reports():
    cur = mysql.connection.cursor();
    #execute query
    reportList = cur.execute("SELECT * FROM reports ")
    reportsDetail = cur.fetchall()
    return render_template('reports.html', reportsDetail = reportsDetail)

#single article
@app.route('/reports/<string:id>/')
def report(id):
    return render_template('report.html', id = id)

# Register form Class
class RegisterForm(Form):
   name = StringField('Name', [validators.Length(min=1, max=50)])
   username = StringField('Username', [validators.Length(min=4, max=25)])
   email = StringField('Email', [validators.Length(min = 6, max = 50)])
   password = PasswordField('Password', [
       validators.DataRequired(),
       validators.EqualTo('confirm', message = 'Password do not match')
   ])
   confirm = PasswordField('Confirm Password')
   profession = SelectField('Profession', choices=[('Doctor', 'Doctor'), ('Staff', 'Staff'), ('Patient', 'Patient')])

#user register
@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        profession = form.profession.data
        #Create cursor
        cur = mysql.connection.cursor();

        #execute query
        cur.execute("INSERT INTO users(name, email, username, password, profession ) VALUES(%s, %s, %s, %s, %s)", (name, email, username, password, profession) )
        
        #Commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form = form)
        
#User Login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create cursor
        cur = mysql.connection.cursor();

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE  username = %s", [username])

        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            #close connection
            cur.close();
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap
# Layout
@app.route('/logout')
def layout():
    session.clear()
    flash('You are now logged Out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


# Image upload

def save_images(photo):
    hash_photo = secrets.token_urlsafe(10)
    _, file_extension = os.path.splitext(photo.filename)
    photo_name = hash_photo + file_extension
    file_path = os.path.join(current_app.root_path, 'static/images', photo_name)
    photo.save(file_path)
    return photo_name


@app.route('/<string:id>/<string:name>/report/share', methods = ['POST','GET'])
@is_logged_in
def shareReport(id, name):
    if request.method == "POST":
        sharedBy = session["username"]
        description = request.form['description']
        report = save_images(request.files['reports'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO reports(sharedBy, description, report)" "VALUES(%s, %s, %s)", (sharedBy, description, report))
        mysql.connection.commit()
        cur.close()
        flash('Report uploaded successfully', 'success')
        return redirect('/')
    return render_template('shareReport.html', name = name, id = id)

#all registered patients
@app.route('/usersList', methods = ['POST','GET'] )
@is_logged_in
def usersList():
    #Create cursor
    cur = mysql.connection.cursor();
    name = session["username"]
    #execute query
    UserListPatient = cur.execute("SELECT * FROM users WHERE profession='Patient'")
    Patients = cur.fetchall()

    UserListDoctor = cur.execute("SELECT * FROM users WHERE profession='Doctor'")
    Doctors = cur.fetchall()

    UserListStaff = cur.execute("SELECT * FROM users WHERE profession='Staff'")
    Staffs = cur.fetchall()

    if UserListPatient > 0 or UserListDoctor > 0 or UserListStaff > 0:
        return render_template('usersList.html', Patients = Patients, Doctors = Doctors, Staffs = Staffs )
    
    else:
        msg = 'No data found'
        return render_template('usersList.html', msg = msg)

    #close connnection
    cur.close()

#single profile of user
@app.route('/users/<string:id>/<string:username>')
def userProfile(id, username):
    cur = mysql.connection.cursor();
    getlist = cur.execute("SELECT * FROM users WHERE id=" + id + "")
    user = cur.fetchall()
    if getlist > 0:
        return render_template('userProfile.html', id = id,  user=user)
    else:
        msg = 'No data found'
        return render_template('userProfile.html', msg=msg)

    cur.close()

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)