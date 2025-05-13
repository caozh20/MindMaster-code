import logging
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
import gc
from enum import Enum, unique
import traceback
from core.plan import *
from core.update_intent import *
from core.const import FPS
from core.inverse_infer_desire import *
from core.inverse_infer_belief import *
from core.inverse_infer_intent import *
from core.scenario import Scenario
from core.finish_check import scenario_finish_check, intent_finish_check
from scenarios.scenario_generating import intent_pool
from llms.parse_state import caption_current_state_to_llm
from llms.gpt_planner import context_agent_with_valid_action
from dataset.interaction_record import InteractionRecord, InteractionSession
from evaluation.metrics import compute_score
from utils.save import save_frames_as_video, save_evaluation_result
import action

sys.path.append(".")
sys.path.append("../")

np.random.seed(1234)
random.seed(1234)


def agent_pipeline(agent, world, args):
    log.info("------------agent ID : {}-----------------".format(agent.id))
    s = time.time()
    # fixme, very time-consuming operation in later rounds, to be optimized
    agent.observe(world, verbose=False)
    agent.update_belief(world)
    log.info(
        "agent {} belief, elapsed time: {}: [agent_ids {}], [object_ids {}], [landmark_ids {}]"
        .format(agent.id, time.time() - s,
                agent.belief.agent_ids, agent.belief.object_ids, agent.belief.landmark_ids)
    )
    # 0426 disabled, fixme, 待测试
    # agent.observation = []
    # update the false belief to None
    # update the belief of the entities being held when moving
    # agent.update_desire()
    inverse_infer_belief(agent, world)
    if args.policy == 'system':
        inverse_infer_intent(agent, world, args)
        inverse_infer_desire(agent, world)
        # intent generation
        propose_intents(agent, world)
        update_intent(agent, world)
        update_goal(agent, world)
        # intent decomposition
        update_task(agent, world, args)

default_action_choices = [['ActionExplore'],
            ['ActionMoveTo', 'somebody or something'],
            ['ActionRotateTo', 'somebody or something'],
            # check somebody's waving actually rotate to somebody
            ['ActionCheckWaving', 'somebody'],
            ['ActionOpen', 'something'],
            ['ActionUnlock', 'something'],
            ['ActionGrab', 'something'],
            ['ActionHit', 'something'],
            # give <something> to <somebody>
            ['ActionGiveTo', 'something', 'somebody'],
            ['ActionWaveHand', 'somebody'],
            ['ActionWaveHand', 'STOP'],
            # move to <somebody>'s attention
            ['ActionMoveToAttention', 'somebody'],
            ['ActionPointTo', 'somebody or something'],
            ['ActionPointTo', 'STOP'],
            ['ActionObserveAgent', 'somebody'],
            # follow somebody's gaze
            ['ActionFollowGaze', 'somebody'],
            ['ActionWait'],
            # nod head to somebody
            ['ActionNodHead', 'somebody'],
            ['ActionNodHead', 'STOP'],
            # shake head to somebody
            ['ActionShakeHead', 'somebody'],
            ['ActionShakeHead', 'STOP'],
            ['ActionPlay', 'something'],
            # put something1 into something2
            ['ActionPutInto', 'something1', 'something2'],
            # put something1 onto something2
            ['ActionPutOnto', 'something1', 'something2'],
            # put something down
            ['ActionPutDown', 'something'],
            # follow somebody's pointing
            ['ActionFollowPointing', 'somebody']]


# random action for single agent
def random_action(agent, W: World):
    action_template = random.choice(default_action_choices)
    action_name = action_template[0]
    # 单参数
    if len(action_template) == 2:
        if "somebody" in action_template[1] and "something" in action_template[1]:
            entity_tmp = random.choice(W.entities)
            return getattr(action, action_name)(agent, entity_tmp)
        elif "somebody" in action_template[1]:
            agent_tmp = random.choice(W.agents)
            return getattr(action, action_name)(agent, agent_tmp)
        elif "something" in action_template[1]:
            object_tmp = random.choice(W.objects)
            return getattr(action, action_name)(agent, object_tmp)
        else:
            return getattr(action, action_name)(agent, action_template[1])



