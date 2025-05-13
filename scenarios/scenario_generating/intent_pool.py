# 可选的意图池，对于每一个意图，需要有配套的基本物体
# 字典表示或节点，列表表示与节点
# 字典或列表的前两位为保留位，用于标记各种信息
# 目前只针对物体的多样化生成，不增加agent数量
# 场景节点负责agent和必要的objects的部分属性的初始化，与或图负责其余辅助物体的初始化

import random
import copy
import numpy as np
import math
import time
from core.desire import Desire
from scenarios.scenario_generating.play_with_2_3 import PLAY_WITH_2_3
from scenarios.scenario_generating.put_into_3_4_baby import PUT_INTO_3_4_BABY
from scenarios.scenario_generating.request_help_2_open_3 import REQUEST_HELP_2_OPEN_3
from scenarios.scenario_generating.container import CONTAINER
from scenarios.scenario_generating.classroom import CLASSROOM
from scenarios.scenario_generating.baby import BABY
from scenarios.scenario_generating.cuptotable import CUPTOTABLE
from scenarios.scenario_generating.chimpanzee import CHIMPANZEE
from scenarios.scenario_generating.get_box import GET_BOX
from scenarios.scenario_generating.get_chess import GET_CHESS
from scenarios.scenario_generating.give import GIVE
from core.agent import Agent
from core.agent_utils import _attention_check
from core.entity import Entity
from core.const import ENTITY_SIZE_CONFIG

OBJECTS = {
    "phone": {
        #    ...
    },
    "chess": {
        'name': 'chess',
        'size': ENTITY_SIZE_CONFIG['chess'],
        'is_game': 1,
        'is_multiplayer_game': 1
    },
    "table": {
        'name': 'table',
        'size': ENTITY_SIZE_CONFIG['table'],
        'is_supporter': True,
    },
    "cup": {
        'name': 'cup',
        'size': ENTITY_SIZE_CONFIG['cup']
    },
    "banana": {
        'name': 'banana',
        'size': ENTITY_SIZE_CONFIG['banana']
    },
    # "ipad": {
    #     'name': 'ipad',
    #     'size': [70, 80]
    # },
    "box": {
        "name": "box",
        "size": ENTITY_SIZE_CONFIG['box'],
        "is_container": True,
        "open": False,
        "locked": False
    },
    "key": {
        "name": "key",
        "size": ENTITY_SIZE_CONFIG['key'],
        "is_key": True,
    },
    "shelf": {
        "name": "shelf",
        "size": ENTITY_SIZE_CONFIG['shelf'],
        "is_container": True,
        "open": False,
    },
    "books": {
        "name": "books",
        "size": ENTITY_SIZE_CONFIG['books'],
        
    },
    "timer": {
        "name": "timer",
        "size": ENTITY_SIZE_CONFIG['timer'],
    },
    "dumbbell": {
        "name": "dumbbell",
        "size": ENTITY_SIZE_CONFIG['dumbbell'],
    }
}


