from flask import Flask, render_template, url_for, request, redirect, session, flash
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///nushka.db'

db = SQLAlchemy(app)

UPLOAD_FOLDER = os.getcwd()

ALLOWED_EXTENSIONS = {'txt', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class User(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	username= db.Column(db.String(100), unique=True)
	password= db.Column(db.String(100))

	def __init__(self, username, password):
		self.username = username
		self.password = password


	def __repr__(self):
		return "<task %r> " % self.id 

class FileStorage(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(100))
	key=db.Column(db.String(32),unique=True)
	fileURL=db.Column(db.String(1000))
	expTime=db.Column(db.String(100))
	readOnly=db.Column(db.Integer)

	def __repr__(self):
		return "<task %r> " % self.id
db.create_all()

app.secret_key = "hope is a good thing doc" 
##routes goes here

@app.route("/signup",methods=["GET","POST"])
def signup():
	if request.method=="POST":
		username = request.form["username"]
		password= request.form["password"]
		new_user = User(username=username, password=password)
		try:
			db.session.add(new_user)
			db.session.commit()
			return render_template("login.html")
		except:
			return "error!"

	else:
		return render_template('signup.html')


@app.route('/login', methods=["GET","POST"])
def login():
	if request.method=="POST":
		username = request.form["username"]
		password= request.form["password"]
		try:
			user1 = db.session.query(User).filter_by(username=username, password=password).first()
			if(user1 is not None):
				session["user_login"] = True
				session["username"] = username
				return redirect("/upload")
			else:
				return "You are not authorized."
		except:
			return "there was an error in procesing your request"

	else:
		return render_template('login.html')


@app.route("/logout", methods=["GET"])
def logout():
	session["user_login"] = False
	session["username"] = None
	return redirect("/login")

@app.route("/delete", methods=["GET", "POST"])
def deleteFile():
	if(request.method == "POST"):
		key = request.form["key"]
		try:
			db.session.query(FileStorage).filter_by(key=key).delete()
			db.session.commit()
			return redirect("/upload")
		except:
			return "key error"
	else:
		return redirect("/upload")

@app.route("/upload",methods=["GET","POST"])
def upload():
	if(request.method == "POST"):
		err=None
		key=request.form["key"]
		#url=request.form["url"]
		#print(url)
		if 'file' not in request.files:
			return redirect("/upload")
		file = request.files['url']
		# if user does not select file, browser also
		# submit an empty part without filename
		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return redirect("/upload")
		exptime = request.form["expTime"]
		exptime= str(exptime)
		new_file=FileStorage(username=session["username"],key=key,fileURL="hope",expTime=exptime, readOnly=0)

		if db.session.query(FileStorage).filter_by(key=key).first() is None:
			db.session.add(new_file)
			db.session.commit()
			user_files = db.session.query(FileStorage).filter_by(username=session["username"]).all()
			db.session.commit()
			valid_files = []
			present_time = str(datetime.now())
			# print(present_time)
			present_time=present_time[0:10]
			for i in user_files:
				if(i.expTime > present_time):
					valid_files.append(i)
		return render_template('homepage.html',user_files=valid_files)
	else:

		user_files = db.session.query(FileStorage).filter_by(username=session["username"]).all()
		db.session.commit()
		valid_files = []
		present_time = str(datetime.now())
		# print(present_time)
		present_time=present_time[0:10]
		for i in user_files:
			if(i.expTime > present_time):
				valid_files.append(i)
		return render_template("homepage.html",user_files=valid_files)

# @app.route('/',methods=["GET"])
# def index():
# 	if("user_login" in session and session["user_login"] == True):
# 		user_files = db.session.query(FileStorage).filter_by(username=session["username"]).all()
# 		db.session.commit()
# 		return render_template("homepage.html", user_files=user_files)
# 	else:
# 		return "Welcome!"
		

@app.route('/read',methods=["POST"])
def read():
    key = request.form["key"]
    try:
        file = db.session.query(FileStorage).filter_by(key=key).first()
        db.session.commit()
    except:
    	return "Something went wrong."
    result = {key:file.fileURL}
    result=str(result)
    return render_template('read.html',result=result)

@app.route('/admin',methods=["GET"])
def admin():
	all_user = db.session.query(User).all()
	all_files = db.session.query(FileStorage).all()
	return render_template('admin.html', all_user=all_user, all_files=all_files)


if __name__ == '__main__':
	app.run(debug=True)