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

def llm_extraction(text: str, args, extracting_id, used_prompt_template) -> dict:
    data_dict = read_json(args.LLM_EXTRACTION_SAVE_PATH)
    if data_dict is not None:
        if data_dict.get(str(extracting_id)) is not None:
            result = data_dict.get(str(extracting_id))
            return result
    if data_dict is None:
        data_dict = {}
    prompt = used_prompt_template.format(text=text)
    client = anthropic.Anthropic(api_key="")

    print(text)
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
    data_dict[str(extracting_id)] = response_to_store
    save_json(data_dict, args.LLM_EXTRACTION_SAVE_PATH)
    return response_to_store
    
def extract_action_dict(text: str, args, extracting_id) -> dict:
    """
    从字符串中提取包含动作和置信度的字典
    
    Args:
        text (str): 包含目标字典的字符串
        
    Returns:
        dict: 提取出的字典，包含动作和对应的置信度
    """
    # 使用正则表达式匹配目标格式的字典
    result = extract_fixed_action_dict(text)    
    if len(result) == 0:
        result = extract_last_3_actions(text)
        if len(result) == 0:
            result = extract_last_3_extended_actions(text)
            if len(result) == 0:
                response = llm_extraction(text, args, extracting_id, PROMPT_ACTION_MATCH)
                result = extract_fixed_action_dict(response)
                if len(result) == 0:
                    return False, text
    return True, result

def extract_intent_dict(text: str, args, extracting_id) -> dict:
    """
    从字符串中提取包含动作和置信度的字典
    
    Args:
        text (str): 包含目标字典的字符串
        
    Returns:
        dict: 提取出的字典，包含动作和对应的置信度
    """
    # 使用正则表达式匹配目标格式的字典
    result = extract_fixed_intent_dict(text)    
    if len(result) == 0:
        result = extract_last_3_intentions(text)
        if len(result) == 0:
            result = extract_last_3_extended_intentions(text)
            if len(result) == 0:
                
                response = llm_extraction(text, args, extracting_id, PROMPT_INTENT_MATCH)
                result = extract_fixed_intent_dict(response)
                if len(result) == 0:
                    return False, text
    
    return True, result

def extract_value_dict(text: str, args, extracting_id) -> dict:
    """
    从字符串中提取包含动作和置信度的字典
    
    Args:
        text (str): 包含目标字典的字符串
        
    Returns:
        dict: 提取出的字典，包含动作和对应的置信度
    """
    result = extract_fixed_value_dict(text)
    if len(result) == 0:
        # 使用正则表达式匹配目标格式的字典
        result = extract_latest_kv(text, ['active', 'active_cf', 'social', 'social_cf', 'helpful', 'helpful_cf'])
        if len(result) == 0:
            response = llm_extraction(text, args, extracting_id, PROMPT_VALUE_MATCH)
            result = extract_fixed_value_dict(response)
            if len(result) == 0:
                return False, text
        
        return True, result
    else:
        return True, result

def extract_fixed_value_dict(text: str) -> dict:
    # 精确匹配固定格式的 dict，允许空格和小数
    pattern = (
        r'\{\\?"active\\?"\s*:\s*-?\d+\.?\d*\s*,\s*'
        r'\\?"active_cf\\?"\s*:\s*-?\d+\.?\d*\s*,\s*'
        r'\\?"social\\?"\s*:\s*-?\d+\.?\d*\s*,\s*'
        r'\\?"social_cf\\?"\s*:\s*-?\d+\.?\d*\s*,\s*'
        r'\\?"helpful\\?"\s*:\s*-?\d+\.?\d*\s*,\s*'
        r'\\?"helpful_cf\\?"\s*:\s*-?\d+\.?\d*\s*\}'
    )

    matches = re.findall(pattern, text)
    if not matches:
        return {}

    last_match = matches[-1]

    # 还原成 JSON 格式（去除转义）
    try:
        json_str = last_match.replace('\\"', '"')
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {}

