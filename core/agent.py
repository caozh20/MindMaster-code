# import numpy as np
# from copy import deepcopy
# import random
# from random import choice
import numpy as np

from utils.base import *
from .agent_utils import _attention_check
from .const import *
from .desire import *
from .entity_utils import _no_obstacle_check
from .intent import *
# from .inverse_infer_belief import _inverse_infer_belief
# from .inverse_infer_desire import _inverse_infer_desire
# from .inverse_infer_intent import _inverse_infer_intent
# from .plan import _update_goal, _update_task, _act
# from .update_all_tasks import _update_all_tasks
# from .update_intent import _update_intent
# from .update_plan import _update_plan
# from .world import *
# from .scenario import *
from .entity import *
# from .inverse_infer_belief import *
# from .agent_utils import *
# from .condition import Condition
# from memory_profiler import profile

class Agent(Entity):
    def __init__(self, name=None,
                       id = None,
                       attention=None,
                       position=None):
        super(Agent, self).__init__()

        self.name = name
        self.id = id

        # observable attributes
        self._position = position
        # self.bodypose=None
        self.size = 50
        self.attention = attention
        self.visual_distance = 400

        self.holding_ids = []
        # self.holding_entities=[]

        self.pointing = None
        self.lifting = []
        self.waving = None
        self.hitting = None
        self.speaking = None         # todo: speaking will stop after one step
        self.performing = None
        self.nodding = False
        self.shaking = False
        self.playing = None
        self.eating = None
        # Whether the hands are occupied, if true then cannot open
        self.hands_occupied = False

        self.action_history=[]

        self.observation = None

        self.desire = Desire()
        self.belief = Belief()
        self.intents = {"HIHU":[], "HILU":[], "LIHU":[], "LILU":[]}
        self.intent_history_llm = []
        self.other_intent_history_llm = []

        # the origin initial intent, for online game
        self.initial_intent = None

        self.intent_now = None
        self.intent_type_now = None
        self.intent_fail = None
        self.failed_intent = []
        # record the previous successful intent to avoid repetitive help
        self.intent_last = None
        self.intent_history = dict()
        self.intent_related_ids = []

        # self.memory=[] # a list of beliefs

        # task planning
        # we have a history of intents
        # goal (current hierarchical intent) --> task --> plan
        self.goal=None
        self.goal_name=None
        self.goal_over=False
        # self.goal_success=False
        # self.new_goal_flag=False
        self.all_tasks=[]
        self.task=None
        # self.task_success=False
        self.task_level=None
        self.task_name=None
        self.task_fail=False
        self.task_over=False
        self.plan=[]
        self.trial_n=0
        self.plan_recycle=None
        self.action_fail=False
        # record the time that being observed
        self.be_observed_time = None
        self.point_confirm = False
        # record the observation in one time step
        # self.be_observation = None

        # condition for action and plan
        # self.condition = Condition()
        # maintain the finished intent list
        self.finished_intent = []

        # 当玩多人游戏时，需要记录正在玩的游戏，以便即使更新游戏的被玩状态
        self.playing_object_id = None

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = np.asarray(pos)

    @position.getter
    def position(self):
        return np.asarray(self._position)

    def intents_len(self):
        L=0
        for k, v in self.intents.items():
            L+=len(v)
        if self.intent_now is not None:
            L+=1
        return L

    def reset_position(self):
        #todo:这里先只改这三个属性
        self.position = None
        self.rotate = None
        self.attention =  None

    def reset_mind(self):

        self.desire=Desire()
        self.belief=Belief()
        self.intents={"HIHU":[], "HILU":[], "LIHU":[], "LILU":[]}
        self.failed_intent=[]

    def reset_goal(self):

        self.goal=None
        self.goal_name=None
        self.goal_over=False

        self.all_tasks=[]

        self.task=None
        self.task_level=None
        self.task_name=None
        self.task_fail=False
        self.task_over=False

        self.plan=[]
        self.trial_n=0

    def reset_task(self):

        self.task=None
        self.task_level=None
        self.task_name=None
        self.task_fail=False
        self.task_over=False

        self.plan=[]
        self.trial_n=0

    def reset_gestures(self):
        self.pointing = None
        self.waving = None
        self.nodding = False
        self.shaking = False
        self.playing = None
        self.performing = None
        self.eating = None
        self.speaking = None

    def reachable_check(self, entity, W, offset=5):
        true_entity = entity
        if hasattr(entity, 'being_contained') and len(entity.being_contained) > 0:
            # true_entity = get_entity_in_whose_mind(entity.being_contained[0], W, self.id)
            true_entity = W.retrieve_by_id(entity.being_contained[0])
        if hasattr(entity, 'being_held_id') and len(entity.being_held_id) > 0:
            # true_entity = get_entity_in_whose_mind(entity.being_held_id[0], W, self.id)
            true_entity = W.retrieve_by_id(entity.being_held_id[0])
        return Is_Near(self, true_entity, W, offset)

    # return different code
    # for attention check fail: return -1
    # for obstacle check fail: return -2
    # only 1: means pass check, will not return 0
    def attention_check(self, target, W, Att_R=None):
        if not _attention_check(self, target, Att_R):
            return -1
        else:
            if _no_obstacle_check(self, target, W):
                return True
            else:
                return -2
        # return _no_obstacle_check(self, target, W)

    def belief_id_check(self, entity):
        for _entity in  self.belief.get_all_entities():
            if entity.id == _entity.id:
                return True
        return False

    def observe(self, W, verbose=True):
        observation = []
        obs_ids = []
        for entity in W.entities:
            if self.id != entity.id:
                if self.attention_check(entity, W) == 1 or entity.id in self.holding_ids:
                    if verbose:
                        print("{%s} see {%s}!" % (self.name, entity.name))
                    observation.append(entity.get_observation(W))
                    obs_ids.append(entity.id)
                elif isinstance(entity, Agent) and entity.speaking is not None:
                    if len(entity.action_history) >= 0 and entity.action_history[-1][0] == 'ActionSpeak':
                        if verbose:
                            print("{%s} see {%s}!" % (self.name, entity.name))
                        observation.append(entity.get_verbal_observation(W, self))
                        obs_ids.append(entity.id)
        # expand observation scope, if you can see the obj you can also see who holds it, vice versa
        for obs in observation:
            if isinstance(obs, Object):
                for being_held_id in obs.being_held_id:
                    if being_held_id not in obs_ids and self.id != being_held_id:
                        observation.append(W.retrieve_by_id(being_held_id).get_observation(W))
            if isinstance(obs, Agent):
                for held_id in obs.holding_ids:
                    if held_id not in obs_ids:
                        observation.append(W.retrieve_by_id(held_id).get_observation(W))
        self.observation = observation

    def observe_and_update_belief(self, W, verbose=True):
        self.observe(W, verbose=verbose)
        self.update_belief(W)

    # others get observation
    def get_observation(self, W):
        # if self.be_observed_time != W.time:
        #     del self.be_observation
        _agent = Agent()
        # agent_attr_obs_dcopy(self, self, _agent, W)
        agent_attr_obs_dcopy(self, _agent)
        self.be_observed_time = W.time
        _agent.be_observed_time = W.time

        return _agent

    def get_verbal_observation(self, W, obs_agent):
        _agent = Agent()
        # agent_attr_obs_dcopy(self, self, _agent, W)
        agent_attr_obs_dcopy(self, _agent)

        _agent.id = deepcopy(self.id)
        _agent.name = deepcopy(self.name)
        _agent.position = deepcopy(self.position)
        _agent.attention = deepcopy(compute_rotate(self.position, obs_agent.position))
        _agent.rotate = deepcopy(compute_rotate(self.position, obs_agent.position))
        # _agent.holding_ids = deepcopy(agent.holding_ids)
        # _agent.desire = deepcopy(agent.desire)
        # _agent.pointing = deepcopy(agent.pointing)
        # _agent.lifting = deepcopy(agent.lifting)
        # _agent.waving = deepcopy(agent.waving)
        # _agent.hitting = deepcopy(agent.hitting)
        # _agent.speaking = deepcopy(agent.speaking)
        # _agent.nodding = deepcopy(agent.nodding)
        # _agent.shaking = deepcopy(agent.shaking)
        # _agent.playing = deepcopy(agent.playing)
        # _agent.hands_occupied = deepcopy(agent.hands_occupied)

        self.be_observed_time = W.time

        return _agent

    # @profile
    def update_belief(self, W):
        self.belief.update(self.observation, self.attention_check, self, W)

    def has_intent(self, I, cate):

        if self.intent_now is not None and same_intent(self.intent_now, I):
            return True

        if len(self.intents[cate]) == 0:
            return False

        for tmp in self.intents[cate]:
            if same_intent(I, tmp):
                return True

        return False

    def already_has_intent(self, I):
        if self.intent_now is not None and same_intent(self.intent_now, I):
            return True
        for cate in INTENTS_PRIORITY_LIST:
            if len(self.intents[cate]) == 0:
                continue
            for tmp in self.intents[cate]:
                if same_intent(I, tmp):
                    return True
        return False

    def update_estimation_of_agent(self, new_help_int, ins_cate):
        for cate in INTENTS_PRIORITY_LIST:
            if len(self.intents[cate]) == 0:
                if cate == ins_cate:
                    self.intents[ins_cate].append(new_help_int)
                    return
                else:
                    continue
            for i, tmp in enumerate(self.intents[cate]):
                if estimation_of_same_agent(tmp, new_help_int):
                    self.intents[cate][i] = new_help_int
                    return
        self.intents[ins_cate].append(new_help_int)

    # judge the intent I whether has been finished already
    # todo: has finished intent这里可能会有问题, 无法处理两次相同的intent
    def has_finished_intent(self, I):
        if len(self.finished_intent) == 0:
            return False
        for tmp in self.finished_intent:
            if same_intent(I, tmp):
                return True
        return False

    def is_in_contact(self, target, W):
        if not isinstance(target, Entity):
            return False
        real_target = target
        if hasattr(target, 'being_contained') and len(target.being_contained) > 0:
            real_target = W.retrieve_by_id(target.being_contained[0])
        if hasattr(target, 'being_held_id') and len(target.being_held_id) > 0:
            real_target = W.retrieve_by_id(target.being_held_id[0])
        dist = euclidean_dist(self.position, real_target.position)
        if isinstance(real_target, Agent):
            # 5 means a distance tolerance
            if dist > (real_target.size + self.size + 20):
                return False
        else:
            w, h = real_target.size
            # 5 means a distance tolerance
            if dist > (np.sqrt((w/2)**2 + (h/2)**2) + self.size + 20):
                return False
        return True

    def is_holding(self, target):
        for obj_id in self.holding_ids:
            if obj_id == target.id:
                return True
        return False
    
    def pick_up(self, target, W):
        self.holding_ids.append(target.id)
        if len(target.being_held_id) > 0:
            for being_held_id in target.being_held_id:
                being_held_entity = W.retrieve_by_id(being_held_id)
                if isinstance(being_held_entity, Agent):
                    assert target.id in being_held_entity.holding_ids
                    being_held_entity.holding_ids.remove(
                        target.id)
                if isinstance(being_held_entity, Object):
                    assert target.id in being_held_entity.containing
                    being_held_entity.containing.remove(target.id)
        target.being_held_id = [self.id]
        target.update_being_held_entity(W)
        target.position = agent_left_upper_with_offset(self, target)
        target.rotate = self.rotate
        target.attention = self.attention

    def put_down(self, target):
        if target.id in self.holding_ids:
            self.holding_ids.remove(target.id)
        target.rotate = 0.5
        if self.hands_occupied and len(self.holding_ids) == 0:
            self.hands_occupied = False
        if self.id in target.being_held_id:
            target.being_held_id.remove(self.id)

    def phy_encoding(self):
        """
        [
        [id] - id (0)
        [x, y] - position (1,2)
        [x_p, y_p] - relative position (3,4)
        [r] - attention (5)
        {0,1} - holding (6)
        ]
        :return:  a vector of length 7
        """
        agent_phy_encoding=[]
        agent_phy_encoding.append(self.id)
        agent_phy_encoding.extend(self.position)
        agent_phy_encoding.extend([round(self.position[0]/WORLD_WIDTH, 3), round(self.position[1]/WORLD_HEIGHT, 3)])
        agent_phy_encoding.append(self.attention)
        agent_phy_encoding.append(1 if len(self.holding_ids)>0 else 0)

        return agent_phy_encoding


def compute_rotate(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    if x1 == x2:
        if y1 < y2:
            return 0.5
        else:
            return -0.5
    else:
        theta = math.atan((y2 - y1)/(x2 - x1))
        # return theta / math.pi
        if (x2 - x1) > 0:
            return theta / math.pi
        else:
            if theta < 0:
                return (theta / math.pi) + 1
            else:
                return (theta / math.pi) - 1

from .action import *
# from .check_fn import *
from .belief import *
