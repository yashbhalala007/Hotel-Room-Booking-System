# index.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import math, random
from datetime import date
from flask_mysqldb import MySQL
import os
from werkzeug.utils import secure_filename
import pdfkit
from flask_mail import Mail, Message

UPLOAD_FOLDER = 'static/images/hotel/'
config = pdfkit.configuration(wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

app=Flask(__name__)
app.secret_key = 'HelloIAmLucifer!'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hotelroom'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'yashubhalala2017@gmail.com'
app.config['MAIL_PASSWORD'] = 'gzpzvfzdknzajebg'
app.config['MAIL_DEFAULT_SENDER'] = 'yashubhalala2017@gmail.com'
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False 

mysql = MySQL(app)
mail = Mail(app)

def generateOTP() :
	digits = "0123456789"
	OTP = ""
	for i in range(4) :
		OTP += digits[math.floor(random.random() * 10)]
	return OTP

def days(checkin, checkout) :
	today = str(date.today())
	tdate = today.split("-")
	date0 = date(int(tdate[0]), int(tdate[1]), int(tdate[2]))
	date1 = date(int(checkin[0]), int(checkin[1]), int(checkin[2]))
	date2 = date(int(checkout[0]), int(checkout[1]), int(checkout[2]))
	if (date1 - date0).days < 0 :
		return (date1 - date0).days
	return (date2 - date1).days

def cancledays(checkin) :
	today = str(date.today())
	tdate = today.split("-")
	date0 = date(int(tdate[0]), int(tdate[1]), int(tdate[2]))
	date1 = date(int(checkin[0]), int(checkin[1]), int(checkin[2]))
	if (date1 - date0).days < 0 :
		return (date1 - date0).days
	return (date1 - date0).days

@app.route('/')
def index() :
	session.pop('otp', None)
	if 'loggedin' in session :
		return redirect(url_for('dashboard'))
	return render_template('index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login() :
	if request.method == 'POST' :
		username = request.form['username']
		pwd = request.form['pass']
		cur = mysql.connection.cursor()
		query = "SELECT PASSWORD FROM USERINFO WHERE USERNAME = '%s'"%(username)
		data = cur.execute(query)
		password = cur.fetchone()
		if password is None :
			flash("User Not Found!!")
			return render_template('login.html')
		elif pwd != password[0] :
			flash("Password is incorrect!!")
			return render_template('login.html')
		else :
			session['loggedin'] = True
			session['user'] = username
			return redirect(url_for('dashboard'))
	if 'loggedin' in session :
		return redirect(url_for('dashboard'))
	return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register() :
	session.pop('_flashes', None)
	if request.method == 'POST' :
		try:
			cur = mysql.connection.cursor()
			query = '''CREATE TABLE USERINFO
    		(USERNAME CHAR(20) PRIMARY KEY NOT NULL, 
    		NAME CHAR(20) NOT NULL,
    		EMAIL TEXT NOT NULL, 
    		PASSWORD CHAR(15) NOT NULL,
    		USERROLE TEXT NOT NULL)'''
			cur.execute(query)
			mysql.connection.commit()
		except:
			mysql.connection.rollback()
		username = request.form['username']
		name = request.form['name']
		email = request.form['email']
		pwd = request.form['pass']
		rpwd = request.form['r_pass']
		userrole = "user"
		if 'loggedin' in session :
			userrole = request.form['userrole']
		try :
			query = "INSERT INTO USERINFO(USERNAME,NAME,EMAIL,PASSWORD,USERROLE) VALUES ('%s','%s','%s','%s','%s')"%(username,name,email,pwd,userrole)
			cur.execute(query)
			mysql.connection.commit()
			cur.close()
			if 'loggedin' in session :
				return redirect(url_for('dashboard'))
			session['loggedin'] = True
			session['user'] = request.form['username']
			return redirect(url_for('dashboard'))
		except:
			mysql.connection.rollback()
			cur.close()
			flash("User Already Exists!!")
			return render_template('signup.html')
	if 'loggedin' in session :
		return render_template('signup.html', userrole = "admin")
	return render_template('signup.html')

@app.route('/dashboard')
def dashboard() :
	if 'loggedin' in session :
		user = session['user']
		cur = mysql.connection.cursor()
		query =	"SELECT USERROLE FROM USERINFO WHERE USERNAME = '%s'"%(user)
		data = cur.execute(query)
		userrole = cur.fetchone()
		session['userrole'] = userrole[0]
		cur.close()
		return render_template('dashboard.html', userrole = userrole[0])
	return redirect(url_for('index'))

@app.route('/logout')
def logout() :
	session.pop('user', None)
	session.pop('loggedin', None)
	session.pop('_flashes', None)
	session.pop('userrole', None)
	return redirect(url_for('index'))

@app.route('/forgotpass', methods = ['GET', 'POST'])
def forgotpass() :
	session.pop('_flashes', None)
	if request.method == 'POST' :
		d = request.form['d']
		if d == '1' :
			username = request.form['username']
			cur = mysql.connection.cursor()
			query = "SELECT EMAIL FROM USERINFO WHERE USERNAME = '%s'"%(username)
			data = cur.execute(query)
			data = cur.fetchone()
			if 'otp' in session :
				return render_template('forgotpass.html', d = 2, username = username)
			if data is None :
				flash("User Not Found!!")
				return redirect(url_for('login'))
			else :
				otp = generateOTP()
				session['otp'] = str(otp)
				bd = "OTP For Change Password"
				msg = Message(bd, recipients = [data[0]])
				msg.body = "Your OTP is : %s"%(str(otp))
				mail.send(msg)
				return render_template('forgotpass.html', d = 2, username = username)
		elif d == '2' :
			username = request.form['usernamet']
			otpe = request.form['otp']
			if session['otp'] == otpe :
				return render_template('forgotpass.html', d = 3, username = username)
			else :
				flash("Invalid OTP Please Write Valid OTP!!")
				return render_template('forgotpass.html', d = 2, username = username)	
		elif d == '3' :
			username = request.form['usernamet']
			pwd = request.form['pass']
			rpwd = request.form['r_pass']
			cur = mysql.connection.cursor()
			query = "UPDATE USERINFO SET PASSWORD = '%s' WHERE USERNAME = '%s'"%(pwd, username)
			cur.execute(query)
			mysql.connection.commit()
			cur.close()
			session.pop('otp', None)
			session.pop('_flashes', None)
			flash("Password  Updated Successfully!!")
			return redirect(url_for('login'))
	return render_template('forgotpass.html', d = 1)

@app.route('/searchhotel', methods = ['GET', 'POST'])
def searchhotel() :
	if request.method == 'POST' :
		search = request.form['search']
		depart = request.form['depart']
		returnd = request.form['return']
		if depart == "" or returnd == "" :
			flash("Please Select Date!!")
			return redirect(url_for('dashboard'))
		departdate = depart.split("-")
		returndate = returnd.split("-")
		day = days(departdate, returndate)
		if day < 0 :
 			flash("Selected Dates are Invalid!!!")
 			return redirect(url_for('dashboard'))
		choiceperson = request.form['choices-single-defaul']
		searchdata = []
		searchdata.append(depart)
		searchdata.append(returnd)
		searchdata.append(choiceperson)
		cur = mysql.connection.cursor()
		query = "SELECT * FROM HOTELS WHERE CITY = '%s'"%(search)
		data = cur.execute(query)
		data = cur.fetchall()
		if data is None :
			flash("Hotel Not Found Enter City Correctly!!")
			if 'loggedin' in session :
				return redirect(url_for('dashboard'))
			else :
				return redirect(url_for('index'))
		else :
			if 'loggedin' in session :
				user = session['user']
				cur = mysql.connection.cursor()
				query =	"SELECT USERROLE FROM USERINFO WHERE USERNAME = '%s'"%(user)
				cur.execute(query)
				userrole = cur.fetchone()
				cur.close()
				return render_template('dashboard.html', data = data, searchdata = searchdata, userrole = userrole[0])
			else :
				return render_template('index.html', data = data)
	if 'loggedin' in session :
		return redirect(url_for('dashboard'))
	else :
		return redirect(url_for('index'))

@app.route('/addhotel', methods = ['GET', 'POST'])
def addhotel() :
	if request.method == 'POST' :
		hotelname = request.form['hotelname']
		address = request.form['address']
		email = request.form['email']
		mobile = request.form['mobile']
		price = request.form['price']
		wifi = request.form['wifi']
		ac = request.form['ac']
		pool = request.form['pool']
		spa = request.form['spa']
		parking = request.form['parking']
		restaurant = request.form['restaurant']
		city = request.form['city']
		file = request.files['pic']
		filename = secure_filename(file.filename)
		filename = hotelname + ".jpg"
		pic = str(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		try :
			query = '''CREATE TABLE HOTELS
			(HOTEL_ID INT(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
			HOTEL_NAME TEXT NOT NULL,
			ADDRESS TEXT NOT NULL,
			EMAIL TEXT NOT NULL,
			MOBILE TEXT NOT NULL,
			PRICE INT(11) NOT NULL,
			IMAGE TEXT NOT NULL,
			WIFI TEXT NOT NULL,
			AC TEXT NOT NULL,
			POOL TEXT NOT NULL,
			SPA TEXT NOT NULL,
			PARKING TEXT NOT NULL,
			RESTAURANT TEXT NOT NULL,
			CITY TEXT NOT NULL)'''
			cur = mysql.connection.cursor()
			cur.execute(query)
			mysql.connection.commit()
			cur.close()
		except:
			mysql.connection.rollback()
			cur.close()
		try :
			cur = mysql.connection.cursor()
			query = "INSERT INTO HOTELS(HOTEL_NAME,ADDRESS,EMAIL,MOBILE,PRICE,IMAGE,WIFI,AC,POOL,SPA,PARKING,RESTAURANT,CITY) VALUES('%s','%s','%s','%s',%d,'%s','%s','%s','%s','%s','%s','%s','%s')"%(hotelname,address,email,mobile,int(price),pic,wifi,ac,pool,spa,parking,restaurant,city)
			cur.execute(query)
			mysql.connection.commit()
			cur.close()
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		except Exception as e :
			mysql.connection.rollback()
			cur.close()
			flash(str(e))
			return redirect(url_for('addhotel'))
	if 'loggedin' in session :
		if session['userrole'] == 'admin' :
			return render_template('addhotel.html')
		return redirect(url_for('dashboard'))
	return redirect(url_for('index'))

@app.route('/booknow', methods = ['GET', 'POST'])
def booknow() :
	if 'printed' in session :
		session.pop('printed', None)
		return redirect(url_for('dashboard'))
	if request.method == 'POST' :
 		if 'loggedin' in session :
 			hotelid = request.form['hotelid']
 			depart = request.form['depart']
 			returnd = request.form['returnd']
 			person = request.form['person']
 			departdate = depart.split("-")
 			returndate = returnd.split("-")
 			depart = departdate[2] + "-" +departdate[1] + "-" +departdate[0]
 			returnd = returndate[2] + "-" +returndate[1] + "-" +returndate[0]
 			day = days(departdate, returndate)
 			if day == 0 :
 				day = 1
 			cur = mysql.connection.cursor()
 			query = "SELECT HOTEL_NAME,PRICE,IMAGE FROM HOTELS WHERE HOTEL_ID = %d"%(int(hotelid))
 			cur.execute(query)
 			hotel = cur.fetchone()
 			data = [hotelid, hotel[0], int(day*hotel[1]), hotel[2], depart, returnd, person]
 			return render_template('booknow.html', data = data)
 		flash("Login First")
 		return redirect(url_for('login'))
	if 'loggedin' in session :
 		return redirect(url_for('dashboard'))
	return redirect(url_for('login'))

@app.route('/invoice', methods = ['GET', 'POST'])
def invoice() :
	if request.method == 'POST' :
		if 'loggedin' in session :
			hotelid = request.form['hotelid']
			checkin = request.form['checkin']
			checkout = request.form['checkout']
			total = request.form['total']
			person = request.form['person']
			user = session['user']
			today = str(date.today())
			tdate = today.split("-")
			today = tdate[2] + "-" +tdate[1] + "-" +tdate[0]
			try :
				query = '''CREATE TABLE INVOICE
				(INVOICE_ID INT(11) PRIMARY KEY NOT NULL AUTO_INCREMENT,
				HOTEL_NAME TEXT NOT NOT NULL,
				USERNAME TEXT NOT NULL,
				HOTEL_ID INT(11) NOT NULL,
				BOOKING_DATE TEXT NOT NULL,
				CHECKIN TEXT NOT NULL,
				CHECKOUT TEXT NOT NULL,
				PERSON TEXT NOT NULL,
				TOTAL TEXT NOT NULL)'''
				cur = mysql.connection.cursor()
				cur.execute(query)
				mysql.connection.commit()
				cur.close()
			except:
				mysql.connection.rollback()
				cur.close()
			cur = mysql.connection.cursor()
			query = "SELECT NAME,EMAIL FROM USERINFO WHERE USERNAME = '%s'"%(user)
			cur.execute(query)
			userdata = cur.fetchone()
			query = "SELECT HOTEL_NAME,ADDRESS FROM HOTELS WHERE HOTEL_ID = %d"%(int(hotelid))
			cur.execute(query)
			hoteldata = cur.fetchone()
			try :
				query = "INSERT INTO INVOICE(USERNAME,HOTEL_ID,BOOKING_DATE,CHECKIN,CHECKOUT,PERSON,TOTAL) VALUES('%s',%d,'%s','%s','%s','%s','%s')"%(user,int(hotelid),today,checkin,checkout,person,total)
				cur.execute(query)
				mysql.connection.commit()
				query = "SELECT INVOICE_ID FROM INVOICE ORDER BY INVOICE_ID DESC LIMIT 1"
				cur.execute(query)
				invoice_id = cur.fetchone()
				cur.close()
			except Exception as e :
				mysql.connection.rollback()
				cur.close()
			data = [userdata[0], userdata[1], invoice_id[0], today, hoteldata[1], hoteldata[0], checkin, checkout, person, total]
			rendered = render_template('invoice.html', data = data)
			pdf = pdfkit.from_string(rendered, False, configuration = config)
			response = make_response(pdf)
			response.headers['Content-Type'] = 'application/pdf'
			response.headers['Content-Disposition'] = 'attachment; filename = invoice.pdf'
			session['printed'] = True
			return response
	return redirect(url_for('index'))
@app.route("/myrooms")
def myrooms() :
	if 'loggedin' in session :
		username = session['user']
		query = "SELECT INVOICE_ID, HOTEL_ID, BOOKING_DATE, CHECKIN, CHECKOUT FROM INVOICE WHERE USERNAME = '%s'"%(username)
		cur = mysql.connection.cursor()
		cur.execute(query)
		invoicedata = cur.fetchall()
		if invoicedata is None :
			return redirect(url_for('dashboard'))
		data = []
		j = 0
		for i in invoicedata :
			query = "SELECT * FROM HOTELS WHERE HOTEL_ID = %d"%(int(i[1]))
			cur.execute(query)
			hoteldata = cur.fetchone()
			data.append(list(i))
			data[j].extend(list(hoteldata))
			j = j + 1 
		return render_template('myrooms.html', data = data, userrole = session['userrole'])
	return redirect(url_for('index'))

@app.route('/cancle', methods = ['GET', 'POST'])
def cancle():
	if request.method == 'POST' :
		if 'loggedin' in session :
			invoiceid = request.form['invoiceid']
			query = "SELECT CHECKIN FROM INVOICE WHERE INVOICE_ID = %d"%(int(invoiceid))
			cur = mysql.connection.cursor()
			cur.execute(query)
			invoicedata = cur.fetchone()
			if invoicedata is None :
				return redirect(url_for('myrooms'))
			date = str(invoicedata[0])
			date = date.split("-")
			dt = []
			dt.append(date[2])
			dt.append(date[1])
			dt.append(date[0])
			d = cancledays(dt)
			if d <= 0 :
				flash("You can't cancle this room!!")
				return redirect(url_for('myrooms'))
			query = "DELETE FROM INVOICE WHERE INVOICE_ID = %d"%(int(invoiceid))
			cur.execute(query)
			mysql.connection.commit()
			cur.close()
			flash("Your room is cancled Successfully!!")
			return redirect(url_for('myrooms'))
	return redirect(url_for('index'))

if __name__ == '__main__' :
	app.debug = True
	app.run()
	app.run(debug = True)
