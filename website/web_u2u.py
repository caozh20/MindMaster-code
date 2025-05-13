from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session, make_response, current_app, send_from_directory
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from utils.base import log
from utils.save import save_frames_as_video, save_base64_frames_as_video
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import json
import threading
import time
import globals
from .pipeline_utils_u2u import *
from .models import db
from .models import User, UserInteraction, UserValuesAssign
from .pipeline_common import valid_action, get_action_option_dict, parse_action, get_intent_desc
from .pipeline_common import get_belief_related_id_names_dict, generate_intent_option_dict
from .pipeline_common import calc_agents_values_floating_pos

web_u2u = Blueprint('web_u2u', __name__)

sem = threading.Semaphore()
INTERVAL = 20

executor = ThreadPoolExecutor(max_workers=4)


@web_u2u.route('/gif/<filename>')
def serve_gif(filename):
    return send_from_directory(f'../assets/resize_gifs', filename)


@web_u2u.route('/logout', )
@login_required
def logout():
    logout_user()
    return redirect(url_for('web_u2u.login'))


@web_u2u.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        pswd1 = request.form.get('password1')
        pswd2 = request.form.get('password2')
        gender = request.form.get('gender')
        age = request.form.get('age')
        education = request.form.get('education')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists!', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters!', category='error')
        elif len(first_name) < 2:
            flash('first name must be greater than 1 characters!', category='error')
        elif pswd1 != pswd2:
            flash('Passwords don\'t match!', category='error')
        elif len(pswd1) < 6:
            flash('password must be at least 6 characters!', category='error')
        elif age == '' or gender == '' or education == '':
            flash('gender/age/education cannot by empty!', category="error")
        else:
            # add user to databse
            new_user = User(email=email,
                            first_name=first_name,
                            password=generate_password_hash(pswd1, method='sha256'),
                            age=age,
                            gender=gender,
                            education=education)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('web_u2u.interact_u2u'))
    return render_template('sign-up.html', user=current_user)


