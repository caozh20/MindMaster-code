import random
from random import choice
import traceback
from .intent import Intent
from .entity import Object
from .agent import Agent
from utils.base import dis, get_same_direction_objs
from .const import *
from .check_fn import Pure_Together_Check


def update_all_tasks(agent_self, W):

    if agent_self.goal.ref_intent is not None:
        agent_self.goal_name = "ref " + " ".join([str(e) for e in agent_self.goal.ref_intent])
        who_id = agent_self.goal.ref_intent[0]
        for i in range(1, len(agent_self.goal.ref_intent)):
            agent_self.all_tasks.append(["ref", who_id, agent_self.goal.ref_intent[i]])
            agent_self.all_tasks.append(['ind', 'gaze_follow', who_id])

    elif agent_self.goal.soc_intent is not None:
        if isinstance(agent_self.goal.soc_intent[2], Intent):
            try:
                agent_self.goal_name = agent_self.goal.soc_intent[0] + " " \
                                       + str(agent_self.goal.soc_intent[1]) + " " \
                                       + agent_self.goal.soc_intent[2].print()
            except Exception as e:
                traceback.print_exc()
                agent_self.goal_name = ''

        else:
            try:
                agent_self.goal_name = agent_self.goal.soc_intent[0] \
                                       + " " + str(agent_self.goal.soc_intent[1]) \
                                       + " " + str(agent_self.goal.soc_intent[2])
            except Exception as e:
                traceback.print_exc()
                agent_self.goal_name = ''

        if agent_self.goal.soc_intent[0] == "help":
            # check for age
            who_id, Int = agent_self.goal.soc_intent[1], agent_self.goal.soc_intent[2]
            who_id = int(who_id)
            who = agent_self.belief.get(who_id)

            if Int.ref_intent is not None:
                # the informed agent is myself, just check
                if Int.ref_intent[0] == agent_self.id:
                    agent_self.all_tasks.append(
                        ["ind", "check", Int.ref_intent[1]])
                else:
                    # randomly point to who or where
                    if random.uniform(0, 1) < 0.5:
                        agent_self.all_tasks.append(
                            ["ref", Int.ref_intent[0], who_id])
                        agent_self.all_tasks.append(['ind', 'gaze_follow', Int.ref_intent[0]])
                    else:
                        agent_self.all_tasks.append(
                            ["ref", Int.ref_intent[0], Int.ref_intent[1]])  # could not handle len<2 yet

            elif Int.soc_intent is not None and len(Int.soc_intent) > 0:
                # soc_intent
                # ["help", sb_id, intent()] --> take the help soc_intent as agent_self intent... is this all?
                # ["harm", sb_id, intent()] --> take the harm soc_intent as agent_self intent
                # ["request_help", sb_id, intent()] --> attract sb and ref to the agent
                # ["share", sb_id, sth_id] -->
                # ["inform", sb_id, sth_id] -->
                # [give to, ..] ?

                if Int.soc_intent[0] == "help":  # todo: the problem of recursion
                    agent_self.goal.soc_intent = [
                        "help", Int.soc_intent[1], Int.soc_intent[2]]
                elif Int.soc_intent[0] == "harm":
                    agent_self.goal.soc_intent = [
                        "harm", Int.soc_intent[1], Int.soc_intent[2]]
                elif Int.soc_intent[0] == "request_help":
                    # if the request_help is for myself
                    if Int.soc_intent[1] == agent_self.id:
                        agent_self.goal = Int.soc_intent[2]
                        update_all_tasks(agent_self, W)
                        # if Int.soc_intent[2].ind_intent is not None:
                        #     agent_self.goal.ind_intent = Int.soc_intent[2].ind_intent
                        # if Int.soc_intent[2].soc_intent is not None:
                        #     agent_self.goal.soc_intent = Int.soc_intent[2].soc_intent
                        # if Int.soc_intent[2].ref_intent is not None:
                        #     agent_self.goal.ref_intent = Int.soc_intent[2].ref_intent
                    else:
                        agent_self.all_tasks.append(
                            ["ind", "attract", Int.soc_intent[1]])
                        agent_self.all_tasks.append(
                            ["soc", "request_help", Int.soc_intent[2], who_id])
                elif Int.soc_intent[0] == "share":
                    if random.uniform(0, 1) < 0.5:
                        agent_self.all_tasks.append(
                            ["soc", "share", Int.soc_intent[1], who_id])
                    else:
                        agent_self.all_tasks.append(
                            ["soc", "share", Int.soc_intent[1], Int.soc_intent[2]])
                elif Int.soc_intent[0] == "inform":
                    if random.uniform(0, 1) < 0.5:
                        agent_self.all_tasks.append(
                            ["soc", "inform", Int.soc_intent[1], who_id])
                        agent_self.all_tasks.append(['ind', 'gaze_follow', Int.soc_intent[1]])
                    else:
                        agent_self.all_tasks.append(
                            ["soc", "inform", Int.soc_intent[1], Int.soc_intent[2]])
                elif Int.soc_intent[0] == "play_with":
                    if Pure_Together_Check(agent_self, who_id, Int.soc_intent[2], W):
                        agent_self.all_tasks.append(
                            ["soc", "play_with", who_id, Int.soc_intent[2]])
                    if Int.soc_intent[1] == agent_self.id:
                        agent_self.all_tasks.append(
                            ["soc", "play_with", who_id, Int.soc_intent[2]])
                    else:
                        agent_self.all_tasks.append(
                            ["ind", "get", Int.soc_intent[2], None])
                        agent_self.all_tasks.append(
                            ["ind", "give", Int.soc_intent[2], who_id])
                        agent_self.all_tasks.append(
                            ["soc", "play_with", who_id, Int.soc_intent[2]])

            elif Int.ind_intent is not None:
                if Int.ind_intent[0] == "put_onto":
                    what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]

                    # if who is holding sth:
                    #     # open the container
                    #     agent_self.all_tasks.append(["ind", "open", where])
                    # else:
                    #     # put sth onto sw
                    #     # put sth onto the agent
                    #     # open the container
                    #     if random.uniform(0, 1) < 1/3.:
                    #         agent_self.all_tasks.append(["ind", "open", where])
                    #     elif random.uniform(0, 1) < 2/3.:
                    #         agent_self.all_tasks.append(["ind", "put", what, where])
                    #     else:
                    #         agent_self.all_tasks.append(["ind", "put", what, who])
                    what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]
                    # help, who, put_into, what, where
                    # todo: shuffle problem, randomness
                    # "open" before "put into where"
                    # shuffle logic,
                    #
                    task_pools = []

                    # if not W.retrieve_by_id(where_id).open:
                    #     task_pools.append(["ind", "open", where_id])

                    # if what_id not in W.retrieve_by_id(who_id).holding_ids:
                    #     # partially help
                    #     task_pools.append(["ind", "give", what_id, who_id])
                    # else:
                    task_pools.append(["ind", "put_onto", what_id, where_id])

                    for tmp in task_pools:
                        # if random.uniform(0, 1) < 0.5:
                        agent_self.all_tasks.append(tmp)

                    if len(agent_self.all_tasks) == 0:
                        agent_self.all_tasks.append(choice(task_pools))

                elif Int.ind_intent[0] == "put_into":
                    # todo: belief or world? should be deciding  based on belief, not the reality, right?
                    what_id, where_id = int(Int.ind_intent[1]), int(Int.ind_intent[2])
                    # help, who, put_into, what, where
                    # todo: shuffle problem, randomness
                    # "open" before "put into where"
                    # shuffle logic,
                    #
                    task_pools = []

                    if not W.retrieve_by_id(where_id).open:
                        task_pools.append(["ind", "open", where_id])

                    # dis(W.retrieve_by_id(what_id), W.retrieve_by_id(where_id)) <= 1 means sth are almost in sw
                    # if what_id not in W.retrieve_by_id(who_id).holding_ids and dis(W.retrieve_by_id(what_id), W.retrieve_by_id(where_id)) > NEAR_DIS:
                    #     # partially help
                    #     task_pools.append(["ind", "give", what_id, who_id])
                    # else:
                    #     task_pools.append(["ind", "put_into", what_id, where_id])

                    if random.uniform(0, 1) < 0.1 \
                            and what_id not in W.retrieve_by_id(who_id).holding_ids \
                            and dis(W.retrieve_by_id(what_id), W.retrieve_by_id(where_id)) > NEAR_DIS:
                        agent_self.all_tasks.append(["ind", "give", what_id, who_id])
                    else:
                        agent_self.all_tasks.append(["ind", "put_into", what_id, where_id])

                    # if len(agent_self.all_tasks) == 0:
                    #     agent_self.all_tasks.append(choice(task_pools))

                elif Int.ind_intent[0] == "give":
                    # [give, sth, sb] --> get, give and point
                    what_id = Int.ind_intent[1]
                    what = W.retrieve_by_id(what_id)
                    where = None
                    if isinstance(what, Object) and len(what.being_held_id):
                        where = what.being_held_id[0]
                    agent_self.all_tasks.append(['ind', 'get', Int.ind_intent[1], where])
                    agent_self.all_tasks.append(['ind', 'give', Int.ind_intent[1], Int.ind_intent[2]])
                    agent_self.all_tasks.append(['ref', who_id, Int.ind_intent[1]])
                    pass

                elif Int.ind_intent[0] == "get":
                    what_id = Int.ind_intent[1]
                    what = W.retrieve_by_id(what_id)
                    where_id = None
                    if isinstance(what, Object):
                        if len(what.being_held_id):
                            where_id = what.being_held_id[0]

                    if where_id != agent_self.id:
                        # if agent_self.desire.active >= 1:
                            # [get, sth, from sw]  --> get sth from sw and give it to the agent
                        if len(Int.ind_intent) >= 3:
                            agent_self.all_tasks.append(['ind', 'get', Int.ind_intent[1], Int.ind_intent[2]])
                        else:
                            agent_self.all_tasks.append(['ind', 'get', Int.ind_intent[1], None])
                        if agent_self.desire.active >= 0.5:
                            agent_self.all_tasks.append(['ind', 'give', Int.ind_intent[1], who_id])
                        # else:
                        #     agent_self.all_tasks.append(['ref', who_id, where_id if where_id is not None else what_id])
                        #     agent_self.all_tasks.append(['ind', 'gaze_follow', who_id])
                    else:
                        # help sb get sth from me
                        agent_self.all_tasks.append(['ind', 'give', Int.ind_intent[1], who_id])
                    pass  # todo

                elif Int.ind_intent[0] == "find":
                    # [find, sth] --> point to sw..or get sth and give it to the agent
                    # tode: check it in belief or not?
                    what = W.retrieve_by_id(Int.ind_intent[1])
                    if isinstance(what, Object):

                        # if random.uniform(0, 1) > 0.5:
                        if agent_self.desire.active < 0.5:
                            agent_self.all_tasks.append(['ref', who_id, Int.ind_intent[1]])
                        else:
                            if len(what.being_held_id):
                                where = what.being_held_id[0]
                            else:
                                where = None
                            agent_self.all_tasks.append(
                                ["ind", "get", Int.ind_intent[1], where])
                            agent_self.all_tasks.append(
                                ["ind", "give", Int.ind_intent[1], who_id])
                    else:
                        # if random.uniform(0, 1) > 0.5:
                        agent_self.all_tasks.append(['ref', who_id, Int.ind_intent[1]])
                        # else:
                        #     agent_self.all_tasks.append(['ref', Int.ind_intent[1], who_id])
                    pass

                elif Int.ind_intent[0] == "move_to":
                    # [move_to, sw] --> sth: get and give
                    #                   sb: refer to
                    s = W.retrieve_by_id(Int.ind_intent[1])
                    if isinstance(s, Object):
                        if len(s.being_held_id):
                            where = s.being_held_id[0]
                        else:
                            where = None
                        agent_self.all_tasks.append(
                            ["ind", "get", Int.ind_intent[1], where])
                    elif isinstance(s, Agent):
                        agent_self.all_tasks.append(
                            ["ref", Int.ind_intent[1], who_id])
                    pass
                elif Int.ind_intent[0] == "open":
                    # [open, sth] --> open sth
                    agent_self.all_tasks.append(["ind", "open", Int.ind_intent[1]])
                    if agent_self.desire.social >= 0.5:
                        agent_self.all_tasks.append(["ref", who_id, Int.ind_intent[1]])

                elif Int.ind_intent[0] == "play":
                    # [play, sth] --> play with the object
                    agent_self.all_tasks.append(["ind", "get", Int.ind_intent[1], None])
                    agent_self.all_tasks.append(["ind", "give", Int.ind_intent[1], who_id])
                elif Int.ind_intent[0] == "check":
                    # [check, sw] --> NA
                    agent_self.all_tasks.append(["ind", "check", Int.ind_intent[1]])
                    pass
                elif Int.ind_intent[0] == "confirm":
                    # [confirm, sb] --> NA
                    agent_self.all_tasks.append(
                        ["ind", "confirm", Int.ind_intent[1]])
                    agent_self.all_tasks.append(
                        ["ref", Int.ind_intent[1], who_id])
                    pass
                elif Int.ind_intent[0] == "attract":
                    # [attract, sb] --> attract sb and ref to the agent
                    # avoid wave hands to myself
                    if Int.ind_intent[1] == agent_self.id:
                        agent_self.all_tasks.append(["ind", "check", who_id])
                    else:
                        agent_self.all_tasks.append(
                            ["ind", "attract", Int.ind_intent[1]])
                        agent_self.all_tasks.append(
                            ["ref", Int.ind_intent[1], who_id])
                    pass
        elif agent_self.goal.soc_intent[0] == "harm":
            who, Int = agent_self.goal.soc_intent[1], agent_self.goal.soc_intent[2]

            if Int.ref_intent is not None:
                pass
            elif Int.soc_intent is not None:
                # soc_intent
                # ["help", sb_id, intent()] --> take the help soc_intent as agent_self intent... is this all?
                # ["harm", sb_id, intent()] --> take the harm soc_intent as agent_self intent
                # ["request_help", sb_id, intent()] --> attract sb and ref to the agent
                # ["share", sb_id, sth_id] -->
                # ["inform", sb_id, sth_id] -->
                # [give to, ..] ?
                pass
            elif Int.ind_intent is not None:
                # Int is a ind_intent
                #         # [put, sth, into/onto sw] --> move sth? move sw?
                #         # [get, sth, from sw]  --> move sth? close sw?
                #         # [find, sth] --> [hide sth]
                #         # [move_to, sw] --> [move_to, sw]
                #         # [open, sth] --> [close, sth]?
                #         # [play, sth] --> [move, sth]
                #         # [check, sw] --> NA? occlude sw?
                #         # [confirm, sb] --> occlude sb?
                #         # [attract, sb] --> occlude? attract sb?

                if Int.ind_intent[0] == "put":
                    what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]
                    what = W.retrieve_by_id(what_id)
                    where = W.retrieve_by_id(where_id)

                elif Int.ind_intent[0] == "get":
                    # [get, sth, from sw]  --> get sth from sw and give it to the agent
                    pass

                elif Int.ind_intent[0] == "find":
                    # [find, sth] --> point to sw..or get sth and give it to the agent
                    pass

                elif Int.ind_intent[0] == "move_to":
                    # [move_to, sw] --> NA
                    pass
                elif Int.ind_intent[0] == "open":
                    # [open, sth] --> open sth
                    pass
                elif Int.ind_intent[0] == "play":
                    # [play, sth] --> play with the agent

                    pass
                elif Int.ind_intent[0] == "check":
                    # [check, sw] --> NA
                    pass
                elif Int.ind_intent[0] == "confirm":
                    # [confirm, sb] --> NA
                    pass
                elif Int.ind_intent[0] == "attract":
                    # [attract, sb] --> attract sb and ref to the agent
                    pass

        elif agent_self.goal.soc_intent[0] == "request_help":

            who_id, Int = agent_self.goal.soc_intent[1], agent_self.goal.soc_intent[2]
            # TODO: should we add new pointing here?

            if Int.ref_intent is not None:
                pass
            elif Int.soc_intent is not None:
                # soc_intent
                # ["help", sb_id, intent()] --> take the help soc_intent as agent_self intent... is this all?
                # ["harm", sb_id, intent()] --> take the harm soc_intent as agent_self intent
                # ["request_help", sb_id, intent()] --> attract sb and ref to the agent
                # ["share", sb_id, sth_id] -->
                # ["inform", sb_id, sth_id] -->
                # [give to, ..] ?

                pass
            elif Int.ind_intent is not None:
                # Int is a ind_intent
                #         # [put, sth, into/onto sw] --> point to sth, point to sw
                #         # [get, sth, from sw] --> point to sth/sw (container)
                #         # [find, sth] --> no way to point to? maybe could point to the old position? or speak?
                #         # [move_to, sw] --> hahahah?
                #         # [open, sth] --> point to sth
                #         # [play, sth] --> point to sth
                #         # [check, sw] --> NA
                #         # [confirm, sb] --> NA
                #         # [attract, sb] --> point to sb

                if Int.ind_intent[0] == "put_onto":
                    what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]
                    what = W.retrieve_by_id(what_id)
                    where = W.retrieve_by_id(where_id)
                    # agent_self.all_tasks.append(["ind", "attract", who_id])
                    agent_self.all_tasks.append(["ref", who_id, what_id])
                    agent_self.all_tasks.append(["ref", who_id, where_id])
                    agent_self.all_tasks.append(["ind", "confirm", who_id])
                    agent_self.all_tasks.append(["ind", "put_onto", who_id, what_id, where_id])

                elif Int.ind_intent[0] == "put_into":
                    what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]
                    what = W.retrieve_by_id(what_id)
                    where = W.retrieve_by_id(where_id)
                    # agent_self.all_tasks.append(["ind", "attract", who_id])
                    agent_self.all_tasks.append(["ref", who_id, what_id])
                    agent_self.all_tasks.append(["ref", who_id, where_id])
                    agent_self.all_tasks.append(["ind", "confirm", who_id])
                    agent_self.all_tasks.append(["ind", "put_into", who_id, what_id, where_id])

                elif Int.ind_intent[0] == "get":
                    # [get, sth, from sw]  --> get sth from sw and give it to the agent
                    # print('finally', Int.ind_intent)
                    # what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]
                    what_id = int(Int.ind_intent[1])
                    # agent_self.all_tasks.append(["ind", "attract", who_id])
                    agent_self.all_tasks.append(["ref", who_id, what_id])
                    same_direction_objs = get_same_direction_objs(W, agent_self, W.retrieve_by_id(what_id))
                    if len(same_direction_objs) > 1:
                        agent_self.point_confirm = True
                        agent_self.all_tasks.append(['ind', 'point_confirm', who_id, what_id])
                    # agent_self.all_tasks.append(["ind", "confirm", who_id])
                    agent_self.all_tasks.append(["ind", "get", what_id, who_id, "passive"])

                elif Int.ind_intent[0] == "find":
                    # [find, sth] --> point to sw..or get sth and give it to the agent
                    pass

                elif Int.ind_intent[0] == "move_to":
                    # [move_to, sw] --> NA
                    pass
                elif Int.ind_intent[0] == "open":
                    what_id = Int.ind_intent[1]
                    what = W.retrieve_by_id(what_id)
                    # agent_self.all_tasks.append(["ind", "attract", who_id])
                    agent_self.all_tasks.append(["ref", who_id, what_id])
                    pass
                elif Int.ind_intent[0] == "play":
                    # [play, sth] --> play with the agent
                    target_person_id = agent_self.goal.soc_intent[1]
                    agent_self.all_tasks.append(["ind", "attract", target_person_id])
                    target_intent = agent_self.goal.soc_intent[2]
                    agent_self.all_tasks.append(["ref", who_id, Int.ind_intent[1]])
                    pass
                elif Int.ind_intent[0] == "check":
                    # [check, sw] --> NA
                    pass
                elif Int.ind_intent[0] == "confirm":
                    # [confirm, sb] --> NA
                    pass
                elif Int.ind_intent[0] == "attract":
                    # [attract, sb] --> attract sb and ref to the agent
                    pass
                    # todo: no codes here! need to complete this!

        elif agent_self.goal.soc_intent[0] == "share":
            # if not done in the ref_intent, assume that we are randomly choosing the "move to and give" solution
            who_id, what_id = agent_self.goal.soc_intent[1], agent_self.goal.soc_intent[2]
            who = W.retrieve_by_id(who_id)
            what = W.retrieve_by_id(what_id)
            agent_self.all_tasks.append(["ind", "put", what, who])

        elif agent_self.goal.soc_intent[0] == "inform":
            # print("Error! the inform soc_intent should come down to ref_intent!") #todo
            agent_self.goal.ref_intent = agent_self.goal.soc_intent[1:]
            agent_self.goal_name = "inform " + " ".join([str(e) for e in agent_self.goal.soc_intent])
            who_id = agent_self.goal.soc_intent[1]
            for i in range(2, len(agent_self.goal.soc_intent)):
                agent_self.all_tasks.append(["ref", who_id, agent_self.goal.soc_intent[i]])
            agent_self.all_tasks.append(["ind", "confirm", who_id])

        elif agent_self.goal.soc_intent[0] == "play_with":
            who_id, what_id = agent_self.goal.soc_intent[1], agent_self.goal.soc_intent[2]
            if Pure_Together_Check(agent_self, who_id, what_id, W):
                agent_self.all_tasks.append(["soc", "play_with", who_id, what_id])
            else:
                # agent_self.all_tasks.append(["ind", "attract", who_id])
                agent_self.all_tasks.append(["ref", who_id, what_id])
                agent_self.all_tasks.append(["soc", "play_with", who_id, what_id])

    else:
        ind_intent = agent_self.goal.ind_intent
        assert ind_intent is not None
        agent_self.goal_name = " ".join([str(e) for e in ind_intent])
        if ind_intent[0] == "follow":
            who_id, what_id = ind_intent[1:]
            agent_self.all_tasks.append(["ind", "check", what_id])
            # fixme, whether in a probability way
            agent_self.all_tasks.append(["ind", "confirm", who_id])
        else:
            agent_self.all_tasks.append(["ind"] + ind_intent)
