from copy import deepcopy
from collections import defaultdict
# from .intent import *
from utils.base import log
from .plan import update_task, act
from .update_all_tasks import update_all_tasks
from .agent_utils import *
from .agent import *
from .check_fn import CheckFn
from .score import *
from .const import SIMU_EPOCHS, alpha, beta
from .action import *
from scipy.stats import poisson, norm
import matplotlib.pyplot as plt
import numpy as np
import random


# P_n < 0, n 越大概率值越小（因 lambda < 1），倾向于分较少的段；
# fixme，待调参
def Poisson_n(n):
    return poisson.logpmf(k=n - 1, mu=0.6)


# P_s < 0，越靠近 loc 概率值越大
# fixme，待调参
def P_segment(S):
    x = 0
    for l_s in S:
        x += norm.logpdf(l_s, loc=7, scale=2)
    return x

def rand_propose_S(L, n):
    S = []
    for i in range(1, n + 1):
        if i == n:
            l_s = L - sum(S)
            S.append(l_s)

            assert sum(S) == L
            assert len(S) == n

            return S
        else:
            l_s = random.randint(1, L - sum(S) - (n - len(S) - 1))
            S.append(l_s)

def propose_all_S(L, n):
    all_S = []

    if n == 1:
        return [[L]]
    else:
        for l_s in range(1, L - (n - 1) + 1):

            _all_S = propose_all_S(L - l_s, n - 1)

            for v in _all_S:
                all_S.append([l_s] + v)

    return all_S


def inverse_infer_intent(agent_self, W, args):

    for agent in agent_self.belief.agents:

        if agent.id == agent_self.id:
            continue

        if len(agent.action_history) == 0:
            continue

        intent_temporal_reasoning(agent, agent_self, W, args, LOG_CHECK=False)


