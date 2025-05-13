
from flask import Blueprint, render_template, url_for, request, jsonify, flash, redirect, session, make_response
from datetime import datetime
import uuid
import pickle
import threading
import time
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import time
import threading
from datetime import timedelta

import globals
from .models import db, User, UserInteraction
from .pipeline_common import PlayingStatus, action_to_desc
from .pipeline_utils_u2m import *
from .pipeline_utils_u2u import ScenarioRoom, ClientUserState
from .models import User, UserValuesAssign


web_base = Blueprint('web_base', __name__)

# 存储用户的最后心跳时间
user_last_heartbeat = {}
# 3s -> 5s
heartbeat_timeout = 5  # 秒


@web_base.route('/finish', methods=['GET'])
@login_required
def finish():
    user_uuid = request.cookies.get('sid')
    if user_uuid:
        room: ScenarioRoom = globals.global_rooms_dict[user_uuid]
        room.mark_user_finished(user_uuid)
        print(f'global_user_dict: {globals.global_user_dict}')
        print(f'User {user_uuid} marked as finished in room {room.room_info()}')

        user_state: ClientUserState = globals.global_user_u2u_args[user_uuid]
        user_state.playing_status = PlayingStatus.FINISHED

        if room.all_users_finished():
            print(f'All users finished in room {room.room_info()}')
            # room.cleanup(global_user_args=global_user_u2u_args) 

    return render_template('thanks.html')


@web_base.route('/break', methods=['GET'])
@login_required
def show_break():
    user_uuid = request.cookies.get('sid')
    if user_uuid:
        print(f'global_user_dict: {globals.global_user_dict}')
        print(f'[show_break] {datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, '
              f'username: {globals.global_user_dict[user_uuid]}, user_uuid: {user_uuid}')
        
        room: ScenarioRoom = globals.global_rooms_dict[user_uuid]
        room.mark_user_finished(user_uuid)
        
        user_state: ClientUserState = globals.global_user_u2u_args[user_uuid]
        user_state.playing_status = PlayingStatus.FINISHED

        print(f'User {user_uuid} marked as finished in room {room.room_info()}')
        
        # Check if all users in the room have finished
        if room.all_users_finished():
            print(f'All users finished in room {room.room_info()}')
            # clean up the room
            # room.cleanup(global_user_args=global_user_u2u_args)

    return render_template('break.html')

@web_base.route('/warm_up_break', methods=['GET'])
@login_required
def show_warm_up_break():
    return render_template('warm_up_break.html')

# @web_base.route('/user_leave', methods=['POST'])
# def user_leave():
#     data = request.json
#     user_uuid = data.get('sid')
#     if user_uuid:

#         print(f'global_user_dict: {global_user_dict}')
#         print(f'[user_leave] {datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, '
#               f'username: {global_user_dict[user_uuid]}, user_uuid: {user_uuid}')
        
#         room: ScenarioRoom = global_rooms_dict[user_uuid]
#         room.mark_user_finished(user_uuid)

#         user_state: ClientUserState = global_user_u2u_args[user_uuid]

#         print(f'global_user_dict: {globals.global_user_dict}')
#         print(f'[user_leave] {datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, '
#               f'username: {globals.global_user_dict[user_uuid]}, user_uuid: {user_uuid}')
        
#         room: ScenarioRoom = globals.global_rooms_dict[user_uuid]
#         room.mark_user_finished(user_uuid)

#         user_state: ClientUserState = globals.global_user_u2u_args[user_uuid]
#         user_state.playing_status = PlayingStatus.QUIT

#         print(f'User {user_uuid} marked as finished in room {room.room_info()}')
#         if room.all_users_finished():
#             print(f'All users left the room {room.room_info()}')
#             # room.cleanup(global_user_args=global_user_u2u_args)
    
#     # fixeme, 2024/09/23
#     # logout_user()
#     return jsonify({'status': 'success'})


@web_base.route('/')
def index():
    return redirect(url_for('web_base.login'))


@web_base.route('/login', methods=['GET', 'POST'])
def login():
    # print(f'request headers: {request.headers}')
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        user = User.query.filter_by(email=email).first()
        if email != '' and name != '':
            session['name'] = email
            if not user:
                user = User(email=email, name=name)
                db.session.add(user)
                db.session.commit()

            login_user(user, remember=True)
            user_uuid = request.cookies['sid']
            globals.global_user_dict[user_uuid] = email

            print(f'[login] {datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, '
                  f'email: {email}, name: {name}, user_uuid: {user_uuid}')
            # if mode == 'u2u':
            #     # to page_render.html interact_u2u with get method
            #     return redirect(url_for('web_u2u.interact_u2u'))
            # return redirect(url_for('web_u2m.interact'))
            return redirect(url_for('web_u2u.show_rooms'))
        else:
            flash('email and name cannot be none', category='error')


    if request.referrer and 'interact' in request.referrer:
        # 前端会捕获到 400 错误，然后终止前端的轮询
        return jsonify({'error': 'Unexpected redirect from interact page'}), 400
    
    resp = make_response(render_template('login.html', ))

    user_uuid = str(uuid.uuid4())
    resp.set_cookie('sid', user_uuid)
    
    print(f'[login] User Agent: {request.headers.get("User-Agent")}')
    print(f'[login] IP Address: {request.remote_addr}')

    # referrer 是用户从哪个页面跳转过来的
    # 目前我本地测试时，会概率性地出现interact页面周期性轮旋时，出现突然客户端跟服务器断开连接的情况，
    # 此时会反复地跳转到login页面，而referrer会记录为 127.0.0.1/u2u/interact
    # 为什么会 net::ERR_CONNECTION_RESET，还没有完全定位到
    print(f'[login] Referrer: {request.referrer}')

    print(f'[login] {request.method} assigned user_uuid: {user_uuid}, maybe exist old uuid: {request.cookies.get("sid")}')
    return resp



