from random import choice
from .intent import Intent, actual_same_intent, intent_not_None
from .entity import Object
from .agent_utils import get_entity_in_whose_mind
from utils.base import dis, get_same_direction_objs


def propose_intents(agent_self, W=None):

    other_agents_in_belief = [agent.id for agent in agent_self.belief.agents if agent.id != agent_self.id]

    # if agent_self.pointing:
    #     point_target = get_entity_in_whose_mind(agent_self.pointing, W, -1)
    #     same_direction_objs = get_same_direction_objs(W, agent_self, point_target)
    #     if len(same_direction_objs) > 1:
    #         tmp = Intent()
    #         # fixme
    #         receiver_agent_id = 2
    #         tmp.ind_intent = ['point_confirm', receiver_agent_id, agent_self.pointing]
    #         agent_self.intents['HIHU'].append(tmp)

    # check the waving
    for agent in agent_self.belief.agents:
        if agent.waving and agent.id != agent_self.id:
            tmp = Intent()
            tmp.ind_intent = ["check", agent.id]
            if not agent_self.has_intent(tmp, "HIHU") \
                    and agent_self.attention_check(agent, W) == 1 \
                    and not agent_self.attention_check(agent, W, Att_R=0.001) == 1:
                if agent_self.has_finished_intent(tmp):
                    continue
                agent_self.intents["HIHU"].append(tmp)


    # follow the pointing
    for agent in agent_self.belief.agents:
        if agent.pointing and agent.id != agent_self.id:
            point_target = get_entity_in_whose_mind(agent.pointing, W, -1)
            same_direction_objs = get_same_direction_objs(W, agent, point_target)
            same_direction_objs = list(set(agent.belief.agent_ids) & set(same_direction_objs))
            if len(same_direction_objs) > 1:
                tmp = Intent()
                tmp.ind_intent = ['refer_disambiguation', agent.id, same_direction_objs]
                if agent_self.has_finished_intent(tmp) or (agent_self.intent_now is not None
                                                           and agent_self.intent_now.ind_intent is not None
                                                           and agent_self.intent_now.ind_intent[0] == 'refer_disambiguation'):
                    continue
                agent_self.intents['HIHU'].append(tmp)
            else:
                tmp = Intent()
                tmp.ind_intent = ["follow", agent.id, agent.pointing]
                # fixme condition of response to the pointing
                if agent_self.point_confirm:
                    continue
                if not agent_self.has_intent(tmp, "HIHU") and agent_self.attention_check(agent, W) == 1:
                    if agent_self.has_finished_intent(tmp):
                        continue
                    agent_self.intents["HIHU"].append(tmp)

    if agent_self.intent_fail:
        if agent_self.intent_now.soc_intent is None and agent_self.desire.social == 1 and len(other_agents_in_belief) > 0:
            helpful_scores = [agent.desire.helpful for agent in other_agents_in_belief]
            max_helpful = max(helpful_scores)
            indexes = [idx for (idx, v) in enumerate(helpful_scores) if v == max_helpful]
            index = choice(indexes)
            agent_self.intent_now.soc_intent = ["request_help", other_agents_in_belief[index], agent_self.intent_now.ind_intent]
            agent_self.intent_fail = False
        else:
            agent_self.failed_intent.append(agent_self.intent_now)
            agent_self.intent_now = None
            agent_self.intent_type_now = None
            agent_self.intent_fail = False

    # agent_self response to other's request_help (by infer)
    for agent in agent_self.belief.agents:
        if agent.id == agent_self.id:
            continue
        if intent_not_None(agent.intent_now, "soc") and (agent.intent_now.soc_intent[0] == "request_help"):
                tmp = Intent()
                # if need_my_help(agent_self, agent.id, other_soc_intent[2].ind_intent, W):
                # todo: 这里为啥要加ind_intent?
                if need_my_help(agent_self, agent.id, agent.intent_now.soc_intent[2].ind_intent, W):

                    tmp.soc_intent = ["help", agent.id, agent.intent_now.soc_intent[2]]

                    if agent_self.desire.helpful >= 0.5:
                        cate_tmp = "HIHU"
                    else:
                        cate_tmp = "LILU"

                    if not agent_self.already_has_intent(tmp):
                        agent_self.update_estimation_of_agent(tmp, cate_tmp)
                        # agent_self.intents[cate_tmp].append(tmp)

    # agent_self response to other's soc intent (by infer)
    for agent in agent_self.belief.agents:
        if agent.id == agent_self.id:
            continue
        if agent.intent_now is not None:
            if (agent.intent_now.soc_intent is None) or (agent.intent_now.soc_intent[0] != "request_help"):
                # todo: 这里一旦发现新的需要帮助的intent就直接覆盖原来的intent，很有问题。。
                if agent_self.desire.helpful >= 0.5:
                    # help sb explore/check/move_to doesn't make sense
                    if agent.intent_now.ind_intent is not None and not need_my_help(agent_self, agent.id, agent.intent_now.ind_intent, W):
                        pass
                    else:
                        tmp = Intent()
                        # myself infer other's intent, other's intent is inform myself something
                        if agent.intent_now.soc_intent and agent.intent_now.soc_intent[0] == 'inform' and agent.intent_now.soc_intent[1] == agent_self.id:
                            # maybe confirm the agent, first check then confirm base the stack (first in last out)
                            tmp.ind_intent = ['follow', agent.id, agent.intent_now.soc_intent[2]]
                            # tmp.ind_intent = ['check', agent.intent[-1].soc_intent[2]]
                            # if random.uniform(0, 1) < 1: #todo
                            #     another_int = Intent()
                            #     another_int.ind_intent = ['confirm', agent.id]
                            #     if not agent_self.has_intent(another_int):
                            #         agent_self.intent.append(another_int)
                            # check it
                            if not agent_self.already_has_intent(tmp):
                                # agent_self.intents["HILU"].append(tmp)
                                # todo
                                agent_self.intents["LIHU"].append(tmp)
                            break

                        to_help_int = agent.intent_now.ind_intent
                        tmp.soc_intent = ["help", agent.id, agent.intent_now]

                        if to_help_int is not None:
                            # if random.uniform(0, 1) < 1:
                                # get sth from none, and sth is hidden, insert a ref intent
                                # if to_help_int[0] in ['get']:
                                #     sth_id, sw_id = to_help_int[1:]
                                #     sth = get_entity_in_whose_mind(sth_id, W, in_whose_mind=agent_self.id)
                                #     if isinstance(sth, Object) and sth.is_hidden(W) and sw_id is None:
                                #         tmp.ref_intent = [agent.id, sth.being_held_id[0]]
                                # find/play sth is hidden
                            if to_help_int[0] in ['find', 'play']:
                                sth_id = to_help_int[1]
                                sth = get_entity_in_whose_mind(sth_id, W, in_whose_mind=agent_self.id)
                                if isinstance(sth, Object) and sth.is_hidden(W):
                                    tmp.ref_intent = [agent.id, sth.being_held_id[0]]
                        if not agent_self.already_has_intent(tmp):
                            # fixme, temporary fix, 2022/10/20
                            agent_self.update_estimation_of_agent(tmp, 'HIHU' if urgent_intent(agent) else 'HILU')
                            # agent_self.intents["HILU"].append(tmp)

                elif agent_self.desire.helpful < 0.5:
                    if (agent.intent_now.ind_intent is not None) and (agent.intent_now.ind_intent[0] in ["explore", "check", "move_to"]):
                        pass
                    else:
                        tmp = Intent()
                        tmp.soc_intent = ["help", agent.id, agent.intent_now]
                        if not agent_self.already_has_intent(tmp):
                            agent_self.update_estimation_of_agent(tmp, 'LILU')
                            # agent_self.intents["LILU"].append(tmp)

                # elif agent_self.desire.helpful == -2:
                #     tmp = Intent()
                #     tmp.soc_intent = ["harm", agent.id, agent.intent_now]
                #     if not agent_self.already_has_intent(tmp):
                #         agent_self.intents["HILU"].append(tmp)
                #
                # elif agent_self.desire.helpful == -1:
                #     tmp = Intent()
                #     tmp.soc_intent = ["harm", agent.id, agent.intent_now]
                #     if not agent_self.already_has_intent(tmp):
                #         agent_self.intents["LILU"].append(tmp)

    if agent_self.desire.active == 1:
        for e in agent_self.observation:
            if isinstance(e, Object):
                if e.is_game and not e.is_multiplayer_game:
                    tmp = Intent()
                    tmp.ind_intent = ["play", e.id]
                    if not agent_self.already_has_intent(tmp):
                        agent_self.intents["HILU"].append(tmp)
                elif e.is_salient:
                    if len(other_agents_in_belief) > 0:
                        if agent_self.desire.social == 1:
                            tmp = Intent()
                            tmp.soc_intent = ["share", choice(other_agents_in_belief), e.id]
                            if not agent_self.already_has_intent(tmp):
                                agent_self.intents["HILU"].append(tmp)

    # keep playing with
    if agent_self.intent_last is not None and \
            agent_self.intent_last.soc_intent is not None and agent_self.intent_last.soc_intent[0] == "play_with":
        agent_self.intents["LILU"].append(agent_self.intent_last)

    if agent_self.desire.active >= 1:
        tmp = Intent()
        tmp.ind_intent = ["explore"]
        if not agent_self.already_has_intent(tmp):
            agent_self.intents["LILU"].append(tmp)


