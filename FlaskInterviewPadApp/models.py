import hashlib
import json
import random
import threading

import time

import datetime

from flask import request, session
from flask_login import current_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
login_manager = LoginManager()
def total_seconds(dt_object):
    try:
        return dt_object.total_seconds()
    except:
        return dt_object.seconds + 3600*24*dt_object.days
def init_app(app,db_uri=None):
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or app.config.get('SQLALCHEMY_DATABASE_URI','sqlite:///./test.db')
    db.app = app
    db.init_app(db.app)
    login_manager.init_app(app)

    # threading.Thread(target=clear_active_users ).start()

    return db
def user2dict(user,**kwargs):
    return{
        "id": user.id,
        "realname": user.realname,
        "email": user.email,
        "nickname": user.nickname,
        "username": user.nickname,
        "classes":"my_btn" if not getattr(current_user,'is_admin',False) else "my_btn admin"
    }
class InvitedUser:
    realname=None
    email=None
    nickname=None
    sid=None
    is_authenticated=True
    is_anonymous=False
    is_active=True
    is_system_guest = True
    invite_token = None
    def get_id(self):
        return self.email
    def to_dict(self):
        d = user2dict(self)
        d['invite_token'] = self.invite_token
        d['invite_url'] = self.invite_url
        return d
    def get_invite_url(self):
        return "%s/code/%s"%(request.host_url,self.invite_token)
    def __init__(self,invite_token,realname,nickname,email,is_active=True):
        self.realname = realname
        self.invite_token = invite_token
        self.invite_url = self.get_invite_url()
        self.nickname = nickname
        self.email = email
        self.is_active = is_active
    @property
    def id(self):
        return self.realname

class GuestUser(InvitedUser):
    is_authenticated = False
    is_anonymous = True
    def __init__(self, nickname):
        InvitedUser.__init__(self,"<Unknown>", nickname, "guest@openroom.net")

class ActiveRoomUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20))
    email = db.Column(db.String(80))
    room_id = db.Column(db.Integer,db.ForeignKey('room.id'))
    room = db.relationship('Room', backref=db.backref('active_users', lazy=True))
    sid = db.Column(db.String(80))
    is_admin = db.Column(db.Boolean,default=False)
    is_active = db.Column(db.Boolean,default=True)
    state = db.Column(db.String(10),default="active")
    session_started = db.Column(db.DateTime,default=datetime.datetime.now)
    session_ended = db.Column(db.DateTime, default=None,nullable=True)
    def to_dict(self):
        return {
            "email":self.email,
            "room_name":self.room.room_name,
            "nickname":self.nickname,
            "username":self.nickname,
            "state":self.state,
            "is_admin":self.is_admin,
            "session_started":self.session_started.isoformat(),
            "session_ended":self.session_ended.isoformat() if self.session_ended else None,
            "is_active":self.is_active
        }
    @staticmethod
    def leave_room(room=None):
        my_active_users = ActiveRoomUser.query.filter_by(sid=request.sid)
        if room:
            my_active_users = my_active_users.filter_by(room_id=room.id)
        my_active_users.update(session_ended=datetime.datetime.now(),state="disconnected")
        db.session.commit()

    @staticmethod
    def join_room(room):
        last_room = ActiveRoomUser.query.filter_by(room_id=room.id,email=current_user.email).order_by('-id').first()
        if last_room:
            if not last_room.session_ended:
                raise ValueError("User Is Already In this room!")
            else:
                timedelta = datetime.datetime.now() - last_room.session_ended
                if total_seconds(timedelta) < 180:
                    print("Session Restored!")
                    last_room.session_ended = None
                    last_room.state = 'active'
                    last_room.sid = request.sid
                    db.session.commit()
                    return
                else:
                    print("Expired:",total_seconds(timedelta))
                    print("CREATE NEW SESSION")
        is_admin = False
        if current_user.is_authenticated and getattr(current_user,'is_real_user',False):
            is_admin = True
        active_user = ActiveRoomUser(room_id=room.id,
                                     email=current_user.email, nickname=current_user.nickname,
                                     sid=request.sid, is_admin=is_admin)
        db.session.add(active_user)
        print("Session Joined")
        db.session.commit()

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(80),unique=True)
    realname = db.Column(db.String(80),unique=True)
    Xpassword = db.Column(db.String(80))
    token = db.Column(db.String(80))
    pin = db.Column(db.String(80))
    nickname = db.Column(db.String(20))
    sid = db.Column(db.String(50))
    reset_token = db.Column(db.String(80),default=None,nullable=True)
    is_active = db.Column(db.Boolean,default=True)
    is_anonymous=False
    is_real_user=True
    is_admin = True
    def to_dict(self):
        return user2dict(self)
    @property
    def is_authenticated(self):
        return bool(self.id) and self.id == current_user.id
    @staticmethod
    def exchange_token(ident_token):
        invite = Invites.query.filter_by(token_invite=ident_token).first()
        if not invite:
            return False
        session["X-authentication"] = ident_token
        session["X-email"]=invite.email
        session["X-room_id"]=invite.room_id
        return invite.to_user()

    @staticmethod
    def alternate_user_loader():
        invite_tok = session.get('X-authentication', None)
        invite_email = session.get('X-email', None)
        invite_room_id = session.get('X-room_id', None)
        if not invite_tok or not invite_email:
            return None
        invite = Invites.query.filter_by(token_invite=invite_tok,email=invite_email,room_id=invite_room_id).first()
        if not invite:
            return None
        return invite.to_user()
    @staticmethod
    @login_manager.user_loader
    def user_loader(id):
        return User.query.filter_by(id=id).first() or User.alternate_user_loader()



    @classmethod
    def login(cls,username,password):
        print(username,password)
        return User.query.filter_by(email=username,Xpassword=User.pw_enc(password)).first()
    def get_id(self):
        return self.id
    @classmethod
    def pw_enc(cls,pw):
        if not isinstance(pw,bytes):
            pw = pw.encode('latin1')
        return hashlib.sha256(pw).hexdigest()
    def __init__(self,**kwargs):
        if 'Xpassword' in kwargs:
            raise Exception("Do not pass in Xpassword... pass in password")
        if 'password' in kwargs:
            kwargs['Xpassword'] = self.pw_enc(kwargs.pop('password'))
        db.Model.__init__(self,**kwargs)
    @property
    def password(self):
        return "Nope, that wont work!"
    @password.setter
    def set_password(self,password):
        self.Xpassword = self.pw_enc(password)


class ReportCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('my_reports',lazy=True))
    notes = db.Column(db.Text,nullable=True,default="")
    technical_skills = db.Column(db.Integer,nullable=True,default=None)
    willingness_to_learn = db.Column(db.Integer,nullable=True,default=None)
    culture_fit = db.Column(db.Integer,nullable=True,default=None)
    problem_solving = db.Column(db.Integer,nullable=True,default=None)
    creative = db.Column(db.Integer,nullable=True,default=None)
    organized = db.Column(db.Integer,nullable=True,default=None)

class ReviewCandidates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewer = db.relationship('User', backref=db.backref('my_candidates', lazy=True))
    invitee_id = db.Column(db.Integer, db.ForeignKey('invites.id'))
    invitee = db.relationship('Invites', backref=db.backref('my_reviewers', lazy=True))

class Invites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invited_by_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    invited_by = db.relationship('User', backref=db.backref('my_invitees', lazy=True))
    room_id = db.Column(db.Integer,db.ForeignKey('room.id'), nullable=False)
    room = db.relationship('Room', backref=db.backref('invited_users', lazy=True))
    email = db.Column(db.String(80))
    real_name = db.Column(db.String(80))
    nickname = db.Column(db.String(20))
    is_active = db.Column(db.Boolean,default=True)
    token_invite = db.Column(db.String(80))
    def refresh_token(self):
        tmp_token = hashlib.sha256((str(time.time()) + str(random.uniform(-100, 124))).encode('latin1')).hexdigest()
        self.token_invite = tmp_token

    def to_user(self):
        return InvitedUser(invite_token=self.token_invite,nickname=self.nickname,email=self.email,realname=self.real_name)
    def __init__(self,**kwargs):
        tmp_token =hashlib.sha256((str(time.time())+str(random.uniform(-100,124))).encode('latin1')).hexdigest()
        kwargs['token_invite'] = kwargs.pop('token_invite',tmp_token)
        db.Model.__init__(self, **kwargs)
    @classmethod
    def get_my_invitation(cls):
        invite = Invites.query.filter_by(token_invite=invite_tok,email=invite_email).first()
        if not invite:return None
        return invite


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref=db.backref('my_rooms', lazy=True))
    room_name=db.Column(db.String(40))
    invite_only = db.Column(db.Boolean,default=True)
    editing_enabled = db.Column(db.Boolean,default=True)
    is_active = db.Column(db.Boolean,default=True)
    language=db.Column(db.String(20))
    current_text=db.Column(db.Text())
    created=db.Column(db.DateTime,default=datetime.datetime.now)
    active_users = [];
    def get_users_nicknames(self):
        return [self.owner.nickname,] + [u.nickname for u in self.invited_users]
    def is_owner(self):
        return current_user.is_authenticated and current_user.id == self.owner_id
    def verify_allowed(self):
        return current_user.is_authenticated or Invites.query.filter_by(room_id=self.id,email=current_user.email).first()
