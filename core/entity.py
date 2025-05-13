from copy import deepcopy
import numpy as np
from core.const import *
# from entity_utils import object_attr_obs_dcopy


class Entity():
    def __init__(self, id=None, name='', p_pos=None, rotate=0):
        self.id = id
        self.name = name
        # [width, height]，分别表示x轴宽度和y轴宽度（当rotate = 0.5的时候）
        self.size = None
        # 范围为+-700, 以图像中心为原点
        self.position = p_pos
        # -1 - 1,其中0表示与x轴平行，0.5表示与y轴平行
        self.rotate = rotate

        # record the time that being observed
        self.be_observed_time = None
        # record the observation in one time step
        self.be_observation = None

    def contains(self, point):
        """Check if the point is within the entity's bounds."""
        lower_bound = np.asarray(self.position) - np.asarray(self.size) / 2
        upper_bound = np.asarray(self.position) + np.asarray(self.size) / 2
        return np.all(lower_bound <= point) and np.all(point <= upper_bound)

    def area(self):
        """Calculate the area of the entity."""
        return np.prod(self.size)


class Object(Entity):
    def __init__(self):
        super(Object, self).__init__()
        # container
        self.is_container=False
        self.open = False

        self.locked = False
        self.hidden = False

        self.needs_key = False
        self.containing=[]
        self.being_held_id=[]
        self.being_held_entity=[]

        # id list
        self.being_contained=[]

        # table
        self.is_supporter = False
        self.supporting_ids = []

        # game
        self.is_game=False
        self.is_multiplayer_game=False
        # saliency
        self.is_salient=False
        # key
        self.is_key = False
        self.being_played = False
        self.being_multi_played = False
        self.player_num = 0
        # 可以达到的位置与agent的对应关系
        self.id2position = {}
        # todo, 只有插入没有删除，0321
        self.edge_occupied = []
        # broken
        self.is_broken = False

    def reset_position(self):
        self.position = None

    def update_being_held_entity(self, W):

        self.being_held_entity = []
        if len(self.being_held_id) > 0:
            for i in self.being_held_id:
                self.being_held_entity.append(W.retrieve_by_id(i))

    def _copy(self):
        obj_new = Object()
        self._copy_to(obj_new)
        return obj_new

    def _copy_to(self, obj_new):
        obj_new.id = deepcopy(self.id)
        obj_new.name = deepcopy(self.name)
        obj_new.position = deepcopy(self.position)
        obj_new.rotate = deepcopy(self.rotate)
        obj_new.open = deepcopy(self.open)
        obj_new.locked = deepcopy(self.locked)
        obj_new.needs_key = deepcopy(self.needs_key)
        obj_new.hidden = deepcopy(self.hidden)
        obj_new.being_held_id = deepcopy(self.being_held_id)
        obj_new.being_contained = deepcopy(self.being_contained)
        # obj_new.being_held_entity = deepcopy(self.being_held_entity)
        obj_new.being_played = deepcopy(self.being_played)
        obj_new.being_multi_played = deepcopy(self.being_multi_played)
        obj_new.is_game = deepcopy(self.is_game)
        obj_new.is_multiplayer_game = deepcopy(self.is_multiplayer_game)
        obj_new.is_container = deepcopy(self.is_container)
        obj_new.is_supporter = deepcopy(self.is_supporter)
        obj_new.size = deepcopy(self.size)
        obj_new.is_broken = deepcopy(self.is_broken)


    # decide what can be observed by others
    def get_observation(self, W):
        # if self.be_observed_time != W.time:
        #     # del self.be_observation
        #     # _object = deepcopy(self)
        #     _object = self._copy()
        #     # object_attr_obs_dcopy(self, _object)
        #     _object.containing = []
        #     self.be_observation = _object
        #     self.be_observed_time = W.time
        _object = self._copy()
        # object_attr_obs_dcopy(self, _object)
        _object.containing = []
        self.be_observation = _object
        self.be_observed_time = W.time
        return self.be_observation

    # judge this object can be observed
    # case1: this object is held by another object && another object is locked
    def can_be_observed(self, W):
        if self.being_held_id:
            for id in self.being_held_id:
                entity = W.retrieve_by_id(id)
                if isinstance(entity, Object):
                    if not entity.open:
                        return False
        if self.being_contained:
            for id in self.being_contained:
                entity = W.retrieve_by_id(id)
                if isinstance(entity, Object):
                    if not entity.open:
                        return False
        return True

    # this object is hidden in a container
    def is_hidden(self, W):
        return not self.can_be_observed(W)

    # 对于一些想要agent移动到特定位置的物体，在available_position内提供它所能够移动到的位置
    def multiplayer_game_available_position(self, agent_size, agent_id, W):
        # 假设可以被多人游玩的物体一定是chess，且一定只支持左右两个方向游玩
        if self.is_multiplayer_game:
            agent = W.retrieve_by_id(agent_id)
            # 先检查领取对应位置的人有没有处于该处于的位置上
            to_delete = []
            occupied_position = []
            keys = self.id2position.keys()
            for id in keys:
                if not Is_Near(self, id, W):
                    to_delete.append(id)
                else:
                    occupied_position.append(self.id2position[id])
            for id in to_delete:
                self.player_num -= 1
                self.id2position.pop(id)
            # 再检查目标有没有已经获得位置：
            if self.id2position.get(agent_id) is not None:
                return self.id2position[agent_id]
            # 就近原则
            # 这里架设了agent_size相同
            if self.player_num == 0:
                # 判断左右
                if agent.position[0] < self.position[0]:
                    return np.asarray((self.position[0] - self.size[0]/2 - agent_size, self.position[1]))
                else:
                    return np.asarray((self.position[0] + self.size[0] / 2 + agent_size, self.position[1]))
            elif self.player_num == 1:
                if (self.position[0] - self.size[0]/2 - agent_size) == occupied_position[0][0]:
                    return np.asarray((self.position[0] + self.size[0]/2 + agent_size, self.position[1]))
                else:
                    return np.asarray((self.position[0] - self.size[0]/2 - agent_size, self.position[1]))
            else:
                return None
        return None

    def encoding(self):
        """
        [
        [id] - id (0)
        [x, y] - position, (1-2)
        [x_p, y_p] - relative position (3-4)
        [0,0,1,0,0,0,0,0,0,0] - category: banana, cup, key, timer, books, dumbbell, chess, table, cabinet, box, (5, 14)
        {0,1} - supporter or not (15)
        {0,1} - container or not (16)
        {0,1} - being contained (17)
        {0,1} - containing (18)
        {0,1} - being held (19)
        {0,1} - broken or not (20)
        {0,1} - open or closed (21)
        {0,1} - locked or not (22)
        ]
        :return: a vector of length 23
        """
        obj_encoding=[]
        obj_encoding.append(self.id)
        obj_encoding.extend(self.position)
        obj_encoding.extend([round(self.position[0]/WORLD_WIDTH, 3), round(self.position[1]/WORLD_HEIGHT, 3)])

        # categories=['banana', 'cup', 'key', 'timer', 'books', 'dumbbell', 'chess', 'table', 'cabinet', 'box']
        categories = ['banana', 'cup', 'key', 'timer', 'books', 'dumbbell', 'chess', 'table', 'shelf', 'box']
        category_to_index = {category: idx for idx, category in enumerate(categories)}
        one_hot=[0]*len(categories)
        # print(self.name)
        one_hot[category_to_index[self.name]]=1
        obj_encoding.extend(one_hot)

        obj_encoding.append(1 if self.name in ['table', 'cabinet', 'box'] else 0)
        obj_encoding.append(1 if self.name in ['cabinet', 'box'] else 0)
        obj_encoding.append(1 if len(self.being_contained)>0 else 0)
        obj_encoding.append(1 if len(self.containing)>0 else 0)
        obj_encoding.append(1 if len(self.being_held_id)>0 else 0)
        obj_encoding.append(1 if self.is_broken else 0)
        obj_encoding.append(1 if self.open else 0)
        obj_encoding.append(1 if self.locked else 0)

        return obj_encoding



class Landmark(Entity):
    def __init__(self):
        super(Landmark, self).__init__()


    def reset_position(self):
        self.position=None

    def get_observation(self, W):
        return self
    def encoding(self):
        """
        [id] - id (0)
        [x, y] - position (1,2)
        [x_p, y_p] - relative position (3,4)
        [w, h] - size (5,6)
        [r] - rotate (7)

        :return:
        """
        landmark_encoding=[]
        landmark_encoding.append(self.id)
        landmark_encoding.extend(self.position)
        landmark_encoding.extend([round(self.position[0]/WORLD_WIDTH, 3), round(self.position[1]/WORLD_HEIGHT, 3)])
        landmark_encoding.extend(self.size if self.size is not None else [0,0])
        landmark_encoding.append(self.rotate)

        return landmark_encoding

from core.entity_utils import Is_Near