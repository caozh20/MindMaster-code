from core.entity import Entity, Object
from core.agent import Agent
from sys import flags
from utils.base import dis, euclidean_dist
from core.const import *
from core.agent_utils import get_entity_in_whose_mind
from core.world import World
from core.action import *
from utils.base import log
import random
from core.entity_utils import Is_Near

class CheckFn():
    def __init__(self, *args):
        pass


class belief_id_position_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(belief_id_position_check, self).__init__()
        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W: World, in_whose_mind=-1):

        # agent = W.retrieve_by_id(self.agent_id)
        agent = get_entity_in_whose_mind(self.agent_id, W, in_whose_mind)
        if (self.target_id not in agent.belief.get_all_ids()) or (agent.belief.get_by_id(self.target_id).position is None):
            return False, ActionExplore(W.retrieve_by_id(self.agent_id))
        else:
            return True, None

    @staticmethod
    def name():
        return "belief_id_position_check"

    def action_name(self):
        return [['ActionExplore', str(self.agent_id)]]


class self_attention_check(CheckFn):
    # attention_check is always after belief check?
    def __init__(self, agent_id, target_id):
        super(self_attention_check, self).__init__()
        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        agent = get_entity_in_whose_mind(self.agent_id, W, in_whose_mind)
        target = get_entity_in_whose_mind(self.target_id, W, in_whose_mind)
        # if agent.attention_check(target, 0.001):
        attention_flag = agent.attention_check(target, W)

        # if attention_flag == True:
        #     return True, None
        # elif attention_flag == -1:
        #     return False, ActionRotateTo(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))
        # else:
        #     return False, ActionExplore(W.retrieve_by_id(self.agent_id))

        if attention_flag != -1:
            return True, None
        else:
            # return False, ActionRotateTo(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))
            return False, ActionRotateTo(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))

    @staticmethod
    def name():
        return "self_attention_check"

    def action_name(self):
        # return [['ActionExplore', str(self.agent_id)], ['ActionRotateTo', str(self.agent_id), str(self.target_id)]]
        return [['ActionRotateTo', str(self.agent_id), str(self.target_id)]]


class turn_to_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(turn_to_check, self).__init__()

        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        agent = get_entity_in_whose_mind(self.agent_id, W, in_whose_mind)
        target = get_entity_in_whose_mind(self.target_id, W, in_whose_mind)
        attention_flag = agent.attention_check(target, W, 0.001)
        if attention_flag == True:
            return True, None
        elif attention_flag == -1:
            return False, ActionRotateTo(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))
        else:
            return False, ActionExplore(W.retrieve_by_id(self.agent_id))

    @staticmethod
    def name():
        return "turn_to_check"

    def action_name(self):
        return [["ActionRotateTo", str(self.agent_id), str(self.target_id)]]


class receiver_attention_on_me_by_refer_check(CheckFn):
    def __init__(self, receiver_id, me_id):
        super(receiver_attention_on_me_by_refer_check, self).__init__()
        self.receiver_id = receiver_id
        self.me_id = me_id

    def __call__(self, W, in_whose_mind=-1):
        # build the communication channel?
        # todo: show the instant and flexible feature of our work
        me = get_entity_in_whose_mind(self.me_id, W, in_whose_mind)
        receiver = me.belief.get_by_entity(W.retrieve_by_id(self.receiver_id))

        if not receiver:
            return False, ActionExplore(W.retrieve_by_id(self.me_id))
        # which means needs eye to eye
        if receiver.attention_check(me, W, Att_R=0.001) == 1:
            me.waving = False
            return True, None
        else:
            v, a = self_attention_check(
                self.me_id, self.receiver_id)(W, in_whose_mind)
            if v is True:
                return False, ActionWaveHand(W.retrieve_by_id(self.me_id), W.retrieve_by_id(self.receiver_id))
            elif v is False:
                return False, a

    @staticmethod
    def name():
        return "receiver_attention_on_me_by_refer_check"

    def action_name(self):
        return [['ActionExplore', str(self.me_id)],
                ['ActionRotateTo', str(self.me_id), str(self.receiver_id)],
                ['ActionWaveHand', str(self.me_id), str(self.receiver_id)]]


