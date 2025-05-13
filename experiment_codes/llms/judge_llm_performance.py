import json
import re

import sys
sys.path.append('.')
import argparse
import ast
import pandas as pd
import anthropic
from experiment_codes.llms.llm_summarize import *
import os

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
    # 创建一个字典来存储结果
    results = {
        'model': args.MODEL,
        'exp_name': args.EXP_NAME,
        'test_version': args.TEST_VERSION
    }
    
    df = pd.read_csv(args.EXTRACT_DATA_SAVE_PATH)
    
    if 'value' in args.EXP_NAME:
        tested_ids = df['tested_ids'].tolist()
        active_distance_list = df['active_distance'].tolist()
        social_distance_list = df['social_distance'].tolist()
        helpful_distance_list = df['helpful_distance'].tolist()
        active_confidence_list = df['active_confidence'].tolist()
        social_confidence_list = df['social_confidence'].tolist()
        helpful_confidence_list = df['helpful_confidence'].tolist()
        ground_truth_active_list = df['ground_truth_active'].tolist()
        ground_truth_social_list = df['ground_truth_social'].tolist()
        ground_truth_helpful_list = df['ground_truth_helpful'].tolist()
        extracted_active_list = df['extracted_active'].tolist()
        extracted_social_list = df['extracted_social'].tolist()
        extracted_helpful_list = df['extracted_helpful'].tolist()

        results.update({
            'avg_active_distance': round(sum(active_distance_list) / len(active_distance_list), 3),
            'avg_active_confidence': round(sum(active_confidence_list) / len(active_confidence_list), 3),
            'avg_social_distance': round(sum(social_distance_list) / len(social_distance_list), 3),
            'avg_social_confidence': round(sum(social_confidence_list) / len(social_confidence_list), 3),
            'avg_helpful_distance': round(sum(helpful_distance_list) / len(helpful_distance_list), 3),
            'avg_helpful_confidence': round(sum(helpful_confidence_list) / len(helpful_confidence_list), 3)
        })
    elif 'intent' in args.EXP_NAME:
        tested_ids = df['tested_ids'].tolist()
        most_possible_intention_list = df['most_possible_intention'].tolist()
        most_possible_intention_cf_list = df['most_possible_intention_cf'].tolist()
        second_possible_intention_list = df['second_possible_intention'].tolist()
        second_possible_intention_cf_list = df['second_possible_intention_cf'].tolist()
        third_possible_intention_list = df['third_possible_intention'].tolist()
        third_possible_intention_cf_list = df['third_possible_intention_cf'].tolist()
        ground_truth_intention_list = df['ground_truth_intention'].tolist()
    elif 'action' in args.EXP_NAME:
        tested_ids = df['tested_ids'].tolist()
        most_possible_action_list = df['most_possible_action'].tolist()
        most_possible_action_cf_list = df['most_possible_action_cf'].tolist()
        second_possible_action_list = df['second_possible_action'].tolist()
        second_possible_action_cf_list = df['second_possible_action_cf'].tolist()
        third_possible_action_list = df['third_possible_action'].tolist()
        third_possible_action_cf_list = df['third_possible_action_cf'].tolist()
        ground_truth_action_list = df['ground_truth_action'].tolist()

    DATA_LENGTH = len(tested_ids)
    
    print(args.SAVE_PATH_PREFIX)

    if 'value' in args.EXP_NAME:
        
        print('average active distance: ', sum(active_distance_list) / len(active_distance_list))
        print('average active confidence: ', sum(active_confidence_list) / len(active_confidence_list))
        print('average social distance: ', sum(social_distance_list) / len(social_distance_list))
        print('average social confidence: ', sum(social_confidence_list) / len(social_confidence_list))
        print('average helpful distance: ', sum(helpful_distance_list) / len(helpful_distance_list))
        print('average helpful confidence: ', sum(helpful_confidence_list) / len(helpful_confidence_list))

    else:
        top_1_acc = []
        top_1_success_cf = []
        top_1_fail_cf = []
        top_3_acc = []
        top_3_success_acc = []
        object_top_1_acc = []
        object_top_1_success_cf = []
        object_top_1_fail_cf = []
        object_top_3_acc = []
        object_top_3_success_cf = []
        total_top_1_acc = []
        total_top_1_success_cf = []
        total_top_1_fail_cf = []
        total_top_3_acc = []
        total_top_3_success_cf = []

        for i in range(DATA_LENGTH):
            if 'intent' in args.EXP_NAME: 
                gt = ground_truth_intention_list[i]
                gt = remove_prefix_agent(gt)
                most_possible = remove_prefix_agent(most_possible_intention_list[i])
                second_possible = remove_prefix_agent(second_possible_intention_list[i])
                third_possible = remove_prefix_agent(third_possible_intention_list[i])
                most_possible_cf = most_possible_intention_cf_list[i]
                second_possible_cf = second_possible_intention_cf_list[i]
                third_possible_cf = third_possible_intention_cf_list[i]
            elif 'action' in args.EXP_NAME:
                gt = ground_truth_action_list[i]
                gt = remove_prefix_agent(gt)
                most_possible = remove_prefix_agent(most_possible_action_list[i])
                second_possible = remove_prefix_agent(second_possible_action_list[i])
                third_possible = remove_prefix_agent(third_possible_action_list[i])
                most_possible_cf = most_possible_action_cf_list[i]
                second_possible_cf = second_possible_action_cf_list[i]
                third_possible_cf = third_possible_action_cf_list[i]
            group = gt.split('-')
            gt_object = []
            gt_predicate = group[0]
            if len(group) > 1:
                gt_object = group[1:]
            most_group = most_possible.split('-')
            second_group = second_possible.split('-')
            third_group = third_possible.split('-')
            most_object = []
            second_object = []
            third_object = []
            most_predicate = most_group[0]
            second_predicate = second_group[0]
            third_predicate = third_group[0]
            if len(most_group) > 1:
                most_object = most_group[1:]
            if len(second_group) > 1:
                second_object = second_group[1:]
            if len(third_group) > 1:
                third_object = third_group[1:]

            if most_predicate == gt_predicate:
                top_1_acc.append(1)
                top_1_success_cf.append(most_possible_cf)
            else:
                top_1_acc.append(0)
                top_1_fail_cf.append(most_possible_cf)
            
            if most_predicate == gt_predicate:
                top_3_acc.append(1)
                top_3_success_acc.append(most_possible_cf)
            elif second_predicate == gt_predicate:
                top_3_acc.append(1)
                top_3_success_acc.append(second_possible_cf)
            elif third_predicate == gt_predicate:
                top_3_acc.append(1)
                top_3_success_acc.append(third_possible_cf)
            else:
                top_3_acc.append(0)

            fail_flag = False
            for object in gt_object:
                if object not in most_object:
                    object_top_1_acc.append(0)
                    object_top_1_fail_cf.append(most_possible_cf)
                    fail_flag = True
                    break
            if not fail_flag:
                object_top_1_acc.append(1)
                object_top_1_success_cf.append(most_possible_cf)
            
            fail_flag = False
            for object in gt_object:
                if object not in most_object:
                    fail_flag = True
                    break
            if not fail_flag:
                object_top_3_acc.append(1)
                object_top_3_success_cf.append(most_possible_cf)
            else:
                fail_flag = False
                for object in gt_object:
                    if object not in second_object:
                        fail_flag = True
                        break
                if not fail_flag:
                    object_top_3_acc.append(1)
                    object_top_3_success_cf.append(second_possible_cf)
                else:
                    fail_flag = False
                    for object in gt_object:
                        if object not in third_object:
                            fail_flag = True
                            break
                    if not fail_flag:
                        object_top_3_acc.append(1)
                        object_top_3_success_cf.append(third_possible_cf)
                    else:
                        object_top_3_acc.append(0)
            

            if gt == most_possible:
                total_top_1_acc.append(1)
                total_top_1_success_cf.append(most_possible_cf)
            else:
                total_top_1_acc.append(0)
                total_top_1_fail_cf.append(most_possible_cf)
            
            if gt == most_possible:
                total_top_3_acc.append(1)
                total_top_3_success_cf.append(most_possible_cf)
            elif gt == second_possible:
                total_top_3_acc.append(1)
                total_top_3_success_cf.append(second_possible_cf)
            elif gt == third_possible:
                total_top_3_acc.append(1)
                total_top_3_success_cf.append(third_possible_cf)
            else:
                total_top_3_acc.append(0)
                    
        results.update({
            'top_1_acc': round(sum(top_1_acc) / len(top_1_acc), 3),
            'top_1_success_cf': round(sum(top_1_success_cf) / len(top_1_success_cf), 3),
            'top_1_fail_cf': round(sum(top_1_fail_cf) / len(top_1_fail_cf), 3),
            'top_3_acc': round(sum(top_3_acc) / len(top_3_acc), 3),
            'top_3_success_acc': round(sum(top_3_success_acc) / len(top_3_success_acc), 3),
            'object_top_1_acc': round(sum(object_top_1_acc) / len(object_top_1_acc), 3),
            'object_top_1_success_cf': round(sum(object_top_1_success_cf) / len(object_top_1_success_cf), 3),
            'object_top_1_fail_cf': round(sum(object_top_1_fail_cf) / len(object_top_1_fail_cf), 3),
            'object_top_3_acc': round(sum(object_top_3_acc) / len(object_top_3_acc), 3),
            'object_top_3_success_cf': round(sum(object_top_3_success_cf) / len(object_top_3_success_cf), 3),
            'total_top_1_acc': round(sum(total_top_1_acc) / len(total_top_1_acc), 3),
            'total_top_1_success_cf': round(sum(total_top_1_success_cf) / len(total_top_1_success_cf), 3),
            'total_top_1_fail_cf': round(sum(total_top_1_fail_cf) / len(total_top_1_fail_cf), 3),
            'total_top_3_acc': round(sum(total_top_3_acc) / len(total_top_3_acc), 3),
            'total_top_3_success_cf': round(sum(total_top_3_success_cf) / len(total_top_3_success_cf), 3)
        })
    
    # 保存结果到CSV
    results_df = pd.DataFrame([results])
    results_file = './experiment_res/llm_performance_results.csv'
    # 如果文件存在，追加模式；如果不存在，创建新文件
    if os.path.exists(results_file):
        results_df.to_csv(results_file, mode='a', header=False, index=False)
    else:
        results_df.to_csv(results_file, index=False)
    
    # 打印结果
    for key, value in results.items():
        if key not in ['model', 'exp_name', 'test_version']:
            print(f"{key}: {value}")

