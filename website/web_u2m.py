from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask import Blueprint, render_template, url_for, request, jsonify, redirect, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import login_user, login_required, logout_user, current_user
import base64
import io
from PIL import Image
import json
import uuid
import pickle
import time
from .models import User, UserInteraction
from .models import db
from utils.base import log, frame_to_b64
from utils.save import save_frames_as_video
from .pipeline_utils_u2m import *
from .pipeline_common import valid_action, get_action_option_dict, parse_action, get_intent_desc
from .pipeline_common import get_belief_related_id_names_dict, generate_intent_option_dict


web_u2m = Blueprint('web_u2m', __name__)

INTERVAL = 20

@web_u2m.route('/step', methods=['GET', 'POST'])
@login_required
def step():
    global global_fix_time_per_round
    global INTERVAL

    start_time = time.time()
    if ('sid' not in request.cookies) or not session.get('name'):
        return redirect('/')

    user_uuid = request.cookies['sid']
    print(f"step user_uuid: {user_uuid}, name: {session.get('name')}")
    # get 方法应该是不被执行的
    if request.method == 'GET':
        args = UserState()
        global_user_args[user_uuid] = args
        init_scenario(global_user_args[user_uuid])
        action_option_dict = get_action_option_dict(args.client_agent, args.start_action_option_dict, args.world)
        return jsonify({'message': 'round {} finished'.format(args.iterations), 'action_option_dict': action_option_dict})
    else:
        args = global_user_args[user_uuid]
        args.CAN_SEND_FRAME = False

        # 判断输入的动作是否有效
        try:
            user_action = parse_action(args.client_agent, args.world, request.form)
            v, m = valid_action(args.world, args.client_agent, user_action)
        except ValueError as e:
            v = False
            m = 'Invalid action parameters!!! Please select other again.'

        done = FinishStatus.DOING

        if v:
            done = main_protocol_interact(args, user_action)
            if done == FinishStatus.SUCCESS or done == FinishStatus.REACH_MAX_ITER:
                # 保存 args.frames to video
                try:
                    user_name = global_user_dict[user_uuid].split('@')[0]
                except:
                    user_name = ''
                now = datetime.now().strftime('%m%d%H%M')
                save_frames_as_video(args, args.frames, f'{user_name}_{args.scenario_name}_{args.client_agent.name}_{now}.mp4')
                args.finished_tasks += 1

            user_interaction = UserInteraction(user_id=current_user.id,
                                               user_name=global_user_dict[user_uuid],
                                               mode='u2m',
                                               task_id=args.task_id,
                                               scenario=args.scenario_name,
                                               iteration=args.iterations,
                                               user_agent_id=args.client_agent.id,
                                               user_agent_action=user_action,
                                               running_status=done.value,
                                               world_agents=args.world.agents,
                                               world_objs=args.world.objects,
                                               world_landmarks=args.world.landmarks,
                                               your_high_intent=request.form['your_high_intent'],
                                               # your_low_intent=request.form['your_low_intent'],
                                               other_high_intent_estimated=request.form['other_high_intent'],
                                               other_desire_estimated=request.form['other_desire']
                                               # other_low_intent_estimated=request.form['other_low_intent']
                                       )
            db.session.add(user_interaction)
            db.session.commit()

        else:
            # 这里需要给用户提供反馈
            pass
        action_option_dict = get_action_option_dict(args.client_agent, args.start_action_option_dict, args.world)
        # my intent
        intent_option_dict, tasks_option_dict, tasks_flat_option_list = generate_intent_option_dict(args.world, args.client_agent, mode='u2m')
        agents_rel_pos_dict = calc_agents_rel_pos(args)
        belief_agent_list = get_belief_agent_list(args)
        other_intent_option_dict = defaultdict(dict)
        other_tasks_option_dict = defaultdict(dict)
        other_flat_dict = defaultdict(list)

        for belief_agent in args.client_agent.belief.agents:
            if belief_agent.id == args.client_agent.id:
                continue
            # estimate other's intent
            intent_dict, tasks_dict, tasks_flat_list = generate_intent_option_dict(args.world, belief_agent, me=args.client_agent, mode='u2m')
            other_intent_option_dict[belief_agent.id] = intent_dict
            other_tasks_option_dict[belief_agent.id] = tasks_dict
            other_flat_dict[belief_agent.id] = tasks_flat_list

        end_time = time.time()
        # 先假定固定5s
        response_time = (start_time - args.LAST_RESPONSE_TIME)
        if response_time > INTERVAL:
            response_time = INTERVAL
        wait_time = INTERVAL - (end_time - start_time) + INTERVAL - response_time
        if global_fix_time_per_round:
            log.info(f"start_time: {start_time}")
            log.info(f"Last_response: {args.LAST_RESPONSE_TIME}")
            log.info(f"program_time: {end_time - start_time}")
            log.info(f"wait_time: {wait_time}")
            log.info(f"response_time: {response_time}")
            time.sleep(wait_time)

        args.CAN_SEND_FRAME = True
        args.done = done
        return jsonify({'message': 'round {} finished'.format(args.iterations),
                        'action_option_dict': action_option_dict,
                        'intent_option_dict': intent_option_dict,
                        'tasks_option_dict': tasks_option_dict,
                        'tasks_flat_list': tasks_flat_option_list,
                        'belief_agent_list': belief_agent_list,
                        'other_intent_option_dict': other_intent_option_dict,
                        'other_tasks_option_dict': other_tasks_option_dict,
                        'other_flat_tasks_dict': other_flat_dict,
                        'agents_rel_pos_dict': agents_rel_pos_dict,
                        'done': done.value,
                        'finished_tasks': args.finished_tasks,
                        'invalid': (not v),
                        'hint': m})


