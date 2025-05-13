import logging
import os.path
from datetime import datetime
import pandas as pd
from dotenv import find_dotenv, load_dotenv
import gc
import json
import traceback
from core.plan import *
from core.update_intent import *
from core.inverse_infer_desire import *
from core.inverse_infer_belief import *
from core.inverse_infer_intent import *
from core.scenario import Scenario
from core.finish_check import scenario_finish_check, intent_finish_check
from scenarios.scenario_generating import intent_pool
from experiment_codes.llms.parse_state import caption_current_state_to_llm
from experiment_codes.llms.gpt_planner import context_agent_with_valid_action, context_tom_agent
from data_analysis.interaction_record import InteractionRecord, InteractionSession
from evaluation.metrics import compute_score
from utils.save import save_frames_as_video, save_evaluation_result, save_base64_frames_as_video
from core.const import ScenarioFinishedStatus, FPS, MAX_STEPS
import threading
import random
import glob
import pickle
import pickle
import os
import logging
import time

sys.path.append(".")
sys.path.append("../")

# Previous: 12345
RANDOM_SEED = 1234567
SELECTED_SCENARIO = None

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


class ScenarioCheckpointManager:
    """场景检查点管理器，用于保存和恢复整个场景状态"""
    
    def __init__(self, checkpoint_dir="./scenario_checkpoints"):
        """初始化场景检查点管理器"""
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.logger = logging.getLogger("ScenarioCheckpointManager")
        self.logger.info(f"场景检查点管理器初始化，保存目录: {checkpoint_dir}")
    
    def save_checkpoint(self, scenario_id, state_data):
        """保存场景检查点"""
        checkpoint_file = os.path.join(
            self.checkpoint_dir, 
            f"scenario_{scenario_id}.pkl"
        )
        
        # 创建临时文件，成功后再重命名，避免写入过程中崩溃导致检查点损坏
        temp_file = checkpoint_file + ".tmp"
        try:
            with open(temp_file, 'wb') as f:
                pickle.dump(state_data, f)
            
            # 如果之前的检查点存在，创建备份
            if os.path.exists(checkpoint_file):
                backup_file = checkpoint_file + ".bak"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(checkpoint_file, backup_file)
            
            # 重命名临时文件为正式检查点文件
            os.rename(temp_file, checkpoint_file)
            self.logger.info(f"成功保存场景检查点: {checkpoint_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存场景检查点失败: {e}")
            return False
    
    def load_checkpoint(self, scenario_id):
        """加载场景检查点"""
        checkpoint_file = os.path.join(
            self.checkpoint_dir, 
            f"scenario_{scenario_id}.pkl"
        )
        
        # 尝试加载检查点
        try:
            if not os.path.exists(checkpoint_file):
                self.logger.info(f"检查点文件不存在: {checkpoint_file}")
                return None
            
            with open(checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
            self.logger.info(f"成功加载场景检查点: {checkpoint_file}")
            return checkpoint_data
        except Exception as e:
            self.logger.error(f"加载检查点失败: {e}")
            
            # 尝试加载备份检查点
            backup_file = checkpoint_file + ".bak"
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, 'rb') as f:
                        checkpoint_data = pickle.load(f)
                    self.logger.info(f"从备份加载场景检查点: {backup_file}")
                    return checkpoint_data
                except Exception as e2:
                    self.logger.error(f"加载备份检查点也失败: {e2}")
            
            return None
    
    def cleanup_checkpoint(self, scenario_id):
        """清理检查点文件"""
        checkpoint_file = os.path.join(
            self.checkpoint_dir, 
            f"scenario_{scenario_id}.pkl"
        )
        backup_file = checkpoint_file + ".bak"
        
        try:
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
            if os.path.exists(backup_file):
                os.remove(backup_file)
            self.logger.info(f"成功清理场景检查点文件")
            return True
        except Exception as e:
            self.logger.error(f"清理场景检查点文件失败: {e}")
            return False