class receiver_attention_on_me_by_action_check(CheckFn):
    def __init__(self, receiver_id, me_id):
        super(receiver_attention_on_me_by_action_check, self).__init__()
        self.receiver_id = receiver_id
        self.me_id = me_id

    def __call__(self, W, in_whose_mind=-1):
        # build the communication channel?
        # todo: show the instant and flexible feature of our work
        me = get_entity_in_whose_mind(self.me_id, W, in_whose_mind)
        receiver = me.belief.get_by_entity(W.retrieve_by_id(self.receiver_id))

        if not receiver:
            return False, ActionExplore(W.retrieve_by_id(self.me_id))
        # which means needs eye to eye
        if receiver.attention_check(me, W, Att_R=0.001) == 1:
            me.waving = False
            return True, None
        else:
            v, a = self_attention_check(
                self.me_id, self.receiver_id)(W, in_whose_mind)
            if v is True:
                return False, ActionMoveToAttention(W.retrieve_by_id(self.me_id), W.retrieve_by_id(self.receiver_id))
            elif v is False:
                return False, a

    @staticmethod
    def name():
        return "receiver_attention_on_me_by_action_check"

    def action_name(self):
        return [['ActionExplore', str(self.me_id)],
                ['ActionRotateTo', str(self.me_id), str(self.receiver_id)],
                ['ActionMoveToAttention', str(self.me_id), str(self.receiver_id)]]


class receiver_attention_on_target_check(CheckFn):
    def __init__(self, receiver_id, target_id, me_id):
        super(receiver_attention_on_target_check, self).__init__()
        self.receiver_id = receiver_id
        self.target_id = target_id
        self.me_id = me_id

    def __call__(self, W, in_whose_mind=-1):
        # which can use belief?
        # todo: check whether the receiver and the target are retrieved from the world...
        receiver = get_entity_in_whose_mind(self.receiver_id, W, in_whose_mind)
        me = get_entity_in_whose_mind(self.me_id, W, in_whose_mind)
        target = get_entity_in_whose_mind(self.target_id, W, in_whose_mind)
        if not receiver and target:
            return False, ActionExplore(W.retrieve_by_id(self.me_id))
        # if receiver.attention_check(target, W, Att_R=0.01) == 1:
        if receiver.attention_check(target, W, ) == 1:
            return True, ActionPointTo(W.retrieve_by_id(self.me_id), STOP)
        else:
            # todo: just pointing here?
            return False, ActionPointTo(me, W.retrieve_by_id(self.target_id))

    @staticmethod
    def name():
        return "receiver_attention_on_target_check"

    def action_name(self):

        return [['ActionExplore', str(self.me_id)],
                ['ActionPointTo', str(self.me_id), str(self.target_id)],
                ['ActionPointTo', str(self.me_id), str(-1)]]


class real_position_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(real_position_check, self).__init__()
        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        # todo: the false belief problem
        v, a = belief_id_position_check(
            self.agent_id, self.target_id)(W, in_whose_mind)
        if v is False:
            return v, a
        # todo: rotate to the position in belief
        else:
            v, a = self_attention_check(
                self.agent_id, self.target_id)(W, in_whose_mind)
            return v, a

    @staticmethod
    def name():
        return "real_position_check"

    def action_name(self):

        return [['ActionExplore', str(self.agent_id)],
                ['ActionRotateTo', str(self.agent_id), str(self.target_id)]]


