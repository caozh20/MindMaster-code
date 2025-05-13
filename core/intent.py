import os
import sys
import os.path as osp
import random
import argparse
import matplotlib.pyplot as plt
import scipy.stats
import numpy as np
from copy import deepcopy
import operator
from typing import List
# from memory_profiler import profile
from utils.base import log
from utils.base import dis
from core.const import REACHABLE_RADIUS, intent_prior_config_dict, IntentCategory, NEAR_DIS
from core.entity import Object
# from core.world import World
from core.agent_utils import get_entity_in_whose_mind
from core.intent_predicates import *


class Intent():
    def __init__(self, intent_pred=None):
        self.ind_intent: List = None
        # [put_onto, sth, sw]
        # [put_into, sth, sw]
        # [give, sth, to sb]
        # [get, sth, from sw]
        # [find, sth]
        # [move_to, sw]
        # [open, sth]
        # [play, sth]
        # [check, sw]
        # [confirm, sb]
        # [attract, sb]: deprecated, contained by referring task
        # [follow, sb, sth]: newly added 20220831
        # [explore]

        if intent_pred is None:
            self.intent_pred = default_intent_pred
        else:
            self.intent_pred = intent_pred

        self.soc_intent: List = None
        # want R do  -- request help
        # want R know  -- seems like this one is the "help" one..
        # want R share  -- cooperate

        # ["help", sb_id, intent()]
        # ["harm", sb_id, intent()]
        # ["request_help", sb_id, intent()]
        # todo: 这些是直接用intent()呢?还是直接写ind_intent?
        # ["share", sb_id, sth_id] #todo：注意区分share和inform，这里的share是类似于分享食物的意思
        # ["inform", sb_id, sth_id]
        # ["play_with", sb_id, sth_id]

        self.comm_intent = None
        # want R know social intent  -- "for you" signals
        # [sb_id, soc_intent()]

        self.ref_intent = None
        # want R attend to -- point to
        # [sb_id, attend to sth_id, and sth_id]

    def env_constraint(self):
        pass

    def update(self, desire, C):
        # C is indicated in the configuration file,
        pass

    def print(self):

        tmp = ""
        if self.ind_intent is not None:
            tmp += " Ind_intent: " + \
                " ".join([str(e) for e in self.ind_intent])
        if self.soc_intent is not None:
            if self.soc_intent[0] == "request_help" or self.soc_intent[0] == "help":
                tmp += " Soc_intent: " + \
                    " ".join([str(e) for e in self.soc_intent[:2]])
                tmp += self.soc_intent[2].print()
            else:
                tmp += " Soc_intent: " + \
                    " ".join([str(e) for e in self.soc_intent])
        if self.comm_intent is not None:
            tmp += " Comm_intent: " + \
                " ".join([str(e) for e in self.comm_intent])
        if self.ref_intent is not None:
            tmp += " Ref_intent: " + \
                " ".join([str(e) for e in self.ref_intent])
        return tmp

    def category(self):
        if self.ref_intent is not None:
            return "ref"
        elif self.soc_intent is not None:
            return self.soc_intent[0]
        elif self.ind_intent is not None:
            return self.ind_intent[0]
        else:
            return "None"

    def intent_related_ids(self):
        related_ids = []
        if self.ind_intent is not None:
            for int_id in self.ind_intent:
                if isinstance(int_id, int):
                    related_ids.append(int_id)
        if self.ref_intent is not None:
            for int_id in self.ref_intent:
                if isinstance(int_id, int):
                    related_ids.append(int_id)
        if self.comm_intent is not None:
            for int_id in self.comm_intent:
                if isinstance(int_id, int):
                    related_ids.append(int_id)
        if self.soc_intent is not None:
            for int_id in self.soc_intent:
                if isinstance(int_id, int):
                    related_ids.append(int_id)
                if isinstance(int_id, Intent):
                    related_ids.extend(int_id.intent_related_ids())
        # print('intent_related_ids:', related_ids)
        return list(set(related_ids))

    def __call__(self):
        return {"ind_intent": self.ind_intent, "social_intent": self.soc_intent, "comm_intent": self.comm_intent,
                "ref_intent": self.ref_intent}
    
    def to_scenario_name(self, agent_id):
        # 将intent转变为scenario name
        if self.soc_intent is not None:
            if isinstance(self.soc_intent[2], Intent):
                help_intent = self.soc_intent[2]
                intent_prefix = f"{agent_id}_{self.soc_intent[0]}_{self.soc_intent[1]}"
                for i in range(len(help_intent)):
                    intent_prefix += f"_{help_intent[i]}"




