import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from collections import Counter
import ast
from datetime import datetime
import argparse

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def parse_values(value_str):
    """
    解析价值字符串为字典
    
    Args:
        value_str: 包含价值信息的字符串
        
    Returns:
        解析后的字典或None（如果解析失败）
    """
    try:
        # 尝试直接解析JSON字符串
        return json.loads(value_str)
    except:
        try:
            # 如果不是JSON格式，尝试使用ast.literal_eval
            return ast.literal_eval(value_str)
        except:
            print(f"无法解析: {value_str}")
            return None

def load_and_preprocess_data(data_path, test):
    """
    加载并预处理数据
    
    Args:
        data_path: 数据文件路径
        
    Returns:
        处理后的DataFrame
    """
    df = pd.read_csv(data_path)
    
    print(test)
    value_dimensions = ['active', 'social', 'helpful']
    if test:
        df['parsed_values'] = df['ground_truth_values'].apply(parse_values)
        
        # 提取各个维度的值
        for dim in value_dimensions:
            df[dim] = df['parsed_values'].apply(lambda x: x.get(dim, None) if x else None)
        
        # 创建整体值的表示
        df['value_tuple'] = df['parsed_values'].apply(
            lambda x: tuple(x.get(dim, 0) for dim in value_dimensions) if x else None
        )
    else:
    # 提取各个维度的值
        for dim in value_dimensions:
            df[dim] = df['extracted_{}'.format(dim)]
        
        # 将df[dim]转化为一个tuple
        df['value_tuple'] = df[value_dimensions].apply(
            lambda x: tuple(x) if all(x.notnull()) else None, axis=1
        )
    
    return df, value_dimensions

def calculate_statistics(df, value_dimensions):
    """
    计算统计信息
    
    Args:
        df: 数据DataFrame
        value_dimensions: 价值维度列表
        
    Returns:
        dimension_stats: 各维度统计
        tuple_stats: 整体值统计
    """
    # 统计每个维度的分布
    dimension_stats = {}
    for dim in value_dimensions:
        dimension_stats[dim] = df[dim].value_counts().sort_index()
    
    # 统计整体值的分布
    tuple_stats = df['value_tuple'].value_counts().sort_index()
    
    return dimension_stats, tuple_stats

def save_statistics_to_excel(dimension_stats, tuple_stats, output_path):
    """
    保存统计结果到Excel
    
    Args:
        dimension_stats: 各维度统计
        tuple_stats: 整体值统计
        output_path: 输出文件路径
    """
    with pd.ExcelWriter(output_path) as writer:
        # 保存各个维度的统计
        for dim, stats in dimension_stats.items():
            stats.to_frame('count').to_excel(writer, sheet_name=f'{dim}_distribution')
        
        # 保存整体值的统计
        tuple_stats.to_frame('count').to_excel(writer, sheet_name='value_tuple_distribution')

def plot_dimension_distributions(dimension_stats, output_dir):
    """
    绘制各维度的分布图
    
    Args:
        dimension_stats: 各维度统计
        output_dir: 输出目录
    """
    # 绘制柱状图
    plt.figure(figsize=(15, 10))
    for i, (dim, stats) in enumerate(dimension_stats.items()):
        plt.subplot(1, 3, i+1)
        plt.bar(stats.index, stats.values)
        plt.title(f'{dim} 维度分布')
        plt.xlabel('值')
        plt.ylabel('频次')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'value_dimensions_bar.png'), dpi=300)
    plt.close()
    
    # 绘制饼图
    plt.figure(figsize=(15, 10))
    for i, (dim, stats) in enumerate(dimension_stats.items()):
        plt.subplot(1, 3, i+1)
        plt.pie(stats.values, labels=stats.index, autopct='%1.1f%%')
        plt.title(f'{dim} 维度分布')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'value_dimensions_pie.png'), dpi=300)
    plt.close()

def plot_tuple_distribution(tuple_stats, output_dir):
    """
    绘制整体值的分布图
    
    Args:
        tuple_stats: 整体值统计
        output_dir: 输出目录
    """
    tuple_labels = [str(t) for t in tuple_stats.index]
    
    # 绘制柱状图
    plt.figure(figsize=(12, 6))
    plt.bar(tuple_labels, tuple_stats.values)
    plt.title('整体价值分布')
    plt.xlabel('价值组合')
    plt.ylabel('频次')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'value_tuple_bar.png'), dpi=300)
    plt.close()
    
    # 绘制饼图
    plt.figure(figsize=(10, 10))
    plt.pie(tuple_stats.values, labels=tuple_labels, autopct='%1.1f%%')
    plt.title('整体价值分布')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'value_tuple_pie.png'), dpi=300)
    plt.close()

def plot_correlation_heatmap(df, value_dimensions, output_dir):
    """
    绘制维度相关性热力图
    
    Args:
        df: 数据DataFrame
        value_dimensions: 价值维度列表
        output_dir: 输出目录
    """
    plt.figure(figsize=(10, 8))
    correlation_matrix = df[value_dimensions].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('价值维度相关性热力图')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'value_correlation_heatmap.png'), dpi=300)
    plt.close()

def analyze_value_data(data_path, output_dir, test):
    """
    分析价值数据的主函数
    
    Args:
        data_path: 数据文件路径
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载和预处理数据
    df, value_dimensions = load_and_preprocess_data(data_path, test)
    
    # 计算统计信息
    dimension_stats, tuple_stats = calculate_statistics(df, value_dimensions)
    
    # 保存统计结果到Excel
    save_statistics_to_excel(dimension_stats, tuple_stats, 
                            os.path.join(output_dir, 'value_statistics.xlsx'))
    
    # 绘制各维度的分布图
    plot_dimension_distributions(dimension_stats, output_dir)
    
    # 绘制整体值的分布图
    plot_tuple_distribution(tuple_stats, output_dir)
    
    # 绘制相关性热力图
    plot_correlation_heatmap(df, value_dimensions, output_dir)
    
    print(f"分析完成，结果已保存到 {output_dir} 目录")

if __name__ == "__main__":
    # 设置路径
    # data_path = "./data/dataset_value_pred_world_view_segment_True_for_test.csv"
    # output_dir = f"./experiment_codes/llms/analysis/value/test"
    
    # 运行分析
    # for model in ['Claude', 'DeepSeek-R1', 'Gemini', 'gpt-4o', 'Llama3', 'Qwen3-8B', 'Random']:
    #     data_path = f'./experiment_res/llms_res/value_pred_world_view_Model_{model}_for_testV1.csv'
    #     output_dir = f"./experiment_codes/llms/analysis/value/{model}"
        
    #     # 分析价值数据
    #     analyze_value_data(data_path, output_dir)
    parser = argparse.ArgumentParser(description="Value Analysis")
    parser.add_argument('--data_path', type=str, required=True, help='Path to the data file')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory to save the output files')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    analyze_value_data(args.data_path, args.output_dir, args.test)