@web_u2u.route('/step', methods=['POST'])
@login_required
def step():
    '''
    用户点击下一步，提交自己的标注数据以及选择要执行的动作
    :return:
    '''
    start_time = time.time()
    if ('sid' not in request.cookies) or not session.get('name'):
        return redirect('/')

    user_uuid = request.cookies['sid']
    room: ScenarioRoom = globals.global_rooms_dict[user_uuid]
    client_agent: Agent = room.client_user_dict[user_uuid]
    partner_user_uuid, partner_agent = room.get_partner(user_uuid)

    room.CAN_SEND_FRAME = False
    client_agent_state = globals.global_user_u2u_args[user_uuid]
    partner_agent_state = globals.global_user_u2u_args[partner_user_uuid]

    
    log.info(f"client's initial intent:{client_agent.initial_intent}")
    # 判断输入的动作是否有效
    log.info(f"room: {room.room_id}, username: {globals.global_user_dict.get(user_uuid, '')}, user input: {request.form}")
    user_action = parse_action(client_agent, room.world, request.form)

    done = FinishStatus.DOING
    v, m = valid_action(room.world, client_agent, user_action)

    user_done = False
    if v:
        room.doing_agent = client_agent.id
        user_done, done = main_protocol_interact_u2u(room, user_uuid, user_action, 
                                                     globals.global_user_u2u_args, 
                                                     request.form['your_high_intent'])        

        if done == FinishStatus.SUCCESS:
            if room.intent_diff == 0:
                #对应一个intent和一个intent为none的情况
                if client_agent.initial_intent and client_agent.initial_intent != 'None':
                    #client_agent.initial_intent不为none
                    #client_agent自己完成了
                    client_agent_state.finish_status = 11
                    partner_agent_state.finish_status = 10
                else:
                    #client_agent.initial_intent为none
                    #client_agent帮partner完成了
                    client_agent_state.finish_status = 21
                    partner_agent_state.finish_status = 20
            elif room.intent_diff == 1:
                client_agent_state.finish_status = 2
            elif room.intent_diff == 2:
                client_agent_state.finish_status = 3
                partner_agent_state.finish_status = 3
        if done == FinishStatus.REACH_MAX_ITER:
            client_agent_state.finish_status = 4
            partner_agent_state.finish_status = 4
        
        
        if done == FinishStatus.SUCCESS or done == FinishStatus.REACH_MAX_ITER:
            # 排除warm_up_game
            if room.room_name is not None and "热身" in room.room_name:
                pass
            else:
                client_agent_state.finished_tasks += 1
                partner_agent_state.finished_tasks += 1
                update_user_task_count(user_name=globals.global_user_dict[user_uuid])
                update_user_task_count(user_name=globals.global_user_dict[partner_user_uuid])
                
        print('other_desire_estimated:', request.form['other_desire'])

        user_interaction = UserInteraction(
                                           game_id=room.room_id,
                                           scenario=room.scenario_name_to_store,
                                           user_id=current_user.id,
                                           user_uuid=user_uuid,
                                           user_name=globals.global_user_dict[user_uuid],
                                           task_id=client_agent_state.task_id,
                                           mode='u2u',
                                           control_test=room.control_test,
                                           iteration=room.iterations,
                                           user_agent_id=client_agent.id,
                                           user_agent_action=user_action,
                                           running_status=done.value,
                                           world_agents=room.world.agents,
                                           world_objs=room.world.objects,
                                           world_landmarks=room.world.landmarks,
                                           your_high_intent=request.form['your_high_intent'],
                                           # other_user_id=,
                                           other_high_intent_estimated=request.form['other_high_intent'],
                                           other_desire_estimated=request.form['other_desire'],
                                           estimation_explanation=request.form['explanation1'],
                                           intention_explanation=request.form['explanation2'],
                                           action_explanation=request.form['explanation3'],
                                           )
        db.session.add(user_interaction)
        db.session.commit()

    else:
        # 这里需要给用户提供反馈
        pass

    action_option_dict = get_action_option_dict(client_agent, room.start_action_option_dict, room.world)
    # my intent
    intent_option_dict = generate_intent_option_dict(room.world, client_agent, mode='u2u')
    belief_agent_list = get_belief_agent_list(client_agent)

    # partner user_uuid
    partner_user_uuid, partner_agent = room.get_partner(user_uuid)

    # if not room.control_test:
    #     other_last_interaction = UserInteraction.query.filter_by(user_uuid=partner_user_uuid).order_by(
    #         UserInteraction.id.desc()).first()
    #     if other_last_interaction:
    #         other_desire_estimated = other_last_interaction.other_desire_estimated
    #         # print(f'{user_uuid}, other_desire_estimated by {partner_user_uuid}: {other_desire_estimated}')
    #         client_agent_state.value_consistency = calc_value_consistency(client_agent.desire(), other_desire_estimated)
    # value_consistency = client_agent_state.value_consistency


    other_intent_option_dict = defaultdict(dict)

    for belief_agent in client_agent.belief.agents:
        if belief_agent.id == client_agent.id:
            continue
        # estimate other's intent
        intent_dict = generate_intent_option_dict(room.world, belief_agent, me=client_agent, mode='u2u')
        other_intent_option_dict[belief_agent.id] = intent_dict

    end_time = time.time()
    # 先假定固定5s
    response_time = (start_time - room.LAST_RESPONSE_TIME)
    if response_time > INTERVAL:
        response_time = INTERVAL
    # 这里不需要给机器的反应留时间
    wait_time = INTERVAL - response_time
    if globals.global_fix_time_per_round:
        log.info(f"start_time: {start_time}")
        log.info(f"Last_response: {room.LAST_RESPONSE_TIME}")
        log.info(f"program_time: {end_time - start_time}")
        log.info(f"wait_time: {wait_time}")
        log.info(f"response_time: {response_time}")
        time.sleep(wait_time)

    room.CAN_SEND_FRAME = True
    room.done = done
    return jsonify({'message': 'round {} finished'.format(room.iterations),
                    'action_option_dict': action_option_dict,
                    'intent_option_dict': intent_option_dict,
                    'belief_agent_list': belief_agent_list,
                    'other_intent_option_dict': other_intent_option_dict,
                    'done': done.value,
                    'finished_tasks': client_agent_state.finished_tasks,
                    'invalid': (not v),
                    'hint': m,
                    'finish_status': client_agent_state.finish_status,
                    'doing_agent':room.doing_agent,
                    # 'goal_completion': user_done,
                    # 'value_consistency': value_consistency
                    })


