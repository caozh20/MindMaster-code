# 可选的意图池，对于每一个意图，需要有配套的基本物体
# 字典表示或节点，列表表示与节点
# 字典或列表的前两位为保留位，用于标记各种信息
# 目前只针对物体的多样化生成，不增加agent数量
# 场景节点负责agent和必要的objects的部分属性的初始化，与或图负责其余辅助物体的初始化

import random
import copy
import numpy as np
import math
# from scenarios.generating.play_with_2_3 import PLAY_WITH_2_3
# from scenarios.generating.put_into_3_4_baby import PUT_INTO_3_4_BABY
# from scenarios.generating.request_help_2_open_3 import REQUEST_HELP_2_OPEN_3
from scenarios.generating.container import CONTAINER
from scenarios.generating.classroom import CLASSROOM
from scenarios.generating.baby import BABY
# from scenarios.generating.cuptotable import CUPTOTABLE
from scenarios.generating.chimpanzee import CHIMPANZEE
# seed = int(random.random() * 10000)
# random.seed(3095)
# print(seed)

OBJECTS = {
    "phone": {
        #    ...
    },
    "chess": {
        'name': 'chess',
        'size': [100, 100],
        'is_game': 1,
        'is_multiplayer_game': 1
    },
    "table": {
        'name': 'table',
        'size': [299, 193],
        'is_supporter': True,
    },
    "cup": {
        'name': 'cup',
        'size': [50, 29],
    },
    "banana": {
        'name': 'banana',
        'size': [50, 50]
    },
    "ipad": {
        'name': 'ipad',
        'size': [40, 40]
    },
    "box": {
        "name": "box",
        "size": [120, 120],
        "is_container": True,
        "open": False
    },
    "key": {
        "name": "key",
        "size": [30, 30],
        "is_key": True,
    },
    "toy": {
        "name": "toy",
        "size": [30, 35],
    }
}

intends = {
    "play_with": {
        "required_objects": ['chess'],
        "required_agents": ['alice'],
        #     ...
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


    # 根据intent_pool，随机生成一个intent
    # 目前假设只有两个intent
    def __call__(self, *args, **kwargs):
        pass

    def make_agents(self):
        if self.agents is None:
            return
        for agent in self.agents:
            if 'pos' not in agent:
                random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                # 这里假设agent大小一直不变，都是50
                while not self.is_available_position(random_position, [50, 50]):
                    random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                agent['pos'] = np.asarray(random_position)
            else:
                # 检查初始化的位置是否正确，否则重新初始化
                while not self.is_available_position(agent['pos'], [50, 50]):
                    agent['pos'] = np.asarray([random.random() * 1400 - 700, random.random() * 1400 - 700])
            # desire 生成
            if 'desire' in agent:
                desire = agent['desire']
                # # 补足其它未指定的desire
                # if 'active' not in desire:
                #     desire['active'] = random.randint(-1, 1)
                # if 'social' not in desire:
                #     desire['social'] = random.randint(-1, 1)
                # if 'helpful' not in desire:
                #     desire['helpful'] = random.randint(-1, 1)
                # 补足其它未指定的desire
                if 'active' not in desire:
                    desire['active'] = 1
                if 'social' not in desire:
                    desire['social'] = 1
                if 'helpful' not in desire:
                    desire['helpful'] = 1
            else:
                desire = {}
                # desire['active'] = random.randint(-1, 1)
                # desire['social'] = random.randint(-1, 1)
                # desire['helpful'] = random.randint(-1, 1)
                desire['active'] = 1
                desire['social'] = 1
                desire['helpful'] = 1
                agent['desire'] = desire
            # rotate 和 attention 目前保持一致
            # 暂时随机生成
            if 'attention' not in agent and 'rotate' not in agent:
                agent['attention'] = random.random()
                agent['rotate'] = agent['attention']
            else:
                if 'attention' not in agent:
                    agent['attention'] = agent['rotate']
                else:
                    agent['rotate'] = agent['attention']
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
        # 之后每次以0.2的概率再次增加物体
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
            # 记录已经被交互的物体，防止其被重复交互
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
                if object_iter["name"] in can_be_supported and object_iter['id'] not in having_been_interacted and\
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
                if object_iter["name"] in can_be_contained and object_iter['id'] not in having_been_interacted and\
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
            if object_iter['id'] in be_supported_dict or object_iter['id'] in be_contained_dict or object_iter['id'] in having_been_interacted:
                continue
            elif 'pos' not in object_iter:
                # 再检查物体是否在初始化时就被容纳或是拿取了
                if 'being_held_id' in object_iter:
                    for agent in self.agents:
                        if agent['id'] == object_iter['being_held_id'][0]:
                            object_iter['pos'] = agent['pos']
                else:
                    random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                    while not self.is_available_position(random_position, [object_iter['size'][0]/2, object_iter['size'][1]/2]):
                        random_position = [random.random() * 1400 - 700, random.random() * 1400 - 700]
                    object_iter['pos'] = np.asarray(random_position)
            else:
                # 检查初始化的位置是否正确，否则重新初始化
                while not self.is_available_position(object_iter['pos'], [object_iter['size'][0]/2, object_iter['size'][1]/2]):
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
                                                                object_iter['size'][1]//2 + target['size'][1]//2]),
                                                       object_iter['rotate']]
            if 'containing' in object_iter:
                containing = object_iter['containing']
                for i in range(len(containing)):
                    target = self.get_object(containing[i])
                    interacting_dict[containing[i]] = [object_iter['pos'], object_iter['rotate']]
        # 开始更新被支撑或是被容纳的物体的位置
        # 对于被容纳的物体，其位置与容器相同
        # 对于被支撑的物体，其位置位于支撑物上方
        for object_iter in self.objects:
            if interacting_dict.get(object_iter['id']) is not None:
                object_iter['pos'] = interacting_dict[object_iter['id']][0]
                object_iter['rotate'] = interacting_dict[object_iter['id']][1]


    # 这里的size要求输入总size的一半
    def is_available_position(self, pos, size, add=False):
        distance = math.sqrt(size[0]**2 + size[1]**2)
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

objects_pool = ["chess", "table", "cup", "banana", "ipad", "box", "key", "toy"]

can_be_supported = ["cup", "ipad", "banana"]

can_be_contained = ["cup", "ipad", "banana"]




# 可以根据自己的需要往池子里添加自己想要的intent
INTENT_POOL = [BABY, CLASSROOM, CHIMPANZEE, CONTAINER]

# Scenario_Generating()

# todo: 根据intent类别确定终止条件
# finish