class IntentSampler():
    def __init__(self):

        self.vpool = []

    def get_intent_index(self, prev_int):
        for i, this_int in enumerate(self.vpool):
            if same_intent(this_int, prev_int):
                return i
        return -1

    # @profile
    def valid_pool(self, agent=None, guesser=None, world=None):

        # 这里还是有问题呀！有些情况下自己也可以算是target！
        self.vpool = []

        agent_ids = guesser.belief.get_agent_ids()
        ag_ids = [id for id in agent_ids if id != agent.id]
        lm_ids = guesser.belief.get_landmark_ids()
        object_ids = guesser.belief.get_obj_ids()

        valid_pool = []

        # todo: put_into, 需要check一下是否为容器
        # ind_intent
        # for a in ["put_onto", "put_into", "give", "get", "find", "move_to", "open", "play", "check", "confirm",
        #           "attract", "explore", 'follow', 'gaze_follow']:
        for a in ["put_onto", "put_into", "give", "get", "find", "move_to", "open", "play", "respond_to",
                  "greet", "observe", "gaze_follow", "harm", "explore"]:
            
            if a in ["put_onto"]:
                for sth in object_ids:
                    obj_ids = [id for id in object_ids if id != sth]
                    for sw in (obj_ids + lm_ids):
                        sth_obj = guesser.belief.get_by_id(sth)
                        sw_obj = guesser.belief.get_by_id(sw)
                        sample = Intent()
                        sample.ind_intent = [a, sth, sw]
                        if isinstance(sth_obj, Object) and isinstance(sw_obj, Object):
                            if not put_onto_constraint_check(sample.ind_intent, sth=sth_obj, sw=sw_obj):
                                continue
                        valid_pool.append(sample)

            if a in ["put_into"]:
                for sth_id in object_ids:
                    obj_ids = [id for id in object_ids if id != sth_id]
                    sth = get_entity_in_whose_mind(sth_id, world, guesser.id)
                    for sw_id in obj_ids:
                        sample = Intent()
                        sample.ind_intent = [a, sth_id, sw_id]
                        sw = get_entity_in_whose_mind(sw_id, world, guesser.id)
                        if isinstance(sw, Object) and isinstance(sth, Object):
                            if not put_into_constraint_check(sample.ind_intent, sth=sth, sw=sw):
                                continue
                        valid_pool.append(sample)

            if a in ["get"]:
                for sth in object_ids:
                    if world.get(sth).is_container or world.get(sth).is_supporter:
                        continue
                    obj_ids = [id for id in object_ids if id != sth]
                    for sw in (obj_ids + lm_ids + ag_ids):
                        sth_obj = guesser.belief.get_by_id(sth)
                        sw_obj = guesser.belief.get_by_id(sw)
                        sample = Intent()
                        sample.ind_intent = [a, sth, sw]
                        if sth in agent.holding_ids:
                            continue
                        if not get_constraint_check(agent, sample.ind_intent, sth=sth_obj, sw=sw_obj):
                            continue
                        valid_pool.append(sample)

                    sample = Intent()
                    sample.ind_intent = [a, sth, None]
                    valid_pool.append(sample)

            elif a == "give":
                if len(object_ids) > 0 and len(ag_ids) > 0:
                    for sth in object_ids:
                        for sb in ag_ids:
                            sample = Intent()
                            sample.ind_intent = [a, sth, sb]
                            valid_pool.append(sample)

            elif a == "find":
                find_intents = []
                for sth in object_ids + ag_ids:
                    if sth not in agent.belief.get_all_ids():
                        sample = Intent()
                        sample.ind_intent = [a, sth]
                        find_intents.append(sample)
                if len(find_intents) > 0:
                    find_intents.sort(key=lambda x: dis(agent, world.get(x.ind_intent[1])), reverse=True)
                    valid_pool.append(find_intents[0])

            elif a in ["move_to", "check"]:
                if len(ag_ids + object_ids + lm_ids) > 0:
                    for sw in ag_ids + object_ids + lm_ids:
                        sample = Intent()
                        sample.ind_intent = [a, sw]
                        valid_pool.append(sample)

            elif a in ["open"]:
                for sth_id in object_ids:
                    sth = world.retrieve_by_id(sth_id)
                    sample = Intent()
                    sample.ind_intent = [a, sth_id]
                    if not open_constraint_check(sample.ind_intent, sth=sth):
                        continue
                    valid_pool.append(sample)

            elif a in ["play"]:
                for sth in object_ids:
                    sth_obj = world.retrieve_by_id(sth)
                    sample = Intent()
                    sample.ind_intent = [a, sth]
                    if not play_constraint_check(sample.ind_intent, sth=sth_obj):
                        continue
                    if sth_obj.is_game and sth_obj.is_multiplayer_game:
                        continue
                    valid_pool.append(sample)

            elif a in ["respond_to", "greet"]:
                for sb in ag_ids:
                    sample = Intent()
                    sample.ind_intent = [a, sb]
                    valid_pool.append(sample)

            elif a in ['follow']:
                for sb_id in ag_ids:
                    for sth_id in object_ids:
                        sample = Intent()
                        sample.ind_intent = [a, sb_id, sth_id]
                        valid_pool.append(sample)

            elif a in ['gaze_follow']:
                for sb_id in ag_ids:
                    sample = Intent()
                    sample.ind_intent = [a, sb_id]
                    valid_pool.append(sample)

            elif a in ['observe']:
                for sb_id in ag_ids:
                    sample = Intent()
                    sample.ind_intent = [a, sb_id]
                    valid_pool.append(sample)
                # 下文代码会处理observe world的情况，equivalent to explore
                # if len(ag_ids) == 0:
                #     sample = Intent()
                #     sample.ind_intent = [a, 'world']
                #     valid_pool.append(sample)

        self.vpool = deepcopy(valid_pool)
        # soc_intent
        for b in ["request_help"]:
            #
            for sb in ag_ids:
                for tmp in self.vpool:
                    if tmp.ind_intent[0] in ["put_onto", "put_into", "get", "give", "find", "open", "play", "attract"]:
                        sample = Intent()
                        sample.soc_intent = [b, sb, tmp]
                        if not request_help_constraint_check(sample):
                            continue
                        valid_pool.append(sample)

        for b in ["help", "harm", "share", "inform", "play_with"]:
            if b in ["help"]:
                for sb in ag_ids:
                    # print(sb)
                    # todo: check .belief.
                    if guesser.belief.get_by_id(sb).intent_now is not None:
                        _intent = guesser.belief.get_by_id(sb).intent_now

                        if _intent.ind_intent is not None and _intent.ind_intent[0] not in ["check", "confirm",
                                                                                            "explore", "follow",
                                                                                            "respond_to", "greet"]:
                            sample = Intent()
                            sample.soc_intent = [b, sb, _intent]
                            valid_pool.append(sample)

            if b in ["harm"]:
                for sb in ag_ids:
                    # todo: check .belief.
                    if guesser.belief.get_by_id(sb).intent_now is not None:
                        _intent = guesser.belief.get_by_id(sb).intent_now

                        sample = Intent()
                        sample.soc_intent = [b, sb, _intent]
                        valid_pool.append(sample)

            elif b in ["share", "inform"]:
                if len(ag_ids) > 0 and len(object_ids) > 0:
                    for sb_id in ag_ids:
                        for sth_id in object_ids:
                            sb = get_entity_in_whose_mind(sb_id, world, guesser.id)
                            sth = get_entity_in_whose_mind(sth_id, world, guesser.id)

                            if sth_id not in agent.belief.all_ids:
                                log.info("agent {} propose intent of agent {}, cannot {} {} with agent {} for belief reason".format(
                                    guesser.id, agent.id, b, sth_id, sb_id)
                                )
                                continue
                            if dis(sb, sth) <= NEAR_DIS:
                                log.info(
                                    "agent {} propose intent of agent {}, cannot {} {} with agent {} for agent {} and {} in same location".format(
                                        guesser.id, agent.id, b, sth_id, sb_id, sb_id, sth_id)
                                )
                                continue
                            sample = Intent()
                            sample.soc_intent = [b, sb_id, sth_id]
                            valid_pool.append(sample)

            elif b in ["play_with"]:
                if len(ag_ids) > 0 and len(object_ids) > 0:
                    for sth_id in object_ids:
                        sth = get_entity_in_whose_mind(sth_id, world, guesser.id)
                        if sth.is_multiplayer_game:
                            for sb_id in ag_ids:
                                sample = Intent()
                                sample.soc_intent = [b, sb_id, sth_id]
                                valid_pool.append(sample)

        self.vpool = deepcopy(valid_pool)

        # ref_intent
        for tmp in self.vpool:
            if tmp.soc_intent is not None:
                if tmp.soc_intent[0] == "share" or tmp.soc_intent[0] == "inform":
                    tmp.ref_intent = [tmp.soc_intent[1], tmp.soc_intent[2]]

        self.vpool = deepcopy(valid_pool)

        # intents without specific targets, such as [inform, sb, None]
        # for the replacement version respond-to and greet,it seems they have to have at least one object
        for a in ["confirm", "attract"]:
        # for a in ["find", "confirm", "attract"]:
            tmp = Intent()
            tmp.ind_intent = [a, None]
            self.vpool.append(tmp)

        for a in ["observe"]:
            tmp = Intent()
            tmp.ind_intent = [a, 'world']
            self.vpool.append(tmp) 
        
        # for a in ["inform"]:
        #     tmp = Intent()
        #     tmp.soc_intent = [a, None, None]
        #     self.vpool.append(tmp)

    def __call__(self):
        return random.choice(self.vpool)