def extract_fixed_intent_dict(text):
    # 正则表达式：提取意图字段及其值
    pattern = re.compile(
        r'"most_possible_intention"\s*:\s*"([^"]+)",\s*'  # 匹配双引号包围的值
        r'"most_possible_intention_cf"\s*:\s*([0-9.]+),\s*'
        r'"second_possible_intention"\s*:\s*"([^"]+)",\s*'
        r'"second_possible_intention_cf"\s*:\s*([0-9.]+),\s*'
        r'"third_possible_intention"\s*:\s*"([^"]+)",\s*'
        r'"third_possible_intention_cf"\s*:\s*([0-9.]+)'
    )

    match = pattern.search(text)
    if match:
        try:
            # 提取匹配的各个字段值
            most_possible_intention = match.group(1).strip('"')  # 去掉双引号
            most_possible_intention_cf = float(match.group(2))
            second_possible_intention = match.group(3).strip('"')  # 去掉双引号
            second_possible_intention_cf = float(match.group(4))
            third_possible_intention = match.group(5).strip('"')  # 去掉双引号
            third_possible_intention_cf = float(match.group(6))

            if most_possible_intention_cf > 1:
                return {}
            if second_possible_intention_cf > 1:
                return {}
            if third_possible_intention_cf > 1:
                return {}

            # 将提取的字段转为字典
            intention_data = {
                "most_possible_intention": most_possible_intention,
                "most_possible_intention_cf": most_possible_intention_cf,
                "second_possible_intention": second_possible_intention,
                "second_possible_intention_cf": second_possible_intention_cf,
                "third_possible_intention": third_possible_intention,
                "third_possible_intention_cf": third_possible_intention_cf
            }
            return intention_data

        except Exception as e:
            print(f"Error: {e}")
            return {}
    else:
        return {}


def extract_last_3_intentions(text: str) -> dict:
    # 匹配形式如 Agent_1-Open-Box_4 的字符串
    text = text.lower()
    pattern = re.compile(r'agent_\d+(?:-[\w]+)+')
    matches = list(pattern.finditer(text))

    if len(matches) < 3:
        return {}

    # 取最后三个匹配（从倒数第三个开始）
    last_three = matches[-3:]

    # 用于保存结果
    output = {}

    # 名称对应关系（倒数第一是 third_possible_intention）
    keys = [
        ('most_possible_intention', 'most_possible_intention_cf'),
        ('second_possible_intention', 'second_possible_intention_cf'),
        ('third_possible_intention', 'third_possible_intention_cf')
    ]

    # 从后向前匹配填入对应字段
    for (intent_key, cf_key), match in zip(reversed(keys), reversed(last_three)):
        intention = match.group()
        # 从匹配位置开始往后找第一个数字（float 或 int）
        substring = text[match.end():]
        cf_match = re.search(r'\d+\.\d+|\d+', substring)
        if not cf_match:
            return {}
        confidence = float(cf_match.group())
        output[intent_key] = intention
        output[cf_key] = confidence

    if output['most_possible_intention_cf'] > 1:
        return {}
    if output['second_possible_intention_cf'] > 1:
        return {}
    if output['third_possible_intention_cf'] > 1:
        return {}

    return output