@web_u2u.route('/survey', methods=['POST'])
@login_required
def survey():
    '''
    用户在场景结束时提交自己的标注数据以及选择要执行的动作
    :return:
    '''

    if ('sid' not in request.cookies) or not session.get('name'):
        return redirect('/')

    user_uuid = request.cookies['sid']
    room = globals.global_rooms_dict[user_uuid]
    client_agent = room.client_user_dict[user_uuid]
    client_agent_state = globals.global_user_u2u_args[user_uuid]

    try:
        user_name = globals.global_user_dict[user_uuid].split('@')[0]
    except:
        user_name = ''
    now = datetime.now().strftime('%m%d%H%M')

    # 异步执行
    # executor.submit(save_frames_as_video, client_agent_state, client_agent_state.frames,
    #                 f'{user_name}_{room.scenario_name}_{client_agent.name}_{now}.mp4')
    executor.submit(save_base64_frames_as_video, client_agent_state, client_agent_state.frames,
                    f'{user_name}_{room.scenario_name}_{client_agent.name}_{now}.mp4')
    

    user_interaction = UserInteraction(
                                       game_id=room.room_id,
                                       user_id=current_user.id,
                                       user_uuid=user_uuid,
                                       user_name=globals.global_user_dict[user_uuid],
                                       task_id=client_agent_state.task_id,
                                       scenario=room.scenario_name_to_store,
                                       mode='u2u',
                                       control_test=room.control_test,
                                       iteration=room.iterations,
                                       user_agent_id=client_agent.id,
                                       world_agents=room.world.agents,
                                       world_objs=room.world.objects,
                                       world_landmarks=room.world.landmarks,
                                       other_high_intent_estimated=request.form['other_high_intent'],
                                        other_desire_estimated=request.form['other_desire'],
                                        estimation_explanation=request.form['explanation1'],
                                       )
    db.session.add(user_interaction)
    db.session.commit()
    return jsonify({'message': 'round {} finished'.format(room.iterations),
                    'finished_tasks': client_agent_state.finished_tasks,
                    })


# fixme, 未来会删除该路由（仅在测试阶段使用）
@web_u2u.route('/reset', methods=['GET'])
@login_required
def reset():
    if ('sid' not in request.cookies) or request.cookies['sid'] not in globals.global_user_dict:
        return redirect('/')
    user_uuid = request.cookies['sid']
    args = globals.global_user_u2u_args[user_uuid]
    args.reset()
    print('{} choose the {} in the reset'.format(session.get('name'), args.scenario_name))
    init_scenario(args)
    # return render_template('page_render.html',
    #                        username=global_user_dict[user_uuid],
    #                        agent_name=args.client_agent.name,
    #                        desire=args.client_agent.desire,
    #                        n_agents=len(args.world.agents),
    #                        object_names=','.join([obj.name for obj in args.world.objects]),
    #                        all_agents=args.world.agents,
    #                        all_objs=args.world.objects,
    #                        all_lambmards=args.world.landmarks,
    #                        intent_desc=get_intent_desc(args.client_agent))
    return redirect(url_for('web_u2u.interact_u2u'))
    # return jsonify({'message': 'reset succeeds.'})