@web_base.route('/logout', )
@login_required
def logout():
    logout_user()
    return redirect(url_for('web_base.login'))


@web_base.route('/reset', methods=['GET'])
@login_required
def reset():
    if ('sid' not in request.cookies) or request.cookies['sid'] not in globals.global_user_dict:
        return redirect('/')
    user_uuid = request.cookies['sid']
    if mode == 'u2m':
        args = globals.global_user_args[user_uuid]
        args.reset()
        print('{} choose the {} in the reset'.format(session.get('name'), args.scenario_name))
        init_scenario(args)
        return redirect(url_for('web_u2m.interact'))
    else:
        # todo, 2023/03/14
        return redirect(url_for('web_u2u.interact_u2u'))

@web_base.errorhandler(500)
def internal_server_error(error):
    print(f"500 error: {error}")
    return "Internal Server Error", 500


@web_base.route('/admin', methods=['GET'])
# @login_required
def admin_panel():
    # 检查用户是否有管理员权限
    # if current_user.email not in ['admin@example.com', 'other_admin@example.com']:
    #     flash('You do not have permission to access this page.', category='error')
    #     return redirect(url_for('web_base.index'))
    return render_template('admin_panel.html')


@web_base.route('/admin/status', methods=['GET'])
# @login_required
def admin_status():

    rooms_status = {}
    users_status = {}

    for _, room in globals.global_rooms_dict.items():

        user_list = []
        for user_uuid, _ in room.client_user_dict.items():
            user_list.append(user_uuid + ':' + globals.global_user_dict[user_uuid])
            
        rooms_status[room.room_id] = {
            'status': room.get_room_status(),
            'users': user_list,
            'scenario': room.scenario_name
        }

    for user_uuid, user_email in globals.global_user_dict.items():
        if globals.global_user_u2u_args.get(user_uuid) is None:
            continue
        
        user_state: ClientUserState = globals.global_user_u2u_args[user_uuid]
        user_room: ScenarioRoom = globals.global_rooms_dict[user_uuid]

        this_agent: Agent = user_room.client_user_dict[user_uuid]

        if user_state.playing_status == PlayingStatus.PLAYING:
            if len(user_room.client_user_dict) >= 2:
                user_status = 'playing'
            else:
                # < 2
                user_status = 'waiting'
        elif user_state.playing_status == PlayingStatus.FINISHED:
            user_status = 'finished'
        elif user_state.playing_status == PlayingStatus.QUIT:
            user_status = 'quit'
        else:
            user_status = 'unknown'

        try:
            partner_uuid, partner_agent = user_room.get_partner(user_uuid)
            partner_email = globals.global_user_dict[partner_uuid]
        except:
            partner_uuid = None
            partner_email = None

        other_last_action = 'unknown'
        if partner_uuid:
            belief_agent: Agent = this_agent.belief.get(partner_agent.id)
            if belief_agent and len(belief_agent.action_history) > 0:
                other_last_action = action_to_desc(belief_agent.action_history[-1], user_room.world)

        users_status[user_uuid] = {
            'email': user_email,
            'roomId': user_room.room_id,
            'partner': f'{partner_uuid}:{partner_email}',
            'status': user_status,
            'other_last_action': other_last_action
        }

    return jsonify({
        'rooms': rooms_status,
        'users': users_status
    })


@web_base.route('/heartbeat', methods=['POST'])
@login_required
def heartbeat():
    data = request.json
    user_uuid = data.get('sid')
    if user_uuid:
        user_last_heartbeat[user_uuid] = datetime.now()
        # print(f'Heartbeat received from {user_uuid} at {user_last_heartbeat[user_uuid]}')
        if globals.global_user_u2u_args.get(user_uuid) is not None:
            user_state = globals.global_user_u2u_args[user_uuid]
            if user_state.playing_status == PlayingStatus.QUIT:
                user_state.playing_status = PlayingStatus.PLAYING
                room: ScenarioRoom = globals.global_rooms_dict[user_uuid]
                room.remove_user_finished(user_uuid=user_uuid)


        return jsonify({'status': 'success'})
    return jsonify({'status': 'failed', 'reason': 'no sid provided'}), 400

def check_heartbeats():
    while True:
        now = datetime.now()
        to_remove = []
        for user_uuid, last_time in user_last_heartbeat.items():
            if now - last_time > timedelta(seconds=heartbeat_timeout):
                print(f'User {user_uuid} timed out. Marking as left. global rooms dict: {globals.global_rooms_dict.keys()}')
                # 处理用户离开逻辑
                room: ScenarioRoom = globals.global_rooms_dict[user_uuid]
                if room:
                    room.mark_user_finished(user_uuid)
                    user_state: ClientUserState = globals.global_user_u2u_args.get(user_uuid)
                    if user_state:
                        user_state.playing_status = PlayingStatus.QUIT
                    if room.all_users_finished():
                        print(f'All users left the room {room.room_info()}')
                        # room.cleanup(global_user_args=global_user_u2u_args)
                to_remove.append(user_uuid)
        for user_uuid in to_remove:
            del user_last_heartbeat[user_uuid]
        time.sleep(heartbeat_timeout)


heartbeat_thread = threading.Thread(target=check_heartbeats, daemon=True)
heartbeat_thread.start()

from main_interact import mode
