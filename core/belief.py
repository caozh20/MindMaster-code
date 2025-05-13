# In this case, the agent will update its belief by its observation.
# But it will generate false belief, which will cause error in the scenario.

from copy import deepcopy
from collections import defaultdict
from .agent_utils import *
from .entity_utils import *
from .entity_utils import *


class Belief():
    def __init__(self):
        self.objects = []
        self.landmarks = []
        self.agents = []

        # 记录其他agent 的 action history
        self.other_agent_action_history = []

        self.object_ids = []
        self.agent_ids = []
        self.landmark_ids = []
        self.all_ids = []

        # memory previous position, for effective interaction
        # can have false belief
        self.memory_position = {}

        # when something is pointed or someone has shown interest in interacting with me, it will be attractive
        # self.attractive_objects = {}

        # 记录 agent 的 action history，避免当其成为 false belief 而被删除时，action_history 也丢了
        self.belief_agent_action_trajectory = defaultdict(list)

    # 清空belief里面的所有内容
    def clear(self):
        for object in self.objects:
            del object
        for landmark in self.landmarks:
            del landmark
        for agent in self.agents:
            del agent
        del self.object_ids
        del self.agent_ids
        del self.landmark_ids
        del self.all_ids

    def add_object(self, object):
        if isinstance(object, Object):
            self.objects.append(object)
            self.object_ids.append(object.id)
            self.all_ids.append(object.id)
            self.memory_position[object.id] = object.position
            return True
        return False

    def add_landmark(self, landmark):
        if isinstance(landmark, Landmark):
            self.landmarks.append(landmark)
            self.landmark_ids.append(landmark.id)
            self.all_ids.append(landmark.id)
            self.memory_position[landmark.id] = landmark.position
            return True
        return False

    def add_agent(self, agent):
        if isinstance(agent, Agent):
            self.agents.append(agent)
            self.agent_ids.append(agent.id)
            self.all_ids.append(agent.id)
            self.memory_position[agent.id] = agent.position
            return True
        return False

    @property
    def entities(self):
        # first render big object, then small object to avoid rendering overlap
        if len(self.objects) > 0:
            self.objects.sort(
                key=lambda obj: 0 if obj is None or obj.size is None else obj.size[0] * obj.size[1], reverse=True)
        return self.agents + self.objects + self.landmarks

    def update(self, observation, attention_check, agent_self, W):
        # phase 1 : update belief based on new observed entities
        for entity in observation:
            have_found = False
            if isinstance(entity, Agent):
                # 由于属性 copy 的限制，entity 的action_history 只有最后一布的action
                if len(entity.action_history) > 0:
                    self.other_agent_action_history.append(entity.action_history[-1])
                for i, agent in enumerate(self.agents):
                    if entity.id == agent.id:
                        agent_attr_obs_dcopy(entity, agent)
                        agent.be_observed_time = W.time
                        have_found = True
                        break

                # new agent
                if not have_found:
                    _entity = Agent()
                    # agent_attr_obs_dcopy(agent_self, entity, _entity, W)
                    agent_attr_obs_dcopy(entity, _entity)
                    if _entity.id in self.belief_agent_action_trajectory:
                        hist_action = self.belief_agent_action_trajectory[_entity.id]
                        for action in hist_action[::-1]:
                            _entity.action_history.insert(0, action)
                    _entity.be_observed_time = W.time
                    self.add_agent(_entity)

            elif isinstance(entity, Object):
                for i, object in enumerate(self.objects):
                    if entity.id == object.id:
                        # object = object_attr_obs_dcopy(entity)
                        # object = entity._copy()
                        entity._copy_to(object)
                        object.be_observed_time = W.time
                        have_found = True
                        break
                if not have_found:
                    copy = deepcopy(entity)
                    copy.be_observed_time = W.time
                    self.add_object(copy)

            elif isinstance(entity, Landmark):
                for i, landmark in enumerate(self.landmarks):
                    if entity.id == landmark.id:
                        have_found = True
                        break
                if not have_found:
                    copy = deepcopy(entity)
                    copy.be_observed_time = W.time
                    self.add_landmark(copy)

        # phase 2: false belief check
        observed_ids = [entity.id for entity in observation]
        belief_agent_ids = [agent.id for agent in self.agents]
        belief_object_ids = [object.id for object in self.objects]
        belief_landmark_ids = [landmark.id for landmark in self.landmarks]

        belief_agent_ids = [a for a in belief_agent_ids if a not in observed_ids]

        false_belief_agents = []
        for i, agent in enumerate(self.agents):
            if agent.id in belief_agent_ids:
                if agent.id == agent_self.id:
                    continue
                if attention_check(agent.position, W) == 1:
                    # cannot del in a forloop
                    false_belief_agents.append(agent)
        self.del_false_belief_agents(false_belief_agents)

        # non-observed but in belief
        belief_object_ids = [a for a in belief_object_ids if a not in observed_ids]

        # 0930, grab a container and the container containing some blf objects
        filter_object_ids = []
        for blf_obj_id in belief_object_ids:
            blf_obj = self.get_by_id(blf_obj_id)
            if blf_obj:
                for holding_id in agent_self.holding_ids:
                    holding_obj = self.get_by_id(holding_id)
                    if holding_obj:
                        if hasattr(holding_obj, 'containing') and blf_obj_id in holding_obj.containing:
                            filter_object_ids.append(blf_obj_id)
                            blf_obj.position = holding_obj.position
                            blf_obj.rotate = holding_obj.rotate

        for filter_object_id in filter_object_ids:
            belief_object_ids.remove(filter_object_id)
    
        false_belief_objs = []
        for i, object in enumerate(self.objects):
            if object.id in belief_object_ids:
                # if len(object.being_held_id):
                #     continue
                if attention_check(object.position, W) == 1:
                    # cannot del in a forloop
                    false_belief_objs.append(object)
        self.del_false_belief_objects(false_belief_objs)

        # should the landmarks be moved?
        belief_landmark_ids = [a for a in belief_landmark_ids if a not in observed_ids]

        false_belief_landmarks = []
        for i, landmark in enumerate(self.landmarks):
            if landmark.id in belief_landmark_ids:
                if attention_check(landmark.position, W) == 1:
                    # cannot del in a forloop
                    false_belief_landmarks.append(landmark)
        self.del_false_belief_landmarks(false_belief_landmarks)

        # phase 3: update belief of self
        found=0
        for agent in self.agents:
            if agent.id == agent_self.id:
                found=1
        if found==0:
            self.add_agent(agent_self)

    def del_false_belief_agents(self, false_belief_agents):
        for false_belief_agent in false_belief_agents:
            self.agents.remove(false_belief_agent)
            self.agent_ids.remove(false_belief_agent.id)
            self.all_ids.remove(false_belief_agent.id)
            if len(false_belief_agent.action_history) > 0:
                # self.belief_agent_action_trajectory[false_belief_agent.id].extend(false_belief_agent.action_history)
                self.belief_agent_action_trajectory[false_belief_agent.id] = false_belief_agent.action_history
            self.memory_position[false_belief_agent.id] = None
            # agent 成为 false belief 时，agent holding 的物体是否成为 false belief
            for holding_id in false_belief_agent.holding_ids:
                if holding_id not in self.all_ids:
                    continue
                self.object_ids.remove(holding_id)
                self.all_ids.remove(holding_id)
                self.objects.remove(self.get_by_id(holding_id))

    def del_false_belief_objects(self, false_belief_objs):
        for false_belief_obj in false_belief_objs:
            self.objects.remove(false_belief_obj)
            self.object_ids.remove(false_belief_obj.id)
            self.all_ids.remove(false_belief_obj.id)

    def del_false_belief_landmarks(self, false_belief_landmarks):
        for false_belief_landmark in false_belief_landmarks:
            self.landmarks.remove(false_belief_landmark)
            self.landmark_ids.remove(false_belief_landmark.id)
            self.all_ids.remove(false_belief_landmark.id)

    def del_objects(self, obj_ids: list):
        # 这里可能带来的变化是，对别人的belief的估计可能会出问题，怎么更新？
        false_belief_objs = []
        for obj_id in obj_ids:
            false_belief_objs.append(self.get(obj_id))
        false_belief_objs = [obj for obj in false_belief_objs if obj is not None]
        if len(false_belief_objs) == 0:
            return
        self.del_false_belief_objects(false_belief_objs=false_belief_objs)

    def check(self, target):
        if isinstance(target, int):
            return self.check_by_id(target)
        else:
            return self.check_by_entity(target)

    # todo: check through id; make sure this is correct!
    # also, here we don't check the false belief of entity attributes!
    def check_by_entity(self, entity):
        if isinstance(entity, Agent):
            if entity.id in [agent.id for agent in self.agents]:
                return True
            else:
                return False
        elif isinstance(entity, Object):
            if entity.id in [object.id for object in self.objects]:
                return True
            else:
                return False
        elif isinstance(entity, Landmark):
            if entity.id in [landmark.id for landmark in self.landmarks]:
                return True
            else:
                return False
        else:
            raise ValueError("Wrong Entity Type!")

    def check_by_id(self, id):
        if id in self.object_ids:
            return True
        if id in self.agent_ids:
            return True
        if id in self.landmark_ids:
            return True
        return False

    def get(self, target):
        if isinstance(target, int):
            return self.get_by_id(target)
        else:
            return self.get_by_entity(target)

    def get_by_entity(self, entity):
        if isinstance(entity, Agent):
            for agent in self.agents:
                if agent.id == entity.id:
                    return agent
        elif isinstance(entity, Object):
            for object in self.objects:
                if object.id == entity.id:
                    return object
        elif isinstance(entity, Landmark):
            for landmark in self.landmarks:
                if landmark.id == entity.id:
                    return landmark
        return None

    def get_by_id(self, id):
        for agent in self.agents:
            if agent.id == id:
                return agent
        for object in self.objects:
            if object.id == id:
                return object
        for landmark in self.landmarks:
            if landmark.id == id:
                return landmark
        return None

    def get_all_entities(self):
        return self.agents + self.objects + self.landmarks

    def get_all_ids(self):
        return [agent.id for agent in self.agents] + [object.id for object in self.objects] + [landmark.id for landmark
                                                                                               in self.landmarks]

    def get_agent_ids(self):
        return [agent.id for agent in self.agents]

    def get_obj_ids(self):
        return [object.id for object in self.objects]

    def get_landmark_ids(self):
        return [landmark.id for landmark in self.landmarks]

    def __call__(self):
        return {"objects": self.objects, "landmarks": self.landmarks, "agents": self.agents}

    def check_position(self, target):
        # if the input is id
        if isinstance(target, int):
            if self.memory_position.get(target) is not None:
                return self.memory_position[target]
            else:
                return False
        elif isinstance(target, Entity):
            if self.memory_position.get(target.id) is not None:
                return self.memory_position[target.id]
            else:
                return False


from core.agent import Agent
from core.world import *