import sys

sys.path.append(".")

from openai import AzureOpenAI
import os, os.path
import random
import requests
import traceback
import anthropic

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import argparse
import json
import pandas as pd
import ast
from datetime import datetime
import time
from tqdm import tqdm
import logging

import subprocess
import torch
import threading
from copy import deepcopy

lock = threading.Lock()



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('experiment_debug.log')
    ]
)

logger = logging.getLogger(__name__)

import sys

sys.path.append(".")

from experiment_codes.llms.exp_prompts import *

import importlib
# 先把模块载入
# from awq.modules.linear.gemm import user_has_been_warned

# Configure logging

logger.info("Import Finished")

def test_import_time(module_name):
    """Measure time to import a module."""
    t0 = time.time()
    module = __import__(module_name)
    t1 = time.time()
    return t1 - t0

def test_cuda_initialization():
    """Test torch import and CUDA initialization time."""
    import torch
    t0 = time.time()
    count = torch.cuda.device_count()
    t1 = time.time()
    return count, t1 - t0

def check_local_conflict(module_name):
    """Check for local files/directories that might conflict with module imports."""
    cwd = os.getcwd()
    conflicts = []
    candidates = [module_name + '.py', module_name]
    for name in candidates:
        path = os.path.join(cwd, name)
        if os.path.exists(path):
            conflicts.append(path)
    return conflicts

