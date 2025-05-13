from .check_fn import *
from .action import *
from .const import *
from .update_all_tasks import *
from .update_plan import update_plan
from .update_intent import *

def update_goal(agent_self, W):

    if agent_self.intent_now is None:
        return

    if agent_self.goal is not None and len(agent_self.all_tasks) == 0:
        agent_self.goal_over = True

    if agent_self.goal_over:
        last_intent = agent_self.intent_now
        # judge this intent's purpose whether be achieved or not
        # if last_intent.intent_pred(agent_self):
        #     agent_self.intent_last = last_intent
        #     agent_self.intent_now = None
        #     agent_self.intent_type_now = None
        # else:
        agent_self.reset_goal()
        agent_self.goal = agent_self.intent_now
        update_all_tasks(agent_self, W)

        if agent_self.intents_len() == 0:
            agent_self.reset_goal()
            return
        else:
            # new goal
            agent_self.reset_goal()
            agent_self.goal = agent_self.intent_now
            update_all_tasks(agent_self, W)

    # WARNING: SAME INTENT NOT ALLOWED?
    if (agent_self.goal is not None) and (agent_self.goal == agent_self.intent_now):
        if not agent_self.goal.ind_intent or 'explore' not in agent_self.goal.ind_intent:
            return

    # new goal
    agent_self.reset_goal()
    agent_self.goal = agent_self.intent_now
    update_all_tasks(agent_self, W)


def update_task(agent_self, W, args):

    if len(agent_self.all_tasks) == 0 and (agent_self.goal is not None):
        agent_self.goal_over = True
        update_goal(agent_self, W)
    if len(agent_self.all_tasks) == 0 and (agent_self.goal is None):
        return
    if agent_self.task_over:
        # new task
        if len(agent_self.all_tasks) == 0:
            agent_self.goal_over = True
            # todo
            update_goal(agent_self, W)
        if len(agent_self.all_tasks) > 0:
            agent_self.task_level = agent_self.all_tasks[0][0]
            agent_self.task = agent_self.all_tasks[0][1:]
            if agent_self.task_level == 'ref':
                agent_self.task_name = "ref " + " ".join(str(e) for e in agent_self.task)
            else:
                agent_self.task_name = " ".join(str(e) for e in agent_self.task)
            update_plan(agent_self, W, args)
            agent_self.task_over = False
    if len(agent_self.all_tasks) == 0 and (agent_self.goal is None):
        return
    if (agent_self.task is not None) and (agent_self.task == agent_self.all_tasks[0][1:]):
        return
    else:
        # new task
        if not len(agent_self.all_tasks):
            return
        agent_self.task_level = agent_self.all_tasks[0][0]
        agent_self.task = agent_self.all_tasks[0][1:]
        if agent_self.task_level == 'ref':
            agent_self.task_name = "ref " + " ".join(str(e) for e in agent_self.task)
        else:
            agent_self.task_name = " ".join(str(e) for e in agent_self.task)
        update_plan(agent_self, W, args)


def act(agent_self, W, args, in_whose_mind=-1):

    # print(agent_self.name, agent_self.plan, agent_self.task)
    if len(agent_self.plan) == 0:
        agent_self.task_over = True
        update_task(agent_self, W, args)
        # logger.info('agent {} task [{}]'.format(agent_self.id, agent_self.task_name))
    # execute agent_self.plan
    # exit mechanism
    # todo: repeating an action, e.g., explore
    # todo: if failed, switch to another possible action at step t
    while True:
        # The whole action_fail part is moved to action and update_all_tasks
        if agent_self.action_fail and (
                agent_self.plan_recycle
                is not None):  # todo: where to set action_fail as True?
            agent_self.plan.insert(0, agent_self.plan_recycle)
            agent_self.action_fail = False

        if len(agent_self.plan) == 0:
            agent_self.task_over = True
            return
        if agent_self.trial_n > MAX_TRIAL:
            print(agent_self.task_name + ", failure!")
            # todo: stop action here...
            agent_self.task_fail = True
            return
        if isinstance(agent_self.plan[0], Action):
            agent_self.plan_recycle = agent_self.plan.pop(0)
            # if len(agent_self.plan) == 0:
            #     agent_self.task_over = True
            #     update_task(agent_self, W, args)
            # means this intent has been consumed and release it
            if len(agent_self.plan) == 0:
                agent_self.all_tasks.pop(0)
                # agent_self.task_over = True
                if len(agent_self.all_tasks) == 0:
                    released_intent = agent_self.intent_now
                    agent_self.intent_last = agent_self.intent_now
                    agent_self.intent_now=None
                    agent_self.intent_type_now=None
                    agent_self.goal = None
                    agent_self.finished_intent.append(released_intent)
                    # log.info("agent {} release current intent({})".format(agent_self.id, released_intent.print()))
            return agent_self.plan_recycle  # todo: double check here
        elif isinstance(agent_self.plan[0], CheckFn):
            v, a = agent_self.plan[0](W, in_whose_mind)
            if v is False:
                agent_self.plan_recycle = None
                agent_self.trial_n += 1
                assert a != None
                return a
            else:
                agent_self.plan_recycle = agent_self.plan.pop(0)
                # means this intent has been consumed and release it
                if len(agent_self.plan) == 0:
                    agent_self.all_tasks.pop(0)
                    # agent_self.task_over = True
                    if len(agent_self.all_tasks) == 0:
                        released_intent = agent_self.intent_now
                        agent_self.intent_last = agent_self.intent_now
                        agent_self.intent_now=None
                        agent_self.intent_type_now=None
                        agent_self.goal = None
                        agent_self.finished_intent.append(released_intent)
                        if released_intent is not None:
                            log.info("agent {} release current intent({})".format(agent_self.id, released_intent.print()))
                agent_self.trial_n = 0
                if a is not None:
                    return a
