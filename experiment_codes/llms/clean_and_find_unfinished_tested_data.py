import json
import re

import argparse
import ast

def read_json(file_path):
    """读取JSON文件
    如果文件不存在，静默返回None
    如果JSON格式错误，返回None"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def save_json(data, file_path):
    """保存数据到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving file {file_path}: {str(e)}")

def parse_arguments():

    parser=argparse.ArgumentParser(description='raw data processing')
    parser.add_argument('--TEST_RATIO', default=1)
    parser.add_argument('--MODEL', default="Qwen3-8B", choices=["QwQ", "gpt-4o", "Qwen3", "Qwen3-Online", "QwQ-Online-AWQ", "Claude", "Gemini", "QwQ-AWQ", "DeepSeek-R1", "Llama3", "Qwen3-8B", "DEBUG"])

    return parser.parse_args()

def main(args):
    tested_data = read_json(args.RESULT_SAVE_PATH)
    total_data = read_json(args.DATASET_PATH)
    TOTAL_DATA_LENGTH = len(total_data.keys())
    if isinstance(tested_data, dict):
            # New datasave format
        DATA_LENGTH = len(tested_data.keys())
    elif isinstance(tested_data, list):
        # Old datasave format
        DATA_LENGTH = len(tested_data) - 1
    else:
        print("Unknown data format, ERROR")
        return
    
    if TOTAL_DATA_LENGTH > DATA_LENGTH:
        print(f"{args.RESULT_SAVE_PATH} is not finished, please continue")

    for i in range(DATA_LENGTH):

        if isinstance(tested_data, dict):
            # New datasave format
            data_dict = tested_data[str(i)]
        elif isinstance(tested_data, list):
            # Old datasave format
            data_dict = tested_data[i + 1]
        else:
            print("Unknown data format, ERROR")
            return
        
        response = str(data_dict['response'])
        answer = str(data_dict['answer'])

        if "ERROR" in response or 'landmark' in response or 'most_possible_intent_cf' in response:
            print("FindError")
            print(f"error in {i}, {args.RESULT_SAVE_PATH}")
            del tested_data[str(i)]
            continue
    
    save_json(tested_data, args.RESULT_SAVE_PATH)

if __name__ == "__main__":
    args = parse_arguments()
    args.TEST_VERSION = 'V1'

    for name in ['intent_pred_world_view', 'intent_pred_agent_view', 'value_pred_world_view', 'value_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
    # for name in ['value_pred_world_view']:
        # for model in ['Qwen3-8B', 'Llama3', 'gpt-4o', 'Gemini', 'Claude', 'DeepSeek-R1']:
        for model in ['Random']:
            args.MODEL=model
            args.EXP_NAME=name
            args.DATASET_PATH='./experiment_res/llms_test/'+name+'_for_test_only_promptV1'+'.json'
            SAVE_PATH_PREFIX = './experiment_res/llms_test/'+name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION
            args.RESULT_SAVE_PATH=SAVE_PATH_PREFIX+'.json'
            print(args.RESULT_SAVE_PATH)
            main(args)
