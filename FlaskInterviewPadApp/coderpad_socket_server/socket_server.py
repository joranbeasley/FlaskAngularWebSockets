import random
import string
import traceback

import sys

import time

import datetime
from flask import current_app, Flask, request
from flask_login import current_user
from flask_socketio import join_room, leave_room, SocketIO, disconnect, emit

from models import User, Room, db, Invites, ActiveRoomUser
from coderpad_socket_server.room_util import get_latest_prog, update_latest_prog
import logging
logging.basicConfig(level=logging.WARN)
log = logging.getLogger('coderpad-socketio')
# logN = logging.getLogger('NOTIFY')
def emit2(event,*args,**kwargs):
    # if kwargs.get('broadcast',True) is False:
    #     logN.info("EMIT: %r => %s %s"%(event,args,kwargs))
    # else:
    #     logB.info("EMIT: %r => %s %s"%(event,args,kwargs))
    emit(event,*args,**kwargs)
class ActiveUsers:
    active_users_by_room={}
    active_users_by_sid={}
    active_sids_by_room = {}
    active_emails_by_room = {}
    active_sids = set()
    pending_sids = set()
    @staticmethod
    def close_all_open(delay=0.5):
        time.sleep(delay)
        try:
            ActiveRoomUser.query.filter_by(session_ended=None).update(dict(session_ended=datetime.datetime.now()))
            db.session.commit()
        except:
            traceback.print_exc()
            print("???!!!!!")
        else:
            print("OK CLEARED!")



    @staticmethod
    def user_connected():
        ActiveUsers.pending_sids.add(request.sid)
    @staticmethod
    def get_room_users(room_name,include_inactive=True):
        inactive_users = []
        room = Room.query.filter_by(room_name=room_name).order_by('-id').first()
        if include_inactive:
            inactive_users = [invite.to_user().to_dict() for invite in room.invited_users if invite.email not in ActiveUsers.active_emails_by_room.setdefault(room_name,set())]

        active_users =  ActiveRoomUser.query.filter_by(room_id=room.id,session_ended=None).all()

        return active_users + inactive_users


    @staticmethod
    def user_is_away():
        if request.sid not in ActiveUsers.active_sids:
            raise Exception("User is not active")
        ActiveUsers.get_by_sid(request.sid)['status'] = 'inactive'
    @staticmethod
    def user_is_back():
        if request.sid not in ActiveUsers.active_sids:
            raise Exception("User is not active")
        ActiveUsers.get_by_sid(request.sid)['status'] = 'active'
    @staticmethod
    def user_disconnected():
        if request.sid in ActiveUsers.pending_sids:
            ActiveUsers.pending_sids.remove(request.sid)
            print("REMOVED PENDING USER")
        active_users = ActiveRoomUser.query.filter_by(sid=request.sid,session_ended=None).all()
        userData = {}
        for active_user in active_users:
            userData['username'] = active_user.nickname
            userData.setdefault('rooms',[]).append(active_user.room.room_name)
            active_user.session_ended = datetime.datetime.now()
        db.session.commit()
        print("OK REMOVED USER",userData)
        return userData

    @staticmethod
    def sids_in_room(room_id):
        sid_list = ActiveRoomUser.query.with_entities(ActiveRoomUser.sid).filter_by(room_id=room_id).all()
        if sid_list:
            sid_list = list(zip(*sid_list))[0]
        return set(sid_list)
    @staticmethod
    def join_room(room_name):
        my_sid = request.sid
        room = Room.query.filter_by(room_name=room_name, is_active=True).first()
        if my_sid in ActiveUsers.sids_in_room(room.id):
            raise Exception("You already are in this room")
        if my_sid not in ActiveUsers.pending_sids:
            raise Exception("This user is unexpected...")
        else:
            ActiveUsers.pending_sids.remove(my_sid)
        ActiveRoomUser.join_room(room)
        # log.info("ADDED USER %s TO %s"%(userDataDict,room_name))


    @staticmethod
    def is_authenticated(room_name):
        if getattr(current_user,'is_admin',False):return True
        room = Room.query.filter_by(room_name=room_name,is_active=True).first()
        if not room:
            return False
        return ActiveRoomUser.query.filter_by(room_id=room.id,sid=request.sid,session_ended=None).count()>0
    @staticmethod
    def require_authentication(fn):
        def _inner_fn(*args,**kwargs):
            if not request.sid in ActiveUsers.active_sids:
                disconnect()
            return fn(*args,**kwargs)
        return _inner_fn
socketio = SocketIO()
@socketio.on('connect')
def on_connect():
    print( "OK CONNECTED:",request.sid )
    ActiveUsers.user_connected()
@socketio.on("disconnect")
def on_disconnect():
    userData = ActiveUsers.user_disconnected()
    if not userData:
        print("User had not finished connecting?")
    for room_name in userData['rooms']:
        emit('user_left', {'username': userData['username']}, room=room_name)


