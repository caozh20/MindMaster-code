from human_study.recover_data import recover_world, heuristic
from core.finish_check import scenario_finish_check
from website.pipeline_common import get_action_option_dict, generate_start_action_option_dict
from copy import deepcopy

class Node():
    def __init__(self, agents, objects, landmarks, target_intent, agent_id):
        self.world = recover_world(agents, objects, landmarks)
        self.target_intent = target_intent
        self.agent_id = agent_id
        self.finish_check = scenario_finish_check(self.world, self.target_intent.to_scenario_name(self.agent_id))
        pass

    def heuristic(self):
        return heuristic(self.world, self.target_intent, self.agent_id)
    
    def is_goal(self):
        return self.finish_check(self.world, self.target_intent.to_scenario_name(self.agent_id))
    
    def get_valid_action(self):
        action_dict = generate_start_action_option_dict(self.world.agents, self.world.objects)
        user_agent = self.world.retrieve_by_id(self.agent_id)
        updated_action_dict = get_action_option_dict(user=user_agent, start_action_option_dict=action_dict, world=self.world)
        # 现在获得了所有可用的action_dict
        # 之后需要根据目标Intent 进一步筛选action
        # 不对，应该在初始化action_dict时就按intent来
        # 我们先处理自己一个人完成intent的情况，忽略social action



def generate_start_action_option_dict_by_intent_ind(agents, objects, target_intent):
    # 对于不同intent都通用的action
    general_action_dict = {
        'ActionPutDown': [deepcopy(object_name_id_list)],
        'ActionOpen': [deepcopy(object_name_id_list)],
        'ActionClose': [deepcopy(object_name_id_list)],
        'ActionGrab': [deepcopy(object_name_id_list)],
        'ActionMoveTo': [deepcopy(name_id_list) + [['X: Y: ', 'X: Y: ']]],
        'ActionRotateTo': [deepcopy(name_id_list) + [['X: Y: ', 'X: Y: ']]],
        'ActionUnlock': [deepcopy(object_name_id_list), deepcopy(object_name_id_list)],
    }

    # 之后根据不同的intent添加不同的action
    if 
    {
        'Get': 'Get..From..',
        'Give': 'Give..To..',
        'Find': 'Find',
        'Open': 'Open',
        'PutInto': 'Put..Into..',
        'PutOnto': 'Put..Onto..',
        'PlayWith': 'Play..With..',
        'RespondTo': 'RespondTo',
        'Inform': 'Inform',
        'Observe': 'Observe',
        'Greet': 'Greet',
        'Harm': 'Harm',
        'Help': 'Help',
        'RequestHelp': 'RequestHelp',
    }

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
        'ActionPlay': [deepcopy(object_name_id_list), deepcopy(agent_name_id_list)],
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
    }