@web_u2u.route("/interact", methods=["GET", "POST"])
@login_required
def interact_u2u():
    '''
    周期性抓取后端计算的 frames，返回给前端，前端通过 js 定时刷新，实现动画效果
    :return:
    '''

    if ('sid' not in request.cookies) or request.cookies['sid'] not in globals.global_user_dict:
        return redirect('/')

    user_uuid = request.cookies['sid']
    user_name = globals.global_user_dict[user_uuid]

    # only executed once
    if user_uuid not in globals.global_rooms_dict:
        globals.global_user_dict[user_uuid] = session.get('name')
        new_room, _ = globals.global_rooms_dict.assign_room(user_uuid, globals.global_user_dict[user_uuid])
        # who first enters into the room, who should first do the action
        if new_room.active_user_uuid is None:
            new_room.active_user_uuid = user_uuid

        globals.global_user_u2u_args[user_uuid] = ClientUserState(user_uuid)

        log.info('{} enters into the {} as agent: {}'.format(session.get('name'), new_room.room_info(), new_room.client_user_dict[user_uuid].name))
        log.info(f'num rooms: {globals.global_rooms_dict.num_rooms()}')

        if not new_room.control_test:
            user_values_assign = UserValuesAssign.query.filter_by(user_id=current_user.id, control_test=False).first()
            # update 1111
            print(f'insert user_values_assign: {current_user.id, current_user.email, new_room.client_user_dict[user_uuid].desire()}')
            values_assign = UserValuesAssign(user_id=current_user.id,
                                                control_test=False,
                                                email=current_user.email,
                                                initial_values=new_room.client_user_dict[user_uuid].desire.to_json())
            db.session.add(values_assign)
            db.session.commit()

            # 同一个用户是否需要继承上一次的 value 值，如下的 if-else 走的是继承逻辑
            # if not user_values_assign:
            #     print(f'insert user_values_assign: {current_user.id, current_user.email, new_room.client_user_dict[user_uuid].desire()}')
            #     values_assign = UserValuesAssign(user_id=current_user.id,
            #                                      control_test=False,
            #                                      email=current_user.email,
            #                                      initial_values=new_room.client_user_dict[user_uuid].desire.to_json())
            #     db.session.add(values_assign)
            #     db.session.commit()
            # else:
            #     print(f'inherits user_values_assign: {current_user.id, current_user.email}')
            #     print(f'before assign: {new_room.client_user_dict[user_uuid].desire()}')
            #     new_room.client_user_dict[user_uuid].desire = Desire.from_json(user_values_assign.initial_values)
            #     print(f'after assign: {new_room.client_user_dict[user_uuid].desire()}')

            # for demo here to preassign
            # new_room.client_user_dict[user_uuid].desire = Desire(social=1, active=0, helpful=0)

        init_scenario(new_room, globals.global_user_u2u_args)

    room = globals.global_rooms_dict[user_uuid]

    client_agent = room.client_user_dict[user_uuid]
    partner_agent = client_agent
    for agent in room.world.agents:
        if agent.id == client_agent.id:
            continue
        partner_agent = agent

    user_state: ClientUserState = globals.global_user_u2u_args[user_uuid]
    user_state.round_finished = False
    to_finish_page = True
    
    if request.method == 'GET':
        # print(f'interact: {user_uuid}, get, init frames: {len(user_state.frames)}')
        action_option_dict = get_action_option_dict(client_agent, room.start_action_option_dict, room.world)
        id_names_dict = get_world_id_names_dict(room)
        if room.control_test:
            values_pos_ratio = calc_agents_values_floating_pos([client_agent, partner_agent])
        else:
            values_pos_ratio = calc_agents_values_floating_pos([client_agent])
        intent_option_dict = generate_intent_option_dict(room.world, client_agent, mode='u2u')
        other_intent_option_dict = defaultdict(dict)
        for belief_agent in client_agent.belief.agents:
            if belief_agent.id == client_agent.id:
                continue
            intent_dict = generate_intent_option_dict(room.world, belief_agent, me=client_agent, mode='u2u')
            other_intent_option_dict[belief_agent.id] = intent_dict
        belief_agent_list = get_belief_agent_list(client_agent)
        return render_template('page_render.html',
                               # username=global_user_dict[user_uuid],
                               mode='u2u',
                               control_test=room.control_test,
                               agent_id=client_agent.id,
                               partner_agent_id=partner_agent.id,
                               agent_name=client_agent.name,
                               partner_name=partner_agent.name,
                               my_value=client_agent.desire,
                               partner_value=partner_agent.desire,
                               values_pos_ratio=values_pos_ratio,
                               n_agents=len(room.world.agents),
                               object_names=','.join([obj.name for obj in room.world.objects]),
                               client_agent=client_agent,
                               all_agents=room.world.agents,
                               # agents_rel_pos_dict=agents_rel_pos_dict,
                               all_objs=room.world.objects,
                               all_lambmards=room.world.landmarks,
                               world_id_name_dict=id_names_dict,
                               intent_option_dict=intent_option_dict,
                               # tasks_option_dict=tasks_option_dict,
                               # tasks_flat_list=tasks_flat_option_list,
                               other_intent_option_dict=other_intent_option_dict,
                               # other_tasks_option_dict=other_tasks_option_dict,
                               # other_flat_tasks_dict=other_flat_tasks_dict,
                               belief_agent_list=belief_agent_list,
                               intent_desc=get_intent_desc(client_agent, room.world),
                               partner_value_desc=partner_agent.desire.parse(),
                               action_option_dict=action_option_dict,
                            #    latest_frame=frame_to_b64(user_state.frames[user_state.frame_index])
                               latest_frame=user_state.frames[user_state.frame_index]
                               )
    else:
        # 这里响应前端的周期性回调
        if len(user_state.frames) > 0:
            frame = user_state.frames[user_state.frame_index]
            # frame_data = frame_to_b64(frame)
            frame_data = frame

            temp_agent, temp_other_agent = user_state.temp_agents(client_agent.id, partner_agent.id)
            if room.control_test:
                values_pos_ratio = calc_agents_values_floating_pos([temp_agent, temp_other_agent])
            else:
                values_pos_ratio = calc_agents_values_floating_pos([temp_agent])

            if user_state.frame_index < len(user_state.frames) - 1:
                if room.CAN_SEND_FRAME:
                    room.SENDING = True
                    user_state.frame_index += 1
                else:
                    pass
            else:
                if room.SENDING:
                    room.LAST_RESPONSE_TIME = time.time()
                room.SENDING = False
                to_finish_page = (get_user_tasks_count(user_name=user_name) - get_user_tasks_count(user_name=user_name, user_task_dict=globals.global_user_task_dict)) >= 4
                user_state.round_finished = (True and room.room_ready())
        else:
            frame_data = ''
            values_pos_ratio = None

        return json.dumps({'frame_index': user_state.frame_index,
                           'finished_flag': user_state.round_finished,
                           # 减少带宽占用，只在渲染时发送 frame_data，
                           'frame_data': frame_data if not user_state.round_finished else '',
                           'iteration': room.iterations,
                           # todo, 0906, 这里存在带宽的问题，可类似 frame_data 那样，只发送变化的部分
                           # 只在 round 结束时发送 action_option_dict，节省带宽，以及前端可能的缓存
                           'action_option_dict': get_action_option_dict(client_agent, room.start_action_option_dict, room.world) 
                                if user_state.round_finished else {},
                           'values_pos_ratio': calc_agents_values_floating_pos([client_agent, partner_agent]) 
                                if values_pos_ratio is None else values_pos_ratio,
                           # 标识当前用户是否为激活态（即可以执行 action）
                           'active': user_uuid == room.active_user_uuid,
                           'sending': (room.SENDING and room.CAN_SEND_FRAME),
                           'done': room.done.value,
                           'finished_tasks': room.finished_tasks,
                           'to_finish_page': to_finish_page,
                           'fix_time_per_round': globals.global_fix_time_per_round,
                           'finish_status': user_state.finish_status,
                           'doing_agent': room.doing_agent, 
                           'room_name': room.room_name, 
                           }
                          )



