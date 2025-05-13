import numpy as np
import random
import time
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from core.action import *
from core.agent import *
from core.entity_utils import Is_Near
from core.world import World

# 用户参与的最大轮数
MAX_ITERATIONS = 20
USER_FILE_PATH = 'user_tasks.json'

class FinishStatus(Enum):
    SUCCESS = 0
    DOING = 1
    REACH_MAX_ITER = 2

@unique
class PlayingStatus(Enum):
    PLAYING = 'playing'
    FINISHED = 'finished'
    QUIT = 'quit'


def valid_action(world, user, user_action):
    # 针对各个Action作进一步检测
    # 手占用检测
    if user_action.name()[0] == "ActionOpen":
        if user.hands_occupied:
            return False, "Hands are occupied! Try another solution based on your value."
        if user_action.target.locked:
            return False, "The container is locked! Please unlock it first with the key."
    if user_action.name()[0] == "ActionClose":
        if user.hands_occupied:
            return False, "Hands are occupied! Try another solution based on your value."
    if user_action.name()[0] == 'ActionGrab':
        being_contained = user_action.target.being_contained
        if len(being_contained) > 0:
            where = world.retrieve_by_id(being_contained[0])
            if hasattr(where, 'open') and not where.open:
                return False, 'It\'s contained! You need to open the container first.'
        if user_action.target.is_broken:
            return False, 'You cannot pick up a broken object.'
    if user_action.name()[0] == 'ActionUnlock':
        if not user_action.target.locked:
            return False, "The container is unlocked!!!"
        have_key = False
        for holding_id in user.holding_ids:
            if world.retrieve_by_id(holding_id).is_key:
                have_key = True
        if not have_key:
            return False, "The container is locked! You need to find the key."
    if user_action.name()[0] == "ActionPutInto":
        container = user_action.destination
        if not container.open:
            return False, f"The container ({container.name}) is closed! Please open it first."
    # if user_action.name()[0] == "ActionMoveTo":
    #     # if user_action.agent.attention_check(user_action.target, W=args.world) is not True:
    #     if user_action.agent.attention_check(user_action.target, W=world) == -1:
    #         return False, "You have to rotate to the target before you move to it. "
    if user_action.name()[0] == "ActionPlay":
        game_id = user_action.name()[2]
        game = world.retrieve_by_id(int(game_id))
        if game.is_multiplayer_game:
            near_count = 0
            for agent in world.agents:
                if Is_Near(agent, game, world, offset=20):
                    near_count += 1
            if near_count <= 1:
                return False, "The game requires more than two players, but currently, only you are nearby. Please invite others to join."
    return True, None


def get_intent_desc(client_agent: Agent, world):
    intent = None

    if client_agent.initial_intent:
        intent = client_agent.initial_intent
        # print('initial_intent print:', intent.print())
    else:
        if client_agent.intent_now is not None:
            intent = client_agent.intent_now
        for intent_type in INTENTS_PRIORITY_LIST:
            if intent_type in client_agent.intents and len(client_agent.intents[intent_type]) > 0:
                intent = client_agent.intents[intent_type][0]
    # print('intent print:', intent.print())
    desc = ''
    if intent is not None:
        if intent.soc_intent is not None:
            # target_agent_name = world.retrieve_by_id(intent.soc_intent[1]).name
            target_agent_name = f'agent_{world.retrieve_by_id(intent.soc_intent[1]).id}'
            if len(intent.soc_intent) >= 3 and isinstance(intent.soc_intent[2], Intent):
                ind_intent_desc = get_ind_intent_desc(intent.soc_intent[2].ind_intent, world)
                if not ind_intent_desc:
                    desc = 'none'
                else:
                    if intent.soc_intent[0] == 'request_help':
                        desc = "request {}'s help to {}".format(target_agent_name, ind_intent_desc)
                    elif intent.soc_intent[0] == 'help':
                        desc = 'help {} to {}'.format(target_agent_name, ind_intent_desc)
            elif intent.soc_intent[0] == 'play_with':
                target_obj_name = world.retrieve_by_id(intent.soc_intent[2]).name
                desc = 'play {} with {} together'.format(target_obj_name, target_agent_name)
            else:
                target_obj_name = world.retrieve_by_id(intent.soc_intent[2]).name
                desc = '{} {} {}'.format(intent.soc_intent[0], target_agent_name, target_obj_name)
        elif intent.ind_intent is not None:
            desc = get_ind_intent_desc(intent.ind_intent, world)
            if not desc:
                desc = 'none'
    else:
        desc = 'none'
    # return desc.title() if desc is not None else ""
    return desc if desc is not None else ""