def extract_last_3_extended_intentions(text: str) -> dict:
    # 关键动词集（intent_desc_dict 的 key）
    text = text.lower()
    intent_keys = [
        'get', 'give', 'find', 'open', 'putinto', 'putonto',
        'playwith', 'respondto', 'inform', 'observe',
        'greet', 'harm', 'help', 'requesthelp', 'na'
    ]
    
    # 构造 pattern，匹配以这些 key 开头的 “意图-对象” 结构
    pattern = re.compile(rf'\b(?:{"|".join(intent_keys)})[-\w_]*')
    matches = list(pattern.finditer(text))

    if len(matches) < 3:
        return {}

    last_three = matches[-3:]

    # 名称对照
    keys = [
        ('most_possible_intention', 'most_possible_intention_cf'),
        ('second_possible_intention', 'second_possible_intention_cf'),
        ('third_possible_intention', 'third_possible_intention_cf')
    ]

    output = {}

    for (intent_key, cf_key), match in zip(reversed(keys), reversed(last_three)):
        intention = match.group()
        substring = text[match.end():]
        cf_match = re.search(r'\d+\.\d+|\d+', substring)
        if not cf_match:
            return {}
        confidence = float(cf_match.group())
        if confidence > 1:
            return {}
        output[intent_key] = intention
        output[cf_key] = confidence

    if output['most_possible_intention_cf'] > 1:
        return {}
    if output['second_possible_intention_cf'] > 1:
        return {}
    if output['third_possible_intention_cf'] > 1:
        return {}

    return output

def extract_fixed_action_dict(text: str) -> dict:
    # 正则表达式：提取意图字段及其值
    pattern = re.compile(
        r'"most_possible_action"\s*:\s*"([^"]+)",\s*'  # 匹配双引号包围的值
        r'"most_possible_action_cf"\s*:\s*([0-9.]+),\s*'
        r'"second_possible_action"\s*:\s*"([^"]+)",\s*'
        r'"second_possible_action_cf"\s*:\s*([0-9.]+),\s*'
        r'"third_possible_action"\s*:\s*"([^"]+)",\s*'
        r'"third_possible_action_cf"\s*:\s*([0-9.]+)'
    )

    match = pattern.search(text)
    if match:
        try:
            # 提取匹配的各个字段值
            most_possible_action = match.group(1).strip('"')  # 去掉双引号
            most_possible_action_cf = float(match.group(2))
            second_possible_action = match.group(3).strip('"')  # 去掉双引号
            second_possible_action_cf = float(match.group(4))
            third_possible_action = match.group(5).strip('"')  # 去掉双引号
            third_possible_action_cf = float(match.group(6))

            if most_possible_action_cf > 1:
                return {}
            if second_possible_action_cf > 1:
                return {}
            if third_possible_action_cf > 1:
                return {}

            # 将提取的字段转为字典
            intention_data = {
                "most_possible_action": most_possible_action,
                "most_possible_action_cf": most_possible_action_cf,
                "second_possible_action": second_possible_action,
                "second_possible_action_cf": second_possible_action_cf,
                "third_possible_action": third_possible_action,
                "third_possible_action_cf": third_possible_action_cf
            }
            return intention_data

        except Exception as e:
            print(f"Error: {e}")
            return {}
    else:
        return {}

def extract_last_3_actions(text: str) -> dict:
    # 匹配形式如 Agent_1-Open-Box_4 的字符串
    text = text.lower()
    pattern = re.compile(r'agent_\d+(?:-[\w]+)+')
    matches = list(pattern.finditer(text))

    if len(matches) < 3:
        return {}

    # 取最后三个匹配（从倒数第三个开始）
    last_three = matches[-3:]

    # 用于保存结果
    output = {}

    # 名称对应关系（倒数第一是 third_possible_intention）
    keys = [
        ('most_possible_action', 'most_possible_action_cf'),
        ('second_possible_action', 'second_possible_action_cf'),
        ('third_possible_action', 'third_possible_action_cf')
    ]

    # 从后向前匹配填入对应字段
    for (intent_key, cf_key), match in zip(reversed(keys), reversed(last_three)):
        intention = match.group()
        # 从匹配位置开始往后找第一个数字（float 或 int）
        substring = text[match.end():]
        cf_match = re.search(r'\d+\.\d+|\d+', substring)
        if not cf_match:
            return {}
        confidence = float(cf_match.group())
        output[intent_key] = intention
        output[cf_key] = confidence

    if output['most_possible_action_cf'] > 1:
        return {}
    if output['second_possible_action_cf'] > 1:
        return {}
    if output['third_possible_action_cf'] > 1:
        return {}

    return output