class Scenario_Generating:
    def __init__(self):
        intent_prototype = INTENT_POOL[random.randint(0, len(INTENT_POOL) - 1)]
        self.intent_name = intent_prototype["name"]
        self.objects = copy.deepcopy(intent_prototype['objects'])
        self.agents = copy.deepcopy(intent_prototype['agents'])
        self.landmarks = copy.deepcopy(intent_prototype['landmarks'])
        # 对于位置是否重叠的检查，要求每个物体在旋转的过程中不会与其他物体冲突，除非它是被放在物体上或是在容器内的
        # used_position元素： [up, down, left, right]
        self.have_timer = self.have_timer_check()
        self.used_position = []
        # 在生成agent时检查有无指定的holding，如果有，则单独处理
        # holding_dict: {id: position}，用于position生成
        self.holding_dict = {}
        self.make_agents()
        self.make_objects()

    @staticmethod
    def assign_agent_attention(agent):
        pos_x, pos_y = agent['pos']
        if pos_x < 0 and pos_y < 0:
            # [0, 0.5]
            agent['attention'] = random.random() / 2
        elif pos_x < 0 and pos_y > 0:
            # [-0.5, 0]
            agent['attention'] = -1 * random.random() / 2
        elif pos_x > 0 and pos_y < 0:
            # [0.5, 1]
            agent['attention'] = random.random() / 2 + 0.5
        else:
            # [-1, -0.5]
            agent['attention'] = random.random() / 2 - 1
        agent['rotate'] = agent['attention']

    def make_agents(self):
        if self.agents is None:
            return
        for agent in self.agents:
            if 'pos' not in agent:
                # random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                random_position = np.random.randint(-600, 600, 2)
                # 这里假设agent大小一直不变，都是50
                while not self.is_available_position(random_position, [50, 50]):
                    # random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                    random_position = np.random.randint(-600, 600, 2)
                agent['pos'] = np.asarray(random_position)
            else:
                # 检查初始化的位置是否正确，否则重新初始化
                while not self.is_available_position(agent['pos'], [50, 50]):
                    agent['pos'] = np.random.randint(-600, 600, 2)

            # sample desire
            agent['desire'] = Desire.sample_dict()

            Scenario_Generating.assign_agent_attention(agent)

            # holding检查
            if "holding_ids" in agent:
                holding = agent['holding_ids']
                for i in range(len(holding)):
                    self.holding_dict[holding[i]] = agent['pos']

    # 该函数不仅要补足已有的objects属性，还要添加新的objects
    # 应该保证场景中至少有三个物体
    def make_objects(self):
        # 先确定要添加物体的id
        id = 0
        if self.agents is not None:
            id += len(self.agents)
        if self.objects is not None:
            id += len(self.objects)
        if self.landmarks is not None:
            id += len(self.landmarks)

        # 不能同时出现两个timer
        while len(self.objects) < 3:
            object_selected = copy.deepcopy(OBJECTS[objects_pool[random.randint(0, len(objects_pool) - 1)]])
            if object_selected['name'] == 'ipad':
                if self.have_timer:
                    continue
                else:
                    self.have_timer = True
            self.objects.append(object_selected)
            id += 1
            object_selected['id'] = copy.deepcopy(id)

        # 之后每次以0.5的概率再次增加物体
        while random.random() < 0.5:
            object_selected = copy.deepcopy(OBJECTS[objects_pool[random.randint(0, len(objects_pool) - 1)]])
            if object_selected['name'] == 'ipad':
                if self.have_timer:
                    continue
                else:
                    self.have_timer = True
            self.objects.append(object_selected)
            id += 1
            object_selected['id'] = copy.deepcopy(id)

        # 记录选择的objects 中supporter. container的个数
        supporter_num = 0
        supporter_list = []
        container_num = 0
        container_list = []
        # 记录已经被容纳 or 支撑的物体
        having_been_interacted = []
        # 默认一个桌子或者容器只能支持或容纳一个物体
        for object_iter in self.objects:
            if object_iter['name'] == 'table' and 'supporting_ids' not in object_iter:
                supporter_num += 1
                supporter_list.append(object_iter)
            elif object_iter['name'] == 'box' and 'containing' not in object_iter:
                container_num += 1
                container_list.append(object_iter)
            if 'supporting_ids' in object_iter:
                having_been_interacted += object_iter['supporting_ids']
            if 'containing' in object_iter:
                having_been_interacted += object_iter['containing']
        # 根据supporter和container的数量决定哪些物体会被支撑或存放
        be_supported_num = 0
        be_contained_num = 0
        be_supported_dict = {}
        be_contained_dict = {}
        for object_iter in self.objects:
            if be_supported_num < supporter_num:
                if object_iter["name"] in can_be_supported and object_iter['id'] not in having_been_interacted and \
                        self.holding_dict.get(object_iter['id']) is None:
                    # 0.5的概率被放到桌子上
                    if random.random() < 0.5:
                        supporter = supporter_list[be_supported_num]
                        if 'supporting_ids' not in supporter:
                            supporter['supporting_ids'] = [object_iter['id']]
                        else:
                            supporter['supporting_ids'].append(object_iter['id'])
                        be_supported_num += 1
                        be_supported_dict[object_iter['id']] = supporter
                        continue
            if be_contained_num < container_num:
                if object_iter["name"] in can_be_contained and object_iter['id'] not in having_been_interacted and \
                        self.holding_dict.get(object_iter['id']) is None:
                    # 0.5的概率被放到桌子上
                    if random.random() < 0.5:
                        container = container_list[be_contained_num]
                        if 'being_contained' not in object_iter:
                            object_iter['being_contained'] = [container['id']]
                        else:
                            object_iter['being_contained'].append(container['id'])
                        if 'containing' not in container:
                            container['containing'] = [object_iter['id']]
                        else:
                            container['containing'].append(object_iter['id'])
                        be_contained_num += 1
                        be_contained_dict[object_iter['id']] = container
                        continue
        # 对于初始化时已经指定被交互的物体，根据交互物体的位置确定其位置
        # id: [position, rotate]
        interacting_dict = {}
        # 开始更新物体的位置与朝向
        for object_iter in self.objects:
            # 先检查是否被支撑或是容纳
            # 如果是的话，等待支撑物或容器位置更新完后再进行更新
            if object_iter['id'] in be_supported_dict or object_iter['id'] in be_contained_dict or object_iter[
                'id'] in having_been_interacted:
                continue
            elif 'pos' not in object_iter:
                # 再检查物体是否在初始化时就被容纳或是拿取了
                if 'being_held_id' in object_iter:
                    for agent in self.agents:
                        if agent['id'] == object_iter['being_held_id']:
                            object_iter['pos'] = agent['pos']
                else:
                    random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                    while not self.is_available_position(random_position,
                                                         [object_iter['size'][0] / 2, object_iter['size'][1] / 2]):
                        random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                    object_iter['pos'] = np.asarray(random_position)
            else:
                # 检查初始化的位置是否正确，否则重新初始化
                while not self.is_available_position(object_iter['pos'],
                                                     [object_iter['size'][0] / 2, object_iter['size'][1] / 2]):
                    object_iter['pos'] = np.asarray([random.random() * 1400 - 700, random.random() * 1400 - 700])
            # 随机选择rotate
            if 'rotate' not in object_iter:
                # 对于桌子，我们不妨让它朝上
                if object_iter['name'] == "table":
                    object_iter['rotate'] = 0.5
                else:
                    # object_iter['rotate'] = random.random()
                    object_iter['rotate'] = 0.5
            # 记录容器所支撑的物体的位置
            if 'supporting_ids' in object_iter:
                supporting = object_iter['supporting_ids']
                for i in range(len(supporting)):
                    target = self.get_object(supporting[i])
                    interacting_dict[supporting[i]] = [np.asarray([object_iter['pos'][0], object_iter['pos'][1] +
                                                                   object_iter['size'][1] // 2 + target['size'][
                                                                       1] // 2]),
                                                       object_iter['rotate']]
            if 'containing' in object_iter:
                containing = object_iter['containing']
                for i in range(len(containing)):
                    target = self.get_object(containing[i])
                    interacting_dict[containing[i]] = [object_iter['pos'], object_iter['rotate']]
                    # assert False
        # 开始更新被支撑或是被容纳的物体的位置
        # 对于被容纳的物体，其位置与容器相同
        # 对于被支撑的物体，其位置位于支撑物上方
        for object_iter in self.objects:
            if interacting_dict.get(object_iter['id']) is not None:
                object_iter['pos'] = interacting_dict[object_iter['id']][0]
                object_iter['rotate'] = interacting_dict[object_iter['id']][1]

    def is_available_position(self, pos, size, add=False):
        distance = math.sqrt(size[0] ** 2 + size[1] ** 2)
        up = pos[1] + distance
        down = pos[1] - distance
        left = pos[0] - distance
        right = pos[0] + distance
        if add:
            self.used_position.append([up, down, left, right])
            return True
        # 先检查是否越界
        if up > 700 or down < -700:
            return False
        if left < -700 or right > 700:
            return False
        if len(self.used_position):
            for used in self.used_position:
                # 先检查上下是否有重叠
                # used: [up, down, left, right]
                if down > used[0] or up < used[1]:
                    pass
                else:
                    if right < used[2] or left > used[3]:
                        pass
                    else:
                        return False
        self.used_position.append([up, down, left, right])
        return True

    # 检查object里是否有timer，以确保只生成一个timer
    def have_timer_check(self):
        for iter in self.objects:
            if iter['name'] == 'ipad':
                return True
        return False

    def get_object(self, id):
        for object in self.objects:
            if id == object['id']:
                return object


# objects_pool = ["chess", "table", "cup", "banana", "ipad", "box", "key", "toy"]
# can_be_supported = ["cup", "ipad", "banana"]
# can_be_contained = ["cup", "ipad", "banana"]
objects_pool = ["chess", "table", "cup", "banana", "box", "key","shelf","books","timer", "dumbbell"]
can_be_supported = ["chess", "cup", "banana", "key", "timer", "books","dumbbell"]
can_be_contained = ["chess", "cup", "banana", "key", "timer", "books","dumbbell"]
target_obj1_pool = ["chess", "cup", "banana", "key", "timer", "books","dumbbell"]
target_obj2_pool = ["shelf", "table", "box"]

# 可以根据自己的需要往池子里添加自己想要的intent
INTENT_POOL = [
    BABY,
    CONTAINER,
    CUPTOTABLE,
    PLAY_WITH_2_3,
    PUT_INTO_3_4_BABY,
    CHIMPANZEE, 
    # GET_BOX,
    GET_CHESS, 
    GIVE
    # REQUEST_HELP_2_OPEN_3,
    # CLASSROOM,
]

INTENT_POOL_RANDOM = [
    "get",
    "give",
    "find",
    "open",
    "put_into",
    "put_onto",
    "play_with"
]

agent_list = [{
    "id": 1,
    "name": 'agent 1',
    "desire": {}
    },
    {
    "id": 2,
    "name": 'agent 2',
    "desire": {}
    }]


class Scenario_Generating_Random:
    def __init__(self, control_test=False, room_exp_name=None, initial_value=None, initial_intent=None) -> None:
        if initial_intent is not None:
            self.initial_intent = initial_intent
        else:
            self.initial_intent = INTENT_POOL_RANDOM[random.randint(0, len(INTENT_POOL_RANDOM) - 1)]
        self.initial_value = initial_value
        self.intent_name = ""
        self.intent_name_another = None
        self.agents = copy.deepcopy(agent_list)
        self.objects = None
        self.landmarks = None
        # 对于位置是否重叠的检查，要求每个物体在旋转的过程中不会与其他物体冲突，除非它是被放在物体上或是在容器内的
        # used_position元素： [up, down, left, right]
        # self.have_timer = self.have_timer_check()
        self.used_position = []
        # 在生成agent时检查有无指定的holding，如果有，则单独处理
        # holding_dict: {id: position}，用于position生成
        self.holding_dict = {}
        if control_test:
            self.intent_diff = 0
        else:
            # 0 another no intent
            # 1 conflict intent item
            # 2 another different intent
            self.intent_diff = random.randint(0,2)
            print(f'init intent diff type in intent_pool.py : {self.intent_diff}, room_exp_name: {room_exp_name}')
        self.make_agents()
        box_cnt = self.rdn_necessary_objects()
        self.make_objects(box_cnt)
        self.generate_in_or_out_belief_obj()
        self.generate_in_or_out_belief_agent()
        print("for debug, intent name:", self.intent_name)
        print("for debug, intent name another:", self.intent_name_another)
        print("for debug, agents:", self.agents)
        print("for debug, objects:", self.objects)


    def make_agents(self):
        for i, agent in enumerate(self.agents):
            if 'pos' not in agent:
                # random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                random_position = np.random.randint(-600, 600, 2)
                # 这里假设agent大小一直不变，都是50
                while not self.is_available_position(random_position, [50, 50]):
                    # random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                    random_position = np.random.randint(-600, 600, 2)
                agent['pos'] = np.asarray(random_position)
            else:
                # 检查初始化的位置是否正确，否则重新初始化
                while not self.is_available_position(agent['pos'], [50, 50]):
                    agent['pos'] = np.random.randint(-600, 600, 2)

            if self.initial_value is not None:
                agent['desire'] = self.value_str2dict(self.initial_value[i])
            else:
                # sample desire
                agent['desire'] = Desire.sample_dict()

            Scenario_Generating.assign_agent_attention(agent)

            # holding检查, random 生成， 放到target_obj生成里面
            if "holding_ids" in agent:
                holding = agent['holding_ids']
                for i in range(len(holding)):
                    self.holding_dict[holding[i]] = agent['pos']
    
    @staticmethod
    def value_str2dict(value_str):
        # 去掉括号并分割字符串
        values = value_str.strip('()').split(',')
        # 转换为浮点数
        values = [float(v.strip()) for v in values]
        
        # 创建字典
        return {
            "active": values[0],
            "social": values[1],
            "helpful": values[2]
        }

    # 该函数不仅要补足已有的objects属性，还要添加新的objects
    # 应该保证场景中至少有三个物体
    # holding target_obj的scenario过于简单，不考虑初始化时holding something
    def rdn_necessary_objects(self):
        object_in_scene = []
        target_obj1 = None
        target_obj2 = None
        idx_id = 3
        with_intent_agent_idx = random.randint(0,1)
        
        box_cnt = 0
        
        add_box_for_find_init_intent = False
        
        target_obj1, target_obj2 = self.generating_intent_target_obj(self.initial_intent)
        
        print(f'first init intent {self.initial_intent}, target_obj1: {target_obj1} and target_obj2: {target_obj2}')
        
        if self.initial_intent == "find":
            target_obj1.update({"not_in_belief":True})
            add_box_for_find_init_intent = True
        target_obj1.update({'id':idx_id})
        
        if "not_contained_by" in target_obj1:
            target_obj1["not_contained_by"].append(idx_id+1)
        if "not_on" in target_obj1:
            target_obj1["not_on"].append(idx_id+1)
        
        object_in_scene.append(target_obj1)
        idx_id = idx_id + 1
        if target_obj2:
            target_obj2.update({'id': idx_id})
            if "not_containing" in target_obj2:
                target_obj2["not_containing"].append(idx_id-1)
            if "not_supporting" in target_obj2:
                target_obj2["not_supporting"].append(idx_id-1)
            object_in_scene.append(target_obj2)
            idx_id = idx_id + 1
        
        if self.initial_intent in ["put_into","open"]:
            box_cnt =  box_cnt + 1
                
        
        self.intent_name = self.update_intent_in_agent(with_intent_agent_idx, self.initial_intent, target_obj1, target_obj2)
        
        
        ### target_obj1是否在container中
        if not add_box_for_find_init_intent:
            in_or_not_in_container = random.randint(0, 1)
        else:
            in_or_not_in_container = 1
            print("init intent is find sth, add a box outside")
        
        ## 如果target_obj1 in container, container是否上锁。注意如果在container里，的位置摆放计算
        if in_or_not_in_container:
            # target_container_list = [item for item in target_obj2_pool if OBJECTS[item].get("is_container", None)] 
            # target_container = target_container_list[random.randint(0,len(target_container_list) - 1)]
            if not add_box_for_find_init_intent:
                box_cnt = box_cnt + 1
                print("add a box outside target_obj1 and the init intent is not find sth")
            container = copy.deepcopy(OBJECTS["box"])
            locked_or_not =  random.randint(0, 1)
            if locked_or_not and object_in_scene[0]["name"] != 'key':
                print("add a lock for init intent box")
                container["locked"] = True
                container["open"] = False
                container["needs_key"] = True
                container.update({'id': idx_id})
                container.update({'containing': [object_in_scene[0]['id']]})
                object_in_scene[0].update({'being_contained':[idx_id]})
                idx_id = idx_id + 1
                object_in_scene.append(container)
                key = copy.deepcopy(OBJECTS['key'])
                key.update({'id':idx_id})
                idx_id = idx_id + 1
                object_in_scene.append(key)
            else:
                container["locked"] = False
                print("no lock for init intent box")
                container.update({'id':idx_id})
                container.update({'containing': [object_in_scene[0]['id']]})
                object_in_scene[0].update({'being_contained':[idx_id]})
                idx_id = idx_id + 1
                object_in_scene.append(container)
        
        # self.objects = copy.deepcopy(object_in_scene)
        
        # another_w_intent, three cases generately randomly
        # another_w_intent = 0 # 0 another no intent
        # another_w_intent = 1 # 1 conflict intent item
        # another_w_intent = 2 # 2 another different intent
        # another_w_intent = random.randint(0,2)
        another_w_intent = copy.deepcopy(self.intent_diff)
        
        add_box_for_find_another_intent = False
        
        if another_w_intent == 0:
            self.objects = copy.deepcopy(object_in_scene)
            return box_cnt
        else:
            ## 也可能生成一样的intent，但是概率很小
            another_intent = INTENT_POOL_RANDOM[random.randint(0, len(INTENT_POOL_RANDOM) - 1)]
            target_obj1_another, target_obj2_another = self.generating_intent_target_obj(another_intent)
            
            print(f'another intent {another_intent}, first generate target_obj1: {target_obj1_another} and target_obj2: {target_obj2_another}')
            
            if another_w_intent == 2:   
                if another_intent == "find":
                    target_obj1_another.update({"not_in_belief": True})
                    add_box_for_find_another_intent = True
                
                target_obj1_another.update({'id':idx_id})
                
                if box_cnt >= 2:
                    print("box reaches maximum number 2")
                    if another_intent == "open":
                        self.intent_diff = 1
                        target_obj2_another = target_obj2
                        target_obj2_another.update({'open':False})
                        print("open same box, intent diff to be 1")
                        
                    elif another_intent == "put_into":
                        print("put into same box, intent diff to be 1")
                        self.intent_diff = 1
                        target_obj2_another = target_obj2
                        print(f'target_obj2_another replaced by target_obj2 {target_obj2}')
                        if "not_contained_by" not in target_obj1_another:
                            target_obj1_another["not_contained_by"] = [target_obj2["id"]]
                        else:
                            target_obj1_another["not_contained_by"].append(target_obj2["id"])
                        if "not_containing" not in target_obj2_another:
                            target_obj2_another.update({"not_containing":[idx_id]})
                        else:
                            target_obj2_another["not_containing"].append(idx_id)
                    else:
                        if target_obj2_another:
                            idx_id = idx_id + 1
                            target_obj2_another.update({'id':idx_id})
                            object_in_scene.append(target_obj2_another)
                            if another_intent == "put_onto":
                                if "not_on" not in target_obj1_another:
                                    target_obj1_another["not_on"] = [idx_id]
                                else:
                                    target_obj1_another["not_on"].append(idx_id)
                                if "not_supporting" not in target_obj2_another:
                                    target_obj2_another["not_supporting"] = [idx_id - 1]
                                else:
                                    target_obj2_another["not_supporting"].append(idx_id - 1)
                    
                    object_in_scene.append(target_obj1_another)
                    idx_id = idx_id + 1

                else:
                    if "not_contained_by" in target_obj1_another:
                        target_obj1_another["not_contained_by"].append(idx_id+1)
                    if "not_on" in target_obj1_another:
                        target_obj1_another["not_on"].append(idx_id+1)
                    
                    object_in_scene.append(target_obj1_another)
                    idx_id = idx_id + 1
                    if target_obj2_another:
                        target_obj2_another.update({'id': idx_id})
                        if "not_containing" in target_obj2_another:
                            target_obj2_another["not_containing"].append(idx_id-1)
                            box_cnt = box_cnt + 1
                        if "not_supporting" in target_obj2_another:
                            target_obj2_another["not_supporting"].append(idx_id-1)
                        object_in_scene.append(target_obj2_another)
                        idx_id = idx_id + 1
                # play_with another agent and if the agent has initial intent other than play_with, it leads to intent conflict
                if (
                    (self.initial_intent == "play_with" and another_intent != "play_with") or 
                    (another_intent == "play_with" and self.initial_intent != "play_with")
                    ):
                    self.intent_diff = 2
                if self.initial_intent == "play_with" and another_intent == "play_with":
                    self.intent_diff = 1
            else:
                if "open" not in [self.initial_intent, another_intent] and another_intent != "play_with":
                    if target_obj2 is None and target_obj2_another:
                        # target_obj2_another corresponds to put_into/put_onto obj2
                        target_obj1_another = target_obj1
                        if another_intent == "put_into":
                            target_obj1_another.update({"not_contained_by":[idx_id]})
                            target_obj2_another.update({'id': idx_id})
                            target_obj2_another.update({"not_containing":[target_obj1["id"]]})
                            box_cnt = box_cnt + 1
                        elif another_intent == "put_onto":
                            target_obj1_another.update({"not_on":[idx_id]})
                            target_obj2_another.update({'id': idx_id})
                            target_obj2_another.update({"not_supporting":[target_obj1["id"]]})
                        else:
                            target_obj2_another.update({'id': idx_id})
                        object_in_scene.append(target_obj2_another)
                        idx_id = idx_id + 1
                    elif target_obj2_another is None:
                        target_obj1_another = target_obj1
                        if another_intent == "find":
                            target_obj1_another.update({"not_in_belief":True})
                            if not add_box_for_find_init_intent:
                                add_box_for_find_another_intent = True
                    else:
                        if self.initial_intent == another_intent:
                            # 只有两个intent相同，才可以随意替换target_obj1和target_obj2
                            same_idx_1_or_2 = random.randint(0,1)
                            if same_idx_1_or_2 and box_cnt < 2 :
                                target_obj1_another = target_obj1
                                if another_intent == "put_into":
                                    target_obj1_another["not_contained_by"].append(idx_id)
                                    target_obj2_another.update({'id': idx_id})
                                    target_obj2_another.update({"not_containing":[target_obj1["id"]]})
                                    box_cnt = box_cnt + 1
                                elif another_intent == "put_onto":
                                    target_obj1_another["not_on"].append(idx_id)
                                    target_obj2_another.update({'id': idx_id})
                                    target_obj2_another.update({"not_supporting":[target_obj1["id"]]})
                                else:
                                    target_obj2_another.update({'id': idx_id})
                                object_in_scene.append(target_obj2_another)
                                idx_id = idx_id + 1
                            elif not same_idx_1_or_2 or box_cnt >= 2:
                                target_obj2_another = target_obj2
                                if another_intent == "put_into":
                                    target_obj2_another["not_containing"].append(idx_id)
                                    target_obj1_another.update({'id': idx_id})
                                    target_obj1_another.update({"not_contained_by":[target_obj2["id"]]})
                                elif another_intent == "put_onto":
                                    target_obj2_another["not_supporting"].append(idx_id)
                                    target_obj1_another.update({'id': idx_id})
                                    target_obj1_another.update({"not_on":[target_obj2["id"]]})
                                else:
                                    target_obj1_another.update({'id': idx_id})
                                object_in_scene.append(target_obj1_another)
                                idx_id = idx_id + 1
                        else:
                            # 一个是put_into, 一个是put_onto,只能替换target_obj1
                            target_obj1_another = target_obj1
                            # initial intent == put_into, another_intent == put_onto
                            if self.initial_intent == "put_into": 
                                target_obj1_another.update({"not_on":[idx_id]})
                                target_obj2_another.update({"not_supporting":[target_obj1["id"]]})
                            # initial intent == put_onto, another_intent == put_into
                            elif self.initial_intent == "put_onto":
                                target_obj1_another.update({"not_contained_by":[idx_id]})
                                target_obj2_another.update({"not_containing":[target_obj1["id"]]})
                            target_obj2_another.update({'id': idx_id})
                            object_in_scene.append(target_obj2_another)
                            idx_id = idx_id + 1
                if "play_with" != another_intent and "open" in [self.initial_intent, another_intent]:
                    # open只能和put_into互换target_obj2
                    if "put_into" in [self.initial_intent, another_intent]:
                        target_obj2_another = target_obj2
                        if another_intent == "put_into":
                            target_obj2_another.update({"not_containing":[idx_id]})
                        target_obj1_another.update({'id': idx_id})
                        object_in_scene.append(target_obj1_another)
                        idx_id = idx_id + 1
                    elif self.initial_intent == another_intent == "open":
                        #两个intent都是open
                        target_obj2_another = target_obj2
                        target_obj1_another = target_obj1                        
                    #排除了两个open intent后,如果一个intent为open，另外一个非put_into的intent，不能有重复的target_obj
                    elif self.initial_intent != another_intent:
                        self.intent_diff = 2
                        target_obj1_another.update({'id': idx_id})
                        if another_intent == "find":
                            target_obj1_another.update({"not_in_belief":True})
                            add_box_for_find_another_intent = True
                        object_in_scene.append(target_obj1_another)
                        idx_id = idx_id + 1
                        if target_obj2_another:
                            target_obj2_another.update({'id': idx_id})
                            object_in_scene.append(target_obj2_another)
                            if another_intent == "put_onto":
                                if "not_supporting" in target_obj2_another:
                                    target_obj2_another["not_supporting"].append(idx_id - 1)
                                if "not_on" in target_obj1_another:
                                    target_obj1_another["not_on"].append(idx_id)
                            idx_id = idx_id + 1
                
                if another_intent == "play_with" and self.initial_intent != "play_with":
                    if target_obj1["name"] != target_obj1_another["name"]:
                        self.intent_diff = 2
                        # another_intent "play_with", only one target_obj1_another chess
                        target_obj1_another.update({'id': idx_id})
                        object_in_scene.append(target_obj1_another)
                        idx_id = idx_id + 1
                    else:
                        # both chess for target_obj1 and target_obj1_another
                        target_obj1_another = target_obj1
                if another_intent == "play_with" and self.initial_intent == "play_with":
                    # another_intent == play_with == self.initial_intent
                    target_obj1_another = target_obj1

            
            self.intent_name_another = self.update_intent_in_agent((with_intent_agent_idx+1)%2, another_intent, target_obj1_another, target_obj2_another)
            
            print(f'another intent {self.intent_name_another}, after modification update target_obj1: {target_obj1_another} and target_obj2: {target_obj2_another}')
            
            
            if not add_box_for_find_another_intent:
                in_or_not_in_container = random.randint(0, 1)
            else:
                in_or_not_in_container = 1
                print("find sth for another intent, add box")
            
            ## 如果target_obj1 in container, container是否上锁。注意如果在container里，的位置摆放计算
            if in_or_not_in_container and target_obj1_another["id"] != target_obj1["id"] and box_cnt <= 2:
                # target_container_list = [item for item in target_obj2_pool if OBJECTS[item].get("is_container", None)] 
                # target_container = target_container_list[random.randint(0,len(target_container_list) - 1)]
                print("add box")
                container = copy.deepcopy(OBJECTS["box"])
                # if not add_box_for_find_another_intent:
                box_cnt = box_cnt + 1
                locked_or_not =  random.randint(0, 1)
                one_agent_idx = object_in_scene.index(target_obj1_another)
                if locked_or_not and target_obj1_another["name"] != 'key':
                    print("add box locked")
                    container["locked"] = True
                    container["open"] = False
                    container['needs_key'] = True
                    container.update({'id': idx_id})
                    container.update({'containing': [object_in_scene[one_agent_idx]['id']]})
                    object_in_scene[one_agent_idx].update({'being_contained':[idx_id]})
                    idx_id = idx_id + 1
                    object_in_scene.append(container)
                    key = copy.deepcopy(OBJECTS['key'])
                    key.update({'id':idx_id})
                    idx_id = idx_id + 1
                    object_in_scene.append(key)
                else:
                    container["locked"] = False
                    container.update({'id':idx_id})
                    container.update({'containing': [object_in_scene[one_agent_idx]['id']]})
                    object_in_scene[one_agent_idx].update({'being_contained':[idx_id]})
                    idx_id = idx_id + 1
                    object_in_scene.append(container)
            
        self.objects = copy.deepcopy(object_in_scene)
        return box_cnt
            
    def update_intent_in_agent(self, with_intent_agent_idx, initial_intent, target_obj1, target_obj2):
        self.agents[with_intent_agent_idx]['intent']={}
        idx_id = int(target_obj1["id"])
        # open 特殊处理，open target_obj2
        if initial_intent != 'open' and initial_intent != "play_with":
            self.agents[with_intent_agent_idx]['intent']['ind'] = [initial_intent, idx_id]
            self.agents[with_intent_agent_idx]['intent']['soc'] = None
            self.agents[with_intent_agent_idx]['intent']['comm'] = None
            self.agents[with_intent_agent_idx]['intent']['ref'] = None
            self.agents[with_intent_agent_idx]['intent']['type'] = 'LILU'
            intent_name = str(self.agents[with_intent_agent_idx]['id'])+"_"+initial_intent+"_"+str(idx_id)

        if initial_intent == "play_with":
            self.agents[with_intent_agent_idx]['intent']['ind'] = [initial_intent]
            self.agents[with_intent_agent_idx]['intent']['soc'] = None
            self.agents[with_intent_agent_idx]['intent']['comm'] = None
            self.agents[with_intent_agent_idx]['intent']['ref'] = None
            self.agents[with_intent_agent_idx]['intent']['type'] = 'LILU'
            intent_name = str(self.agents[with_intent_agent_idx]['id'])+"_"+initial_intent

        # print(initial_intent)
        # print(target_obj2)
        
        if target_obj2:
            idx_id_2 = int(target_obj2["id"])
            if initial_intent != "open":
                self.agents[with_intent_agent_idx]['intent']['ind'].append(idx_id_2)
                intent_name = intent_name+"_"+str(idx_id_2)
            # open 特殊处理，open target_obj2
            elif initial_intent == "open":
                self.agents[with_intent_agent_idx]['intent']['ind'] = [initial_intent, idx_id_2]
                self.agents[with_intent_agent_idx]['intent']['soc'] = None
                self.agents[with_intent_agent_idx]['intent']['comm'] = None
                self.agents[with_intent_agent_idx]['intent']['ref'] = None
                self.agents[with_intent_agent_idx]['intent']['type'] = 'HILU'
                intent_name = str(self.agents[with_intent_agent_idx]['id'])+"_"+initial_intent+"_"+str(idx_id_2)
    
        if initial_intent == "give" or initial_intent == "play_with":
            intent_name = intent_name+"_"+str(self.agents[(with_intent_agent_idx+1)%2]['id'])
            self.agents[with_intent_agent_idx]['intent']['ind'].append(self.agents[(with_intent_agent_idx+1)%2]['id'])
        
        if initial_intent == "play_with":
            intent_name = intent_name + "_"+str(idx_id)
            self.agents[with_intent_agent_idx]['intent']['ind'].append(idx_id)
        
        return intent_name
                
    def generating_intent_target_obj(self, initial_intent):
        
        #generating target obj        
        if initial_intent in ["put_into"]:
            target_container_list = [item for item in target_obj2_pool if OBJECTS[item].get("is_container", None)] 
            target_container = target_container_list[random.randint(0,len(target_container_list) - 1)]
            target_obj2 = copy.deepcopy(OBJECTS[target_container])
            target = target_obj1_pool[random.randint(0, len(target_obj1_pool) - 1)]
            target_obj1 = copy.deepcopy(OBJECTS[target])
            target_obj2["not_containing"] = []
            target_obj1["not_contained_by"] = []

        elif initial_intent in ["put_onto"]:
            target_supporter_list = [item for item in target_obj2_pool if OBJECTS[item].get("is_supporter", None)]
            target_supporter = target_supporter_list[random.randint(0,len(target_supporter_list) - 1)]
            target_obj2 = copy.deepcopy(OBJECTS[target_supporter])
            target = target_obj1_pool[random.randint(0, len(target_obj1_pool) - 1)]
            target_obj1 = copy.deepcopy(OBJECTS[target])
            target_obj1["not_on"] = []
            target_obj2["not_supporting"] = []

        elif initial_intent in ["play_with"] :
            target_obj1 = copy.deepcopy(OBJECTS["chess"])
            target_obj2 = None
            
        elif initial_intent in ["open"]:
            target_container_list = [item for item in target_obj2_pool if OBJECTS[item].get("is_container", None)] 
            target_container = target_container_list[random.randint(0,len(target_container_list) - 1)]
            target_obj2 = copy.deepcopy(OBJECTS[target_container])
            target_obj2["open"] = False
            if target_obj2["name"] == "box":
                target_obj2["locked"] = True
                target_obj2["needs_key"] = True
            target_obj1 = copy.deepcopy(OBJECTS["key"])
        else: # 
            target = target_obj1_pool[random.randint(0, len(target_obj1_pool) - 1)]
            target_obj1 = copy.deepcopy(OBJECTS[target])
            target_obj2 = None
        
        return target_obj1, target_obj2
               
    
    # 该函数不仅要补足已有的objects属性，还要添加新的objects
    # 应该保证场景中至少有三个物体
    def make_objects(self, box_cnt):
        # 先确定要添加物体的id
        id = 0
        if self.agents is not None:
            id += len(self.agents)
        if self.objects is not None:
            id += len(self.objects)
        if self.landmarks is not None:
            id += len(self.landmarks)

        # 不能同时出现两个timer
        while len(self.objects) < 3:
            object_name = objects_pool[random.randint(0, len(objects_pool) - 1)]
            object_selected = copy.deepcopy(OBJECTS[object_name])
            # if object_selected['name'] == 'ipad':
            #     if self.have_timer:
            #         continue
            #     else:
            #         self.have_timer = True
            if box_cnt >= 2 and object_name in ["box","shelf"]:
                continue
            elif box_cnt < 2 and object_name in ["box","shelf"]:
                box_cnt = box_cnt + 1
            self.objects.append(object_selected)
            id += 1
            object_selected['id'] = copy.deepcopy(id)

        # 之后每次以0.5的概率再次增加物体
        while random.random() < 0.5:
            object_name = objects_pool[random.randint(0, len(objects_pool) - 1)]
            object_selected = copy.deepcopy(OBJECTS[object_name])
            # if object_selected['name'] == 'ipad':
            #     if self.have_timer:
            #         continue
            #     else:
            #         self.have_timer = True
            if box_cnt >= 2 and object_name in ["box","shelf"]:
                continue
            elif box_cnt < 2 and object_name in ["box","shelf"]:
                box_cnt = box_cnt + 1
            self.objects.append(object_selected)
            id += 1
            object_selected['id'] = copy.deepcopy(id)

        # 记录选择的objects 中supporter. container的个数
        supporter_num = 0
        supporter_list = []
        container_num = 0
        container_list = []
        # 记录已经被容纳 or 支撑的物体
        having_been_interacted = []
        # 默认一个桌子或者容器只能支持或容纳一个物体
        for object_iter in self.objects:
            if object_iter['name'] == 'table' and 'supporting_ids' not in object_iter:
                supporter_num += 1
                supporter_list.append(object_iter)
            elif object_iter['name'] in ['box', 'shelf'] and 'containing' not in object_iter:
                container_num += 1
                container_list.append(object_iter)
            if 'supporting_ids' in object_iter:
                having_been_interacted += object_iter['supporting_ids']
            if 'containing' in object_iter:
                having_been_interacted += object_iter['containing']
        # 根据supporter和container的数量决定哪些物体会被支撑或存放
        be_supported_num = 0
        be_contained_num = 0
        be_supported_dict = {}
        be_contained_dict = {}
        for object_iter in self.objects:
            # print("supporter list", supporter_list)
            if be_supported_num < supporter_num:
                if object_iter["name"] in can_be_supported and object_iter['id'] not in having_been_interacted and \
                        self.holding_dict.get(object_iter['id']) is None and object_iter.get("not_in_belief", None) is None:
                    # 0.5的概率被放到桌子上
                    if random.random() < 0.5:
                        supporter = supporter_list[be_supported_num]
                        id_not_on = None
                        # print("single support", supporter)
                        if supporter.get("not_supporting", None):
                            id_not_on = supporter["not_supporting"][0]
                        if id_not_on and int(id_not_on) == int(object_iter['id']):
                            # print("id not on",id_not_on)
                            continue
                        if 'supporting_ids' not in supporter:
                            supporter['supporting_ids'] = [object_iter['id']]
                        else:
                            supporter['supporting_ids'].append(object_iter['id'])
                        be_supported_num += 1
                        be_supported_dict[object_iter['id']] = supporter
                        continue
            # print("container list", container_list)
            if be_contained_num < container_num:
                if object_iter["name"] in can_be_contained and object_iter['id'] not in having_been_interacted and \
                        self.holding_dict.get(object_iter['id']) is None:
                    # 0.5的概率被放到container里面
                    if random.random() < 0.5:
                        container = container_list[be_contained_num]
                        id_not_in = None
                        if object_iter['name'] == 'key' and container.get('locked', None) and container['locked'] == True:
                            continue
                        
                        # print("single container", container)
                        id_not_in_list = None
                        if container.get("not_containing", None):
                            id_not_in_list = container["not_containing"]
                        if id_not_in_list:
                            flag_list = False
                            for id_not_in in id_not_in_list:
                                if int(id_not_in) == int(object_iter['id']):
                                    flag_list = True
                            if flag_list:
                                # print("id not in", id_not_in)
                                continue
                        if 'being_contained' not in object_iter:
                            object_iter['being_contained'] = [container['id']]
                        else:
                            object_iter['being_contained'].append(container['id'])
                        if 'containing' not in container:
                            container['containing'] = [object_iter['id']]
                        else:
                            container['containing'].append(object_iter['id'])
                        be_contained_num += 1
                        be_contained_dict[object_iter['id']] = container
                        continue
        # 对于初始化时已经指定被交互的物体，根据交互物体的位置确定其位置
        # id: [position, rotate]
        interacting_dict = {}
        # 开始更新物体的位置与朝向
        for object_iter in self.objects:
            # 先检查是否被支撑或是容纳
            # 如果是的话，等待支撑物或容器位置更新完后再进行更新
            if object_iter['id'] in be_supported_dict or object_iter['id'] in be_contained_dict or object_iter[
                'id'] in having_been_interacted:
                continue
            elif 'pos' not in object_iter:
                # 再检查物体是否在初始化时就被容纳或是拿取了
                if 'being_held_id' in object_iter:
                    for agent in self.agents:
                        if agent['id'] == object_iter['being_held_id']:
                            object_iter['pos'] = agent['pos']
                elif "not_in_belief" in object_iter:
                    idx_object = object_iter["id"]
                    agent_with_find_intent = []
                    flag = False
                    for agent in self.agents:
                        if not agent.get("intent", None) or not agent["intent"].get("ind", None):
                            continue
                        # find obj cannot be in the view field of which agent
                        # print(f'for debug: {agent}')
                        if agent["intent"]["ind"][0] == "find" and int(agent["intent"]["ind"][1]) == int(idx_object):
                            current_agent = Agent(name=agent["name"], id = agent["id"], attention=agent["rotate"], position=agent["pos"])
                            agent_with_find_intent.append(current_agent)
                            flag = True

                    random_position = generate_rd_obj_position()
                    current_obj = Entity(id=object_iter['id'], name=object_iter['name'], p_pos=random_position, rotate=0)

                    # fixme, time-consuming
                    t0 = time.time()

                    # while not self.is_available_position(random_position,
                    #                                     [object_iter['size'][0] / 2, object_iter['size'][1] / 2]) or flag:
                    #     flag = False
                    #     for agent_individual in agent_with_find_intent:
                    #         if _attention_check(agent_individual, current_obj):
                    #             flag = True
                    #             continue
                    #     if flag:
                    #         rdn1 = random.random()
                    #         rdn2 = random.random()
                    #         sign1 = 1 if rdn1 >= 0.5 else -1
                    #         sign2 = 1 if rdn2 >= 0.5 else -1
                    #         random_position = [ rdn1* 1400 - 700 - sign1 * 60,  rdn2* 1400 - 700 - sign2 * 50]
                    #         # random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                    #         current_obj = Entity(id=object_iter['id'], name=object_iter['name'], p_pos=random_position, rotate=0)

                    while not self.is_available_position(random_position, [object_iter['size'][0] / 2, object_iter['size'][1] / 2]) or flag:
                        random_position = sample_out_of_attentions_position(agent_with_find_intent)
                        flag = False

                    current_obj = Entity(id=object_iter['id'], name=object_iter['name'], p_pos=random_position, rotate=0)

                    print(f'{current_obj.id} sample position elapsed time: {time.time() - t0}')
                    object_iter['pos'] = np.asarray(random_position)
                else:
                    random_position = generate_rd_obj_position()
                    while not self.is_available_position(random_position,
                                                         [object_iter['size'][0] / 2, object_iter['size'][1] / 2]):
                        # random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                        random_position = generate_rd_obj_position()
                            
                    object_iter['pos'] = np.asarray(random_position)
            else:
                # 检查初始化的位置是否正确，否则重新初始化
                while not self.is_available_position(object_iter['pos'],
                                                     [object_iter['size'][0] / 2, object_iter['size'][1] / 2]):
                    # object_iter['pos'] = np.asarray([random.random() * 1400 - 700, random.random() * 1400 - 700])
                    random_position = generate_rd_obj_position()
                    object_iter['pos'] = np.asarray(random_position)
                    
            # 随机选择rotate
            if 'rotate' not in object_iter:
                # 对于桌子，我们不妨让它朝上
                if object_iter['name'] == "table":
                    object_iter['rotate'] = 0.5
                else:
                    # object_iter['rotate'] = random.random()
                    object_iter['rotate'] = 0.5
            # 记录容器所支撑的物体的位置
            if 'supporting_ids' in object_iter:
                supporting = object_iter['supporting_ids'] 
                
                for i in range(len(supporting)):
                    target = self.get_object(supporting[i])

                    # 30 for title height
                    supporting_object_y = object_iter['pos'][1] + object_iter['size'][1] // 2 + target['size'][1] // 2
                    if supporting_object_y > 700 - target['size'][1]//2 - 80:
                        object_iter['pos'][1] = object_iter['pos'][1] - (supporting_object_y - (700 - target['size'][1]//2 - 80))

                    interacting_dict[supporting[i]] = [np.asarray([object_iter['pos'][0], object_iter['pos'][1] +
                                                                   object_iter['size'][1] // 2 + target['size'][
                                                                       1] // 2]),
                                                       object_iter['rotate']]
            if 'containing' in object_iter:
                containing = object_iter['containing']
                for i in range(len(containing)):
                    target = self.get_object(containing[i])
                    interacting_dict[containing[i]] = [object_iter['pos'], object_iter['rotate']]
                    # assert False
        # 开始更新被支撑或是被容纳的物体的位置
        # 对于被容纳的物体，其位置与容器相同
        # 对于被支撑的物体，其位置位于支撑物上方
        for object_iter in self.objects:
            if interacting_dict.get(object_iter['id']) is not None:
                object_iter['pos'] = interacting_dict[object_iter['id']][0]
                object_iter['rotate'] = interacting_dict[object_iter['id']][1]

    def is_available_position(self, pos, size, add=False):
        distance = math.sqrt(size[0] ** 2 + size[1] ** 2)
        up = pos[1] + distance
        down = pos[1] - distance
        left = pos[0] - distance
        right = pos[0] + distance
        if add:
            self.used_position.append([up, down, left, right])
            return True
        # 先检查是否越界
        if up > 700 or down < -700:
            return False
        if left < -700 or right > 700:
            return False
        if len(self.used_position):
            for used in self.used_position:
                # 先检查上下是否有重叠
                # used: [up, down, left, right]
                if down > used[0] or up < used[1]:
                    pass
                else:
                    if right < used[2] or left > used[3]:
                        pass
                    else:
                        return False
        self.used_position.append([up, down, left, right])
        return True
    
    # 检查object里是否有timer，以确保只生成一个timer
    def have_timer_check(self):
        for iter in self.objects:
            if iter['name'] == 'ipad':
                return True
        return False

    def get_object(self, id):
        for object in self.objects:
            if id == object['id']:
                return object

    def generate_in_or_out_belief_obj(self):
        object_in_scene = copy.deepcopy(self.objects)
        for object_iter in object_in_scene:
            for i in range(len(self.agents)):
                ###indicator for in or not in belief, 0/1, for object_iter in agent X
                in_or_not_belief = random.randint(0, 1)
                if in_or_not_belief and not object_iter.get("not_in_belief", None):
                    obj_id_in_belief = copy.deepcopy(object_iter['id'])
                    if not self.agents[i].get('belief_obj_ids', None):
                        self.agents[i]['belief_obj_ids'] = [obj_id_in_belief]
                    else:
                        if obj_id_in_belief not in self.agents[i]['belief_obj_ids']:
                            self.agents[i]['belief_obj_ids'].append(obj_id_in_belief)
                    if object_iter.get('being_contained', None):
                        obj_container_id = object_iter['being_contained'][0]
                        if obj_container_id not in self.agents[i]['belief_obj_ids']:
                            print("add container id in line 1174")
                            self.agents[i]['belief_obj_ids'].append(obj_container_id)
                else:
                    print(f'{object_iter["name"]}_{object_iter["id"]}, rdn in or out belief indicator: {in_or_not_belief} for agent_{i}, not in belief constraint {object_iter.get("not_in_belief",None)}')
                    continue
    
        for i in range(len(self.agents)):
            if self.agents[i].get("belief_obj_ids", None):
                id_obj_list = self.agents[i]["belief_obj_ids"]
                for id_obj in id_obj_list:
                    obj = self.get_object(id_obj)
                    if obj and obj.get("being_contained", None):
                        obj_container_id = obj["being_contained"][0]
                        if obj_container_id not in self.agents[i]['belief_obj_ids']:
                            print("add container id in line 1188")
                            self.agents[i]['belief_obj_ids'].append(obj_container_id)

    def generate_in_or_out_belief_agent(self):
        for i in range(len(self.agents)):
            in_or_not_belief = random.randint(0, 1)
            if in_or_not_belief:
                if not self.agents[i].get('belief_agent_ids', None):
                    self.agents[i]['belief_agent_ids']= [self.agents[(i+1)%2]['id']]
            continue


def is_in_any_attention(agents, x, y):
    entity = Entity(p_pos=(x, y))
    return any(_attention_check(agent, entity) == 1 for agent in agents)


def sample_out_of_attentions_position(agents, grid_size=10):
    x_coords = np.arange(-600, 600, grid_size)
    y_coords = np.arange(-600, 600, grid_size)
    available_positions = []

    for x in x_coords:
        for y in y_coords:
            if not is_in_any_attention(agents, x + grid_size / 2, y + grid_size / 2):
                available_positions.append((x + grid_size / 2, y + grid_size / 2))

    # theoretically impossible
    if not available_positions:
        raise ValueError("No available positions found outside of agents' attention areas.")

    return available_positions[np.random.randint(len(available_positions))]

def generate_rd_obj_position():
    rdn1 = random.random()
    rdn2 = random.random()
    sign1 = 1 if rdn1 >= 0.5 else -1
    sign2 = 1 if rdn2 >= 0.5 else -1
    # 所有object的position都往里移动100单位量
    random_position = [ rdn1* 1400 - 700 - sign1 * 150,  rdn2* 1400 - 700 - sign2 * 150]
    return random_position

if __name__ == '__main__':
    # 构造测试用例
    agent1 = Agent(attention=0, position=(0, 0))
    agent2 = Agent(attention=-1, position=(0, 0))
    agents = [agent1, agent2]
    print(sample_out_of_attentions_position(agents))
    p1 = (50.0, 0.)
    assert is_in_any_attention(agents, *p1)
    p2 = (-50.0, 0.)
    assert is_in_any_attention(agents, *p2)
    p3 = (0., 50.0)
    assert not is_in_any_attention(agents, *p3)
    p4 = (0., -50.0)
    assert not is_in_any_attention(agents, *p4)