def intent_temporal_reasoning(agent, agent_self, W, args, LOG_CHECK=False):
    """
    I: intent proposals for all the segments
    S: segments, [l_s], recording the lengths of all the segments.
       Note that the summation of all the lengths should be equal to the length of action_seq.
    n: the number of segments
    action_seq: the observed action sequences
    """
    action_seq = agent.action_history
    action_hist_copy = deepcopy(action_seq)
    if len(action_seq) > 1:
        # 过滤连续重复的 explore
        action_hist_copy = [v for i, v in enumerate(action_seq) if i == 0
                       or v[:-1] != ['ActionExplore', str(agent.id)]
                       or (v[:-1] == ['ActionExplore', str(agent.id)] and v[:-1] != action_seq[i-1][:-1])]
        if len(action_hist_copy) > 1:
            # 过滤连续重复的 ActionObserveAgent
            action_hist_copy = [v for i, v in enumerate(action_hist_copy) if i == 0
                           or v[0] != 'ActionObserveAgent'
                           or (v[0] == 'ActionObserveAgent' and v[:-1] != action_hist_copy[i - 1][:-1])]

    action_hist = []
    for action in action_hist_copy:
        if action[0] == 'ActionWait' or action[0] == 'ActionShakeHead' or action[0] == 'ActionNodHead':
            continue
        action_hist.append(action)
    log.info('agent: {}, action hist: {}'.format(agent.name, action_hist))
    intent_SP = IntentSampler()
    intent_SP.valid_pool(agent, agent_self, W)
    # todo: 这个valid_pool目前没有[inform, sb, none]

    _agent = Agent()
    # agent_attr_obs_dcopy(agent_self, agent, _agent, W)
    agent_attr_obs_dcopy(agent, _agent)

    # assert sum(S)==len(action_seq)
    # assert n==len(S)
    # assert len(I)==n
    max_n = 3
    SCORES = []
    SCORES_s = []
    INTENTS = []
    L = len(action_hist)

    for split_ind, n in enumerate(range(1, max_n + 1)):

        P_n = Poisson_n(n)
        all_S = propose_all_S(L, n)

        for inner_ind, S in enumerate(all_S):
            P_s = P_segment(S)

            cum_l = np.cumsum(S)
            pre_inds = cum_l[:-1]
            pre_inds = np.insert(pre_inds, 0, 0)
            fol_inds = cum_l - 1
            all_inds = np.vstack((pre_inds, fol_inds))
            all_inds = np.transpose(all_inds)

            score = 0
            tmp_intent_hist = []

            for i in range(len(S)):
                inds = all_inds[i]
                if inds[0] == inds[1]:
                    actions = [action_hist[inds[0]]]
                else:
                    actions = action_hist[inds[0]:(inds[1]+1)]

                max_intent, max_score = opt_intent_1seg(actions, intent_SP, agent, agent_self, _agent, W, args, LOG_CHECK=False)

                score += max_score
                tmp_intent_hist.append(max_intent)
            # fixme, score(prior + ll + hoi) + prob (P_n + P_s) ?
            score += P_s
            score += P_n
            SCORES.append(score)

            # log.info('split_ind: {}/{}, inner_ind: {}/{}, guesser: {}, actor: {}, segments: {}({}, {}), score: {}'.format(
            #     split_ind, max_n, inner_ind, len(all_S),
            #     agent_self.id, agent.id, all_S[inner_ind], n, action_hist, score)
            # )
            SCORES_s.append(S)
            INTENTS.append(tmp_intent_hist)

    # _agent.clear()
    # del _agent

    SCORE_max = max(SCORES)
    indexes = [idx for (idx, v) in enumerate(SCORES) if v == SCORE_max]

    # todo: randomly choose one max intent, might be a big problem! might switching all the time!!
    ind = random.choice(indexes)

    # if agent.intent_now is not None and intent_SP.get_intent_index(agent.intent_now) in indexes:
    #     log.info(
    #         'agent {} infer intent of agent {}, no higher intent update, still: {}, score: {}'.format(
    #             agent_self.id, agent.id, agent.intent_now.print(), max_score
    #         )
    #     )
    #     return

    SEG_opt = SCORES_s[ind]
    INTENTS_opt = INTENTS[ind]
    log.info('final max split index: {} (num segments: {}, seg opt: {}), max_score: {}, random choice from {}'.format(
        ind, len(INTENTS_opt), SEG_opt, SCORE_max, len(indexes))
    )
    agent.intent_history = INTENTS_opt

    agent.intent_now = decide_which_segment(INTENTS_opt)

    log.info('agent {} infer intent of agent {}, intent now is: {}'.format(agent_self.id, agent.id,
                                                                           agent.intent_now.print() if agent.intent_now else None))

    # intent_SP.clear()
    # del intent_SP

    # if agent.intents_len() == 0:
    #     log.info(
    #         'agent {} infer intent of agent {}, first infer intent: {}, score: {}, random choice from: {}'.format(
    #             agent_self.id, agent.id,
    #             max_intent.print(), max_score, len(indexes)
    #         )
    #     )
    #
    # if agent.intent_now is not None and intent_SP.get_intent_index(agent.intent_now) not in indexes:
    #     intent_now_index = intent_SP.get_intent_index(agent.intent_now)
    #     log.info(
    #         'agent {} infer intent of agent {}, update the intent from {}(score: {}) to {}(score: {}, rand choice from {})'.format(
    #             agent_self.id, agent.id,
    #             agent.intent_now.print(), SCORE_all[intent_now_index] if intent_now_index != -1 else "invalid",
    #             max_intent.print(), max_score, len(indexes)
    #         )
    #     )
    #
    # if max_intent is not None:
    #     if agent.intent_now is not None and same_intent(max_intent, agent.intent_now):
    #         return
    #     # agent.intent.append(max_intent) #todo: check here
    #     agent.intent_now = max_intent  # todo: only guess one intent in one scenario
    #     # todo: maybe should add a choice for No guess


def decide_which_segment(INTENTS_opt):
    for i, int_tmp in enumerate(INTENTS_opt[::-1]):
        if int_tmp.ind_intent is not None and int_tmp.ind_intent[0] in ['check', 'confirm', 'gaze_follow', 'follow']:
            log.info("the {}/{} is a responding check intent: {}".format(len(INTENTS_opt)-i, len(INTENTS_opt), int_tmp.print()))
            continue
        return int_tmp
    return None


