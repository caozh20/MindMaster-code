import ast

from core.agent import Agent
from core.desire import Desire
from core.entity_utils import Is_Near
from core.world import World
from core.entity import Entity, Object, Landmark
from website.pipeline_common import get_intent_desc
from core.const import default_action_choices, action_description


def parse_entity(entity: Entity, W: World, verbose=True, entity_id=None):
    """解析实体为字符串表示，支持已删除的实体
    
    Args:
        entity: 要解析的实体
        W: 世界对象
        verbose: 是否生成详细描述
        entity_id: 实体ID，用于当entity为None时查找id_to_name_str
    
    Returns:
        实体的字符串表示
    """
    # 如果实体为None但提供了entity_id，尝试从id_to_name_str获取
    if entity is None:
        if entity_id is not None and entity_id in W.id_to_name_str:
            return W.id_to_name_str[entity_id]
        return f"unknown_entity_{entity_id}" if entity_id is not None else "unknown_entity"
    
    # 正常处理非None实体
    if isinstance(entity, Agent):
        return parse_agent(entity)
    return parse_object(entity, W, verbose)


def parse_to_entity(entity_desc, W: World):
    try:
        if isinstance(entity_desc, str):    
            entity_desc = ast.literal_eval(entity_desc)
    except:
        print(f"Error parsing entity_desc: {entity_desc}")
        pass
    for entity in W.entities:
        if entity_desc.startswith('agent') and isinstance(entity, Agent) and entity_desc == f'agent_{entity.id}':
            return entity
        if entity.name == entity_desc.split('_')[0]:
            if int(entity.id) == int(entity_desc.split('_')[-1]):
                return entity
            else:
                continue
    if entity_desc == "STOP":
        return entity_desc
    return None


def parse_agent(agent: Agent):
    return f'agent_{agent.id}'


def parse_object(obj: Object, W: World, verbose=True, entity_id=None):
    """解析对象为字符串表示，支持详细描述模式
    
    Args:
        obj: 要解析的对象
        W: 世界对象
        verbose: 是否生成详细描述
        entity_id: 实体ID，用于当obj为None时查找id_to_name_str
    
    Returns:
        对象的字符串表示
    """
    # 如果obj为None，尝试从id_to_name_str获取
    if obj is None:
        if entity_id is not None and entity_id in W.id_to_name_str:
            return W.id_to_name_str[entity_id]
        return f"unknown_object_{entity_id}" if entity_id is not None else "unknown_object"
    
    # 非None对象的处理
    if not verbose:
        return f'{obj.name}_{obj.id}'
    
    if obj.is_container:
        return f'{obj.name}_{obj.id}'
    
    return f'{obj.name}_{obj.id}'

# format of action_history(action_name_list, iteration)
# action_name 后面带着自己的id，prompt 里可以省去这个id
def parse_action_history(action_history, W: World):
    action_list = []
    if action_history is None:
        return action_list
        
    for action_tuple in action_history:
        # 长度至少为3
        if len(action_tuple) == 3:
            action_list.append([action_tuple[-1], action_tuple[0]])
        elif len(action_tuple) == 4:
            # 需要对 explore 进行兼容
            if action_tuple[2] is not None and action_tuple[2] != 'None' and action_tuple[2] != '-1' and action_tuple[2] != -1:
                entity_id = int(action_tuple[2])
                target = W.retrieve_by_id(entity_id)
                
                # 传递entity_id给parse_entity
                entity_str = parse_entity(target, W, verbose=False, entity_id=entity_id)
                
                action_list.append([action_tuple[-1], action_tuple[0], entity_str])
            else:
                action_list.append([action_tuple[-1], action_tuple[0], action_tuple[2]])
        elif len(action_tuple) == 5:
            trg1_id = int(action_tuple[2])
            trg2_id = int(action_tuple[3])
            
            trg1 = W.retrieve_by_id(trg1_id)
            trg2 = W.retrieve_by_id(trg2_id)
            
            # 传递entity_id给parse_entity
            trg1_str = parse_entity(trg1, W, verbose=False, entity_id=trg1_id)
            trg2_str = parse_entity(trg2, W, verbose=False, entity_id=trg2_id)
            
            action_list.append([action_tuple[-1], action_tuple[0], trg1_str, trg2_str])
    return action_list