def agent_pipeline(agent, world, args):
    log.info("------------agent ID : {}-----------------".format(agent.id))
    s = time.time()
    # fixme, very time-consuming operation in later rounds, to be optimized
    agent.observe_and_update_belief(world, verbose=False)
    log.info(
        "agent {} belief, elapsed time: {}: [agent_ids {}], [object_ids {}], [landmark_ids {}]"
        .format(agent.id, time.time() - s,
                agent.belief.agent_ids, agent.belief.object_ids, agent.belief.landmark_ids)
    )
    if agent.belief.agent_ids is not None and len(agent.belief.agent_ids) > 0:
        for other_agent in agent.belief.agents:
            log.info(f"agent {other_agent.id} action history: {other_agent.action_history}")
        print(type(agent.belief))
        print(agent.belief.other_agent_action_history)
        log.info(f"other_agent_action_history: {agent.belief.other_agent_action_history}")
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


def agent_step(agent, world: World, iter, session, args, frames, local_tokenizer, local_model):
    agent_pipeline(agent, world, args)
    other_agent = f'agent_{3 - agent.id}'
    log.info('iter {}: agent {} goal [{}]'.format(iter, agent.id, agent.goal_name))
    log.info('iter {}: agent {} task [{}]'.format(iter, agent.id, agent.task_name))

    if args.policy == 'system':
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

    else:
        error_information = ''  
        error_history = []  # 用于记录所有尝试的错误
        # 记录大模型最终是否成功输出
        success_flag = False
        
        for attempt in range(args.try_times):
            try:
                current_state_desc = caption_current_state_to_llm(agent, world)
                current_state_desc['previous_action_error'] = error_information
            
                tom_resp = context_tom_agent(agent, timestamp=iter, 
                                        your_state=current_state_desc, 
                                        W=world, other_agent_id=other_agent,
                                        model=args.model, source=args.source, 
                                        gpt_record_file_path=args.gpt_record_file_path)
                
                action, intention_resp, estimation_resp = tom_resp
                intention_estimation = estimation_resp.intent_estimation
                values_estimation = estimation_resp.values_estimation
                actions = [action]
            except Exception as e:
                error_history.append(str(e))
                error_information = "\n".join(error_history)
                print(f"Error in attempt {attempt + 1} (step_1): {str(e)}")
                continue
            
            try:
                world.step(actions)
                # 执行成功，记录并退出循环
                record = InteractionRecord(
                    round=iter,
                    agent=agent,
                    intent_now=intention_resp.intention_formatter,
                    mind_est={other_agent: {
                        'intent_est': intention_estimation.intention_formatter,
                        'desire_est': str(values_estimation)
                    }},
                    action=action.name(),
                    policy=args.policy,
                    prompt='',
                    resp='',
                    token_usage=''
                )
                session.add_round(record)
                agent.intent_history_llm.append(intention_resp.intention_desc)
                agent.other_intent_history_llm.append(intention_estimation.intention_desc)
                success_flag = True
                break
                
            except Exception as e:
                # 记录新的错误信息
                new_error = f"Attempt {attempt + 1}: When executing action {action.name()}, {str(e)}"
                error_history.append(new_error)
                # 累积所有错误信息
                error_information = "\n".join(error_history)
                print(f"Error in attempt {attempt + 1} (step_2): {new_error}")
                continue
        
        # 如果所有尝试都失败，记录到日志
        if len(error_history) == args.try_times:
            log.warning(f"All {args.try_times} attempts failed for agent {agent.id} at iteration {iter}")
            log.warning(f"Error history:\n{error_information}")

    name = None
    # action: given by algo
    if action is not None:
        name = action.name()
        # name.append(not agent.action_fail)
        # 标识当前动作执行的 iteration；
        name.append(iter)
        # format of action_history(action_name_list, iteration)
        agent.action_history.append(name)

        # 1226 把状态搞对；
        reset_gesture(agent)

    log.info("iter {}: agent {} action [{}]".format(iter, agent.id, name))

    if args.show_whose_belief is not None:
        whose_belief = world.retrieve_by_id(int(args.show_whose_belief))
        whose_belief.observe(world, verbose=False)
        whose_belief.update_belief(world)
        this_frames, _ = world.render_belief(whose_belief, iter=iter, current_agent=agent)

    else:
        this_frames = world.render(iter=iter, show_names=args.show_names, current_agent=agent)

    record.video_start = f'{len(frames) * 1. / FPS:.4f}'
    frames.extend(this_frames)
    record.video_end = f'{len(frames) * 1. / FPS:.4f}'


