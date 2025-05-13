from core.agent import Agent
from copy import deepcopy
import numpy as np
import math
import random
from random import randint
from core.const import *
from utils import base
from utils.base import angle, rel_pos_in_shelf
from core.entity import *
from utils.base import log, edge_location, attention_location, agent_left_upper_with_offset
# for vscode and other editor
import core


def update_holding_position_rotate(agent, W):
    if len(agent.holding_ids) <= 0:
        return
    for e_id in agent.holding_ids:
        e = W.retrieve_by_id(e_id)
        # e.position = self.agent.position
        e.rotate = agent.rotate
        e.position = agent_left_upper_with_offset(agent, e)


class Action():
    def __init__(self, agent: Agent, target):
        self.agent = agent
        self.target = target

        try:
            assert isinstance(agent, Agent)
        except AssertionError:
            print("Not an agent performing the action!")

        self.agent_id = agent.id

        if isinstance(target, Entity):
            self.target_id = target.id
        elif isinstance(target, list) and len(target) == 2:
            self.target_id = f'{target[0]},{target[1]}'
        else:
            self.target_id = None


class ActionMoveTo(Action):
    def __init__(self, agent, target):
        if target is None:
            target = EXPLORE
        if isinstance(target, str) and 'explore' in target.lower():
            target = EXPLORE
        super(ActionMoveTo, self).__init__(agent, target)

    def name(self):
        if self.target == EXPLORE:
            # print('Agent {}, ActionMoveTo, EXPLORE'.format(self.agent.id))
            return ['ActionMoveTo', str(self.agent_id), '-1']

        else:
            # print('Agent {}, ActionMoveTo, Target {}'.format(self.agent.id, self.target.id))
            # print(['ActionMoveTo', str(self.agent_id), str(self.target_id)])
            return ['ActionMoveTo', str(self.agent_id), str(self.target_id)]

    def execute(self, W):

        if self.target == EXPLORE:
            tmp_position = self.agent.position + np.array([randint(-70, 70), randint(-70, 70)], dtype=np.float64)
            while not W.position_available_check(tmp_position):
                tmp_position = self.agent.position + np.array([randint(-70, 70), randint(-70, 70)], dtype=np.float64)
            for i in range(len(tmp_position)):
                self.agent.position[i] = tmp_position[i]
            update_holding_position_rotate(self.agent, W)
        elif isinstance(self.target, Entity):
            if core.check_fn.pure_belief_position_check(self.agent, self.target, W):
                # self.agent.position = deepcopy(self.target.position)
                # move to the position in belief? the Sally-Anne test (false belief)
                # self.agent.position = deepcopy(
                #     self.agent.belief.get(self.target).position)
                # 从游玩的状态移动
                if self.agent.playing_object_id is not None:
                    W.retrieve_by_id(self.agent.playing_object_id).player_num -= 1
                    self.agent.playing_object_id = None


                if isinstance(self.target, Object) and self.target.multiplayer_game_available_position(self.agent.size, self.agent.id, W) is not None:
                    if self.target.id2position.get(self.agent.id) is None:
                        self.target.id2position[self.agent.id] = self.target.multiplayer_game_available_position(self.agent.size, self.agent.id, W)
                        self.target.player_num += 1
                    self.agent.position = self.target.id2position[self.agent.id]
                    self.agent.playing_object_id = self.target.id
                else:
                    # edge_type, self.agent.position = edge_location(self.agent.position, self.agent.size, self.target, W)
                    edge_type, self.agent.position = edge_location(self.agent.position, self.agent.size, self.agent.belief.get(self.target), W)
                    if hasattr(self.target, 'edge_occupied'):
                        self.target.edge_occupied.append(edge_type)

                # move to edge location of target and then rotate to the center of target
                self.agent.rotate = angle([1, 0], np.array(self.agent.belief.get(self.target).position) - np.array(self.agent.position)) / 180
                self.agent.attention = self.agent.rotate

                update_holding_position_rotate(self.agent, W)
            else:
                # todo: give feedbacks to the agent
                pass

        else:  # might be a location
            print(f"ActionMoveTo: {self.target}, {self.agent.position}")
            self.agent.rotate = angle([1, 0], np.array(self.target) - np.array(self.agent.position)) / 180
            self.agent.attention = self.agent.rotate
            self.agent.position = self.target
            update_holding_position_rotate(self.agent, W)