def check_agents_visibility(agent: Agent, W: World, other_agent_id):
    # you cannot see the other agent
    # you can see the other agent, and the other agent can see you
    # you can see the other agent, and the other agent cannot see you
    for entity in agent.observation:
        if entity.id == agent.id:
            continue
        if not isinstance(entity, Agent):
            continue

        # todo 0325
        # other_attentions base my attention
        other_attentions = [f'agent_{o.id}' if isinstance(o, Agent) else f'{o.name}_{o.id}'
                            for o in [*agent.observation, agent]
                            if o.id != entity.id and entity.attention_check(o, W) == 1]
        other_attentions_desc = f"{other_attentions} are now in agent_{entity.id}'s field of view"

        # other_attentions base my belief
        # other_attentions = [o for o in agent.belief if o.id != entity.id and entity.attention_check(o, W) == 1]

        if entity.attention_check(agent, W) == 1:
            return f'You and agent_{entity.id} can see each other, {other_attentions_desc}'
        else:
            return f'You can see agent_{entity.id}, and agent_{entity.id} cannot see you, {other_attentions_desc}'
    return f'You cannot see agent_{other_agent_id}'


def initial_prompts(agent: Agent, W: World):
    your_name = f'agent_{agent.id}'
    your_desire, others_desire = parse_both_desire(W, agent)
    your_initial_intent = get_intent_desc(agent, W)
    return f'''
    Imagine that there are two agents in a room, agent_1 and agent_2, and you are {your_name}. You can only use nonverbal signals to communicate.
    {your_desire}. 
    {others_desire}. 
    Your initially assigned goal is {your_initial_intent}, you can do it by yourself or request someone's help to do it based on your desire.
    Your Task: Engage in an interaction with the environment and other agents, making decisions based on your desires, beliefs, and the dynamics of the environment.
    '''


def observation_belief_prompts(timestamp, agent: Agent, W: World):
    agent_state, object_state, attention_list, reachable_entities = parse_current_attention(W=W, agent=agent)
    belief_list = parse_belief_not_attention(agent, W)
    holding_ids = parse_holdings(agent, W)
    visible_check = check_agents_visibility(agent, W, 3 - agent.id)
    your_2nd_belief = parse_2nd_belief(agent, W)
    return f'''
    [Observation] At time {timestamp}, {attention_list} are in your field of view, and {reachable_entities} are in your reachable distance, and {belief_list} are in your memory which means not in your field of view now.
    {object_state} You are holding {holding_ids}.  
    {visible_check}. {your_2nd_belief} You can remember the last position of objects that are in your memory.
    '''


def default_action_space_prompts():
    return f'''
    You can only choose your action from the following action space: {default_action_choices}. 
    Specifically, here are more explanations (Please understand the meaning of each action based on the following descriptions, rather than just their literal sense): {action_description}
    '''


def interaction_history_prompts(other_name, interaction_history_desc):
    return f'''
    You and {other_name} perform actions alternately. In some timestamps you may have no idea of {other_name}'s action if {other_name} is not in your field of view at that timestamp.
    {interaction_history_desc} Based on your interaction action history with {other_name}, what do you think is the most likely goal of {other_name}?
    '''


def constraints_hints_prompt():
    return f'''Please note that actions requiring interaction with objects, such as playing, must ensure the object is reachable.
    And when you choose to put something, it should be in your hands.
    When you choose an action, you must replace the 'somebody' or 'something' with concrete target instead of 'area_of_interest' or something else. Otherwise, the action will fail.
    The action should not include the timestamp. Note that the action must include '', thus [ActionExplore] is wrong, you should use ['ActionExplore'].
    The action must be chosen from the possible actions.
    When you want to give something to somebody, your should make sure the somebody is in your reachable distance.
    When you want to nod head or do other actions for social interaction, you should consider whether others can see your action.
    You can only choose one action. You cannot directly manipulate objects that are not within your current field of view or memory.
    In our setting, if you see an open box, then you can see all the entities inside it, if there are any.
    '''


def intent_estimation_prompts(other_name):
    return f'''
    Given your underlying desire and others' desire, your initially assigned intention and your estimation of {other_name}'s goal, your memory and new observation, and the previous interaction history, What's your most probable next action considering the physical feasibility of the action execution?
    Let's think step by step and then output the most rational answer following the prescribed action format which is wrapped in square brackets without nested squared brackets.
    '''