class distance_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(distance_check, self).__init__()
        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        # agent = W.retrieve_by_id(self.agent_id)
        agent = get_entity_in_whose_mind(self.agent_id, W, in_whose_mind)
        target = W.retrieve_by_id(self.target_id)
        if not target:
            return False, ActionExplore(W.retrieve_by_id(self.agent_id))
        if self.target_id in agent.holding_ids:
            return True, None

        true_target = target
        if hasattr(target, 'being_contained') and len(target.being_contained) > 0:
            true_target = W.retrieve_by_id(target.being_contained[0])
        if hasattr(target, 'being_held_id') and len(target.being_held_id) > 0:
            true_target = W.retrieve_by_id(target.being_held_id[0])

        max_border_distance = (agent.size + true_target.size) if isinstance(true_target.size, int) else (
                    agent.size + np.sqrt((true_target.size[0] // 2) ** 2 + (true_target.size[1] // 2) ** 2))

        if dis(agent, target) <= max_border_distance + 5:  # self.reachable_check
            # 5 means a tolerance
            return True, None
        else:
            return False, ActionMoveTo(W.retrieve_by_id(self.agent_id), true_target)

    @staticmethod
    def name():
        return "distance_check"

    def action_name(self):
        return [['ActionExplore', str(self.agent_id)], ['ActionMoveTo', str(self.agent_id), str(self.target_id)]]


class key_in_mind_check(CheckFn):
    def __init__(self, agent_id):
        super(key_in_mind_check, self).__init__()
        self.agent_id = agent_id

    def __call__(self, W, in_whose_mind=-1):
        key_id = 0
        agent = W.retrieve_by_id(self.agent_id)
        for obj in agent.belief.objects:
            if obj.is_key:
                key_id = obj.id
        if key_id == 0:
            # in chimpanzee should not reach here
            return False, ActionExplore(W.retrieve_by_id(self.agent_id))
        else:
            return True, key_id

    @staticmethod
    def name():
        return "key_in_mind_check"

    def action_name(self):
        return [['ActionExplore', str(self.agent_id)]]


class unlocked_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(unlocked_check, self).__init__()
        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        agent = W.retrieve_by_id(self.agent_id)
        target = W.retrieve_by_id(self.target_id)
        actions = []
        if hasattr(target, 'locked') and target.locked:
            my_key_in_mind_check = key_in_mind_check(self.agent_id)
            v, a = my_key_in_mind_check(W, self.agent_id)
            if not v:
                return v, a
            else:
                key_id = a
                key = W.retrieve_by_id(key_id)

                v, a = self_attention_check(self.agent_id, key_id)(W, in_whose_mind)
                if not v:
                    return v, a
                v, a = distance_check(self.agent_id, key_id)(W, in_whose_mind)
                if not v:
                    return v, a
                # todo: holding check?
                if len(key.being_held_id) == 0:
                    return False, ActionGrab(agent, key)
                v, a = distance_check(self.agent_id, self.target_id)(W, in_whose_mind)
                if not v:
                    return v, a
                if len(key.being_held_id) > 0:
                    return False, ActionUnlock(agent, target)
        else:
            return True, None

    @staticmethod
    def name():
        return "unlocked_check"

    def action_name(self):
        # todo
        return [['ActionExplore', str(self.agent_id)], ['ActionMoveTo', str(self.agent_id), str(self.target_id)]]


class open_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(open_check, self).__init__()

        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        target = get_entity_in_whose_mind(self.target_id, W, in_whose_mind)
        agent = get_entity_in_whose_mind(self.agent_id, W, in_whose_mind)
        if target.open:
            if agent.hitting:
                agent.hitting = None
            return True, None
        elif agent.hands_occupied:
            return False, ActionHit(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))
        else:
            return False, ActionOpen(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))

    @staticmethod
    def name():
        return "open_check"

    def action_name(self):
        return [["ActionOpen", str(self.agent_id), str(self.target_id)]]


class gaze_follow_loop_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(gaze_follow_loop_check, self).__init__()

        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        if self.target_id == STOP:
            return True, None
        return False, ActionObserveAgent(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))

    @staticmethod
    def name():
        return "gaze_follow_loop_check"

    def action_name(self):
        return [["ActionObserveAgent", str(self.agent_id), str(self.target_id)]]