@web_u2m.route('/reset', methods=['GET'])
@login_required
def reset():
    global global_user_dict
    global global_user_args
    if ('sid' not in request.cookies) or request.cookies['sid'] not in global_user_dict:
        return redirect('/')
    user_uuid = request.cookies['sid']
    args = global_user_args[user_uuid]
    args.reset()
    log.info('{} choose the {} in the reset'.format(session.get('name'), args.scenario_name))
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
    return redirect(url_for('web_u2m.interact'))
    # return jsonify({'message': 'reset succeeds.'})


# @web_u2m.route('/finish', methods=['GET'])
# @login_required
# def finish():
#     global global_user_dict
#     global global_user_args
#     if ('sid' not in request.cookies) or request.cookies['sid'] not in global_user_dict:
#         return redirect('/')
#     user_uuid = request.cookies['sid']
#     return render_template('thanks.html')


# @web_u2m.route('/')
# def index():
#     return redirect(url_for('web_u2m.login'))


@web_u2m.route("/interact", methods=["GET", "POST"])
@login_required
def interact():
    global global_fix_time_per_round
    start_time = time.time()
    global global_user_dict
    global global_user_args
    if ('sid' not in request.cookies) or request.cookies['sid'] not in global_user_dict:
        return redirect('/')

    user_uuid = request.cookies['sid']
    if user_uuid not in global_user_args:
        args = UserState()
        global_user_args[user_uuid] = args
        log.info('{} choose the {}'.format(session.get('name'), args.scenario_name))
        global_user_dict[user_uuid] = session.get('name')
        init_scenario(args)

    finished = False

    # fixme, 这里每次刷新会有问题；
    # only done once or when refresh the page
    if request.method == 'GET':
        args = global_user_args[user_uuid]
        action_option_dict = get_action_option_dict(args.client_agent, args.start_action_option_dict, args.world)
        id_names_dict = get_world_id_names_dict(args)
        agents_rel_pos_dict = calc_agents_rel_pos(args)
        # generate my intent
        intent_option_dict, tasks_option_dict, tasks_flat_option_list = generate_intent_option_dict(args.world, args.client_agent, me=args.client_agent, mode='u2m')
        other_intent_option_dict = defaultdict(dict)
        other_tasks_option_dict = defaultdict(dict)
        other_flat_tasks_dict = defaultdict(list)
        for belief_agent in args.client_agent.belief.agents:
            if belief_agent.id == args.client_agent.id:
                continue
            # estimate other's intent
            intent_dict, tasks_dict, tasks_flat_list = generate_intent_option_dict(args.world, belief_agent, me=args.client_agent, mode='u2m')
            other_intent_option_dict[belief_agent.id] = intent_dict
            other_tasks_option_dict[belief_agent.id] = tasks_dict
            other_flat_tasks_dict[belief_agent.id] = tasks_flat_list
        belief_agent_list = get_belief_agent_list(args)

        # end_time = time.time()
        # # 先假定固定40s
        # wait_time = 5 - (end_time - start_time)
        # print("114519", wait_time)
        # print(args.iterations)
        # if args.iterations != 0:
        #     time.sleep(wait_time)

        return render_template('page_render.html',
                               mode='u2m',
                               username=global_user_dict[user_uuid],
                               agent_name=args.client_agent.name,
                               desire=args.client_agent.desire,
                               n_agents=len(args.world.agents),
                               object_names=','.join([obj.name for obj in args.world.objects]),
                               client_agent=args.client_agent,
                               all_agents=args.world.agents,
                               agents_rel_pos_dict=agents_rel_pos_dict,
                               all_objs=args.world.objects,
                               all_lambmards=args.world.landmarks,
                               world_id_name_dict=id_names_dict,
                               intent_option_dict=intent_option_dict,
                               tasks_option_dict=tasks_option_dict,
                               tasks_flat_list=tasks_flat_option_list,
                               other_intent_option_dict=other_intent_option_dict,
                               other_tasks_option_dict=other_tasks_option_dict,
                               other_flat_tasks_dict=other_flat_tasks_dict,
                               belief_agent_list=belief_agent_list,
                               intent_desc=get_intent_desc(args.client_agent, args.world),
                               action_option_dict=action_option_dict,
                               latest_frame=frame_to_b64(args.frames[-1]))
    else:
        args = global_user_args[user_uuid]
        if len(args.frames) > 0:
            frame = args.frames[args.frame_index]
            frame_data = frame_to_b64(frame)
            if args.frame_index < len(args.frames) - 1:
                if args.CAN_SEND_FRAME:
                    args.SENDING = True
                    args.frame_index += 1
                else:
                    pass
            else:
                if args.SENDING:
                    args.LAST_RESPONSE_TIME = time.time()
                finished = True
                args.SENDING = False
        else:
            frame_data = ''

        return json.dumps({'frame_index': args.frame_index,
                           # 减少带宽占用
                           'frame_data': frame_data if not finished else '',
                           'done': args.done.value,
                           'finished_flag': finished,
                           'iteration': args.iterations,
                           'sending': args.SENDING,
                           'finished_tasks': args.finished_tasks,
                           'fix_time_per_round': global_fix_time_per_round})


from main_interact import global_user_args, global_user_dict, global_fix_time_per_round
