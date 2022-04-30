from flask import Flask, request , session , redirect
from flask import render_template
from flask import current_app as app
from application.models import *
from application.database import db
from datetime import datetime
import pytz    
import matplotlib.pyplot as plt
import numpy as np

@app.route("/", methods = ["GET", "POST" ])
def home(): 
	if request.method == "GET":  
		if "username" in session:
			return redirect("/dashboard")
		else:
			return render_template("homepage.html")

	elif request.method == "POST":
		username =  request.form.get("username")
		password = request.form.get("password", None)
		usernamexist = db.session.query(User).filter(User.user_id == username).first()
		if usernamexist:
			if (usernamexist.user_id == username and usernamexist.password == password):
				session['username'] = username
				return redirect("/dashboard")
			else:
				return render_template("homepage.html", message = "incorrect credentials")
		else:
			return render_template("homepage.html", message = "Username does not exist")
    				

@app.route("/signup", methods = ["GET", "POST"])
def signup():
	if request.method == "GET":
		if "username" in session:
			return render_template("loginalready.html")
		else:	
			return render_template("signuppage.html")

	elif request.method == "POST":
		username = request.form.get("username")
		password = request.form.get("password", None)
		usernamexist = db.session.query(User).filter(User.user_id == username).first()
		if usernamexist:
    			return render_template("signuppage.html", message = "Username already exist. Please try using different username")
		else:
			newuser = User(user_id = username , password = password)
			db.session.add(newuser)
			db.session.commit()
			session['username'] = username
			return redirect("/")


@app.route("/dashboard", methods = ["GET"])
def dashboard():
		if request.method == "GET":
			if "username" in session.keys():
				alltrackers = db.session.query(Tracker).filter(Tracker.user_id == session["username"]).all()
				all_logs = []
				for i in alltrackers:
					all_logs = (db.session.query(TrackerLog).filter(TrackerLog.tracker_id == i.tracker_id).all())+ all_logs
					print(all_logs)
				return render_template("dashboard.html", trackers = alltrackers, four_logs=all_logs[:-4:-1])
			else:
				return redirect("/")
		else:
			return redirect("/")	


@app.route("/logout")
def logout():   
	session.pop("username", None)
	return redirect('/')


@app.route("/tracker/add", methods=['POST'])
def addtracker():
		name =  request.form.get("trackername")
		description =  request.form.get("trackerdescription")
		type =  request.form.get("trackertype")
		setting =  request.form.get("trackersettings")
		alltrackers = db.session.query(Tracker).filter(Tracker.user_id == session["username"]).all()
		alltrackername = db.session.query(Tracker.tracker_name).filter(Tracker.user_id == session["username"]).all()
		for i in alltrackername:
			if (i[0] == name):
				m = 'This tracker name already exist'
				return render_template('dashboard.html', message = m, trackers = alltrackers)	
		if (name == '' or type == ''):
			m = 'Tracker Name or Type should not be empty'	
			return render_template('dashboard.html', message = m)	
		trackertoadd = Tracker(tracker_name = name , tracker_description = description , tracker_type = type , tracker_settings = setting , user_id = session['username'])
		db.session.add(trackertoadd)
		db.session.commit()
		return redirect('/dashboard')

@app.route("/tracker/<trackerid>", methods = ["GET"])
def trackerinfo(trackerid):
	tracker = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid).first()
	alltrackerlog = db.session.query(TrackerLog).filter(TrackerLog.tracker_id == trackerid).all()
	if alltrackerlog == []:
		m = "No Logs found"
		return(render_template('trackerinfo.html', T_ = tracker, all_log = alltrackerlog, message = m))
	else:
		plot_grapher(tracker.tracker_type, alltrackerlog)
		return render_template('trackerinfo.html', T_ = tracker, all_log = alltrackerlog)

@app.route("/tracker/<trackerid>/delete", methods = ["GET"])
def deletetracker(trackerid):
	trackertodelete = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid).first()
	alltrackerlog = db.session.query(TrackerLog).filter(TrackerLog.tracker_id == trackerid).all()
	for log in alltrackerlog:
		db.session.delete(log)
	db.session.delete(trackertodelete)
	db.session.commit()
	return redirect('/dashboard')