class grab_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(grab_check, self).__init__()

        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        target = get_entity_in_whose_mind(self.target_id, W, in_whose_mind)
        if isinstance(target, Object) and len(target.being_held_id) > 0:
            for where_id in target.being_held_id:
                where = get_entity_in_whose_mind(where_id, W, in_whose_mind)
                if isinstance(where, Object):
                    if not where.open:
                        return False, ActionOpen(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(where_id))
        return True, None

    @staticmethod
    def name():
        return "grab_check"

    def action_name(self):
        # fixme, only in the execution the where id can be
        return [["ActionOpen", str(self.agent_id), str(-1)]]


class holding_check(CheckFn):
    def __init__(self, agent_id, target_id):
        super(holding_check, self).__init__()
        self.agent_id = agent_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        agent = get_entity_in_whose_mind(self.agent_id, W, in_whose_mind)
        target = get_entity_in_whose_mind(self.target_id, W, in_whose_mind)
        if self.target_id in agent.holding_ids:
            return True, None
        elif agent.attention_check(target, W) != 1:
            return False, ActionRotateTo(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))
        else:
            if len(target.being_held_id) == 0:
                return False, ActionGrab(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id))
            else:
                return False, ActionGrab(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id), W.retrieve_by_id(self.target_id).being_held_entity[0])

    @staticmethod
    def name():
        return "holding_check"

    def action_name(self):
        return [["ActionRotateTo", str(self.agent_id), str(self.target_id)], ["ActionGrab",  str(self.agent_id), str(self.target_id)]]


class give_check(CheckFn):
    def __init__(self, agent_id, target_id, sb_id):
        super(give_check, self).__init__()
        self.agent_id = agent_id
        self.target_id = target_id
        self.sb_id = sb_id

    def __call__(self, W, in_whose_mind=-1):
        agent = get_entity_in_whose_mind(self.agent_id, W, in_whose_mind)
        target = get_entity_in_whose_mind(self.target_id, W, in_whose_mind)
        sb = get_entity_in_whose_mind(self.sb_id, W, in_whose_mind)
        if self.target_id not in agent.holding_ids and self.target_id in sb.holding_ids:
            return True, None
        else:
            return False, ActionGiveTo(W.retrieve_by_id(self.agent_id), W.retrieve_by_id(self.target_id), W.retrieve_by_id(self.sb_id))

    @staticmethod
    def name():
        return "give_check"

    def action_name(self):
        return [["ActionGiveTo",  str(self.agent_id), str(self.target_id), str(self.sb_id)]]


# True means in agent's belief, two targets are together
def Pure_Together_Check(agent_input, target1_input, target2_input, W):
    target1 = None
    target2 = None
    agent_id = None
    if isinstance(agent_input, int):
        agent_id = agent_input
    elif isinstance(agent_input, Agent):
        agent_id = agent_input.id
    if isinstance(target1_input, int):
        target1 = get_entity_in_whose_mind(target1_input, W, agent_id)
    elif isinstance(target1_input, Entity):
        target1 = target1_input
    if isinstance(target2_input, int):
        target2 = get_entity_in_whose_mind(target2_input, W, agent_id)
    elif isinstance(target2_input, Entity):
        target2 = target2_input
    if target1 is None or target2 is None:
        return False
    if target1.position is None or target2.position is None:
        # Todo: how to solve the unknown target?
        return False
    return Is_Near(target1, target2, W)


# rotate only once rather than loop, no matter false belief or not
class rotate_to_check(CheckFn):
    def __init__(self, me_id, who_id):
        super(rotate_to_check, self).__init__()
        self.me_id = me_id
        self.who_id = who_id

    def __call__(self, W, in_whose_mind=-1):
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        who = get_entity_in_whose_mind(self.who_id, W, self.me_id)
        return True, ActionRotateTo(me, who)
    @staticmethod
    def name():
        return "rotate_to_check"

    def action_name(self):
        return [['ActionRotateTo', str(self.me_id), str(self.who_id)]]


