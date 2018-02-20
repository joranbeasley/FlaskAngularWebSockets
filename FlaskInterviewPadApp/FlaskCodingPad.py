import json
import threading
from base64 import b64encode

import multiprocessing

import time
from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, current_user, login_user

from admin_routes import admin_bp
from coderpad_socket_server.socket_server import init_app as socketio_init_app, ActiveUsers

app = Flask(__name__)
app.secret_key = "\xbe\xefA FliskIt,and a FLASK3t!@\xde\xad"

def create_context(room_instance,**kwargs):
    ng_context = {
        'editor_details': {
            'theme': 'monokai',
            'language': 'python',
            'current_text':room_instance.current_text or ''
        },
        'room_details': {
            'users':ActiveUsers.get_room_users(room_instance.room_name),
            'username': current_user.nickname,
            'room_name': room_instance.room_name,
            'room_owner': room_instance.is_owner()
        },
        'ws':{'endpoint': "/ws",'url':request.host_url.rstrip("/")}
    }
    return ng_context

@app.route('/code/<token>')
@app.route("/r/<roomname>")
def main_entry_point(token=None,roomname=None):
    room=None
    if roomname:
        room = Room.query.filter_by(room_name=roomname).first()
        if not room:
            return "Room Not Found", 404
        if not room.verify_allowed():
            return "Room Forbidden", 405
    else:
        invite=None
        if token:
            user = User.exchange_token(token)
        if not user:
            return "Session not found", 404
        elif not user.is_active:
            return "Session has been closed",405
        # user = User.exchange_token(token)??
        print("UUUUU:", user.to_dict())
        login_user(user)
        room = Invites.query.filter_by(token_invite=token).first().room.room_name
        return redirect('/r/%s'%room)
    ctx = create_context(room)

    # ctx['room_details']['users'][0]['state']='active'
    # ctx['room_details']['users'][0]['is_admin']=True
    # ctx['room_details']['users'][-1]['is_admin']=True
    # ctx['room_details']['users'][-1]['state']='inactive'
    # ctx['room_details']['users'][-1]['state']='inactive'
    details = b64encode(json.dumps(ctx).encode('latin1')).decode('latin1')
    return render_template('app-index.html',room=room,angular_ctx=details)
@app.route("/active/<room_name>")
def active(room_name):
    return json.dumps(ActiveUsers.get_room_users(room_name))
app.register_blueprint(admin_bp)
if __name__ == '__main__':
    from models import init_app as db_init_app, Room, Invites, User

    db_init_app(app)
    socketio = socketio_init_app(app,resource="/ws")

    # app.run(debug=True)

    socketio.run(app,debug  =True)