# get intent base prior,
def base_intent_prior(I):
    if I.ind_intent is not None:
        return intent_prior_config_dict[IntentCategory.Ind].get(I.ind_intent[0], 0)
    if I.soc_intent is not None:
        return intent_prior_config_dict[IntentCategory.Soc].get(I.soc_intent[0], 0)
    if I.ref_intent is not None:
        return intent_prior_config_dict[IntentCategory.Ref].get('ref', 0)
    return 0


# intent prior with respect to parameter and scene: realizability
def intent_prior_wrt_para(I, W, in_whose_mind=-1):
    base_prior = base_intent_prior(I)
    update_prior = base_prior

    # affordance: find, put_onto
    if (I.ind_intent is not None and I.ind_intent[0] == 'put_onto') \
            or (I.soc_intent is not None and I.soc_intent[0] in ('help', 'request_help') and
                I.soc_intent[2].ind_intent is not None and I.soc_intent[2].ind_intent[0] == 'put_onto'):
        ind_intent = I.ind_intent if I.ind_intent is not None and I.ind_intent[
            0] == 'put_onto' else I.soc_intent[2].ind_intent
        sth_id, sw_id = ind_intent[1:]
        # sw = W.retrieve_by_id(sw_id)
        sw = get_entity_in_whose_mind(sw_id, W, in_whose_mind=in_whose_mind)
        # which means a container is less likely to be put onto
        if hasattr(sw, 'is_container') and sw.is_container:
            update_prior -= 0.5
    if (I.ind_intent is not None and I.ind_intent[0] in ['find', 'get']) \
            or (I.soc_intent is not None and I.soc_intent[0] in ('help', 'request_help') and
                I.soc_intent[2].ind_intent is not None and I.soc_intent[2].ind_intent[0] in ['find', 'get']):
        ind_intent = I.ind_intent if I.ind_intent is not None and I.ind_intent[0] in [
            'find', 'get'] else I.soc_intent[2].ind_intent
        sth_id = ind_intent[1]
        # sth = W.retrieve_by_id(sth_id)
        sth = get_entity_in_whose_mind(sth_id, W, in_whose_mind=in_whose_mind)
        # which means the sth is in hidden state
        if isinstance(sth, Object) and len(sth.being_held_id) == 0:
            update_prior -= 0.5
        if I.soc_intent is not None and I.soc_intent[0] == 'request_help' and ind_intent[0] == 'get':
            sb_id = I.soc_intent[1]
            sb = get_entity_in_whose_mind(
                sb_id, W, in_whose_mind=in_whose_mind)
            # which means sb already has the sth
            if dis(sth, sb) < 10:
                update_prior -= 0.5

    # affordance: which means a container is less likely to be moved
    if (I.ind_intent is not None and I.ind_intent[0] in ['get', 'give']) \
            or (I.soc_intent is not None and I.soc_intent[0] in ('help', 'request_help') and
                I.soc_intent[2].ind_intent is not None and I.soc_intent[2].ind_intent[0] in ['get', 'give']):
        ind_intent = I.ind_intent if I.ind_intent is not None and I.ind_intent[0] in [
            'get', 'give'] else I.soc_intent[2].ind_intent
        sth_id = ind_intent[1]
        # sth = W.retrieve_by_id(sth_id)
        sth = get_entity_in_whose_mind(sth_id, W, in_whose_mind=in_whose_mind)
        # which means the sth is in hidden state
        if isinstance(sth, Object) and sth.is_container:
            update_prior -= 0.5

    # distance
    if (I.ind_intent is not None and I.ind_intent[0] == 'put_into') \
            or (I.soc_intent is not None and I.soc_intent[0] in ('help', 'request_help') and
                I.soc_intent[2].ind_intent is not None and I.soc_intent[2].ind_intent[0] == 'put_into'):
        ind_intent = I.ind_intent if I.ind_intent is not None and I.ind_intent[
            0] == 'put_into' else I.soc_intent[2].ind_intent
        sth_id, sw_id = ind_intent[1:]
        # sth = W.retrieve_by_id(sth_id)
        sth = get_entity_in_whose_mind(sth_id, W, in_whose_mind=in_whose_mind)
        # sw = W.retrieve_by_id(sw_id)
        sw = get_entity_in_whose_mind(sw_id, W, in_whose_mind=in_whose_mind)
        # which means sth already in the sw
        if dis(sth, sw) <= 10:
            update_prior -= 0.5

    if (I.ind_intent is not None and I.ind_intent[0] == 'get') \
            or (I.soc_intent is not None and I.soc_intent[0] in ('help', 'request_help') and
                I.soc_intent[2].ind_intent is not None and I.soc_intent[2].ind_intent[0] == 'get'):
        ind_intent = I.ind_intent if I.ind_intent is not None and I.ind_intent[
            0] == 'get' else I.soc_intent[2].ind_intent
        sth_id, sw_id = ind_intent[1:]
        if sw_id is not None:
            sth = get_entity_in_whose_mind(
                sth_id, W, in_whose_mind=in_whose_mind)
            sw = get_entity_in_whose_mind(
                sw_id, W, in_whose_mind=in_whose_mind)
            if dis(sth, sw) > 200:
                update_prior -= 0.75
            elif dis(sth, sw) > 50:
                update_prior -= 0.5
            elif dis(sth, sw) > 10:
                update_prior -= 0.25

    # playable
    if I.ind_intent is not None and I.ind_intent[0] == "play":
        sth_id = I.ind_intent[1]
        if get_entity_in_whose_mind(sth_id, W, in_whose_mind=in_whose_mind).is_game:
            update_prior += 1
    if I.soc_intent is not None:
        if I.soc_intent[0] == "help" or I.soc_intent[0] == "request_help":
            help_intent = I.soc_intent[2]
            if help_intent.ind_intent is not None and help_intent.ind_intent[0] == "play":
                sth_id = help_intent.ind_intent[1]
                if get_entity_in_whose_mind(sth_id, W, in_whose_mind=in_whose_mind).is_game and not get_entity_in_whose_mind(sth_id, W, in_whose_mind=in_whose_mind).is_multiplayer_game:
                    update_prior += 1
        elif I.soc_intent[0] == "play_with":
            if get_entity_in_whose_mind(I.soc_intent[2], W, in_whose_mind=in_whose_mind).is_game:
                update_prior += 1
    return update_prior


