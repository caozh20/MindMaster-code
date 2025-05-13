from copy import deepcopy

import numpy as np

from .entity import *
from utils.base import *
from .const import *

# Age
BABY = 0
ADULT = 1

# tired tolerance
TIRED_TOLERANCE = 10

def get_entity_in_whose_mind(entity_id, W, in_whose_mind):
    try:
        if entity_id == in_whose_mind:
            # log.info("self(id: {}) in self's(id: {}) mind".format(entity_id, in_whose_mind))
            return W.retrieve_by_id(entity_id)
        if not in_whose_mind or in_whose_mind == -1:
            return W.retrieve_by_id(entity_id)
        return W.retrieve_by_id(in_whose_mind).belief.get_by_id(entity_id)
    except:
        return None


# def agent_attr_obs_dcopy(agent_self, agent, agent_new, W):
def agent_attr_obs_dcopy(agent, agent_new):
    agent_new.id = deepcopy(agent.id)
    agent_new.name = deepcopy(agent.name)
    agent_new.position = deepcopy(agent.position)
    agent_new.attention = deepcopy(agent.attention)
    agent_new.rotate = deepcopy(agent.rotate)
    agent_new.holding_ids = deepcopy(agent.holding_ids)
    agent_new.desire = deepcopy(agent.desire)
    agent_new.pointing = deepcopy(agent.pointing)
    agent_new.lifting = deepcopy(agent.lifting)
    agent_new.waving = deepcopy(agent.waving)
    agent_new.hitting = deepcopy(agent.hitting)
    agent_new.speaking = deepcopy(agent.speaking)
    agent_new.performing = deepcopy(agent.performing)
    agent_new.nodding = deepcopy(agent.nodding)
    agent_new.shaking = deepcopy(agent.shaking)
    agent_new.playing = deepcopy(agent.playing)
    agent_new.hands_occupied = deepcopy(agent.hands_occupied)

    # todo？？
    if len(agent.action_history):
        this_action = agent.action_history[-1]
        agent_new.action_history.append(deepcopy(this_action))


def _attention_check(agent, target, Att_R=None):

    if Att_R is not None:
        R=Att_R
    else:
        R=ATTENTION_RADIUS

    # check whether the target is in self's perception field
    if agent is None or target is None or agent.position is None:
        return False

    if isinstance(target, Entity):
        if target.position is None:
            return False
        if target.id in agent.holding_ids:
            return True
        if isinstance(agent.position == target.position, bool):
            if agent.position == target.position:
                return True
        if (np.asarray(agent.position) == target.position).all():
            return True
        angle_entity = angle([1, 0], np.asarray(target.position) - agent.position) / 180
        # min(origin, complementary), min(origin, 2-origin)
        diff = abs(angle_entity - agent.attention)
        if diff > 1:
            diff = 2-diff
        if diff <= (R / 2 + 0.006):
            return True
        else:
            return False

    else:
        # target is position
        if (np.asarray(agent.position) == target).all():
            return True
        angle_entity = angle([1, 0], np.asarray(target) - agent.position) / 180
        # min(origin, complementary), min(origin, 2-origin)
        diff = abs(angle_entity - agent.attention)
        if diff > 1:
            diff = 2 - diff
        if diff <= (R / 2 + 0.006):
            return True
        else:
            return False


def reset_gesture(agent):
    if len(agent.action_history) == 0:
        return
    last_action = agent.action_history[-1]
    if agent.waving and last_action[0] != 'ActionWaveHand':
        agent.waving = False
    if agent.pointing and last_action[0] != 'ActionPointTo':
        agent.pointing = None
    if agent.shaking and last_action[0] != 'ActionShakeHead':
        agent.shaking = False
    if agent.nodding and last_action[0] != 'ActionNodHead':
        agent.nodding = False