@socketio.on('join')
def on_join(data):
    log.info("JOIN:%s - %s"%(data,request.sid))
    try:
        user = User.query.filter_by(id=current_user.id).first()
    except:
        user = None

    username = data['username']
    room_name = data['room']
    if not user:
        active_room_users = []
        room = Room(room_name=room_name)
    else:
        room = Room.query.filter_by(room_name=room_name).first()
        if not room:
            disconnect()
        # if hasattr(current_user,'id') and isinstance(current_user._get_current_object(),User):
        current_user.sid = request.sid
        #     User.query.filter_by(id=current_user.id).update(dict(sid = request.sid))
        #     db.session.commit()
        if room.invite_only:
            if current_user.is_anonymous:
                disconnect()
            username = current_user.nickname
            try:
                user = User.query.filter_by(id=current_user.id).first()
            except:
                user = None
            if not user:
                invite = Invites.get_my_invitation()
                user = invite.to_user()
            user.sid=request.sid
            db.session.commit()
            if room.invite_only and not room.verify_allowed():
                print("User %s is not invited to room %s"%(current_user,room))
                disconnect()
        active_room_users = ActiveUsers.get_room_users(room.room_name)




    join_room(room.room_name)
    # print("C:",current_user)
    if not user or current_user.is_anonymous:
        ActiveUsers.join_room(room_name)#,{'username':username,'id':random.choice(string.ascii_uppercase),"sid":request.sid,"is_AFK":False})

    else:
        ActiveUsers.join_room(room_name)#,current_user.to_dict())
    emit2('user_list', {'active_users': active_room_users,
                        'program_text': get_latest_prog(room.room_name)}, broadcast=False)
    emit2('user_joined',{'username':username}, room=room_name)


@socketio.on('run')
@ActiveUsers.require_authentication
def on_run(data):
    emit2('user_run', {'username': data['username']}, room=data['room'])

@socketio.on('speak')
@ActiveUsers.require_authentication
def on_speech(data):
    print("SPEAK!",data)
    data['message'] = data['message'].replace("\"","&quot;").replace("'","&#39;")
    emit('user_speech', data, room=data['room_details']['room'])

@socketio.on('leave')
def on_leave(data):
    print("Graceful shutdown?")

@socketio.on("focus_lost")
def on_lost_focus(data):
    room_name = data['room_details']['room']
    room = Room.query.filter_by(room_name=room_name).first()
    if not room or not room.owner.sid:
        return
    user = User.query.filter_by(username=data['room_details']['username'], is_active='TRUE').first()
    if user:
        data['user_id'] = user.id
        user.is_AFK = True
        db.session.commit()
    data['action'] = "LOST"
    # print 'focus_update', data, room.owner.sid
    emit2('focus_update', data, room=room.owner.sid)
@socketio.on("focus_gained")
def on_focus_gained(data):
    room_name = data['room_details']['room']
    room = Room.query.filter_by(room_name=room_name).first()
    data['action']="GAINED"
    if room and room.owner.sid:
        user = User.query.filter_by(username=data['room_details']['username'],is_active='TRUE').first()
        if user:
            data['user_id'] = user.id
            user.is_AFK = False
            db.session.commit()
        emit2('focus_update', data, room=room.owner.sid)

@socketio.on('message')
def handle_message(message):
    print('received message.. not sure how or why: ' + message)

@socketio.on("sync_request")
@ActiveUsers.require_authentication
def request_sync(user_details):
    room_name = user_details['room_details']['room']
    if not ActiveUsers.is_authenticated(room_name):
        disconnect()
    room = Room.query.filter_by(room_name=room_name).first()
    if not room or not room.is_invited(current_user):
        disconnect()
    payload = {'program_text':get_latest_prog(room_name)}
    if hasattr(current_user,'is_admin') and current_user.is_admin:
        payload['active_users']=ActiveUsers.get_room_users(room_name)
        print("ACTIVE USERS:", payload['active_users'])
        active_ids = {u['id'] for u in payload['active_users']}
        payload['all_users']=[u.to_dict() for u in room.room_members()]
        for user in payload['all_users']:
            user['online'] = user['id'] in active_ids
    emit2('sync_result',payload)

def handle_change_message(data):
    room = data['room_details']['room']
    current_text_lines = get_latest_prog(room).splitlines()
    start_line = data['start']['row']
    end_line = data['end']['row']
    try:
        end_line_text = current_text_lines[end_line]
    except IndexError:
        end_line_text = ""
    try:
        start_line_text = current_text_lines[start_line]
    except:
        start_line_text=""
    if (data['action'] == "insert"):
        print("INSERT?",data)
        line0 = data['lines'].pop(0)
        lhs = start_line_text[0:data['start']['column']]
        rhs = start_line_text[data['start']['column']:]
        if (not data['lines']):
            try:
                current_text_lines[start_line] = lhs + line0 + rhs
            except IndexError:
                current_text_lines.append(lhs + line0 + rhs)
        else:
            current_text_lines[start_line] = lhs + line0;
            lineN = data['lines'].pop()
            data['lines'].append(lineN+rhs)
            current_text_lines[start_line + 1:start_line + 1] = data['lines']



    elif (data['action'] == "remove"):
        try:
            lhs = start_line_text[0:data['start']['column']]
        except:
            lhs = ""
        try:
            rhs = end_line_text[data['end']['column']:]
        except IndexError:
            rhs = ""
        new_line = lhs + rhs
        current_text_lines[start_line:end_line+1] = [new_line,]
    update_latest_prog(room,"\n".join(current_text_lines))

@socketio.on('on_editor_change')
@ActiveUsers.require_authentication
def handle_editor_change(message):
    socketio = current_app.extensions['socketio']
    room = message['room_details']['room']
    if not ActiveUsers.is_authenticated(room):
        disconnect()
    emit2('editor_change_event',message, room=room)
    handle_change_message(message)

def init_app(app,**kwargs):
    ActiveUsers.close_all_open(0.1)
    socketio.init_app(app,**kwargs)
    return socketio
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("host",nargs="?")
    parser.add_argument("port",nargs="?")
    parser.add_argument("-p","--portnum",default="5678")
    args = parser.parse_args()
    if not args.host:
        args.host = "127.0.0.1"
    args.port = args.port or args.portnum
    print("Serving Sockets @ ws://%s:%s"%(args.host,args.port))
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    init_app(app)
    socketio.run(app,args.host,args.port)