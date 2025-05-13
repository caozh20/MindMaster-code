import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import ast
import os
from pathlib import Path

def extract_intent_action(row):
    # 提取intent
    intent_parts = row['intent'].split('-')
    intent = intent_parts[1] if len(intent_parts) > 1 else None
    
    # 提取action
    try:
        actions = ast.literal_eval(row['actions'])
        action = None
        if actions and len(actions) > 0:
            action_parts = actions[0].split('-')
            if len(action_parts) > 1:
                action = action_parts[1][6:] if action_parts[1].startswith('Action') else action_parts[1]
    except (ValueError, SyntaxError):
        action = None
    
    return pd.Series([intent, action])

def analyze_intent_action_distribution():
    # 创建输出目录
    output_dir = Path('./analysis_results/intent_action_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取数据
    df = pd.read_csv('./data/dataset_intent_pred_world_view.csv')
    
    # 提取intent和action
    df[['intent', 'action']] = df.apply(extract_intent_action, axis=1)
    
    # 过滤掉None值
    df = df.dropna(subset=['intent', 'action'])
    
    # 计算频次
    frequency = df.groupby(['intent', 'action']).size().reset_index(name='count')
    
    # 获取所有唯一的intent和action用于排序
    all_intents = sorted(df['intent'].unique())
    all_actions = sorted(df['action'].unique())
    
    # 创建热力图数据
    heatmap_data = frequency.pivot(index='intent', columns='action', values='count')
    # 确保所有intent和action都在热力图中
    heatmap_data = heatmap_data.reindex(index=all_intents, columns=all_actions).fillna(0)
    
    # 保存Excel文件
    with pd.ExcelWriter(output_dir / 'intent_action_analysis.xlsx') as writer:
        # 保存热力图格式的数据
        heatmap_data.to_excel(writer, sheet_name='Heatmap')
        
        # 保存详细数据
        frequency.to_excel(writer, sheet_name='Detailed Data', index=False)
    
    # 绘制并保存柱状图
    plt.figure(figsize=(15, 8))
    sns.barplot(data=frequency, x='intent', y='count', hue='action')
    plt.xticks(rotation=45)
    plt.title('Intent-Action Distribution')
    plt.tight_layout()
    plt.savefig(output_dir / 'bar_chart.png')
    plt.close()
    
    # 绘制并保存饼图
    plt.figure(figsize=(12, 12))
    frequency.groupby('action')['count'].sum().plot.pie(autopct='%1.1f%%')
    plt.title('Action Distribution')
    plt.savefig(output_dir / 'pie_chart.png')
    plt.close()
    
    # 绘制并保存热力图
    plt.figure(figsize=(15, 10))
    sns.heatmap(heatmap_data, annot=True, fmt='g', cmap='YlOrRd')
    plt.title('Intent-Action Heatmap')
    plt.tight_layout()
    plt.savefig(output_dir / 'heatmap.png')
    plt.close()

if __name__ == '__main__':
    analyze_intent_action_distribution()