def intent_prior(I, scenario=None):
    if scenario is None:
        if I.ind_intent is not None and I.ind_intent[0] in ["put_onto", "put_into", "get", "find", "open", "play", 'gaze_follow']:
            return 2
        elif I.ind_intent is not None and I.ind_intent[0] in ["give", "check", "confirm", "move_to", "attract", "follow"]:
            return 1
        elif I.ind_intent is not None and I.ind_intent[0] in ['explore']:
            return 0
        # `inform` prior, todo, 0321
        elif I.soc_intent is not None and I.soc_intent[0] in ["help", "request_help", "play_with", "inform"]:
            return 2
        elif I.soc_intent is not None and I.soc_intent[0] in ["share", ]:
            return 1
        elif I.soc_intent is not None and I.soc_intent[0] in ["harm"]:
            return 0
        elif I.ref_intent is not None:
            return 2
    elif scenario == "classroom":

        if I.ind_intent is not None and I.ind_intent[0] in ["put_onto", "put_into", "get", "find", "move_to", "open",
                                                            "play"]:
            return 1
        if I.ind_intent is not None and I.ind_intent[0] in ["attract"]:
            return 2
        elif I.ind_intent is not None and I.ind_intent[0] in ["give", "check", "confirm", "explore"]:
            return 1
        elif I.soc_intent is not None and I.soc_intent[0] in ["help", "inform"]:
            return 2
        elif I.soc_intent is not None and I.soc_intent[0] in ["share", ]:
            return 1
        elif I.soc_intent is not None and I.soc_intent[0] in ["harm"]:
            return 0
        elif I.ref_intent is not None:
            return 2
    # elif scenario == 'chimpanzee':
    #     if I.soc_intent is not None and I.soc_intent[0] in ["request_help"] and I.soc_intent[2].ind_intent[0] in [
    #             "open"]:
    #         return 3
    #     if I.ind_intent is not None and I.ind_intent[0] in ["open"]:
    #         return 5
    #     else:
    #         return 1