def generate_start_action_option_dict(agents, objects):
    agent_name_id_list = []
    for agent in agents:
        agent_name_id_list.append([agent.name, agent.id])
    agent_name_id_list = sorted(agent_name_id_list, key=lambda x: x[0])

    object_name_id_list = []
    for object in objects:
        object_name_id_list.append([object.name, object.id])

    object_name_id_list = sorted(object_name_id_list, key=lambda x: x[0])
    name_id_list = deepcopy(agent_name_id_list + object_name_id_list)

    return {
        'ActionWait': [],
        'ActionWaveHand': [deepcopy(agent_name_id_list)],
        'ActionNodHead': [deepcopy(agent_name_id_list)],
        'ActionShakeHead': [deepcopy(agent_name_id_list)],
        'ActionMoveToAttention': [deepcopy(agent_name_id_list)],
        'ActionPointTo': [deepcopy(name_id_list)],
        'ActionObserveAgent': [deepcopy(agent_name_id_list)],
        'ActionPlay': [deepcopy(object_name_id_list), deepcopy(agent_name_id_list)],
        'ActionFollowPointing': [deepcopy(agent_name_id_list)], 
        'ActionPutDown': [deepcopy(object_name_id_list)],
        'ActionEat': [deepcopy(object_name_id_list)], 
        'ActionSmash': [deepcopy(object_name_id_list)],
        'ActionOpen': [deepcopy(object_name_id_list)],
        'ActionClose': [deepcopy(object_name_id_list)],
        'ActionGrab': [deepcopy(object_name_id_list)],
        'ActionMoveTo': [deepcopy(name_id_list) + [['X: Y: ', 'X: Y: ']]],
        'ActionRotateTo': [deepcopy(name_id_list) + [['X: Y: ', 'X: Y: ']]],
        'ActionUnlock': [deepcopy(object_name_id_list), deepcopy(object_name_id_list)],
        'ActionGiveTo': [deepcopy(object_name_id_list), deepcopy(agent_name_id_list)],
        'ActionPutInto': [deepcopy(object_name_id_list), deepcopy(object_name_id_list)],
        'ActionPutOnto': [deepcopy(object_name_id_list), deepcopy(object_name_id_list)],
        'ActionSpeak': [[['Hello!', 'Hello!'], ['Thank you!', 'Thank you!']]], 
        'ActionPerform': [[['eat', 'eat'], ['drink', 'drink']]],
        # 'ActionCheckWaving': [deepcopy(agent_name_id_list)],
        # 'ActionHit': [deepcopy(object_name_id_list)],
        # 'ActionExplore': [],
        # 'ActionFollowGaze': [deepcopy(agent_name_id_list)],
    }