@app.route("/tracker/<trackerid>/edit", methods = ["GET","POST"])
def edittracker(trackerid):
	if request.method == 'GET':
		trackertoedit = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid).first()
		return render_template("edittracker.html", tracker = trackertoedit)
	if request.method == 'POST':	
		trackertoedit = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid).first()
		name = request.form.get("trackername")
		type = request.form.get("trackertype")
		settings = request.form.get("trackersettings")
		description = request.form.get("trackerdescription")
		if name:
			alltrackername = db.session.query(Tracker.tracker_name).filter(Tracker.user_id == session["username"]).all()
			for i in alltrackername:
				if(i[0] == name):
					m = 'This tracker name already exist'
					return render_template('edittracker.html', message = m)	
			trackertoedit.tracker_name = name
		if type:
			trackertoedit.tracker_type = type
		if settings:
			trackertoedit.tracker_settings = settings
		if description:
			trackertoedit.tracker_description = description
		db.session.commit()
		t = "/tracker/"+str(trackerid)
		return redirect(t)



@app.route("/<trackerid>/log/add", methods = ["POST"])
def addlog(trackerid):
	value = request.form.get("logvalue") 
	note = request.form.get("lognote")
	tracker = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid).first()
	if not value:
		m = 'value cannot be empty'
		alltrackerlog = db.session.query(TrackerLog).filter(TrackerLog.tracker_id == trackerid).all()
		return render_template('trackerinfo.html', T_ = tracker, all_log = alltrackerlog, message = m)
	#value = str(value) +" " +tracker.tracker_type		
	tz_AS = pytz.timezone('Asia/Kolkata')   
	ct = datetime.now(tz_AS).strftime("%d-%m-%Y, %H:%M:%S")
	logtoadd = TrackerLog( log_value = value, log_note = note, tracker_id = trackerid , time_stamp = ct)
	db.session.add(logtoadd)
	db.session.commit()
	return redirect(f"/tracker/{trackerid}")

@app.route("/log/<log_id>/delete", methods = ["GET"])
def deletelog(log_id):
	logtoedit = db.session.query(TrackerLog).filter(TrackerLog.log_id == log_id).first()
	tracker_id = logtoedit.tracker_id	
	db.session.delete(logtoedit)
	db.session.commit()
	return redirect(f"/tracker/{tracker_id}")

@app.route("/log/<log_id>/edit", methods = ["GET","POST"])
def editlog(log_id):
	logtoedit = db.session.query(TrackerLog).filter(TrackerLog.log_id == log_id).first()
	tracker_id = logtoedit.tracker_id	
	tracker = db.session.query(Tracker).filter(Tracker.tracker_id == tracker_id).first()
	if request.method == "GET":
		return render_template("editlog.html",T_ = tracker, log = logtoedit)
	if request.method == "POST":
		value = request.form.get("logvalue")
		note = request.form.get("lognote")
		timestamp = request.form.get("timestamp")
		if value:
			if value.strip() == "":
				m = 'value cannot be empty'
				alltrackerlog = db.session.query(TrackerLog).filter(TrackerLog.tracker_id == tracker_id).all()
				return render_template('editlog.html', T_ = tracker, log =logtoedit, message = m)

			logtoedit.log_value = value
		if note:
			logtoedit.log_note = note
		if timestamp:
			print(timestamp)
			timestamp_ = timestamp[8:10]+"-"+timestamp[5:7]+"-"+timestamp[0:4]+", "+timestamp[11:]+":00" 
			logtoedit.time_stamp = timestamp_
		db.session.commit()
		return redirect(f"/tracker/{tracker_id}")


def plot_grapher(_type , all_log):
	import matplotlib.pyplot as plt
	x, y = [], []
	for i in all_log:
		x.append(i.time_stamp[0:10])
		y.append(i.log_value)
	plt.plot(x, y)
	plt.xlabel('time')
	plt.ylabel(_type)
	plt.xticks(rotation=25)
	plt.title("Tracker Details")
	plt.savefig('static/my_plot.png')
	plt.close()