def agent_step(agent, world, iter, session, args, frames):
    agent_pipeline(agent, world, args)
    other_agent = f'agent_{3 - agent.id}'
    log.info('seed: {}, iter {}: agent {} goal [{}]'.format(args.seed, iter, agent.id, agent.goal_name))
    log.info('seed: {}, iter {}: agent {} task [{}]'.format(args.seed, iter, agent.id, agent.task_name))

    action = random_action()

    action = act(agent, world, args, agent.id)

    mind_est = {}
    for _agent in agent.belief.agents:
        if _agent.id == agent.id:
            continue
        mind_est[f'agent_{_agent.id}'] = {'intent_est': _agent.intent_now.print() if _agent.intent_now else None,
                                          'desire_est': _agent.desire()}

    actions = [action]
    world.step(actions)

    record = InteractionRecord(round=iter,
                               agent=agent,
                               intent_now=agent.intent_now,
                               mind_est=mind_est,
                               action=action.name() if action else None,
                               policy=args.policy)
    session.add_round(record)

    name = None
    # action: given by algo
    if action is not None:
        name = action.name()
        # name.append(not agent.action_fail)
        # 标识当前动作执行的 iteration；
        name.append(iter)
        # print("Add history", name)
        agent.action_history.append(name)

        # 1226 把状态搞对；
        reset_gesture(agent)

    log.info("seed: {}, iter {}: agent {} action [{}]".format(args.seed, iter, agent.id, name))

    if args.show_whose_belief is not None:
        whose_belief = world.retrieve_by_id(int(args.show_whose_belief))
        whose_belief.observe(world, verbose=False)
        whose_belief.update_belief(world)
        this_frames, _ = world.render_belief(whose_belief, iter=iter, show_rect=args.showrect)
    else:
        this_frames = world.render(iter=iter, show_rect=args.showrect)

    record.video_start = f'{len(frames) * 1. / FPS:.4f}'
    frames.extend(this_frames)
    record.video_end = f'{len(frames) * 1. / FPS:.4f}'


@unique
class ScenarioFinishedStatus(Enum):
    # Normal termination
    SUCCESS = 'success'
    # Not finished within the maximum number of steps
    STOPPED = 'stopped'
    # Abnormal termination
    EXCEPTION = 'exception'


def scenario_play(args):
    pygame.init()
    if args.random_scenario:
        scenario_generator = intent_pool.Scenario_Generating()
        scenario = Scenario(AGENTS=scenario_generator.agents, OBJS=scenario_generator.objects,
                            LANDMARKS=scenario_generator.landmarks)
        args.scenario = scenario_generator.intent_name
        scenario.scenario_name = scenario_generator.intent_name if scenario.scenario_name == 'random' else scenario.scenario_name
    else:
        if args.epochs <= 1:
            scenario = Scenario(osp.join("./scenarios/{}".format(args.scenario), args.scenario + ".pkl"))
        else:
            args.scenario = random.choice(['container', 'cuptotable', 'baby',
                                           'multipointing', 'play_game',
                                           ])
            scenario = Scenario(osp.join("./scenarios/{}".format(args.scenario), args.scenario + ".pkl"))

    random.seed(args.seed)
    world = scenario.make_world(args.shuffle, mode='m2m', scenario_name=scenario.scenario_name, show=args.render)
    check_scenario = scenario_finish_check(world, args.scenario)
    check_intent = intent_finish_check(world)
    if not args.show_whose_belief:
        world.render_init()
        world.render()
    frames = []
    iter = 0
    finished_flag = False
    now = datetime.now().strftime('%Y%m%d%H%M')
    session = InteractionSession(session_id=f'{scenario.scenario_name}_{now}_{len(world.agents)}_{len(world.objects)}', policy=args.policy)

    desire_pair = f'{[round(n, 2) for n in world.retrieve_by_id(1).desire()]}_{[round(n, 2) for n in world.retrieve_by_id(2).desire()]}'

    try:
        while iter < 15:
            if finished_flag:
                break

            begin = time.time()

            log.info(">>>>>>>>>>>>>>>>>>>>>>>>[ round {} ]<<<<<<<<<<<<<<<<<<<<<<<".format(iter))
            for agent in world.agents:
                # 形式上地处理事件，防止程序卡住
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pass

                agent_step(agent, world, iter, session, args, frames)

                # for debug
                # eval_result = compute_score(session, world)

                if check_scenario(world, args.scenario):
                    finished_flag = True
                    break

            iter += 1
            end = time.time()

            if end - begin > 3:
                log.info("current round {} elapsed time: {}".format(iter, end - begin))
            gc.collect()
    except Exception as e:
        print(f'exception occurs: {e}')
        traceback.print_exc()
        return scenario.scenario_name, ScenarioFinishedStatus.EXCEPTION.value, session.session_id, None

    try:
        session.finished_status = ScenarioFinishedStatus.SUCCESS.value if finished_flag else ScenarioFinishedStatus.STOPPED.value
        eval_result = compute_score(session, world)
    except Exception as e:
        print(f'exception occurs: {e}')
        traceback.print_exc()
        return scenario.scenario_name, ScenarioFinishedStatus.EXCEPTION.value, session.session_id, None

    world.close()

    if args.save:

        session.export_to_csv(f'{args.savedir}/{session.session_id}_{desire_pair}.csv')
        # filename = 'demo_{}_{}_{}_{}_{}.mp4'.format(args.scenario, n_objs, now, args.seed, iter)
        filename = f'{session.session_id}.mp4'
        save_frames_as_video(args, frames, filename)

    if finished_flag:
        return scenario.scenario_name, ScenarioFinishedStatus.SUCCESS.value, session.session_id, eval_result
    return scenario.scenario_name, ScenarioFinishedStatus.STOPPED.value, session.session_id, eval_result