def react_setting():
    return f'''
    You need to generate your [Thought] and based on that thought, generate a legitimate [Action]. This [Action] will be submitted to the environment for execution, and the environment will return an [Observation] to you.
    '''


def react(timestamp, agent: Agent, W: World, other_name, interaction_history_desc):
    return initial_prompts(agent, W) \
           + default_action_choices() \
           + constraints_hints_prompt() \
           + interaction_history_prompts(other_name, interaction_history_desc) + intent_estimation_prompts(other_name) \
           + react_setting() + \
           observation_belief_prompts(timestamp, agent, W)


def caption_current_state_to_llm(agent: Agent, W: World):

    # 下面所有函数统一以World 开头
    # agent 指的是目前正在观察的agent 
    desire, others_desire = parse_both_desire(W, agent)
    agent_state, object_state, attention_list,  reachable_entities = parse_current_attention(W=W, agent=agent)
    other_reachable_entities_desc = parse_others_reachable_entities_in_belief(W=W, agent=agent)
    belief_list = parse_belief_not_attention(agent, W)
    holding_ids = parse_holdings(agent, W)
    others_observation = parse_others_obs(agent, W)

    parse_state_dict = {}
    parse_state_dict['other_name'] = f'agent_{3 - agent.id}'
    parse_state_dict['visible_check'] = check_agents_visibility(agent, W, 3-agent.id)
    # parse_state_dict['name'] = agent.name + '_' + str(agent.id)
    parse_state_dict['name'] = f'agent_{agent.id}'

    parse_state_dict['desire'] = desire
    parse_state_dict['attention'] = attention_list
    parse_state_dict['belief'] = belief_list
    parse_state_dict['2nd_belief'] = parse_2nd_belief(agent, W)

    parse_state_dict['reachable_entities'] = reachable_entities
    parse_state_dict['other_reachable_desc'] = other_reachable_entities_desc
    parse_state_dict['initial_intent'] = get_intent_desc(agent, W)
    parse_state_dict['intent_history_llm'] = agent.intent_history_llm
    parse_state_dict["other_intent_history_llm"] = agent.other_intent_history_llm
    parse_state_dict['action_history'] = parse_action_history(agent.action_history, W)
    # placeholder
    parse_state_dict['others_desire'] = others_desire
    parse_state_dict['the_other_action_history'] = []
    parse_state_dict["object_state"] = object_state
    parse_state_dict["agent_state"] = agent_state
    parse_state_dict['holding_ids'] = holding_ids
    parse_state_dict['others_observation'] = others_observation

    # 理论上，我们需要从belief 中拿到 对方agent 的 action_history
    # 但是由于我们Belief 类本身的限制，一旦被认定为false belief，就会被删除
    # 所以我们需要在belief 中添加一个属性，用来记录对方的action_history
    # for other_agent in agent.belief.agents:
    #     if other_agent.id == agent.id:
    #         continue
    #     parse_state_dict['the_other_action_history'] = parse_action_history(other_agent.action_history, W)
    #     break
    parse_state_dict['the_other_action_history'] = parse_action_history(agent.belief.other_agent_action_history, W)

    return parse_state_dict


def parse_others_obs(agent: Agent, W: World):
    others_observation = {}
    
    # 添加对None的检查
    if agent.belief.agents is None:
        return others_observation
        
    for other_agent in agent.belief.agents:
        if other_agent.id == agent.id:
            continue
        
        other_observation = []
        # 添加对None的检查
        if other_agent.observation is None:
            continue
            
        for entity in other_agent.observation:
            if entity.id == other_agent.id:
                continue
            
            entity_id = entity.id
            entity_in_world = W.retrieve_by_id(entity_id)
            other_observation.append(parse_entity(entity_in_world, W, verbose=False, entity_id=entity_id))
        
        others_observation[f'agent_{other_agent.id}'] = other_observation
    
    return others_observation


def parse_holdings(agent, W):
    holding_ids = []
    if agent.holding_ids is None:
        return holding_ids
        
    for entity_id in agent.holding_ids:
        entity = W.retrieve_by_id(entity_id)
        holding_ids.append(parse_entity(entity, W, verbose=True, entity_id=entity_id))
    return holding_ids