def get_action_option_dict(user, start_action_option_dict, world: World):
    # 检查物体与agent的距离，限制play, get等需要距离的动作
    action_option_dict = deepcopy(start_action_option_dict)
    for object in world.objects:
        name_id = [object.name, object.id]
        # 先检查在不在belief里面，如若不在则全部删去
        if user.belief.get(object) is None:
            # print('{} not in belief'.format(name_id))
            action_option_dict['ActionMoveTo'][0].remove(name_id)
            action_option_dict['ActionRotateTo'][0].remove(name_id)

            action_option_dict['ActionUnlock'][0].remove(name_id)
            action_option_dict['ActionUnlock'][1].remove(name_id)

            action_option_dict['ActionOpen'][0].remove(name_id)
            action_option_dict['ActionClose'][0].remove(name_id)
            action_option_dict['ActionPutDown'][0].remove(name_id)
            action_option_dict['ActionGrab'][0].remove(name_id)
            # action_option_dict['ActionHit'][0].remove(name_id)
            action_option_dict['ActionGiveTo'][0].remove(name_id)
            action_option_dict['ActionPointTo'][0].remove(name_id)
            action_option_dict['ActionPlay'][0].remove(name_id)
            action_option_dict['ActionPutInto'][0].remove(name_id)
            action_option_dict['ActionPutInto'][1].remove(name_id)
            action_option_dict['ActionPutOnto'][0].remove(name_id)
            action_option_dict['ActionPutOnto'][1].remove(name_id)
            action_option_dict['ActionEat'][0].remove(name_id)
            action_option_dict['ActionSmash'][0].remove(name_id)
        else:
            # 根据远近排除相应的动作
            if not Is_Near(user, object, world):
                # print('{} not near'.format(name_id))
                action_option_dict['ActionUnlock'][0].remove(name_id)
                action_option_dict['ActionUnlock'][1].remove(name_id)

                action_option_dict['ActionOpen'][0].remove(name_id)
                action_option_dict['ActionClose'][0].remove(name_id)
                action_option_dict['ActionGrab'][0].remove(name_id)
                action_option_dict['ActionGiveTo'][0].remove(name_id)
                action_option_dict['ActionPlay'][0].remove(name_id)
                action_option_dict['ActionPutInto'][0].remove(name_id)
                action_option_dict['ActionPutInto'][1].remove(name_id)
                action_option_dict['ActionPutOnto'][0].remove(name_id)
                action_option_dict['ActionPutOnto'][1].remove(name_id)
                # action_option_dict['ActionHit'][0].remove(name_id)
                action_option_dict['ActionEat'][0].remove(name_id)
                action_option_dict['ActionSmash'][0].remove(name_id)
            # else:
                # 根据状态排除可选项
            if not object.is_game:
                try:
                    action_option_dict['ActionPlay'][0].remove(name_id)
                except:
                    pass

            if object.id not in user.holding_ids:
                try:
                    action_option_dict['ActionPutDown'][0].remove(name_id)
                except:
                    pass

            if object.id not in user.holding_ids:
                try:
                    action_option_dict['ActionEat'][0].remove(name_id)
                except:
                    pass

            if object.id not in user.holding_ids:
                try:
                    action_option_dict['ActionSmash'][0].remove(name_id)
                except:
                    pass

            if 'banana' not in object.name:
                try: 
                    action_option_dict['ActionEat'][0].remove(name_id)
                except:
                    pass

            if 'cup' not in object.name:
                try: 
                    action_option_dict['ActionSmash'][0].remove(name_id)
                except:
                    pass

            if 'key' not in object.name:
                try:
                    action_option_dict['ActionUnlock'][1].remove(name_id)
                except:
                    pass

            if not object.is_container:
                try:
                    action_option_dict['ActionPutInto'][1].remove(name_id)
                except:
                    pass
                try:
                    action_option_dict['ActionOpen'][0].remove(name_id)
                except:
                    pass
                try:
                    action_option_dict['ActionUnlock'][0].remove(name_id)
                except:
                    pass
                try:
                    action_option_dict['ActionClose'][0].remove(name_id)
                except:
                    pass
            else:
                if object.open:
                    try:
                        action_option_dict['ActionOpen'][0].remove(name_id)
                    except:
                        pass
                    try:
                        action_option_dict['ActionUnlock'][0].remove(name_id)
                    except:
                        pass
                elif object.open == False:
                    try:
                        action_option_dict['ActionClose'][0].remove(name_id)
                    except:
                        pass
            # 是否支撑物
            if not object.is_supporter:
                try:
                    action_option_dict['ActionPutOnto'][1].remove(name_id)
                except:
                    pass
            # 是否被agent持有，如果是，则不能Moveto, Grab等
            # 不被持有的物体不能被PutInto, PutOnto, GiveTo
            # 不能hit自己持有的东西
            if len(object.being_held_id) and object.being_held_id[0] == user.id:
                try:
                    action_option_dict['ActionGrab'][0].remove(name_id)
                except:
                    pass
                try:
                    action_option_dict['ActionMoveTo'][0].remove(name_id)
                except:
                    pass
                # try:
                #     action_option_dict['ActionHit'][0].remove(name_id)
                # except:
                #     pass
                try:
                    action_option_dict['ActionRotateTo'][0].remove(name_id)
                except:
                    pass
            else:
                try:
                    action_option_dict['ActionPutInto'][0].remove(name_id)
                except:
                    pass
                try:
                    action_option_dict['ActionPutOnto'][0].remove(name_id)
                except:
                    pass
                try:
                    action_option_dict['ActionGiveTo'][0].remove(name_id)
                except:
                    pass
    for agent in world.agents:
        name_id = [agent.name, agent.id]
        if agent.id == user.id:
            action_option_dict['ActionPlay'][1].remove(name_id)
            continue
        # 检查belief
        if user.belief.get(agent) is None:
            action_option_dict['ActionMoveTo'][0].remove(name_id)
            action_option_dict['ActionRotateTo'][0].remove(name_id)
            # action_option_dict['ActionCheckWaving'][0].remove(name_id)
            action_option_dict['ActionWaveHand'][0].remove(name_id)
            action_option_dict['ActionMoveToAttention'][0].remove(name_id)
            action_option_dict['ActionPointTo'][0].remove(name_id)
            # action_option_dict['ActionFollowGaze'][0].remove(name_id)
            action_option_dict['ActionNodHead'][0].remove(name_id)
            action_option_dict['ActionShakeHead'][0].remove(name_id)
            action_option_dict['ActionFollowPointing'][0].remove(name_id)
            action_option_dict['ActionGiveTo'][1].remove(name_id)
            action_option_dict['ActionPlay'][1].remove(name_id)
            if not world.exist_in_last_belief(agent.id, user.id):
                action_option_dict['ActionObserveAgent'][0].remove(name_id)
            continue
        # 距离, give something to sb
        elif not Is_Near(user, agent, world):
            action_option_dict['ActionGiveTo'][1].remove(name_id)
        # 只有当有agent在waving的时候，才能够check follow
        # if not user.belief.get(agent).waving:
            # try:
            #     action_option_dict['ActionCheckWaving'][0].remove(name_id)
            # except:
            #     pass
        if not user.belief.get(agent).pointing:
            try:
                action_option_dict['ActionFollowPointing'][0].remove(name_id)
            except:
                pass
        # 有些动作不能对agent做
    # 去除一些自己和自己挥手，点头的操作
    name_id = [user.name, user.id]
    action_option_dict['ActionNodHead'][0].remove(name_id)
    action_option_dict['ActionShakeHead'][0].remove(name_id)
    action_option_dict['ActionWaveHand'][0].remove(name_id)
    action_option_dict['ActionMoveToAttention'][0].remove(name_id)
    action_option_dict['ActionPointTo'][0].remove(name_id)
    action_option_dict['ActionMoveTo'][0].remove(name_id)
    action_option_dict['ActionObserveAgent'][0].remove(name_id)
    # action_option_dict['ActionFollowGaze'][0].remove(name_id)
    # action_option_dict['ActionCheckWaving'][0].remove(name_id)
    action_option_dict['ActionRotateTo'][0].remove(name_id)
    action_option_dict['ActionFollowPointing'][0].remove(name_id)
    action_option_dict['ActionGiveTo'][1].remove(name_id)
    # 根据agent是否正在hit，添加hit stop
    # if user.hitting is not None:
    #     action_option_dict['ActionHit'][0].append(['Stop', -1])
    # 检查有无动作被完全否定
    # for action in ['ActionNodHead', 'ActionShakeHead', 'ActionWaveHand', 'ActionMoveToAttention', 'ActionGrab',
    #                'ActionPlay', 'ActionOpen', 'ActionUnlock', 'ActionPointTo', 'ActionRotateTo', 'ActionObserveAgent',
    #                'ActionFollowGaze', 'ActionPutDown', 'ActionCheckWaving', 'ActionMoveTo', 'ActionFollowPointing',
    #                'ActionHit', 'ActionEat', 'ActionSmash']:
    for action in ['ActionNodHead', 'ActionShakeHead', 'ActionWaveHand', 'ActionMoveToAttention',
                   'ActionGrab', 'ActionClose', 'ActionPlay', 'ActionOpen', 'ActionPointTo',
                   'ActionRotateTo', 'ActionObserveAgent', 'ActionMoveTo', 'ActionFollowPointing',
                   'ActionEat', 'ActionSmash','ActionPutDown',
                # 'ActionFollowGaze',
                   ]:
        if len(action_option_dict[action][0]) == 0:
            action_option_dict.pop(action)
    # 双参数动作：
    for action in ['ActionPutInto', 'ActionPutOnto', 'ActionGiveTo', 'ActionUnlock']:
        if len(action_option_dict[action][0]) == 0:
            action_option_dict.pop(action)
            continue
        if len(action_option_dict[action][1]) == 0:
            action_option_dict.pop(action)
            continue
    # 不显示参数
    for action in ['ActionWaveHand', 'ActionNodHead', 'ActionShakeHead']:
        if action in action_option_dict and len(action_option_dict[action][0]) > 0:
            action_option_dict[action] = []
    return action_option_dict