def scenario_play(args, local_tokenizer, local_model):
    # 初始化检查点管理器
    checkpoint_manager = ScenarioCheckpointManager()
    scenario_id = f"{args.scenario}_{datetime.now().strftime('%Y%m%d')}"
    
    # 尝试加载检查点
    checkpoint = checkpoint_manager.load_checkpoint(scenario_id)
    if checkpoint:
        # 从检查点恢复状态
        log.info(f"从检查点恢复场景状态: {scenario_id}")
        scenario = checkpoint['scenario']
        world = checkpoint['world']
        session = checkpoint['session']
        frames = checkpoint['frames']
        iter = checkpoint['iter']
        finished_flag = checkpoint['finished_flag']
        desire_pair = checkpoint['desire_pair']
    else:
        # 正常初始化场景
        pygame.init()
        if args.random_scenario:
            scenario_generator = intent_pool.Scenario_Generating()
            scenario = Scenario(AGENTS=scenario_generator.agents, OBJS=scenario_generator.objects,
                                LANDMARKS=scenario_generator.landmarks)
            args.scenario = scenario_generator.intent_name
            scenario.scenario_name = scenario_generator.intent_name if scenario.scenario_name == 'random' else scenario.scenario_name
            world = scenario.make_world(mode='m2m', scenario_name=scenario.scenario_name, show=args.render)
        elif args.data_scenario:
            # 指定文件夹路径
            folder_path = './data/grouped_data_pickle/*.pkl'  # 请根据需要修改路径
            pkl_files = glob.glob(folder_path)
            selected_file = random.choice(pkl_files) if pkl_files else None
            
            args.scenario_save_name = selected_file.split("/")[-1]  # 先获取文件名
            args.scenario_save_name = args.scenario_save_name.rsplit(".", 1)[0] 

            with open(selected_file, "rb") as f:
                data_raw_tmp = pd.read_pickle(f)

            data_raw_tmp = data_raw_tmp.reset_index(drop=True)
            objects = data_raw_tmp['world_objs'].apply(pickle.loads)[0]
            landmarks = data_raw_tmp['world_landmarks'].apply(pickle.loads)[0]
            agents = data_raw_tmp['world_agents'].apply(pickle.loads)[0]

            # 对于已经存储好的agent，需要在belief 中添加 ther_agent_action_history
            for agent in agents:
                agent.belief.other_agent_action_history = []
                # 由于数据读取时可能有其他的action已经被执行，所以选择重置agent的姿态，避免这部分的信息影响决策
                agent.reset_gestures()
            
            scenario = Scenario(AGENTS=agents, OBJS=objects, LANDMARKS=landmarks)
            scenario.scenario_name = data_raw_tmp['scenario'].apply(lambda x: pickle.loads(x) if isinstance(x, bytes) else x).tolist()[0]
            world = scenario.make_world(mode='m2m', scenario_name=scenario.scenario_name, show=args.render)

        else:
            if args.epochs <= 1:
                scenario = Scenario(osp.join("./scenarios/{}".format(args.scenario), args.scenario + ".pkl"))
            else:
                args.scenario = random.choice(['container', 'cuptotable', 'baby',
                                               'multipointing', 'play_game',
                                               'chimpanzee'])
                scenario = Scenario(osp.join("./scenarios/{}".format(args.scenario), args.scenario + ".pkl"))

            world = scenario.make_world(args.shuffle, mode='m2m', scenario_name=scenario.scenario_name, show=args.render)

        # fully sample
        for agent in world.agents:
            agent.desire = Desire.sample()

        check_scenario = scenario_finish_check(world, args.scenario)
        check_intent = intent_finish_check(world)
        # del scenario
        # God's perspectives
        if not args.show_whose_belief:
            world.render_init()
            world.render()
        else:
            the_agent = world.retrieve_by_id(int(args.show_whose_belief))
            the_agent.observe(world, verbose=False)
            the_agent.update_belief(world)
            inverse_infer_intent(the_agent, world, args)
            world.render_agent_belief(world.retrieve_by_id(int(args.show_whose_belief)))
            world.render_belief(world.retrieve_by_id(int(args.show_whose_belief)))

        frames = []
        iter = 0
        finished_flag = False
        now = datetime.now().strftime('%Y%m%d%H%M')
        session = InteractionSession(session_id=f'{scenario.scenario_name}_{now}_{len(world.agents)}_{len(world.objects)}', policy=args.policy)

        desire_pair = f'{[round(n, 2) for n in world.retrieve_by_id(1).desire()]}_{[round(n, 2) for n in world.retrieve_by_id(2).desire()]}'
    
    try:
        while iter < MAX_STEPS:
            if finished_flag:
                break

            begin = time.time()

            # 在每次迭代前保存检查点
            checkpoint_data = {
                'scenario': scenario,
                'world': world,
                'session': session,
                'frames': frames,
                'iter': iter,
                'finished_flag': finished_flag,
                'desire_pair': desire_pair,
                'timestamp': time.time()
            }
            checkpoint_manager.save_checkpoint(scenario_id, checkpoint_data)

            log.info(">>>>>>>>>>>>>>>>>>>>>>>>[ round {} ]<<<<<<<<<<<<<<<<<<<<<<<".format(iter))
            for agent in world.agents:
                # 形式上地处理事件，防止程序卡住
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pass

                agent_step(agent, world, iter, session, args, frames, local_tokenizer, local_model)
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
        session.finished_status = ScenarioFinishedStatus.EXCEPTION
        return scenario, session, None, None, None

    # 场景成功完成，清理检查点
    checkpoint_manager.cleanup_checkpoint(scenario_id)
    
    thread = None

    try:
        session.finished_status = ScenarioFinishedStatus.SUCCESS if finished_flag else ScenarioFinishedStatus.STOPPED
        eval_result = compute_score(session, world)
    except Exception as e:
        print(f'exception occurs: {e}')
        traceback.print_exc()
        session.finished_status = ScenarioFinishedStatus.EXCEPTION
        return scenario, session, None, None, None

    world.close()

    video_name = f'{args.scenario_save_name}_{session.finished_status.value}_{session.policy}_{session.session_id}.mp4'

    if args.save:
        thread = threading.Thread(target=save_data, args=(args, session, desire_pair, frames, video_name))
        thread.start()

    return scenario, session, eval_result, {video_name: world.entities_names_dict()}, thread