def validate_intent(agent_self, world):
    # the intent that you want to help sb with, can be the same with sb's current intent
    intent_now = agent_self.intent_now

    try:
        if intent_now.ind_intent[0] == 'follow' and intent_now.ind_intent[2] in agent_self.holding_ids:
            return False
    except:
        pass

    if intent_not_None(intent_now, "soc") and intent_now.soc_intent[0] == "help":
        to_helper_id = intent_now.soc_intent[1]
        to_helper = agent_self.belief.get_by_id(to_helper_id)

        if to_helper is not None and to_helper.intent_now is not None:
            if not actual_same_intent(agent_self, intent_now.soc_intent[2], to_helper.intent_now):
                return False
            # 如果上一次已经成功帮助， 则不会重复帮助， 除非是帮助play_with（表现为一直在玩）
            # elif
            if agent_self.intent_last is not None and agent_self.intent_last.soc_intent is not None and \
                    agent_self.intent_last.soc_intent[0] == "help" and \
                    actual_same_intent(agent_self, intent_now.soc_intent[2], agent_self.intent_last.soc_intent[2]) and not \
                    (intent_now.soc_intent[2].soc_intent is not None and intent_now.soc_intent[2].soc_intent[0] == "play_with"):
                return False
            # help sb get sth is invalid when sth is already held by sb
            if intent_now.soc_intent[2].ind_intent is not None and intent_now.soc_intent[2].ind_intent[0] == 'get':
                sth_id = intent_now.soc_intent[2].ind_intent[1]
                if sth_id in to_helper.holding_ids:
                    return False
        # the intent (help sb find sth) is invalid when sth already in sb's belief
        if len(intent_now.soc_intent) > 2 and isinstance(intent_now.soc_intent[2], Intent):
            ind = intent_now.soc_intent[2].ind_intent
            if ind is not None and ind[0] == 'find' and to_helper is not None and ind[1] in to_helper.belief.all_ids:
                return False

    # 随着任务的执行，agent 及 object 位置及状态的变化，有些 intent 的合法性也不成立了，
    # fixme，20220915, 使用 intent.py 中的 intent_constraint_check_dict
    # 待测试
    # intent = agent_self.intent_now
    # if intent_not_None(intent, "ind"):
    #     if intent[0] in intent_constraint_check_dict.keys():
    #         if not intent_constraint_check_dict[intent[0]](intent):
    #             return False
    # if intent_not_None(intent, "soc") and intent.soc_intent[0] == 'request_help':
    #     if not intent_constraint_check_dict.get('request_help')(intent):
    #         return False
    # if intent_not_None(intent_now, "ind"):
    #     if intent_now.ind_intent[0] == "follow":
    #         sth_id = intent_now.ind_intent[2]
    #         sth = get_entity_in_whose_mind(sth_id, W=world, in_whose_mind=agent_self.id)
    #         if sth is not None and dis(sth, agent_self) <= NEAR_DIS:
    #             log.info("the intent {} is no longer valid for the distance".format(intent_now.print()))
    #             return False
    return True


