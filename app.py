from flask import Flask,request,redirect,render_template,url_for,session,flash,jsonify
import mysql.connector
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired


app = Flask(__name__)
app.secret_key = "mysecretkey"
conn = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password ='root',
    database = 'codegnan'
)

# --------- Email Config ---------
app.config['MAIL_SERVER'] ='smtp.gmail.com'
app.config['MAIL_PORT'] =587
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']="asrimurakonda@gmail.com"
app.config['MAIL_PASSWORD']="ljrk xhar nztz aanw"

mail = Mail(app)

#Token Serializer
s= URLSafeTimedSerializer(app.secret_key)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/home')
def register_page():
    return render_template("register.html")

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form['email']
    password = request.form['pwrd']
    cpassword = request.form['cpwrd']
    role = request.form['role']

    cursor = conn.cursor()

    if password != cpassword:
        flash("Password and Confirm Password do not match")
        return redirect('/register')

    cursor.execute(
        "SELECT * FROM users WHERE username=%s",
        (username,)
    )

    user = cursor.fetchone()

    if user:
        flash("Email already registered")
        return redirect('/register')

    cursor.execute(
        """
        INSERT INTO users(username,password,role)
        VALUES(%s,%s,%s)
        """,
        (username,password,role)
    )

    conn.commit()
    cursor.close()

    flash("Registration Successful")

    return redirect('/login')


@app.route('/about')
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route('/send_message', methods=['POST'])
def send_message():

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    message = request.form['message']

    msg = Message(
        subject="New Contact Form Message",
        sender=app.config['MAIL_USERNAME'],
        recipients=["asrimurakonda@gmail.com"]
    )

    msg.body = f"""
Name : {name}

Email : {email}

Phone : {phone}

Message :

{message}
"""

    mail.send(msg)

    flash("Message Sent Successfully.")

    return redirect('/contact')

@app.route('/login',methods=['GET','POST'])
def login():

    if request.method=="GET":
        return render_template("login.html")

    email=request.form['email']
    password=request.form['pwrd']

    cursor=conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (email,password)
    )

    admin=cursor.fetchone()

    if admin is None:
        flash("Invalid Username or Password")
        return redirect('/login')

    session['email']=admin[1]
    session['role']=admin[3]

    return redirect('/dashboard')


@app.route('/employees', methods=['POST'])
def add_employee():

    if 'email' not in session:
        return redirect('/login')

    eid=request.form['eid']
    ename=request.form['ename']
    edept=request.form['edept']
    esalary=request.form['esalary']
    ephone=request.form['ephone']

    cursor=conn.cursor()

    cursor.execute(
        "SELECT * FROM employees WHERE eid=%s",
        (eid,)
    )

    employee=cursor.fetchone()

    if employee:
        flash("Employee ID already exists.")
        return redirect('/add_employee')

    cursor.execute(
        """
        INSERT INTO employees
        (eid,ename,edept,esalary,ephone)
        VALUES(%s,%s,%s,%s,%s)
        """,
        (eid,ename,edept,esalary,ephone)
    )

    conn.commit()
    cursor.close()

    flash("Employee Added Successfully!")

    return redirect('/view_employee')

@app.route('/dashboard')
def dashboard():

    if 'email' not in session:
        return redirect('/login')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()

    return render_template(
        "dashboard.html",
        username=session['email'],
        users=users,
        employees=employees
    )

@app.route('/add_employee')
def add_employee_page():

    if 'email' not in session:
        return redirect('/login')

    return render_template("add_employee.html")


@app.route('/view_employee')
def view_employee():

    if 'email' not in session:
        return redirect('/login')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees")

    employees = cursor.fetchall()

    cursor.close()

    return render_template(
        "view_employee.html",
        employees=employees
    )


@app.route('/forgot_password')
def forgot_password():
    return render_template("forgot_password.html")


@app.route('/send_reset_link',methods=['POST'])
def send_reset_link():
    email = request.form['email']
    cursor = conn.cursor()

    cursor.execute(
    "SELECT * FROM users WHERE username=%s",
    (email,)
)

    user = cursor.fetchone()

    if user is None:
        flash("Email not registered!")
        return redirect('/forgot_password')

    token = s.dumps(email,salt='password-reset-salt')

    link = f"http://localhost:5000/reset_password/{token}"

    msg = Message("Password Reset Request",
                  sender=app.config['MAIL_USERNAME'],
                  recipients =[email])
    msg.body = f"Click the link to reset your password: {link}"
    mail.send(msg)

    flash("Reset link sent to your email!")
    return redirect('/login')

@app.route('/reset_password/<token>', methods=['GET','POST'])
def reset_password(token):

    try:
        email = s.loads(
            token,
            salt='password-reset-salt',
            max_age=300
        )

    except SignatureExpired:
        return "Link Expired"

    if request.method == 'POST':

        new_password = request.form['pwrd']

        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (new_password, email)
        )

        conn.commit()

        flash("Password updated successfully!")

        return redirect('/login')

    return render_template("reset_password.html")

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

app.run(debug=True)