def intent_LLScore(action_csq, action_hist):

    # if action is not None and action.name() in action_hist:
    #     indices = [i for i, x in enumerate(action_hist) if x == action.name()]
    #     L=len(action_hist)
    #     r=L*(L-1)/2.
    #     return len(indices)/len(action_hist) + (np.sum(indices)/(r+0.0000001))
    # else:
    #     return 0

    L = len(action_hist)
    r = L * (L - 1) / 2.

    # todo: do we need to normalize the score here?
    score = 0.
    for action in action_csq:
        if action[0] == 'ActionRotateTo' and action[-1] == '-1':
            indices = [i for i, x in enumerate(action_hist) if x == action]
            score += 1*(len(indices)/L + (np.sum(indices)/(r + 0.0000001)))
        elif action[0] == 'ActionRotateTo' and action[-1] != '-1':
            indices = [i for i, x in enumerate(action_hist) if x == action]
            score += 1.2*(len(indices) / L +
                          (np.sum(indices) / (r + 0.0000001)))
        else:
            indices = [i for i, x in enumerate(action_hist) if x == action]
            score += 1.5*(len(indices) / L +
                          (np.sum(indices) / (r + 0.0000001)))
    return score/(len(action_csq)+0.0000001)


def rindex(lst, value):
    return len(lst) - operator.indexOf(reversed(lst), value) - 1


