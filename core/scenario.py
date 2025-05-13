import random

from core.intent import *
from core.entity import *
from core.world import *
from core.const import ENTITY_SIZE_CONFIG
from core.agent import *
import numpy as np
import pickle
import os


class Scenario:
    def __init__(self, config_file=None, AGENTS=None, OBJS=None, LANDMARKS=None, control_test=False):

        if config_file is not None:
            with open(config_file, 'rb') as f:
                AGENTS, OBJS, LANDMARKS = pickle.load(f)
        self.scenario_name = os.path.split(os.path.split(config_file)[0])[1] if config_file is not None else 'random'
        self.agents = AGENTS
        self.objects = OBJS
        self.landmarks = LANDMARKS
        self.control_test = control_test
        self.desire_pair = None

        # all the entries is fluent/mutable
        self.goal_state = []
        # goal_mask to guarantee the same length of states of all scenarios
        # also conditioned on scenario
        self.goal_mask = []

    def make_world(self, init_shuffle=False, mode=None, scenario_name=None, show=False):
        W = World(mode, scenario_name, show, know_other_values=self.control_test)
        self.make_agent(W, init_shuffle)
        self.make_object(W)
        self.make_landmark(W)

        for o in W.objects:
            o.update_being_held_entity(W)

        for i, A in enumerate(W.agents):
            if isinstance(self.agents[i], Agent):
                continue
            if 'belief_obj_ids' in self.agents[i]:
                for obj_id in self.agents[i]['belief_obj_ids']:
                    cpy = deepcopy(W.retrieve_by_id(obj_id))
                    # 0808, initial belief
                    if cpy is None:
                        # fixme
                        print(f'!!!{scenario_name}, obj_id: {obj_id} is None, agent_id: {A.id}, belief_obj_ids: {self.agents[i]["belief_obj_ids"]}')
                        continue
                    cpy.be_observed_time = -1
                    A.belief.add_object(cpy)

            if 'belief_agent_ids' in self.agents[i]:
                for agent_id in self.agents[i]['belief_agent_ids']:
                    cpy = deepcopy(W.retrieve_by_id(agent_id))
                    # 0808, initial belief
                    cpy.be_observed_time = -1
                    A.belief.add_agent(cpy)

        # scenario conditioned construct goal state
        # agent*3, 4*3=12
        # agent: pos_x, pos_y, attention, is_holding, waving, pointing;
        # object*8
        # object: pos_x, pos_y, is_held, is_played, is_in, in, is_on, on;
        if 'classroom' in self.scenario_name:
            attention_list = [-0.7222, 0.25, 0.5]
            # 1. agents
            # pos_x, pos_y, attention, is_holding, waving, pointing;
            for i in range(3):
                agent = W.retrieve_by_id(i+1)
                self.goal_state.extend([agent.position[0], agent.position[1], attention_list[i], 0, 0, 0])

            # 2. objects: clock, box, cup, chess, table
            # pos_x, pos_y, is_held, is_played, is_in, in, is_on, on;
            clock = W.retrieve_by_id(4)
            self.goal_state.extend([clock.position[0], clock.position[1], 0, 0, 0, 0, 0, 0])

            # 3. does not need to maintain the landmark ??

            # goal_mask, only mask the clock
            self.goal_mask = ([1]*4 + [0]*2) * 3 + [0] * 8

        elif 'cuptotable' in self.scenario_name:

            # 6*3
            attention_list = [0.5, 0]
            for i in range(2):
                agent = W.retrieve_by_id(i+1)
                self.goal_state.extend([agent.position[0], agent.position[1], attention_list[i], 0, 0, 0])

            # padding
            self.goal_state.extend([0]*6)

            table = W.retrieve_by_id(3)
            cup = W.retrieve_by_id(4)
            chess = W.retrieve_by_id(5)
            banana = W.retrieve_by_id(6)
            box = W.retrieve_by_id(7)

            # clock
            self.goal_state.extend([0]*8)
            # cup
            self.goal_state.extend([table.position[0], table.position[1] + table.size[1]/3 + cup.size[1]/2,
                                    0, 0, 0, 0, 1, 0])
            # table
            self.goal_state.extend([table.position[0], table.position[1],
                                    0, 0, 0, 0, 0, 1])

            self.goal_mask = ([1]*4 + [0]*2)*2 + [0]*6
            self.goal_mask += [0]*8 + ([1]*2 + [0]*4 + [1]*2)*2

        return W

    def diff_to_goal_state(self, current_state):
        # element-wise multiplication
        return np.asarray(current_state) - np.asarray(self.goal_mask) * np.asarray(self.goal_state)

    def make_landmark(self, W):
        LANDMARKS = self.landmarks
        if LANDMARKS is None:
            return
        if len(LANDMARKS) > 0 and isinstance(LANDMARKS[0], Landmark):
            W.landmarks = LANDMARKS
        else:
            W.landmarks = [Landmark() for _ in range(len(LANDMARKS))]
        for i, lmk in enumerate(W.landmarks):
            if isinstance(LANDMARKS[i], Landmark):
                continue
            lmk.id = LANDMARKS[i]["id"]
            lmk.name = LANDMARKS[i]["name"]
            # lmk.color = np.array(LANDMARKS[i]['color'])
            lmk.size = np.array(LANDMARKS[i]['size'], dtype=int)
            lmk.rotate = LANDMARKS[i]['rotate']
            lmk.position = np.array(LANDMARKS[i]['pos'], dtype=np.float64)

    def make_agent(self, W, init_shuffle=False):
        AGENTS = self.agents
        if isinstance(AGENTS[0], Agent):
            W.agents = AGENTS
        else:
            W.agents = [Agent() for _ in range(len(AGENTS))]
        for i, A in enumerate(W.agents):
            if isinstance(AGENTS[i], Agent):
                continue
            A.id = AGENTS[i]["id"]
            A.name = AGENTS[i]["name"]
            A.name = A.name.replace(' ', '_')

            if not init_shuffle:
                A.position = np.array(AGENTS[i]['pos'], dtype=np.float64)
                A.attention = AGENTS[i]['attention']
                if "rotate" in AGENTS[i]:
                    A.rotate = AGENTS[i]['rotate']
            else:
                A.position = np.asarray([random.randint(-WORLD_WIDTH, WORLD_HEIGHT),
                                         random.randint(-WORLD_WIDTH, WORLD_HEIGHT)])
                A.rotate = random.random() * 2 - 1
                A.attention = A.rotate

            if 'holding_ids' in AGENTS[i]:
                A.holding_ids = AGENTS[i]['holding_ids']
                # A.update_holding_others(W)
            if 'hands_occupied' in AGENTS[i]:
                A.hands_occupied = AGENTS[i]['hands_occupied']

            if 'desire' in AGENTS[i]:
                A.desire = Desire(active=AGENTS[i]['desire']['active'],
                                  social=AGENTS[i]['desire']['social'],
                                  helpful=AGENTS[i]['desire']['helpful'])

            if 'intent' in AGENTS[i]:
                if isinstance(AGENTS[i]['intent'], dict):
                    if 'intent_pred' in AGENTS[i]['intent']:
                        intent_tmp = Intent(
                            intent_pred=AGENTS[i]['intent']['intent_pred'])
                    else:
                        intent_tmp = Intent()

                    intent_tmp.ind_intent = AGENTS[i]['intent']['ind']

                    intent_tmp.soc_intent = AGENTS[i]['intent']['soc']

                    # only for online game
                    A.initial_intent = deepcopy(intent_tmp)

                    # print(f'initial intent of {A.name}_{A.id}:', intent_tmp)
                    # todo, 0325
                    self.initial_intent_socialize(A, intent_tmp)

                    intent_tmp.comm_intent = AGENTS[i]['intent']['comm']
                    intent_tmp.ref_intent = AGENTS[i]['intent']['ref']

                    A.intent_related_ids.extend(intent_tmp.intent_related_ids())
                    A.intents[AGENTS[i]['intent']['type']].append(intent_tmp)
                    A.intent_related_ids = list(set(A.intent_related_ids))

                elif isinstance(AGENTS[i]['intent'], list):
                    for j, intent in enumerate(AGENTS[i]['intent']):
                        intent_tmp = Intent()

                        intent_tmp.ind_intent = intent['ind']
                        intent_tmp.soc_intent = intent['soc']
                        intent_tmp.comm_intent = intent['comm']
                        intent_tmp.ref_intent = intent['ref']
                        # todo, socialize
                        A.intent_related_ids.extend(intent_tmp.intent_related_ids())

                        A.intents[intent['type']].append(intent_tmp)
                    A.intent_related_ids = list(set(A.intent_related_ids))

        self.desire_pair = {
            f'agent_{1}': W.retrieve_by_id(1).desire(),
            f'agent_{2}': W.retrieve_by_id(2).desire()
        }

    def initial_intent_socialize(self, A, intent_tmp):
        if intent_tmp.ind_intent is None:
            return intent_tmp

        if A.desire.social >= 0.8 and A.desire.active <= 0.2:
            # ind => social
            ind = Intent()
            ind.ind_intent = intent_tmp.ind_intent
            if ind.ind_intent[0] != 'play':
                intent_tmp.soc_intent = ['request_help', 3 - A.id, ind]
            else:
                intent_tmp.soc_intent = ['play_with', 3 - A.id, ind.ind_intent[1]]
            return

        elif A.desire.social <= 0.2 and A.desire.active >= 0:
            # ind (same)
            return

        elif (A.desire.social >= 0.8 and A.desire.active >= 0.8) or (A.desire.social <= 0.2 and A.desire.active <= 0.2):
            if random.random() < 0.5 and intent_tmp.ind_intent != ['explore']:
                # 50% ind => social
                # 50% ind(same)
                ind = Intent()
                ind.ind_intent = intent_tmp.ind_intent

                if ind.ind_intent[0] != 'play':
                    intent_tmp.soc_intent = ['request_help', 3 - A.id, ind]
                else:
                    intent_tmp.soc_intent = ['play_with', 3 - A.id, ind.ind_intent[1]]
                return

    def make_object(self, W):
        OBJS = self.objects
        if isinstance(OBJS[0], Object):
            W.objects = OBJS
        else:
            W.objects = [Object() for _ in range(len(OBJS))]

        for i, obj in enumerate(W.objects):
            if isinstance(OBJS[i], Object):
                continue
            obj.id = OBJS[i]["id"]
            obj.name = OBJS[i]["name"]
            obj.position = np.array(OBJS[i]['pos'], dtype=np.float64) if 'pos' in OBJS[i] else np.array([0, 0])
            # obj.size = np.array(OBJS[i]['size'], dtype=int)
            obj.size = np.asarray(ENTITY_SIZE_CONFIG[obj.name])
            if "rotate" in OBJS[i]:
                obj.rotate = OBJS[i]["rotate"]

            for agent in W.agents:
                if obj.id in agent.holding_ids:
                    obj.position = agent.position
                    break

            if 'is_container' in OBJS[i]:
                obj.is_container = OBJS[i]['is_container']

            if 'is_supporter' in OBJS[i]:
                obj.is_supporter = OBJS[i]['is_supporter']

            if 'supporting_ids' in OBJS[i]:
                obj.supporting_ids = OBJS[i]['supporting_ids']

            if 'open' in OBJS[i]:
                obj.open = OBJS[i]['open']

            if 'containing' in OBJS[i]:
                obj.containing = OBJS[i]['containing']

            if 'is_game' in OBJS[i]:
                obj.is_game = OBJS[i]['is_game']

            if 'is_salient' in OBJS[i]:
                obj.is_salient = OBJS[i]['is_salient']

            if 'locked' in OBJS[i]:
                obj.locked = OBJS[i]['locked']
                if obj.locked:
                    obj.needs_key = True

            if 'is_key' in OBJS[i]:
                obj.is_key = OBJS[i]['is_key']

            if 'being_contained' in OBJS[i]:
                obj.being_contained = OBJS[i]['being_contained']
                obj.update_being_held_entity(W)

            if 'is_multiplayer_game' in OBJS[i]:
                obj.is_multiplayer_game = OBJS[i]['is_multiplayer_game']

            if 'being_held_id' in OBJS[i]:
                obj.being_held_id = OBJS[i]['being_held_id']
                obj.update_being_held_entity(W)
                obj.position = agent_left_upper_with_offset(W.retrieve_by_id(obj.being_held_id[0]), obj)

        for i, obj in enumerate(W.objects):
            if hasattr(obj, 'being_contained') and len(obj.being_contained) > 0:
                being_contained_id = obj.being_contained[0]
                contained_entity = W.retrieve_by_id(being_contained_id)
                if 'shelf' in contained_entity.name:
                    obj.position = rel_pos_in_shelf(contained_entity, obj)

    def reset_world(self, world):
        self.cnt = 1
        self.make_agent(world)
        self.make_object(world)
        self.make_landmark(world)
