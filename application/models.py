from .database import db

class User(db.Model):
	__tablename__ = 'user'
	user_id = db.Column(db.String , primary_key = True, unique=True , nullable=False)
	password = db.Column(db.String)
	trackers = db.relationship('Tracker' , backref = 'User')

class Tracker(db.Model):
	__tablename__ = 'tracker'
	tracker_id = db.Column(db.Integer, autoincrement=True, primary_key=True, unique=True , nullable=False)
	tracker_name = db.Column(db.String, nullable=False)
	tracker_description = db.Column(db.String)
	tracker_type = db.Column(db.String, nullable=False)
	tracker_settings = db.Column(db.String)
	user_id = db.Column(db.String, db.ForeignKey('user.user_id'), nullable = False)
	trackerlogs = db.relationship('TrackerLog' , backref = 'Tracker')

class TrackerLog(db.Model):
	__tablename__ = 'trackerlog'
	log_id = db.Column(db.Integer , primary_key = True, autoincrement=True)
	log_value = db.Column(db.String, nullable = False)
	log_note = db.Column(db.String)
	time_stamp = db.Column(db.String, nullable = False)
	tracker_id = db.Column(db.Integer,db.ForeignKey('tracker.tracker_id'), nullable = False)