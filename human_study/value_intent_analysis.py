import os
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import json

import sys 
sys.path.append('./')

def load_pickle_data(file_path: str) -> List:
    """加载pickle文件"""
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def process_csv_file(csv_path: str, pickle_path: str) -> Tuple[Dict, pd.DataFrame, List]:
    """处理单个CSV文件，返回agent_id到desire的映射和包含intent的DataFrame"""
    print(f"\n处理文件: {csv_path}")
    
    # 加载pickle数据
    agents = load_pickle_data(pickle_path)
    print(f"加载的agents数量: {len(agents)}")
    
    agents = agents.reset_index(drop=True)
    agents = agents['world_agents'].apply(pickle.loads)[0]
    
    # 创建agent_id到desire的映射
    agent_desire_map = {}
    for agent in agents:
        agent_desire_map[agent.id] = agent.desire.to_dict()
    print(f"创建的agent_desire_map大小: {len(agent_desire_map)}")
    
    # 读取CSV文件
    df = pd.read_csv(csv_path)
    print(f"CSV文件行数: {len(df)}")
    print(f"原始intent分布:\n{df['your_high_intent'].value_counts()}")
    
    # 创建新的intent列
    df['intent'] = None
    
    # 处理NA的情况
    na_mask = df['your_high_intent'] == 'NA'
    print(f"NA值的数量: {na_mask.sum()}")
    df.loc[na_mask, 'intent'] = 'NA'
    
    # 处理非NA的情况
    non_na_mask = ~na_mask
    df.loc[non_na_mask, 'intent'] = df.loc[non_na_mask, 'your_high_intent'].apply(
        lambda x: None if pd.isna(x) else (
            None if x[0].isdigit() and x.replace('-', '').isdigit() else (
                x.split('-', 1)[1] if '-' in x and x.split('-')[0].isdigit() else x
            )
        )
    )
    
    # 对非None且非NA的intent进行截取
    valid_mask = ~df['intent'].isna() & (df['intent'] != 'NA')
    df.loc[valid_mask, 'intent'] = df.loc[valid_mask, 'intent'].str.split('-').str[0]
    
    # 检测包含数字的intent
    number_intents = []
    for idx, row in df.iterrows():
        if row['intent'] is not None and row['intent'] != 'NA' and any(c.isdigit() for c in str(row['intent'])):
            number_intents.append({
                '文件': csv_path,
                '原始intent': row['your_high_intent'],
                '处理后的intent': row['intent'],
                'user_agent_id': row['user_agent_id']
            })
            df.at[idx, 'intent'] = None
    
    # 将空字符串转换为None
    df['intent'] = df['intent'].replace('', None)
    print(f"处理后的intent分布:\n{df['intent'].value_counts()}")
    print(f"None值的数量: {df['intent'].isna().sum()}")
    
    return agent_desire_map, df, number_intents

def analyze_desire_intent_distribution(agent_desire_map: Dict, df: pd.DataFrame) -> Dict:
    """分析desire和intent的分布"""
    print("\n开始分析desire和intent的分布")
    results = {
        'active': {},
        'social': {},
        'helpful': {},
        'tuple': {}
    }
    
    # 遍历每一行数据
    skipped_empty = 0
    skipped_na = 0
    skipped_no_agent = 0
    processed_rows = 0
    
    for _, row in df.iterrows():
        user_agent_id = row['user_agent_id']
        intent = row['intent']
        
        # 如果intent为空，跳过该行
        if intent is None:
            skipped_empty += 1
            continue
            
        # 如果intent为NA，跳过该行
        if intent == 'NA':
            skipped_na += 1
            continue
            
        if user_agent_id not in agent_desire_map:
            skipped_no_agent += 1
            continue
            
        processed_rows += 1
        desire = agent_desire_map[user_agent_id]
        
        # 确保intent是字符串类型
        intent = str(intent) if intent is not None else None
        
        # 统计各个维度的分布
        for dim in ['active', 'social', 'helpful']:
            value = float(desire[dim])  # 确保值是浮点数
            if value not in results[dim]:
                results[dim][value] = {}
            if intent not in results[dim][value]:
                results[dim][value][intent] = 0
            results[dim][value][intent] += 1
            
        # 统计tuple的分布
        tuple_key = (float(desire['active']), float(desire['social']), float(desire['helpful']))
        if tuple_key not in results['tuple']:
            results['tuple'][tuple_key] = {}
        if intent not in results['tuple'][tuple_key]:
            results['tuple'][tuple_key][intent] = 0
        results['tuple'][tuple_key][intent] += 1
    
    print(f"跳过的空值行数: {skipped_empty}")
    print(f"跳过的NA值行数: {skipped_na}")
    print(f"跳过的无agent行数: {skipped_no_agent}")
    print(f"处理的行数: {processed_rows}")
    
    # 确保每个维度都有数据
    for dim in ['active', 'social', 'helpful']:
        if not results[dim]:
            print(f"Warning: No data available for dimension {dim}")
            results[dim] = {0.0: {'NA': 0}}  # 添加一个默认值
    
    if not results['tuple']:
        print("Warning: No tuple data available")
        results['tuple'] = {(0.0, 0.0, 0.0): {'NA': 0}}  # 添加一个默认值
    
    return results