def parse_belief_not_attention(agent, W):
    belief_list = []
    attention_ids = [entity.id for entity in agent.observation]
    for entity in agent.belief.entities:
        if entity.id == agent.id:
            continue
        # not in current attention but in history belief
        if entity.id in attention_ids:
            continue
        
        # 保存实体ID
        entity_id = entity.id
        
        # 检查该实体是否存在于世界中
        world_entity = W.retrieve_by_id(entity_id)
        if isinstance(entity, Agent):
            belief_list.append(parse_agent(entity))
        else:
            # 传递entity_id参数
            belief_list.append(parse_entity(entity, W, verbose=True, entity_id=entity_id))
            
    return belief_list


def parse_both_desire(W: World, agent: Agent):
    desire = f'Your values: {agent.desire.parse()}'
    others_desire = ""
    for tmp in W.agents:
        if tmp.id == agent.id:
            continue
        others_desire += f"agent_{tmp.id}'s values: {tmp.desire.parse()}"
    return desire, others_desire

def parse_others_reachable_entities_in_belief(W: World, agent: Agent):
    target_reachable_entities = []
    other_agent = None
    for agent_tmp in agent.observation:
        if isinstance(agent_tmp, Agent) and agent_tmp.id != agent.id:
            other_agent = agent_tmp
            break
    if other_agent is None:
        return ""
    for entity in agent.belief.entities:
        if entity.id == agent.id:
            continue
        if other_agent.reachable_check(entity, W):
            target_reachable_entities.append(parse_entity(entity, W, verbose=False))
    target_reachable_entities_desc = ""
    if len(target_reachable_entities) > 0:
        target_reachable_entities_desc = f"Agent_{other_agent.id} can reach {target_reachable_entities}"
    return target_reachable_entities_desc