@web_u2u.route("/wiki", methods=["GET", "POST"])
def wiki():
    return render_template('wiki.html')

@web_u2u.route('/join_room', methods=['POST'])
@login_required
def join_room():
    data = request.json
    user_uuid = data.get('sid')
    action = data.get('action')
    room = data.get('room')

    # 模拟错误场景：如果房间名为空，返回错误
    if not room and action == 'join':
        return jsonify({'error': 'Room name is required to join a room', 'status': 'error'}), 400

    if action == "join":
        room_id = room['room_id']

        globals.global_user_dict[user_uuid] = session.get('name')
        new_room, _ = globals.global_rooms_dict.assign_room(user_uuid, globals.global_user_dict[user_uuid], room_id=room_id)
    elif action == "create":
        globals.global_user_dict[user_uuid] = session.get('name')
        new_room, _ = globals.global_rooms_dict.assign_room(user_uuid, globals.global_user_dict[user_uuid], create_new_room=True)
    else:
        return jsonify({'error': 'Wrong action input', 'status': 'error'}), 400

    # who first enters into the room, who should first do the action
    if new_room.active_user_uuid is None:
        new_room.active_user_uuid = user_uuid

    globals.global_user_u2u_args[user_uuid] = ClientUserState(user_uuid)

    log.info('{} enters into the {} as agent: {}'.format(session.get('name'), new_room.room_info(), new_room.client_user_dict[user_uuid].name))
    log.info(f'num rooms: {globals.global_rooms_dict.num_rooms()}')

    if not new_room.control_test:
        user_values_assign = UserValuesAssign.query.filter_by(user_id=current_user.id, control_test=False).first()
        # update 1111
        print(f'insert user_values_assign: {current_user.id, current_user.email, new_room.client_user_dict[user_uuid].desire()}')
        values_assign = UserValuesAssign(user_id=current_user.id,
                                            control_test=False,
                                            email=current_user.email,
                                            initial_values=new_room.client_user_dict[user_uuid].desire.to_json())
        db.session.add(values_assign)
        db.session.commit()

    init_scenario(new_room, globals.global_user_u2u_args)

    # 模拟成功场景
    if action == 'create':
        return jsonify({'message': 'Room successfully created', 'status': 'success', 'redirect_url': url_for('web_u2u.interact_u2u')})
    elif action == 'join':
        return jsonify({'message': f'Successfully joined room {room_id}', 'status': 'success', 'redirect_url': url_for('web_u2u.interact_u2u')})
    else:
        return jsonify({'error': 'Invalid action', 'status': 'error'}), 400