class ActionMoveToAttention(Action):
    def __init__(self, agent, target):
        super(ActionMoveToAttention, self).__init__(agent, target)

    def name(self):
        return ['ActionMoveToAttention', str(self.agent_id), str(self.target_id)]

    def execute(self, W):

        if isinstance(self.target, Agent):
            # check if the agent is in the agent's belief
            # if core.check_fn.pure_belief_position_check(self.agent, self.target, W):
            if self.agent.playing_object_id is not None:
                W.retrieve_by_id(self.agent.playing_object_id).player_num -= 1
                self.agent.playing_object_id = None
            else:
                self.agent.position = attention_location(self.target)
                self.agent.rotate = angle([1, 0], - np.array(self.agent.position) + np.array(
                    self.target.position)) / 180
                self.agent.attention = self.agent.rotate
            update_holding_position_rotate(self.agent, W)

        else:  # might be a location
            self.agent.position = self.target
            update_holding_position_rotate(self.agent, W)


class ActionFollowGaze(Action):
    def __init__(self, agent, target):
        super(ActionFollowGaze, self).__init__(agent, target)

    def name(self):
        return ['ActionFollowGaze', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        fix_position = attention_location(self.target, 300)
        self.agent.rotate = angle([1, 0], fix_position - self.agent.position) / 180
        self.agent.attention = self.agent.rotate
        update_holding_position_rotate(self.agent, W)


class ActionRotateTo(Action):
    def __init__(self, agent, target):
        if target is None:
            target = SEARCH
        if isinstance(target, str) and 'explore' in target.lower():
            target = EXPLORE
        super(ActionRotateTo, self).__init__(agent, target)

    def name(self):
        if self.target == EXPLORE:
            # print('Agent {}, ActionRotateTo, SEARCH'.format(self.agent.id))
            return ['ActionRotateTo', str(self.agent_id), '-1']
        elif isinstance(self.target, Entity):
            # print('Agent {}, ActionRotateTo, Target {}'.format(self.agent.id, self.target.id))
            return ['ActionRotateTo', str(self.agent_id), str(self.target_id)]
        elif self.target is not None:
            # print('Agent {}, ActionRotateTo, Angle {}'.format(self.agent.id, self.target))
            # print(['ActionRotateTo', str(self.agent_id), str(self.target)])
            return ['ActionRotateTo', str(self.agent_id), str(self.target)]

    def execute(self, W):
        if self.target == SEARCH:
            # todo
            # todo: change to a better implement -- turn right for a fixed angle...
            self.agent.rotate += random.uniform(-0.1, 0.2)
            # print('Searching....random sampled rotation angle is {}'.format(self.agent.rotate))

            # normalize to [-1, 1]
            if self.agent.rotate > 1:
                self.agent.rotate = -(2 - self.agent.rotate)
            if self.agent.rotate < -1:
                self.agent.rotate = 2 + self.agent.rotate

            self.agent.attention = self.agent.rotate
        elif isinstance(self.target, Entity):
            # the agent has to move to the position of the target in his belief!
            # then, what if he moves to a wrong place and found nothing? how to check the after-effect?
            if core.check_fn.pure_belief_position_check(self.agent, self.target, W):
                self.agent.rotate = angle([1, 0], np.array(self.agent.belief.get(self.target).position) - np.array(
                    self.agent.position)) / 180
                self.agent.attention = self.agent.rotate
                update_holding_position_rotate(self.agent, W)
            else:
                # tode: give feedbacks to the agent
                raise RuntimeError(f"ActionRotateTo: I can not find the target {self.target.id}. Exploration may help.")
        elif isinstance(self.target, (list, tuple)) and len(self.target) == 2:
            self.agent.rotate = angle([1, 0], np.array(self.target) - np.array(self.agent.position)) / 180
            self.agent.attention = self.agent.rotate
            update_holding_position_rotate(self.agent, W)
        else:   # might be an angle
            self.agent.rotate = self.target
            self.agent.attention = self.agent.rotate
            update_holding_position_rotate(self.agent, W)


# happens in the planing of `check intent`, target must retrieve from the world
class ActionCheckWaving(Action):
    def __init__(self, agent, target):
        super(ActionCheckWaving, self).__init__(agent, target)

    def name(self):
        if self.target is None:
            return ['ActionCheckWaving', str(self.agent_id), str(self.target)]
        return ['ActionCheckWaving', str(self.agent_id), str(self.target.id)]

    def execute(self, W):
        self.agent.rotate = angle([1, 0], np.array(self.target.position) - np.array(self.agent.position)) / 180
        self.agent.attention = self.agent.rotate
        update_holding_position_rotate(self.agent, W)


class ActionObserveAgent(Action):
    """
    this action happens keep gazing at agent or object, follow its moving in WORLD not mind/belief
    so the target has to be retrieved from the world
    """

    def __init__(self, agent, target):
        super(ActionObserveAgent, self).__init__(agent, target)

    def name(self):
        # print('Agent {}, ActionGazeAt, Target {}'.format(self.agent.id, self.target.id))
        if isinstance(self.target, Entity):
            return ['ActionObserveAgent', str(self.agent_id), str(self.target_id)]
        else:
            return ['ActionObserveAgent', str(self.agent_id), str(self.target)]

    def execute(self, W):
        if isinstance(self.target, Entity):
            self.agent.attention = angle(
                [1, 0], np.asarray(self.target.position) - np.asarray(self.agent.position)) / 180
            self.agent.rotate = self.agent.attention
        else:  # might be an angle
            self.agent.attention = self.target
            self.agent.rotate = self.agent.attention
        update_holding_position_rotate(self.agent, W)


class ActionFollowPointing(Action):
    # 当其他人在point时，可以选择follow其point，此时动作发起者会随着pointing看向被指的对象
    def __init__(self, agent, target):
        super(ActionFollowPointing, self).__init__(agent, target)

    def name(self):
        return ["ActionFollowPointing", str(self.agent.id), str(self.target.id)]

    def execute(self, W):
        # ActionPointTo, sb, item
        item = W.retrieve_by_id(self.target.pointing)
        # using ActionCheckWaving to avoid belief check in ActionRotateTo
        temp_action = ActionCheckWaving(self.agent, item)
        temp_action.execute(W)


class ActionGrab(Action):
    def __init__(self, agent, target, where=None):
        super(ActionGrab, self).__init__(agent, target)
        self.where = where
        if not isinstance(target, Object):
            raise ValueError(f"Wrong target! {target}")

    def name(self):
        if self.where is not None:
            return ['ActionGrab', str(self.agent_id), str(self.target_id), str(self.where.id)]
        else:
            return ['ActionGrab', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        if not (self.agent.attention_check(self.target, W) == 1) and not self.agent.is_in_contact(self.target, W):
            raise RuntimeError("Cannot grab the target without attention towards it!")
        elif not self.agent.reachable_check(self.target, W, offset=20):
            raise RuntimeError(f"{self.agent.name}({self.agent.position}:{self.agent.attention}) Cannot grab the target {self.target.name}({self.target.position}) out of reachable range!")
        elif len(self.target.being_contained) > 0 and not W.retrieve_by_id(self.target.being_contained[0]).open:
            raise RuntimeError(f"{self.agent.name} Cannot grab the target {self.target.name} when it is in a closed container!")
        elif self.target.is_broken:
            raise RuntimeError(f"{self.agent.name} Cannot grab the target {self.target.name} when it is broken!")
        else:
            if self.where is None:
                self.agent.holding_ids.append(self.target.id)
                # self.agent.update_holding_entities(W)
                # self.target.being_held_id.append(self.agent.id)
                if len(self.target.being_held_id) > 0:
                    for being_held_id in self.target.being_held_id:
                        being_held_entity = W.retrieve_by_id(being_held_id)
                        if isinstance(being_held_entity, Agent):
                            assert self.target.id in being_held_entity.holding_ids
                            being_held_entity.holding_ids.remove(
                                self.target.id)
                        if isinstance(being_held_entity, Object):
                            assert self.target.id in being_held_entity.containing
                            being_held_entity.containing.remove(self.target.id)
                self.target.being_held_id = [self.agent.id]
                self.target.being_contained = []
                self.target.update_being_held_entity(W)
                # WARNING: NOT DEEP COPY
                # self.target.position = self.agent.position
                # self.target.position = agent_left_with_offset(self.agent, self.target)
                self.target.position = agent_left_upper_with_offset(self.agent, self.target)
                self.target.rotate = self.agent.rotate
                self.target.attention = self.agent.attention
            elif isinstance(self.where, Agent):
                assert self.target.id in self.where.holding_ids
                # todo: require before direcly take ?
                self.agent.holding_ids.append(self.target.id)
                # self.agent.update_holding_entities(W)
                # WARNING: NOT DEEP COPY
                # self.target.position = self.agent.position
                self.target.position = agent_left_upper_with_offset(self.agent, self.target)
                self.target.rotate = self.agent.rotate
                self.target.attention = self.agent.attention
                self.target.being_held_id.remove(self.where.id)
                self.target.being_held_id.append(self.agent.id)
                self.target.being_contained = []
                self.target.update_being_held_entity(W)
                self.where.holding_ids.remove(self.target.id)
                # self.where.update_holding_entities(W)
            elif isinstance(self.where, Object):
                assert self.target.id in self.where.containing
                # todo: require before direcly take ?
                self.agent.holding_ids.append(self.target.id)
                # self.agent.update_holding_entities(W)
                # WARNING: NOT DEEP COPY
                # self.target.position = self.agent.position
                self.target.position = agent_left_upper_with_offset(self.agent, self.target)
                self.target.rotate = self.agent.rotate
                self.target.attention = self.agent.attention
                self.target.being_held_id.remove(self.where.id)
                self.target.being_held_id.append(self.agent.id)
                self.target.update_being_held_entity(W)
                self.where.containing.remove(self.target.id)
                self.target.being_contained = []
                # self.where.update_holding_entities(W)
        
        # 0930, 
        if hasattr(self.target, 'is_container') and self.target.is_container:
            for obj_id in self.target.containing:
                obj = W.retrieve_by_id(obj_id)
                obj.position = self.target.position
                obj.rotate = self.target.rotate

class ActionPutDown(Action):
    def __init__(self, agent, target):
        super(ActionPutDown, self).__init__(agent, target)
        if not isinstance(target, Object):
            raise ValueError("Wrong target")

    def name(self):
        # print('Agent {}, ActionPutDown, Target {}'.format(self.agent.id, self.target.id))
        return ['ActionPutDown', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        if not self.target.id in self.agent.holding_ids:
            raise RuntimeError("Cannot putdown the target when not holding it!")
        self.agent.holding_ids.remove(self.target.id)
        if self.agent.hands_occupied and len(self.agent.holding_ids) == 0:
            self.agent.hands_occupied = False
        # self.target.rotate = 0.5
        self.target.being_held_id.remove(self.agent.id)
        # self.target.position = agent_left_with_offset(self.agent, self.target, more=self.target.size[0])


class ActionPutOnto(Action):
    def __init__(self, agent, target, destination):
        super(ActionPutOnto, self).__init__(agent, target)
        self.destination = destination
        if not isinstance(target, Object):
            raise ValueError("Wrong target")

    def name(self):
        if not self.destination or not self.destination.id:
            raise ValueError("Destination not exists")
        # print('Agent {}, ActionPutOnto, Target {}, Destination {}'.format(self.agent.id, self.target.id, self.destination.id))
        return ['ActionPutOnto', str(self.agent_id), str(self.target_id), str(self.destination.id)]

    def execute(self, W):

        if not self.target.id in self.agent.holding_ids:
            raise RuntimeError(
                "Cannot putdown the target when not holding it!")
        elif not self.agent.reachable_check(self.destination, W):
            raise RuntimeError(
                f"Cannot put {self.target.name}_{self.target.id} onto the {self.destination.name}_{self.destination.id} out of reachable range!")
        else:
            self.agent.holding_ids.remove(self.target.id)
            # self.agent.rotate = angle([1, 0], np.array(self.destination.position) - np.array(self.agent.position)) / 180
            # self.agent.attention = self.agent.rotate
            self.destination.supporting_ids.append(self.target.id)
            # self.agent.update_holding_entities(W)
            # upper center
            self.target.being_held_id = []
            self.target.position = np.asarray([self.destination.position[0],
                                               self.destination.position[1] + self.destination.size[1]//3 + self.target.size[1]//2])
            self.target.rotate = 0.5
            # put down into a cabinet? need further modification


class ActionUnlock(Action):
    def __init__(self, agent, target):
        # destination = -1 means put onto the ground, now in action put down
        super(ActionUnlock, self).__init__(agent, target)
        if not isinstance(target, Object):
            raise ValueError("Wrong target")

    def name(self):
        # print('Agent {}, ActionPutOnto, Target {}, Destination {}'.format(self.agent.id, self.target.id, self.destination.id))
        return ['ActionUnlock', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        def holding_a_key(agent):
            for holding_id in agent.holding_ids:
                if W.retrieve_by_id(holding_id).is_key:
                    return True, holding_id
            return False, None
        flag, key_id = holding_a_key(self.agent)
        if not flag:
            raise RuntimeError("Cannot unlock the target when not holding a key!")
        key = W.retrieve_by_id(key_id)
        self.agent.holding_ids.remove(key_id)

        # fixme
        key.hidden = True

        key.being_held_id = []
        key.rotate = 0.5
        key.position = np.asarray([self.target.position[0] + self.target.size[0]/3, self.target.position[1]])
        self.target.locked = False


class ActionPutInto(Action):
    def __init__(self, agent, target, destination):
        super(ActionPutInto, self).__init__(agent, target)
        self.destination = destination

    def name(self):
        # print('Agent {}, ActionPutInto, Target {}, Destination {}'.format(self.agent.id, self.target.id, self.destination.id))
        return ['ActionPutInto', str(self.agent_id), str(self.target_id), str(self.destination.id)]

    def execute(self, W):
        # todo
        # self.target = self.agent.belief.get_by_id(self.target)
        # self.destination = self.agent.belief.get_by_id(self.destination)

        if not self.destination.is_container:
            # print(self.destination.id)
            # print(self.destination.is_container)
            raise RuntimeError("Not a container! Cannot put into it!")
        elif not self.destination.open:
            raise RuntimeError("The container is closed! Cannot put into it!")
        elif self.target.id not in self.agent.holding_ids:
            raise RuntimeError("Not holding the target!")
        elif not self.agent.reachable_check(self.destination, W):
            raise RuntimeError(f"Cannot put {self.target.name}_{self.target.id} into the {self.destination.name}_{self.destination.id} out of reachable range!")
        else:
            self.agent.holding_ids.remove(self.target.id)
            # self.agent.update_holding_entities(W)
            self.destination.containing.append(self.target.id)
            if 'shelf' in self.destination.name:
                # self.target.position = np.asarray([self.destination.position[0],
                #                                    self.destination.position[1] - self.destination.size[1]//4])
                self.target.position = rel_pos_in_shelf(self.destination, self.target)
            else:
                self.target.position = self.destination.position
            self.target.rotate = self.destination.rotate
            self.target.being_held_id.remove(self.agent.id)
            self.target.update_being_held_entity(W)
            self.target.being_contained.append(self.destination.id)
            if len(self.agent.holding_ids) == 0 and self.agent.hands_occupied:
                self.agent.hands_occupied = False
            # todo: visible or not?
            # todo: how to distinguish onto and into?
            # todo: object.contained_by


class ActionGiveTo(Action):
    def __init__(self, agent, target, destination):
        super(ActionGiveTo, self).__init__(agent, target)
        self.destination = destination

    def name(self):
        # print('Agent {}, ActionGive, Target {}, Destination {}'.format(self.agent.id, self.target.id, self.destination.id))

        return ['ActionGiveTo', str(self.agent_id), str(self.target_id), str(self.destination.id)]

    def execute(self, W):
        if not isinstance(self.destination, Agent):
            raise RuntimeError("Not an agent! Must give sth to sb!")
        elif self.target.id not in self.agent.holding_ids:
            raise RuntimeError(f"Not holding the {self.target.name}_{self.target.id}!")
        elif not self.agent.reachable_check(self.destination, W):
            raise RuntimeError(f"Cannot give {self.target.name}_{self.target.id} to {self.destination.name}_{self.destination.id} out of reachable range!")
        else:
            if self.target.id in self.agent.holding_ids:
                self.agent.holding_ids.remove(self.target.id)
                # self.agent.update_holding_entities(W)
                self.destination.holding_ids.append(self.target.id)
                # self.destination.update_holding_entities(W)
                self.target.rotate = self.destination.rotate
                # self.target.position = self.destination.position
                # self.target.position = agent_left_with_offset(self.destination, self.target)
                self.target.position = agent_left_upper_with_offset(self.destination, self.target)
                self.target.being_held_id.remove(self.agent.id)
                self.target.being_held_id.append(self.destination.id)
                self.target.update_being_held_entity(W)
            else:
                log.info("{} not held by {}".format(self.target.id, self.agent.id))
            # todo: visible or not?
            # todo: how to distinguish onto and into?
            # todo: object.contained_by


class ActionPointTo(Action):
    def __init__(self, agent, target):
        super(ActionPointTo, self).__init__(agent, target)

    def name(self):
        if self.target == STOP:
            # print('Agent {}, ActionPointTo, STOP'.format(self.agent.id))
            return ['ActionPointTo', str(self.agent_id), '-1']

        else:
            # print('Agent {}, ActionPointTo, Target {}'.format(self.agent.id, self.target.id))
            return ['ActionPointTo', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        # fixme, 0826, temporality bug fix, ActionWaveHand(stop)
        # if self.agent.waving:
        #     self.agent.waving = None
        if self.target == STOP:
            self.agent.pointing = None
        elif isinstance(self.target, Entity):
            if not self.agent.belief.check(self.target):
                raise RuntimeError(
                    "The target is not in the agent's belief! Cannot point to the target!")
            else:
                # todo: false belief problem here, but we only record id, which might not be enough!
                self.agent.pointing = self.target.id
        else:
            raise NotImplementedError()


# class ActionSpeak(Action):
#     def __init__(self, agent, target):
#         super(ActionSpeak, self).__init__(agent, target)
#
#     def name(self):
#         if self.target == STOP:
#             # print('Agent {}, ActionSpeak, STOP'.format(self.agent.id))
#             return ['ActionSpeak', str(self.agent_id), '-1']
#         else:
#             # print('Agent {}, ActionSpeak, Target {}'.format(self.agent.id, self.target.id))
#             return ['ActionSpeak', str(self.agent_id), str(self.target_id)]
#
#     def execute(self, W):
#         # todo: change the speaking state here!
#         if self.target == STOP:
#             self.agent.speaking = None
#         else:
#             self.agent.speaking = self.target


# todo: how to stop the action state after executing?
class ActionHit(Action):
    def __init__(self, agent, target):
        super(ActionHit, self).__init__(agent, target)

    def name(self):
        if self.target == STOP:
            # print('Agent {}, ActionHit, STOP'.format(self.agent.id))
            return ['ActionHit', str(self.agent_id), '-1']
        else:
            # print('Agent {}, ActionHit, Target {}'.format(self.agent.id, self.target.id))
            return ['ActionHit', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        if self.target == STOP:
            self.agent.hitting = None
        elif not self.agent.attention_check(self.target, W):
            raise RuntimeError(
                "Cannot hit the target without attention towards it!")
        else:
            self.agent.hitting = self.target.id


class ActionNodHead(Action):
    def __init__(self, agent, target=None):
        super(ActionNodHead, self).__init__(agent, target)
        self.agent = agent
        self.target = target

    def name(self):
        if self.target == STOP:
            # print('Agent {}, ActionNodHead, STOP'.format(self.agent.id))
            return ['ActionNodHead', str(self.agent_id), '-1']
        else:
            # print('Agent {}, ActionNodHead, Target {}'.format(self.agent.id, self.target.id))
            return ['ActionNodHead', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        if self.target == STOP:
            self.agent.nodding = False
        else:
            self.agent.nodding = True


class ActionShakeHead(Action):
    def __init__(self, agent, target=None):
        super(ActionShakeHead, self).__init__(agent, target)
        self.agent = agent
        self.target = target

    def name(self):
        if self.target == STOP:
            # print('Agent {}, ActionShakeHead, STOP'.format(self.agent.id))
            return ['ActionShakeHead', str(self.agent_id), '-1']
        else:
            # print('Agent {}, ActionShakeHead, Target {}'.format(self.agent.id, self.target.id))
            return ['ActionShakeHead', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        if self.target == STOP:
            self.agent.shaking = False
        else:
            self.agent.shaking = True


class ActionWaveHand(Action):
    def __init__(self, agent, target=None):
        super(ActionWaveHand, self).__init__(agent, target)

    def name(self):
        if self.target == STOP:
            # print('Agent {}, ActionWaveHand, STOP'.format(self.agent.id))
            return ['ActionWaveHand', str(self.agent_id), '-1']
        else:
            # print('Agent {}, ActionWaveHand, Target {}'.format(self.agent.id, self.target.id))
            return ['ActionWaveHand', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        if self.target == STOP:
            self.agent.waving = False
        else:
            self.agent.waving = True


# todo: holding check....
class ActionOpen(Action):
    def __init__(self, agent, target):
        super(ActionOpen, self).__init__(agent, target)

    def name(self):
        # print('Agent {}, ActionOpen, Target {}'.format(self.agent.id, self.target.id))
        return ['ActionOpen', str(self.agent_id), str(self.target_id)]

    def execute(self, W):

        if not self.agent.belief.check(self.target):
            raise RuntimeError(
                "The target is not in the agent's belief! Cannot open the target!")
        elif not self.agent.reachable_check(self.target, W):
            raise RuntimeError(
                f"Cannot open the {self.target.name}_{self.target.id} out of reachable range!")
        else:
            # cannot adopt to the case of put_into sth sw.
            # if the agent have something in hands, it can not open
            # if len(self.agent.holding_ids):
            #     self.agent.action_fail = True
            if self.target.locked:
                if not self.agent.holding_ids:
                    raise RuntimeError("You need a key to unlock the target before opening it!")
                # check if the key is in the agent's holding_ids
                for id in self.agent.holding_ids:
                    if W.retrieve_by_id(id).name == "key":
                        raise RuntimeError("You need to unlock the target first!")
                    else:
                        raise RuntimeError("You need a key to unlock the target before opening it!")
            self.target.open = True
        # assert object type
        # check the open state before action


class ActionClose(Action):
    def __init__(self, agent, target):
        super(ActionClose, self).__init__(agent, target)

    def name(self):
        # print('Agent {}, ActionClose, Target {}'.format(self.agent.id, self.target.id))
        return ['ActionClose', str(self.agent_id), str(self.target_id)]

    def execute(self, W):

        if not self.agent.belief.check(self.target):
            raise RuntimeError(
                "The target is not in the agent's belief! Cannot close the target!")
        elif not self.agent.reachable_check(self.target, W):
            raise RuntimeError(
                f"Cannot close the {self.target.name}_{self.target.id} out of reachable range!")
        else:
            # cannot adopt to the case of put_into sth sw.
            # if the agent have something in hands, it can not open
            # if len(self.agent.holding_ids):
            #     self.agent.action_fail = True
            self.target.open = False
        # assert object type
        # check the open state before action


class ActionPlay(Action):
    def __init__(self, agent, target, agent_with=None):
        super(ActionPlay, self).__init__(agent, target)
        self.agent_with = agent_with

    def name(self):
        # print('Agent {}, ActionPlay, Target {}'.format(self.agent.id, self.target.id))
        if isinstance(self.agent_with, Agent):
            return ['ActionPlay', str(self.agent_id), str(self.target_id), str(self.agent_with.id)]
        else:
            return ['ActionPlay', str(self.agent_id), str(self.target_id)]

    def execute(self, W):
        if not self.agent.belief.check(self.target):
            raise RuntimeError(
                "The target is not in the agent's belief! Cannot play the target! Re-reasoning again and then output JSON format information as required! ")
        elif not self.agent.reachable_check(self.target, W, offset=20):
            raise RuntimeError(
                "Cannot play the target out of reachable range! Re-reasoning again and then output JSON format information as required! ")
        else:
            self.agent.playing = self.target.id
            if not self.target.being_played:
                self.target.being_played = self.agent.id
            else:
                if self.agent.id != self.target.being_played:
                    self.target.being_multi_played = self.agent.id


class ActionWait(Action):
    def __init__(self, agent, target=None):
        super(ActionWait, self).__init__(agent, target)

    def name(self):
        return ['ActionWait', str(self.agent_id)]

    def execute(self, W):
        # change nothing
        pass


class ActionEat(Action):
    def __init__(self, agent, target):
        super().__init__(agent, target)

    def name(self):
        return ['ActionEat', str(self.agent_id), str(self.target_id)]
    
    def execute(self, W):
        # 在所有地方去除目标物体
        if not self.agent.reachable_check(self.target, W):
            raise RuntimeError(
                f"Cannot eat the {self.target.name}_{self.target.id} out of reachable range!")
        elif not "banana" in self.target.name:
            raise RuntimeError(
                f"Cannot eat the {self.target.name}_{self.target.id}")
        else:
            if not self.agent.is_holding(self.target):
                raise RuntimeError(
                f"You need to pick up {self.target.name}_{self.target.id} first before eating it")
            self.agent.eating = self.target
            # delete object
            # obj in world
            W.delete_obj(self.target)
            # obj in belief
            # todo 0823 会有 belief update 的问题，如果这里不这么 hack 处理，又会导致 world 很多的成员函数取值都会出错
            for agent_tmp in W.agents:
                agent_tmp.belief.del_objects([self.target.id])
            self.agent.put_down(self.target)
            pass


class ActionSmash(Action):
    def __init__(self, agent, target):
        super().__init__(agent, target)

    def name(self):
        return ['ActionSmash', str(self.agent_id), str(self.target_id)]
    
    def execute(self, W):
        # 在所有地方去除目标物体
        if not self.agent.reachable_check(self.target, W):
            raise RuntimeError(
                f"Cannot smash the {self.target.name}_{self.target.id} out of reachable range!")
        elif not "cup" in self.target.name:
            raise RuntimeError(
                f"Cannot smash the {self.target.name}_{self.target.id}")
        else:
            self.target.is_broken = True
            # todo
            self.agent.belief.get(self.target.id).is_broken = True
            # 水杯离开手里
            self.agent.put_down(self.target)
            pass


class ActionSpeak(Action):
    def __init__(self, agent, target):
        super().__init__(agent, target)

    def name(self):
        return ['ActionSpeak', str(self.agent_id), str(self.target)]
    
    def execute(self, W):
        self.agent.speaking = self.target


class ActionPerform(Action):
    def __init__(self, agent, target):
        # 0619 target can only be "drink" or "eat"
        super().__init__(agent, target)

    def name(self):
        return ['ActionPerform', str(self.agent_id), str(self.target)]
    
    def execute(self, W):
        self.agent.performing = self.target

class ActionExplore(Action):
    def __init__(self, agent, target=None, args=None):
        super(ActionExplore, self).__init__(agent, target)
        self.args = args

    def name(self):
        # print('Agent {}, ActionPlay, Target {}'.format(self.agent.id, self.target.id))
        return ['ActionExplore', str(self.agent.id)]

    def execute(self, W):

        if self.args and self.args.scenario == "classroom":
            # todo: 教室里面不能随意走动
            self.fixed_rotate(W)
        # if no any landmark in belief, then agent doesn't need to move to explore
        elif len(self.agent.belief.landmarks) == 0:
            self.fixed_rotate(W)
        elif self.agent.intent_now is not None and self.agent.intent_now.soc_intent is not None and self.agent.intent_now.soc_intent[0] == 'request_help':
            self.fixed_rotate(W)
        else:
            self.check_behind(W)

    def fixed_rotate(self, W):

        self.agent.rotate += ATTENTION_RADIUS
        if self.agent.rotate > 1:
            self.agent.rotate = -(2 - self.agent.rotate)
        if self.agent.rotate < -1:
            self.agent.rotate = 2 + self.agent.rotate
        self.agent.attention = self.agent.rotate
        update_holding_position_rotate(self.agent, W)

    def check_behind(self, W):

        if random.randint(1, 5) != 1:
            # probability 4/5 = 80%
            # only rotate
            self.fixed_rotate(W)
        else:
            # probability 1/5 = 20%
            # move (and also decide the rotate)'
            # move to the behind of a landmark, only support one landmark
            landmark = self.agent.belief.landmarks[0]
            rand = random.random()
            tmp_pos = -rand * self.agent.position + (1 + rand) * landmark.position
            while not W.position_available_check(tmp_pos):
                # print(rand, self.agent.position, landmark.position, tmp_pos)
                rand = random.random()
                tmp_pos = -rand * self.agent.position + (1 + rand) * landmark.position
            self.agent.rotate = angle([1, 0], np.array(
                tmp_pos) - np.array(self.agent.position)) / 180
            self.agent.attention = self.agent.rotate
            for i in range(len(tmp_pos)):
                self.agent.position[i] = tmp_pos[i]
            update_holding_position_rotate(self.agent, W)

# Pure means that the check_fn does not involve the action
# Check for planning, but not action
def pure_belief_position_check(agent_input, target_input, W):
    # 判断是否 target 在 agent 的 belief 中
    # 如果在，返回 True，否则返回 False
    agent = None
    target = None

    # if the agent is agent's id
    if isinstance(agent_input, int):
        agent = W.retrieve_by_id(agent_input)
    elif isinstance(agent_input, Agent):
        agent = agent_input

    if isinstance(target_input, int):
        target = W.retrieve_by_id(target_input)
    elif isinstance(target_input, Entity):
        target = target_input

    if agent is None or target is None:
        return False
    
    if not agent.belief.check(target):
        return False
    elif agent.belief.get(target).position is None:
        return False
    
    return True