def save_data(args, session, desire_pair, frames, video_name):
    if args.save:
        session.export_to_csv(args.savedir, f'{args.scenario_save_name}_{session.finished_status.value}_{session.policy}_{session.session_id}_{desire_pair}_{SELECTED_SCENARIO}.csv')
        # save_frames_as_video(args, frames, video_name)
        save_base64_frames_as_video(args, frames, video_name)

def main_protocol(args):
    flat_results = []
    path = args.savedir
    LEN = 0
    if os.path.exists(os.path.join(path, f'eval.xlsx')):
    
        df = pd.read_excel(os.path.join(path, f'eval.xlsx'), engine='openpyxl')
        flat_results = df.values.tolist()
        
        LEN = flat_results[-1][0] + 1
        random.seed(random.randint(1, 65535))
    else:
        flat_results = []

    if args.local_model:
        from experiment_codes.llms.llm_models import llama3_load_model
        local_tokenizer, local_model = llama3_load_model()
    else:
        local_tokenizer = None
        local_model = None

    # for the video annotation
    video_meta_dict = {}

    for epoch in range(args.epochs):
        scenario, session, eval_result, names_dict, thread = scenario_play(args, local_tokenizer, local_model)
        print(f'epoch: {epoch}, {scenario.scenario_name} has finished with: {session.finished_status.value}.')
        if session.finished_status == ScenarioFinishedStatus.EXCEPTION:
            continue

        video_meta_dict.update(names_dict)

        agent_based_score_dict, total_score = eval_result
        agent_1_score_dict = agent_based_score_dict['agent_1']
        agent_2_score_dict = agent_based_score_dict['agent_2']
        desire_pair = scenario.desire_pair

        flat_results.append([epoch + LEN, session.session_id, session.finished_status.value, total_score,
                             agent_1_score_dict['accept_status'],
                             desire_pair['agent_1'] if desire_pair else 'None',
                             agent_1_score_dict['total_score'],
                             agent_1_score_dict['rational_score'],
                             agent_1_score_dict['intent_score'], agent_1_score_dict['value_score'],
                             agent_1_score_dict['value_score_list'],
                             desire_pair['agent_2'] if desire_pair else 'None',
                             agent_2_score_dict['total_score'],
                             agent_2_score_dict['rational_score'],
                             agent_2_score_dict['intent_score'], agent_2_score_dict['value_score'],
                             agent_2_score_dict['value_score_list']])

        if epoch % 5 == 0:

            if args.save:
                today = datetime.now().strftime('%Y%m%d%H')

                # with open(f'{args.savedir}/{today}_video_meta_info.json', 'w') as f:
                with open(os.path.join(args.savedir, f'{today}_video_meta_info.json'), 'w') as f:
                    json.dump(video_meta_dict, f)

                flat_results_df = pd.DataFrame(flat_results, columns=['epoch', 'session_id', 'finished_status',
                                                                    'total_score',
                                                                    'accept_status',
                                                                    'a1_desire', 'a1_total_score',
                                                                    'a1_rational_score',
                                                                    'a1_intent_score', 'a1_value_score',
                                                                    'a1_value_score_list',
                                                                    'a2_desire', 'a2_total_score',
                                                                    'a2_rational_score',
                                                                    'a2_intent_score', 'a2_value_score',
                                                                    'a2_value_score_list'])
                save_evaluation_result(args, f'eval.xlsx', flat_results_df)
                # save_evaluation_result(args, f'{today}_batch_{args.epochs}_eval.xlsx', flat_results_df)

            if thread is not None:
                thread.join()


