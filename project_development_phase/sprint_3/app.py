from flask import *
import ibm_db
from sendgridmail import sendmail
import os
from dotenv import load_dotenv

load_dotenv()

conn = ibm_db.connect(os.getenv('DB_KEY'),'','')

app = Flask(__name__)

app.app_context().push()
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SECRET_KEY'] = 'AJDJRJS24$($(#$$33--'

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/")
def login():
    return render_template("login.html")

# Login
@app.route("/loginmethod", methods = ['GET'])
def loginmethod():
    global userid
    msg = ''

    if request.method == 'GET':
        uname = request.args.get("uname")
        psw = request.args.get("psw")

        sql = "SELECT * FROM accounts WHERE username =? AND password=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, uname)
        ibm_db.bind_param(stmt, 2, psw)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)

        if uname == 'admin' and psw == 'admin':
            return redirect(url_for('admin'))

        if account:
            session['loggedin'] = True
            session['id'] = account['USERNAME']
            userid = account['USERNAME']
            session['username'] = account['USERNAME']
            return redirect(url_for("about"))
        else:
            msg = 'Incorrect Username and Password'
            flash(msg)
            return redirect(url_for("login"))

@app.route("/admin")
def admin():
    send_sql = "SELECT * FROM donor"
    prep_stmt = ibm_db.prepare(conn, send_sql)
    ibm_db.execute(prep_stmt)
    row = ibm_db.fetch_assoc(prep_stmt)

    values = {}
    ind = 0
    while row != False:
        values[ind] = row
        ind += 1
        row = ibm_db.fetch_assoc(prep_stmt)
    print(values)

    return render_template('admin.html',values=values)

# Signup
@app.route("/signupmethod", methods = ['POST'])
def signupmethod():
    msg = ''
    if request.method == 'POST':
        uname = request.form['uname']
        email = request.form['email']
        name = request.form['name']
        dob = request.form['dob']
        psw = request.form['psw']
        con_psw = request.form['con_psw']

        sql = "SELECT * FROM accounts WHERE username =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, uname)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)

        if account:
            msg = 'Account already exists !'
            flash(msg)
            return redirect(url_for("signup"))
        elif psw != con_psw:
            msg = "Password and Confirm Password do not match."
            flash(msg)
            return redirect(url_for("signup"))
        else:
            insert_sql = "INSERT INTO accounts VALUES (?, ?, ?, ?, ?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, email)
            ibm_db.bind_param(prep_stmt, 3, dob)
            ibm_db.bind_param(prep_stmt, 4, uname)
            ibm_db.bind_param(prep_stmt, 5, psw)
            ibm_db.execute(prep_stmt)

            insert_donor = "INSERT INTO donor(Name,Username,Email,DOB,Availability) VALUES (?, ?, ?, ?, ?)"
            prep_stmt = ibm_db.prepare(conn, insert_donor)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, uname)
            ibm_db.bind_param(prep_stmt, 3, email)
            ibm_db.bind_param(prep_stmt, 4, dob)
            ibm_db.bind_param(prep_stmt, 5, "Not Available")
            ibm_db.execute(prep_stmt)

            sendmail(email,'Plasma donor App login',name, 'You are successfully Registered!')

            return redirect(url_for("login"))

    elif request.method == 'POST':
        msg = 'Please fill out the form !'
        flash(msg)
        return redirect(url_for("signup"))

@app.route("/home")
def home():
    return render_template("home.html")

@app.route('/requester')
def requester():
    if session['loggedin'] == True:
        return render_template('home.html')
    else:
        msg = 'Please login!'
        return render_template('login.html', msg = msg)

@app.route('/requested',methods=['POST'])
def requested():
    global value
    bloodgrp = request.form['bloodgrp']
    city = request.form['city']

    send_sql = "SELECT * FROM donor where BLOODTYPE = ? and CITY = ? and USERNAME != ? and AVAILABILITY = ?"
    prep_stmt = ibm_db.prepare(conn, send_sql)
    ibm_db.bind_param(prep_stmt, 1, bloodgrp)
    ibm_db.bind_param(prep_stmt, 2, city)
    ibm_db.bind_param(prep_stmt, 3, session['username'])
    ibm_db.bind_param(prep_stmt, 4, 'Available')
    ibm_db.execute(prep_stmt)
    row = ibm_db.fetch_assoc(prep_stmt)

    value = {}
    ind = 0
    while row != False:
        value[ind] = row
        ind += 1
        row = ibm_db.fetch_assoc(prep_stmt)
    print(value)

    return render_template("donorlist.html", value=value)

    # return render_template('home.html', pred="Your request is sent to the concerned people.")