def intent_LLScore_v2(action_csq, action_hist, intent=None, W=None):

    action_score = 0
    hoi_score = 0

    # action term
    L = len(action_hist)

    # count from 0
    # r = L * (L - 1) / 2.

    # count from 1
    r = L * (L + 1) / 2.

    if L == 0 or len(action_csq) == 0:
        # log.info("intent {} has no action plan!".format(intent.print()))
        # return 0
        return -L
    obs_indices = []
    penalty = 0
    csq_indices = []
    csq_before_this_action = action_csq
    for i, obs_action in enumerate(action_hist[::-1]):
        csq_index = -1
        try:
            csq_index = rindex(csq_before_this_action, obs_action[:-1])
        except:
            # log.info("the observed action({}) doesn't appear in the planning csq of intent({})".format(obs_action, intent.print()))
            pass

        # count from 0
        # obs_action_index = L - i - 1

        # count from 1
        obs_action_index = L - i

        if csq_index != -1:
            obs_indices.insert(0, obs_action_index)
            csq_indices.insert(0, csq_index)
            csq_before_this_action = csq_before_this_action[:csq_index]
        else:
            penalty += -obs_action_index
    # l/L + s/S
    # action_score = len(csq_indices)/L + sum(csq_indices) / (r + 0.0000001)
    action_score = len(obs_indices)/L + \
        (sum(obs_indices) + penalty/2.) / (r + 0.0000001)
    # return sum(obs_indices) / (r + 0.0000001)
    # return len(obs_indices)/L + sum(obs_indices) / (r*L + 0.0000001)

    # return action_score
    # return action_score * len(action_hist) / len(action_csq)
    return action_score + len(obs_indices) * 1. / len(action_csq)


def same_intent(I1, I2):
    assert isinstance(I1, Intent)
    assert isinstance(I2, Intent)
    if (I1.soc_intent is None and I2.soc_intent is not None) or (I1.soc_intent is not None and I2.soc_intent is None):
        return False
    # running here means, (I1.soc_intent is None or I2.soc_intent is None) or (I1.soc_intent is not None and I2.soc_intent is not None)
    if I1.ind_intent != I2.ind_intent:
        return False
    # soc_intent[2] maybe a intent or not ([inform, sb, sth])
    elif (I1.soc_intent != I2.soc_intent) and (I1.soc_intent[:2] != I2.soc_intent[:2]
                                               or not isinstance(I1.soc_intent[2], Intent)
                                               or not isinstance(I2.soc_intent[2], Intent)
                                               or not same_intent(I1.soc_intent[2], I2.soc_intent[2])):
        return False
    elif I1.comm_intent != I2.comm_intent:
        return False
    elif I1.ref_intent != I2.ref_intent:
        return False
    else:
        return True


