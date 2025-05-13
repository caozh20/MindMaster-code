import pandas as pd
import ast
from typing import List, Dict, Tuple
import os
import matplotlib.pyplot as plt
from collections import Counter
import datetime
import numpy as np
from itertools import combinations

def load_and_process_actions(file_path: str = "./data/dataset_intent_pred_world_view_segment_False.csv") -> List[str]:
    """
    加载CSV文件并处理actions列，将字符串形式的列表转换为实际的Python列表，
    然后将所有元素整理成一个大的列表
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        所有action元素组成的列表
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件 {file_path} 不存在")
    
    # 读取CSV文件
    df = pd.read_csv(file_path)
    
    # 检查是否包含actions列
    if 'actions' not in df.columns:
        raise ValueError("CSV文件中不包含'actions'列")
    
    # 初始化一个空列表来存储所有action
    all_actions = []
    
    # 遍历每一行的actions列
    for action_str in df['actions']:
        # 使用ast.literal_eval将字符串形式的列表转换为Python列表
        try:
            action_list = ast.literal_eval(action_str)
            # 将每个action添加到总列表中
            all_actions.extend(action_list)
        except (SyntaxError, ValueError) as e:
            print(f"处理行时出错: {action_str}")
            print(f"错误: {str(e)}")
            continue
    
    return all_actions

def extract_action_types(actions: List[str]) -> List[str]:
    """
    从动作字符串中提取核心动作类型，例如将'Agent_1-ActionRotateTo-Box_6'处理为'RotateTo'
    
    Args:
        actions: 动作字符串列表
        
    Returns:
        处理后的核心动作类型列表
    """
    action_types = []
    
    for action in actions:
        try:
            # 按'-'分割字符串
            parts = action.split('-')
            
            # 检查是否有足够的部分，并且中间部分以'Action'开头
            if len(parts) >= 2 and parts[1].startswith('Action'):
                # 提取中间部分并去除'Action'前缀
                action_type = parts[1][6:]  # 去除'Action'前缀（长度为6）
                action_types.append(action_type)
            else:
                print(f"无法解析动作字符串: {action}")
                action_types.append("Unknown")
        except Exception as e:
            print(f"处理动作时出错: {action}")
            print(f"错误: {str(e)}")
            action_types.append("Error")
    
    return action_types

def count_action_types(action_types: List[str]) -> Dict[str, int]:
    """
    统计各种动作类型的频次
    
    Args:
        action_types: 动作类型列表
        
    Returns:
        动作类型及其频次的字典
    """
    return dict(Counter(action_types))

def analyze_action_transitions(action_types: List[str]) -> Dict[Tuple[str, str], int]:
    """
    分析动作转换的频次
    
    Args:
        action_types: 动作类型列表
        
    Returns:
        动作转换及其频次的字典，键为(前一个动作, 后一个动作)的元组
    """
    transitions = {}
    
    # 遍历动作列表，分析相邻动作之间的转换
    for i in range(len(action_types) - 1):
        current_action = action_types[i]
        next_action = action_types[i + 1]
        transition = (current_action, next_action)
        
        transitions[transition] = transitions.get(transition, 0) + 1
    
    return transitions

def analyze_n_gram_transitions(action_types: List[str], n: int = 3) -> Dict[Tuple[str, ...], int]:
    """
    分析n阶动作转换的频次
    
    Args:
        action_types: 动作类型列表
        n: n-gram的阶数，默认为3
        
    Returns:
        n阶动作转换及其频次的字典，键为n个连续动作的元组
    """
    n_gram_transitions = {}
    
    # 遍历动作列表，分析n个连续动作的转换
    for i in range(len(action_types) - n + 1):
        # 获取n个连续动作
        n_gram = tuple(action_types[i:i+n])
        n_gram_transitions[n_gram] = n_gram_transitions.get(n_gram, 0) + 1
    
    return n_gram_transitions

def visualize_and_save_results(action_counts: Dict[str, int], 
                              transitions: Dict[Tuple[str, str], int],
                              n_gram_transitions: Dict[Tuple[str, ...], int] = None,
                              output_dir: str = None):
    """
    可视化动作类型频次和转换频次并保存结果
    
    Args:
        action_counts: 动作类型及其频次的字典
        transitions: 动作转换及其频次的字典
        n_gram_transitions: n阶动作转换及其频次的字典
        output_dir: 输出目录
    """
    # 创建输出目录（如果未指定，则创建带时间戳的目录）
    if output_dir is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("./analysis_results", f"action_analysis_{timestamp}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备数据
    actions = list(action_counts.keys())
    counts = list(action_counts.values())
    
    # 按频次排序
    sorted_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)
    sorted_actions = [actions[i] for i in sorted_indices]
    sorted_counts = [counts[i] for i in sorted_indices]
    
    # 1. 生成柱状图
    plt.figure(figsize=(12, 8))
    plt.bar(sorted_actions, sorted_counts, color='royalblue')
    plt.title('动作类型频次分布')
    plt.xlabel('动作类型')
    plt.ylabel('频次')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # 保存柱状图
    bar_chart_path = os.path.join(output_dir, 'action_frequency_bar.png')
    plt.savefig(bar_chart_path)
    plt.close()
    
    # 2. 生成饼图
    plt.figure(figsize=(10, 10))
    
    # 如果动作类型太多，只显示前10个，其他合并为"其他"
    if len(sorted_actions) > 10:
        top_actions = sorted_actions[:10]
        top_counts = sorted_counts[:10]
        other_count = sum(sorted_counts[10:])
        
        labels = top_actions + ['其他']
        sizes = top_counts + [other_count]
    else:
        labels = sorted_actions
        sizes = sorted_counts
    
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # 保证饼图是圆形的
    plt.title('动作类型占比')
    
    # 保存饼图
    pie_chart_path = os.path.join(output_dir, 'action_frequency_pie.png')
    plt.savefig(pie_chart_path)
    plt.close()
    
    # 3. 生成Excel表格 - 动作频次
    df_actions = pd.DataFrame({
        '动作类型': sorted_actions,
        '频次': sorted_counts,
        '占比(%)': [count / sum(counts) * 100 for count in sorted_counts]
    })
    
    excel_actions_path = os.path.join(output_dir, 'action_frequency.xlsx')
    df_actions.to_excel(excel_actions_path, index=False)
    
    # 4. 生成热力图 - 动作转换
    # 获取所有唯一的动作类型
    unique_actions = sorted(set([a for t in transitions.keys() for a in t]))
    
    # 创建一个完整的转换矩阵，包括所有可能的转换（包括频率为0的）
    transition_matrix = np.zeros((len(unique_actions), len(unique_actions)))
    
    # 填充转换矩阵
    for (from_action, to_action), count in transitions.items():
        from_idx = unique_actions.index(from_action)
        to_idx = unique_actions.index(to_action)
        transition_matrix[from_idx, to_idx] = count
    
    # 绘制热力图
    plt.figure(figsize=(12, 10))
    plt.imshow(transition_matrix, cmap='YlGnBu')
    plt.colorbar(label='转换频次')
    plt.title('动作转换热力图')
    plt.xlabel('目标动作')
    plt.ylabel('源动作')
    plt.xticks(range(len(unique_actions)), unique_actions, rotation=45, ha='right')
    plt.yticks(range(len(unique_actions)), unique_actions)
    plt.tight_layout()
    
    # 保存热力图
    heatmap_path = os.path.join(output_dir, 'action_transition_heatmap.png')
    plt.savefig(heatmap_path)
    plt.close()
    
    # 5. 生成Excel表格 - 动作转换
    # 创建转换数据DataFrame
    transition_data = []
    for i, from_action in enumerate(unique_actions):
        for j, to_action in enumerate(unique_actions):
            transition_data.append({
                '源动作': from_action,
                '目标动作': to_action,
                '转换频次': transition_matrix[i, j]
            })
    
    df_transitions = pd.DataFrame(transition_data)
    
    # 按照源动作和目标动作排序，确保y轴和x轴的排列顺序相同
    df_transitions = df_transitions.sort_values(['源动作', '目标动作'])
    
    excel_transitions_path = os.path.join(output_dir, 'action_transitions.xlsx')
    df_transitions.to_excel(excel_transitions_path, index=False)
    
    # 6. 生成Excel表格 - n阶动作转换
    if n_gram_transitions:
        n_gram_data = []
        for n_gram, count in n_gram_transitions.items():
            n_gram_data.append({
                '动作序列': ' -> '.join(n_gram),
                '转换频次': count
            })
        
        df_n_gram = pd.DataFrame(n_gram_data)
        df_n_gram = df_n_gram.sort_values('转换频次', ascending=False)
        
        excel_n_gram_path = os.path.join(output_dir, f'{len(n_gram)}_gram_transitions.xlsx')
        df_n_gram.to_excel(excel_n_gram_path, index=False)
        
        print(f"n阶动作转换Excel表格: {excel_n_gram_path}")
    
    print(f"分析结果已保存至: {output_dir}")
    print(f"动作频次柱状图: {bar_chart_path}")
    print(f"动作频次饼图: {pie_chart_path}")
    print(f"动作频次Excel表格: {excel_actions_path}")
    print(f"动作转换热力图: {heatmap_path}")
    print(f"动作转换Excel表格: {excel_transitions_path}")

if __name__ == "__main__":
    # 加载并处理数据
    all_actions = load_and_process_actions()
    
    # 提取核心动作类型
    action_types = extract_action_types(all_actions)
    
    # 统计动作类型频次
    action_counts = count_action_types(action_types)
    
    # 分析动作转换
    transitions = analyze_action_transitions(action_types)
    
    # 分析n阶动作转换 (这里以3阶为例)
    n_gram_transitions = analyze_n_gram_transitions(action_types, n=3)
    
    # 可视化并保存结果
    visualize_and_save_results(action_counts, transitions, n_gram_transitions)
    
    # 打印结果的前10个元素作为示例
    print(f"共有 {len(action_types)} 个动作类型")
    print("动作类型统计 (前10项):")
    for i, (action_type, count) in enumerate(sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]):
        print(f"{i+1}. {action_type}: {count}次")
    
    print("\n动作转换统计 (前10项):")
    # 按转换频次排序，但只显示非零转换
    non_zero_transitions = [(k, v) for k, v in transitions.items() if v > 0]
    for i, ((from_action, to_action), count) in enumerate(sorted(non_zero_transitions, key=lambda x: x[1], reverse=True)[:10]):
        print(f"{i+1}. {from_action} -> {to_action}: {count}次")
    
    print("\n3阶动作转换统计 (前10项):")
    for i, (n_gram, count) in enumerate(sorted(n_gram_transitions.items(), key=lambda x: x[1], reverse=True)[:10]):
        print(f"{i+1}. {' -> '.join(n_gram)}: {count}次")