@app.route('/about')
def about():
    print(session["username"], session['id'])

    display_sql = "SELECT * FROM donor WHERE username = ?"
    prep_stmt = ibm_db.prepare(conn, display_sql)
    ibm_db.bind_param(prep_stmt, 1, session['id'])
    ibm_db.execute(prep_stmt)
    account = ibm_db.fetch_assoc(prep_stmt)
    print(account)
    donors = {}
    for values in account:
        if type(account[values]) == str:
            donors[values] = account[values].strip()
        else:
            donors[values] = account[values]
    print(donors)
    return render_template("about.html", account = donors)

@app.route('/sendEmail', methods = ["GET", "POST"])
def sendEmail():
    if request.method == 'POST':
        if request.form['select'] == 'select':
            email = request.form["Email"]
            uname = request.form['Username']
            curr_uname = session["username"]
            name = request.form['Name']
            select = "SELECT * from requests where Username = ? and Requestuname = ?"
            stmt = ibm_db.prepare(conn, select)
            ibm_db.bind_param(stmt, 1, uname)
            ibm_db.bind_param(stmt, 2, curr_uname)
            ibm_db.execute(stmt)
            bool = ibm_db.fetch_assoc(stmt)

            print("boolean"+str(bool))
            if not bool:
                request_sql = "INSERT INTO requests VALUES (?, ?)"
                stmt = ibm_db.prepare(conn, request_sql)
                ibm_db.bind_param(stmt, 1, uname)
                ibm_db.bind_param(stmt, 2, curr_uname)
                ibm_db.execute(stmt)
                sendmail(email, 'Plasma donor App plasma request', name,'You have received a request for Plasma Donation from a donee.')
            else:
                print(bool)
            print(email)
            print(name)
    return render_template("donorlist.html", value=value)

@app.route('/requests')
def requests():
    req_sql = "SELECT * From requests where Username = ?"
    stmt = ibm_db.prepare(conn, req_sql)
    ibm_db.bind_param(stmt, 1, session['username'])
    ibm_db.execute(stmt)
    req = ibm_db.fetch_assoc(stmt)
    print(req)
    print(session['username'])
    values = {}
    ind = 0
    while req != False:
        get_data = "Select * from donor where Username = ?"
        prep_stmt = ibm_db.prepare(conn, get_data)
        ibm_db.bind_param(prep_stmt, 1, req['REQUESTUNAME'])
        ibm_db.execute(prep_stmt)
        req1 = ibm_db.fetch_assoc(prep_stmt)
        values[ind] = req1
        ind += 1
        req = ibm_db.fetch_assoc(stmt)
    print(values)

    return render_template("requests.html", value=values)

@app.route('/details', methods = ['POST'])
def details():
    if request.method == 'POST':
        uname = request.form['uname']
        email = request.form['email']
        name = request.form['name']
        dob = request.form['dob']
        age = request.form['age']
        phone = request.form['phone']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        bloodtype = request.form['bloodtype']
        description = request.form['description']
        avail = request.form['avail']

        sql = "SELECT * FROM donor WHERE Username =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, uname)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)

        if account:
            update_sql = "UPDATE donor set Name=?, Username=?, Email=?, DOB=?, Age=?, Phone=?, City=?, State=?, Country=?, BloodType=?,Description=?,Availability=? where Username = ?"
            prep_stmt = ibm_db.prepare(conn, update_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, uname)
            ibm_db.bind_param(prep_stmt, 3, email)
            ibm_db.bind_param(prep_stmt, 4, dob)
            ibm_db.bind_param(prep_stmt, 5, age)
            ibm_db.bind_param(prep_stmt, 6, phone)
            ibm_db.bind_param(prep_stmt, 7, city)
            ibm_db.bind_param(prep_stmt, 8, state)
            ibm_db.bind_param(prep_stmt, 9, country)
            ibm_db.bind_param(prep_stmt, 10, bloodtype)
            ibm_db.bind_param(prep_stmt, 11, description)
            ibm_db.bind_param(prep_stmt, 12, avail)
            ibm_db.bind_param(prep_stmt, 13, uname)
            ibm_db.execute(prep_stmt)
            print("Update Success")
            return redirect(url_for("about"))
        else:
            insert_sql = "INSERT INTO donor VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, uname)
            ibm_db.bind_param(prep_stmt, 3, email)
            ibm_db.bind_param(prep_stmt, 4, dob)
            ibm_db.bind_param(prep_stmt, 5, age)
            ibm_db.bind_param(prep_stmt, 6, phone)
            ibm_db.bind_param(prep_stmt, 7, city)
            ibm_db.bind_param(prep_stmt, 8, state)
            ibm_db.bind_param(prep_stmt, 9, country)
            ibm_db.bind_param(prep_stmt, 10, bloodtype)
            ibm_db.bind_param(prep_stmt, 11, description)
            ibm_db.bind_param(prep_stmt, 12, avail)
            ibm_db.bind_param(prep_stmt, 13, False)

            ibm_db.execute(prep_stmt)
            print("Sucess")
            return redirect(url_for("about"))

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return render_template('login.html')

if __name__ == '__main__':
   app.run(host='0.0.0.0',debug='TRUE')