def create_heatmap(data: Dict, title: str, save_path: str):
    """创建并保存热力图"""
    # 将数据转换为DataFrame格式
    df = pd.DataFrame(data).fillna(0)
    
    # 检查数据是否为空
    if df.empty:
        print(f"Warning: No data available for {title}")
        return
        
    # 确保所有值都是数值类型
    df = df.astype(float)
    
    # 检查是否有非零数据
    if df.values.sum() == 0:
        print(f"Warning: All values are zero for {title}")
        return
    
    try:
        # 对列进行排序（x轴）
        df = df.reindex(sorted(df.columns, key=float), axis=1)
        
        # 创建热力图
        plt.figure(figsize=(12, 8))
        sns.heatmap(df, annot=True, fmt='g', cmap='YlOrRd')
        plt.title(title)
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(save_path)
        plt.close()
    except Exception as e:
        print(f"Error creating heatmap for {title}: {str(e)}")
        print("Data shape:", df.shape)
        print("Data sample:", df.head())

def save_to_excel(results: Dict, number_intents: List, save_path: str):
    """将结果保存到Excel文件"""
    with pd.ExcelWriter(save_path) as writer:
        # 保存原有的统计结果
        for dim in ['active', 'social', 'helpful']:
            # 创建完整的数据表格
            all_intents = set()
            all_values = set()
            
            # 收集所有的intent和value
            for value, intents in results[dim].items():
                all_values.add(float(value))
                all_intents.update(intents.keys())
            
            # 创建完整的DataFrame
            data = []
            for intent in sorted(all_intents):
                for value in sorted(all_values):
                    count = results[dim].get(value, {}).get(intent, 0)
                    data.append({
                        'intent': intent,
                        'value': value,
                        'count': count
                    })
            
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=dim, index=False)
            
            # 创建热力图数据
            heatmap_data = pd.DataFrame(results[dim]).fillna(0)
            heatmap_data = heatmap_data.reindex(sorted(heatmap_data.columns, key=float), axis=1)
            heatmap_data.to_excel(writer, sheet_name=f'{dim}_heatmap_data', index=True)
        
        # 处理tuple数据
        tuple_data = {}
        for key, value in results['tuple'].items():
            tuple_data[str(key)] = value
        df_tuple = pd.DataFrame(tuple_data).fillna(0)
        df_tuple.to_excel(writer, sheet_name='tuple')
        
        # 保存包含数字的intent到新的sheet
        if number_intents:
            df_number = pd.DataFrame(number_intents)
            df_number.to_excel(writer, sheet_name='包含数字的intent', index=False)