# as for the help intent
def estimation_of_same_agent(I1, I2):
    assert isinstance(I1, Intent)
    assert isinstance(I2, Intent)
    if I1.soc_intent is None or I2.soc_intent is None:
        return False
    if I1.soc_intent[0] != 'help' or I2.soc_intent[0] != 'help':
        return False
    return I1.soc_intent[:2] == I2.soc_intent[:2]


def actual_same_intent(guesser, I1, I2):
    # strictly judge
    if same_intent(I1, I2):
        return True

    # ['get', sth, None] == ['get', sth, sw]
    # fixme, 0921
    if I1.ind_intent is not None and I2.ind_intent is not None:
        if I1.ind_intent[0] == 'get' and I1.ind_intent[:2] == I2.ind_intent[:2]:
            return True

    # actual meaning judge in the social intent
    if I2.soc_intent is not None and I2.soc_intent[0] == 'request_help':
        request_agent_id = I2.soc_intent[1]
        # if guesser.id == request_agent_id:
        # todo: 这里不一定必须是请求我的帮助,我也可以更加主动地帮助
        if I2.soc_intent[2].ind_intent == I1.ind_intent:
            return True
        # ['get', sth, None] == ['get', sth, sw]
        if I1.ind_intent is not None and I1.ind_intent[0] == 'get' and I1.ind_intent[:2] == I2.soc_intent[2].ind_intent[:2]:
            return True
    if I1.soc_intent is not None and I2.soc_intent is not None:
        if I1.soc_intent[:2] != I2.soc_intent[:2]:
            return False
        if not isinstance(I1.soc_intent[2], Intent) or not isinstance(I2.soc_intent[2], Intent):
            return False
        if isinstance(I1.soc_intent[2].ind_intent, Intent) and I1.soc_intent[2].ind_intent[0] == 'get' and I1.soc_intent[2].ind_intent[:2] == I2.soc_intent[2].ind_intent[:2]:
            return True
    return False


def intent_not_None(intent, level=None):
    if intent is None:
        return False

    if level is None:
        return True
    elif level == "ind":
        if intent.ind_intent is None:
            return False
        else:
            return True
    elif level == "soc":
        if intent.soc_intent is None:
            return False
        else:
            return True
    elif level == "comm":
        if intent.comm_intent is None:
            return False
        else:
            return True
    elif level == "ref":
        if intent.ref_intent is None:
            return False
        else:
            return True


def put_onto_constraint_check(put_onto_intent, W=None, sth=None, sw=None):
    if sth is None and sw is None:
        sth_id, sw_id = put_onto_intent[1], put_onto_intent[2]
        sth = W.retrieve_by_id(sth_id)
        sw = W.retrieve_by_id(sw_id)
    # fixme 0915, cannot put sth onto sw when sth is bigger than sw
    if sth.size[0] * sth.size[1] > sw.size[0] * sw.size[1]:
        return False
    if not hasattr(sw, 'is_supporter') or not sw.is_supporter:
        return False
    # cannot put sth onto sw when they are already very close
    if dis(sth, sw) <= NEAR_DIS:
        return False
    return True


def put_into_constraint_check(put_into_intent, W=None, sth=None, sw=None):
    if sth is None and sw is None:
        sth_id, sw_id = put_into_intent[1], put_into_intent[2]
        sth = W.retrieve_by_id(sth_id)
        sw = W.retrieve_by_id(sw_id)
    # cannot put sth into sw when sw isn't a container
    if not hasattr(sw, 'is_container') or not sw.is_container:
        return False
    # cannot put sth into sw when sth are already in sw
    if sth.id in sw.containing:
        return False
    return True