def parse_current_attention(W: World, agent: Agent):
    object_state = []
    agent_state = []
    attention_list = []
    reachable_entities = []

    # 添加对None的检查
    if agent.observation is None:
        return [], [], [], []
        
    for entity in agent.observation:
        if entity.id == agent.id:
            continue
        if isinstance(entity, Agent):
            attention_list.append(parse_agent(entity))
            if len(entity.holding_ids) != 0:
                agent_state.append(f"agent_{entity.id} is holding {entity.holding_ids}. ")
            if entity.waving:
                agent_state.append(f"agent_{entity.id} is waving. ")
            if entity.pointing:
                agent_state.append(f"agent_{entity.id} is pointing. ")
            if entity.nodding:
                agent_state.append(f"agent_{entity.id} is nodding. ")
            if entity.shaking:
                agent_state.append(f"agent_{entity.id} is shaking head. ")
            if entity.playing:
                agent_state.append(f"agent_{entity.id} is playing. ")
            if entity.performing:
                agent_state.append(f"agent_{entity.id} is performing {entity.performing}. ")
            if entity.speaking:
                agent_state.append(f"agent_{entity.id} is speaking {entity.speaking}. ")
            if entity.eating:
                agent_state.append(f"agent_{entity.id} is eating. ")
            if entity.attention_check(agent, W) is True:
                agent_state.append(f"agent_{entity.id} can observe me. ")
            tmp_observation_list = []
            tmp_reachable_list = []
            for entity_tmp in agent.observation:
                if entity_tmp.id == entity.id:
                    continue
                if entity.attention_check(entity_tmp, W) is True:
                    tmp_observation_list.append(parse_entity(entity_tmp, W, verbose=False))
                if entity.reachable_check(entity_tmp, W) and isinstance(entity_tmp, Object):
                    tmp_reachable_list.append(parse_entity(entity_tmp, W, verbose=False))
            if len(tmp_observation_list) == 0 and len(tmp_reachable_list) == 0:
                agent_state.append(f"In your current observation, agent_{entity.id} can observe nothing and can reach nothing. ")
            elif len(tmp_observation_list) == 0:
                agent_state.append(f"In your current observation, agent_{entity.id} can observe nothing but can reach {tmp_reachable_list}. ")
            elif len(tmp_reachable_list) == 0:
                agent_state.append(f"In your current observation, agent_{entity.id} can observe {tmp_observation_list} but can reach nothing. ")
            else:
                agent_state.append(f"In your current observation, agent_{entity.id} can observe {tmp_observation_list} and can reach {tmp_reachable_list}. ")
        else:
            attention_list.append(parse_entity(entity, W, verbose=False))

        if agent.reachable_check(entity, W) and isinstance(entity, Object):
            reachable_entities.append(parse_entity(entity, W, verbose=False))

        if isinstance(entity, Object):
            if entity.is_container:
                if entity.open:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is open. ")
                else:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is closed. ")
            if entity.needs_key:
                if entity.locked:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is locked. ")
                else:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is unlocked. ")
            # if len(entity.supporting_ids) != 0:
            if entity.is_supporter:
                if len(entity.supporting_ids) > 0:
                    tmp_prompt = f"{parse_entity(entity, W, verbose=False)} is supporting "
                    for supp_id in entity.supporting_ids:
                        supp_entity = W.retrieve_by_id(supp_id)
                        tmp_prompt += f"{parse_entity(supp_entity, W, verbose=False, entity_id=supp_id)}, "
                    tmp_prompt = tmp_prompt[:-2] + ". "
                    object_state.append(tmp_prompt)
                else:
                    object_state.append(f"There is nothing on {parse_entity(entity, W, verbose=False)}. ")

            if entity.is_game:
                object_state.append(f"{parse_entity(entity, W, verbose=False)} can be played. ")
            if entity.is_multiplayer_game:
                object_state.append(f"{parse_entity(entity, W, verbose=False)} requires two players for the game. ")
            if entity.being_played:
                object_state.append(f"{parse_entity(entity, W, verbose=False)} is being played. ")

            if len(entity.being_contained) > 0:
                be_contained_id = entity.being_contained[0]
                object_state.append(f"{parse_entity(entity, W, verbose=False)} is contained in {W.retrieve_by_id(be_contained_id).name}_{be_contained_id}. ")

        # 统一在agent_state以及object_state中添加entity的position
        # 如果是agent 还需要添加rotation
        if isinstance(entity, Agent):
            agent_state.append(f"{parse_entity(entity, W, verbose=False)} is at {[int(round(x, 0)) for x in entity.position]}. ")
            agent_state.append(f"{parse_entity(entity, W, verbose=False)} is facing {int(round(entity.rotate * 180, 0))}. ")
        else:
            object_state.append(f"{parse_entity(entity, W, verbose=False)} is at {[int(round(x, 0)) for x in entity.position]}. ")

        # 处理各种关系
        if hasattr(entity, 'contained_ids') and entity.contained_ids is not None:
            tmp_prompt = f"{parse_entity(entity, W, verbose=False, entity_id=entity.id)} contains "
            for cont_id in entity.contained_ids:
                cont_entity = W.retrieve_by_id(cont_id)
                # 传递entity_id参数
                tmp_prompt += f"{parse_entity(cont_entity, W, verbose=False, entity_id=cont_id)}, "
            tmp_prompt = tmp_prompt[:-2] + ". "
            object_state.append(tmp_prompt)
        
        # 处理being_contained关系
        if hasattr(entity, 'being_contained') and entity.being_contained is not None and len(entity.being_contained) > 0:
            be_contained_id = entity.being_contained[0]
            container = W.retrieve_by_id(be_contained_id)
            # 传递entity_id参数
            tmp_prompt = f"{parse_entity(entity, W, verbose=False, entity_id=entity.id)} is contained in {parse_entity(container, W, verbose=False, entity_id=be_contained_id)}. "
            object_state.append(tmp_prompt)
    return agent_state, object_state, attention_list, reachable_entities

