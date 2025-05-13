import pandas as pd
import ast
from typing import List, Dict, Tuple
import os
import matplotlib.pyplot as plt
from collections import Counter
import datetime
import numpy as np
from itertools import combinations

def load_and_process_actions(file_path: str = "./data/dataset_intent_pred_world_view_segment_False.csv", top_3=False) -> List[str]:
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
    if 'most_possible_action' not in df.columns:
        raise ValueError("CSV文件中不包含'actions'列")
    
    # 初始化一个空列表来存储所有action
    all_actions = []
    
    # 遍历每一行的actions列
    for action_str in df['most_possible_action']:
        # 使用ast.literal_eval将字符串形式的列表转换为Python列表
        try:
            # action_list = ast.literal_eval(action_str)
            action_list = [action_str]
            # 将每个action添加到总列表中
            all_actions.extend(action_list)
        except (SyntaxError, ValueError) as e:
            print(f"处理行时出错: {action_str}")
            print(f"错误: {str(e)}")
            continue
    
    # top_3
    if top_3:
        for action_str in df['second_possible_action']:
            # 使用ast.literal_eval将字符串形式的列表转换为Python列表
            try:
                # action_list = ast.literal_eval(action_str)
                action_list = [action_str]
                # 将每个action添加到总列表中
                all_actions.extend(action_list)
            except (SyntaxError, ValueError) as e:
                print(f"处理行时出错: {action_str}")
                print(f"错误: {str(e)}")
                continue

        for action_str in df['third_possible_action']:
            # 使用ast.literal_eval将字符串形式的列表转换为Python列表
            try:
                # action_list = ast.literal_eval(action_str)
                action_list = [action_str]
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
            action = action.lower()
            parts = action.split('-')
            
            # # 检查是否有足够的部分，并且中间部分以'Action'开头
            # if len(parts) >= 2 and parts[1].startswith('action'):
            #     # 提取中间部分并去除'Action'前缀
            #     action_type = parts[1][6:]  # 去除'Action'前缀（长度为6）
            #     action_types.append(action_type)
            # else:
            #     print(f"无法解析动作字符串: {action}")
            #     action_types.append("Unknown")
            for part in parts:
                if part.startswith('action'):
                    action_type = part[6:]
                    action_types.append(action_type)
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
        output_dir = "./experiment_codes/llms/analysis/action"
    
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
    
    print(f"分析结果已保存至: {output_dir}")
    print(f"动作频次柱状图: {bar_chart_path}")
    print(f"动作频次饼图: {pie_chart_path}")
    print(f"动作频次Excel表格: {excel_actions_path}")

if __name__ == "__main__":
    # 加载并处理数据
    parser = argparse.ArgumentParser(description="分析动作类型")
    parser.add_argument('--file_path', type=str, default=None, help='CSV文件路径')
    parser.add_argument('--output_dir', type=str, default=None, help='输出目录')
    parser.add_argument('--top_3', action='store_false')
    args = parser.parse_args()

    all_actions = load_and_process_actions(file_path=args.file_path, top_3=args.top_3)

    # 提取核心动作类型
    action_types = extract_action_types(all_actions)
    
    # 统计动作类型频次
    action_counts = count_action_types(action_types)
    
    transitions = None
    n_gram_transitions = None

    # 可视化并保存结果
    # visualize_and_save_results(action_counts, transitions, n_gram_transitions, output_dir=f"./experiment_codes/llms/analysis/action/test")
    visualize_and_save_results(action_counts, transitions, n_gram_transitions, output_dir=args.output_dir)
    
    # 打印结果的前10个元素作为示例
    print(f"共有 {len(action_types)} 个动作类型")
    print("动作类型统计 (前10项):")
    for i, (action_type, count) in enumerate(sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]):
        print(f"{i+1}. {action_type}: {count}次")