def map_para_to_entity(param, user_agent, world):
    param1, param2 = param.split(',')
    param1 = float(param1) * 1400 - 700
    param2 = - float(param2) * 1400 + 700
    pos = np.asarray([param1, param2])
    entity = world.locate_pos_with_entity(pos, user_agent)
    return entity, param1, param2


def parse_action(user_agent: Agent, world, action_desc):
    action, param1, param2 = action_desc['action'], action_desc['param1'], action_desc['param2']

    if action == 'ActionExplore':
        return ActionExplore(user_agent, None)

    if action == 'ActionMoveTo':
        if ',' in param1:
            entity, param1, param2 = map_para_to_entity(param1, user_agent, world)
            if entity is None:
                # print('does not match any entity')
                return ActionMoveTo(user_agent, [param1, param2])
            else:
                # print('match entity from pos:', entity.id)
                return ActionMoveTo(user_agent, world.retrieve_by_id(int(entity.id)))
        else:
            return ActionMoveTo(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionRotateTo':
        # mouse input
        if ',' in param1:
            entity, param1, param2 = map_para_to_entity(param1, user_agent, world)
            if entity is None:
                # print('does not match any entity')
                return ActionRotateTo(user_agent, [param1, param2])
            else:
                # print('match entity from pos:', entity.id)
                return ActionRotateTo(user_agent, world.retrieve_by_id(int(entity.id)))
        else:
            return ActionRotateTo(user_agent, world.retrieve_by_id(int(param1)))

    if action == 'ActionCheckWaving':
        # return ActionCheckWaving(client_agent, get_entity_in_whose_mind(int(param1), world, client_agent.id))
        return ActionCheckWaving(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionOpen':
        # return ActionOpen(client_agent, get_entity_in_whose_mind(int(param1), world, client_agent.id))
        return ActionOpen(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionClose':
        return ActionClose(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionUnlock':
        return ActionUnlock(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionGrab':
        return ActionGrab(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionHit':
        if int(param1) == -1:
            return ActionHit(user_agent, STOP)
        return ActionHit(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionGiveTo':
        return ActionGiveTo(user_agent, world.retrieve_by_id(int(param1)), world.retrieve_by_id(int(param2)))
    
    if action == 'ActionMoveToAttention':
        return ActionMoveToAttention(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionPointTo':
        return ActionPointTo(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionObserveAgent':
        return ActionObserveAgent(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionWait':
        return ActionWait(user_agent)
    
    if action == 'ActionWaveHand':
        if param1 == '':
            return ActionWaveHand(user_agent, None)
        return ActionWaveHand(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionNodHead':
        if param1 == '':
            return ActionNodHead(user_agent, None)
        return ActionNodHead(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionShakeHead':
        if param1 == '':
            return ActionShakeHead(user_agent, None)
        return ActionShakeHead(user_agent, world.retrieve_by_id(int(param1)))
    
    if action == 'ActionPlay':
        return ActionPlay(user_agent, world.retrieve_by_id(int(param1)), world.retrieve_by_id(int(param2)))
    if action == 'ActionPutInto':
        return ActionPutInto(user_agent, world.retrieve_by_id(int(param1)), world.retrieve_by_id(int(param2)))
    if action == 'ActionPutOnto':
        return ActionPutOnto(user_agent, world.retrieve_by_id(int(param1)), world.retrieve_by_id(int(param2)))
    if action == 'ActionPutDown':
        return ActionPutDown(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionFollowPointing':
        # return ActionFollowPointing(user_agent, world.retrieve_by_id(int(param1)))
        try:
            return ActionFollowPointing(user_agent, user_agent.belief.get(int(param1)))
        except:
            return ActionFollowPointing(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionFollowGaze':
        return ActionFollowGaze(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionEat':
        return ActionEat(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionSmash':
        return ActionSmash(user_agent, world.retrieve_by_id(int(param1)))
    if action == 'ActionSpeak': 
        return ActionSpeak(user_agent, str(param1))
    if action == 'ActionPerform':
        return ActionPerform(user_agent, str(param1))


# base who's belief to estimate other's intent
def get_belief_related_id_names_dict(world, who):
    id_name_dict = defaultdict(lambda: defaultdict(str))
    for agent in who.belief.agents:
        id_name_dict['agent'][agent.id] = agent.name
    for obj in who.belief.objects:
        id_name_dict['obj'][obj.id] = obj.name
    for ldm in who.belief.landmarks:
        id_name_dict['ldm'][ldm.id] = ldm.name
    for entity_id in who.intent_related_ids:
        entity = world.retrieve_by_id(entity_id)
        if isinstance(entity, Agent):
            id_name_dict['agent'][entity.id] = entity.name
        elif isinstance(entity, Object):
            id_name_dict['obj'][entity.id] = entity.name
        else:
            id_name_dict['ldm'][entity.id] = entity.name
    return id_name_dict


def get_ind_intent_desc(ind, world):
    main = ind[0]

    try:
        if ind[1] == 'world':
            obj_1 = ind[1]
        else:
            # obj_1 = world.retrieve_by_id(ind[1]).name
            obj_1 = trg_name_desc(ind[1], world)
    except:
        obj_1 = None

    try:
        # obj_2 = world.retrieve_by_id(ind[2]).name
        obj_2 = trg_name_desc(ind[2], world)
    except:
        obj_2 = None

    # if main in ['explore']:
    #     return 'explore in the room'

    if main in ['move_to']:
        return 'move to {}'.format(ind[1] if obj_1 is None else obj_1)

    # if main in ['give']:
    #     return 'give {} to {}'.format(obj_1, obj_2)

    if main in ['play_with']:
        splits = main.split('_')
        return '{} {} {} {}'.format(splits[0], obj_2, splits[1], obj_1)

    if main in ['put_into', 'put_onto']:
        # in or on
        splits = main.split('_')
        # return 'make {} {} {}'.format(obj_1, splits[1], obj_2)
        return '{} is {} {}'.format(obj_1, splits[1][:2], obj_2)


    # if main in ['inform']:
    #     return '{} {} {}'.format(main, obj_1, obj_2)
    # if main in ['get', 'find', 'open', 'greet', 'play']:
    #     if obj_2 is None:
    #         return '{} {}'.format(main, obj_1)
    #     else:
    #         return '{} {} from {}'.format(main, obj_1, obj_2)
    if main in ['greet', 'play']:
        if obj_2 is None:
            return '{} {}'.format(main, obj_1)
        else:
            return '{} {} from {}'.format(main, obj_1, obj_2)
    
    if main in ['get']:
        # if obj_2 is None:
        #     return 'get holding {}'.format(obj_1)
        # else:
        #     return 'get holding {} taken from {}'.format(obj_1, obj_2)
        return 'holding {}'.format(obj_1)
       

    if main in ['find']:
        if obj_2 is None:
            return 'find {}'.format(obj_1)
        else:
            return 'find {} taken from {}'.format(obj_1, obj_2)

    if main in ['give']:
        # return 'give {} to {}'.format(obj_1, obj_2)
        return '{} is holding {}'.format(obj_2, obj_1)
    
    if main in ['inform']:
        return 'make {} in {}\'s mind'.format(obj_1, obj_2)
            
    if main in ['open']:
        # if obj_2 is None:
        #     return 'make {} {}'.format(obj_1, main)
        # else:
        #     return 'make {} {} from {}'.format(obj_1, main, obj_2)
        return '{} is {}'.format(obj_1, main)
    
    if main in ['gaze_follow','observe']:
        return 'observe {}'.format(obj_1)


def trg_name_desc(trg_id, world):
    if not isinstance(world.retrieve_by_id(trg_id), Agent):
        return f'{world.retrieve_by_id(trg_id).name}_{world.retrieve_by_id(trg_id).id}'
    return f'agent_{world.retrieve_by_id(trg_id).id}'


def generate_intent_option_dict(world, who, me=None, mode='u2m') -> dict:
    if me is None:
        belief_related_id_names_dict = get_belief_related_id_names_dict(world, who)
    else:
        # base who's belief to estimate other's intent
        belief_related_id_names_dict = get_belief_related_id_names_dict(world, me)
    # intent_pool = ['Explore', 'Get', 'Give', 'Check', 'Find', 'Open', 'PutInto', 'PutOnto',
    #                'Greet', 'PlayWith', 'Follow', 'Refer', 'Inform', 'Confirm', 'ObserveAgent']
    intent_pool = ['Observe', 'Get', 'Give', 'Find', 'Open', 'PutInto', 'PutOnto',
                   'Greet', 'PlayWith', 'Inform', 'RespondTo', 'Harm']

    # high level(intent) => low level(tasks) => action;
    # action => low level(tasks) => high level(intent);
    # high level
    intent_option_dict = defaultdict(list)
    # low level means the decomposition of intent to tasks
    # tasks_option_dict = defaultdict(list)

    for intent_name in intent_pool:
        # if intent_name in ['Explore']:
        #    intent_option_dict[0].append(intent_name)
        #    tasks_option_dict[intent_name].append(intent_name)
        if intent_name in ['Observe']:
            # below equivalent to explore
            intent_option_dict[1].append(f'{intent_name}-world')
            # tasks_option_dict[f'{intent_name}-world'].append(f'{intent_name}-world')
            # below equivalent to observeAgent
            for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                if agent_name == who.name:
                    continue
                the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                intent_option_dict[1].append(f'{intent_name}-{the_agent_name}')
                # tasks_option_dict[f'{intent_name}-{the_agent_name}'].append(f'{intent_name}-{the_agent_name}')

        elif intent_name in ['Find']:
            for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                if agent_name == who.name:
                    continue
                the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                intent_option_dict[1].append(f'{intent_name}-{the_agent_name}')
                # tasks_option_dict[f'{intent_name}-{the_agent_name}'].append(f'{intent_name}-{the_agent_name}')

            for obj_id, obj_name in belief_related_id_names_dict['obj'].items():
                intent_option_dict[1].append(f'{intent_name}-{obj_name}_{obj_id}')
                # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}'].append(f'{intent_name}-{obj_name}_{obj_id}')
                # if world.retrieve_by_id(obj_id).is_container:
                #     tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}'].append(f'Open-{obj_name}_{obj_id}')

        elif intent_name in ['Check']:
            for obj_id, obj_name in belief_related_id_names_dict['obj'].items():
                intent_option_dict[1].append(f'{intent_name}-{obj_name}_{obj_id}')
                # if world.retrieve_by_id(obj_id).is_container:
                #     tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}'].append(f'Open-{obj_name}_{obj_id}')
                # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}'].append(f'{intent_name}-{obj_name}_{obj_id}')

            for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                if agent_name == who.name:
                    continue
                the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                intent_option_dict[1].append(f'{intent_name}-{the_agent_name}')
                # tasks_option_dict[f'{intent_name}-{the_agent_name}'].append(f'{intent_name}-{the_agent_name}')

        elif intent_name in ['RespondTo', 'Greet']:
            for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                if agent_name == who.name:
                    continue
                the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                intent_option_dict[1].append(f'{intent_name}-{the_agent_name}')
                # tasks_option_dict[f'{intent_name}-{the_agent_name}'].append(f'{intent_name}-{the_agent_name}')

        elif intent_name == 'Open':
            for obj_id, obj_name in belief_related_id_names_dict['obj'].items():
                if world.retrieve_by_id(obj_id).is_container:
                    intent_option_dict[1].append(f'{intent_name}-{obj_name}_{obj_id}')
                    # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}'].append(f'{intent_name}-{obj_name}_{obj_id}')

        elif intent_name in ['Inform', 'Refer']:
            for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                if agent_name == who.name:
                    continue
                the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                # refer/inform sb sth
                for obj_id, obj_name in belief_related_id_names_dict['obj'].items():
                    intent_option_dict[2].append(f'{intent_name}-{the_agent_name}-{obj_name}_{obj_id}')
                    # tasks_option_dict[f'{intent_name}-{the_agent_name}-{obj_name}_{obj_id}'].append(f'Find-{the_agent_name}')
                    # tasks_option_dict[f'{intent_name}-{the_agent_name}-{obj_name}_{obj_id}'].append(f'Find-{obj_name}_{obj_id}')
                    # tasks_option_dict[f'{intent_name}-{the_agent_name}-{obj_name}_{obj_id}'].append(f'Greet-{the_agent_name}')
                    # tasks_option_dict[f'{intent_name}-{the_agent_name}-{obj_name}_{obj_id}'].append(f'Refer-{the_agent_name}-{obj_name}_{obj_id}')

                # fixme 0419
                # refer/inform sb1 sb2
                for _agent_id, _agent_name in belief_related_id_names_dict['agent'].items():
                    if _agent_name == who.name:
                        continue
                    if _agent_name == agent_name:
                        continue
                    intent_option_dict[2].append(f'{intent_name}-{agent_name}-{_agent_name}')
                    # tasks_option_dict[f'{intent_name}-{agent_name}-{_agent_name}'].append(f'Find-{agent_name}')
                    # tasks_option_dict[f'{intent_name}-{agent_name}-{_agent_name}'].append(f'Find-{_agent_name}')
                    # tasks_option_dict[f'{intent_name}-{agent_name}-{_agent_name}'].append(f'Greet-{agent_name}')
                    # tasks_option_dict[f'{intent_name}-{agent_name}-{_agent_name}'].append(f'Refer-{agent_name}-{_agent_name}')

        elif intent_name in ['Give']:
            for obj_id, obj_name in belief_related_id_names_dict['obj'].items():
                for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                    if agent_name == who.name:
                        continue
                    the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                    intent_option_dict[2].append(f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}')
                    # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}'].append(f'Get-{obj_name}_{obj_id}')
                    # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}'].append(f'Give-{obj_name}_{obj_id}-{the_agent_name}')

        elif intent_name in ['PlayWith']:
            for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                if agent_name == who.name:
                    continue
                the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                for obj_id, obj_name in belief_related_id_names_dict['obj'].items():
                    if world.retrieve_by_id(obj_id).is_multiplayer_game:
                        # intent_option_dict[2].append(f'{intent_name}-{agent_name}-{obj_name}')
                        # tasks_option_dict[f'{intent_name}-{agent_name}-{obj_name}'].append(f'Attract-{agent_name}')
                        # tasks_option_dict[f'{intent_name}-{agent_name}-{obj_name}'].append(f'Refer-{agent_name}-{obj_name}')
                        # tasks_option_dict[f'{intent_name}-{agent_name}-{obj_name}'].append(f'{intent_name}-{agent_name}-{obj_name}')

                        intent_option_dict[2].append(f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}')
                        # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}'].append(f'Greet-{the_agent_name}')
                        # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}'].append(f'Refer-{the_agent_name}-{obj_name}_{obj_id}')
                        # tasks_option_dict[f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}'].append(f'{intent_name}-{obj_name}_{obj_id}-{the_agent_name}')

        elif intent_name in ['PutOnto', 'PutInto']:
            for obj_1_id, obj_1_name in belief_related_id_names_dict['obj'].items():
                for obj_2_id, obj_2_name in belief_related_id_names_dict['obj'].items():
                    if obj_2_id == obj_1_id:
                        continue
                    obj_1 = world.retrieve_by_id(obj_1_id)
                    obj_2 = world.retrieve_by_id(obj_2_id)

                    if obj_1.size[0]*obj_1.size[1] > obj_2.size[0]*obj_2.size[1]:
                        continue

                    if hasattr(obj_2, 'is_container') and obj_2.is_container:
                        intent_option_dict[2].append(f'PutInto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}')
                        # tasks_option_dict[f'PutInto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}'].append(f'Get-{obj_1_name}_{obj_1_id}')
                        # tasks_option_dict[f'PutInto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}'].append(f'PutInto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}')
                    if hasattr(obj_2, 'is_supporter') and obj_2.is_supporter:
                        intent_option_dict[2].append(f'PutOnto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}')
                        # tasks_option_dict[f'PutOnto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}'].append(f'Get-{obj_1_name}_{obj_1_id}')
                        # tasks_option_dict[f'PutOnto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}'].append(f'PutOnto-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}')

        elif intent_name in ['Get']:
            for obj_1_id, obj_1_name in belief_related_id_names_dict['obj'].items():
                for obj_2_id, obj_2_name in belief_related_id_names_dict['obj'].items():
                    if obj_2_id == obj_1_id:
                        continue
                    obj_2 = world.retrieve_by_id(obj_2_id)
                    if (hasattr(obj_2, 'is_container') and not obj_2.is_container) and (hasattr(obj_2, 'is_supporter') and not obj_2.is_supporter):
                        continue
                    intent_option_dict[2].append(f'{intent_name}-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}')
                    # tasks_option_dict[f'{intent_name}-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}'].append(f'{intent_name}-{obj_1_name}_{obj_1_id}-{obj_2_name}_{obj_2_id}')
                for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
                    if agent_name == who.name:
                        continue
                    the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
                    intent_option_dict[2].append(f'{intent_name}-{obj_1_name}_{obj_1_id}-{the_agent_name}')
                    # tasks_option_dict[f'{intent_name}-{obj_1_name}_{obj_1_id}-{the_agent_name}'].append(f'{intent_name}-{obj_1_name}_{obj_1_id}-{the_agent_name}')

                intent_option_dict[1].append(f'{intent_name}-{obj_1_name}_{obj_1_id}')
                # tasks_option_dict[f'{intent_name}-{obj_1_name}_{obj_1_id}'].append(f'{intent_name}-{obj_1_name}_{obj_1_id}')

    # help intent
    for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
        # help sb except me
        if agent_name == who.name:
            continue
        the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
        for num in [1, 2]:
            for ind_int in intent_option_dict[num]:
                if ind_int.startswith('Help') or ind_int.startswith('Request') or ind_int.startswith('Harm'):
                    continue
                if ind_int.startswith('Check'):
                    continue
                # two agent, cannot help to respond to
                if ind_int.startswith('RespondTo') or (ind_int.startswith("Observe") and "world" not in ind_int) or ind_int.startswith("Greet"):
                    continue
                # help sb put_into/put_onto
                if ind_int.startswith('Put'):
                    obj_1_name, obj_2_name = ind_int.split('-')[1:]
                    intent_option_dict[num+1].append(f'Help-{the_agent_name}-{ind_int}')
                    # tasks_option_dict[f'Help-{the_agent_name}-{ind_int}'].append(f'Get-{obj_1_name}')
                    # tasks_option_dict[f'Help-{the_agent_name}-{ind_int}'].append(f'{ind_int}')
                if ind_int.startswith('Open'):
                    intent_option_dict[num + 1].append(f'Help-{the_agent_name}-{ind_int}')
                    # tasks_option_dict[f'Help-{the_agent_name}-{ind_int}'].append(f'{ind_int}')

                # work only for two agents
                if the_agent_name == "me":
                    another_agent = [ag_name for _,ag_name in belief_related_id_names_dict['agent'].items() if ag_name != me.name][0]
                else:
                    another_agent = 'me'
                 
                # if ind_int.startswith('Inform'):
                #     new_int = ind_int.split('-')
                #     new_int[-2] = another_agent
                    
                #     if (me and new_int[-1] == me.name) or new_int[-1] == another_agent:
                #         new_int[-1] = the_agent_name
                    
                #     new_int = '-'.join(new_int)
                #     intent_option_dict[num + 1].append(f'Help-{the_agent_name}-{new_int}')
                #     # tasks_option_dict[f'Help-{the_agent_name}-{ind_int}'].append(f'{new_int}')

                # help sb get sth from sb/give sth to sb/playwith sth sb/ find sb
                if (
                    (ind_int.startswith('Get') and the_agent_name in ind_int) or
                    ind_int.startswith('Give') or
                    ind_int.startswith('PlayWith') or
                    (ind_int.startswith('Find') and the_agent_name in ind_int)
                    ):
                    new_int = ind_int.split('-')
                    new_int[-1] = another_agent
                    new_int = '-'.join(new_int)
                    intent_option_dict[num + 1].append(f'Help-{the_agent_name}-{new_int}')
                elif (
                    (ind_int.startswith('Get') and the_agent_name not in ind_int) or
                    (ind_int.startswith('Find') and the_agent_name not in ind_int) or
                    (ind_int.startswith("Observe") and "world" in ind_int)
                        ):
                    intent_option_dict[num + 1].append(f'Help-{the_agent_name}-{ind_int}')
            
                
                # at least three agents (me, sb1, sb2)
                # help sb1 to attract sb2 (sb1/sb2 != me) -- here means greetings
                if len(belief_related_id_names_dict['agent'].items()) >= 3:
                    another_agent = None
                    for _, other_name in belief_related_id_names_dict['agent'].items():
                        if other_name != who.name and other_name != agent_name:
                            another_agent = other_name

                    if ind_int.startswith('Greet'):
                        new_int = ind_int.split('-')
                        new_int[-1] = another_agent
                        new_int = '-'.join(new_int)
                        intent_option_dict[num + 1].append(f'Help-{the_agent_name}-{new_int}')
                        # tasks_option_dict[f'Help-{the_agent_name}-{ind_int}'].append(f'{new_int}')

                    if ind_int.startswith('Inform'):
                        new_int = ind_int.split('-')
                        new_int[-2] = another_agent
                        new_int = '-'.join(new_int)
                        intent_option_dict[num + 1].append(f'Help-{the_agent_name}-{new_int}')
                        # tasks_option_dict[f'Help-{the_agent_name}-{ind_int}'].append(f'{new_int}')

    # request_help intent
    for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
        # request_help sb except me
        if agent_name == who.name:
            continue
        the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
        for num in [1, 2]:
            for ind_int in intent_option_dict[num]:
                if ind_int.startswith('Help') or ind_int.startswith('Request') or ind_int.startswith('Harm'):
                    continue
                if ind_int.startswith('Check'):
                    continue
                # two agent, cannot request help to respond to
                if ind_int.startswith('RespondTo') or (ind_int.startswith("Observe") and "world" not in ind_int) or ind_int.startswith("Greet"):
                    continue
                if ind_int.startswith('Put'):
                    obj_1_name, obj_2_name = ind_int.split('-')[1:]
                    intent_option_dict[num+1].append(f'RequestHelp-{the_agent_name}-{ind_int}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Find-{the_agent_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Find-{obj_1_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Find-{obj_2_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Greet-{the_agent_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Refer-{the_agent_name}-{obj_1_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Refer-{the_agent_name}-{obj_2_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Observe-{the_agent_name}')
                if ind_int.startswith('Open') or ind_int.startswith('Get'):
                    intent_option_dict[num + 1].append(f'RequestHelp-{the_agent_name}-{ind_int}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Find-{the_agent_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Find-{ind_int.split("-")[1]}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Greet-{the_agent_name}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Refer-{the_agent_name}-{ind_int.split("-")[1]}')
                    # tasks_option_dict[f'RequestHelp-{the_agent_name}-{ind_int}'].append(f'Observe-{the_agent_name}')
                    
    # harm intent
    # harm somebody his individual intent
    for agent_id, agent_name in belief_related_id_names_dict['agent'].items():
        # request_help sb except me
        if agent_name == who.name:
            continue
        the_agent_name = 'me' if me is not None and mode == 'u2u' else agent_name
        for num in [1, 2]:
            for ind_int in intent_option_dict[num]:
                if ind_int.startswith('Help') or ind_int.startswith('Request') or ind_int.startswith('Harm'):
                    continue
                if ind_int.startswith('Check'):
                    continue
                # two agent, cannot harm to respond to/greet.
                # 目前的场景也不能harm observe。
                if ind_int.startswith('RespondTo') or ind_int.startswith("Observe") or ind_int.startswith("Greet"):
                    continue
                
                # work only for two agents
                if the_agent_name == "me":
                    another_agent = [ag_name for _,ag_name in belief_related_id_names_dict['agent'].items() if ag_name != me.name][0]
                else:
                    another_agent = 'me'

                if (
                    (ind_int.startswith('Get') and the_agent_name in ind_int) or
                    ind_int.startswith('Give') or
                    ind_int.startswith('PlayWith') or
                    (ind_int.startswith('Find') and the_agent_name in ind_int)
                    ):
                    new_int = ind_int.split('-')
                    new_int[-1] = another_agent
                    new_int = '-'.join(new_int)
                    intent_option_dict[num + 1].append(f'Harm-{the_agent_name}-{new_int}')
                elif (
                    ind_int.startswith('Put') or
                    ind_int.startswith('Open') or
                    (ind_int.startswith('Find') and the_agent_name not in ind_int) or
                    (ind_int.startswith('Get') and the_agent_name not in ind_int)
                    ):
                    intent_option_dict[num+1].append(f'Harm-{the_agent_name}-{ind_int}')
                # elif ind_int.startswith('Inform'):
                #     new_int = ind_int.split('-')
                #     new_int[-2] = another_agent
                #     if (me and new_int[-1] == me.name) or new_int[-1] == another_agent:
                #         new_int[-1] = the_agent_name
                #     new_int = '-'.join(new_int)
                #     intent_option_dict[num + 1].append(f'Harm-{the_agent_name}-{new_int}')
                    
                # tasks_option_dict[f'Harm-{the_agent_name}-{ind_int}'].append(f'Harm-{the_agent_name}-{ind_int}')

    # tasks_flat_option_list = list(set([task for task_list in list(tasks_option_dict.values()) for task in task_list]))
    # tasks_flat_option_list.sort()
    # return intent_option_dict, tasks_option_dict, tasks_flat_option_list
    return intent_option_dict


def _calc_user_agent_values_floating_pos(client_agent: Agent):
    pos = client_agent.position
    size = client_agent.size
    try:
        x, y = pos[0], pos[1]
        att = client_agent.attention

        if 0 <= att <= 1:
            y -= size + 8
            direction = 'up'
        else:
            y += size + 8
            direction = 'down'

        x_ratio = (x + 700) / 1400
        y_ratio = (700 - y) / 1400

        return {'x_ratio': x_ratio, 'y_ratio': y_ratio, 'direction': direction}
    except:
        return {}

def calc_agents_values_floating_pos(agents):
    agents_values = {}
    for agent in agents:
        agents_values[agent.id] = _calc_user_agent_values_floating_pos(agent)
    return agents_values


def action_to_desc(action, world: World):
    # ActionMoveTo => MoveTo
    action_head = action[0][6:] if action[0].startswith('Action') else action[0]
    params = []
    for para in action[2:-1]:
        if para.lower() == 'none':
            continue
        try:
            obj = world.retrieve_by_id(int(para))
            if '_' in obj.name:
                params.append(obj.name)
            else:
                params.append(f'{obj.name}_{obj.id}')        
        except:
            if ',' in para:
                x, y = para.strip('[]').split(',')
                x = x.split('.')[0]
                y = y.split('.')[0]
                # params.append(f'({x},{y})')
                # 不体现坐标信息
                params.append('')
                # print(f'{action_head}, raw para: {para}, processed para: {params[-1]}')
            else:
                params.append(para)
    # play sth with sb
    if action_head == 'Play' and len(params) == 2:
        params.insert(1, 'with')

    # Handle special action formatting cases
    if action_head == 'PutInto':
        action_head = 'Put'
        params.insert(1, 'into')
    elif action_head == 'PutOnto':
        action_head = 'Put' 
        params.insert(1, 'onto')
    elif action_head == 'PutDown':
        action_head = 'Put'
        params.append('down')
    elif action_head == 'GiveTo':
        action_head = 'Give'
        params.insert(1, 'to')
    elif action_head == 'FollowPointing':
        action_head = 'Follow'
        if params:
            params[0] = f"{params[0]}'s pointing"
    elif action_head == 'MoveToAttention':
        action_head = 'Move'
        if params:
            params = ['to', f"{params[0]}'s attention"]
    
    params_str = ' '.join(params)
    return f'{action_head} {params_str}'