def remove_prefix_agent(str):
    str = str.lower()
    if str[:5] == 'agent':
        str = str[8:]
    return str

if __name__ == "__main__":
    args = parse_arguments()
    args.TEST_VERSION = 'V1'

    # for name in ['intent_pred_world_view', 'intent_pred_agent_view', 'value_pred_world_view', 'value_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
    # for name in ['value_pred_world_view', 'value_pred_agent_view']:
    for name in ['intent_pred_world_view', 'intent_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
    # for name in ['action_update_agent_view']:
        for model in ['Qwen3-8B', 'Llama3', 'gpt-4o', 'Gemini', 'Claude', 'DeepSeek-R1', 'Random']:
        # for model in ['Qwen3-8B']:
            args.MODEL=model
            args.EXP_NAME=name
            args.SAVE_PATH = './experiment_res/llms_test/'
            args.SAVE_PATH_PREFIX = name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION
            args.RESULT_SAVE_PATH=args.SAVE_PATH+args.SAVE_PATH_PREFIX+'.json'
            args.EXTRACT_ERROR_SAVE_PATH = './experiment_res/match_errors/extract_error_dict_'+args.EXP_NAME+'_'+args.MODEL+'.json'
            args.EXTRACT_DATA_SAVE_PATH = './experiment_res/llms_res/' + args.SAVE_PATH_PREFIX + '.csv'
            args.LLM_EXTRACTION_SAVE_PATH = './experiment_res/prompt_response/llm_extraction_'+args.EXP_NAME+'_'+args.MODEL+'.json'
            main(args)
