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
        logger.info(f"Attempting to read JSON file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Successfully read JSON file: {file_path}")
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


def run(args):
    from transformers import AutoTokenizer, AutoModelForCausalLM

    import torch

    logger.info(f"Starting experiment: {args.EXP_NAME}")
    logger.info(f"Using model: {args.MODEL}")
    logger.info(f"Dataset path: {args.DATASET_PATH}")
    logger.info(f"Result save path: {args.RESULT_SAVE_PATH}")

    if not args.GENERATE_PROMPT:

        if args.MODEL == "QwQ":
            logger.info("Loading QwQ model...")

            # Enable CUDA optimizations
            if torch.cuda.is_available():
                logger.info("Enabling CUDA optimizations...")
                torch.backends.cudnn.benchmark = True
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                logger.info("CUDA optimizations enabled")
                
                # 检测和记录可用的GPU
                gpu_count = torch.cuda.device_count()
                logger.info(f"检测到 {gpu_count} 个可用的GPU")
                for i in range(gpu_count):
                    logger.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")
                    logger.info(f"GPU {i} 总内存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")

            local_model_path = "/mnt/lustre/home/zhihao/my_models/QwQ-32B"
            
            # 为每个GPU分配最大内存
            max_memory = {}
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                # 为每个GPU分配85%的可用内存
                for i in range(gpu_count):
                    max_memory[i] = f"{int(torch.cuda.get_device_properties(i).total_memory / 1024**3)}GB"
                logger.info(f"配置GPU内存分配: {max_memory}")
            
            # Add progress bar for model loading
            with tqdm(total=2, desc="Loading QwQ model", position=0) as pbar:
                logger.info("Starting model loading with optimizations...")
                model = AutoModelForCausalLM.from_pretrained(
                    local_model_path,
                    device_map="auto",
                    max_memory=max_memory,  # 使用配置的内存分配
                    # load_in_8bit=True,  # Enable 8-bit quantization
                    # use_cache=True,  # Enable KV cache
                    # use_flash_attention_2=True  # Enable Flash Attention 2
                )
                pbar.update(1)
                logger.info("Model loaded successfully")

                logger.info("Starting tokenizer loading...")
                tokenizer = AutoTokenizer.from_pretrained(
                    local_model_path,
                    use_fast=True  # Use fast tokenizer
                )
                pbar.update(1)
                logger.info("Tokenizer loaded successfully")

                model.eval()  # Set to evaluation mode

        elif args.MODEL == "QwQ-AWQ":
            from transformers import AutoTokenizer, AutoModelForCausalLM

            logger.info("Loading QwQ-AWQ model...")

            local_model_path = "/mnt/lustre/home/zhihao/my_models/QwQ-32B-AWQ"

            logger.info(f"Loading model from: {local_model_path}")

            model = AutoModelForCausalLM.from_pretrained(
                local_model_path, 
                device_map="auto",
            )

            logger.info("Model loaded successfully")

            tokenizer = AutoTokenizer.from_pretrained(local_model_path)

            logger.info("Tokenizer loaded successfully")

        elif args.MODEL == "Qwen3-8B":

            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            model_name = "/mnt/lustre/home/zhihao/my_models/Qwen/Qwen3-8B"

            tokenizer = AutoTokenizer.from_pretrained(model_name)

            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",  # 自动分配到多个 GPU
                torch_dtype=torch.float16,  # 减少显存使用
            )

        elif args.MODEL == "Llama3":
            # 模型路径，可以是 Hugging Face 上的模型，也可以是本地路径
            model_name = "/home/zhihao/my_models/llama"

            from transformers import MllamaForConditionalGeneration, AutoProcessor

            
            model = MllamaForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )
            processor = AutoProcessor.from_pretrained(model_name)
            # 加载到设备
            model = model.to("cuda")  # 如果有GPU，确保模型被加载到GPU上

        elif args.MODEL == "Qwen3":
            logger.info("Loading Qwen3 model...")
            

            local_model_path = "/mnt/lustre/home/zhihao/my_models/Qwen3-32B-AWQ"
            logger.info(f"Loading model from: {local_model_path}")
            
            # Check GPU memory before loading
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                logger.info(f"检测到 {gpu_count} 个可用的GPU")
                for i in range(gpu_count):
                    logger.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")
                    logger.info(f"GPU {i} 总内存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
                    
                logger.info(f"Available GPU memory before loading: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
                logger.info(f"Current GPU memory usage: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
            else:
                logger.warning("No GPU available, using CPU")
                
            # 为每个GPU分配最大内存
            max_memory = {}
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                # 为每个GPU分配85%的可用内存
                for i in range(gpu_count):
                    max_memory[i] = f"{int(torch.cuda.get_device_properties(i).total_memory * 0.85 / 1024**3)}GB"
                logger.info(f"配置GPU内存分配: {max_memory}")

            try:
                # Add progress bar for model loading
                with tqdm(total=2, desc="Loading Qwen3 model", position=0) as pbar:
                    logger.info("Starting to load tokenizer...")
                    tokenizer = AutoTokenizer.from_pretrained(local_model_path)
                    pbar.update(1)
                    logger.info("Tokenizer loaded successfully")

                    logger.info("Starting to load model...")
                    # Add device_map configuration
                    model = AutoModelForCausalLM.from_pretrained(
                        local_model_path,
                        device_map="auto",
                        max_memory=max_memory,  # 使用配置的内存分配
                        torch_dtype=torch.float16,  # Use float16 to reduce memory usage
                        low_cpu_mem_usage=True, 
                        local_files_only=True
                    )
                    pbar.update(1)
                    logger.info("Model loaded successfully")

                    # Check GPU memory after loading
                    if torch.cuda.is_available():
                        for i in range(gpu_count):
                            logger.info(f"GPU {i} 内存使用: {torch.cuda.memory_allocated(i) / 1024**3:.2f} GB")
                        logger.info(f"Available GPU memory after loading: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
                        logger.info(f"Current GPU memory usage: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

            except Exception as e:
                logger.error(f"Error during model loading: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

        elif args.MODEL == "Qwen3-Online":
        
            from transformers import AutoTokenizer, AutoModelForCausalLM

            tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-32B-AWQ")
            model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-32B-AWQ")

        elif args.MODEL == "QwQ-Online-AWQ":
            from awq import AutoAWQForCausalLM
            from transformers import AutoTokenizer

            model_id = "Qwen/QwQ-32B-AWQ"

            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            model = AutoAWQForCausalLM.from_quantized(
                model_id,
                fuse_layers=True,
                trust_remote_code=True,
                device="cuda",
                safetensors=True,
            )

    logger.info(f"Reading dataset from: {args.DATASET_PATH}")
    df = pd.read_csv(args.DATASET_PATH)
    logger.info(f"Dataset loaded successfully with {len(df)} rows")

    # load data
    if 'pred' in args.EXP_NAME:
        logger.info("Processing prediction experiment data...")
        if 'intent' in args.EXP_NAME:
            intent_list = df['intent'].tolist()
            infer_intent_list = df['infer_intent'].apply(ast.literal_eval).tolist()
            logger.info(f"Loaded {len(intent_list)} intent samples")
        elif 'value' in args.EXP_NAME:
            ground_truth_values = df['ground_truth_values'].tolist()
            infer_value_list = df['infer_values'].apply(ast.literal_eval).tolist()
            logger.info(f"Loaded {len(ground_truth_values)} value samples")
        
        other_actions_list = df['actions_for_infer'].apply(ast.literal_eval).tolist()
        your_actions_list = df['other_actions'].apply(ast.literal_eval).tolist()
        state_list = df['state_prompt'].apply(ast.literal_eval).tolist()
        test_agent_id_list = df['test_agent_id'].tolist()
        logger.info("Prediction data processing completed")
    else:
        logger.info("Processing update experiment data...")
        intent_list = df['intent'].tolist()
        your_actions_list = df['actions_for_update'].apply(ast.literal_eval).tolist()
        other_actions_list = df['other_actions'].apply(ast.literal_eval).tolist()
        state_list = df['state_prompt'].apply(ast.literal_eval).tolist()
        infer_intent_list = df['infer_intent'].apply(ast.literal_eval).tolist()
        infer_value_list = df['infer_values'].apply(ast.literal_eval).tolist()
        values_for_update_list = df['values_for_update'].tolist()
        previous_intent_list = df['previous_intent'].apply(ast.literal_eval).tolist()
        next_action_list = df['next_action'].tolist()
        test_agent_id_list = df['test_agent_id'].tolist()
        logger.info("Update data processing completed")

    DATA_LENGTH = len(state_list)
    logger.info(f"Total data length: {DATA_LENGTH}")

    if args.GENERATE_PROMPT:
        prompt_save_dict = {}
        results = [0]

    results = read_json(args.RESULT_SAVE_PATH)
    if results is None:
        logger.info("No existing results found, initializing new results list")
        results = [0]
    else:
        logger.info(f"Loaded existing results, current index: {results[0]}")

    if 'world' in args.EXP_NAME:
        other_action_description = "The first agent's action"
        your_action_description = "The second agent's action"
        world_state_description = "world_state"
    else:
        other_action_description = "other_action"
        your_action_description = "your_action"
        world_state_description = "world_state observed by you"

    # 使用tqdm显示进度
    progress_bar = tqdm(total=DATA_LENGTH * args.TEST_RATIO, desc=args.EXP_NAME)

    while results[0] < DATA_LENGTH * args.TEST_RATIO:
        # 更新进度条
        progress_bar.update(1)

        if 'pred' in args.EXP_NAME:
            if 'agent' in args.EXP_NAME:
                prompt_agent_id = f"You are Agent_{test_agent_id_list[results[0]]}, and the other agent is Agent_{3 - int(test_agent_id_list[results[0]])}. "
            elif 'world' in args.EXP_NAME:
                prompt_agent_id = f"The first agent is Agent_{3 - int(test_agent_id_list[results[0]])} and the second agent is Agent_{test_agent_id_list[results[0]]}. "
        elif 'update' in args.EXP_NAME:
            prompt_agent_id = f"You are Agent_{test_agent_id_list[results[0]]}, and the other agent is Agent_{3 - int(test_agent_id_list[results[0]])}. "

        ALL_STEP_PROMPT = ""

        # update 情况下，state_list 长度要比 other_actions_list 和 your_actions_list 少1，因为state_list 记录的是动作完成后世界的状态
        # 这里需要补偿一个state，即当前世界状态
        if 'update' in args.EXP_NAME and len(state_list[results[0]]):
            state_list[results[0]].append(state_list[results[0]][-1])

        # git like step prompt

        previous_agent_state_prompt = []
        previous_object_state_prompt = []

        for i in range(len(other_actions_list[results[0]])):
            # 由于是轮流做动作，可能会出现state和action长度不够的情况
            if len(state_list[results[0]][i][3]) == 0:
                if "world" in args.EXP_NAME:
                    # Nothing reachable
                    reachable = "nothing is reachable for both agents"
                else:
                    reachable = "nothing is reachable for you"
            else:
                reachable_dict = state_list[results[0]][i][3]
                reachable = ""
                if 'agent' in args.EXP_NAME:
                    if len(reachable_dict) == 0:
                        reachable = "nothing is reachable for you"
                    else:
                        reachable = f"{reachable_dict} are reachable for you. "
                elif 'world' in args.EXP_NAME:
                    for j in reachable_dict.keys():
                        reachable += f"agent_{j} reachable: {reachable_dict[j]}\n"
            
            if len(your_actions_list[results[0]]) == i:
                if 'agent' in args.EXP_NAME:
                    your_action = "You are deciding what to do"
                else:
                    if 'pred' in args.EXP_NAME:
                        your_action = "The second agent is deciding what to do"
                    else:
                        your_action = "The first agent is deciding what to do"
            elif len(your_actions_list[results[0]]) - 1 < i:
                if 'agent' in args.EXP_NAME:
                    your_action = "You do nothing"
                else:
                    if 'pred' in args.EXP_NAME:
                        your_action = "The second agent does nothing"
                    else:
                        your_action = "The first agent does nothing"
            else:
                your_action = your_actions_list[results[0]][i]
                if your_action is None:
                    if 'agent' in args.EXP_NAME:
                        your_action = "You do nothing"
                    else:
                        if 'pred' in args.EXP_NAME:
                            your_action = "The second agent does nothing"
                        else:
                            your_action = "The first agent does nothing"

            if other_actions_list[results[0]][i] is not None:
                other_action = other_actions_list[results[0]][i]
            else:
                if 'agent' in args.EXP_NAME:
                    if (len(your_actions_list[results[0]]) > i) and (your_actions_list[results[0]][i] is not None):
                        other_action = "The other agent does nothing"
                    elif len(your_actions_list[results[0]]) == i:
                        other_action = "The other agent does nothing"
                    else:
                        other_action = "You can not observe other's action"
                else:
                    if 'pred' in args.EXP_NAME:
                        other_action = "The first agent does nothing"
                    else:
                        other_action = "The second agent does nothing"

            if len(previous_agent_state_prompt) == 0 and len(previous_object_state_prompt) == 0:

                step_prompt = TIME_STEP_TEMPLATE.format(
                    index=i + 1,
                    other_action=other_action,
                    your_action=your_action,
                    obj_list=state_list[results[0]][i][2],
                    reachable=reachable,
                    other_information="".join(state_list[results[0]][i][0]) + "".join(state_list[results[0]][i][1]), 
                    other_action_description=other_action_description,
                    your_action_description=your_action_description,
                    world_state_description=world_state_description
                )

                previous_agent_state_prompt = state_list[results[0]][i][0] 
                previous_object_state_prompt = state_list[results[0]][i][1]
            else:
                # only present difference information
                prompt_to_show = []

                prompt_disappear_information = []
                prompt_new_information = []

                prompt_disappear_information.append("The following information is changed:")

                # disappear information
                for prompt in previous_agent_state_prompt:
                    if prompt not in state_list[results[0]][i][0]:
                        prompt_disappear_information.append(prompt)
                for prompt in previous_object_state_prompt:
                    if prompt not in state_list[results[0]][i][1]:
                        prompt_disappear_information.append(prompt)

                prompt_new_information.append("The following information is new:")

                # new
                for prompt in state_list[results[0]][i][0]:
                    if prompt not in previous_agent_state_prompt:
                        prompt_new_information.append(prompt)
                for prompt in state_list[results[0]][i][1]:
                    if prompt not in previous_object_state_prompt:
                        prompt_new_information.append(prompt)

                if len(prompt_disappear_information) == 1 and len(prompt_new_information) == 1:
                    prompt_to_show_final = "The observed state is unchanged."
                elif len(prompt_disappear_information) == 1 :
                    prompt_to_show_final = "".join(prompt_disappear_information) + "There is no new information."
                elif len(prompt_new_information) == 1:
                    prompt_to_show_final = "".join(prompt_new_information) + "There is no changed information."
                else:
                    prompt_to_show_final = "".join(prompt_disappear_information) + "".join(prompt_new_information)

                step_prompt = TIME_STEP_TEMPLATE.format(
                    index=i + 1,
                    other_action=other_action,
                    your_action=your_action,
                    obj_list=state_list[results[0]][i][2],
                    reachable=reachable,
                    other_information=prompt_to_show_final,
                    other_action_description=other_action_description,
                    your_action_description=your_action_description,
                    world_state_description=world_state_description
                )

                previous_agent_state_prompt = state_list[results[0]][i][0] 
                previous_object_state_prompt = state_list[results[0]][i][1]

            if 'pred' in args.EXP_NAME and args.USE_GT_INFER:
                if 'intent' in args.EXP_NAME:
                    infer_intent = infer_intent_list[results[0]]
                    if len(infer_intent) - 1 == i:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"Now you are inferring the first agent's intent based on the given observations."
                        else:
                            step_prompt += f"Now you are inferring the other agent's intent based on the given observations."
                    elif len(infer_intent) - 1 < i:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, your inference about the first agent's intent is: {infer_intent[-1]}."
                        else:
                            step_prompt += f"In this step, your inference about the other agent's intent is: {infer_intent[-1]}."
                    else:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, your inference about the first agent's intent is: {infer_intent[i]}."
                        else:
                            step_prompt += f"In this step, your inference about the other agent's intent is: {infer_intent[i]}."
                # elif 'value' in args.EXP_NAME:
                #     infer_value = infer_value_list[results[0]]
                #     if len(infer_value) - 1 == i:
                #         if 'world' in args.EXP_NAME:
                #             step_prompt += f"Now you are inferring the first agent's value based on the given observations."
                #         else:
                #             step_prompt += f"Now you are inferring the other agent's value based on the given observations."
                #     elif len(infer_value) - 1 < i:
                #         if 'world' in args.EXP_NAME:
                #             step_prompt += f"In this step, your inference about the first agent's value is: {infer_value[-1]}."
                #         else:
                #             step_prompt += f"In this step, your inference about the other agent's value is: {infer_value[-1]}."
                #     else:
                #         if 'world' in args.EXP_NAME:
                #             step_prompt += f"In this step, your inference about the first agent's value is: {infer_value[i]}."
                #         else:
                #             step_prompt += f"In this step, your inference about the other agent's value is: {infer_value[i]}."
            elif 'update' in args.EXP_NAME:
                # update
                infer_intent = infer_intent_list[results[0]]
                if len(infer_intent) - 1 == i:
                    # only give the last inference
                    if 'world' in args.EXP_NAME:
                        step_prompt += f"In this step, your inference about the first agent's intent is: {infer_intent[-1]}."
                    else:
                        step_prompt += f"In this step, your inference about the other agent's intent is: {infer_intent[-1]}."
                infer_value = infer_value_list[results[0]]
                if len(infer_value) - 1 == i:
                    if 'world' in args.EXP_NAME:
                        step_prompt += f"In this step, your inference about the first agent's value is: {infer_value[-1]}."
                    else:
                        step_prompt += f"In this step, your inference about the other agent's value is: {infer_value[-1]}."
                previous_intent = previous_intent_list[results[0]]
                if 'intent' in args.EXP_NAME:
                    if not len(previous_intent):
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, first agent's intent is: None."
                        else:
                            step_prompt += f"In this step, your intent is: None."
                    elif len(previous_intent) == i:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"Now you are updating the first agent's intent based on the given information."
                        else:
                            step_prompt += f"Now you are updating your intent based on the given information."
                    elif len(previous_intent) - 1 < i:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, first agent's intent is: {previous_intent[-1]}."
                        else:
                            step_prompt += f"In this step, your intent is: {previous_intent[-1]}."
                    else:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, first agent's intent is: {previous_intent[i]}."
                        else:
                            step_prompt += f"In this step, your intent is: {previous_intent[i]}."
                else:
                    # action update
                    if not len(previous_intent):
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, first agent's intent is: None."
                        else:
                            step_prompt += f"In this step, your intent is: None."
                    elif len(previous_intent) == i:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, first agent's intent is: {intent_list[results[0]]}."
                        else:
                            step_prompt += f"In this step, your intent is: {intent_list[results[0]]}."
                    elif len(previous_intent) - 1 < i:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, first agent's intent is: {previous_intent[-1]}."
                        else:
                            step_prompt += f"In this step, your intent is: {previous_intent[-1]}."
                    else:
                        if 'world' in args.EXP_NAME:
                            step_prompt += f"In this step, first agent's intent is: {previous_intent[i]}."
                        else:
                            step_prompt += f"In this step, your intent is: {previous_intent[i]}."

            ALL_STEP_PROMPT += step_prompt

        if args.EXP_NAME=="intent_pred_world_view":
            prompt = PROMPT_INTENTION_WORLD_VIEW.format(AGENT_ID_INTRO=prompt_agent_id, IntentionSpace=IntentionSpace, ActionSpace=ActionSpace, POSITION_ROTATE=POSITION_ROTATE, step_prompt=ALL_STEP_PROMPT)
        elif args.EXP_NAME=="intent_pred_agent_view":
            prompt = PROMPT_INTENTION_AGENT_VIEW.format(AGENT_ID_INTRO=prompt_agent_id, IntentionSpace=IntentionSpace, ActionSpace=ActionSpace, POSITION_ROTATE=POSITION_ROTATE, step_prompt=ALL_STEP_PROMPT)
        elif args.EXP_NAME=="value_pred_world_view":
            prompt = PROMPT_VALUE_WORLD_VIEW.format(AGENT_ID_INTRO=prompt_agent_id, ValueSpace=ValueSpace, ActionSpace=ActionSpace, POSITION_ROTATE=POSITION_ROTATE, step_prompt=ALL_STEP_PROMPT)
        elif args.EXP_NAME=="value_pred_agent_view":
            prompt = PROMPT_VALUE_AGENT_VIEW.format(AGENT_ID_INTRO=prompt_agent_id, ValueSpace=ValueSpace, ActionSpace=ActionSpace, POSITION_ROTATE=POSITION_ROTATE, step_prompt=ALL_STEP_PROMPT)
        elif args.EXP_NAME=="intent_update_agent_view":
            prompt = PROMPT_INTENT_UPDATE_AGENT_VIEW.format(AGENT_ID_INTRO=prompt_agent_id, IntentionSpace=IntentionSpace, ActionSpace=ActionSpace, POSITION_ROTATE=POSITION_ROTATE, step_prompt=ALL_STEP_PROMPT, your_value=values_for_update_list[results[0]])
        elif args.EXP_NAME=="action_update_agent_view":
            prompt = PROMPT_ACTION_UPDATE_AGENT_VIEW.format(AGENT_ID_INTRO=prompt_agent_id, IntentionSpace=IntentionSpace, ActionSpace=ActionSpace, POSITION_ROTATE=POSITION_ROTATE, step_prompt=ALL_STEP_PROMPT, your_value=values_for_update_list[results[0]])

        if args.GENERATE_PROMPT is False:
            logger.info(f"Starting model inference for sample {results[0]}")
            start_time = time.time()
            
            # 添加重试机制
            max_retries = 3  # 最大重试次数
            retry_delay = 2  # 初始重试延迟（秒）
            retry_count = 0
            success = False
            
            while not success and retry_count < max_retries:
                try:
                    if retry_count > 0:
                        logger.warning(f"重试 #{retry_count} - 为样本 {results[0]} 调用模型...")
                        
                    if args.MODEL in ["QwQ", "Qwen3-8B"]:
                        logger.info("Preparing input for local model...")
                        messages = [
                            {"role": "user", "content": prompt}
                        ]
                        text = tokenizer.apply_chat_template(
                            messages,
                            tokenize=False,
                            add_generation_prompt=True
                        )

                        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
                        logger.info("Generating response...")
                        generated_ids = model.generate(
                            **model_inputs,
                            max_new_tokens=2048
                        )
                        generated_ids = [
                            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
                        ]

                        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
                        logger.info("Response generated successfully")
                        response_to_store = response
                        success = True

                    elif args.MODEL == "Llama3":
                        inputs = processor(text=prompt, return_tensors="pt").to(model.device)

                        # Generate
                        output = model.generate(**inputs, max_new_tokens=2048)

                        response_to_store = processor.decode(output[0])

                    elif args.MODEL == "Claude":
                        client = anthropic.Anthropic(api_key="")

                        response = client.messages.create(
                            model="claude-3-7-sonnet-20250219",  # 可选: claude-3-sonnet, claude-3-haiku
                            max_tokens=2048,
                            temperature=0.4,
                            messages=[
                                {"role": "user", "content": prompt}
                            ]
                        )

                        print(response.content)
                        response_to_store = response.content[0].text
                        success = True

                    elif args.MODEL == "gpt-4o":
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
                        logger.error(f"达到最大重试次数 ({max_retries}), 放弃样本 {results[0]}")
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
                        logger.error(f"达到最大重试次数 ({max_retries}), 放弃样本 {results[0]}")
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
                        logger.error(f"达到最大重试次数 ({max_retries}), 放弃样本 {results[0]}")
                        response_to_store = f"ERROR: 未知错误，达到最大重试次数: {str(e)}"
                        break

            end_time = time.time()
            cost_time = end_time - start_time
            logger.info(f"Inference completed in {cost_time:.2f} seconds")

            # 如果所有重试都失败，但我们还是要保存结果
            if not success and retry_count >= max_retries:
                logger.warning(f"样本 {results[0]} 的所有重试都失败，保存错误信息并继续")

            if args.MODEL == "DeepSeek-R1":
                if 'pred' in args.EXP_NAME:

                    if 'intent' in args.EXP_NAME:
                        results.append({
                            'intent': intent_list[results[0]],
                            'other_actions': other_actions_list[results[0]],
                            'your_actions': your_actions_list[results[0]],
                            'state_prompt': state_list[results[0]],
                            'infer_intent': infer_intent_list[results[0]],
                            "prompt": prompt,
                            'response': response_to_store,
                            'reasoning': reasoning_to_store,
                            'cost_time': cost_time
                        })
                    elif 'value' in args.EXP_NAME:
                        results.append({
                            'ground_truth_value': ground_truth_values[results[0]],
                            'other_actions': other_actions_list[results[0]],
                            'your_actions': your_actions_list[results[0]],
                            'state_prompt': state_list[results[0]],
                            'infer_values': infer_value_list[results[0]],
                            "prompt": prompt,
                            'response': response_to_store,
                            'reasoning': reasoning_to_store,
                            'cost_time': cost_time
                        })
                else:
                    results.append({
                        'intent': intent_list[results[0]],
                        'other_actions': other_actions_list[results[0]],
                        'your_actions': your_actions_list[results[0]],
                        'state_prompt': state_list[results[0]],
                        'infer_intent': infer_intent_list[results[0]],
                        'infer_values': infer_value_list[results[0]],
                        'values_for_update': values_for_update_list[results[0]],
                        'previous_intent': previous_intent_list[results[0]],
                        'next_action': next_action_list[results[0]],
                        "prompt": prompt,
                        'response': response_to_store, 
                        'reasoning': reasoning_to_store,
                        'cost_time': cost_time
                    })

                results[0] += 1
                save_json(results, args.RESULT_SAVE_PATH)
            else:
                if 'pred' in args.EXP_NAME:

                    if 'intent' in args.EXP_NAME:
                        results.append({
                            'intent': intent_list[results[0]],
                            'other_actions': other_actions_list[results[0]],
                            'your_actions': your_actions_list[results[0]],
                            'state_prompt': state_list[results[0]],
                            'infer_intent': infer_intent_list[results[0]],
                            "prompt": prompt,
                            'response': response_to_store,
                            'cost_time': cost_time
                        })
                    elif 'value' in args.EXP_NAME:
                        results.append({
                            'ground_truth_value': ground_truth_values[results[0]],
                            'other_actions': other_actions_list[results[0]],
                            'your_actions': your_actions_list[results[0]],
                            'state_prompt': state_list[results[0]],
                            'infer_values': infer_value_list[results[0]],
                            "prompt": prompt,
                            'response': response_to_store,
                            'cost_time': cost_time
                        })
                else:
                    results.append({
                        'intent': intent_list[results[0]],
                        'other_actions': other_actions_list[results[0]],
                        'your_actions': your_actions_list[results[0]],
                        'state_prompt': state_list[results[0]],
                        'infer_intent': infer_intent_list[results[0]],
                        'infer_values': infer_value_list[results[0]],
                        'values_for_update': values_for_update_list[results[0]],
                        'previous_intent': previous_intent_list[results[0]],
                        'next_action': next_action_list[results[0]],
                        "prompt": prompt,
                        'response': response_to_store, 
                        'cost_time': cost_time
                    })

                results[0] += 1
                save_json(results, args.RESULT_SAVE_PATH)
        else:
            if 'pred' in args.EXP_NAME:
                if 'intent' in args.EXP_NAME:
                    if "agent" in args.EXP_NAME:
                        prompt_save_dict[results[0]] = {
                        'intent': intent_list[results[0]],
                        'other_actions': other_actions_list[results[0]],
                        'your_actions': your_actions_list[results[0]],
                        'state_prompt': state_list[results[0]],
                        'infer_intent': infer_intent_list[results[0]],
                        "prompt": prompt,
                        "answer": infer_intent_list[results[0]][-1]
                        }
                    elif 'world' in args.EXP_NAME:
                        prompt_save_dict[results[0]] = {
                            'intent': intent_list[results[0]],
                            'other_actions': other_actions_list[results[0]],
                            'your_actions': your_actions_list[results[0]],
                            'state_prompt': state_list[results[0]],
                            'infer_intent': infer_intent_list[results[0]],
                            "prompt": prompt,
                            "answer": intent_list[results[0]]                      
                        }
                elif 'value' in args.EXP_NAME:
                    if 'agent' in args.EXP_NAME:
                        prompt_save_dict[results[0]] = {
                            'ground_truth_value': ground_truth_values[results[0]],
                            'other_actions': other_actions_list[results[0]],
                            'your_actions': your_actions_list[results[0]],
                            'state_prompt': state_list[results[0]],
                            'infer_values': infer_value_list[results[0]],
                            "prompt": prompt,
                            "answer": infer_value_list[results[0]]
                        }
                    elif 'world' in args.EXP_NAME:
                        prompt_save_dict[results[0]] = {
                            'ground_truth_value': ground_truth_values[results[0]],
                            'other_actions': other_actions_list[results[0]],
                            'your_actions': your_actions_list[results[0]],
                            'state_prompt': state_list[results[0]],
                            'infer_values': infer_value_list[results[0]],
                            "prompt": prompt,
                            "answer": ground_truth_values[results[0]]
                        }
            elif 'update' in args.EXP_NAME:
                if 'intent' in args.EXP_NAME:
                    prompt_save_dict[results[0]] = {
                        'other_actions': other_actions_list[results[0]],
                        'your_actions': your_actions_list[results[0]],
                        'state_prompt': state_list[results[0]],
                        'infer_intent': infer_intent_list[results[0]],
                        'infer_values': infer_value_list[results[0]],
                        'values_for_update': values_for_update_list[results[0]],
                        'previous_intent': previous_intent_list[results[0]],
                        'next_action': next_action_list[results[0]],
                        "prompt": prompt,
                        'intent': intent_list[results[0]], 
                        'answer': intent_list[results[0]], 
                    }
                elif 'action' in args.EXP_NAME:
                    prompt_save_dict[results[0]] = {
                        'other_actions': other_actions_list[results[0]],
                        'your_actions': your_actions_list[results[0]],
                        'state_prompt': state_list[results[0]],
                        'infer_intent': infer_intent_list[results[0]],
                        'infer_values': infer_value_list[results[0]],
                        'values_for_update': values_for_update_list[results[0]],
                        'previous_intent': previous_intent_list[results[0]],
                        'next_action': next_action_list[results[0]],
                        "prompt": prompt,
                        'intent': intent_list[results[0]], 
                        'answer': next_action_list[results[0]], 
                    }
            results[0] += 1
    if not args.GENERATE_PROMPT:
        save_json(results, args.RESULT_SAVE_PATH)
    else:
        save_json(prompt_save_dict, args.RESULT_SAVE_PATH)

    # 关闭进度条
    progress_bar.close()


def parse_arguments():

    parser=argparse.ArgumentParser(description='raw data processing')
    parser.add_argument('--REGION', default="")
    parser.add_argument('--API_KEY', default="")
    parser.add_argument('--API_BASE', default="")
    parser.add_argument('--ENDPOINT', default="")
    parser.add_argument('--DATASET_PATH', default="")
    parser.add_argument('--RESULT_SAVE_PATH', default="")
    parser.add_argument('--EXP-NAME', default="")
    parser.add_argument('--TEST_RATIO', default=1)
    parser.add_argument('--GENERATE_PROMPT', default=True)
    parser.add_argument('--USE_GT_INFER', default=False)
    parser.add_argument('--MODEL', default="QwQ", choices=["QwQ", "gpt-4o", "Qwen3", "Qwen3-Online", "QwQ-Online-AWQ", "Claude", "Gemini", "QwQ-AWQ", "DeepSeek-R1", "Llama3", "Qwen3-8B"])
    parser.add_argument('--BATCH_SIZE', default=1)
    parser.add_argument('--GENERATE_TRAIN_PROMPT', default=True)

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_arguments()

    # common
    args.REGION = ""
    args.API_KEY = ""
    args.API_BASE = ""
    args.ENDPOINT = f"{args.API_BASE}/{args.REGION}"
    args.TEST_VERSION = 'V1'

    for name in ['intent_pred_world_view', 'intent_pred_agent_view', 'value_pred_world_view', 'value_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
    # for name in ['action_update_agent_view']:
        args.EXP_NAME=name
        args.DATASET_PATH='./data/dataset_'+name+'_segment_True_for_test'+'.csv'
        if args.GENERATE_TRAIN_PROMPT:
            args.DATASET_PATH='./data/dataset_'+name+'_segment_True_for_train'+'.csv'
        if args.GENERATE_PROMPT is False:
            if 'pred' in args.EXP_NAME:
                args.RESULT_SAVE_PATH='./experiment_res/llms_test/'+name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION+'.json'
            else:
                args.RESULT_SAVE_PATH='./experiment_res/llms_test/'+name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION+'.json'
        else:
            if args.GENERATE_TRAIN_PROMPT:
                args.RESULT_SAVE_PATH='./experiment_res/llms_test/'+name+'_for_train_only_prompt'+args.TEST_VERSION+'.json'
            else:
                args.RESULT_SAVE_PATH='./experiment_res/llms_test/'+name+'_for_test_only_prompt'+args.TEST_VERSION+'.json'
        run(args)
