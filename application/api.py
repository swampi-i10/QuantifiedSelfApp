from flask_restful import Resource, Api, request
from flask_restful import fields, marshal_with
from flask_restful import reqparse
from application.validation import SchemaValidationError, BusinessValidationError, NotFoundError
from application.models import *
from application.database import db
from flask import current_app as app
import uuid,jwt
from datetime import datetime, timedelta
from functools import wraps
import werkzeug
from flask import abort

tracker_parser = reqparse.RequestParser()
tracker_parser.add_argument('tracker_name')
tracker_parser.add_argument('tracker_description')
tracker_parser.add_argument('tracker_type')
tracker_parser.add_argument('tracker_settings')

log_parser = reqparse.RequestParser()
log_parser.add_argument('tracker_id')
log_parser.add_argument('log_value')
log_parser.add_argument('log_note')
log_parser.add_argument('time_stamp')

user_parser = reqparse.RequestParser()
user_parser.add_argument('user_id')
user_parser.add_argument('password')

resource_fields_tracker = {
    'tracker_id':   fields.Integer,
    'tracker_name':    fields.String,
    'tracker_description':    fields.String,
    'tracker_type':    fields.String,
    'tracker_settings':    fields.String
}

resource_fields_log = {
    'log_id':   fields.Integer,
    'log_value':    fields.String,
    'log_note':    fields.String,
    'time_stamp':    fields.String
}

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'token' in request.headers:
            token = request.headers['token']
        # return 401 if token is not passed
        if not token:
            raise SchemaValidationError( 405 , "BE1011","token cannot be found")
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user_id = data['user_id']
        except:
            raise SchemaValidationError( 405 , "BE1010",'Token is invalid !!')
        # returns the current logged in users contex to the routes
        return  f(current_user_id, *args, **kwargs)
    return decorated

class TrackerAPI(Resource):
    @marshal_with(resource_fields_tracker)
    @token_required
    def get(self, userid, trackerid):
        tracker = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid).first()
        if tracker is None:
            raise NotFoundError(status_code=404)
        return tracker

    @token_required
    def delete(self, userid, trackerid):
        trackertodelete = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid).first()
        if trackertodelete is None:
            raise NotFoundError(status_code=404)
        alltrackerlog = db.session.query(TrackerLog).filter(TrackerLog.tracker_id == trackerid).all()
        if alltrackerlog is not None:
            for log in alltrackerlog:
                db.session.delete(log)
        db.session.delete(trackertodelete)
        db.session.commit()
        return {'Status': 'Deleted'}        

    @marshal_with(resource_fields_tracker)
    @token_required
    def post(self, userid):
        args = tracker_parser.parse_args()
        name = args.get("tracker_name", None)
        description = args.get("tracker_description", None)
        type = args.get("tracker_type", None)
        setting = args.get("tracker_settings", None)
        if name != None or name != "":
            if type != None or type !="":
                alltrackername = db.session.query(Tracker.tracker_name).all() #.filter(Tracker.user_id == session["username"]).all()
                for i in alltrackername:
                    if (i[0] == name):
                        return SchemaValidationError(405 , "BE1003", "tracker name already exist")
                trackertoadd = Tracker(tracker_name = name , tracker_description = description , tracker_type = type , tracker_settings = setting , user_id = 'testing')
                db.session.add(trackertoadd)
                db.session.commit()
            else:
                raise SchemaValidationError( 405 , "BE1001", "tracker type should not be none")
        else:
            raise SchemaValidationError( 405 , "BE1002", "tracker name should not be none")
        return trackertoadd

    @marshal_with(resource_fields_tracker)
    @token_required
    def put(self, userid, trackerid):
        args = tracker_parser.parse_args()
        name = args.get("tracker_name", None)
        description = args.get("tracker_description", None)
        type = args.get("tracker_type", None)
        setting = args.get("tracker_settings", None)

        if name is not None:
            if type is not None:
                alltrackername = db.session.query(Tracker.tracker_name).all()#.filter(Tracker.user_id == session["username"]).all()
                for i in alltrackername:
                    if (i[0] == name):
                        return SchemaValidationError(405 , "BE1003", "tracker name already exist")
                trackertoedit = db.session.query(Tracker).filter(Tracker.tracker_id == trackerid)
                trackertoedit['tracker_name'] = name
                trackertoedit['tracker_description'] =  description
                trackertoedit['tracker_type'] = type
                trackertoedit['tracker_settings'] = setting
                db.session.commit()
            else:
                return SchemaValidationError( 405 , "BE1001", "tracker type should not be none")
        else:
            return SchemaValidationError( 405 , "BE1002", "tracker name should not be none")
        return trackertoedit    

class LogAPI(Resource):
    @marshal_with(resource_fields_log)
    @token_required
    def get(self, userid, logid):
        log = db.session.query(TrackerLog).filter(TrackerLog.log_id == logid).first()
        if log is None:
            raise NotFoundError(status_code=404)
        return log

    @token_required
    def delete(self, userid, logid):
        logtodelete = db.session.query(TrackerLog).filter(TrackerLog.log_id == logid).first()
        if logtodelete is None:
            raise NotFoundError(status_code=404)
        db.session.delete(logtodelete)
        db.session.commit()
        return {'Status': 'Deleted'}        

    @marshal_with(resource_fields_log)
    @token_required
    def post(self, userid):
        args = log_parser.parse_args()
        tid = args.get("tracker_id", None)
        value = args.get("log_value", None)
        note = args.get("log_note", None)
        timestamp = args.get("time_stamp", None)
        if value != None or value != "":
                logtoadd = TrackerLog(tracker_id = tid,log_value = value, log_note = note, time_stamp = timestamp)
                db.session.add(logtoadd)
                db.session.commit()
        else:
            raise SchemaValidationError( 405 , "BE1002", "tracker name should not be none")
        return logtoadd                             

class UserAPI(Resource):
    @token_required
    def get(self, userid):
        # creates dictionary of form data
        args = user_parser.parse_args()
        uid = args.get("user_id", None)
        password = args.get("password", None)
        if not uid or not password or uid == "" or password == "":
            # returns 401 if any email or / and password is missing
            raise SchemaValidationError( 403 , "BE1007", "user_id and password are required")
    
        user = User.query.filter_by(user_id = uid).first()
        if not user:
            # returns 401 if user does not exist
            raise SchemaValidationError( 403 , "BE1008", "User Does not Exist")
        if user.password == password:
            # generates the JWT Token
            token = jwt.encode({ 'user_id': user.user_id,'exp' : datetime.utcnow() + timedelta(minutes = 30)}, app.config['SECRET_KEY'])
            return ({'token' : token.decode('UTF-8')}, 201)
        # returns 403 if password is wrong
        raise SchemaValidationError( 403 , "BE1009", "Wrong password")
   
    @token_required
    def post(self, userid):
            args = user_parser.parse_args()
            uid = args.get("user_id", None)
            password = args.get("password", None)
            if not uid or uid == "":
                # returns 401 if any email or / and password is missing
                raise SchemaValidationError( 403 , "BE1007", "user_id is required")
            userexist = User.query.filter_by(user_id = uid).first()
            if userexist:
                raise SchemaValidationError( 403 , "BE1006", "user_id already exist. try different")
            usertoadd = User(user_id = uid , password = password)
            db.session.add(usertoadd)
            db.session.commit()   
            return {"status" : "User Created"}  

