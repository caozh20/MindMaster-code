

def inverse_infer_belief(agent_self, world):

    if len(agent_self.belief.agents) == 0:
        return

    for agent in agent_self.belief.agents:

        if agent.id == agent_self.id:
            continue
        if agent.position is None:
            continue

        # phase 1
        second_observed_ids = []

        for _agent in agent_self.belief.agents:
            if agent.id == _agent.id:
                continue
            elif _agent.position is None:
                continue
            elif agent.attention_check(_agent, world) == 1:
                second_observed_ids.append(_agent.id)
                if _agent.id not in agent.belief.agent_ids:
                    _tmp = Agent()
                    # agent_attr_obs_dcopy(agent_self, _agent, _tmp, world)
                    agent_attr_obs_dcopy(_agent, _tmp)
                    agent.belief.add_agent(_tmp)

        for object in agent_self.belief.objects:
            if object.position is None:
                continue
            if agent.attention_check(object, world) == 1:
                second_observed_ids.append(object.id)
                agent.belief.add_object(deepcopy(object))

        for landmark in agent_self.belief.landmarks:
            if landmark.position is None:
                continue
            if agent.attention_check(landmark, world) == 1:
                second_observed_ids.append(landmark.id)
                agent.belief.add_landmark(deepcopy(landmark))

        # phase 2
        second_belief_agents = [a.id for a in agent.belief.agents]
        second_belief_objects = [o.id for o in agent.belief.objects]
        second_belief_landmarks = [l.id for l in agent.belief.landmarks]

        second_belief_agents = [a for a in second_belief_agents if a not in second_observed_ids]
        second_belief_objects = [a for a in second_belief_objects if a not in second_observed_ids]
        second_belief_landmarks = [a for a in second_belief_landmarks if a not in second_observed_ids]

        false_belief_agents = []
        for a in agent.belief.agents:
            if a.id == agent.id:
                continue
            if a.id in second_belief_agents:
                if agent.attention_check(a, world) == 1:
                    false_belief_agents.append(a)
        agent.belief.del_false_belief_agents(false_belief_agents)

        false_belief_objs = []
        for o in agent.belief.objects:
            if o.id in second_belief_objects:
                if agent.attention_check(o, world) == 1:
                    false_belief_objs.append(o)
        agent.belief.del_false_belief_objects(false_belief_objs)

        false_belief_landmarks = []
        for l in agent.belief.landmarks:
            if l.id in second_belief_landmarks:
                if agent.attention_check(l, world) == 1:
                    false_belief_landmarks.append(l)
        agent.belief.del_false_belief_landmarks(false_belief_landmarks)

        # phase 3: update belief of self
        found = 0
        for _agent in agent.belief.agents:
            if _agent.id == agent.id:
                found = 1
        if found == 0:
            agent.belief.add_agent(agent)


from .agent import Agent
from .agent_utils import *
from .entity_utils import *
