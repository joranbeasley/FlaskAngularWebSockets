import json

from flask import Blueprint, render_template, request, redirect
from flask_login import login_user, current_user, login_required

from models import User, db, Room, Invites

admin_bp = Blueprint("admin","admin",url_prefix="/admin")

@login_required
@admin_bp.route("/reportcard")
def reportcard():
    ctx =  dict(
        grades = [
            ("Culture Fit","culture",0),
            ("Technical Skills","technical",0),
            ("Willingness To Learn","learning",0),
            ("Problem Solving","problem_solving",0),
            ("Creativity","creativity",0),
            ("Well Organized","organized",0),
        ],
        language="python",
        candidates_code = open(__file__,"rb").read().decode('latin1'),
        candidate_name = "Joran Beasley",
        reviewer_name = "Fred Lionetti",
    )
    return render_template('app-reportcard.html',**ctx)


@admin_bp.route('/login',methods=["GET","POST"])
def login():
    if request.form:
        user = User.login(**request.form.to_dict())
        if user:
            login_user(user)
            return redirect(request.args.get("next","/admin"))
        else:
            print("Failed to Login")
    return render_template('admin-pages/app-login.html')

@login_required
@admin_bp.route("/create_room",methods=["GET","POST"])
def create_room():
    if request.form:
        r = Room(language=request.form.get('room_language'),room_name=request.form.get('room_name'),invite_only=request.form.get('invite_only','')=='on')
        r.owner_id = current_user.id
        db.session.add(r)
        db.session.commit()
        return redirect("/r/%s"%r.room_name)
    return render_template("admin-pages/create_room.html")

@login_required
@admin_bp.route("/invite_guest",methods=["GET","POST"])
def invite_guest():
    payload = request.form.to_dict() or request.json
    room = Room.query.filter_by(room_name=payload.pop('room_name')).first()
    if not room:
        return "Room Not Found",404
    if not room.is_owner():
        return "Only The Room Owner Can Do That",405
    payload['room_id'] = room.id
    payload['invited_by_id'] = current_user.id
    invite = Invites(**payload)
    db.session.add(invite)
    db.session.commit()
    return json.dumps({"STATUS":"OK",
                       "user":{
                           "username":invite.nickname,
                           "email":invite.email,
                           "real_name":invite.real_name,
                           "state":"",
                           "url": request.host_url + "/code/%s" % invite.token_invite
                               }

                       })

@login_required
@admin_bp.route("/add_user",methods=["GET","POST"])
def add_user():
    if request.form:
        u = User(**request.form.to_dict())
        db.session.add(u)
        db.session.commit()
        login_user(u)
        redirect(request.args.get('next','/admin'))
    return render_template("admin-pages/invite-user.html")

@login_required
@admin_bp.route("/")
def admin():
    return render_template("admin-pages/app-admin.html")