if __name__ == "__main__":
    # load env
    assert load_dotenv(find_dotenv(filename='.env', raise_error_if_not_found=True))
    os.environ["LANGCHAIN_PROJECT"] = f'mmrp_{datetime.now().strftime("%m%d-%H-%M")}'
    
    parser = argparse.ArgumentParser(description=None)

    parser.add_argument('-s', '--scenario',
                        default="cuptotable",
                        choices=['chimpanzee', 'classroom', 'container', 'cuptotable',
                                 'helping', 'multipointing', 'play_game', 'sally_anne',
                                 'baby', 'refer_disambiguation'],
                        help='configuration file for scenario configuration')

    parser.add_argument('--policy', default='system', choices=['system', 'gpt'], help='which policy to use')
    parser.add_argument('--model', default='gpt-4o-2024-08-06',
                        choices=['deepseek', 
                                 'gpt-35-turbo-0125', 
                                 'gpt-4o-mini-2024-07-18',
                                 'gpt-4-turbo-2024-04-09',
                                 'gpt-4o-2024-08-06', 
                                 'claude-3-7-sonnet-20250219'],
                        help='which llm model to use')
    parser.add_argument('--source', choices=['bigai', 'claude'], default='bigai', help='which api key to use')
    parser.add_argument('--verbose', default=True, help='whether to print details or not')
    parser.add_argument('--shuffle', default=False,
                        help='whether to shuffle the init position and rotate of agent or not')
    # parser.add_argument('--save', default=False, help='whether to save the video or not')
    parser.add_argument('--save', default=False, action='store_true', help='whether to save the video or not')
    parser.add_argument('--savedir', default="./save", help='whether to save the video or not')

    parser.add_argument('--show_names', default=True, help='whether to show the names of agents and objects')
    parser.add_argument('--show_whose_belief', default=None, help='whether to show whose belief')
    parser.add_argument('--render', default=False, action='store_true', help='whether to show the render or not')

    parser.add_argument('--epochs', default=1, type=int)
    parser.add_argument('--random_scenario', action='store_true',
                        help='whether choose to generate scenario with multi_objects')
    parser.add_argument('--data_scenario', action='store_true',
                        help='whether choose to use scenario from human data')
    parser.add_argument('--local_model', default=False, action='store_true', help='whether to use llama3 local model')
    parser.add_argument('--offline_experiment', default=True, action='store_true', help='whether to create and maintain specific room')
    parser.add_argument('--try_times', default=5, help='the times of trying to get a valid action')
    parser.add_argument('--gpt_record_file_path', default='./gpt_record.json', help='the path to record the gpt input and response')
    args = parser.parse_args()

    args.scenario_save_name = ""

    log.info(args)

    # python main_m2m.py --policy gpt --model gpt-4o-2024-08-06 --source bigai --render --save --data_scenario
    # python main_m2m.py --policy gpt --model claude-3-7-sonnet-20250219 --source claude --render --save --data_scenario
    # cuptotable is the default scenario
    main_protocol(args)