def extract_last_3_extended_actions(text: str) -> dict:
    # 关键动词集（intent_desc_dict 的 key）
    text = text.lower()

    action_keys = [
        'actionmoveto',
        'actionrotateto',
        'actionopen',
        'actionunlock',
        'actiongrab',
        'actiongiveto',
        'actionwavehand',
        'actionmovetoattention',
        'actionpointto',
        'actionwait',
        'actionnodhead',
        'actionshakehead',
        'actionplay',
        'actionputinto',
        'actionputonto',
        'actionputdown',
        'actionfollowpointing',
        'actioneat',
        'actionsmash',
        'actionSpeak',
        'actionperform',
        'actionclose',

    ]
    
    # 构造 pattern，匹配以这些 key 开头的 “意图-对象” 结构
    pattern = re.compile(rf'\b(?:{"|".join(action_keys)})[-\w_]*')
    matches = list(pattern.finditer(text))

    if len(matches) < 3:
        return {}

    last_three = matches[-3:]

    # 名称对照
    keys = [
        ('most_possible_action', 'most_possible_action_cf'),
        ('second_possible_action', 'second_possible_action_cf'),
        ('third_possible_action', 'third_possible_action_cf')
    ]

    output = {}

    for (intent_key, cf_key), match in zip(reversed(keys), reversed(last_three)):
        intention = match.group()
        substring = text[match.end():]
        cf_match = re.search(r'\d+\.\d+|\d+', substring)
        if not cf_match:
            return {}
        confidence = float(cf_match.group())
        if confidence > 1:
            return {}
        output[intent_key] = intention
        output[cf_key] = confidence

    if output['most_possible_action_cf'] > 1:
        return {}
    if output['second_possible_action_cf'] > 1:
        return {}
    if output['third_possible_action_cf'] > 1:
        return {}

    return output

def extract_latest_kv(text: str, keys: list[str]) -> dict:
    result = {}
    for key in keys:
        # 匹配完整的 key 单词
        key_pattern = rf'(?<!\w){key}(?!\w)'
        key_matches = list(re.finditer(key_pattern, text))

        if not key_matches:
            return {}  # 如果某个 key 没找到，直接返回空 dict

        # 找到最后一次匹配
        start_pos = key_matches[-1].end()

        # 从该位置往后找第一个数字
        number_match = re.search(r'-?\d+\.?\d*', text[start_pos:])
        if not number_match:
            return {}  # 找不到对应的数值也返回空 dict

        value_str = number_match.group(0)
        result[key] = float(value_str)
    
    return result

def parse_arguments():

    parser=argparse.ArgumentParser(description='raw data processing')
    parser.add_argument('--TEST_RATIO', default=1)
    parser.add_argument('--MODEL', default="Qwen3-8B", choices=["QwQ", "gpt-4o", "Qwen3", "Qwen3-Online", "QwQ-Online-AWQ", "Claude", "Gemini", "QwQ-AWQ", "DeepSeek-R1", "Llama3", "Qwen3-8B", "DEBUG"])

    return parser.parse_args()

