import pygame
from pygame.locals import *
import copy
from collections import defaultdict
from core.Astar_Solver import Astar_Solver
from utils.base import angle, angle_clip, segment, compress_image, compress_and_encode
from utils.base import log, dis, euclidean_dist, agent_left_no_offset, agent_right_no_offset
# from utils import rendering
from utils.mylibrary import *
from core.const import *
from core.action import *
from core.agent import Agent
from core.entity import *
from core.agent_utils import agent_attr_obs_dcopy
from core.belief import Belief
import time
import numpy as np
from gym import spaces
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from globals import mutex
# from core.RRT_Solver import RRT_Solver
import os


plt.switch_backend('agg')

# very light blue background
# SCREEN_COLOR = (252, 253, 255)
# black background
SCREEN_COLOR = (45, 46, 54)


def set_screen(mode, show=False):
    if mode is not None and mode == 'm2m' and show:
        screen = pygame.display.set_mode((1400, 1400))
    else:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        screen = pygame.display.set_mode((1400, 1400), flags=pygame.HIDDEN)
    screen.fill(SCREEN_COLOR)
    # pygame.display.set_caption("Communication Simulator")
    return screen


def cvt_pos_x(x):
    return x + 700


def cvt_pos_y(y):
    # return abs(y) + 700 if y < 0 else 700 - y
    return 700 - y


def cvt_pos(pos):
    # old pos: 0, 0 在中心，x 轴向右，y 轴向上
    # new pos: 0,0 在左上角，x 轴向右，y 轴向下
    x, y = pos
    return np.asarray([cvt_pos_x(x), cvt_pos_y(y)])


def cvt_pos_inplace(pos):
    pos[0] = cvt_pos_x(pos[0])
    pos[1] = cvt_pos_y(pos[1])


# change from the
def inverse_pos(pos):
    x, y = pos
    return tuple([x - 700, 700 - y])


def inverse_rotation(rotation):
    rot = (rotation + 90) / 180
    if rot > 1:
        rot = rot - 2
    if rot < -1:
        rot = 2 + rot
    return rot


def basic_agent_copy(agents):
    agents_cpy = []
    for agent in agents:
        agent_cpy = Agent()
        agent_attr_obs_dcopy(agent, agent_cpy)
        agents_cpy.append(agent_cpy)
    return agents_cpy


class RenderingFlags():
    def __init__(self, L) -> None:
        self.entity_action_finished_flags = []
        self.nodding_flags = []
        self.shaking_flags = []
        self.waving_flags = []
        self.pointing_flags = []
        self.played_flags = []
        self.hitting_flags = []
        self.performing_flags = []
        
        self.eating_flags = []
        
        for _ in range(L):
            self.entity_action_finished_flags.append(False)
            self.nodding_flags.append(False)
            self.shaking_flags.append(False)
            self.waving_flags.append(False)
            self.pointing_flags.append(False)
            self.played_flags.append(False)
            self.hitting_flags.append(False)
            self.performing_flags.append(False)
            self.eating_flags.append(False)

    def set_eating_flag(self,i,flag=True):
        self.eating_flags[i] = flag
    
    def set_finished_flag(self, i, flag=True):
        self.entity_action_finished_flags[i] = flag

    def set_nodding_flag(self, i, flag=True):
        self.nodding_flags[i] = flag

    def set_shaking_flag(self, i, flag=True):
        self.shaking_flags[i] = flag

    def set_waving_flag(self, i, flag=True):
        self.waving_flags[i] = flag

    def set_pointing_flag(self, i, flag=True):
        self.pointing_flags[i] = flag

    def set_performing_flag(self, i, flag=True):
        self.performing_flags[i] = flag

    def set_played_flag(self, i, flag=True):
        self.played_flags[i] = flag

    def set_hitting_flag(self, i, flag=True):
        self.hitting_flags[i] = flag

    def check_finished_flag(self, i):
        return self.entity_action_finished_flags[i]

    def check_all_finished(self):
        return False if False in self.entity_action_finished_flags else True

    def _sleep_more(self):
        for i, flag in enumerate(self.entity_action_finished_flags):
            if not flag and (self.nodding_flags[i] or self.waving_flags[i] or self.played_flags[i] or self.hitting_flags[i] or self.shaking_flags[i]):
                return True
        return False