def main_protocol(args):
    flat_results = []
    for epoch in range(args.epochs):
        scenario_name, finished_status, session_id, eval_result = scenario_play(args)
        print(f'epoch: {epoch}, {scenario_name} has finished with: {finished_status}.')
        if finished_status == ScenarioFinishedStatus.EXCEPTION.value:
            continue
        agent_based_score_dict, total_score = eval_result
        agent_1_score_dict = agent_based_score_dict['agent_1']
        agent_2_score_dict = agent_based_score_dict['agent_2']

        flat_results.append([session_id, finished_status, total_score,
                             agent_1_score_dict['intent_score'], agent_1_score_dict['value_score'], agent_1_score_dict['total_score'],
                             agent_2_score_dict['intent_score'], agent_2_score_dict['value_score'], agent_2_score_dict['total_score']])

    if args.save:
        flat_results_df = pd.DataFrame(flat_results, columns=['session_id', 'finished_status', 'total_score',
                                                              'a1_intent_score', 'a1_value_score', 'a1_total_score',
                                                              'a2_intent_score', 'a2_value_score', 'a2_total_score'])
        today = datetime.now().strftime('%Y%m%d%H')
        save_evaluation_result(args, f'{today}_batch_{args.epochs}_eval.xlsx', flat_results_df)


if __name__ == "__main__":
    assert load_dotenv(override=True)

    parser = argparse.ArgumentParser(description=None)

    parser.add_argument('-s', '--scenario',
                        default="cuptotable",
                        choices=['chimpanzee', 'classroom', 'container', 'cuptotable',
                                 'helping', 'multipointing', 'play_game', 'sally_anne',
                                 'baby', 'refer_disambiguation'],
                        help='configuration file for scenario configuration')

    parser.add_argument('--policy', default='system', choices=['system', 'gpt'], help='which policy to use')
    parser.add_argument('--verbose', default=True, help='whether to print details or not')
    parser.add_argument('--shuffle', default=False,
                        help='whether to shuffle the init position and rotate of agent or not')
    # parser.add_argument('--save', default=False, help='whether to save the video or not')
    parser.add_argument('--save', default=False, action='store_true', help='whether to save the video or not')
    parser.add_argument('--savedir', default="./save/", help='whether to save the video or not')
    parser.add_argument('--seed', default=1234, type=int)
    parser.add_argument('--showrect', default=False, help='whether to show the rect of image')
    parser.add_argument('--show_whose_belief', default=None, help='whether to show whose belief')
    parser.add_argument('--render', default=False, action='store_true', help='whether to show the render or not')
    parser.add_argument('--epochs', default=1, type=int)
    parser.add_argument('--random_scenario', action='store_true',
                        help='whether choose to generate scenario with multi_objects')
    args = parser.parse_args()

    log.info(args)
    main_protocol(args)
