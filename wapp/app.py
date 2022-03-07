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

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import encrypt as encryptAES
import decrypt as decryptAES
import rsa as rsa


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

        #generate private and public key
        private_key, public_key = rsa.generate_rsa_keys()
        e,n = public_key
        d, n = private_key
        e = str(e)
        n = str(n)
        d = str(d)
        
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        profession = form.profession.data
        #Create cursor
        cur = mysql.connection.cursor();

        #execute query
        cur.execute("INSERT INTO users(name, email, username, password, profession, e, n, d ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (name, email, username, password, profession, e, n, d) )
        
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
            id= int(data['id'])

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #passed                
                session['logged_in'] = True
                session['username'] = username
                session['id'] = id

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

# display shared reports
@app.route('/reports')
@is_logged_in
def reports():
    id = session['id']
    cur = mysql.connection.cursor();
    #execute query
    reportList = cur.execute("SELECT * FROM reports where sharedToUser = "+str(id)+"")
    reportsDetail = cur.fetchall()
    return render_template('reports.html', reportsDetail = reportsDetail)





# Image upload

def save_images(photo):
    hash_photo = secrets.token_urlsafe(10)
    _, file_extension = os.path.splitext(photo.filename)
    photo_name = hash_photo + file_extension
    file_path = os.path.join(current_app.root_path, 'static/images', photo_name)
    photo.save(file_path)
    return photo_name

# share report
@app.route('/<string:id>/<string:name>/report/share', methods = ['POST','GET'])
@is_logged_in
def shareReport(id, name):
    if request.method == "POST":
        sharedBy = session["username"]
        sharedTo = name
        sharedToUser = id

        description = request.form['description']
        report = save_images(request.files['reports'])
        key_to_encrypt_file = "jsdbfjdbnjf"
        encrypted_key = key_to_encrypt_file
        cur = mysql.connection.cursor()
        #fetch public_key 
        public_key_data = cur.execute("SELECT * from users where id ="+id+'')
        valid = cur.fetchone()

        e = int(valid["e"])
        n = int(valid["n"])
        public_key = e , n 
        encrypted_key =  rsa.encrypt(public_key, encrypted_key)

        encrypted_key = ' '.join(map(str,encrypted_key))

        
        cur.execute("INSERT INTO reports(sharedBy, description, report, encrypted_key, sharedToUser, sharedTo)" "VALUES(%s, %s, %s, %s, %s, %s)", (sharedBy, description, report, encrypted_key, int(sharedToUser), sharedTo))
        mysql.connection.commit()
        cur.close()

        
        key_to_encrypt_file  = key_to_encrypt_file.encode('UTF-8')
        key_to_encrypt_file = pad(key_to_encrypt_file, AES.block_size)
        encryptAES.encrypt('static/images/'+report +'', key_to_encrypt_file)


        flash('Report uploaded successfully', 'success')
        return redirect('/')
    return render_template('shareReport.html', name = name, id = id)


# decryption of reports
@app.route('/<string:id>/download', methods = ['POST','GET'])
@is_logged_in
def decryptAndDownload(id):

    key_to_encrypt_file = "jsdbfjdbnjf"

    
    
    #decrypt key_to_encrypt_file using RSA
    cur = mysql.connection.cursor()

    #fetch encrypted_key 
    public_report_data = cur.execute("SELECT * from reports where id ="+id+'')
    valid = cur.fetchone()
    report = valid['report']

    encrypted_key = valid['encrypted_key']
    arr = encrypted_key.split(' ')
    final_encryptedArr = [int(i) for i in arr]

    #get p
    loggedInUser = str(session['id'])
    
    private_key_data = cur.execute("SELECT * from users where id ="+loggedInUser+'')
    valid = cur.fetchone()

    d = int(valid["d"])
    n = int(valid["n"])
    private_key = d , n 

    decryptedKey =  rsa.decrypt(private_key, final_encryptedArr)

    
    # decrypt report using AES
    decryptedKey = decryptedKey.encode('UTF-8')
    decryptedKey = pad(decryptedKey, AES.block_size)

    #decrypt(filename, key)
    decryptAES.decrypt('static/images/'+report +'', decryptedKey)

    #download 


    #ReEncrypt
    # encryptAES.encrypt('static/images/'+report +'', decryptedKey)


    flash('Report uploaded successfully', 'success')
    return redirect('/')






#all registered patients
@app.route('/usersList', methods = ['POST','GET'] )
@is_logged_in
def usersList():
    #Create cursor
    cur = mysql.connection.cursor();
    name = session["username"]
    current_user = session['id']
    #execute query
    UserListPatient = cur.execute("SELECT * FROM users WHERE profession='Patient' and id != "+str(current_user)+"")
    Patients = cur.fetchall()

    UserListDoctor = cur.execute("SELECT * FROM users WHERE profession='Doctor'and id != "+str(current_user)+"")
    Doctors = cur.fetchall()

    UserListStaff = cur.execute("SELECT * FROM users WHERE profession='Staff'and id != "+str(current_user)+"")
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