class confirm_check(CheckFn):
    def __init__(self, me_id, receiver_id):
        super(confirm_check, self).__init__()
        self.receiver_id = receiver_id
        self.me_id = me_id

    def __call__(self, W, in_whose_mind=-1):
        # build the communication channel?
        # todo: show the instant and flexible feature of our work
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        receiver = get_entity_in_whose_mind(self.receiver_id, W, -1)

        if me.attention_check(receiver, W, Att_R=0.001) != 1:
            # means follow the agent moving
            # return False, ActionObserveAgent(me, receiver)
            return True, None
        # which means needs eye to eye
        if receiver.attention_check(me, W, Att_R=0.001) == 1:
            return True, ActionNodHead(me, receiver)
        else:
            return True, None

    @staticmethod
    def name():
        return "confirm_check"

    def action_name(self):
        return [['ActionObserveAgent', str(self.me_id), str(self.receiver_id)], ['ActionNodHead', str(self.me_id), str(self.receiver_id)]]


class get_sth_from_sb_check(CheckFn):
    # todo:
    def __init__(self, me_id, what_id, where_id):
        super(get_sth_from_sb_check, self).__init__()
        self.me_id = me_id
        self.what_id = what_id
        self.where_id = where_id

    def __call__(self, W, in_whose_mind=-1):
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        where = get_entity_in_whose_mind(self.where_id, W, -1)
        what = get_entity_in_whose_mind(self.what_id, W, -1)
        if self.what_id in me.holding_ids:
            return True, None

        # elif me.pointing or dis(where, what) <= NEAR_DIS:
        #     if me.pointing and dis(where, what) <= NEAR_DIS:
        elif me.pointing or Is_Near(where, what, W):
            if me.pointing and Is_Near(where, what, W):
                me.pointing = None
            return False, ActionObserveAgent(me, where)
        else:
            return False, ActionPointTo(me, what)

    @staticmethod
    def name():
        return "get_sth_from_sb_check"

    def action_name(self):
        return [['ActionPointTo', str(self.me_id), str(self.what_id)], ['ActionObserveAgent', str(self.me_id), str(self.where_id)]]


class put_sth_into_sw_by_sb_check(CheckFn):
    # todo:
    def __init__(self, me_id, who_id, what_id, where_id):
        super(put_sth_into_sw_by_sb_check, self).__init__()
        self.me_id = me_id
        self.who_id = who_id
        self.what_id = what_id
        self.where_id = where_id

    def __call__(self, W, in_whose_mind=-1):
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        who = get_entity_in_whose_mind(self.who_id, W, -1)
        where = get_entity_in_whose_mind(self.where_id, W, -1)
        what = get_entity_in_whose_mind(self.what_id, W, -1)
        if self.what_id in where.containing:
            return True, None
        elif self.what_id in me.holding_ids and me.pointing is None:
            # todo, in probability choose pointto to where or putinto by me self.
            return False, ActionPointTo(me, where)
        else:
            # if dis(who, what) <= NEAR_DIS or dis(who, where) <= NEAR_DIS:
            if me.pointing:
                me.pointing = None
            return False, ActionObserveAgent(me, who)

    @staticmethod
    def name():
        return "put_sth_into_sw_by_sb_check"

    def action_name(self):
        return [['ActionPointTo', str(self.me_id), str(self.where_id)], ['ActionObserveAgent', str(self.me_id), str(self.who_id)]]

class put_sth_onto_sw_by_sb_check(CheckFn):
    # todo:
    def __init__(self, me_id, who_id, what_id, where_id):
        super(put_sth_onto_sw_by_sb_check, self).__init__()
        self.me_id = me_id
        self.who_id = who_id
        self.what_id = what_id
        self.where_id = where_id

    def __call__(self, W, in_whose_mind=-1):
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        who = get_entity_in_whose_mind(self.who_id, W, -1)
        where = get_entity_in_whose_mind(self.where_id, W, -1)
        what = get_entity_in_whose_mind(self.what_id, W, -1)
        if self.what_id in where.supporting_ids:
            return True, None
        elif self.what_id in me.holding_ids and me.pointing is None:
            # todo, in probability choose pointto to where or putinto by me self.
            return False, ActionPointTo(me, where)
        else:
            # if dis(who, what) <= NEAR_DIS or dis(who, where) <= NEAR_DIS:
            if me.pointing:
                me.pointing = None
            return False, ActionObserveAgent(me, who)

    @staticmethod
    def name():
        return "put_sth_onto_sw_by_sb_check"

    def action_name(self):
        return [['ActionPointTo', str(self.me_id), str(self.where_id)], ['ActionObserveAgent', str(self.me_id), str(self.who_id)]]


