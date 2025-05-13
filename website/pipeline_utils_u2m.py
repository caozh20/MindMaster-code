import numpy as np
import random
from copy import deepcopy
import pygame
import time
from collections import defaultdict
from enum import Enum
from core.scenario import Scenario
import os.path as osp
from core.inverse_infer_belief import inverse_infer_belief
from core.inverse_infer_intent import inverse_infer_intent
from core.inverse_infer_desire import inverse_infer_desire
from core.update_intent import propose_intents, update_intent
from core.plan import update_goal, update_task, act
from core.scenario_finish_check import scenario_finish_check
from core.action import *
from core.intent import *
from core.const import INTENTS_PRIORITY_LIST
from core.entity_utils import Is_Near
from globals import increment_task_id
from utils.base import log
from scenarios.generating.intent_pool import Scenario_Generating
from .pipeline_common import generate_start_action_option_dict, get_ind_intent_desc
from .pipeline_common import FinishStatus, MAX_ITERATIONS


class UserState:
    # fixme, 出于兼容性考虑，有些场景下会用到这个场景参数，比如 ActionExplore 等；
    class ScenarioArgs:
        def __init__(self, scenario):
            self.scenario = scenario

    def __init__(self):
        self.all_scenarios = [
            'chimpanzee',
            'container',
            'cuptotable',
            'multipointing',
            'play_game',
            'baby',
            # 'classroom',
            # 与 `baby` 场景重叠
            # 'helping',
            # 'sally_anne',
            # 'refer_disambiguation'
        ]
        self.scenario_name = random.choice(self.all_scenarios)
        print(self.scenario_name, 'has been chosen!!')
        # pygame.quit()
        self.verbose = False
        self.shuffle = False
        self.save = False
        self.savedir = './save/'
        self.batch = False
        self.seed = 1234
        self.showrect = False
        # self.Scenario_generator = Scenario_Generating()
        # self.scenario_name = self.Scenario_generator.intent_name
        # self.scenario = Scenario(AGENTS=self.Scenario_generator.agents, OBJS=self.Scenario_generator.objects,
        #                          LANDMARKS=self.Scenario_generator.landmarks)
        self.scenario = Scenario(osp.join("./scenarios/{}".format(self.scenario_name), self.scenario_name + ".pkl"))
        self.scenario_args = self.ScenarioArgs(self.scenario_name)
        self.world = self.scenario.make_world(self.shuffle)
        self.label_who = self._label_who()

        self.finish_check = scenario_finish_check(self.world, self.scenario_name)
        self.client_agent = self.world.retrieve_by_id(random.choice([agent.id for agent in self.world.agents]))
        self.world.preprocessing(self.client_agent)

        self.show_whose_belief = self.client_agent.id

        # 任务相关
        self.task_id = increment_task_id()
        self.frames = []
        self.temp_agent_pos_att = []
        self.frame_index = 0
        self.iterations = 0
        self.done = FinishStatus.DOING

        # god's perspective
        # self.world.render_init()
        # have finished task
        self.finished_tasks = 0

        # 初始化action_option_dict
        # 一些一定会被删除的会被在初始化时就删去
        self.start_action_option_dict = generate_start_action_option_dict(self.world.agents, self.world.objects)

        # 控制数据发送的变量
        self.CAN_SEND_FRAME = True
        self.LAST_RESPONSE_TIME = time.time()
        self.SENDING = True

    def reset(self):
        self.scenario_name = random.choice(self.all_scenarios)

        # self.Scenario_generator = Scenario_Generating()
        # self.scenario_name = self.Scenario_generator.intent_name
        # self.scenario = Scenario(AGENTS=self.Scenario_generator.agents, OBJS=self.Scenario_generator.objects,
        #                          LANDMARKS=self.Scenario_generator.landmarks)
        self.scenario = Scenario(osp.join("./scenarios/{}".format(self.scenario_name), self.scenario_name + ".pkl"))
        self.scenario_args = self.ScenarioArgs(self.scenario_name)
        # pygame.quit()
        self.world = self.scenario.make_world(self.shuffle)
        self.label_who = self._label_who()
        self.finish_check = scenario_finish_check(self.world, self.scenario_name)

        # todo,  是否需要 shuffle
        # self.client_agent = self.world.retrieve_by_id(self.client_agent.id)
        self.client_agent = self.world.retrieve_by_id(random.choice([agent.id for agent in self.world.agents]))
        self.world.preprocessing(self.client_agent)

        self.start_action_option_dict = generate_start_action_option_dict(self.world.agents, self.world.objects)

        # 任务相关
        self.task_id = increment_task_id()
        self.frames = []
        self.done = FinishStatus.DOING
        self.frame_index = 0
        self.iterations = 0

    def _label_who(self):
        # 三人场景
        if len(self.world.agents) >= 3:
            # 从 others 中二选一
            return random.randint(0, 1)
        return 0


def init_scenario(args):
    for agent in args.world.agents:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass
        agent_pipeline(agent, args)
    frames, _ = args.world.render_belief(args.client_agent, iter=args.iterations, show_rect=args.showrect)
    args.frames.extend(frames)