def opt_intent_1seg(actions, intent_SP, agent, agent_self, _agent, W, args, LOG_CHECK=False):

    SCORE_all = []

    # if LOG_CHECK:
    #     log.info('actions: {}'.format(actions))

    for int_tmp in intent_SP.vpool:
        assert int_tmp.category() != "None"
        prior_score = intent_prior(int_tmp, )
        if prior_score is None:
            prior_score = 0
        ll_scores = []
        # multi simulation to reduce the randomness in the task planning
        for _ in range(SIMU_EPOCHS):
            ll_scores.append(_calc_ll_score(_agent, int_tmp, actions, W, args))
        # LL_score = sum(ll_scores) / SIMU_EPOCHS
        LL_score = max(ll_scores)
        # prior_score = intent_prior_wrt_para(int_tmp, W, in_whose_mind=agent_self.id)
        hoi_term = _calc_hoi_term(int_tmp, actions, W)
        SCORE_all.append(prior_score + alpha * LL_score + beta * hoi_term)
        # for debug
        if LOG_CHECK:
            log.info('agent {} infer intent of agent {}, intent{}, prior_score: {}, LL_score: {}, hoi_term:{}'.format(
                agent_self.id, agent.id, int_tmp.print(), prior_score, LL_score, hoi_term
            ))

    # todo: there are many proposals with the same score....
    max_score = max(SCORE_all)
    indexes = [idx for (idx, v) in enumerate(SCORE_all) if v == max_score]

    # todo: randomly choose one max intent, might be a big problem! might switching all the time!!
    ind = random.choice(indexes)
    max_intent = intent_SP.vpool[ind]
    # log.info('agent {} infer intent of agent {}, max intent: {}, random choice from {}'.format(agent_self.id, agent.id, max_intent.print(), len(indexes)))
    return max_intent, max_score


# one simulation of complete sequence
def _calc_ll_score(_agent, int_tmp, action_hist, W, args):
    _agent.intent_now = int_tmp
    _agent.reset_goal()
    _agent.goal = _agent.intent_now
    update_all_tasks(_agent, W)
    all_plan = []
    num_all_tasks = len(_agent.all_tasks)
    # num_all_tasks = 1
    for i in range(num_all_tasks):
        update_task(_agent, W, args)
        all_plan.extend(_agent.plan)
        _agent.plan = []
        _agent.task_over = True
        # fixme, 需要同 update_task 中的更新保持一致
        _agent.all_tasks.pop(0)

    # action_tmp = act(_agent, W, args, in_whose_mind=agent_self.id)
    # todo: 这里只看一步，而不是几步，有点问题。

    # todo: only one time step forward
    # all possible actions from the plan

    action_csq = []
    for e in all_plan:
        if isinstance(e, CheckFn):
            action_csq.extend(e.action_name())
        elif isinstance(e, Action):
            action_csq.append(e.name())

    # removing consecutive duplicate action
    if len(action_csq) > 1:
        action_csq = [v for i, v in enumerate(
            action_csq) if i == 0 or v != action_csq[i - 1]]
    # removing consecutive duplicate actionexplore
    if len(action_hist) > 1:
        action_hist = [v for i, v in enumerate(action_hist) if i == 0
                       or v[:-1] != ['ActionExplore', str(_agent.id)]
                       or (v[:-1] == ['ActionExplore', str(_agent.id)] and v != action_hist[i-1])]
    LL_score = intent_LLScore_v2(action_csq, action_hist, int_tmp, W)
    return LL_score


# one simulation of complete sequence
def simulate_action_seq(_agent, int_tmp, W, args=None):
    _agent.intent_now = int_tmp
    _agent.reset_goal()
    _agent.goal = _agent.intent_now
    update_all_tasks(_agent, W)
    all_plan = []
    num_all_tasks = len(_agent.all_tasks)
    # num_all_tasks = 1
    for i in range(num_all_tasks):
        update_task(_agent, W, args)
        all_plan.extend(_agent.plan)
        _agent.plan = []
        _agent.task_over = True
        # fixme, 需要同 update_task 中的更新保持一致
        _agent.all_tasks.pop(0)

    action_csq = []
    for e in all_plan:
        if isinstance(e, CheckFn):
            action_csq.extend(e.action_name())
        elif isinstance(e, Action):
            action_csq.append(e.name())
    return action_csq