def main(args):
    tested_data = read_json(args.RESULT_SAVE_PATH)
    print(args.RESULT_SAVE_PATH)
    if isinstance(tested_data, dict):
            # New datasave format
        DATA_LENGTH = len(tested_data.keys())
    elif isinstance(tested_data, list):
        # Old datasave format
        DATA_LENGTH = len(tested_data) - 1
    else:
        print("Unknown data format, ERROR")
        return
    
    if tested_data is None:
        print("No existing tested_id_dict found, ERROR")
        return
    
    if 'value' in args.EXP_NAME:
        tested_ids = []
        active_distance_list = []
        social_distance_list = []
        helpful_distance_list = []
        active_confidence_list = []
        social_confidence_list = []
        helpful_confidence_list = []
        ground_truth_active_list = []
        ground_truth_social_list = []
        ground_truth_helpful_list = []
        extracted_active_list = []
        extracted_social_list = []
        extracted_helpful_list = []

    elif 'intent' in args.EXP_NAME:
        tested_ids = []
        most_possible_intention_list = []
        most_possible_intention_cf_list = []
        second_possible_intention_list = []
        second_possible_intention_cf_list = []
        third_possible_intention_list = []
        third_possible_intention_cf_list = []
        ground_truth_intention_list = []

    elif 'action' in args.EXP_NAME:
        tested_ids = []
        most_possible_action_list = []
        most_possible_action_cf_list = []
        second_possible_action_list = []
        second_possible_action_cf_list = []
        third_possible_action_list = []
        third_possible_action_cf_list = []
        ground_truth_action_list = []

    extract_error_dict = {}

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
        
        response = str(data_dict['response']).lower()
        if args.MODEL in ['gpt-4o', 'Gemini', 'Claude', 'DeepSeek-R1']:
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
            answer = str(answer).lower()
        else:

            if isinstance(data_dict['answer'], dict):
                answer = str(data_dict['answer']).lower()
            else:
                answer = data_dict['answer'].lower()
    
        if 'value' in args.EXP_NAME:
            if isinstance(data_dict['response'], dict):
                extracted_value_dict = data_dict['response']
            else:
                done, extracted_value_dict = extract_value_dict(response, args, i)
                if not done:
                    extract_error_dict[i] = response
                    continue
            
            value_dict = ast.literal_eval(answer)
            tested_ids.append(i)
            active_distance_list.append(abs(float(extracted_value_dict['active']) - float(value_dict['active'])))
            social_distance_list.append(abs(float(extracted_value_dict['social']) - float(value_dict['social'])))
            helpful_distance_list.append(abs(float(extracted_value_dict['helpful']) - float(value_dict['helpful'])))
            active_confidence_list.append(float(extracted_value_dict['active_cf']))
            social_confidence_list.append(float(extracted_value_dict['social_cf']))
            helpful_confidence_list.append(float(extracted_value_dict['helpful_cf']))
            ground_truth_active_list.append(float(value_dict['active']))
            ground_truth_social_list.append(float(value_dict['social']))
            ground_truth_helpful_list.append(float(value_dict['helpful']))
            extracted_active_list.append(float(extracted_value_dict['active']))
            extracted_social_list.append(float(extracted_value_dict['social']))
            extracted_helpful_list.append(float(extracted_value_dict['helpful']))
        elif 'intent' in args.EXP_NAME:
            if isinstance(data_dict['response'], dict):
                extracted_intent_dict = data_dict['response']
            else:
                done, extracted_intent_dict = extract_intent_dict(response, args, i)
                if not done:
                    extract_error_dict[i] = response
                    continue
            tested_ids.append(i)
            most_possible_intention_list.append(extracted_intent_dict['most_possible_intention'])
            most_possible_intention_cf_list.append(extracted_intent_dict['most_possible_intention_cf'])
            second_possible_intention_list.append(extracted_intent_dict['second_possible_intention'])
            second_possible_intention_cf_list.append(extracted_intent_dict['second_possible_intention_cf'])
            third_possible_intention_list.append(extracted_intent_dict['third_possible_intention'])
            third_possible_intention_cf_list.append(extracted_intent_dict['third_possible_intention_cf'])
            ground_truth_intention_list.append(answer)
            
        elif 'action' in args.EXP_NAME:
            if isinstance(data_dict['response'], dict):
                extracted_action_dict = data_dict['response']
            else:
                done, extracted_action_dict = extract_action_dict(response, args, i)
                if not done:
                    extract_error_dict[i] = response
                    continue
            tested_ids.append(i)
            most_possible_action_list.append(extracted_action_dict['most_possible_action'])
            most_possible_action_cf_list.append(extracted_action_dict['most_possible_action_cf'])
            second_possible_action_list.append(extracted_action_dict['second_possible_action'])
            second_possible_action_cf_list.append(extracted_action_dict['second_possible_action_cf'])
            third_possible_action_list.append(extracted_action_dict['third_possible_action'])
            third_possible_action_cf_list.append(extracted_action_dict['third_possible_action_cf'])
            ground_truth_action_list.append(answer)

    if 'value' in args.EXP_NAME:
        # 创建 DataFrame
        df = pd.DataFrame({
            'tested_ids': tested_ids,
            'active_distance': active_distance_list,
            'social_distance': social_distance_list,
            'helpful_distance': helpful_distance_list,
            'active_confidence': active_confidence_list,
            'social_confidence': social_confidence_list,
            'helpful_confidence': helpful_confidence_list, 
            'ground_truth_active': ground_truth_active_list,
            'ground_truth_social': ground_truth_social_list,
            'ground_truth_helpful': ground_truth_helpful_list,
            'extracted_active': extracted_active_list,
            'extracted_social': extracted_social_list,
            'extracted_helpful': extracted_helpful_list
        })
    elif 'intent' in args.EXP_NAME:
        df = pd.DataFrame({
            'tested_ids': tested_ids,
            'most_possible_intention': most_possible_intention_list,
            'most_possible_intention_cf': most_possible_intention_cf_list,
            'second_possible_intention': second_possible_intention_list,
            'second_possible_intention_cf': second_possible_intention_cf_list,
            'third_possible_intention': third_possible_intention_list,
            'third_possible_intention_cf': third_possible_intention_cf_list,
            'ground_truth_intention': ground_truth_intention_list
        })
    elif 'action' in args.EXP_NAME:
        df = pd.DataFrame({
            'tested_ids': tested_ids,
            'most_possible_action': most_possible_action_list,
            'most_possible_action_cf': most_possible_action_cf_list,
            'second_possible_action': second_possible_action_list,
            'second_possible_action_cf': second_possible_action_cf_list,
            'third_possible_action': third_possible_action_list,
            'third_possible_action_cf': third_possible_action_cf_list,
            'ground_truth_action': ground_truth_action_list
        })

    # 保存为 CSV 文件
    df.to_csv(args.EXTRACT_DATA_SAVE_PATH, index=False)

    save_json(extract_error_dict, args.EXTRACT_ERROR_SAVE_PATH)
    