def parse_world_state(W: World):
    # update: change state description to list to support difference based state prompt
    object_state = []
    agent_state = []
    attention_list = []
    reachable_entities = {}

    for entity in W.entities:
        if isinstance(entity, Agent):
            attention_list.append(parse_agent(entity))
            if len(entity.holding_ids) != 0:
                agent_state.append(f"agent_{entity.id} is holding {entity.holding_ids}. ")
            if entity.waving:
                agent_state.append(f"agent_{entity.id} is waving. ")
            if entity.pointing:
                agent_state.append(f"agent_{entity.id} is pointing. ")
            if entity.nodding:
                agent_state.append(f"agent_{entity.id} is nodding. ")
            if entity.shaking:
                agent_state.append(f"agent_{entity.id} is shaking head. ")
            if entity.playing:
                agent_state.append(f"agent_{entity.id} is playing. ")
            if entity.performing:
                agent_state.append(f"agent_{entity.id} is performing {entity.performing}. ")
            if entity.speaking:
                agent_state.append(f"agent_{entity.id} is speaking {entity.speaking}. ")
            if entity.eating:
                agent_state.append(f"agent_{entity.id} is eating. ")
            can_observe_list = []
            for tmp_entity in W.agents + W.objects + W.landmarks:
                if tmp_entity.id == entity.id:
                    continue
                if entity.attention_check(tmp_entity, W) is True:
                    if isinstance(tmp_entity, Object):
                        can_observe_list.append(parse_entity(tmp_entity, W, verbose=False))
                    elif isinstance(tmp_entity, Agent):
                        can_observe_list.append(parse_agent(tmp_entity))
            agent_state.append(f"agent_{entity.id} can observe {can_observe_list}. ")
        else:
            attention_list.append(parse_entity(entity, W, verbose=False))

        for agent in W.agents:
            if agent.reachable_check(entity, W) and isinstance(entity, Object):
                if reachable_entities.get(agent.id) is None:
                    reachable_entities[agent.id] = []
                reachable_entities[agent.id].append(parse_entity(entity, W, verbose=False))

        if isinstance(entity, Object):
            if entity.is_container:
                if entity.open:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is open. ")
                else:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is closed. ")
            if entity.needs_key:
                if entity.locked:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is locked. ")
                else:
                    object_state.append(f"{parse_entity(entity, W, verbose=False)} is unlocked. ")
            # if len(entity.supporting_ids) != 0:
            if entity.is_supporter:
                if len(entity.supporting_ids) > 0:
                    tmp_prompt = f"{parse_entity(entity, W, verbose=False)} is supporting "
                    for supp_id in entity.supporting_ids:
                        supp_entity = W.retrieve_by_id(supp_id)
                        tmp_prompt += f"{parse_entity(supp_entity, W, verbose=False, entity_id=supp_id)}, "
                    tmp_prompt = tmp_prompt[:-2] + ". "
                    object_state.append(tmp_prompt)
                else:
                    object_state.append(f"There is nothing on {parse_entity(entity, W, verbose=False)}. ")

            if entity.is_game:
                object_state.append(f"{parse_entity(entity, W, verbose=False)} can be played. ")
            if entity.is_multiplayer_game:
                object_state.append(f"{parse_entity(entity, W, verbose=False)} requires two players for the game. ")
            if entity.being_played:
                object_state.append(f"{parse_entity(entity, W, verbose=False)} is being played. ")

            if len(entity.being_contained) > 0:
                be_contained_id = entity.being_contained[0]
                object_state.append(f"{parse_entity(entity, W, verbose=False)} is contained in {W.retrieve_by_id(be_contained_id).name}_{be_contained_id}. ")

        # 统一在agent_state以及object_state中添加entity的position
        # 如果是agent 还需要添加rotation
        if isinstance(entity, Agent):
            agent_state.append(f"{parse_entity(entity, W, verbose=False)} is at {[int(round(x, 0)) for x in entity.position]}. ")
            agent_state.append(f"{parse_entity(entity, W, verbose=False)} is facing {int(round(entity.rotate * 180, 0))}. ")
        else:
            object_state.append(f"{parse_entity(entity, W, verbose=False)} is at {[int(round(x, 0)) for x in entity.position]}. ")

        # 处理各种关系
        if hasattr(entity, 'contained_ids') and entity.contained_ids:
            for cont_id in entity.contained_ids:
                cont_entity = W.retrieve_by_id(cont_id)
                # 传递entity_id参数
                container_str = parse_entity(entity, W, verbose=False, entity_id=entity.id)
                contained_str = parse_entity(cont_entity, W, verbose=False, entity_id=cont_id)
                object_state.append(f"{contained_str} is contained in {container_str}. ")
        
        # 处理supporting_ids
        if hasattr(entity, 'supporting_ids') and entity.supporting_ids:
            for supp_id in entity.supporting_ids:
                supp_entity = W.retrieve_by_id(supp_id)
                # 传递entity_id参数  
                supporter_str = parse_entity(entity, W, verbose=False, entity_id=entity.id)
                supported_str = parse_entity(supp_entity, W, verbose=False, entity_id=supp_id)
                object_state.append(f"{supported_str} is supported by {supporter_str}. ")
    return agent_state, object_state, attention_list, reachable_entities