def _calc_hoi_term(int_tmp, action_hist, W):

    # hoi term
    # retrieve the object instance from world by id
    # pointing,
    # rotate to: means attention
    # grabbing:
    # waving

    hoi_score = 0
    for action in action_hist:

        # print(action_hist)
        # print(action)

        if action[0] in ['ActionExplore']:
            # may want to find something or get something:
            obj_ids = W.get_obj_ids()
            for obj_id in obj_ids:
                obj = W.retrieve_by_id(obj_id)
                if obj.is_hidden(W) and ((int_tmp.ind_intent is not None
                                          and int_tmp.ind_intent in [['find', obj_id], ['get', obj_id, None]]
                                         )
                                         or (int_tmp.soc_intent is not None
                                             and int_tmp.soc_intent[2] in [['find', obj_id], ['get', obj_id, None]])):
                    hoi_score += 0.5

        if action[0] in ['ActionHit']:
            obj_id = int(action[2])
            obj = W.retrieve_by_id(obj_id)
            if obj is None:
                continue
            if isinstance(obj, Object) and obj.is_container and int_tmp.ind_intent is not None and int_tmp.ind_intent == ['open', obj_id]:
                hoi_score += 2

        if action[0] in ['ActionPointTo']:
            target_id = int(action[2])
            target = W.retrieve_by_id(target_id)
            if target is None:
                continue
            # may want to play the game (??) or request_help to play the game
            # or play the game with sb
            if isinstance(target, Object):
                if target.is_game and ((int_tmp.ind_intent is not None and int_tmp.ind_intent == ['play', target_id])
                                       or (int_tmp.soc_intent is not None
                                           and isinstance(int_tmp.soc_intent[2], Intent)
                                           and int_tmp.soc_intent[2].ind_intent == ['play', target_id])
                                       or (int_tmp.soc_intent is not None
                                           and int_tmp.soc_intent[0] == "play_with")):
                    hoi_score += 0.1

                elif target.is_container:
                    # close state => open intent increase
                    if not target.open and ((int_tmp.ind_intent is not None and int_tmp.ind_intent == ['open', target_id])
                                            or (int_tmp.soc_intent is not None
                                                and int_tmp.soc_intent[2] is not None
                                                and isinstance(int_tmp.soc_intent[2], Intent)
                                                and int_tmp.soc_intent[2].ind_intent == ['open', target_id])):
                        hoi_score += 0.1
                    # point to a container =>
                    if (int_tmp.ind_intent is not None and int_tmp.ind_intent[0] == 'put_into' and int_tmp.ind_intent[2] == target_id) \
                            or (int_tmp.soc_intent is not None
                                and int_tmp.soc_intent[0] == 'request_help'
                                and int_tmp.soc_intent[2].ind_intent[0] == 'put_into'
                                and int_tmp.soc_intent[2].ind_intent[2] == target_id):
                        hoi_score += 0.1

                elif target.is_supporter:
                    # point to a container =>
                    if (int_tmp.ind_intent is not None and int_tmp.ind_intent[0] == 'put_onto' and int_tmp.ind_intent[2] == target_id) \
                            or (int_tmp.soc_intent is not None
                                and int_tmp.soc_intent[0] == 'request_help'
                                and int_tmp.soc_intent[2].ind_intent[0] == 'put_onto'
                                and int_tmp.soc_intent[2].ind_intent[2] == target_id):
                        hoi_score += 0.1

                # multiplayer_game check
                if target.is_multiplayer_game and int_tmp.soc_intent is not None and int_tmp.soc_intent[0] == 'play_with':
                    hoi_score += 0.1

    # put_onto, put_into
    return hoi_score


if __name__ == "__main__":

    # print(Poisson_n(1))
    # print(Poisson_n(2))
    # print(Poisson_n(3))
    # print(Poisson_n(4))
    # print(Poisson_n(5))
    # print(Poisson_n(6))
    #
    # fig, ax = plt.subplots(1, 1)
    # x = np.linspace(-1, 15, 100)
    # ax.plot(x, norm.pdf(x, loc=5, scale=2), 'r-', lw=5, alpha=0.6, label='lognorm pdf')
    # plt.show()

    # print(sum([1,2,3,4,5]))

    # print(random.randint(1,3))

    # print(propose_S(10,5))

    # print({'1':1, '4':13, '3':5, '2':10}.values())
    all_s=propose_all_S(10, 3)
    cum_l = np.cumsum(all_s[0])

    pre_inds=cum_l[:-1]
    pre_inds=np.insert(pre_inds,0, 0)
    fol_inds = cum_l - 1
    all_inds=np.vstack((pre_inds, fol_inds))
    all_inds=np.transpose(all_inds)


    print(all_s[0])
    print(cum_l)
    print(pre_inds)
    print(fol_inds)
    print(len(all_inds))
    print(all_inds[2])

    print(cum_l[0:0])