class World():
    def __init__(self, mode=None, scenario_name=None, show=True, know_other_values=False):

        self.scenario_name = scenario_name
        self.know_other_values = know_other_values
        self.agents = []
        self.objects = []
        self.landmarks = []

        self.old_agents = None
        self.old_entities = None

        # for rendering belief
        # key: agent_id, value: agent old belief entities
        self.agent_old_entities = {}

        self.dim_p = 2
        # self.dt = 0.1

        self.action_space = spaces.Box(
            low=-1.0, high=+1.0, shape=(2,), dtype=np.float32)
        self.observation_space = spaces.Box(
            low=-np.inf, high=+np.inf, shape=(12,), dtype=np.float32)

        self.screen = set_screen(mode, show)

        # print action
        self.action_agent = []
        self.action_render_geoms = []

        # record the time
        self.time = 0

        # agent belief perspective
        # dict of dict
        # first dict, key: agent_id (whose belief), value: dict
        # second dict, key: entity_id (w.r.t which entity), value: index in rendered_agents
        self.rendered_entity_group_index = defaultdict(dict)
        # from world perspective
        self.world_rendered_entity_group_index = {}

        self.render_init_flag_dict = {}
        self.rendered_agents_dict = {}
        self.rendered_landmarks_dict = {}
        # for rendering belief:
        # key: agent_id, value: pygame.sprite.Group()
        self.rendered_objects_dict = {}
        self.render_init_flag_set = set()

        # ui
        # self.name_color = (38, 82, 218)
        self.name_color = (255, 255, 255)
        self.word_color = (255, 253, 1)
        self.me_color = (255, 255, 255)
        self.me_bounding_box_color = (255, 182, 0)
        pygame.font.init()
        self.my_name_font = pygame.font.SysFont('Times New Roman', 35)

        # constant
        self.rotate_atomic = 0.03
        self.move_atomic = 20
        
        self.flag_eating = {}
        self.eating_sprite = None
        self.eating_sprite_render = None
        self.eating_process = 0

        # 添加id到完整名称字符串的映射表
        self.id_to_name_str = {}

    def delete_obj(self, obj):
        # 这里可能会有bug，只是从objects里面删除了物体，可能还有复杂的依赖关系
        for tmp in self.objects:
            if tmp.id == obj.id:
                self.objects.remove(tmp)
                break

    def _get_obj_state(self, obj):
        # pos_x, pos_y, is_held, is_played, is_in, in, is_on, on;
        obj_state = []
        obj_state.extend([obj.position[0], obj.position[1],
                          1 if len(obj.being_held_id) >= 1 else 0, 1 if obj.being_multi_played else 0,
                          1 if len(obj.being_contained) >= 1 else 0, 1 if len(obj.containing) >= 1 else 0,
                          0, 1 if len(obj.supporting_ids) >= 1 else 0])
        return obj_state

    def get_current_state(self):
        current_state = []
        if self.scenario_name is not None:
            if 'classroom' in self.scenario_name:
                # agents
                for i in range(3):
                    agent = self.retrieve_by_id(i+1)
                    current_state.extend([agent.position[0], agent.position[1], agent.attention,
                                          1 if len(agent.holding_ids) >= 1 else 0,
                                          1 if not agent.waving else 0,
                                          1 if not agent.pointing else 0])
                # objects
                # clock
                clock = self.retrieve_by_id(4)
                current_state.extend(self._get_obj_state(clock))
        return current_state

    def render_init(self):
        # from world
        self.rendered_agents = self.create_agent_group(self.screen)
        self.rendered_landmarks = self.create_landmark_group()
        self.rendered_objects = self.create_object_group()
        self.rendered_actions = None
        pygame.font.init()
        self.my_name_font = pygame.font.SysFont('Times New Roman', 40, bold=True)

    def render_agent_belief(self, agent):
        # only execute once
        if agent.id in self.render_init_flag_set:
            return
        self.rendered_agents_dict[agent.id] = self.create_agent_group(self.screen, agent)
        self.rendered_landmarks_dict[agent.id] = self.create_landmark_group(agent)
        self.rendered_objects_dict[agent.id] = self.create_object_group(agent)
        self.rendered_actions = None
        self.render_init_flag_set.add(agent.id)

    def create_agent_group(self, screen, user_agent=None):
        spirits = pygame.sprite.Group()
        agents = self.agents if user_agent is None else user_agent.belief.agents
        for i, agent in enumerate(agents):
            agent_spirit = MySprite()
            if user_agent and user_agent.id == agent.id:
                # fix user_agent the same asset the yellow one
                # a, s, h = user_agent.desire.symbolize()
                # emoji
                agent_spirit.load("assets/agent_{}.png".format(5), *ENTITY_SIZE_CONFIG['agent'], 4)
                # version 1
                # agent_spirit.load("assets/agent_{}_{}_{}_{}.png".format(5, a, s, h), 221, 221, 4)
                # version 2
                # agent_spirit.load("assets/agent_{}_{}_{}_{}_v2.png".format(5, a, s, h), 210, 210, 4)
            else:
                if self.know_other_values:
                    # a, s, h = agent.desire.symbolize()
                    # ground truth desire
                    # a, s, h = self.retrieve_by_id(agent.id).desire.symbolize()
                    agent_spirit.load("assets/agent_{}.png".format(agent.id), *ENTITY_SIZE_CONFIG['agent'], 4)
                    # version 1
                    # agent_spirit.load("assets/agent_{}_{}_{}_{}.png".format(agent.id, a, s, h), 221, 221, 4)
                    # version 2
                    # agent_spirit.load("assets/agent_{}_{}_{}_{}_v2.png".format(agent.id, a, s, h), 210, 210, 4)
                else:
                    agent_spirit.load("assets/agent_{}.png".format(agent.id), *ENTITY_SIZE_CONFIG['agent'], 4)

            # agent_spirit.position = cvt_pos(agent.position)
            agent_spirit.rect.centerx, agent_spirit.rect.centery = cvt_pos(agent.position)
            # agent_spirit.direction = 0
            # agent_spirit.attention = 0
            agent_spirit.screen = screen
            agent_spirit.rotate(-90 + agent.rotate * 180)
            agent_spirit.id = agent.id
            agent_spirit.name = agent.name
            spirits.add(agent_spirit)
            if user_agent is None:
                self.world_rendered_entity_group_index[agent.id] = i
            else:
                self.rendered_entity_group_index[user_agent.id][agent.id] = i
        return spirits

    def create_belief_agent(self, screen, user_agent, agent_id, agent_name):
        agent = self.retrieve_by_id(agent_id)
        agent_spirit = MySprite()
        if agent_id != user_agent.id:
            agent_spirit.first_appear = True
        agent_spirit.load("assets/agent_{}.png".format(agent_id), *ENTITY_SIZE_CONFIG['agent'], 4)
        # agent_spirit.position = cvt_pos(agent.position)
        agent_spirit.rect.centerx, agent_spirit.rect.centery = cvt_pos(agent.position)
        # agent_spirit.direction = 0
        # agent_spirit.attention = 0
        agent_spirit.screen = screen
        agent_spirit.rotate(-90 + agent.rotate * 180)
        agent_spirit.id = agent_id
        agent_spirit.name = agent_name
        self.rendered_agents_dict[user_agent.id].add(agent_spirit)
        self.rendered_entity_group_index[user_agent.id][agent.id] = len(self.rendered_agents_dict[user_agent.id].sprites()) - 1

    def delete_belief_agent(self, user_agent, agent_id):
        for rendered_agent in self.rendered_agents_dict[user_agent.id]:
            if rendered_agent.id == agent_id:
                rendered_agent.remove(self.rendered_agents_dict[user_agent.id])
                old_index = self.rendered_entity_group_index[user_agent.id].pop(agent_id, None)
                for entity_id, group_index in self.rendered_entity_group_index[user_agent.id].items():
                    if isinstance(self.retrieve_by_id(entity_id), Agent) and group_index > old_index:
                        self.rendered_entity_group_index[user_agent.id][entity_id] -= 1

    def delete_belief_object(self, user_agent, obj_id):
        for rendered_obj in self.rendered_objects_dict[user_agent.id]:
            if rendered_obj.id == obj_id:
                rendered_obj.remove(self.rendered_objects_dict[user_agent.id])
                old_index = self.rendered_entity_group_index[user_agent.id].pop(obj_id, None)
                for entity_id, group_index in self.rendered_entity_group_index[user_agent.id].items():
                    if isinstance(self.retrieve_by_id(entity_id), Object) and group_index > old_index:
                        self.rendered_entity_group_index[user_agent.id][entity_id] -= 1

    def create_landmark_group(self, agent=None):
        landmark_group = pygame.sprite.Group()
        landmarks = self.landmarks if agent is None else agent.belief.landmarks
        for i, landmark in enumerate(landmarks):
            ldm = MySprite()
            ldm.load("assets/wall.png", *ENTITY_SIZE_CONFIG['wall'], 1)
            ldm.rect.centerx, ldm.rect.centery = cvt_pos(landmark.position)
            ldm.rotate(-90+landmark.rotate*180)
            # obj.position = cvt_pos(object.position) + offset
            ldm.direction = 0
            ldm.attention = 0
            landmark_group.add(ldm)
            # obj.image = pygame.Surface(landmark.size)
            # obj.rect = pygame.Rect(landmark.position, landmark.size)
            # obj.image.fill(landmark.color)
            if agent is None:
                self.world_rendered_entity_group_index[landmark.id] = i
            else:
                self.rendered_entity_group_index[agent.id][landmark.id] = i
        return landmark_group

    def create_object_group(self, agent=None):
        object_group = pygame.sprite.Group()
        objects = self.objects if agent is None else agent.belief.objects
        objects.sort(key=lambda o: o.size[0]*o.size[1], reverse=True)
        for i, object in enumerate(objects):
            obj = self._obj_to_sprite(object)
            obj.rect.centerx, obj.rect.centery = cvt_pos(object.position)
            obj.rotate(-90 + object.rotate * 180)
            # obj.position = cvt_pos(object.position) + offset
            obj.direction = 0
            obj.attention = 0
            obj.id = object.id
            obj.name = object.name
            object_group.add(obj)
            if agent is None:
                self.world_rendered_entity_group_index[object.id] = i
            else:
                self.rendered_entity_group_index[agent.id][object.id] = i
        return object_group

    def _obj_to_sprite(self, object):
        obj = MySprite()
        if 'ipad' in object.name or 'clock' in object.name or 'timer' in object.name:
            obj.load("assets/timer.png", *ENTITY_SIZE_CONFIG['timer'], 1)
            # offset = [20, 20]
        elif 'cup' in object.name:
            # obj.load("render/banana_50x50.png", 50, 50, 1)
            obj.load("assets/cup.png", *ENTITY_SIZE_CONFIG['cup'], 1)
            # offset = [25, 25]
        elif 'table' in object.name:
            obj.load("assets/table.png", *ENTITY_SIZE_CONFIG['table'], 1)
        elif object.locked:
            obj.load("assets/box_lock.png", *ENTITY_SIZE_CONFIG['box_unlock'], 1)
        elif 'box' in object.name:
            obj.load("assets/box.png", *ENTITY_SIZE_CONFIG['box'], 1)
        elif 'chess' in object.name:
            obj.load("assets/chess.png", *ENTITY_SIZE_CONFIG['chess'], 1)
        elif 'banana' in object.name:
            obj.load("assets/banana.png", *ENTITY_SIZE_CONFIG['banana'], 1)
        elif 'key' in object.name:
            obj.load('assets/key.png', *ENTITY_SIZE_CONFIG['key'], 1)
        elif 'books' in object.name:
            obj.load('assets/books.png', *ENTITY_SIZE_CONFIG['books'], 1)
        elif 'shelf' in object.name:
            obj.load('assets/shelf.png', *ENTITY_SIZE_CONFIG['shelf'], 1)
        elif 'dumbbell' in object.name:
            obj.load('assets/dumbbell.png', *ENTITY_SIZE_CONFIG['dumbbell'], 1)
        else:
            obj.load("assets/box.png", *ENTITY_SIZE_CONFIG['box'], 1)
        return obj

    def create_belief_object(self, agent, obj_id, obj_name, obj=None):
        obj_entity = self.retrieve_by_id(obj_id)
        
        if not obj_entity:
            obj_entity = obj
        
        obj = self._obj_to_sprite(obj_entity)
        obj.first_appear = True
        obj.rect.centerx, obj.rect.centery = cvt_pos(obj_entity.position)
        obj.rotate(-90 + obj_entity.rotate * 180)
        # obj.position = cvt_pos(object.position) + offset
        obj.direction = 0
        obj.attention = 0
        obj.id = obj_id
        obj.name = obj_name
        self.rendered_objects_dict[agent.id].add(obj)
        self.rendered_entity_group_index[agent.id][obj_id] = len(self.rendered_objects_dict[agent.id].sprites()) - 1

    def get(self, target):
        # if the target is id
        if isinstance(target, int):
            for entity in self.entities:
                if entity.id == target:
                    return entity
        # if the target is name
        if isinstance(target, str):
            for entity in self.entities:
                if entity.name == target:
                    return entity
        return None

    def create_action_group(self):
        # empty, render pointing and waving
        actions = pygame.sprite.Group()
        return actions

    def preprocessing(self, client_agent):
        # client_agent first
        log.info(f'client_agent: {client_agent.id}')
        log.info(f'before: {[agent.id for agent in self.agents]}')
        self.agents.remove(client_agent)
        self.agents.insert(0, client_agent)
        log.info(f'after: {[agent.id for agent in self.agents]}')

        # rename agent
        index = 1
        for agent in self.agents:
            if agent.id == client_agent.id:
                agent.name = 'me'
            else:
                index += 1
                agent.name = 'agent {}'.format(index)

    @property
    def entities(self):
        # first render big object, then small object to avoid rendering overlap
        if len(self.objects) > 0:
            self.objects.sort(
                key=lambda obj: 0 if obj is None or obj.size is None else obj.size[0] * obj.size[1], reverse=True)
        return self.agents + self.objects + self.landmarks

    def entities_names_dict(self):
        return {'agent': [f'agent_{a.id}' for a in self.agents],
                'objects': [f'{o.name}_{o.id}' for o in self.objects]}

    def retrieve_by_id(self, id):

        for e in self.entities:
            if e.id == id:
                return e
        print(f'!!!!!!!!!!!!No entity with id {id}, all ids: {[e.id for e in self.entities]}')
        return None

    def get_agent_ids(self):
        return [agent.id for agent in self.agents]

    def get_obj_ids(self):
        return [object.id for object in self.objects]

    def get_landmark_ids(self):
        return [landmark.id for landmark in self.landmarks]

    # update state of the world
    def step(self, actions):
        # todo: here actions are all agents' actions, not concurrent actions for one agent.
        self.time += 1
        for action in actions:
            if action is not None:
                action.execute(self)

    def reward(self):
        return

    def reset(self):
        pass

    def _reset_render(self):
        self.render_geoms = None
        self.render_geoms_xform = None

    def _agent_noding(self, agent, i, num):
        noding_rad = 0.05
        if i < num // 2:
            return agent.rotate + (i + 1) / (num // 2) * noding_rad
        else:
            i -= num // 2
            return agent.rotate + noding_rad - (i + 1) / (num // 2) * noding_rad

    def _agent_hitting(self, agent, i, num):
        # default direction, left & right
        size = agent.size
        x, y = agent.position
        new_loc = []
        if i < num // 6:
            new_loc = x - (i + 1) / (num // 6) * size, y
        elif i < num * 4 // 6:
            new_loc = x - size + (i + 1) / (num * 4 // 6) * 3 * size, y
        else:
            new_loc = x + 2 * size - (i + 1) / num * 2 * size, y
        return new_loc[0] / WORLD_WIDTH, new_loc[1] / WORLD_HEIGHT

    def _held_by_who(self, entity):
        for who in entity.being_held_entity:
            if isinstance(who, Agent):
                return who
        return None

    def draw_obs_render(self, user_agent, frame, last_frame=False):
        rendered_agents = self.rendered_agents if user_agent is None else self.rendered_agents_dict[user_agent.id]
        for agent in rendered_agents:
            # last_frame: show
            # not last_frame && not first_appear: show
            # myself: show
            if last_frame or (not last_frame and not agent.first_appear) or agent.id == user_agent.id:
                image = pygame.image.load('assets/vision_l.png')
                if frame is not None:
                    if agent.nodding and frame % 4 in [1, 3]:
                        image = pygame.image.load('assets/vision_m.png')
                    elif agent.nodding and frame % 4 == 2:
                        image = pygame.image.load('assets/vision_s.png')
                image_alpha = image.convert_alpha()
                if not agent.isin_attention:
                    image_alpha.set_alpha(agent.default_alpha // (DOWN_SCALED_ALPHA+4))
                else:
                    if not last_frame and agent.reappear:
                        image_alpha.set_alpha(agent.default_alpha // (DOWN_SCALED_ALPHA + 4))
                    else:
                        image_alpha.set_alpha(agent.default_alpha)
                image_alpha = pygame.transform.rotate(image_alpha, agent.rotation)
                image_rect = image_alpha.get_rect(center=(agent.rect.centerx, agent.rect.centery))
                self.screen.blit(image_alpha, image_rect)

    def update_action_render(self, frame, agent=None, last_frame=False, current_agent=None):
        self.rendered_actions = pygame.sprite.Group()
        agents = self.agents if agent is None else agent.belief.agents

        for this_agent in agents:

            if agent is None:
                rendered_agent = self.rendered_agents.sprites()[self.world_rendered_entity_group_index[this_agent.id]]
            else:
                rendered_agent = self.rendered_agents_dict[agent.id].sprites()[self.rendered_entity_group_index[agent.id][this_agent.id]]

            if not (last_frame or (not last_frame and not rendered_agent.first_appear) or agent.id == this_agent.id):
                continue

            if this_agent.pointing:
                what_id = this_agent.pointing
                what = self.retrieve_by_id(int(what_id))

                is_left = self._left_or_right(this_agent)

                action_pointing = MySprite()
                action_pointing.screen = self.screen
                action_pointing.first_frame = frame % 5
                action_pointing.last_frame = frame % 5

                if is_left:
                    if agent is None:
                        action_pointing.load("assets/agent_{}_point_left.png".format(this_agent.id), 34, 126, 5)
                    else:
                        action_pointing.load("assets/agent_{}_point_left.png".format(5 if this_agent.id == agent.id else this_agent.id), 34, 126, 5)
                    action_pointing.rect.centerx, action_pointing.rect.centery = render_agent_left_pos(rendered_agent)
                else:
                    if agent is None:
                        action_pointing.load("assets/agent_{}_point_right.png".format(this_agent.id), 34, 126, 5)
                    else:
                        action_pointing.load("assets/agent_{}_point_right.png".format(5 if this_agent.id == agent.id else this_agent.id), 34, 126, 5)
                    action_pointing.rect.centerx, action_pointing.rect.centery = render_agent_right_pos(rendered_agent)

                action_pointing.update()
                to_target_rotation = angle([1, 0], np.asarray(what.position) - np.asarray(inverse_pos([action_pointing.rect.centerx, action_pointing.rect.centery])))
                action_pointing.rotate(-90 + to_target_rotation)
                if not rendered_agent.isin_attention:
                    action_pointing.downscale_alpha()
                else:
                    action_pointing.reset_alpha()
                self.rendered_actions.add(action_pointing)

            elif this_agent.waving:
                action_waving = self.create_action_waving(agent, frame, rendered_agent, this_agent)
                self.rendered_actions.add(action_waving)

            elif this_agent.performing:
                action_performing = self.create_action_perform(agent, frame, rendered_agent, this_agent)
                self.rendered_actions.add(action_performing)

            elif this_agent.eating:
                # if this_agent.eating.id not in self.flag_eating:
                if self.eating_process == 0:
                    action_eating = self.create_action_eating(agent, frame, rendered_agent, this_agent, False)
                    self.flag_eating[this_agent.eating.id] = True
                    self.rendered_actions.add(action_eating)
                    self.eating_sprite = action_eating
                elif self.eating_process == 1:
                    # eating obj has already be eaten
                    _ = self.create_action_eating(agent, frame, rendered_agent, this_agent, True)
                    # 重置状态，以便下次使用
                    self.eating_process = 0
                    self.eating_sprite = None
                    self.eating_sprite_render = None

    def create_action_eating(self, agent, frame, rendered_agent, this_agent, flag):
        # agent: whose belief (None for world render)
        # this_agent: agent who is eating
        action_eating = MySprite()
        
        if not flag:
            obj = this_agent.eating
            sprite_render = None
            
            # 获取对应的精灵对象（区分普通渲染和信念渲染）
            if agent is None:
                # 普通世界渲染模式
                if obj.id in self.world_rendered_entity_group_index:
                    entity_index = self.world_rendered_entity_group_index[obj.id]
                    sprite_render = self.rendered_objects.sprites()[entity_index]
            else:
                # 信念渲染模式
                if obj.id not in self.rendered_entity_group_index[agent.id]:
                    if isinstance(obj, Object):
                        self.create_belief_object(agent, obj.id, obj.name, obj) 
                
                entity_index = self.rendered_entity_group_index[agent.id][obj.id]
                sprite_render = self.rendered_objects_dict[agent.id].sprites()[entity_index]
            
            # 通用的渲染逻辑
            if sprite_render:
                if 'banana' in obj.name:
                    sprite_render.load('assets/banana.png', *ENTITY_SIZE_CONFIG['banana'], 1)

                # 临时调整旋转角度
                this_agent.rotate -= 0.35
                rawx, rawy = agent_left_upper_with_offset(this_agent, obj)
                this_agent.rotate += 0.35  # 恢复原来的旋转角度
                
                # 更新精灵位置
                sprite_render.rect.centerx = cvt_pos_x(rawx)
                sprite_render.rect.centery = cvt_pos_y(rawy)
                
                # 设置渲染属性
                action_eating.screen = self.screen
                action_eating = sprite_render
                self.eating_sprite_render = sprite_render
                action_eating.update()
                
        elif this_agent.eating and this_agent.eating.id in self.flag_eating:
            obj = this_agent.eating
            # 信念渲染模式下需要删除对象
            if agent is not None:
                self.delete_belief_object(agent, obj.id)
            else:
                # 普通世界渲染模式下也需要删除对象
                if obj.id in self.world_rendered_entity_group_index:
                    entity_index = self.world_rendered_entity_group_index[obj.id]
                    sprite = self.rendered_objects.sprites()[entity_index]
                    sprite.remove(self.rendered_objects)
                    old_index = self.world_rendered_entity_group_index.pop(obj.id, None)
                    # 更新其他对象的索引
                    for entity_id, group_index in self.world_rendered_entity_group_index.items():
                        if isinstance(self.retrieve_by_id(entity_id), Object) and group_index > old_index:
                            self.world_rendered_entity_group_index[entity_id] -= 1
                    # 从世界中删除对象
                    self.delete_obj(obj)
        
            # 无论哪种模式都需要清除eating状态
            this_agent.eating = None

        return action_eating

    def create_action_waving(self, agent, frame, rendered_agent, this_agent):
        action_waving = MySprite()
        if agent is None:
            action_waving.load("assets/agent_{}_waving.png".format(this_agent.id), 196, 90, 14)
        else:
            action_waving.load("assets/agent_{}_waving.png".format(5 if this_agent.id == agent.id else this_agent.id),
                               196, 90, 14)
        action_waving.screen = self.screen
        action_waving.first_frame = frame % 14
        action_waving.last_frame = frame % 14
        action_waving.update()
        action_waving.rect.centerx, action_waving.rect.centery = render_agent_right_pos(rendered_agent)
        action_waving.rotate(rendered_agent.rotation)
        if not rendered_agent.isin_attention:
            action_waving.downscale_alpha()
        else:
            action_waving.reset_alpha()
        return action_waving

    def create_action_perform(self, agent, frame, rendered_agent, this_agent):
        action_performing = MySprite()
        performing = this_agent.performing

        index = frame % 3
        if agent is None:
            action_performing.load(f"assets/agent_{this_agent.id}_{performing}_{index+1}.png", 180, 180, 1)
        else:
            action_performing.load(f"assets/agent_{5 if this_agent.id == agent.id else this_agent.id}_{performing}_{index+1}.png", 180, 180, 1)
        action_performing.screen = self.screen
        action_performing.update()

        action_performing.rotate(rendered_agent.rotation)

        # 中心是不会变的，但其他会变
        action_performing.rect.centerx, action_performing.rect.centery = cvt_pos(this_agent.position)

        if not rendered_agent.isin_attention:
            action_performing.downscale_alpha()
        else:
            action_performing.reset_alpha()
        return action_performing


    def _left_or_right(self, this_agent):
        what_id = this_agent.pointing
        what = self.retrieve_by_id(int(what_id))
        agent_left_pos = agent_left_no_offset(this_agent)
        agent_right_pos = agent_right_no_offset(this_agent)
        is_left = False
        if euclidean_dist(agent_left_pos, what.position) < euclidean_dist(agent_right_pos, what.position):
            is_left = True
        return is_left

    def update_screen(self, frame, agent=None, last_frame=False, current_agent=None):
        # clear and re fill
        self.screen.fill(SCREEN_COLOR)

        # update agent alpha
        self.update_agent_alpha(agent, last_frame)
        entities = self.entities if agent is None else agent.belief.entities

        # draw obs (visual cone)
        self.draw_obs_render(agent, frame, last_frame)
        # update actions
        self.update_action_render(frame, agent, last_frame, current_agent)

        # belief of agent
        if agent is not None:

            if last_frame:
                # draw all
                self.rendered_landmarks_dict[agent.id].draw(self.screen)
                # self.rendered_objects_dict[agent.id].draw(self.screen)
                self._draw_rendered_objects(self.rendered_objects_dict[agent.id], agent)                
                self.rendered_agents_dict[agent.id].draw(self.screen)
            else:
                lmd_group = self.rendered_landmarks_dict[agent.id]
                self._first_appear_filter_draw(agent.id, lmd_group)

                obj_group = self.rendered_objects_dict[agent.id]
                sorted_sprites = sorted(obj_group.sprites(), key=lambda sprite: sprite.rect.width * sprite.rect.height, reverse=True)
                self._first_appear_filter_draw(agent.id, sorted_sprites)

                # only draw not the first appear entity
                agent_group = self.rendered_agents_dict[agent.id]
                self._first_appear_filter_draw(agent.id, agent_group)

            self._show_blf_names(agent, last_frame)
            self._show_grabing_hand(agent, last_frame)
            # pointing/waving hand placed in the foreground
            self.rendered_actions.draw(self.screen)

        else:
            # render the world
            self.rendered_landmarks.draw(self.screen)
            self.rendered_objects.draw(self.screen)
            self.rendered_agents.draw(self.screen)
            self.rendered_actions.draw(self.screen)
            self._show_names()
            self._show_grabing_hand()

        self._render_speaking(agent)
        self._show_shadows(entities, agent)
        pygame.display.flip()
        pygame.display.update()

    def _show_blf_names(self, agent, last_frame=False):

        for agent_sprite in self.rendered_agents_dict[agent.id]:
            agent_name = '{}'.format(agent_sprite.name)
            if agent is not None and agent.id == agent_sprite.id:
                agent_name = 'me'
                # todo, dont show `me` name
                # me_name_bounding_box = self._me_name_bouding_box(agent, agent_sprite)
                # pygame.draw.rect(self.screen, self.me_bounding_box_color, me_name_bounding_box, border_radius=10)
                # text_show = self.my_name_font.render(agent_name, True, self.me_color)
                # # dont show me
                # self.screen.blit(text_show, (me_name_bounding_box.centerx, me_name_bounding_box.centery) - np.array((20, 25)))
            else:
                if last_frame or not agent_sprite.first_appear:
                    # pass
                    text_show = self.my_name_font.render(agent_name, True, self.name_color)
                    if not agent_sprite.isin_attention:
                        text_show.set_alpha(text_show.get_alpha() // DOWN_SCALED_ALPHA)
                    self.screen.blit(text_show, agent_sprite.get_raw_top_left() - np.array((20, 50)))
        for object_sprite in self.rendered_objects_dict[agent.id]:
            if last_frame or not object_sprite.first_appear:
                text_show = self.my_name_font.render(f'{object_sprite.name}_{object_sprite.id}', True, self.name_color)
                if not object_sprite.isin_attention:
                    text_show.set_alpha(text_show.get_alpha() // DOWN_SCALED_ALPHA)
                if 'table' not in object_sprite.name:
                    self.screen.blit(text_show, object_sprite.get_raw_top_left() - np.array((20, 50)))
                else:
                    self.screen.blit(text_show, object_sprite.get_raw_down_mid() - np.array((50, 5)))

    def _show_names(self):
        for agent_sprite in self.rendered_agents:
            agent_name = f'agent_{agent_sprite.id}'
            text_show = self.my_name_font.render(agent_name, True, self.name_color)
            self.screen.blit(text_show, agent_sprite.get_raw_top_left() - np.array((20, 50)))
        for object_sprite in self.rendered_objects:
            obj_name = f'{object_sprite.name}_{object_sprite.id}'
            text_show = self.my_name_font.render(obj_name, True, self.name_color)
            self.screen.blit(text_show, object_sprite.get_raw_top_left() - np.array((20, 50)))

    def _show_shadows(self, entities, agent=None):
        for entity in entities:
            if hasattr(entity, 'being_contained') and len(entity.being_contained) > 0:
                being_contained_obj = self.retrieve_by_id(entity.being_contained[0])
                if not hasattr(being_contained_obj, 'open') or being_contained_obj.open:
                    continue
                if agent:
                    if entity.id not in self.rendered_entity_group_index[agent.id]:
                        continue
                    render_sprite = self.rendered_objects_dict[agent.id].sprites()[self.rendered_entity_group_index[agent.id][entity.id]]
                else:
                    render_sprite = self.rendered_objects.sprites()[self.world_rendered_entity_group_index[entity.id]]
                num_lines = 7
                line_color = self.me_bounding_box_color
                lw = 2
                tl = render_sprite.rect.topleft
                tr = render_sprite.rect.topright
                bl = render_sprite.rect.bottomleft
                br = render_sprite.rect.bottomright
                w, h = render_sprite.rect.width, render_sprite.rect.height
                pygame.draw.line(self.screen, line_color, tl, tr, lw)
                pygame.draw.line(self.screen, line_color, bl, br, lw)
                pygame.draw.line(self.screen, line_color, tl, bl, lw)
                pygame.draw.line(self.screen, line_color, tr, br, lw)
                for i in range(num_lines // 2):
                    pygame.draw.line(self.screen, line_color,
                                     (tr[0] - w / (num_lines / 2) * (i + 1), tr[1]),
                                     (bl[0], bl[1] - h / (num_lines / 2) * (i + 1)), lw)
                pygame.draw.line(self.screen, line_color, tr, bl, lw)
                for i in range(num_lines // 2):
                    pygame.draw.line(self.screen, line_color,
                                     (tr[0], tr[1] + h / (num_lines / 2) * (i + 1)),
                                     (bl[0] + w / (num_lines / 2) * (i + 1), bl[1]), lw)

    def _me_name_bouding_box(self, agent, agent_sprite):
        centerx, centery = agent_sprite.rect.centerx, agent_sprite.rect.centery
        # default 下边
        y_offset = 55
        # agent rotation 朝下，name 上移；
        if len(agent.holding_ids) > 0 and (-315 < agent_sprite.rotation < -225 or 45 < agent_sprite.rotation < 135):
            y_offset = -95
        elif -225 < agent_sprite.rotation < -135 or 135 < agent_sprite.rotation < 225:
            y_offset = -95
        # agent rotation 朝右 && waving（右手），name 上移；
        elif agent.waving and (225 <= agent_sprite.rotation <= 315 or -135 <= agent_sprite.rotation <= -45):
            y_offset = -95
        # agent rotation 朝右 && pointing（右手），name 上移；
        elif agent.pointing and not self._left_or_right(agent) and (225 <= agent_sprite.rotation <= 315 or -135 <= agent_sprite.rotation <= -45):
            y_offset = -95
        me_name_bounding_box = pygame.Rect(centerx - 50, centery + y_offset, 100, 40)
        return me_name_bounding_box

    def _render_agent_speaking(self, agent, agent_sprite):
        if not agent.speaking:
            return
        if len(agent.action_history) == 0:
            return
        last_action = agent.action_history[-1]
        if last_action[0] != 'ActionSpeak':
            return
        if last_action[-1] == '-1':
            return
        text_show = self.my_name_font.render(last_action[2], True, self.word_color)
        if last_action[2] == 'Hello!':
            self.screen.blit(text_show, agent_sprite.get_adj_right(x_offset=80))
        else:
            self.screen.blit(text_show, agent_sprite.get_adj_right(x_offset=140))

    def _render_speaking(self, agent):
        self.rendered_actions = pygame.sprite.Group()
        agents = self.agents if agent is None else agent.belief.agents
        for this_agent in agents:
            if agent is None:
                rendered_agent = self.rendered_agents.sprites()[self.world_rendered_entity_group_index[this_agent.id]]
            else:
                rendered_agent = self.rendered_agents_dict[agent.id].sprites()[
                    self.rendered_entity_group_index[agent.id][this_agent.id]]
            if this_agent.speaking:
                self._render_agent_speaking(this_agent, rendered_agent)

    def _maybe_render_unlock(self, agent_id, sprite, last_frame):
        '''
        对于 unlock 开锁的动作，非最后一帧时，不做渲染，也即只在最后一帧渲染开锁之后的状态
        在最后一帧之前，只渲染关着的状态
        :param sprite:
        :return:
        '''

        old_entity, new_entity = None, None
        if self.agent_old_entities.get(agent_id, None):
            old_entites = self.agent_old_entities[agent_id]
            for i, ent in enumerate(old_entites):
                if ent.id == sprite.id:
                    old_entity = ent
                    break

        agent: Agent = self.get(agent_id)

        if agent:
            for i, ent in enumerate(agent.belief.entities):
                if ent.id == sprite.id:
                    new_entity = ent
                    break
        if old_entity is None or new_entity is None:
            return

        if not (
                getattr(old_entity, 'locked', None) is True and
                getattr(new_entity, 'locked', None) is False
        ):
            return

        if not last_frame:
            sprite.load("assets/box_lock.png", *ENTITY_SIZE_CONFIG['box_lock'], 1)
        else:
            sprite.load("assets/box_unlock.png", *ENTITY_SIZE_CONFIG['box_unlock'], 1)
        sprite.rect.centerx, sprite.rect.centery = cvt_pos(new_entity.position)
        sprite.rotate(-90 + new_entity.rotate * 180)

    def _first_appear_filter_draw(self, agent_id, sprite_group):
        for sprite in sprite_group:
            if not sprite.first_appear:
                self._maybe_render_unlock(agent_id, sprite, last_frame=False)
                self.screen.blit(sprite.image, sprite.rect)


    # decide whether there is an obstacle
    def check_obstacle(self):
        have_changed = []
        obstacle_line = []
        obstacle_entities = []
        for e, entity in enumerate(self.entities):
            if isinstance(entity, Landmark):
                obstacle_entities.append(entity)
                obstacle_line += [[[entity.position[0] - entity.size[0] / 2, entity.position[1] - entity.size[1] / 2],
                                   [entity.position[0] + entity.size[0] / 2, entity.position[1] + entity.size[1] / 2]]]
                obstacle_line += [[[entity.position[0] - entity.size[0] / 2, entity.position[1] - entity.size[1] / 2],
                                   [entity.position[0] + entity.size[0] / 2, entity.position[1] - entity.size[1] / 2]]]

        for e, entity in enumerate(self.entities):
            if self.old_entities[e].position[0] == entity.position[0] and self.old_entities[e].position[1] == entity.position[1]:
                have_changed.append(False)
            else:
                have_changed.append(True)
        have_obstacle = []
        for e, entity in enumerate(self.entities):
            if have_changed[e]:
                for obstacle in obstacle_line:
                    if segment(self.old_entities[e].position, entity.position, obstacle[0], obstacle[1]):
                        have_obstacle.append(True)
                        break
                if len(have_obstacle) < e + 1:
                    have_obstacle.append(False)
            else:
                have_obstacle.append(False)
        return obstacle_entities, have_obstacle

    def check_belief_obstacle(self, agent):
        have_changed = []
        obstacle_line = []
        obstacle_entities = []
        for e, entity in enumerate(agent.belief.entities):
            if isinstance(entity, Landmark):
                obstacle_entities.append(entity)
                obstacle_line += [[[entity.position[0] - entity.size[0] / 2, entity.position[1] - entity.size[1] / 2],
                                   [entity.position[0] + entity.size[0] / 2, entity.position[1] + entity.size[1] / 2]]]
                obstacle_line += [[[entity.position[0] - entity.size[0] / 2, entity.position[1] - entity.size[1] / 2],
                                   [entity.position[0] + entity.size[0] / 2, entity.position[1] - entity.size[1] / 2]]]

        for e, entity in enumerate(agent.belief.entities):
            old_e = None
            for old_entity in self.agent_old_entities[agent.id]:
                if old_entity.id == entity.id:
                    old_e = old_entity
            if old_e is None:
                have_changed.append(False)
                continue
            if old_e.position[0] == entity.position[0] and old_e.position[1] == entity.position[1]:
                have_changed.append(False)
            else:
                have_changed.append(True)
        have_obstacle = []
        for e, entity in enumerate(agent.belief.entities):
            old_e = None
            for old_entity in self.agent_old_entities[agent.id]:
                if old_entity.id == entity.id:
                    old_e = old_entity
            if old_e is None:
                have_obstacle.append(False)
                continue
            if have_changed[e]:
                for obstacle in obstacle_line:
                    # print(obstacle[0], obstacle[1])
                    if segment(old_e.position, entity.position, obstacle[0], obstacle[1]):
                        have_obstacle.append(True)
                        break
                if len(have_obstacle) < e + 1:
                    have_obstacle.append(False)
            else:
                have_obstacle.append(False)
        return obstacle_entities, have_obstacle

    def cac_astar_way(self, have_obstacle, obstacle_entities):
        Solver = Astar_Solver(obstacle_entities)
        way = []
        for e, entity in enumerate(self.entities):
            if have_obstacle[e]:
                possible = Solver.astar(
                    tuple(np.asarray(self.old_entities[e].position).astype(int)), tuple(np.asarray(entity.position).astype(int)))
                if possible:
                    way += [list(possible)]
                else:
                    way.append(None)
            else:
                way.append(None)
        return way

    def cac_belief_astar_way(self, agent, have_obstacle, obstacle_entities):
        Solver = Astar_Solver(obstacle_entities)
        way = []
        for e, entity in enumerate(agent.belief.entities):
            old_e = None
            for old_entity in self.agent_old_entities[agent.id]:
                if old_entity.id == entity.id:
                    old_e = old_entity
            if old_e is None:
                continue
            if have_obstacle[e]:
                possible = Solver.astar(
                    tuple(np.asarray(old_e.position).astype(int)), tuple(np.asarray(entity.position).astype(int)))
                if possible:
                    way += [list(possible)]
                    way[-1].append(tuple(entity.position))
                else:
                    way.append(None)
            else:
                way.append(None)
        return way

    def rotate_and_direct_move(self, frame, rotate_steps, move_steps, entity, e, old_entity, flags: RenderingFlags, rendered_sprite):
        if frame < rotate_steps:
            new_rotate = self.interpolate_rotate(old_entity, entity, frame, rotate_steps)
            rendered_sprite.rotate(new_rotate)
            rendered_sprite.rect.centerx = cvt_pos_x(old_entity.position[0])
            rendered_sprite.rect.centery = cvt_pos_y(old_entity.position[1])

        elif frame < rotate_steps + move_steps:
            rendered_sprite.rect.centerx = cvt_pos_x(old_entity.position[0] +
                                                     (entity.position[0] - old_entity.position[0]) * (frame - rotate_steps + 1) / move_steps)
            rendered_sprite.rect.centery = cvt_pos_y(old_entity.position[1] +
                                                     (entity.position[1] - old_entity.position[1]) * (frame - rotate_steps + 1) / move_steps)

        else:
            rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
            rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
            rendered_sprite.rotate(-90 + entity.rotate * 180)
            flags.set_finished_flag(e)
        return flags

    def render_holding_objs(self, entity, new_rotate, obj_id):
        obj = self.retrieve_by_id(obj_id)
        obj_rendered_index = self.rendered_entity_group_index[obj_id]
        obj_rendered = self.rendered_objects.sprites()[obj_rendered_index]
        obj_rendered.rotate(new_rotate + 90)
        rawx, rawy = agent_left_upper_with_offset(entity, obj)
        obj_rendered.rect.centerx = cvt_pos_x(rawx)
        obj_rendered.rect.centery = cvt_pos_y(rawy)

    def only_rotate(self, frame, rotate_steps, move_steps, entity, e, old_entity, flags: RenderingFlags, rendered_sprite):
        if frame < rotate_steps:
            new_rotate = self.interpolate_rotate(
                old_entity, entity, frame, rotate_steps)
        else:
            flags.set_finished_flag(e)
            new_rotate = -90 + entity.rotate * 180

        rendered_sprite.rotate(new_rotate)
        return flags

    def interpolate_rotate(self, old_entity, entity, frame, rotate_steps):
        '''
        Rotation angle interpolation to avoid turning the larger angle
        '''
        abs_diff = abs(entity.rotate - old_entity.rotate)
        delta_rotate = abs_diff
        # delta_rotate means the real small angle that needs to be rotated
        if abs_diff > 1:
            delta_rotate = 2 - delta_rotate

        if entity.rotate == 0 or old_entity.rotate == 0:
            # increasing
            if (entity.rotate == 0 and old_entity.rotate < 0) or (old_entity.rotate == 0 and entity.rotate > 0):
                new_rotate = -90 + (old_entity.rotate +
                                    delta_rotate * (frame + 1) / rotate_steps) * 180
            # decreasing
            else:
                new_rotate = -90 + (old_entity.rotate -
                                    delta_rotate * (frame + 1) / rotate_steps) * 180
        # same sign
        elif entity.rotate * old_entity.rotate > 0:
            new_rotate = -90 + (old_entity.rotate +
                                (entity.rotate - old_entity.rotate) * (frame + 1) / rotate_steps) * 180
        elif entity.rotate > 0 > old_entity.rotate:
            if abs_diff > 1:
                new_rotate = -90 + (old_entity.rotate + 2 +
                                    (entity.rotate - (old_entity.rotate + 2)) * (frame + 1) / rotate_steps) * 180
            else:
                tmp = old_entity.rotate + 2 + \
                    (delta_rotate * (frame + 1) / rotate_steps)
                new_rotate = -90 + (tmp - 2 if tmp > 2 else tmp) * 180
        else:
            if abs_diff > 1:
                new_rotate = -90 + \
                    (old_entity.rotate + delta_rotate *
                     (frame + 1) / rotate_steps) * 180
            else:
                tmp = old_entity.rotate - \
                    delta_rotate * (frame + 1) / rotate_steps
                new_rotate = -90 + (2 + tmp if tmp < 0 else tmp) * 180
        return new_rotate

    def rotate_move_rotate(self, frame, entity, e, old_entity, flags: RenderingFlags, rendered_sprite, move_steps):
        angle_move = angle([1, 0], np.asarray(entity.position) - np.asarray(old_entity.position)) / 180

        delta_rotate_1 = abs(old_entity.rotate - angle_move)
        if delta_rotate_1 > 1:
            delta_rotate_1 = 2 - delta_rotate_1
        delta_rotate_2 = abs(angle_move - entity.rotate)
        if delta_rotate_2 > 1:
            delta_rotate_2 = 2 - delta_rotate_2

        rotate_steps_1 = int(delta_rotate_1 / self.rotate_atomic)
        rotate_steps_2 = int(delta_rotate_2 / self.rotate_atomic)
        fake_agent = Agent()
        fake_agent.position = entity.position
        fake_agent.rotate = angle_move
        if frame < rotate_steps_1:
            new_rotate = self.interpolate_rotate(old_entity, fake_agent, frame, rotate_steps_1)
            rendered_sprite.rotate(new_rotate)
            rendered_sprite.rect.centerx = cvt_pos_x(old_entity.position[0])
            rendered_sprite.rect.centery = cvt_pos_y(old_entity.position[1])

        elif frame < rotate_steps_1 + move_steps:
            rendered_sprite.rect.centerx = \
                cvt_pos_x(old_entity.position[0] + (entity.position[0] - old_entity.position[0]) * (frame - rotate_steps_1 + 1) / move_steps)
            rendered_sprite.rect.centery = \
                cvt_pos_y(old_entity.position[1] + (entity.position[1] - old_entity.position[1]) * (frame - rotate_steps_1 + 1) / move_steps)
        elif frame < rotate_steps_1 + move_steps + rotate_steps_2:
            new_rotate = self.interpolate_rotate(fake_agent, entity, frame - rotate_steps_1 - move_steps, rotate_steps_2)
            rendered_sprite.rotate(new_rotate)
        else:
            rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
            rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
            rendered_sprite.rotate(-90 + entity.rotate * 180)
            flags.set_finished_flag(e)
        return flags

    def move_rotate(self, frame, entity, e, old_entity, flags, rendered_sprite, move_steps):
        delta_rotate = abs(entity.rotate - old_entity.rotate)
        rotate_steps = int(delta_rotate / self.rotate_atomic)

        if frame < move_steps:
            rendered_sprite.rect.centerx = \
                cvt_pos_x(old_entity.position[0] + (entity.position[0] - old_entity.position[0]) * (frame + 1) / move_steps)
            rendered_sprite.rect.centery = \
                cvt_pos_y(old_entity.position[1] + (entity.position[1] - old_entity.position[1]) * (frame + 1) / move_steps)
        elif frame < move_steps + rotate_steps:
            new_rotate = self.interpolate_rotate(old_entity, entity, frame - move_steps, rotate_steps)
            rendered_sprite.rotate(new_rotate)
        else:
            rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
            rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
            flags[e] = True
        return flags

    def astar_move(self, frame, rotate_steps, move_steps, entity, e, old_entity, rendered_sprite, flags: RenderingFlags, have_obstacle, way):
        pos_trans = np.zeros(self.dim_p)
        if have_obstacle[e] and way[e]:
            if frame > 1 and frame < move_steps:
                pos_trans[0] = way[e][(
                    len(way[e]) // move_steps) * (frame + 1) - 1][0]
                pos_trans[1] = way[e][(
                    len(way[e]) // move_steps) * (frame + 1) - 1][1]
                pos_old = np.array([way[e][len(way[e]) // move_steps * (frame)][0],
                                    way[e][len(way[e]) // move_steps * (frame)][1]])
                # entity.rotate = angle([1, 0], pos_trans - pos_old) / 180
                rendered_sprite.rotate(-90 + angle([1, 0], pos_trans - pos_old))
                # self.rendered_agents.sprites()[e].X = cvt_pos_x(pos_trans[0])
                # self.rendered_agents.sprites()[e].Y = cvt_pos_y(pos_trans[1])
                rendered_sprite.rect.centerx = cvt_pos_x(pos_trans[0])
                rendered_sprite.rect.centery = cvt_pos_y(pos_trans[1])
            elif frame >= move_steps:
                rendered_sprite.rotate(-90 + entity.attention * 180)
                rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
                rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
                flags.set_finished_flag(e)
        else:
            if frame < move_steps:
                x = (self.old_entities[e].position[0] + (entity.position[0] -
                     self.old_entities[e].position[0]) * (frame + 1) / move_steps)
                # self.rendered_agents.sprites()[e].X = cvt_pos_x(x) - self.rendered_agents.sprites()[e].rect.width/2
                rendered_sprite.rect.centerx = cvt_pos_x(x)
                y = (self.old_entities[e].position[1] + (entity.position[1] -
                     self.old_entities[e].position[1]) * (frame + 1) / move_steps)
                # self.rendered_agents.sprites()[e].Y = cvt_pos_y(y) - self.rendered_agents.sprites()[e].rect.height/2
                rendered_sprite.rect.centery = cvt_pos_y(y)
            else:
                flags.set_finished_flag(e)
        return flags

    def flags_init(self):
        entity_action_finished_flags = [False for _ in range(len(self.entities))]
        nodding_flags = [False for _ in range(len(self.entities))]
        shaking_flags = [False for _ in range(len(self.entities))]
        waving_flags = [False for _ in range(len(self.entities))]
        played_flags = [False for _ in range(len(self.entities))]
        hitting_flags = [False for _ in range(len(self.entities))]
        return entity_action_finished_flags, nodding_flags, shaking_flags, waving_flags, played_flags, hitting_flags

    def entity_nodding(self, frame, e, rendered_sprite, nod_times, entity_action_finished_flags, nodding_flags):
        nodding_flags[e] = True
        rendered_sprite.nodding = True
        rendered_sprite.first_frame = frame % 4
        rendered_sprite.last_frame = frame % 4
        rendered_sprite.update()
        nod_times += 1
        if nod_times // 4 >= NODDING_EPOCHS:
            entity_action_finished_flags[e] = True
        return nod_times, nodding_flags, entity_action_finished_flags

    def entity_shaking(self, frame, e, rendered_sprite, shake_times, entity_action_finished_flags, shaking_flags):
        shaking_flags[e] = True
        rendered_sprite.shaking = True
        if 1 <= frame % 4 <= 2:
            rendered_sprite.rotate(rendered_sprite.rotation - 20)
        else:
            rendered_sprite.rotate(rendered_sprite.rotation + 20)
        shake_times += 1
        if shake_times // 4 >= SHAKING_EPOCHS:
            entity_action_finished_flags[e] = True
        return shake_times, shaking_flags, entity_action_finished_flags

    def entity_play(self, played_num, rendered_sprite, e, entity_action_finished_flags, played_flags):
        played_flags[e] = True
        if played_num != 4 and not entity_action_finished_flags[e]:
            if played_num == 0:
                rendered_sprite.rect.centery -= 20
            elif played_num == 1:
                rendered_sprite.rect.centery += 20
            elif played_num == 2:
                rendered_sprite.rect.centery += 20
            elif played_num == 3:
                rendered_sprite.rect.centery -= 20
            played_num += 1
        else:
            played_num = 0
            entity_action_finished_flags[e] = True
        return played_num, played_flags, entity_action_finished_flags

    def entity_hit(self, hitting_num, rendered_sprite, e, entity_action_finished_flags, hitting_flags):
        hitting_flags[e] = True
        if hitting_num < 10 and not entity_action_finished_flags[e]:
            if hitting_num == 0:
                rendered_sprite.rect.centery -= 20
            elif 1 <= hitting_num % 4 <= 2:
                rendered_sprite.rect.centery += 20
            else:
                rendered_sprite.rect.centery -= 20
            hitting_num += 1
        else:
            hitting_num = 0
            entity_action_finished_flags[e] = True
        return hitting_num, hitting_flags, entity_action_finished_flags

    def render(self, iter=0, show_names=False, current_agent=None):
        self.screen.fill(SCREEN_COLOR)

        frame_data_list = []
        
        # obj opening rendering
        for obj in self.objects:
            if not isinstance(obj, Object):
                continue
            if obj.needs_key and not obj.locked:
                self.obj_unlock_geoms(None, obj)
            if obj.open:
                self.obj_open_geoms(None, obj)
            if obj.is_broken:
                self.obj_broken_geoms(None, obj)

        if self.old_entities:
            # decide whether there is an obstacle, if have obstacle in line, using A*
            obstacle_entities, have_obstacle = self.check_obstacle()
            way = self.cac_astar_way(have_obstacle, obstacle_entities)

            # frame is used for count frame
            frame = 0

            # record played sequence
            played_num = 0
            hitting_num = 0

            flags = RenderingFlags(len(self.entities))

            rotate_atomic = 0.02
            move_atomic = 15

            # the render loop in one step
            nod_times = 0
            shake_times = 0
            waving_times = 0
            pointing_times = 0
            performing_times = 0
            eating_process_times = 0
            # whether exists unfinished action rendering
            while not flags.check_all_finished():
                frame += 1
                for e, entity in enumerate(self.entities):
                    entity_index = self.world_rendered_entity_group_index[entity.id]
                    old_entity = self.old_entities[e]
                    if isinstance(entity, Agent):
                        rendered_sprite = self.rendered_agents.sprites()[entity_index]
                    elif isinstance(entity, Object):
                        rendered_sprite = self.rendered_objects.sprites()[entity_index]
                    else:
                        rendered_sprite = self.rendered_landmarks.sprites()[entity_index]

                    if isinstance(entity, Agent):
                        if (not current_agent) or (current_agent.id == entity.id):
                            if entity.nodding:
                                # nodding_flag = True
                                self.update_noding(e, flags, frame, nod_times, rendered_sprite)
                                nod_times += 1
                                continue
                            else:
                                rendered_sprite.nodding = False

                            if entity.shaking:
                                self.update_shaking(e, flags, frame, shake_times, rendered_sprite)
                                shake_times += 1
                                continue
                            else:
                                rendered_sprite.shaking = False

                            if entity.waving and (current_agent is None or current_agent.id == entity.id):
                                self.update_waving(e, flags, waving_times, rendered_sprite)
                                # speed up the waving rendering
                                waving_times += 3
                                continue
                            else:
                                rendered_sprite.waving = False

                            if entity.pointing:
                                self.update_pointing(e, flags, pointing_times, rendered_sprite)
                                pointing_times += 1
                                continue
                            else:
                                rendered_sprite.pointing = False

                            if entity.performing:
                                self.update_performing(e, flags, performing_times, rendered_sprite)
                                performing_times += 1
                                continue
                            else:
                                rendered_sprite.performing = False

                            if entity.eating:
                                self.eating_process = eating_process_times
                                self.update_eating(e, flags, eating_process_times, rendered_sprite)
                                eating_process_times += 1
                                continue
                            else:
                                rendered_sprite.eating = None

                    if isinstance(entity, Agent) and entity.waving:
                        if (not current_agent) or (current_agent.id == entity.id):
                            flags.set_waving_flag(e)

                    # rotate cannot exceed 180
                    delta_rotate = abs(entity.rotate - old_entity.rotate)
                    if delta_rotate > 1:
                        delta_rotate = 2 - delta_rotate
                    rotate_steps = int(delta_rotate / rotate_atomic)
                    move_steps = int(round(dis(entity, old_entity) / move_atomic))

                    if not self.is_held_by_agent(entity):
                        if isinstance(entity, Object) and entity.being_multi_played:
                            flags.set_played_flag(e)
                            if not flags.check_finished_flag(e):
                                _, played_num = self.render_play(rendered_sprite=rendered_sprite, played_num=played_num)
                                flags.set_finished_flag(e, _)
                            if flags.check_finished_flag(e):
                                continue
                        elif isinstance(entity, Agent) and entity.hitting:
                            flags.set_hitting_flag(e)
                            if not flags.check_finished_flag(e):
                                _, hitting_num = self.render_hit(rendered_sprite=rendered_sprite, hitting_num=hitting_num)
                                flags.set_finished_flag(e, _)
                            if flags.check_finished_flag(e):
                                continue
                        elif isinstance(entity, Agent) and len(entity.action_history) \
                                and not np.array_equal(old_entity.position, entity.position) \
                                and entity.action_history[-1][0] == "ActionMoveToAttention":
                            self.rotate_move_rotate(
                                frame, entity, e, old_entity, flags, rendered_sprite, move_steps)
                        elif isinstance(entity, Agent) and len(entity.action_history) \
                                and not np.array_equal(old_entity.position, entity.position) \
                                and entity.action_history[-1][0] == "ActionMoveTo"\
                                and not have_obstacle[e]:
                            self.rotate_move_rotate(
                                frame, entity, e, old_entity, flags, rendered_sprite,
                                move_steps)
                        # first rotate and then move
                        elif not np.array_equal(old_entity.position, entity.position):
                            # if (not have_obstacle[e]) or (entity.id != agent.id):
                            if not have_obstacle[e]:
                                self.rotate_and_direct_move(
                                    frame, rotate_steps, move_steps, entity, e, old_entity, flags, rendered_sprite)
                            else:
                                self.astar_move(frame, rotate_steps, move_steps, entity, e, self.old_entities,
                                                rendered_sprite, flags, have_obstacle, way)
                        # only rotate
                        elif old_entity.rotate != entity.rotate and np.array_equal(old_entity.position, entity.position):
                            self.only_rotate(
                                frame, rotate_steps, move_steps, entity, e, old_entity, flags, rendered_sprite)

                        elif rotate_steps == 0 and move_steps == 0:
                            flags.set_finished_flag(e)

                    else:
                        # current is held
                        belong_agent_id = entity.being_held_id[0]

                        belong_agent = None
                        old_belong_agent = None
                        for i, ent in enumerate(self.entities):
                            if ent.id == belong_agent_id:
                                belong_agent = ent
                        for i, ent in enumerate(self.old_entities):
                            if ent.id == belong_agent_id:
                                old_belong_agent = ent

                        # assert belong_agent is not None
                        if belong_agent is None or (rotate_steps == 0 and move_steps == 0):
                            # false belief
                            flags.set_finished_flag(e)
                            rendered_sprite.rect.centerx, rendered_sprite.rect.centery = cvt_pos(entity.position)
                            continue

                        # 之前已经被 held，此时跟着一块运动
                        if old_belong_agent is not None and rotate_steps != 0 and move_steps != 0:
                            if belong_agent.rotate != old_belong_agent.rotate:
                                for sprite in self.rendered_agents.sprites():
                                    if sprite.id == belong_agent_id:
                                        rendered_belong_agent_sprite = sprite
                                fake_agent = Agent()
                                fake_agent.position = inverse_pos([rendered_belong_agent_sprite.rect.centerx,
                                                                   rendered_belong_agent_sprite.rect.centery])
                                fake_agent.size = belong_agent.size
                                fake_agent.rotate = inverse_rotation(rendered_belong_agent_sprite.rotation)
                                # new_pos = agent_left_with_offset(fake_agent, entity)
                                new_pos = agent_left_upper_with_offset(fake_agent, entity)
                                rendered_sprite.rect.centerx = cvt_pos_x(new_pos[0])
                                rendered_sprite.rect.centery = cvt_pos_y(new_pos[1])
                                rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)

                                tmp_pos = inverse_pos([rendered_sprite.rect.centerx, rendered_sprite.rect.centery])
                                # print('dist: {}'.format(euclidean_dist(tmp_pos, entity.position)))
                                if euclidean_dist(tmp_pos, entity.position) < 20:
                                    rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
                                    rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
                                    rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)
                                    flags.set_finished_flag(e)
                            else:
                                # 先空中旋转 & 漂移的过程
                                self.rotate_and_direct_move(frame, rotate_steps, move_steps, entity, e, old_entity, flags, rendered_sprite)
                        else:
                            for agent_sprite in self.rendered_agents.sprites():
                                if agent_sprite.id == belong_agent_id:
                                    rendered_belong_agent_sprite = agent_sprite
                            fake_agent = Agent()
                            fake_agent.position = inverse_pos([rendered_belong_agent_sprite.rect.centerx, rendered_belong_agent_sprite.rect.centery])
                            fake_agent.size = belong_agent.size
                            # ActionMoveTo: rotate move rotate
                            fake_agent.rotate = inverse_rotation(rendered_belong_agent_sprite.rotation)
                            # fake_agent.rotate = belong_agent.rotate
                            # new_pos = agent_left_with_offset(fake_agent, entity)
                            new_pos = agent_left_upper_with_offset(fake_agent, entity)
                            rendered_sprite.rect.centerx = cvt_pos_x(new_pos[0])
                            rendered_sprite.rect.centery = cvt_pos_y(new_pos[1])
                            rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)
                            tmp_pos = inverse_pos([rendered_sprite.rect.centerx, rendered_sprite.rect.centery])
                            if euclidean_dist(tmp_pos, entity.position) < 20:
                                rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
                                rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
                                rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)
                                flags.set_finished_flag(e)

                # self.update_alpha(agent)
                self.update_screen(frame, last_frame=True if flags.check_all_finished() else False)

                # image = Image.fromarray(np.frombuffer(pygame.image.tostring(self.screen, "RGB"), dtype=np.uint8).reshape((1400, 1400, 3)))
                # 0902, compress 
                # image = compress_image(self.screen)
                # frame_data = np.asarray(image)
                # frame_data_list.append(frame_data)

                frame_data = compress_and_encode(self.screen)
                frame_data_list.append(frame_data)

                if flags._sleep_more():
                    frame_data_list.extend([frame_data] * 3)

        else:
            # first render
            self.update_screen(0)
        time.sleep(0.15)

        # self.old_agents = copy.deepcopy(self.agents)
        self.old_agents = basic_agent_copy(self.agents)
        # todo, 优化性能, 514
        self.old_entities = copy.deepcopy(self.entities)

        pygame.display.update()
        # frame_data = np.frombuffer(pygame.image.tostring(self.screen, "RGBA"), dtype=np.uint8).reshape([1400, 1400, 4])
        # frame_data_list.extend([frame_data] * 8)
        frame_data = compress_and_encode(self.screen)
        frame_data_list.append(frame_data)
        return frame_data_list

    def create_and_update_belief_entities(self, agent):
        for e, entity in enumerate(agent.belief.entities):
            entity_id = entity.id
            if entity_id not in self.rendered_entity_group_index[agent.id]:
                if isinstance(entity, Agent):
                    self.create_belief_agent(self.screen, agent, entity_id, entity.name)
                if isinstance(entity, Object):
                    self.create_belief_object(agent, entity_id, entity.name)
            else:
                # 标识是否为第一次出现，出于跟渲染的顺序对齐，即 rotate 转过去之后，才渲染那些新出现的 entity
                entity_index = self.rendered_entity_group_index[agent.id][entity_id]
                if isinstance(entity, Agent):
                    rendered_sprite = self.rendered_agents_dict[agent.id].sprites()[entity_index]
                    rendered_sprite.first_appear = False
                elif isinstance(entity, Object):
                    rendered_sprite = self.rendered_objects_dict[agent.id].sprites()[entity_index]
                    rendered_sprite.first_appear = False
                else:
                    rendered_sprite = self.rendered_landmarks_dict[agent.id].sprites()[entity_index]
                    rendered_sprite.first_appear = False

            # obj opening rendering
            if isinstance(entity, Object):

                # if len(entity.being_contained) > 0:
                #     self.contained_geoms(agent, entity)
                # else:
                #     self.contained_recovered_geoms(agent, entity)

                if ('box' in entity.name or 'shelf' in entity.name) or entity.is_container:
                    self.obj_container_status_geoms(agent, entity)

                if entity.is_broken:
                    self.obj_broken_geoms(agent, entity)

        # delete false belief agent_sprite/object_sprite
        for entity_id in deepcopy(self.rendered_entity_group_index[agent.id]):
            if entity_id not in agent.belief.all_ids:
                if isinstance(self.retrieve_by_id(entity_id), Agent):
                    self.delete_belief_agent(agent, entity_id)
                if isinstance(self.retrieve_by_id(entity_id), Object):
                    self.delete_belief_object(agent, entity_id)

                # something is eaten
                if self.retrieve_by_id(entity_id) is None:
                    self.delete_belief_object(agent, entity_id)

    def render_play(self, rendered_sprite, played_num):
        if played_num != 4:
            if played_num == 0:
                rendered_sprite.rect.centery -= 20
            elif played_num == 1:
                rendered_sprite.rect.centery += 20
            elif played_num == 2:
                rendered_sprite.rect.centery -= 20
            elif played_num == 3:
                rendered_sprite.rect.centery += 20
            played_num += 1
        else:
            played_num = 0
            return True, played_num
        return False, played_num

    def render_hit(self, rendered_sprite, hitting_num):
        if hitting_num < 10:
            if hitting_num == 0:
                rendered_sprite.rect.centery -= 20
            elif 1 <= hitting_num % 4 <= 2:
                rendered_sprite.rect.centery += 20
            else:
                rendered_sprite.rect.centery -= 20
            hitting_num += 1
        else:
            hitting_num = 0
            return True, hitting_num
        return False, hitting_num

    def init_belief_rendered_sprite(self, agent, entity):
        entity_id = entity.id
        entity_index = self.rendered_entity_group_index[agent.id][entity_id]
        # retrieve the corresponding rendered_sprite of the entities in the world
        if isinstance(entity, Agent):
            rendered_sprite = self.rendered_agents_dict[agent.id].sprites()[entity_index]
        elif isinstance(entity, Object):
            rendered_sprite = self.rendered_objects_dict[agent.id].sprites()[entity_index]
        else:
            rendered_sprite = self.rendered_landmarks_dict[agent.id].sprites()[entity_index]
        return rendered_sprite

    def locate_pos_with_entity(self, pos, agent=None):
        entities = self.entities if agent is None else agent.belief.entities
        pos = np.asarray(pos)
        largest_entity = None
        max_area = -1
        for entity in entities:
            if entity.contains(pos):
                entity_area = entity.area()
                if entity_area > max_area:
                    max_area = entity_area
                    largest_entity = entity
        return largest_entity

    def _agent_sprite_pos_attention_framewise(self, this_agent_id, agent_id):
        # only for rendering belief
        try:
            agent_sprite = self.rendered_agents_dict[this_agent_id].sprites()[self.rendered_entity_group_index[this_agent_id][agent_id]]
            pos = inverse_pos([agent_sprite.rect.centerx, agent_sprite.rect.centery])
            att = inverse_rotation(agent_sprite.rotation)
        except:
            pos = None, None
            att = None
        return pos, att

    def render_belief(self, agent, iter=0, current_agent=None, update_belief_record=True):
        '''
        :param agent: show the belief of the agent
        :param iter:
        :param current_agent: the agent that has done the action
        :param update_belief_record:
        :return:
        '''
        mutex.acquire()
        self.screen.fill(SCREEN_COLOR)

        frame_data_list = []
        # maintain agent_sprite pos attention for frontend rendering
        agent_pos_attention_framewise = defaultdict(list)
        other_agent = self.retrieve_by_id(3 - agent.id)

        self.render_agent_belief(agent)
        self.create_and_update_belief_entities(agent=agent)

        agent_old_entities = self.agent_old_entities.get(agent.id, None)
        # if self.old_agents:
        # frame is used for count frame
        frame = 0

        if agent_old_entities:
            # with history position
            # linear interpolation when there is no obstacle
            # otherwise, A*
            # decide whether there is an obstacle
            obstacle_entities, have_obstacle = self.check_belief_obstacle(agent)
            # if have obstacle in line, using A*
            t = time.time()
            way = self.cac_belief_astar_way(agent, have_obstacle, obstacle_entities)

            # record played sequence
            played_num = 0
            hitting_num = 0

            flags = RenderingFlags(len(agent.belief.entities))

            # the render loop in one step
            nod_times_dict = {}
            shake_times_dict = {}
            waving_times_dict = {}
            pointing_times_dict = {}
            performing_times_dict = {}
            eating_process_times_dict = {}

            while not flags.check_all_finished():
                frame += 1
                # nodding_flag = False
                # waving_flag = False
                for e, entity in enumerate(agent.belief.entities):
                    try:
                        rendered_sprite = self.init_belief_rendered_sprite(agent=agent, entity=entity)
                    except:
                        flags.set_finished_flag(e)
                        continue

                    if isinstance(entity, Agent):
                        if entity.nodding:
                            if nod_times_dict.get(entity.id) is None:
                                nod_times_dict[entity.id] = 0
                            # nodding_flag = True
                            self.update_noding(e, flags, frame, nod_times_dict[entity.id], rendered_sprite)
                            nod_times_dict[entity.id] += 1
                            continue
                        else:
                            rendered_sprite.nodding = False

                        if entity.shaking:
                            if shake_times_dict.get(entity.id) is None:
                                shake_times_dict[entity.id] = 0
                            self.update_shaking(e, flags, frame, shake_times_dict[entity.id], rendered_sprite)
                            shake_times_dict[entity.id] += 1
                            continue
                        else:
                            rendered_sprite.shaking = False

                        if entity.waving and (current_agent is None or current_agent.id == entity.id):
                            if waving_times_dict.get(entity.id) is None:
                                waving_times_dict[entity.id] = 0
                            self.update_waving(e, flags, waving_times_dict[entity.id], rendered_sprite)
                            # speed up the waving rendering
                            waving_times_dict[entity.id] += 3
                            continue
                        else:
                            rendered_sprite.waving = False

                        if entity.pointing:
                            if pointing_times_dict.get(entity.id) is None:
                                pointing_times_dict[entity.id] = 0
                            self.update_pointing(e, flags, pointing_times_dict[entity.id], rendered_sprite)
                            pointing_times_dict[entity.id] += 1
                            continue
                        else:
                            rendered_sprite.pointing = False

                        if entity.performing:
                            if performing_times_dict.get(entity.id) is None:
                                performing_times_dict[entity.id] = 0
                            self.update_performing(e, flags, performing_times_dict[entity.id], rendered_sprite)
                            performing_times_dict[entity.id] += 1
                            continue
                        else:
                            rendered_sprite.performing = False

                        if entity.eating:
                            if eating_process_times_dict.get(entity.id) is None:
                                eating_process_times_dict[entity.id] = 0
                            self.eating_process = eating_process_times_dict[entity.id]
                            self.update_eating(e, flags, eating_process_times_dict[entity.id], rendered_sprite)
                            # for gif generating, slower
                            # time.sleep(0.3)
                            eating_process_times_dict[entity.id] += 1
                            continue
                        else:
                            rendered_sprite.eating = None

                    if isinstance(entity, Agent) and entity.waving:
                        flags.set_waving_flag(e)

                    agent_old_entities_e = None

                    for tmp_e in agent_old_entities:
                        if tmp_e.id == entity.id:
                            agent_old_entities_e = tmp_e

                    if not agent_old_entities_e:
                        flags.set_finished_flag(e)
                        # new appearing agent
                        if isinstance(entity, Agent):
                            self._map_rotate_pos(entity, rendered_sprite)
                        continue

                    # if not adjacent observation, don't interpolate
                    # 是否在视野中发生的变化
                    if entity.id != agent.id and (entity.be_observed_time - agent_old_entities_e.be_observed_time) != 1:
                        flags.set_finished_flag(e)
                        isin_attention = agent.attention_check(entity, self) == 1
                        # 当前不在视野中
                        if not isin_attention:
                            self._map_rotate_pos(entity, rendered_sprite)
                        else:
                            # 当前在视野中，之前不在视野中，最后一帧才改状态
                            rendered_sprite.reappear = True
                        continue

                    rendered_sprite.reappear = False

                    # rotate cannot exceed 180
                    delta_rotate = abs(entity.rotate - agent_old_entities_e.rotate)
                    if delta_rotate > 1:
                        delta_rotate = 2 - delta_rotate
                    rotate_steps = int(delta_rotate / self.rotate_atomic)
                    # rotate_steps = min(rotate_steps, 1)
                    move_steps = int(round(dis(entity, agent_old_entities_e) / self.move_atomic))
                    # move_steps = min(move_steps, 1)

                    # current not be held
                    if not self.is_held_by_agent(entity):
                        if isinstance(entity, Object) and entity.being_multi_played:
                            flags.set_played_flag(e)
                            if not flags.check_finished_flag(e):
                                _, played_num = self.render_play(rendered_sprite=rendered_sprite, played_num=played_num)
                                flags.set_finished_flag(e, _)
                            if flags.check_finished_flag(e):
                                continue
                        elif isinstance(entity, Agent) and entity.hitting:
                            flags.set_hitting_flag(e)
                            if not flags.check_finished_flag(e):
                                _, hitting_num = self.render_hit(rendered_sprite=rendered_sprite, hitting_num=hitting_num)
                                flags.set_finished_flag(e, _)
                            if flags.check_finished_flag(e):
                                continue
                        elif isinstance(entity, Agent) and len(entity.action_history) \
                                and not np.array_equal(agent_old_entities_e.position, entity.position) \
                                and entity.action_history[-1][0] == "ActionMoveToAttention":
                            self.rotate_move_rotate(
                                frame, entity, e, agent_old_entities_e, flags, rendered_sprite, move_steps)
                        elif isinstance(entity, Agent) and len(entity.action_history) \
                                and not np.array_equal(agent_old_entities_e.position, entity.position) \
                                and entity.action_history[-1][0] == "ActionMoveTo"\
                                and not have_obstacle[e]:
                            self.rotate_move_rotate(
                                frame, entity, e, agent_old_entities_e, flags, rendered_sprite,
                                move_steps)
                        # first rotate and then move
                        elif not np.array_equal(agent_old_entities_e.position, entity.position):
                            # if (not have_obstacle[e]) or (entity.id != agent.id):
                            if not have_obstacle[e]:
                                self.rotate_and_direct_move(
                                    frame, rotate_steps, move_steps, entity, e, agent_old_entities_e, flags, rendered_sprite)
                            else:
                                self.astar_move(frame, rotate_steps, move_steps, entity, e, agent_old_entities,
                                                rendered_sprite, flags, have_obstacle, way)
                        # only rotate
                        elif agent_old_entities_e.rotate != entity.rotate and np.array_equal(agent_old_entities_e.position, entity.position):
                            self.only_rotate(
                                frame, rotate_steps, move_steps, entity, e, agent_old_entities_e, flags, rendered_sprite)

                        elif rotate_steps == 0 and move_steps == 0:
                            flags.set_finished_flag(e)

                    else:
                        # current is held
                        belong_agent_id = entity.being_held_id[0]

                        belong_agent = None
                        old_belong_agent = None
                        for i, ent in enumerate(agent.belief.entities):
                            if ent.id == belong_agent_id:
                                belong_agent = ent
                        for i, ent in enumerate(agent_old_entities):
                            if ent.id == belong_agent_id:
                                old_belong_agent = ent

                        # assert belong_agent is not None
                        if belong_agent is None or (rotate_steps == 0 and move_steps == 0):
                            # false belief
                            flags.set_finished_flag(e)
                            rendered_sprite.rect.centerx, rendered_sprite.rect.centery = cvt_pos(entity.position)
                            continue

                        # 之前已经被 held，此时跟着一块运动
                        if old_belong_agent is not None and rotate_steps != 0 and move_steps != 0:
                            if belong_agent.rotate != old_belong_agent.rotate:
                                rendered_belong_agent_sprite = self.rendered_agents_dict[agent.id].sprites()[self.rendered_entity_group_index[agent.id][belong_agent_id]]
                                fake_agent = Agent()
                                fake_agent.position = inverse_pos([rendered_belong_agent_sprite.rect.centerx,
                                                                   rendered_belong_agent_sprite.rect.centery])
                                fake_agent.size = belong_agent.size
                                fake_agent.rotate = inverse_rotation(rendered_belong_agent_sprite.rotation)
                                # new_pos = agent_left_with_offset(fake_agent, entity)
                                new_pos = agent_left_upper_with_offset(fake_agent, entity)
                                rendered_sprite.rect.centerx = cvt_pos_x(new_pos[0])
                                rendered_sprite.rect.centery = cvt_pos_y(new_pos[1])
                                rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)

                                tmp_pos = inverse_pos([rendered_sprite.rect.centerx, rendered_sprite.rect.centery])
                                # print('dist: {}'.format(euclidean_dist(tmp_pos, entity.position)))
                                if euclidean_dist(tmp_pos, entity.position) < 20:
                                    rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
                                    rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
                                    rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)
                                    flags.set_finished_flag(e)
                            else:
                                # 先空中旋转 & 漂移的过程
                                self.rotate_and_direct_move(frame, rotate_steps, move_steps, entity, e, agent_old_entities_e, flags, rendered_sprite)
                        else:
                            rendered_belong_agent_sprite = self.rendered_agents_dict[agent.id].sprites()[self.rendered_entity_group_index[agent.id][belong_agent_id]]
                            fake_agent = Agent()
                            fake_agent.position = inverse_pos([rendered_belong_agent_sprite.rect.centerx, rendered_belong_agent_sprite.rect.centery])
                            fake_agent.size = belong_agent.size
                            # ActionMoveTo: rotate move rotate
                            fake_agent.rotate = inverse_rotation(rendered_belong_agent_sprite.rotation)
                            # fake_agent.rotate = belong_agent.rotate
                            # new_pos = agent_left_with_offset(fake_agent, entity)
                            new_pos = agent_left_upper_with_offset(fake_agent, entity)
                            rendered_sprite.rect.centerx = cvt_pos_x(new_pos[0])
                            rendered_sprite.rect.centery = cvt_pos_y(new_pos[1])
                            rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)
                            tmp_pos = inverse_pos([rendered_sprite.rect.centerx, rendered_sprite.rect.centery])
                            if euclidean_dist(tmp_pos, entity.position) < 20:
                                rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
                                rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])
                                rendered_sprite.rotate(rendered_belong_agent_sprite.rotation)
                                flags.set_finished_flag(e)

                # self.update_alpha(agent)
                self.update_screen(frame, agent, last_frame=True if flags.check_all_finished() else False)

                # image = Image.fromarray(np.frombuffer(pygame.image.tostring(self.screen, "RGB"), dtype=np.uint8).reshape((1400, 1400, 3)))
                # 0902, compress 
                # image = compress_image(self.screen)
                # frame_data = np.asarray(image)
                # frame_data_list.append(frame_data)

                frame_data = compress_and_encode(self.screen)
                frame_data_list.append(frame_data)

                agent_pos_attention_framewise[agent.id].append(self._agent_sprite_pos_attention_framewise(agent.id, agent.id))
                agent_pos_attention_framewise[other_agent.id].append(self._agent_sprite_pos_attention_framewise(agent.id, other_agent.id))

                if flags._sleep_more():
                    frame_data_list.extend([frame_data] * 3)
                    agent_pos_attention_framewise[agent.id].extend([agent_pos_attention_framewise[agent.id][-1]] * 3)
                    agent_pos_attention_framewise[other_agent.id].extend([agent_pos_attention_framewise[other_agent.id][-1]] * 3)

        else:
            # first render
            self.update_screen(0, agent)

        if update_belief_record is True:
            agent_old_entities = copy.deepcopy(agent.belief.entities)
            self.agent_old_entities[agent.id] = agent_old_entities

        # self.update_screen(iter, frame if agent_old_entities else 0, show_rect, agent, last_frame=True)
        # image = Image.fromarray(np.frombuffer(pygame.image.tostring(self.screen, "RGB"), dtype=np.uint8).reshape((1400, 1400, 3)))
        # image = compress_image(self.screen)
        # frame_data = np.asarray(image)
        # # fixme，0421，steps 之间有一些停顿；
        # frame_data_list.extend([frame_data] * 2)

        frame_data = compress_and_encode(self.screen)
        frame_data_list.extend([frame_data] * 2)

        if len(agent_pos_attention_framewise[agent.id]) <= 0:
            agent_pos_attention_framewise[agent.id].append(self._agent_sprite_pos_attention_framewise(agent.id, agent.id))
            agent_pos_attention_framewise[agent.id].append(self._agent_sprite_pos_attention_framewise(agent.id, agent.id))
            agent_pos_attention_framewise[other_agent.id].append(self._agent_sprite_pos_attention_framewise(agent.id, other_agent.id))
            agent_pos_attention_framewise[other_agent.id].append(self._agent_sprite_pos_attention_framewise(agent.id, other_agent.id))
        else:
            agent_pos_attention_framewise[agent.id].extend([agent_pos_attention_framewise[agent.id][-1]] * 2)
            agent_pos_attention_framewise[other_agent.id].extend([agent_pos_attention_framewise[other_agent.id][-1]] * 2)

        mutex.release()
        assert len(frame_data_list) == len(agent_pos_attention_framewise[agent.id]) == len(agent_pos_attention_framewise[other_agent.id])
        # print('agent_pos_attention_framewise', agent_pos_attention_framewise)
        return frame_data_list, agent_pos_attention_framewise

    def update_shaking(self, entity_index, flags, frame, shake_times, rendered_sprite):
        flags.set_shaking_flag(entity_index)
        rendered_sprite.shaking = True
        if 1 <= shake_times % 4 <= 2:
            rendered_sprite.rotate(rendered_sprite.rotation - 20)
        else:
            rendered_sprite.rotate(rendered_sprite.rotation + 20)
        if shake_times // 4 >= SHAKING_EPOCHS:
            rendered_sprite.rotate(rendered_sprite.rotation - 20)
            flags.set_finished_flag(entity_index)

    def update_noding(self, entity_index, flags, frame, nod_times, rendered_sprite):
        flags.set_nodding_flag(entity_index)
        rendered_sprite.nodding = True
        rendered_sprite.first_frame = frame % 4
        rendered_sprite.last_frame = frame % 4
        rendered_sprite.update()

        if nod_times // 4 >= NODDING_EPOCHS:
            flags.set_finished_flag(entity_index)

    def update_waving(self, entity_index, flags, waving_times, rendered_sprite):
        flags.set_waving_flag(entity_index)
        rendered_sprite.waving = True
        if waving_times // 14 >= WAVING_EPOCHS:
            flags.set_finished_flag(entity_index)

    def update_pointing(self, entity_index, flags, pointing_times, rendered_sprite):
        flags.set_pointing_flag(entity_index)
        rendered_sprite.pointing = True
        if pointing_times // 5 >= POINTING_EPOCHS:
            flags.set_finished_flag(entity_index)
    
    def update_eating(self, entity_index, flags, eating_process_times, rendered_sprite):
        flags.set_eating_flag(entity_index)
        if eating_process_times >= 1:
            flags.set_finished_flag(entity_index)
    

    def update_performing(self, entity_index, flags, performing_times, rendered_sprite):
        flags.set_performing_flag(entity_index)
        rendered_sprite.performing = True
        if performing_times // 4 >= PERFORMING_EPOCHS:
            flags.set_finished_flag(entity_index)

    def _map_rotate_pos(self, entity, rendered_sprite):
        rendered_sprite.rotate(-90 + entity.rotate * 180)
        rendered_sprite.rect.centerx = cvt_pos_x(entity.position[0])
        rendered_sprite.rect.centery = cvt_pos_y(entity.position[1])

    def update_agent_alpha(self, agent, last_frame=False):
        if agent is None:
            return
        for e, entity in enumerate(agent.belief.entities):
            isin_attention = agent.attention_check(entity, self) == 1

            if entity.id == agent.id:
                # self
                isin_attention = True

            entity_id = entity.id
            if entity_id not in self.rendered_entity_group_index[agent.id]:
                if isinstance(entity, Agent):
                    self.create_belief_agent(self.screen, agent, entity_id, entity.name)
                if isinstance(entity, Object):
                    self.create_belief_object(agent, entity_id, entity.name)
            entity_index = self.rendered_entity_group_index[agent.id][entity_id]

            if isinstance(entity, Agent):
                rendered_sprite = self.rendered_agents_dict[agent.id].sprites()[entity_index]
            elif isinstance(entity, Object):
                rendered_sprite = self.rendered_objects_dict[agent.id].sprites()[entity_index]
            else:
                rendered_sprite = self.rendered_landmarks_dict[agent.id].sprites()[entity_index]

            if isin_attention:
                rendered_sprite.isin_attention = True
                if not last_frame and rendered_sprite.reappear:
                    rendered_sprite.downscale_alpha()
                else:
                    if last_frame and rendered_sprite.reappear:
                        # print('done!!!')
                        self._map_rotate_pos(entity, rendered_sprite)
                    rendered_sprite.reset_alpha()
            else:
                rendered_sprite.isin_attention = False
                rendered_sprite.downscale_alpha()

    def _draw_rendered_objects(self, rendered_objects_group, agent=None):
        # only for rendering the last frame
        sorted_sprites = sorted(rendered_objects_group.sprites(), key=lambda sprite: sprite.rect.width * sprite.rect.height, reverse=True)
        for sprite in sorted_sprites:
            if agent and agent.belief.get(sprite.id) and agent.belief.get(sprite.id).hidden:
                print(f'{sprite.name}_{sprite.id} is hidden')
                continue

            if agent:
                self._maybe_render_unlock(agent.id, sprite, last_frame=True)
            self.screen.blit(sprite.image, sprite.rect)

    def obj_container_status_geoms(self, user_agent, obj):
        if user_agent is None:
            entity_index = self.world_rendered_entity_group_index[obj.id]
            sprite = self.rendered_objects.sprites()[entity_index]
        else:
            entity_index = self.rendered_entity_group_index[user_agent.id][obj.id]
            sprite = self.rendered_objects_dict[user_agent.id].sprites()[entity_index]

        if obj.open:
            if 'shelf' in obj.name:
                sprite.load('assets/shelf_open.png', *ENTITY_SIZE_CONFIG['shelf_open'], 1)
            else:
                # box
                if obj.needs_key:
                    assert not obj.locked
                    if 'box' in obj.name and len(obj.being_contained) > 0 and 'shelf' in self.retrieve_by_id(obj.being_contained[0]).name:
                        sprite.load('assets/box_unlock_open_small.png', *ENTITY_SIZE_CONFIG['box_unlock_open_small'], 1)
                    else:
                        sprite.load('assets/box_unlock_open.png', *ENTITY_SIZE_CONFIG['box_unlock_open'], 1)
                else:
                    if 'box' in obj.name and len(obj.being_contained) > 0 and 'shelf' in self.retrieve_by_id(obj.being_contained[0]).name:
                        sprite.load('assets/box_open_small.png', *ENTITY_SIZE_CONFIG['box_open_small'], 1)
                    else:
                        sprite.load('assets/box_open.png', *ENTITY_SIZE_CONFIG['box_open'], 1)
        else:
            # close
            if 'shelf' in obj.name:
                sprite.load('assets/shelf.png', *ENTITY_SIZE_CONFIG['shelf'], 1)
            else:
                if obj.needs_key:
                    if obj.locked:
                        if 'box' in obj.name and len(obj.being_contained) > 0 and 'shelf' in self.retrieve_by_id(
                                obj.being_contained[0]).name:
                            sprite.load('assets/box_lock_small.png', *ENTITY_SIZE_CONFIG['box_lock_small'], 1)
                        else:
                            sprite.load('assets/box_lock.png', *ENTITY_SIZE_CONFIG['box_lock'], 1)
                    else:
                        if 'box' in obj.name and len(obj.being_contained) > 0 and 'shelf' in self.retrieve_by_id(
                                obj.being_contained[0]).name:
                            sprite.load('assets/box_unlock_small.png', *ENTITY_SIZE_CONFIG['box_unlock_small'], 1)
                        else:
                            sprite.load('assets/box_unlock.png', *ENTITY_SIZE_CONFIG['box_unlock'], 1)
                else:
                    if 'box' in obj.name and len(obj.being_contained) > 0 and 'shelf' in self.retrieve_by_id(
                            obj.being_contained[0]).name:
                        sprite.load('assets/box_small.png', *ENTITY_SIZE_CONFIG['box_small'], 1)
                    else:
                        sprite.load('assets/box.png', *ENTITY_SIZE_CONFIG['box'], 1)
        sprite.rect.centerx, sprite.rect.centery = cvt_pos(obj.position)
        sprite.rotate(-90 + obj.rotate * 180)


    # obj open
    def obj_open_geoms(self, user_agent, obj):
        # TODO
        if user_agent is None:
            entity_index = self.world_rendered_entity_group_index[obj.id]
            sprite = self.rendered_objects.sprites()[entity_index]
        else:
            entity_index = self.rendered_entity_group_index[user_agent.id][obj.id]
            sprite = self.rendered_objects_dict[user_agent.id].sprites()[entity_index]
        if 'shelf' in obj.name:
            sprite.load('assets/shelf_open.png', *ENTITY_SIZE_CONFIG['shelf_open'], 1)
        else:
            if obj.needs_key:
                sprite.load('assets/box_unlock_open.png', *ENTITY_SIZE_CONFIG['box_unlock_open'], 1)
            else:
                sprite.load('assets/box_open.png', *ENTITY_SIZE_CONFIG['box_open'], 1)
        sprite.rect.centerx, sprite.rect.centery = cvt_pos(obj.position)
        sprite.rotate(-90 + obj.rotate * 180)
        return

    def obj_close_geoms(self, user_agent, obj):
        if user_agent is None:
            entity_index = self.world_rendered_entity_group_index[obj.id]
            sprite = self.rendered_objects.sprites()[entity_index]
        else:
            entity_index = self.rendered_entity_group_index[user_agent.id][obj.id]
            sprite = self.rendered_objects_dict[user_agent.id].sprites()[entity_index]
        if 'shelf' in obj.name:
            sprite.load('assets/shelf.png', *ENTITY_SIZE_CONFIG['shelf'], 1)
        else:
            if obj.needs_key:
                if obj.locked:
                    sprite.load('assets/box_lock.png', *ENTITY_SIZE_CONFIG['box_lock'], 1)
                else:
                    sprite.load('assets/box_unlock.png', *ENTITY_SIZE_CONFIG['box_unlock'], 1)
            else:
                sprite.load('assets/box.png', *ENTITY_SIZE_CONFIG['box'], 1)
        sprite.rect.centerx, sprite.rect.centery = cvt_pos(obj.position)
        sprite.rotate(-90 + obj.rotate * 180)
        return

    def obj_broken_geoms(self, user_agent, obj):
        if 'cup' not in obj.name:
            return
        if user_agent is None:
            entity_index = self.world_rendered_entity_group_index[obj.id]
            sprite = self.rendered_objects.sprites()[entity_index]
        else:
            entity_index = self.rendered_entity_group_index[user_agent.id][obj.id]
            sprite = self.rendered_objects_dict[user_agent.id].sprites()[entity_index]
        sprite.load('assets/cup_broken.png', 90, 56, 1)
        sprite.rect.centerx, sprite.rect.centery = cvt_pos(obj.position)
        sprite.rotate(-90 + obj.rotate * 180)
        return

    def obj_unlock_geoms(self, user_agent, obj):
        # TODO
        if user_agent is None:
            entity_index = self.world_rendered_entity_group_index[obj.id]
            sprite = self.rendered_objects.sprites()[entity_index]
        else:
            entity_index = self.rendered_entity_group_index[user_agent.id][obj.id]
            sprite = self.rendered_objects_dict[user_agent.id].sprites()[entity_index]
        sprite.load("assets/box_unlock.png", *ENTITY_SIZE_CONFIG['box_unlock'], 1)
        # if 'shelf' in obj.name:
        #     sprite.load('assets/shelf_open_255x300.png', 255, 300, 1)
        # else:
        #     sprite.load('assets/box_open_160x120.png', 160, 120, 1)
        sprite.rect.centerx, sprite.rect.centery = cvt_pos(obj.position)
        sprite.rotate(-90 + obj.rotate * 180)
        return

    def _rot_center(self, image, angle):
        """rotate a Surface, maintaining position."""
        loc = image.get_rect().center  # rot_image is not defined
        rot_sprite = pygame.transform.rotate(image, angle)
        rot_sprite.get_rect().center = loc
        return rot_sprite

    def _show_grabing_hand(self, user_agent=None, last_frame=False):
        agents = self.agents if user_agent is None else user_agent.belief.agents
        for agent in agents:
            if len(agent.holding_ids) == 0:
                continue
            # left hand hold
            if user_agent is None:
                rendered_agent = self.rendered_agents.sprites()[self.world_rendered_entity_group_index[agent.id]]
            else:
                rendered_agent = self.rendered_agents_dict[user_agent.id].sprites()[self.rendered_entity_group_index[user_agent.id][agent.id]]

            if last_frame or (not last_frame and not rendered_agent.first_appear) or rendered_agent.id == user_agent.id:
                if user_agent is None:
                    image = pygame.image.load("assets/agent_{}_grab.png".format(agent.id))
                else:
                    image = pygame.image.load("assets/agent_{}_grab.png".format(5 if agent.id == user_agent.id else agent.id))
                image_alpha = image.convert_alpha()
                image_alpha = self._rot_center(image_alpha, rendered_agent.rotation - 27)
                # x, y = render_agent_middle_left_pos(rendered_agent)
                x, y = render_agent_left_upper_pos(rendered_agent)
                image_rect = image_alpha.get_rect(center=(x, y))
                if not rendered_agent.isin_attention:
                    image_alpha.set_alpha(rendered_agent.default_alpha//DOWN_SCALED_ALPHA)
                else:
                    image_alpha.set_alpha(rendered_agent.default_alpha)
                self.screen.blit(image_alpha, image_rect)

    # do not take entity into account
    def position_available_check(self, position):
        if position[0] < -WORLD_WIDTH or position[0] > WORLD_WIDTH:
            return False
        if position[1] < -WORLD_HEIGHT or position[1] > WORLD_HEIGHT:
            return False
        # take landmark as rectangle, which can make mistake
        for landmark in self.landmarks:
            if (landmark.position[0] + landmark.size[0] / 2 + 50) > position[0] > (landmark.position[0] - landmark.size[0] / 2 - 50) and \
                    (landmark.position[1] + landmark.size[1] / 2 + 50) > position[1] > (landmark.position[1] - landmark.size[1] / 2 - 50):
                return False
        return True

    @staticmethod
    def _sleep_more(flags, nodding_flags, shaking_flags, waving_flags, played_flags, hitting_flags,):
        for i, flag in enumerate(flags):
            if not flag and (nodding_flags[i] or waving_flags[i] or played_flags[i] or hitting_flags[i] or shaking_flags[i]):
                return True
        return False

    def is_held_by_agent(self, entity):
        if isinstance(entity, Object) and len(entity.being_held_id) > 0:
            for held_id in entity.being_held_id:
                if isinstance(self.retrieve_by_id(held_id), Agent):
                    return True
        return False

    def _location_occupied_map(self):
        location_map = dict()
        for entity in self.entities:
            location_map[tuple(entity.position)] = entity
        return location_map

    def location_has_been_occupied(self, location, eps=10):
        location_map = self._location_occupied_map()
        for pos, entity in location_map.items():
            if euclidean_dist(pos, location) <= eps:
                return True, entity
        return False, None

    def close(self):
        pygame.display.quit()
        pygame.quit()

    def exist_in_last_belief(self, target_id, agent_id):
        if isinstance(target_id, Entity):
            target_id = target_id.id
        if isinstance(agent_id, Entity):
            agent_id = agent_id.id
        if self.agent_old_entities.get(agent_id) is None:
            return False
        else:
            for entity in self.agent_old_entities[agent_id]:
                if entity.id == target_id:
                    return True
            return False

    def initialize_id_to_name_str(self):
        """初始化id_to_name_str映射"""
        for entity in self.entities:
            if isinstance(entity, Agent):
                self.id_to_name_str[entity.id] = f'agent_{entity.id}'
            else:
                self.id_to_name_str[entity.id] = f'{entity.name}_{entity.id}'

    def add_object(self, object):
        # 现有代码
        self.id_to_name_str[object.id] = f'{object.name}_{object.id}'
        return object

    def add_agent(self, agent):
        # 现有代码
        self.id_to_name_str[agent.id] = f'agent_{agent.id}'
        return agent

    def add_landmark(self, landmark):
        # 现有代码
        self.id_to_name_str[landmark.id] = f'{landmark.name}_{landmark.id}'
        return landmark
