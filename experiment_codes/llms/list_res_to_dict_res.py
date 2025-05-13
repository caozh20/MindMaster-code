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
    print("main")
    data_dict_to_save = {}
    list_data = read_json(args.RESULT_FROM_PATH)
    for i in range(len(list_data) - 1):
        data_dict = list_data[i+1]
        if 'pred' in args.EXP_NAME:
            if 'intent' in args.EXP_NAME:
                if "agent" in args.EXP_NAME:
                    answer = data_dict['infer_intent'][-1]
                elif 'world' in args.EXP_NAME:
                    answer = data_dict['intent']
            elif 'value' in args.EXP_NAME:
                if 'agent' in args.EXP_NAME:
                    answer = data_dict['infer_values']
                elif 'world' in args.EXP_NAME:
                    answer = data_dict['ground_truth_value']
        elif 'update' in args.EXP_NAME:
            if 'intent' in args.EXP_NAME:
                answer = data_dict['intent']
            elif 'action' in args.EXP_NAME:
                answer = data_dict['next_action']
        data_dict['answer'] = answer
        data_dict_to_save[str(i)] = data_dict
    save_json(data_dict_to_save, args.RESULT_SAVE_PATH)

if __name__ == "__main__":
    args = parse_arguments()
    args.TEST_VERSION = 'V1'

    for name in ['intent_pred_world_view', 'intent_pred_agent_view', 'value_pred_world_view', 'value_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
    # for name in ['value_pred_world_view']:
        for model in ['gpt-4o', 'Gemini', 'Claude', 'DeepSeek-R1']:
            args.MODEL=model
            args.EXP_NAME=name
            args.DATASET_PATH='./experiment_res/llms_test/'+name+'_for_test_only_promptV1'+'.json'
            SAVE_PATH_PREFIX = './experiment_res/llms_test/'+name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION
            args.RESULT_SAVE_PATH=SAVE_PATH_PREFIX+'.json'
            args.RESULT_FROM_PATH = './experiment_res/llms_test_backup/'+name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION + '.json'
            print(args.RESULT_FROM_PATH)
            main(args)