def agent_pipeline(agent, args):
    # fixme, very time-consuming operation in later rounds, to be optimized
    agent.observe(args.world, verbose=False)
    agent.update_belief(args.world)
    agent.observation = []
    log.info(
        "agent {} belief, [agent_ids {}], [object_ids {}], [landmark_ids {}]"
        .format(agent.name,
                agent.belief.agent_ids,
                agent.belief.object_ids,
                agent.belief.landmark_ids)
    )
    if agent.id != args.client_agent.id:
        # update the false belief to None
        # update the belief of the entities being held when moving
        # agent.update_desire()
        inverse_infer_belief(agent, args.world)
        inverse_infer_intent(agent, args.world, args.scenario_args)
        inverse_infer_desire(agent)
        propose_intents(agent, args.world)
        update_intent(agent, args.world)
        update_goal(agent, args.world)
        log.info('agent {} goal [{}]'.format(agent.name, agent.goal_name))
        update_task(agent, args.world, args.scenario_args)
        log.info('agent {} task [{}]'.format(agent.name, agent.task_name))


def main_protocol_interact(args, user_action):
    for agent in args.world.agents:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass
        if agent.id == args.client_agent.id:
            if agent.pointing is not None and user_action.name()[0] != 'ActionPointTo':
                agent.pointing = None
            if agent.waving is not None and user_action.name()[0] != 'ActionWaveHand':
                agent.waving = None
            if agent.nodding and user_action.name()[0] != 'ActionNodHead':
                agent.nodding = False
            if agent.nodding and user_action.name()[0] != 'ActionShakeHead':
                agent.shaking = False
            if agent.hitting and user_action.name()[0] != 'ActionHit':
                agent.hitting = None

        actions = []
        if agent.id != args.client_agent.id:
            agent_pipeline(agent, args)
            server_action = act(agent, args.world, args, agent.id)
            action = server_action
        else:
            action = user_action
        actions.append(action)
        log.info('iterations: {}, agent: {}, action: {}'.format(
            args.iterations, agent.name, action.name() if action is not None else "None"))
        args.world.step(actions)

        if action is not None:
            name = action.name()
            name.append(not agent.action_fail)
            agent.action_history.append(name)

        args.client_agent.observe(args.world, verbose=False)
        args.client_agent.update_belief(args.world)

        # render after every action rather than every iteration
        if args.show_whose_belief is not None:
            frames, _ = args.world.render_belief(args.client_agent, iter=args.iterations, show_rect=args.showrect)
            args.frames.extend(frames)
        else:
            args.frames.extend(args.world.render(mode='rgb_array', iter=args.iterations, show_rect=args.showrect))
    args.iterations += 1

    if args.finish_check(args.world, args.scenario_name):
        return FinishStatus.SUCCESS
    if args.iterations >= MAX_ITERATIONS:
        return FinishStatus.REACH_MAX_ITER
    return FinishStatus.DOING


def get_world_id_names_dict(args):
    id_name_dict = dict()
    for agent in args.world.agents:
        id_name_dict[str(agent.id)] = agent.name
        id_name_dict[agent.name] = str(agent.id)
    for obj in args.world.objects:
        id_name_dict[str(obj.id)] = obj.name
        id_name_dict[obj.name] = str(obj.id)
    for ldm in args.world.landmarks:
        id_name_dict[str(ldm.id)] = ldm.name
        id_name_dict[ldm.name] = str(ldm.id)
    return id_name_dict


def get_belief_agent_list(args):
    client_agent = args.client_agent
    belief_agent_list = []
    for agent in client_agent.belief.agents:
        if agent.id == client_agent.id:
            continue
        belief_agent_list.append([agent.id, agent.name])
    belief_agent_list = sorted(belief_agent_list, key=lambda x: x[0])
    if args.label_who == 1:
        # 意味着是 classroom 场景，而2个others中二选一
        if len(belief_agent_list) == 1:
            # 可以不标
            return []
        # 仅标第二个
        return [belief_agent_list[1]]
    return belief_agent_list


def calc_agents_rel_pos(args):
    agent_rel_pos_dict = defaultdict(list)
    offset = 90
    for agent in args.client_agent.belief.agents:
        x, y = agent.position
        x += 700
        y = 700 - y

        def decide_best_rel_pos(x, y):
            # 考虑边框
            r_x = (x+offset)/1400
            r_x_2 = r_x
            r_y = y/1400
            if (r_x + 0.4) > 1:
                r_x = (x-offset)/1400 - 0.4
                r_x_2 = (x-offset)/1400 - 0.191
            if (r_y + 0.1373) > 1:
                r_y = 1-0.14
            return r_x, r_y, r_x_2

        r_x, r_y, r_x_2 = decide_best_rel_pos(x, y)
        # 需判断在 agent 的 left side 还是 right side
        # [intent_x, intent/action_y, action_x]
        agent_rel_pos_dict[agent.name] = ['{0:.2%}'.format(r_x), '{0:.2%}'.format(r_y), '{0:.2%}'.format(r_x_2)]
    return agent_rel_pos_dict