def get_constraint_check(get_intent, W=None, sb=None, sth=None, sw=None):
    if sth is None and sw is None:
        sth_id, sw_id = get_intent[1], get_intent[2]
        sth = W.retrieve_by_id(sth_id)
        sw = W.retrieve_by_id(sw_id)
    # cannot get sth when the agent already holds the sth
    # if sth.id in agent.holding_ids:
    #     return False
    # fixme 0915, cannot get sth from sw when they are distant
    # if sw is not None and dis(sth, sw) > NEAR_DIS:
    #     return False
    # cannot get sth from sw when sth contains sw
    if isinstance(sth, Object) and sw in sth.containing:
        return False
    # cannot get sth from sw when sth is a container
    if isinstance(sth, Object) and sth.is_container:
        return False
    if isinstance(sth, Object) and ((hasattr(sw, 'holding_ids') and sth.id not in sw.holding_ids)
                                    or (isinstance(sw, Object) and sth.id not in sth.containing)):
        return False
    return True


def open_constraint_check(open_intent, W=None, sth=None):
    if sth is None:
        sth_id = open_intent[1]
        sth = W.retrieve_by_id(sth_id)
    # only open intent when sth is a container and not open
    if not (isinstance(sth, Object) and sth.is_container and not sth.open):
        return False
    return True


def play_constraint_check(play_intent, W=None, sth=None):
    if sth is None:
        sth_id = play_intent[1]
        sth = W.retrieve_by_id(sth_id)
    # cannot play sth when sth is not a game
    if not hasattr(sth, 'is_game') or not sth.is_game:
        return False
    return True


def request_help_constraint_check(intent):
    helper_id = intent.soc_intent[1]
    tmp = intent.soc_intent[2]
    if isinstance(tmp, Intent):
        # cannot request my help to attract/find me
        if tmp.ind_intent[0] in ["attract", "find"] and helper_id == tmp.ind_intent[1]:
            return False
        # cannot request my help to give sth to me
        if tmp.ind_intent[0] in ['give'] and helper_id == tmp.ind_intent[2]:
            return False
    return True


def inform_constraint_check(intent, W=None, sb=None, sth=None):
    if sb is None and sth is None:
        sb_id, sth_id = intent.soc_intent[1], intent.soc_intent[2]
        sb = W.retrieve_by_id(sb_id)
        sth = W.retrieve_by_id(sth_id)
    if dis(sb, sth) <= NEAR_DIS:
        return False
    return True


# def follow_constraint_check():
#     pass


intent_constraint_check_dict = {
    "put_onto": put_onto_constraint_check,
    "put_into": put_into_constraint_check,
    "get": get_constraint_check,
    "open": open_constraint_check,
    "play": play_constraint_check,
    "request_help": request_help_constraint_check,
    "inform": inform_constraint_check,
    # "follow": follow_constraint_check
}


def viz_intent_space():
    CATE = ["put_onto", "put_into", "give", "get", "find", "move_to", "open", "play", "check", "confirm", "attract",
            "explore", "help", "harm", "share", "inform", "request_help", "ref"]

    MIN_E = 1000000
    MIN_setup = []
    MIN_cates = []
    MIN_P = []

    for p1 in np.linspace(0, 1, 11):
        for p2 in np.linspace(0, 1, 11):
            for p3 in np.linspace(0, 1, 11):

                IS = IntentSampler(p1, p2, p3)
                int_all = []
                int_cates = []

                for _ in range(5000):
                    intent_s = IS(mode="test")
                    cate = intent_s.category()
                    int_all.append(intent_s)
                    int_cates.append(cate)

                P = []
                Q = []
                for c in CATE:
                    P.append(int_cates.count(c))
                    Q.append(1.)

                P = np.array(P) / (np.sum(np.array(P)) + 0.0000001)
                Q = np.array(Q) / len(Q)

                ent = scipy.stats.entropy(P, Q)
                if ent < MIN_E:
                    MIN_E = ent
                    MIN_setup = [p1, p2, p3]
                    MIN_P = P

    print(MIN_setup)
    print(MIN_E)

    plt.bar(CATE, MIN_P)

    plt.xticks(rotation=90)
    plt.xticks(size=5)
    plt.show()


# from core.agent import Agent
if __name__ == "__main__":

    intent = Intent()
    _intent = Intent()
    _intent.ind_intent = ['get', 3, 4]
    # Soc_intent: request_help 1 Ind_intent: get 3 4
    intent.soc_intent = ['request_help', 1, _intent]
    print(intent.print())

    intent = Intent()
    intent.soc_intent = ['play_with', 3, 4]
    #  Soc_intent: play_with 3 4
    print(intent.print())