class ready_play_together_check(CheckFn):
    # todo:
    def __init__(self, me_id, receiver_id, what_id):
        super(ready_play_together_check, self).__init__()
        self.me_id = me_id
        self.receiver_id = receiver_id
        self.what_id = what_id

    def __call__(self, W, in_whose_mind=-1):
        # assume that when the agent is close, he is ready
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        receiver = get_entity_in_whose_mind(self.receiver_id, W, -1)
        what = get_entity_in_whose_mind(self.what_id, W, -1)
        if not Is_Near(me, what, W):
            return False, ActionMoveTo(me, what)
        v, a = self_attention_check(self.me_id, self.what_id)(W, in_whose_mind)
        if not v:
            return False, a
        # should me point to the what? or something else to change the situation?
        v, a = receiver_attention_on_target_check(
            self.receiver_id, self.what_id, self.me_id)(W, in_whose_mind)
        if not v:
            return False, a
        if not Is_Near(receiver, what, W):
            return False, ActionPointTo(me, what)
        else:
            return True, ActionPlay(me, what)

    @staticmethod
    def name():
        return "ready_play_together_check"

    def action_name(self):
        return [['ActionMoveTo', str(self.me_id), str(self.what_id)], ['ActionPointTo', str(self.me_id), str(self.what_id)], ['ActionPlay', str(self.me_id), str(self.what_id)]]


# point 的接收者
class refer_check(CheckFn):
    def __init__(self, me_id, receiver_id, target_id_list):
        super(refer_check, self).__init__()
        self.me_id = me_id
        self.receiver_id = receiver_id
        self.target_id_list = target_id_list

    def __call__(self, W, in_whose_mind=-1):
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        receiver = get_entity_in_whose_mind(self.receiver_id, W, -1)
        # if receiver.shaking:
        #     for target_id in self.target_id_list:
        #         if target_id != me.pointing:
        #             target = get_entity_in_whose_mind(target_id, W, -1)
        #             return False, ActionPointTo(me, target)
        if receiver.nodding:
            if me.pointing:
                me.pointing = None
            return True, ActionNodHead(me)
        else:
            for target_id in self.target_id_list:
                if target_id != me.pointing:
                    target = get_entity_in_whose_mind(target_id, W, -1)
                    return False, ActionPointTo(me, target)

    @staticmethod
    def name():
        return "refer_check"

    def action_name(self):
        return [['ActionPointTo', str(self.me_id), ], ['ActionPointTo', str(self.me_id), str(STOP)]]


# point 的发出者
class point_check(CheckFn):
    def __init__(self, me_id, receiver_id, target_id):
        super(point_check, self).__init__()
        self.me_id = me_id
        self.receiver_id = receiver_id
        self.target_id = target_id

    def __call__(self, W, in_whose_mind=-1):
        me = get_entity_in_whose_mind(self.me_id, W, -1)
        receiver = get_entity_in_whose_mind(self.receiver_id, W, -1)
        if receiver.pointing is None:
            return False, ActionWait(me)
        elif receiver.pointing != self.target_id:
            return False, ActionShakeHead(me)
        else:
            me.point_confirm = False
            if me.shaking:
                me.shaking = False
            return True, ActionNodHead(me)

    @staticmethod
    def name():
        return "point_check"

    def action_name(self):
        return [['ActionShakeHead', str(self.me_id)], ['ActionNodHead', str(self.me_id)]]