# 提供房间信息的 API
@web_u2u.route('/api/rooms', methods=['GET'])
@login_required
def get_rooms():
    rooms = globals.global_rooms_dict.room_list
    rooms_info_list = []
    for room in rooms:
        rooms_info_list.append(
            {
                "user_num": len(room.client_user_dict.keys()), 
                "room_id": room.room_id, 
                "room_name": room.room_name, 
            }
        )
    return jsonify(rooms_info_list)

@web_u2u.route('/select_room', methods=['GET'])
@login_required
def show_rooms():
    if globals.global_rooms_dict.offline_experiment:
        globals.global_rooms_dict.check_and_recreate_offline_room()
    return render_template('room_select.html')

# 处理按钮点击事件
@web_u2u.route('/restart_room', methods=['GET', 'POST'])
def restart_room():
    if request.method == 'POST':
        group = request.json.get('group')
        if group:
            globals.global_rooms_dict.restart_offline_room(group)
            # 在这里添加重启房间组的逻辑
            print(f"重启房间组 {group}")
            return jsonify({"status": "success", "message": f"房间组 {group} 重启成功"})
        return jsonify({"status": "error", "message": "无效的请求"}), 400
    else:
        return render_template('restart.html')

@web_u2u.route('/qualtrics', methods=['GET'])
def show_qualtrics():
    return render_template('qualtrics.html')

@web_u2u.route('/Qualtrics Survey Software_files/<filename>')
def serve_qualtrics(filename):
    return send_from_directory(f'./templates/Qualtrics Survey Software_files', filename)
