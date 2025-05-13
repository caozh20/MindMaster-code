import numpy as np
import random
from copy import deepcopy
import pygame
import time
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from core.scenario import Scenario
from core.desire import Desire
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
from utils.base import log
from utils.metrics import *
from globals import increment_task_id, global_scenario_record
from scenarios.generating.intent_pool import Scenario_Generating
from scenarios.scenario_generating.intent_pool import Scenario_Generating_Random
from .pipeline_common import generate_start_action_option_dict, get_ind_intent_desc
from .pipeline_common import FinishStatus, MAX_ITERATIONS, PlayingStatus, USER_FILE_PATH

WARM_UP_MAX_ITERACTION = 4

# dict, key: uuid, value: assigned room
class GlobalRoomDict(dict):
    def __init__(self, arg=None):
        # 基于创建顺序，list of ScenarioRoom instances
        if arg:
            self.control_test = arg.control_test_mode
        else:
            self.control_test = False
        self.room_list: list[ScenarioRoom] = []
        self.offline_experiment = False

        self.prior_exp_path = arg.prior_exp_path

        if self.prior_exp_path is not None:
            # 读取可能的预设列表
            with open(arg.prior_exp_path, 'r') as f:
                self.prior_exp_data = json.load(f)

        if arg and arg.offline_experiment is True:
            self.offline_experiment = True
            self._create_offline_room()

    def _needs_new_room(self):
        if len(self.room_list) == 0:
            # needs
            return True
        for room in self.room_list:
            # if not room.room_ready():
            #     # 存在未满的房间
            #     return False
            if room.get_room_status() == 'available':
                # 存在空闲房间
                return False
        # needs
        return True

    def check_room_available(self, room_id):
        for room in self.room_list:
            if room.room_id == room_id:
                if room.get_user_num() >= 2:
                    return False
                else:
                    return room
        return False

    # 分配房间
    def assign_room(self, user_uuid, user_email, room_id=None, create_new_room=False):
        # is_pro = user_email in self.whitelist
        if self._needs_new_room() or (create_new_room is True):
            print(f'[assign new room] {datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, '
                  f'user_uuid: {user_uuid}, user_email: {user_email}')
            new_room = self.create_scenario_room(control_test=self.control_test, user_email=user_email)
            user_agent = new_room.get_client_user(user_uuid)
            self.room_list.append(new_room)
            self.__dict__[user_uuid] = new_room
            
            return new_room, user_agent
        else:
            # 如果不指定房间，则加入随即房间
            if room_id is None:
                print(f'[assign old room] {datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'user_uuid: {user_uuid}, user_email: {user_email}')
                # todo 0918, 应当是空闲房间，未必是最后一个房间
                user_agent = self.room_list[-1].get_client_user(user_uuid)
                self.__dict__[user_uuid] = self.room_list[-1]
                
                if self.room_list[-1].scenario_name in self.room_list[-1].all_scenarios:    
                    if user_email not in global_scenario_record:
                        global_scenario_record[user_email] = [self.room_list[-1].scenario_name]
                    else:
                        global_scenario_record[user_email].append(self.room_list[-1].scenario_name)
                
                print(f'scenario record dict:{global_scenario_record}')
                
                return self.room_list[-1], user_agent
            else: 
                # 加入指定的房间
                # 先检查房间是否可用
                room = self.check_room_available(room_id=room_id)
                if room is False:
                    return False, None
                print(f'[assign old room] {datetime.now().strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'user_uuid: {user_uuid}, user_email: {user_email}')
                # todo 0918, 应当是空闲房间，未必是最后一个房间
                user_agent = room.get_client_user(user_uuid)
                self.__dict__[user_uuid] = room
                
                if room.scenario_name in room.all_scenarios:    
                    if user_email not in global_scenario_record:
                        global_scenario_record[user_email] = [room.scenario_name]
                    else:
                        global_scenario_record[user_email].append(room.scenario_name)
                
                print(f'scenario record dict:{global_scenario_record}')
                
                return room, user_agent
    
    # 当前房间数
    def num_rooms(self):
        return len(self.room_list)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __contains__(self, item):
        return item in self.__dict__
    
    def items(self):
        return [(uuid, room) for uuid, room in self.__dict__.items() 
                if isinstance(room, ScenarioRoom)]

    def check_id_usable(self, room_id):
        for room in self.room_list:
            if room.room_id == room_id:
                return False
        return True

    def retrive_zero_data(self):
        # 获取第一个值为0的三元组
        # 为了让用户避免反复扮演一种agent，在第一次sample时随机化
        # 避免反复sample，当count到10时开始遍历
        count = 0
        keys = list(self.prior_exp_data.keys())
        while True:
            selected_key = keys[random.randint(0, len(keys) - 1)]
            for value2 in self.prior_exp_data[selected_key]:
                for intent in self.prior_exp_data[selected_key][value2]:
                    if self.prior_exp_data[selected_key][value2][intent] == 0:
                        # 找到第一个值为0的三元组后立即更新
                        self.prior_exp_data[selected_key][value2][intent] = 1
                        
                        # 保存更新后的json文件
                        with open(self.prior_exp_path, 'w') as f:
                            json.dump(self.prior_exp_data, f, indent=4)
                        
                        # 返回找到的三元组
                        return [selected_key, value2, intent]
            # 到这里就是没有找到，重新生成selected_key
            count += 1
            if count >= 10:
                break
                        
        # 实在找不到就遍历
        for value1 in self.prior_exp_data:
            for value2 in self.prior_exp_data[value1]:
                for intent in self.prior_exp_data[value1][value2]:
                    if self.prior_exp_data[value1][value2][intent] == 0:
                        # 找到第一个值为0的三元组后立即更新
                        self.prior_exp_data[value1][value2][intent] = 1
                        
                        # 保存更新后的json文件
                        with open(self.prior_exp_path, 'w') as f:
                            json.dump(self.prior_exp_data, f, indent=4)
                        
                        # 返回找到的三元组
                        return [value1, value2, intent]
        
        # 如果没有找到值为0的三元组，返回None
        return None

    def finish_zero_data(self, keys_list): 
        # 读取json文件
        try: 

            self.prior_exp_data[keys_list[0]][keys_list[1]][keys_list[2]] = 2

            # 保存更新后的json文件
            with open(self.prior_exp_path, 'w') as f:
                json.dump(self.prior_exp_data, f, indent=4)
                            
            return True
        except:
            return False

    # 热身组专属id 70000
    def _create_offline_room(self):
        # 线下实验中，一共有4组实验，取编号为1， 2， 3， 4
        # 随机id 的范围为random.randint(0, 65535)
        for i in range(1, 5):
            random_email = f"{random.randint(0, 65535)}@qq.email"
            new_room = self.create_scenario_room(control_test=self.control_test, room_exp_name=f"实验组{i}_第一轮", user_email=random_email, check_room_id_func=self.check_id_usable)
            new_room.set_name(f"实验组{i}_第一轮")
            self.room_list.append(new_room)
            new_room = self.create_scenario_room(control_test=self.control_test, room_exp_name=f"实验组{i}_第二轮", user_email=random_email, check_room_id_func=self.check_id_usable)
            new_room.set_name(f"实验组{i}_第二轮")
            self.room_list.append(new_room)
            new_room = self.create_scenario_room(control_test=self.control_test, room_exp_name=f"实验组{i}_第三轮", user_email=random_email, check_room_id_func=self.check_id_usable)
            new_room.set_name(f"实验组{i}_第三轮")
            self.room_list.append(new_room)
            new_room = self.create_scenario_room(control_test=self.control_test, room_exp_name=f"实验组{i}_第四轮", user_email=random_email, check_room_id_func=self.check_id_usable)
            new_room.set_name(f"实验组{i}_第四轮")
            self.room_list.append(new_room)
            new_room = self.create_scenario_room(control_test=self.control_test, room_exp_name=f"热身组{i}", max_iteration=WARM_UP_MAX_ITERACTION, user_email=random_email, check_room_id_func=self.check_id_usable, warm_up=True)
            new_room.set_name(f"热身组{i}")
            new_room = self.give_warm_up_room_id(new_room)
            self.room_list.append(new_room)
    
    def create_scenario_room(self, control_test=False, user_email=None, max_iteration=None, room_exp_name=None, check_room_id_func=None, warm_up=False):
        if warm_up is True:
            return ScenarioRoom(control_test=control_test, user_email=user_email, max_iteration=max_iteration, room_exp_name=room_exp_name, check_room_id_func=check_room_id_func)
        if self.prior_exp_path is None:
            return ScenarioRoom(control_test=control_test, user_email=user_email, max_iteration=max_iteration, room_exp_name=room_exp_name, check_room_id_func=check_room_id_func)
        else: 
            # 需要读取房间预设信息
            room_setting = self.retrive_zero_data()
            if room_setting is None:
                return ScenarioRoom(control_test=control_test, user_email=user_email, max_iteration=max_iteration, room_exp_name=room_exp_name, check_room_id_func=check_room_id_func)
            else: 
                # 需要预设双方的value以及intent
                return ScenarioRoom(control_test=control_test, user_email=user_email, max_iteration=max_iteration, room_exp_name=room_exp_name, check_room_id_func=check_room_id_func, initial_value=room_setting[:2], initial_intent=room_setting[2])

    def check_and_recreate_room(self, room_name, user_email=None):
        find_flag = False
        for room in self.room_list:
            if room.room_name == room_name:
                find_flag = True
                break
        if find_flag:
            return
        # 没找到就重新生成
        if "热身" in room_name:
            new_room = self.create_scenario_room(control_test=self.control_test, max_iteration=WARM_UP_MAX_ITERACTION, user_email=user_email, check_room_id_func=self.check_id_usable, warm_up=True)
            new_room = self.give_warm_up_room_id(new_room)
        else:
            new_room = self.create_scenario_room(control_test=self.control_test, user_email=user_email, check_room_id_func=self.check_id_usable)
        new_room.set_name(room_name)
        self.room_list.append(new_room)

    def give_warm_up_room_id(self, room):
        room.room_id = random.randint(70000, 80000)
        while not self.check_id_usable(room.room_id):
            room.room_id = random.randint(70000, 80000)
        return room

    # 警告：这可能会删除正在进行游戏的房间
    def restart_room(self, room_name, user_email):
        for room in self.room_list:
            if room.room_name == room_name:
                self.room_list.remove(room)
        if "热身" in room_name:
            new_room = self.create_scenario_room(control_test=self.control_test, max_iteration=WARM_UP_MAX_ITERACTION, user_email=user_email, check_room_id_func=self.check_id_usable, warm_up=True)
            new_room = self.give_warm_up_room_id(new_room)
        else:
            new_room = self.create_scenario_room(control_test=self.control_test, user_email=user_email, check_room_id_func=self.check_id_usable)
        new_room.set_name(room_name)
        self.room_list.append(new_room)

    def check_and_recreate_offline_room(self, index=None):
        if index is None:
            for i in range(1, 5):
                random_email = f"{random.randint(0, 65535)}@qq.email"
                self.check_and_recreate_room(f"实验组{i}_第一轮", user_email=random_email)
                self.check_and_recreate_room(f"实验组{i}_第二轮", user_email=random_email)
                self.check_and_recreate_room(f"实验组{i}_第三轮", user_email=random_email)
                self.check_and_recreate_room(f"实验组{i}_第四轮", user_email=random_email)
                self.check_and_recreate_room(f"热身组{i}", user_email=random_email)
            return True
        else:
            random_email = f"{random.randint(0, 65535)}@qq.email"
            self.check_and_recreate_room(f"实验组{index}_第一轮", user_email=random_email)
            self.check_and_recreate_room(f"实验组{index}_第二轮", user_email=random_email)
            self.check_and_recreate_room(f"实验组{index}_第三轮", user_email=random_email)
            self.check_and_recreate_room(f"实验组{index}_第四轮", user_email=random_email)
            self.check_and_recreate_room(f"热身组{index}", user_email=random_email)
                    
    def restart_offline_room(self, index):
        random_email = f"{random.randint(0, 65535)}@qq.email"
        self.restart_room(f"实验组{index}_第一轮", user_email=random_email)
        self.restart_room(f"实验组{index}_第二轮", user_email=random_email)
        self.restart_room(f"实验组{index}_第三轮", user_email=random_email)
        self.restart_room(f"实验组{index}_第四轮", user_email=random_email)
        self.restart_room(f"热身组{index}", user_email=random_email)

class ScenarioRoom:
    # fixme, 出于兼容性考虑，有些场景下会用到这个场景参数，比如 ActionExplore 等；
    class ScenarioArgs:
        def __init__(self, scenario):
            self.scenario = scenario

    def __init__(self, control_test=False, user_email=None, max_iteration=None, room_exp_name=None, check_room_id_func=None, initial_value=None, initial_intent=None):
        self.room_id = random.randint(0, 65535)
        if check_room_id_func is not None:
            while not check_room_id_func(self.room_id):
                self.room_id = random.randint(0, 65535)
        self.room_name = f"romm{self.room_id}"
        self.all_scenarios = [
            'chimpanzee',
            'container',
            'cuptotable',
            'multipointing',
            'play_game',
            # 'classroom',
            # 'baby',
            # 与 `baby` 场景重叠
            # 'helping',
            # 'sally_anne',
            # 'refer_disambiguation',
            # 'demo'
        ]
        self.iterations = 0
        self.max_iteration = max_iteration
        
        if initial_intent is not None and 'null' in initial_intent:
            initial_intent = None

        if user_email and user_email not in global_scenario_record:
            global_scenario_record[user_email] = []
        
        rdn_or_not = random.random()

        # rdn_or_not = 1
        self.scenario_name_another = None
        self.control_test = control_test
        
        if self.control_test:
            rdn_or_not = 1
        
        # assert user_email
        
        ll = []
        for _,v in global_scenario_record.items():
            ll += v

        all_played_scenario_fixed =set(ll)
        
        # 存储初始的scenario_name
        # 在游戏进行过程中，可能因为scenario_name的变化导致数据出现误差
        self.scenario_name_to_store = None

        # 0.6 (random scenario) vs. 0.4 (pre-defined scenarios)
        if rdn_or_not < 0.6 or len(all_played_scenario_fixed) == len(self.all_scenarios) or (initial_value is not None or initial_intent is not None):       

            scenario_generator = Scenario_Generating_Random(control_test, room_exp_name, initial_intent=initial_intent, initial_value=initial_value)
            self.scenario = Scenario(AGENTS=scenario_generator.agents, OBJS=scenario_generator.objects,
                                LANDMARKS=None, control_test=self.control_test)
            self.scenario_name = scenario_generator.intent_name
            self.scenario_name_to_store = self.scenario_name
            print(f'scenario {self.scenario_name} has been randomly chosen.')
            self.scenario_name_another = scenario_generator.intent_name_another
            print(f'another intent is {self.scenario_name_another}')
            self.intent_diff = scenario_generator.intent_diff
            print(f'intent pair type:{self.intent_diff}')
        else:
            self.scenario_name = random.choice(self.all_scenarios)                        
            # while self.scenario_name in global_scenario_record[user_email]:
            while self.scenario_name in all_played_scenario_fixed:
                # all_scenarios_no_repeated = [sc for sc in self.all_scenarios if sc not in global_scenario_record[user_email]]
                all_scenarios_no_repeated = [sc for sc in self.all_scenarios if sc not in all_played_scenario_fixed]
                self.scenario_name = random.choice(all_scenarios_no_repeated)
            self.scenario_name_to_store = self.scenario_name
            if user_email is not None:
                global_scenario_record[user_email].append(self.scenario_name)
              
            self.scenario = Scenario(osp.join("./scenarios/{}".format(self.scenario_name), self.scenario_name + ".pkl"))
            self.intent_diff = 0

        self.shuffle = False
        self.world = self.scenario.make_world(self.shuffle)

        self._sample_agents_value(initial_value)
        print(f'{self.scenario_name} has been chosen, {self.scenario_name_another} is another, and room id is {self.room_id}')
        print(f'{self.world.agents[0].name}: {self.world.agents[0].desire()}, {self.world.agents[1].name}: {self.world.agents[1].desire()}')

        self.finish_check = scenario_finish_check(self.world, self.scenario_name)
        if self.scenario_name_another:
            self.finish_check_another = scenario_finish_check(self.world, self.scenario_name_another)
        else:
            self.finish_check_another = None

        self.scenario_name_backup = None
        self.scenario_name_another_backup = None
        
        self.showrect = False

        # key uuid, value agent instance
        self.client_user_dict: dict[str, Agent] = {}

        # indicate current user, only _current_user_uuid can move
        self._active_user_uuid = None

        # indicates normal user or pro (our team members)
        # work only in u2u and enable whitelist
        # self._normal_user_ready = False

        self.start_action_option_dict = generate_start_action_option_dict(self.world.agents, self.world.objects)

        self.CAN_SEND_FRAME = True
        self.LAST_RESPONSE_TIME = time.time()
        self.SENDING = True
        # current play execution stage
        self.done = FinishStatus.DOING
        # fixme
        self.finished_tasks = 0
        
        self.doing_agent = None

        self.finished_users = set()

    def _random_get_agent(self):
        # 已被用户持有的 agents；
        held_agents = [agent.id for _, agent in self.client_user_dict.items()]
        return self.world.retrieve_by_id(random.choice([agent.id for agent in self.world.agents if agent.id not in held_agents]))

    @staticmethod
    def value_str2value(value_str):
        # 去掉括号并分割字符串
        values = value_str.strip('()').split(',')
        # 转换为浮点数
        values = [float(v.strip()) for v in values]
        
        return Desire(active=values[0], social=values[1], helpful=values[2])

    def _sample_agents_value(self, initial_value=None):
        if not self.control_test:
            if initial_value is not None:
                for i, agent in enumerate(self.world.agents):
                    agent.desire = self.value_str2value(initial_value[i])
                    print(f'sampled {agent.name}-{agent.id}"s value: {agent.desire()}')
            else:
                for agent in self.world.agents:
                    agent.desire = self._sample_value_config()
                    print(f'sampled {agent.name}-{agent.id}"s value: {agent.desire()}')
                # if agent.initial_intent is None:
                #     agent.desire = self._sample_value_config(helpful_p=[0.3, 0.1, 0.3, 0.3])
                # else:
                #     agent.desire = self._sample_value_config()
        else:
            for agent in self.world.agents:
                if agent.initial_intent:
                    # with intention
                    # [(inactive, active), social, unhelpful]
                    agent.desire = Desire(active=random.choice([0, 1]),
                                          social=1,
                                          helpful=0)
                else:
                    # without intention
                    # [active, social, helpful]
                    agent.desire = Desire(active=1, social=1, helpful=1)

                print(f'control test, agent: {agent.name}-{agent.id}, '
                      f'intention: {agent.initial_intent.print() if hasattr(agent.initial_intent, "print") else agent.initial_intent}, '
                      f'desire: {agent.desire()}')

    def _sample_value_config(self):
        '''
        采样 value 的配置, 与 initial intent 无关
        :return:
        '''
        active_social_pair = [
            # corner case
            (0, 1),
            (1, 0),
            # equal cases, depends on the human user prior
            (0, 0),
            (1, 1),
        ]
        # [1/3, 1/3, 1/6, 1/6]
        active_social_weights = [2, 2, 1, 1]
        active_social_weights = np.asarray(active_social_weights) / sum(active_social_weights)
        active, social = random.choices(active_social_pair, weights=active_social_weights, k=1)[0]
        helpful = np.random.choice([-1, 0, 1, 2])
        return Desire(active, social, helpful)

    def get_client_user(self, user_uuid):
        # enters into the room and map the agent of world
        if user_uuid not in self.client_user_dict and len(self.client_user_dict) < 2:
            self.client_user_dict[user_uuid] = self._random_get_agent()
        return self.client_user_dict[user_uuid]

    # 获取该 scenario 里 user_uuid 对应的 partner；
    def get_partner(self, user_uuid):
        if not self.room_ready():
            return None
        for uuid, agent in self.client_user_dict.items():
            if uuid != user_uuid:
                return uuid, agent
        return None

    def mark_user_finished(self, user_uuid):
        self.finished_users.add(user_uuid)

    def remove_user_finished(self, user_uuid):
        if user_uuid in self.finished_users:
            self.finished_users.remove(user_uuid)
        
    # todo, 恰当的时机，删除掉这个房间及用户（ClientUserState）
    def all_users_finished(self):
        return len(self.finished_users) == len(self.client_user_dict)

    def get_room_status(self):
        # first the room is existing (and has at least 1 user currently)
        room_status = 'busy' if len(self.client_user_dict) == 2 else 'available'
        if len(self.finished_users) > 0:
            room_status = 'unavailable'
        return room_status

    @property
    def active_user_uuid(self):
        return self._active_user_uuid

    @active_user_uuid.setter
    def active_user_uuid(self, user_uuid):
        self._active_user_uuid = user_uuid

    # free
    def room_ready(self):
        return len(self.client_user_dict) >= 2

    def room_info(self):
        return f'{self.scenario_name}_{self.room_id}'
    
    def cleanup(self, global_user_args):
        for user_uuid, client_agent in self.client_user_dict.items():
            if user_uuid in global_user_args:
                global_user_args[user_uuid].cleanup()
        print(f'Room {self.room_id} is cleaned up.')

    def get_user_num(self):
        return len(self.client_user_dict.keys())
    
    def set_name(self, new_name):
        self.room_name = new_name


class ClientUserState:
    def __init__(self, user_uuid):
        self.user_uuid = user_uuid
        # 任务相关
        self.task_id = increment_task_id()
        self.frames = []
        self.frame_index = 0
        self.temp_agent_pos_att = defaultdict(list)
        self.iterations = 0
        self.finished_tasks = 0
        self.round_finished = False
        self.savedir = './save/'
        # base the partner's estimated
        self.value_consistency = 0

        # finish_status == 0, not finished
        # finish_status == 1, one intent + none, finished
        # finish_status == 2, conflict intent, finished
        # finish_status == 3, non conflict intent, finished
        # finish_status == 4, max itearation, no success
        self.finish_status = 0
        self.playing_status = PlayingStatus.PLAYING


    def append_temp_pos_att(self, new_pos_att):
        for agent_id, pos_att in new_pos_att.items():
            self.temp_agent_pos_att[agent_id].extend(pos_att)

    def temp_agents(self, agent_id, other_id):
    
        temp_pos_att = self.temp_agent_pos_att[agent_id][self.frame_index]
        temp_agent = Agent()
        temp_agent.id = agent_id
        temp_agent.position = temp_pos_att[0]
        temp_agent.attention = temp_pos_att[1]
        temp_agent.size = 50

        temp_other_pos_att = self.temp_agent_pos_att[other_id][self.frame_index]
        temp_other_agent = Agent()
        temp_other_agent.id = other_id
        temp_other_agent.position = temp_other_pos_att[0]
        temp_other_agent.attention = temp_other_pos_att[1]
        temp_other_agent.size = 50
        return temp_agent, temp_other_agent
    
    def cleanup(self):
        self.frames = []
        self.temp_agent_pos_att = defaultdict(list)
        self.frame_index = 0
        print(f'cleanup user state {self.user_uuid}')


def init_scenario(room, global_user_args):
    for agent in room.world.agents:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass
        log.info(f'agent pipeline: {agent.name}')
        agent_pipeline(agent, room)

    # 双方都需要维护各自的初始 rendering frame
    for user_uuid, client_agent in room.client_user_dict.items():
        user_state = global_user_args[user_uuid]
        client_agent.observe(room.world, verbose=False)
        client_agent.update_belief(room.world)
        frames, agent_pos_atts = room.world.render_belief(client_agent, iter=room.iterations, current_agent=client_agent)
        user_state.frames.extend(frames)
        user_state.append_temp_pos_att(agent_pos_atts)


def agent_pipeline(agent, room):
    # fixme, very time-consuming operation in later rounds, to be optimized
    agent.observe(room.world, verbose=False)
    agent.update_belief(room.world)
    agent.observation = []
    log.info(
        "agent {} belief, [agent_ids {}], [object_ids {}], [landmark_ids {}]"
        .format(agent.name,
                agent.belief.agent_ids,
                agent.belief.object_ids,
                agent.belief.landmark_ids)
    )


def main_protocol_interact_u2u(room: ScenarioRoom, user_uuid, user_action, global_user_args, intent):

    client_agent: Agent = room.client_user_dict[user_uuid]
    user_state = global_user_args[user_uuid]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pass

    if client_agent.pointing is not None and user_action.name()[0] != 'ActionPointTo':
        client_agent.pointing = None
    if client_agent.waving is not None and user_action.name()[0] != 'ActionWaveHand':
        client_agent.waving = None
    if client_agent.nodding and user_action.name()[0] != 'ActionNodHead':
        client_agent.nodding = False
    if client_agent.nodding and user_action.name()[0] != 'ActionShakeHead':
        client_agent.shaking = False
    if client_agent.hitting and user_action.name()[0] != 'ActionHit':
        client_agent.hitting = None
    if client_agent.performing and user_action.name()[0] != 'ActionPerform':
        client_agent.performing = None
    if client_agent.speaking and user_action.name()[0] != 'ActionSpeak':
        client_agent.speaking = None
    if client_agent.shaking and user_action.name()[0] != 'ActionShakeHead':
        client_agent.shaking = None

    # todo 补充其他状态的清除

    actions = [user_action]
    log.info('iterations: {}, agent: {}, action: {}'.format(
        room.iterations, client_agent.name, user_action.name() if user_action is not None else "None"))
    room.world.step(actions)

    if user_action is not None:
        name = user_action.name()
        name.append(not client_agent.action_fail)
        client_agent.action_history.append(name)

    client_agent.observe(room.world, verbose=False)
    client_agent.update_belief(room.world)
    frames, agent_pos_atts = room.world.render_belief(client_agent, iter=room.iterations, current_agent=client_agent)
    user_state.frames.extend(frames)
    user_state.append_temp_pos_att(agent_pos_atts)
    # user_state.temp_agent_pos_att.extend(agent_pos_atts)

    ret = room.get_partner(user_uuid)
    if ret:
        # trigger partner agent
        partner_uuid, partner_agent = ret
        room.active_user_uuid = partner_uuid
        partner_state = global_user_args[partner_uuid]
        partner_agent.observe(room.world, verbose=False)
        partner_agent.update_belief(room.world)
        frames, agent_pos_atts = room.world.render_belief(partner_agent, iter=room.iterations,
                                 current_agent=partner_agent, update_belief_record=True)
        partner_state.frames.extend(frames)
        partner_state.append_temp_pos_att(agent_pos_atts)
        # partner_state.temp_agent_pos_att.extend(agent_pos_atts)

    room.iterations += 1

    # todo, 0725
    one_agent_finish_check = room.finish_check(room.world, room.scenario_name)
    #intent_diff == 0的情况，只有一个意图
    if room.scenario_name_another:
        another_agent_finish_check = room.finish_check_another(room.world, room.scenario_name_another)
    else:
        # 有一个agent意图是none
        another_agent_finish_check = True
    
    if room.max_iteration is not None:
        if room.iterations >= room.max_iteration:
            return one_agent_finish_check, FinishStatus.REACH_MAX_ITER
    else:
        if room.iterations >= MAX_ITERATIONS:
            return one_agent_finish_check, FinishStatus.REACH_MAX_ITER
    
    if room.intent_diff != 0 and 'Help' in intent:
        # 只截取其中initial_intent字串的部分
        current_agent_initial_intent = client_agent.initial_intent.ind_intent[0]
        # print(current_agent_initial_intent.ind_intent)
        # if ((not room.scenario_name_backup and
        #      current_agent_initial_intent in room.scenario_name) or
        #     (room.scenario_name_backup and
        #      current_agent_initial_intent in room.scenario_name_backup)):
        
        if not room.scenario_name_backup and current_agent_initial_intent in room.scenario_name:
            if one_agent_finish_check and not another_agent_finish_check:
                room.scenario_name_backup = deepcopy(room.scenario_name)
                room.scenario_name = deepcopy(room.scenario_name_another)
                return one_agent_finish_check, FinishStatus.DOING
        # if current_agent_initial_intent in room.scenario_name_another:
        if not room.scenario_name_another_backup and current_agent_initial_intent in room.scenario_name_another:
            if another_agent_finish_check and not one_agent_finish_check:
                room.scenario_name_another_backup = deepcopy(room.scenario_name_another)
                room.scenario_name_another = deepcopy(room.scenario_name)
                return one_agent_finish_check, FinishStatus.DOING

    if room.scenario_name_backup and another_agent_finish_check:
        room.scenario_name = deepcopy(room.scenario_name_backup)
        room.scenario_name_backup = None
        one_agent_finish_check = room.finish_check(room.world, room.scenario_name)
    elif room.scenario_name_backup and not another_agent_finish_check:
        return one_agent_finish_check, FinishStatus.DOING
    
    if room.scenario_name_another_backup and one_agent_finish_check:
        room.scenario_name_another = deepcopy(room.scenario_name_another_backup)
        room.scenario_name_another_backup = None
        another_agent_finish_check = room.finish_check_another(room.world, room.scenario_name_another)
    elif room.scenario_name_another_backup and not one_agent_finish_check:
        return one_agent_finish_check, FinishStatus.DOING
    
    # intent_diff == 1, 两个agent的意图冲突，某一个意图达成，即结束
    if room.intent_diff == 1 and (one_agent_finish_check or another_agent_finish_check):
        return one_agent_finish_check, FinishStatus.SUCCESS
    
    # intent_diff == 2且两个不冲突的意图都满足，或intent_diff == 0 不为空的意图被满足 
    if one_agent_finish_check and another_agent_finish_check:
        return one_agent_finish_check, FinishStatus.SUCCESS
   

    # if room.finish_check(room.world, room.scenario_name):
    # if one_agent_finish_check and another_agent_finish_check:
    #     return FinishStatus.SUCCESS    
    return one_agent_finish_check, FinishStatus.DOING


def get_world_id_names_dict(room):
    id_name_dict = dict()
    for agent in room.world.agents:
        id_name_dict[str(agent.id)] = agent.name
        id_name_dict[agent.name] = str(agent.id)
    for obj in room.world.objects:
        id_name_dict[str(obj.id)] = obj.name
        id_name_dict[obj.name] = str(obj.id)
    for ldm in room.world.landmarks:
        id_name_dict[str(ldm.id)] = ldm.name
        id_name_dict[ldm.name] = str(ldm.id)
    return id_name_dict


def get_belief_agent_list(client_agent):
    belief_agent_list = []
    for agent in client_agent.belief.agents:
        if agent.id == client_agent.id:
            continue
        belief_agent_list.append([agent.id, agent.name])
    return sorted(belief_agent_list, key=lambda x: x[0])


def calc_value_consistency(gt_value, be_estimated_value):
    # gt_value: [active, social, helpful]
    try:
        be_estimated_value = np.array(be_estimated_value.split(','), dtype=float)
    except:
        print(f'cannot convert {be_estimated_value} to float')
        return 0
    euclidean_sim = euclidean_similarity(gt_value, be_estimated_value)
    manhattan_sim = manhattan_similarity(gt_value, be_estimated_value)
    # only cares the direction not the magnitude
    cosine_sim = cosine_similarity(gt_value, be_estimated_value)
    minkowski_sim = minkowski_similarity(gt_value, be_estimated_value)
    print(f'euclidean Similarity: {euclidean_sim:.4f}, Manhattan Similarity: {manhattan_sim:.4f}, cosine Similarity: {cosine_sim:.4f}, Minkowski Similarity (p=3): {minkowski_sim:.4f}')
    return euclidean_sim


def calc_agents_rel_pos(client_agent):
    # label intent box 的总宽度为 440, 看了下，浏览器网页最大宽度为 1100，占比为 40%；
    # label intent box 的总高度为 151, 看了下，浏览器网页最大高度为 1100，占比为 13.73%；
    # label action box 的总宽度为 210, 看了下，浏览器网页最大宽度为 1100，占比为 19.1%；
    agent_rel_pos_dict = defaultdict(list)
    offset = 90
    for agent in client_agent.belief.agents:
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


# simple serialization for user tasks number
def read_user_tasks_data():
    current_dir = Path(__file__).parent
    file_path = current_dir / USER_FILE_PATH
    if file_path.stat().st_size == 0:
        return {}

    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def write_user_tasks_data(data):
    current_dir = Path(__file__).parent
    file_path = current_dir / USER_FILE_PATH
    with open(file_path, 'w') as f:
        json.dump(data, f)


def update_user_task_count(user_name):
    """更新指定用户的任务完成次数。"""
    data = read_user_tasks_data()

    if user_name in data:
        data[user_name] += 1
    else:
        data[user_name] = 1

    write_user_tasks_data(data)


def get_user_tasks_count(user_name, user_task_dict=None):
    """获取指定用户的任务完成次数。"""
    if user_task_dict is None:
        data = read_user_tasks_data()
    else:
        data = user_task_dict
    return data.get(user_name, 0)