if __name__ == "__main__":
    args = parse_arguments()
    args.TEST_VERSION = 'V1'

    for name in ['intent_pred_world_view', 'intent_pred_agent_view', 'value_pred_world_view', 'value_pred_agent_view', 'intent_update_agent_view', 'action_update_agent_view']:
    # for name in ['action_update_agent_view']:
        # for model in ['Qwen3-8B', 'Llama3', 'gpt-4o', 'Gemini', 'Claude', 'DeepSeek-R1']:
        for model in ['Random']:
            args.MODEL=model
            args.EXP_NAME=name
            args.SAVE_PATH = './experiment_res/llms_test/'
            args.SAVE_PATH_PREFIX = name+f"_Model_{args.MODEL}"+"_for_test"+args.TEST_VERSION
            args.RESULT_SAVE_PATH=args.SAVE_PATH+args.SAVE_PATH_PREFIX+'.json'
            args.EXTRACT_ERROR_SAVE_PATH = './experiment_res/match_errors/extract_error_dict_'+args.EXP_NAME+'_'+args.MODEL+'.json'
            args.EXTRACT_DATA_SAVE_PATH = './experiment_res/llms_res/' + args.SAVE_PATH_PREFIX + '.csv'
            args.LLM_EXTRACTION_SAVE_PATH = './experiment_res/prompt_response/llm_extraction_'+args.EXP_NAME+'_'+args.MODEL+'.json'
            main(args)
