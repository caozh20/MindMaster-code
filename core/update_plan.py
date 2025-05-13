from .check_fn import *
import random
from .action import *
from utils.base import *
from .const import *


def update_plan(agent_self, W, args):
    # the planner works like a recursive pre-requirement fulfillment link
    # [open, cabinet 3]
    # open with hand
    # when hand is occupied, hit

    # step back  -- ?
    # watch agent 4 -- why just watching ? belief of agent 4's mind? no further com_intent nor ref_intent?

    # see agent 2's moving back
    # stop pointing
    # play

    # del soc_intent --- after a while? randomly
    # move away

    # move to game, play
    # ref_intent [point to, agent 1] -- why not directly point to the timer?
    # check the intent complement status

    # move, grab, move to agent 1, pass
    # move to container 3, open, get obj 4

    # plan mode - generate a sequence of actions, including all the checks
    # flag vec, indicating where you are, which task should be executed next
    # execution mode

    # todo:add task name

    if agent_self.task_level == "ref":
        who_id, target_id = agent_self.task  # entity, not just id
        # seems like that we don't need the belief id position check, because it's done in the real_position check....
        # there is some "hard order", but also randomness in the plan seq, how to realize this?
        # todo: should target be agent_self.belief.get_by_entity(target)???? this is so philosophic.........
        who = W.retrieve_by_id(who_id)
        target = W.retrieve_by_id(target_id)

        if random.uniform(0, 1) < 0.5:
            agent_self.plan.append(real_position_check(agent_self.id, who_id))
            agent_self.plan.append(real_position_check(agent_self.id, target_id))
        else:
            agent_self.plan.append(real_position_check(agent_self.id, target_id))
            agent_self.plan.append(real_position_check(agent_self.id, who_id))

        if agent_self.desire.active <= 0.5:
            agent_self.plan.append(receiver_attention_on_me_by_refer_check(who_id, agent_self.id))
        else:
            agent_self.plan.append(receiver_attention_on_me_by_action_check(who_id, agent_self.id))

        # if random.uniform(0, 1) < 0.5:
        #     agent_self.plan.append(self_attention_check(agent_self.id, target_id))
        # else:
        #     agent_self.plan.append(self_attention_check(agent_self.id, who_id))
        # agent_self.plan.append(ActionPointTo(agent_self,target))  # todo: only change the pointing attr here, so the receiver need to recognize the action from the attr!
        # # also, there might be CheckFn or Action in the plan list, if else first
        # agent_self.plan.append(self_attention_check(agent_self.id, who_id))

        agent_self.plan.append(self_attention_check(agent_self.id, who_id))
        agent_self.plan.append(ActionPointTo(agent_self, target))

        agent_self.plan.append(receiver_attention_on_target_check(who_id, target_id, agent_self.id))
        # if random.uniform(0,1)<0.5:
        #     agent_self.plan.append(confirm_check(agent_self.id, who_id))

        # if target is not None:
        #     # means a gaze following
        #     rotate_angle = angle([1, 0], target.position - agent_self.position) / 180
        #     # agent_self.plan.append(ActionGazeAt(agent_self, rotate_angle))
        #     agent_self.plan.append(ActionRotateTo(agent_self, rotate_angle))

        # todo: do we need to judge whether "who" see my pointing?
        # what if agent_self and the target are within the "who"'s perception field at the beginning?
        # okay, the task will fail after T trials...

    elif agent_self.task_level == "soc":

        # ["help", sb_id, intent()]
        # ["harm", sb_id, intent()]
        # ["request_help", sb_id, intent()]
        # ["share", sb_id, sth_id]
        # ["inform", sb_id, sth_id]
        # [give to, ..] ?
        if agent_self.task[0] == "help":

            who, Int = agent_self.task[1], agent_self.task[2]
            # how to help in detail?
            # not necessarily ind_intent...could be social intent

            # ind_intent
            # simply take the ind_intent as agent_self intent?
            #         # [put, sth, into/onto sw] --> put sth onto the agent or sw? how to decide...
            #         # [get, sth, from sw]  --> get sth from sw and give it to the agent
            #         # [find, sth] --> point to sw..or get sth and give it to the agent
            #         # [move_to, sw] --> NA
            #         # [open, sth] --> open sth
            #         # [play, sth] --> play with the agent
            #         # [check, sw] --> NA
            #         # [confirm, sb] --> NA
            #         # [attract, sb] --> attract sb and ref to the agent

            # soc_intent
            # ["help", sb_id, intent()] --> take the help soc_intent as agent_self intent... is this all?
            # ["harm", sb_id, intent()] --> take the harm soc_intent as agent_self intent
            # ["request_help", sb_id, intent()] --> attract sb and ref to the agent
            # ["share", sb_id, sth_id] -->
            # ["inform", sb_id, sth_id] -->
            # [give to, ..] ?
            if Int.ref_intent is not None:
                pass
            elif Int.soc_intent is not None:
                pass
            elif Int.ind_intent is not None:
                if Int.ind_intent[0] == 'put_onto':
                    pass
                elif Int.ind_intent[0] == 'put_into':
                    what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]
                    what = W.retrieve_by_id(what_id)
                    where = W.retrieve_by_id(where_id)

                elif Int.ind_intent[0] == 'give':
                    pass
                elif Int.ind_intent[0] == 'get':
                    if Int.ind_intent[2] == None:
                        what_id = Int.ind_intent[1]
                        what = W.retrieve_by_id(what_id)
                        # something todo
                        agent_self.plan.append(real_position_check(agent_self.id, what_id))
                        agent_self.plan.append(distance_check(agent_self.id, what_id))
                        agent_self.plan.append(ActionGrab(agent_self, what))
                    else:
                        what_id, where_id = Int.ind_intent[1], Int.ind_intent[2]
                        what = W.retrieve_by_id(what_id)
                        where = W.retrieve_by_id(where_id)
                        if random.uniform(0, 1) < 0.5:
                            agent_self.plan.append(real_position_check(agent_self.id, what_id))
                            # todo: actually, where position check could be put in the later part?
                            agent_self.plan.append(real_position_check(agent_self.id, where_id))
                        else:
                            agent_self.plan.append(real_position_check(agent_self.id, where_id))
                            agent_self.plan.append(real_position_check(agent_self.id, what_id))
                #         #todo: do we need to check whether "what" is in "where"?

                #         agent_self.plan.append(distance_check(agent_self, where))
                #         agent_self.plan.append(ActionGrab(agent_self, what))
                elif Int.ind_intent[0] == 'find':
                    pass
                elif Int.ind_intent[0] == 'move_to':
                    pass
                elif Int.ind_intent[0] == 'open':
                    pass
                elif Int.ind_intent[0] == 'play':
                    pass
                elif Int.ind_intent[0] == 'check':
                    pass
                elif Int.ind_intent[0] == 'confirm':
                    pass
                elif Int.ind_intent[0] == 'attract':
                    pass

        elif agent_self.task[0] == "harm":
            pass
            who, Int = agent_self.task[1], agent_self.task[2]
            # todo: how to harm in detail?
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

            # Int could also be a soc_intent..

            # soc_intent
            # ["help", sb_id, intent()] -->
            # ["harm", sb_id, intent()] -->
            # ["request_help", sb_id, intent()] -->
            # ["share", sb_id, sth_id] -->
            # ["inform", sb_id, sth_id] -->
            # [give to, ..] ?

        elif agent_self.task[0] == "request_help":
            pass
            who, Int = agent_self.task[1], agent_self.task[2]

            # todo: ref intent?
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

            # soc_intent

            # ["help", sb_id, intent()] -->
            # ["harm", sb_id, intent()] -->
            # ["request_help", sb_id, intent()] -->
            # ["share", sb_id, sth_id] -->
            # ["inform", sb_id, sth_id] -->
            # [give to, ..] ?

        elif agent_self.task[0] == "share":

            who_id, what_id = agent_self.task[1], agent_self.task[2]
            who = W.retrieve_by_id(who_id)
            what = W.retrieve_by_id(what_id)
            # todo: ref to --> go to the ref_intent level
            # todo: "move_to" and give to ?
            if random.uniform(0, 1) < 0.5:
                agent_self.plan.append(real_position_check(agent_self.id, who_id))
                agent_self.plan.append(real_position_check(agent_self.id, what_id))
            else:
                agent_self.plan.append(real_position_check(agent_self.id, what_id))
                agent_self.plan.append(real_position_check(agent_self.id, who_id))

            agent_self.plan.append(self_attention_check(agent_self.id, what_id))
            agent_self.plan.append(distance_check(agent_self.id, what_id))
            # todo: holding check?
            agent_self.plan.append(ActionGrab(agent_self, what))
            agent_self.plan.append(self_attention_check(agent_self.id, who_id))
            agent_self.plan.append(distance_check(agent_self.id, who_id))
            agent_self.plan.append(ActionPutDown(agent_self, what))

        elif agent_self.task[0] == "inform":
            pass
            who_id, what_id = agent_self.task[1], agent_self.task[2]
            who = W.retrieve_by_id(who_id)
            what = W.retrieve_by_id(what_id)
            # todo: should go to the ref_intent??

        elif agent_self.task[0] == "play_with":
            who_id, what_id = agent_self.task[1], agent_self.task[2]
            agent_self.plan.append(ready_play_together_check(agent_self.id, who_id, what_id))

    elif agent_self.task_level == "ind":

        if agent_self.task[0] == "put_onto":
            if len(agent_self.task) < 4:
                # [put, sth, onto sw]
                what_id, where_id = agent_self.task[1], agent_self.task[2]
                what = W.retrieve_by_id(int(what_id))
                where = W.retrieve_by_id(int(where_id))

                if random.uniform(0, 1) < 0.5:
                    agent_self.plan.append(real_position_check(agent_self.id, what_id))
                    agent_self.plan.append(real_position_check(agent_self.id,
                                                         where_id))  # todo: actually, where position check could be put in the later part?
                else:
                    agent_self.plan.append(real_position_check(agent_self.id, where_id))
                    agent_self.plan.append(real_position_check(agent_self.id, what_id))
                # todo : change to randomly insert into the list
                # distance check
                agent_self.plan.append(self_attention_check(agent_self.id, what_id))
                agent_self.plan.append(distance_check(agent_self.id, what_id))
                # todo: holding check?

                # agent_self.plan.append(ActionGrab(agent_self, agent_self.belief.get_by_id(what_id)))

                agent_self.plan.append(holding_check(agent_self.id, what.id))
                # if isinstance(agent_self.belief.get_by_id(what), Object):
                #     agent_self.plan.append(ActionGrab(agent_self, agent_self.belief.get_by_id(what_id)))
                # else:
                #     agent_self.plan.append(ActionGrab(agent_self, what))

                agent_self.plan.append(self_attention_check(agent_self.id, where_id))
                agent_self.plan.append(distance_check(agent_self.id, where_id))
                # agent_self.plan.append(ActionPutOnto(agent_self, agent_self.belief.get_by_id(what_id), agent_self.belief.get_by_id(where_id))) # todo, put down on where?
                # agent_self.plan.append(turn_to_check(agent_self.id, where_id))
                agent_self.plan.append(ActionPutOnto(agent_self, what, where))  # todo, put down on where?
            else:
                who_id, what_id, where_id = agent_self.task[1], agent_self.task[2], agent_self.task[3]
                agent_self.plan.append(put_sth_onto_sw_by_sb_check(agent_self.id, who_id, what_id, where_id))

        elif agent_self.task[0] == "put_into":
            if len(agent_self.task) < 4:
                # [put, sth, into sw]
                what_id, where_id = agent_self.task[1], agent_self.task[2]
                what = W.retrieve_by_id(int(what_id))
                where = W.retrieve_by_id(int(where_id))

                if random.uniform(0, 1) < 0.5:
                    agent_self.plan.append(real_position_check(agent_self.id, what_id))
                    agent_self.plan.append(real_position_check(agent_self.id,
                                                         where_id))  # todo: actually, where position check could be put in the later part?
                else:
                    agent_self.plan.append(real_position_check(agent_self.id, where_id))
                    agent_self.plan.append(real_position_check(agent_self.id, what_id))
                if len(what.being_contained) > 0:
                    agent_self.plan.append(open_check(agent_self.id, what.being_contained[0]))
                # todo : change to randomly insert into the list
                # distance check
                agent_self.plan.append(self_attention_check(agent_self.id, what_id))
                agent_self.plan.append(
                    distance_check(agent_self.id, what_id))  # todo: need to retrieve the entity from belief, or the world???
                # todo: holding check?
                # todo:
                # agent_self.plan.append(holding_check(agent_self, agent_self.belief.get_by_id(what_id)))
                # todo: what if taking the object from a container first? what check?

                agent_self.plan.append(holding_check(agent_self.id, what.id))
                agent_self.plan.append(self_attention_check(agent_self.id, where_id))
                agent_self.plan.append(distance_check(agent_self.id, where_id))
                # agent_self.plan.append(turn_to_check(agent_self.id, where_id))
                agent_self.plan.append(open_check(agent_self.id, where.id))
                # todo: the problem is that the get_by_id method won't pass on to the plan execution time, and will return None at initialization
                agent_self.plan.append(ActionPutInto(agent_self, what, where))  # todo, put down on where?
            else:
                who_id, what_id, where_id = agent_self.task[1], agent_self.task[2], agent_self.task[3]
                agent_self.plan.append(put_sth_into_sw_by_sb_check(agent_self.id, who_id, what_id, where_id))

        elif agent_self.task[0] == "give":
            # [give, sth, to sb]
            what_id, who_id = agent_self.task[1], agent_self.task[2]
            what = W.retrieve_by_id(int(what_id))
            who = W.retrieve_by_id(int(who_id))

            if random.uniform(0, 1) < 0.5:
                agent_self.plan.append(real_position_check(agent_self.id, what_id))
                agent_self.plan.append(real_position_check(agent_self.id,
                                                     who_id))
                # todo: actually, where position check could be put in the later part?
            else:
                agent_self.plan.append(real_position_check(agent_self.id, who_id))
                agent_self.plan.append(real_position_check(agent_self.id, what_id))
            # todo : change to randomly insert into the list
            # distance check
            agent_self.plan.append(self_attention_check(agent_self.id, what_id))
            agent_self.plan.append(distance_check(agent_self.id, what_id))
            # replace the ActionGrab to holding_check
            # 1. holding_check will yield the ActionGrab
            # 2. give task may happen after get task (if get task succeed, then ActionGrab has been executed)
            # agent_self.plan.append(ActionGrab(agent_self, what))  # not necessarily???
            agent_self.plan.append(holding_check(agent_self.id, what.id))
            # agent_self.plan.append(distance_check(agent_self.id, who_id))
            agent_self.plan.append(self_attention_check(agent_self.id, who_id))
            agent_self.plan.append(distance_check(agent_self.id, who_id))
            agent_self.plan.append(receiver_attention_on_me_by_refer_check(who_id, agent_self.id))
            # agent_self.plan.append(ActionGiveTo(agent_self, what, who))  # todo, put down on where?
            agent_self.plan.append(give_check(agent_self.id, what_id, who_id))

        elif agent_self.task[0] == "get":
            # [get, sth, from sw] #todo: container?
            # add sw == none

            if len(agent_self.task)==3:
                if agent_self.task[2] == None:
                    what_id = int(agent_self.task[1])
                    what = W.retrieve_by_id(what_id)
                    agent_self.plan.append(real_position_check(agent_self.id, what_id))
                    agent_self.plan.append(distance_check(agent_self.id, what_id))
                    if isinstance(what, Object) and (len(what.being_held_id) > 0 or len(what.being_contained) > 0):
                        for where_id in what.being_held_id:
                            where = W.retrieve_by_id(where_id)
                            if not isinstance(where, Object):
                                continue
                            agent_self.plan.append(open_check(agent_self.id, where.id))
                            break
                        for where_id in what.being_contained:
                            where = W.retrieve_by_id(where_id)
                            if not isinstance(where, Object):
                                continue
                            agent_self.plan.append(open_check(agent_self.id, where.id))
                            break
                    # agent_self.plan.append(open_check(agent_self.id, what.id))
                    agent_self.plan.append(grab_check(agent_self.id, what_id))
                    agent_self.plan.append(ActionGrab(agent_self, what))

                else:
                    what_id, where_id = agent_self.task[1], agent_self.task[2]
                    what = W.retrieve_by_id(what_id)
                    where = W.retrieve_by_id(where_id)
                    if random.uniform(0, 1) < 0.5:
                        agent_self.plan.append(real_position_check(agent_self.id, what_id))
                        agent_self.plan.append(real_position_check(agent_self.id, where_id))
                        # todo: actually, where position check could be put in the later part?
                    else:
                        agent_self.plan.append(real_position_check(agent_self.id, where_id))
                        agent_self.plan.append(real_position_check(agent_self.id, what_id))
                    # todo: do we need to check whether "what" is in "where"?
                    agent_self.plan.append(self_attention_check(agent_self.id, where_id))
                    agent_self.plan.append(distance_check(agent_self.id, where_id))

                    if isinstance(W.retrieve_by_id(where_id), Object):
                        agent_self.plan.append(open_check(agent_self.id, where.id))

                    agent_self.plan.append(ActionGrab(agent_self, what))

            elif len(agent_self.task)>3 and agent_self.task[3]=="passive":
                #todo: here!
                what_id, where_id = agent_self.task[1], agent_self.task[2]
                agent_self.plan.append(get_sth_from_sb_check(agent_self.id, what_id, where_id))


        elif agent_self.task[0] == "find":
            # [find, sth]
            what_id = agent_self.task[1]
            what = W.retrieve_by_id(what_id)
            # todo:
            # belief check?
            # position check?
            # container?
            agent_self.plan.append(real_position_check(agent_self.id, what_id))

        elif agent_self.task[0] == "move_to":
            if isinstance(agent_self.task[1], int):
                # [move_to, sw]
                where_id = agent_self.task[1]
                if where_id == EXPLORE:
                    agent_self.plan.append(ActionMoveTo(agent_self, where_id))
                else:
                    where = W.retrieve_by_id(where_id)
                    agent_self.plan.append(real_position_check(agent_self.id, where_id))
                    # todo: distance check?
                    agent_self.plan.append(distance_check(agent_self.id, where_id))
            else:
                # [move_to, pos]
                agent_self.plan.append(ActionMoveTo(agent_self, agent_self.task[1]))

        elif agent_self.task[0] == "open":
            # [open, sth]
            what_id = agent_self.task[1]
            what = W.retrieve_by_id(what_id)

            agent_self.plan.append(real_position_check(agent_self.id, what_id))
            agent_self.plan.append(distance_check(agent_self.id, what_id))
            # agent_self.plan.append(turn_to_check(agent_self.id, what_id))
            agent_self.plan.append(unlocked_check(agent_self.id, what_id))
            agent_self.plan.append(ActionOpen(agent_self, what))

        elif agent_self.task[0] == "play":
            # [play, sth]
            what_id = agent_self.task[1]
            what = W.retrieve_by_id(what_id)
            agent_self.plan.append(real_position_check(agent_self.id, what_id))
            agent_self.plan.append(distance_check(agent_self.id, what_id))
            agent_self.plan.append(ActionPlay(agent_self, what))

        elif agent_self.task[0] == "check":
            # [check, sw]
            where_id = agent_self.task[1]
            # notice!!! must retrieve from the WORLD
            where = W.retrieve_by_id(where_id)

            # follow the pointing, rotate to the target
            # if where_id in agent_self.belief.all_ids:
            #     agent_self.plan.append(ActionCheckWaving(agent_self, where))
            # else:
            #     rotate_angle = angle([1, 0], where.position - agent_self.position) / 180
            #     agent_self.plan.append(ActionCheckWaving(agent_self, rotate_angle))

            # directly rotate to the target in WORLD
            agent_self.plan.append(ActionCheckWaving(agent_self, where))

            if not isinstance(where, Agent) and isinstance(where, Object) and where.is_container and not where.open:
                # when target is a container, open it to check (find something new)
                agent_self.plan.append(ActionMoveTo(agent_self, where))
                try:
                    agent_self.plan.append(unlocked_check(agent_self.id, where.id))
                except:
                    agent_self.plan.extend(unlocked_check(agent_self.id, where.id))
                agent_self.plan.append(ActionOpen(agent_self, where))

        elif agent_self.task[0] == "confirm":
            # [confirm, sb]
            who_id = agent_self.task[1]
            # who = W.retrieve_by_id(who_id)
            # agent_self.plan.append(real_position_check(agent_self.id, who_id))
            # agent_self.plan.append(self_attention_check(agent_self.id, who_id))
            # agent_self.plan.append(ActionRotateTo(agent_self, get_entity_in_whose_mind(who_id, W, agent_self.id)))
            # fixme 0329
            agent_self.plan.append(rotate_to_check(agent_self.id, who_id))
            agent_self.plan.append(confirm_check(agent_self.id, who_id))
            agent_self.plan.append(ActionNodHead(agent_self, STOP))

        elif agent_self.task[0] == "attract":
            # [attract, sb]
            who_id = agent_self.task[1]
            who = W.retrieve_by_id(who_id)
            agent_self.plan.append(real_position_check(agent_self.id, who_id))
            agent_self.plan.append(self_attention_check(agent_self.id, who_id))
            agent_self.plan.append(receiver_attention_on_me_by_refer_check(who_id, agent_self.id))
            # todo: how to decide the stop criterion?

        elif agent_self.task[0] == 'gaze_follow':
            who_id = agent_self.task[1]
            who = W.retrieve_by_id(who_id)
            # agent_self.plan.append(real_position_check(agent_self.id, who_id))
            agent_self.plan.append(gaze_follow_loop_check(agent_self.id, who_id))

        elif agent_self.task[0] == 'refer_disambiguation':
            who_id = agent_self.task[1]
            target_id_list = agent_self.task[2]
            try_target = W.retrieve_by_id(target_id_list[0])
            agent_self.plan.append(real_position_check(agent_self.id, try_target.id))
            agent_self.plan.append(real_position_check(agent_self.id, who_id))
            agent_self.plan.append(ActionPointTo(agent_self, try_target))
            agent_self.plan.append(refer_check(agent_self.id, who_id, target_id_list))

        elif agent_self.task[0] == 'point_confirm':
            who_id = agent_self.task[1]
            target_id = agent_self.task[2]
            agent_self.point_confirm = True
            agent_self.plan.append(point_check(agent_self.id, who_id, target_id))
            agent_self.plan.append(ActionNodHead(agent_self, STOP))

        elif agent_self.task[0] == "explore":
            agent_self.plan.append(ActionExplore(agent_self, None, args))
            # if args.scenario == "classroom":
            #     # agent_self.plan.append(ActionRotateTo(agent_self, EXPLORE))
            #     # todo: for test only, remember to change back
            #     agent_self.plan.append(ActionRotateTo(agent_self, 0.9))
            # else:
            #     agent_self.plan.append(random.choice([ActionMoveTo(agent_self, EXPLORE), ActionRotateTo(agent_self, EXPLORE)]))