def update_intent(agent_self, world):

    if not validate_intent(agent_self, world):
        agent_self.intent_now = None
        agent_self.intent_type_now = None

    # judge whether there is a higher priority intent emerges
    for cate in ["HIHU", "LIHU", "HILU", "LILU", None]:
        if cate == agent_self.intent_type_now:
            break
        else:
            if len(agent_self.intents[cate])>0:
                if agent_self.intent_now is not None \
                        and actual_same_intent(agent_self, agent_self.intent_now, agent_self.intents[cate][0]):
                    break
                if agent_self.intent_now is not None:
                    agent_self.intents[agent_self.intent_type_now].append(agent_self.intent_now)

                agent_self.intent_now = agent_self.intents[cate].pop(0)
                agent_self.intent_type_now = cate
                # update intent, the gestures (waving, pointing) may be unsuitable
                agent_self.reset_gestures()

                if not validate_intent(agent_self, world):
                    agent_self.intent_now=None
                    agent_self.intent_type_now=None
                    update_intent(agent_self, world)
                break


def need_my_help(guesser, actor_id, intent, W):
    actor = get_entity_in_whose_mind(actor_id, W, in_whose_mind=guesser.id)
    if intent[0] in ["explore", "check", "move_to"]:
        return False
    if intent[0] == 'give':
        sth_id, sb_id = intent[1], intent[2]
        if guesser.id == sb_id:
            return False
    if intent[0] in ['find', 'get', 'play']:
        sth_id = intent[1]
        sth = get_entity_in_whose_mind(sth_id, W, in_whose_mind=guesser.id)
        if sth is None or dis(sth, actor) < ((guesser.size + max(sth.size) if not isinstance(sth.size, int) else sth.size) + 50):
            return False
    # attract me, cannot help sb to attract me
    if intent[0] in ['attract'] and intent[1] == guesser.id:
        return False
    return True


def urgent_intent(actor):
    if actor.intent_now is None:
        return False
    if actor.intent_now.ind_intent is None:
        return False
    if actor.intent_now.ind_intent[0] != 'open':
        return False
    for action in actor.action_history:
        if 'ActionHit' in action:
            return True
    return False
