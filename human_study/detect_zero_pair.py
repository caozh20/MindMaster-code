import json
import itertools

import sys

sys.path.append('.')

def process_json_files(file1_path, file2_path, output_path):
    # 读取两个json文件
    with open(file1_path, 'r') as f1:
        data1 = json.load(f1)
    with open(file2_path, 'r') as f2:
        data2 = json.load(f2)

    # 从第一个json找出值为0的键的所有配对
    zero_pairs = []
    keys = list(data1['cross_tab'].keys())
    for key1 in keys:
        values = data1['cross_tab'][key1]
        for key2, value in values.items():
            if value == 0:
                zero_pairs.append((key1, key2))

    # 从第二个json中找出值为0的intent并构建嵌套字典
    result_dict = {}
    for key in keys:
        if key in data2['cross_tab']:
            zero_intents = []
            for intent, value in data2['cross_tab'][key].items():
                if value == 0:
                    zero_intents.append(intent)
            
            # 如果没有找到值为0的intent，设为None
            if not zero_intents:
                zero_intents = [None]

            # 生成嵌套字典
            for pair in zero_pairs:
                if pair[0] == key:  # 只处理第一个元素匹配的配对
                    if pair[0] not in result_dict:
                        result_dict[pair[0]] = {}
                    if pair[1] not in result_dict[pair[0]]:
                        result_dict[pair[0]][pair[1]] = {}
                    for intent in zero_intents:
                        result_dict[pair[0]][pair[1]][intent] = 0

    # 将结果保存为json文件
    with open(output_path, 'w') as f:
        json.dump(result_dict, f, indent=4)

    return result_dict


# 使用示例
file1_path = './results/agent_desires_heatmap_data.json'
file2_path = './results/intent_desire_heatmap_data.json'
output_path = './human_study/zero_pair.json'
results = process_json_files(file1_path, file2_path, output_path)