def run_pip_check():
    """Run `pip check` to detect dependency conflicts."""
    try:
        output = subprocess.check_output([sys.executable, "-m", "pip", "check"], stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        output = e.output
    return output

def check_cache_dir():
    """Check HuggingFace cache directory existence and permissions."""
    cache_env = os.environ.get("TRANSFORMERS_CACHE") or os.path.expanduser("~/.cache/huggingface")
    exists = os.path.exists(cache_env)
    perms = None
    if exists:
        perms = oct(os.stat(cache_env).st_mode)[-3:]
    return cache_env, exists, perms



def read_json(file_path):
    """读取JSON文件
    如果文件不存在，静默返回None
    如果JSON格式错误，返回None"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"JSON decode error in file: {file_path}")
        return None

def save_json(data, file_path):
    """保存数据到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {str(e)}")


def wait_until_ready(timeout=600):
    url = "http://localhost:8000/v1/models"
    start_time = time.time()
    while True:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print("✅ vLLM 服务已就绪")
                break
        except requests.exceptions.RequestException:
            print("❌ vLLM 服务未就绪")
            pass  # 服务未就绪
        if time.time() - start_time > timeout:
            raise TimeoutError("⏱️ 等待 vLLM 服务启动超时")
        time.sleep(10)

def generate_action_option_dict(agent_name_id_list, object_name_id_list):

    name_id_list = deepcopy(agent_name_id_list + object_name_id_list)

    return {
        'ActionWait': [],
        'ActionWaveHand': [deepcopy(agent_name_id_list)],
        'ActionNodHead': [deepcopy(agent_name_id_list)],
        'ActionShakeHead': [deepcopy(agent_name_id_list)],
        'ActionMoveToAttention': [deepcopy(agent_name_id_list)],
        'ActionPointTo': [deepcopy(name_id_list)],
        'ActionObserveAgent': [deepcopy(agent_name_id_list)],
        'ActionPlay': [deepcopy(object_name_id_list), deepcopy(agent_name_id_list)],
        'ActionFollowPointing': [deepcopy(agent_name_id_list)], 
        'ActionPutDown': [deepcopy(object_name_id_list)],
        'ActionEat': [deepcopy(object_name_id_list)], 
        'ActionSmash': [deepcopy(object_name_id_list)],
        'ActionOpen': [deepcopy(object_name_id_list)],
        'ActionClose': [deepcopy(object_name_id_list)],
        'ActionGrab': [deepcopy(object_name_id_list)],
        'ActionMoveTo': [deepcopy(name_id_list) + ['XY']],
        'ActionRotateTo': [deepcopy(name_id_list) + ['XY']],
        'ActionUnlock': [deepcopy(object_name_id_list), deepcopy(object_name_id_list)],
        'ActionGiveTo': [deepcopy(object_name_id_list), deepcopy(agent_name_id_list)],
        'ActionPutInto': [deepcopy(object_name_id_list), deepcopy(object_name_id_list)],
        'ActionPutOnto': [deepcopy(object_name_id_list), deepcopy(object_name_id_list)],
        'ActionSpeak': [['Hello!', 'Thank you!']], 
        'ActionPerform': [['eat', 'drink']],
    }

def generate_intent_option_dict(agent_name_id_list, object_name_id_list) -> dict:
    intent_pool = ['Observe', 'Get', 'Give', 'Find', 'Open', 'PutInto', 'PutOnto',
                   'Greet', 'PlayWith', 'Inform', 'RespondTo', 'Harm', 'Help', 'RequestHelp']

    intent_option_dict = {}

    name_id_list = deepcopy(agent_name_id_list + object_name_id_list)

    for intent_name in intent_pool:
        if intent_name in ['Observe']:
            intent_option_dict['Observe'] = [deepcopy([f'world'] + name_id_list)]
        elif intent_name in ['Find']:
            intent_option_dict['Find'] = [deepcopy(name_id_list)]
        elif intent_name in ['Get']:
            intent_option_dict['Get'] = [deepcopy(object_name_id_list)]
        elif intent_name in ['Give']:
            intent_option_dict['Give'] = [deepcopy(object_name_id_list), deepcopy(agent_name_id_list)]
        elif intent_name in ['Open']:
            intent_option_dict['Open'] = [deepcopy(object_name_id_list)]
        elif intent_name in ['PutInto']:
            intent_option_dict['PutInto'] = [deepcopy(object_name_id_list), deepcopy(object_name_id_list)]
        elif intent_name in ['PutOnto']:
            intent_option_dict['PutOnto'] = [deepcopy(object_name_id_list), deepcopy(object_name_id_list)]
        elif intent_name in ['Greet']:
            intent_option_dict['Greet'] = [deepcopy(agent_name_id_list)]
        elif intent_name in ['PlayWith']:
            intent_option_dict['PlayWith'] = [deepcopy(object_name_id_list), deepcopy(agent_name_id_list)]
        elif intent_name in ['Inform']:
            intent_option_dict['Inform'] = [deepcopy(agent_name_id_list), deepcopy(object_name_id_list)]
        elif intent_name in ['RespondTo']:
            intent_option_dict['RespondTo'] = [deepcopy(agent_name_id_list)]
        elif intent_name in ['Harm']:
            intent_option_dict['Harm'] = [deepcopy(agent_name_id_list)]
        elif intent_name in ['Help']:
            intent_option_dict['Help'] = [deepcopy(agent_name_id_list)]
        elif intent_name in ['RequestHelp']:
            intent_option_dict['RequestHelp'] = [deepcopy(agent_name_id_list)]

    return intent_option_dict

def run(args):
    logger.info(f"Starting experiment: {args.EXP_NAME}")
    logger.info(f"Using model: {args.MODEL}")
    logger.info(f"Dataset path: {args.DATASET_PATH}")
    logger.info(f"Result save path: {args.RESULT_SAVE_PATH}")
    
    prompt_to_test = read_json(args.DATASET_PATH)
    tested_data_dict = read_json(args.RESULT_SAVE_PATH)
    DATA_LENGTH = len(prompt_to_test.keys())
    logger.info(f"Total data length: {DATA_LENGTH}")
    if tested_data_dict is None:
        logger.info("No existing tested_id_dict found, initializing new tested_id_dict")
        tested_data_dict = {}

    # 使用tqdm显示进度
    progress_bar = tqdm(total=DATA_LENGTH * args.TEST_RATIO, desc=args.EXP_NAME)

    testing_id = 0
    all_threads = []

    while testing_id < DATA_LENGTH * args.TEST_RATIO:
        if tested_data_dict.get(str(testing_id)) is not None:
            print(f"样本 {testing_id} 已测试过，跳过")
            testing_id += 1
            continue
        # 更新进度条

        # 获取信号量
        semaphore.acquire()

        thread = threading.Thread(target=send_prompt, args=(args, prompt_to_test[str(testing_id)], progress_bar, testing_id, tested_data_dict, semaphore))
        thread.start()

        all_threads.append(thread)

        testing_id += 1

    # 等待所有线程完成
    for thread in all_threads:
        thread.join()

    # 关闭进度条
    progress_bar.close()

def select_random_intent(intent_option_dict, testing_agent_id):
    # 随机选择一个intent
    intent_name = random.choice(list(intent_option_dict.keys()))
    if intent_name in ['Help', 'RequestHelp', 'Harm']:
        other_intent_name = random.choice(list(intent_option_dict.keys()))
        while other_intent_name in ['Help', 'RequestHelp', 'Harm']:
            other_intent_name = random.choice(list(intent_option_dict.keys()))
        intent_option_list = []
        for i in range(len(intent_option_dict[other_intent_name])):
            if len(intent_option_dict[other_intent_name][i]) > 0:
                intent_option_list.append(random.choice(intent_option_dict[other_intent_name][i]))
        return '-'.join([intent_name] + [f"agent_{3-testing_agent_id}"] + [other_intent_name] + intent_option_list)

    intent_option_list = []
    for i in range(len(intent_option_dict[intent_name])):
        if len(intent_option_dict[intent_name][i]) > 0:
            intent_option_list.append(random.choice(intent_option_dict[intent_name][i]))

    return '-'.join([intent_name] + intent_option_list)

def select_random_action(action_option_dict):
    action_name = random.choice(list(action_option_dict.keys()))
    action_option_list = []
    for i in range(len(action_option_dict[action_name])):
        if len(action_option_dict[action_name][i]) > 0:
            action_option_list.append(random.choice(action_option_dict[action_name][i]))
    return '-'.join([action_name] + action_option_list)

def send_prompt(args, prompt_dict, progress_bar, testing_id, tested_data_dict, semaphore):
    logger.info(f"Starting model inference for sample {testing_id}")
    start_time = time.time()
    
    # 添加重试机制
    max_retries = 3  # 最大重试次数
    retry_delay = 2  # 初始重试延迟（秒）
    retry_count = 0
    success = False

    prompt = prompt_dict['prompt']

    while not success and retry_count < max_retries:
        try:
            if retry_count > 0:
                logger.warning(f"重试 #{retry_count} - 为样本 {testing_id} 调用模型...")
                
            if args.MODEL == "gpt-4o":
                from openai import AzureOpenAI

                logger.info("Initializing Azure OpenAI client...")

                REGION = ""
                API_KEY = ""

                API_BASE = ""
                ENDPOINT = f"{API_BASE}/{REGION}"

                client = AzureOpenAI(
                    api_key=API_KEY,
                    api_version="2024-09-01-preview",
                    azure_endpoint=ENDPOINT,
                )

                logger.info("Sending request to Azure OpenAI...")
                response = client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=2048
                )

                logger.info("Response received from Azure OpenAI")
                response_to_store = response.choices[0].message.content
                success = True
            elif args.MODEL == "Gemini":
                from google import genai

                client = genai.Client(api_key="")

                response = client.models.generate_content(
                    model="gemini-2.5-pro-preview-05-06", contents=prompt
                )
                response_to_store = response.text
                success = True
            elif args.MODEL == "DeepSeek-R1":
                API_KEY = ""

                from openai import OpenAI

                client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

                response = client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                )

                reasoning_content = response.choices[0].message.reasoning_content

                response_to_store = response.choices[0].message.content
                reasoning_to_store = reasoning_content
                success = True
            elif args.MODEL == "DEBUG":
                response_to_store = "DEBUG"
                success = True
            elif args.MODEL == "Qwen3-8B":
                import openai
                from openai import OpenAI

                client = OpenAI(
                    api_key="EMPTY",
                    base_url=f"http://localhost:{args.PORT}/v1"
                )

                response = client.chat.completions.create(
                    model=str(args.MODEL_PATH),
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_to_store = response.choices[0].message.content
                success = True
                
            elif args.MODEL == "Llama3":
                import openai
                from openai import OpenAI

                client = OpenAI(
                    api_key="EMPTY",
                    base_url=f"http://localhost:{args.PORT}/v1"
                )

                response = client.chat.completions.create(
                    model=str(args.MODEL_PATH),
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_to_store = response.choices[0].message.content
                success = True

            elif args.MODEL == "QwQ-AWQ":
                import openai
                from openai import OpenAI

                client = OpenAI(
                    api_key="EMPTY",
                    base_url=f"http://localhost:{args.PORT}/v1"
                )

                response = client.chat.completions.create(
                    model=str(args.MODEL_PATH),
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                response_to_store = response.choices[0].message.content
                success = True

            elif args.MODEL == "Claude":
                client = anthropic.Anthropic(api_key="")

                response = client.messages.create(
                    model="claude-3-7-sonnet-20250219",  # 可选: claude-3-sonnet, claude-3-haiku
                    max_tokens=2048,
                    temperature=0,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                print(response.content)
                response_to_store = response.content[0].text
                success = True

            elif args.MODEL == "Random":
                if 'value' in args.EXP_NAME:
                    response_to_store = {
                        'active': random.uniform(0, 1),
                        'active_cf': 1, 
                        'social': random.uniform(0, 1),
                        'social_cf': 1,
                        'helpful': random.uniform(-1, 2),
                        'helpful_cf': 1
                    }
                    
                elif 'intent' in args.EXP_NAME:
                    data_dict = read_json(args.DATASET_PATH)[str(testing_id)]
    
                    state_list = data_dict['state_prompt']
                    test_agent_id_list = int(data_dict['intent'][6])

                    name_id_list = []
                    agent_name_id_list = []
                    object_name_id_list = []

                    for state in state_list:
                        name_id_list += state[2]
                        
                    for name in name_id_list:
                        if name == 'agent_1' or name == 'agent_2':
                            agent_name_id_list.append(name)
                        else:
                            if not 'landmark' in name:
                                object_name_id_list.append(name)

                    intent_option_dict = generate_intent_option_dict(agent_name_id_list, object_name_id_list)

                    if 'update' in args.EXP_NAME:
                        most_possible_intent = select_random_intent(intent_option_dict, 3-test_agent_id_list)
                        second_possible_intent = select_random_intent(intent_option_dict, 3-test_agent_id_list)
                        third_possible_intent = select_random_intent(intent_option_dict, 3-test_agent_id_list)
                    else:
                        most_possible_intent = select_random_intent(intent_option_dict, test_agent_id_list)
                        second_possible_intent = select_random_intent(intent_option_dict, test_agent_id_list)
                        third_possible_intent = select_random_intent(intent_option_dict, test_agent_id_list)

                    response_to_store = {
                        'most_possible_intention': most_possible_intent,
                        'most_possible_intention_cf': 0.9,
                        'second_possible_intention': second_possible_intent,
                        'second_possible_intention_cf': 0.5,
                        'third_possible_intention': third_possible_intent,
                        'third_possible_intention_cf': 0.1,
                    }

                elif 'action' in args.EXP_NAME:
                    data_dict = read_json(args.DATASET_PATH)[str(testing_id)]    
    
                    state_list = data_dict['state_prompt']
                    test_agent_id_list = int(data_dict['intent'][6])

                    name_id_list = []
                    agent_name_id_list = []
                    object_name_id_list = []

                    for state in state_list:
                        name_id_list += state[2]
                        
                    for name in name_id_list:
                        if name == 'agent_1' or name == 'agent_2':
                            agent_name_id_list.append(name)
                        else:
                            if not 'landmark' in name:
                                object_name_id_list.append(name)
                    
                    action_option_dict = generate_action_option_dict(agent_name_id_list, object_name_id_list)

                    if 'update' in args.EXP_NAME:
                        most_possible_action = select_random_action(action_option_dict)
                        second_possible_action = select_random_action(action_option_dict)
                        third_possible_action = select_random_action(action_option_dict)
                    else:
                        most_possible_action = select_random_action(action_option_dict)
                        second_possible_action = select_random_action(action_option_dict)
                        third_possible_action = select_random_action(action_option_dict)

                    response_to_store = {
                        'most_possible_action': most_possible_action,
                        'most_possible_action_cf': 0.9,
                        'second_possible_action': second_possible_action,
                        'second_possible_action_cf': 0.5,
                        'third_possible_action': third_possible_action,
                        'third_possible_action_cf': 0.1,
                    }
                        
                success = True

        except (requests.exceptions.RequestException, 
                requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout, 
                requests.exceptions.HTTPError,
                anthropic.RateLimitError,
                anthropic.APIError,
                anthropic.APIConnectionError,
                anthropic.APITimeoutError) as e:
            retry_count += 1
            if retry_count < max_retries:
                # 指数退避策略
                sleep_time = retry_delay * (2 ** (retry_count - 1)) + random.uniform(0, 1)
                logger.warning(f"API错误: {str(e)}, 将在 {sleep_time:.2f} 秒后重试 ({retry_count}/{max_retries})")
                time.sleep(sleep_time)
            else:
                logger.error(f"达到最大重试次数 ({max_retries}), 放弃样本 {testing_id}")
                response_to_store = f"ERROR: 达到最大重试次数后请求失败: {str(e)}"
                break
                
        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"GPU内存溢出错误: {str(e)}")
            # 对于GPU内存错误，尝试清理缓存后再重试
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            retry_count += 1
            if retry_count < max_retries:
                sleep_time = retry_delay * (2 ** (retry_count - 1))
                logger.warning(f"内存错误，清理缓存后将在 {sleep_time:.2f} 秒后重试 ({retry_count}/{max_retries})")
                time.sleep(sleep_time)
            else:
                logger.error(f"达到最大重试次数 ({max_retries}), 放弃样本 {testing_id}")
                response_to_store = f"ERROR: GPU内存溢出错误，达到最大重试次数: {str(e)}"
                break
                
        except Exception as e:
            logger.error(f"未预期错误: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            retry_count += 1
            if retry_count < max_retries:
                sleep_time = retry_delay * (2 ** (retry_count - 1)) + random.uniform(0, 1)
                logger.warning(f"发生错误，将在 {sleep_time:.2f} 秒后重试 ({retry_count}/{max_retries})")
                time.sleep(sleep_time)
            else:
                logger.error(f"达到最大重试次数 ({max_retries}), 放弃样本 {testing_id}")
                response_to_store = f"ERROR: 未知错误，达到最大重试次数: {str(e)}"
                break

    if success:
        progress_bar.update(1)
    
    end_time = time.time()
    cost_time = end_time - start_time

    prompt_dict['response'] = response_to_store
    prompt_dict['cost_time'] = cost_time

    

    lock.acquire()
    try:
        tested_data_dict[testing_id] = prompt_dict
        save_json(tested_data_dict, args.RESULT_SAVE_PATH)
    finally:
        lock.release()
        semaphore.release()

def parse_arguments():

    parser=argparse.ArgumentParser(description='raw data processing')
    parser.add_argument('--REGION', default="")
    parser.add_argument('--API_KEY', default="")
    parser.add_argument('--API_BASE', default="")
    parser.add_argument('--ENDPOINT', default="")
    parser.add_argument('--RESULT_SAVE_PATH', default="")
    parser.add_argument('--EXP-NAME', default="")
    parser.add_argument('--TEST_RATIO', default=1)
    parser.add_argument('--GENERATE_PROMPT', default=True)
    parser.add_argument('--USE_GT_INFER', default=False)
    parser.add_argument('--MODEL', default="QwQ", choices=["gpt-4o", "Claude", "Gemini", "DeepSeek-R1", "Llama3", "Qwen3-8B", "DEBUG", "Random"])
    parser.add_argument('--GPU_NUM', default=1)
    parser.add_argument('--BATCH_SIZE', default=1)
    parser.add_argument('--PORT', default=8000)
    praser.add_argument('--MODEL_PATH', default="")

    return parser.parse_args()

if __name__ == "__main__":

    args = parse_arguments()

    # common
    args.TEST_VERSION = 'V1'

    # 创建一个信号量对象，最多允许10个线程同时运行
    semaphore = threading.Semaphore(int(args.BATCH_SIZE))

    API_MODEL_LIST = ['gpt-4o', 'Gemini', 'Claude', 'DeepSeek-R1', 'Random']

    if args.MODEL == "QwQ":
        logger.info("Loading QwQ model...")
        import requests
        import time
        import signal

        vllm_process = subprocess.Popen(
            [
                "python3", "-m", "vllm.entrypoints.openai.api_server",
                "--model", str(args.MODEL_PATH),
                "--port", str(args.PORT),
                "--tensor-parallel-size", str(args.GPU_NUM),
                "--gpu-memory-utilization", "0.9"
            ],
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
        )

    elif args.MODEL == "QwQ-AWQ":
        import requests
        import time
        import signal

        log_path = "/mnt/lustre/user/zhihao/vllm_logs/qwq-32b-awq.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_file = open(log_path, "w")
        

        vllm_process = subprocess.Popen(
            [
                "python3", "-m", "vllm.entrypoints.openai.api_server",
                "--model", str(args.MODEL_PATH),
                "--port", str(args.PORT),
                "--tensor-parallel-size", str(args.GPU_NUM),
                "--gpu-memory-utilization", "0.9"
            ],
            stdout=log_file,
            stderr=log_file,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
        )

    elif args.MODEL == "Qwen3-8B":

        import requests
        import time
        import signal

        log_path = "/mnt/lustre/home/user/vllm_logs/qwen3_8b_parrel.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_file = open(log_path, "w")
        

        vllm_process = subprocess.Popen(
            [
                "python3", "-m", "vllm.entrypoints.openai.api_server",
                "--model", str(args.MODEL_PATH),
                "--port", str(args.PORT),
                "--tensor-parallel-size", str(args.GPU_NUM),
                "--gpu-memory-utilization", "0.9"
            ],
            stdout=log_file,
            stderr=log_file,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
        )

    elif args.MODEL == "Llama3":
        import requests
        import time
        import signal

        log_path = "/mnt/lustre/home/user/vllm_logs/llama3_8b.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_file = open(log_path, "w")
        

        vllm_process = subprocess.Popen(
            [
                "python3", "-m", "vllm.entrypoints.openai.api_server",
                "--model", str(args.MODEL_PATH),
                "--port", str(args.PORT),
                "--tensor-parallel-size", str(args.GPU_NUM),
                "--gpu-memory-utilization", "0.9"
            ],
            stdout=log_file,
            stderr=log_file,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
        )

    if args.MODEL in API_MODEL_LIST:
        pass
    else:
        wait_until_ready()

    print("开始测试")

    for name in ['intent_pred_world_view', 'intent_pred_agent_view', 'value_pred_world_view', 'value_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
    # for name in ['value_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
        args.EXP_NAME=name
        args.DATASET_PATH='./experiment_res/llms_test/'+name+'_for_test_only_promptV1'+'.json'
        SAVE_PATH_PREFIX = './experiment_res/llms_test/'+name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION
        args.RESULT_SAVE_PATH=SAVE_PATH_PREFIX+'.json'
        run(args)

    if not args.MODEL in API_MODEL_LIST:

        vllm_process.terminate()
        try:
            vllm_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            vllm_process.kill()

    print("🛑 vLLM 服务已关闭")