def main():
    # 创建保存结果的目录
    output_dir = './analysis_results/desire_intent_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有CSV文件
    data_dir = './data/grouped_data_csv'
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    # 合并所有结果
    all_results = {
        'active': {},
        'social': {},
        'helpful': {},
        'tuple': {}
    }
    
    # 记录特殊intent的信息
    special_intents_info = []
    all_number_intents = []
    
    # 统计信息
    total_empty = 0
    total_na = 0
    total_no_agent = 0
    total_processed = 0
    total_rows = 0
    
    for csv_file in csv_files:
        csv_path = os.path.join(data_dir, csv_file)
        pickle_path = os.path.join('./data/grouped_data_pickle', csv_file.replace('.csv', '.pkl'))
        
        if not os.path.exists(pickle_path):
            print(f"Warning: No pickle file found for {csv_file}")
            continue
            
        print(f"\n处理文件: {csv_file}")
        agent_desire_map, df, number_intents = process_csv_file(csv_path, pickle_path)
        all_number_intents.extend(number_intents)
        
        # 记录包含1或2的原始intent
        special_mask = df['your_high_intent'].str.contains('1|2', na=False, case=False)
        if special_mask.any():
            special_rows = df[special_mask]
            for _, row in special_rows.iterrows():
                if row['intent'] is not None and row['intent'] != 'NA' and ('1' in row['intent'] or '2' in row['intent']):
                    special_intents_info.append({
                        '文件': csv_file,
                        '原始intent': row['your_high_intent'],
                        '处理后的intent': row['intent'],
                        'user_agent_id': row['user_agent_id']
                    })
        
        # 更新统计信息
        file_empty = df['intent'].isna().sum()
        file_na = (df['intent'] == 'NA').sum()
        file_no_agent = len(df) - len(df[df['user_agent_id'].isin(agent_desire_map.keys())])
        file_processed = len(df) - file_empty - file_na - file_no_agent
        
        total_empty += file_empty
        total_na += file_na
        total_no_agent += file_no_agent
        total_processed += file_processed
        total_rows += len(df)
        
        print(f"文件统计信息:")
        print(f"文件总行数: {len(df)}")
        print(f"文件空值行数: {file_empty}")
        print(f"文件NA值行数: {file_na}")
        print(f"文件无agent行数: {file_no_agent}")
        print(f"文件处理行数: {file_processed}")
        
        results = analyze_desire_intent_distribution(agent_desire_map, df)
        
        # 合并结果
        for dim in ['active', 'social', 'helpful']:
            for value, intents in results[dim].items():
                if value not in all_results[dim]:
                    all_results[dim][value] = {}
                for intent, count in intents.items():
                    if intent not in all_results[dim][value]:
                        all_results[dim][value][intent] = 0
                    all_results[dim][value][intent] += count
                    
        for tuple_key, intents in results['tuple'].items():
            if tuple_key not in all_results['tuple']:
                all_results['tuple'][tuple_key] = {}
            for intent, count in intents.items():
                if intent not in all_results['tuple'][tuple_key]:
                    all_results['tuple'][tuple_key][intent] = 0
                all_results['tuple'][tuple_key][intent] += count
    
    # 输出总体统计信息
    print("\n总体统计信息:")
    print(f"总行数: {total_rows}")
    print(f"总空值行数: {total_empty}")
    print(f"总NA值行数: {total_na}")
    print(f"总无agent行数: {total_no_agent}")
    print(f"总处理行数: {total_processed}")
    print(f"验证总和: {total_empty + total_na + total_no_agent + total_processed} (应与总行数相等)")
    
    # 创建并保存热力图
    for dim in ['active', 'social', 'helpful']:
        create_heatmap(
            all_results[dim],
            f'Intent Distribution by {dim.capitalize()}',
            os.path.join(output_dir, f'{dim}_heatmap.png')
        )
    
    # 保存到Excel
    save_to_excel(all_results, all_number_intents, os.path.join(output_dir, 'desire_intent_distribution.xlsx'))
    
    # 保存特殊intent信息到单独的Excel文件
    if special_intents_info:
        df_special = pd.DataFrame(special_intents_info)
        df_special.to_excel(os.path.join(output_dir, 'special_intents.xlsx'), index=False)
        print(f"\n找到 {len(special_intents_info)} 个包含'1'或'2'的intent")
    
    # 保存统计信息到文件
    with open(os.path.join(output_dir, 'statistics.txt'), 'w') as f:
        f.write("总体统计信息:\n")
        f.write(f"总行数: {total_rows}\n")
        f.write(f"总空值行数: {total_empty}\n")
        f.write(f"总NA值行数: {total_na}\n")
        f.write(f"总无agent行数: {total_no_agent}\n")
        f.write(f"总处理行数: {total_processed}\n")
        f.write(f"验证总和: {total_empty + total_na + total_no_agent + total_processed} (应与总行数相等)\n")

if __name__ == '__main__':
    main()