def parse_2nd_belief(agent: Agent, W: World):
    second_belief = 'You think '
    flag = False
    for other_agent in agent.belief.agents:
        if other_agent.id == agent.id:
            continue
        second_belief += f'agent_{other_agent.id} knows '
        belief_list = []
        for entity in other_agent.belief.entities:
            if entity.id == other_agent.id:
                continue
            
            entity_id = entity.id
            entity_in_world = W.retrieve_by_id(entity_id)
            # 传递entity_id参数
            belief_list.append(parse_entity(entity_in_world, W, verbose=False, entity_id=entity_id))
        second_belief += str(set(belief_list))
    return second_belief + ' which maybe your false belief' if flag else ''


def fill_action_history(other_action_history, n):
    filled_action_history = []
    t = 0
    for i in range(n):
        if len(other_action_history) > t and other_action_history[t][0] == i:
            filled_action_history.append(other_action_history[t])
            t += 1
        else:
            filled_action_history.append(None)
    return filled_action_history


def single_action_desc(a, your_name):
    action_head = a[1]
    if action_head == 'ActionMoveTo':
        return f'moved to {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionRotateTo':
        return f'rotated to {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionNodHead':
        return f'nodded head to {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionWaveHand':
        return f'waved hand to {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionPointTo':
        return f'pointed to {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionPutOnto':
        return f'put {a[2]} onto {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionPutInto':
        return f'put {a[2]} into {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionFollowPointing':
        possessive = "your" if your_name == a[2] else f"{a[2]}'s"
        return f"followed {possessive} pointing"
    if action_head == 'ActionCheckWaving':
        possessive = "your" if your_name == a[2] else f"{a[2]}'s"
        return f"checked {possessive} waving"
    if action_head == 'ActionMoveToAttention':
        possessive = "your" if your_name == a[2] else f"{a[2]}'s"
        return f"moved to {possessive} attention"
    if action_head == 'ActionPlay':
        return f"played {a[2]}"
    if action_head == 'ActionObserveAgent':
        return f'observed {"you" if your_name == a[2] else a[2]}'
    if action_head == 'ActionExplore':
        return f'explored in the room'
    if action_head == 'ActionGrab':
        return f'grabbed the {a[2]}'
    if action_head == 'ActionOpen':
        return f'opened the {a[2]}'


def merge_action_history(timestamp, your_name, your_action_history, other_agent_name, other_action_history):
    if len(your_action_history) <= 0 and len(other_action_history) <= 0:
        return '', ''
    fill_other_history = fill_action_history(other_action_history, len(your_action_history))
    interaction_history_desc = ''
    interaction_history_desc_by_timestamp = {}
    for i, (a1, a2) in enumerate(zip(your_action_history, fill_other_history)):
        interaction_history_desc_ind = ''
        if your_name.endswith('_1'):
            interaction_history_desc_ind = f'At timestamp {i}, you have {single_action_desc(a1, your_name)} '
            if not a2:
                interaction_history_desc_ind += f'and have no idea of {other_agent_name}. '
            else:
                interaction_history_desc_ind += f'and then {other_agent_name} have {single_action_desc(a2, your_name)}. '
            interaction_history_desc += interaction_history_desc_ind
            interaction_history_desc_by_timestamp.update({i : interaction_history_desc_ind})
        else:
            interaction_history_desc_ind = f'At timestamp {i}, '
            if not a2:
                interaction_history_desc_ind += f'you have no idea of {other_agent_name} and you have {single_action_desc(a1, your_name)}. '
            else:
                interaction_history_desc_ind += f'{other_agent_name} have {single_action_desc(a2, your_name)} and then you have {single_action_desc(a1, your_name)}. '
            interaction_history_desc += interaction_history_desc_ind
            interaction_history_desc_by_timestamp.update({i : interaction_history_desc_ind})
            
    if not your_name.endswith('_1'):
        interaction_history_desc_ind = ''
        if len(other_action_history) > 0 and other_action_history[-1][0] == timestamp:
            interaction_history_desc_ind = f'At timestamp {timestamp}, {other_agent_name} have {single_action_desc(other_action_history[-1], your_name)}.'
        else:
            interaction_history_desc_ind = f'At timestamp {timestamp}, you have no idea of {other_agent_name}.'
        
        interaction_history_desc += interaction_history_desc_ind
        interaction_history_desc_by_timestamp.update({timestamp : interaction_history_desc_ind})
    
    return interaction_history_desc, interaction_history_desc_by_timestamp


### 需要优化，从预测的intent变成更好的自然语言
def parse_intent(i1):
    intent_history_ind = ""
    if "[" in i1:
        items = i1.split(",")
        action = items[0][1:]
        if len(items) == 1:
            action_ = action[0:-1]
            return f" {action_}"
        obj = items[1][0:]
        if len(items) >= 3:
            if items[2] == "None":
                intent_history_ind += f" {action} {obj}"
            if items[2] != 'None' and "[" not in items[2]:
                obj2 = items[2][0:-1]
                intent_history_ind += f" {action} {obj} with {obj2}"
            if "[" in items[2] and len(items)==4:
                sub_action = items[2][1:].replace("Action","").replace("[","")
                sub_obj2 = items[3][0:-2]
                intent_history_ind += f" {action} from {obj} to {sub_action} {sub_obj2}"
            if "[" in items[2] and len(items)==5:
                sub_action = items[2][1:].replace("Action","").replace("[","")
                sub_obj2 = items[3]
                sub_obj3 = items[4][0:-2]
                intent_history_ind += f" {action} from {obj} to {sub_action} {sub_obj2} onto {sub_obj3}"
            if "[" in items[2] and len(items)==6:
                sub_action = items[2][1:].replace("Action","").replace("[","")
                sub_obj2 = items[3]
                sub_obj3 = items[4]
                sub_obj4 = items[5][0:-2]
                intent_history_ind += f" {action} from {obj} to {sub_action} {sub_obj2} {sub_obj3} {sub_obj4}"
                
        else:
            intent_history_ind += f" {action} {obj},"
                   
    else:
        items_list = i1.split("_")
        new_items_list=[]
        for i in range(len(items_list)):
            if items_list[i].isdigit():
                new_item = items_list[i-1] + "_" + items_list[i]
                new_items_list[-1] = new_item
            else:
                new_items_list.append(items_list[i])
                
        intent_history_ind = " ".join(new_items_list)
    return intent_history_ind

def merge_intent_history(timestamp, your_name, your_intent_history, other_agent_name, other_intent_history):
    intent_history_by_timestamp = {}
    if len(your_intent_history) <= 0 and len(other_intent_history) <= 0:
        return ''
    
    # print("++++++++++++++")
    # print(your_intent_history)
    
    for i, (i1, i2) in enumerate(zip(your_intent_history, other_intent_history)):
        
        i1 = i1.replace("I","you")
        i1 = i1.replace("A","a")
        i1 = i1.replace("My","Your")
        i1 = i1.replace("my","your")
        i2 = i2.replace("A","a")
        
        intent_history_ind = i1
        other_intent_history_ind = i2
        
        # impossible not knowing your self intent
        
        # intent_history_ind = ""
        # other_intent_history_ind = ""
        # assert "unknown" not in i1
        # if "initiate" in i1:
            # continue
        
        # use description directly and omit the parsing process
        # self_intent_ind = parse_intent(i1)
        # intent_history_ind = f"Because you want to " + self_intent_ind + ','
                      
        # if "unknown" in i2 or "Unknown" in i2:
        #     other_intent_history_ind = f", but you cannot infer {other_agent_name}'s intent. "
        # else:
        #     other_intent_ind = parse_intent(i2)
        #     other_intent_history_ind = f" and you guess that {other_agent_name} wants to " + other_intent_ind + '. '

        intent_history_by_timestamp.update({i:intent_history_ind + " and " + other_intent_history_ind})
    
    return intent_history_by_timestamp 
            
def merge_intent_and_action_history(timestamp, interaction_history_desc_by_timestamp, intent_history_desc):
    history = ""
    # print(interaction_history_desc_by_timestamp)
    # print(intent_history_desc)
    # assert len(interaction_history_desc_by_timestamp) == len(intent_history_desc)
    for tmp in range(len(interaction_history_desc_by_timestamp)):
        history += interaction_history_desc_by_timestamp[tmp] 
        if intent_history_desc and intent_history_desc.get(tmp, None): 
            history += intent_history_desc[tmp]
    
    return history

if __name__ == '__main__':

    history = [[0, 'Action1'], [3, 'Action2'], ]
    fill_action_history(history, 5)
