import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import seaborn as sns

def analyze_other_desire_data():
    # 创建结果目录
    result_dir = './analysis_results/other_desire_analysis'
    os.makedirs(result_dir, exist_ok=True)
    
    # 初始化计数器
    active_counts = defaultdict(int)
    social_counts = defaultdict(int)
    helpful_counts = defaultdict(int)
    tuple_counts = defaultdict(int)
    
    # 读取所有CSV文件
    data_dir = './data/grouped_data_csv'
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(data_dir, filename)
            df = pd.read_csv(file_path)
            
            # 处理other_desire_estimated列
            for value in df['other_desire_estimated']:
                if pd.isna(value) or value == ',,':
                    continue
                    
                # 分割值
                values = value.split(',')
                if len(values) != 3:
                    continue
                    
                active, social, helpful = values
                
                # 更新计数器
                active_counts[active] += 1
                social_counts[social] += 1
                helpful_counts[helpful] += 1
                tuple_counts[(active, social, helpful)] += 1
    
    # 创建Excel写入器
    excel_writer = pd.ExcelWriter(os.path.join(result_dir, 'desire_analysis.xlsx'), engine='openpyxl')
    
    # 创建各维度的DataFrame并排序
    # Active维度
    df_active = pd.DataFrame({
        'Value': list(active_counts.keys()),
        'Count': list(active_counts.values())
    })
    df_active = df_active.sort_values('Value')
    df_active.to_excel(excel_writer, sheet_name='Active Distribution', index=False)
    
    # Social维度
    df_social = pd.DataFrame({
        'Value': list(social_counts.keys()),
        'Count': list(social_counts.values())
    })
    df_social = df_social.sort_values('Value')
    df_social.to_excel(excel_writer, sheet_name='Social Distribution', index=False)
    
    # Helpful维度
    df_helpful = pd.DataFrame({
        'Value': list(helpful_counts.keys()),
        'Count': list(helpful_counts.values())
    })
    df_helpful = df_helpful.sort_values('Value')
    df_helpful.to_excel(excel_writer, sheet_name='Helpful Distribution', index=False)
    
    # 创建组合统计的DataFrame并排序
    results = []
    for (active, social, helpful), count in tuple_counts.items():
        results.append({
            'Active': active,
            'Social': social,
            'Helpful': helpful,
            'Count': count
        })
    
    df_combined = pd.DataFrame(results)
    # 按照Active, Social, Helpful的优先级排序
    df_combined = df_combined.sort_values(['Active', 'Social', 'Helpful'])
    df_combined.to_excel(excel_writer, sheet_name='Combined Distribution', index=False)
    
    # 保存Excel文件
    excel_writer.close()
    
    # 绘制各维度柱状图
    plt.figure(figsize=(15, 10))
    
    plt.subplot(3, 1, 1)
    sns.barplot(x='Value', y='Count', data=df_active)
    plt.title('Active Desire Distribution')
    plt.xticks(rotation=45)
    
    plt.subplot(3, 1, 2)
    sns.barplot(x='Value', y='Count', data=df_social)
    plt.title('Social Desire Distribution')
    plt.xticks(rotation=45)
    
    plt.subplot(3, 1, 3)
    sns.barplot(x='Value', y='Count', data=df_helpful)
    plt.title('Helpful Desire Distribution')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(result_dir, 'desire_distribution_bar.png'))
    plt.close()
    
    # 绘制整体分布柱状图
    plt.figure(figsize=(20, 8))
    # 创建组合标签
    df_combined['Combination'] = df_combined.apply(lambda x: f"({x['Active']}, {x['Social']}, {x['Helpful']})", axis=1)
    sns.barplot(x='Combination', y='Count', data=df_combined)
    plt.title('Combined Desire Distribution')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(result_dir, 'combined_distribution_bar.png'))
    plt.close()
    
    # 绘制饼图
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.pie(df_active['Count'], labels=df_active['Value'], autopct='%1.1f%%')
    plt.title('Active Desire Distribution')
    
    plt.subplot(1, 3, 2)
    plt.pie(df_social['Count'], labels=df_social['Value'], autopct='%1.1f%%')
    plt.title('Social Desire Distribution')
    
    plt.subplot(1, 3, 3)
    plt.pie(df_helpful['Count'], labels=df_helpful['Value'], autopct='%1.1f%%')
    plt.title('Helpful Desire Distribution')
    
    plt.tight_layout()
    plt.savefig(os.path.join(result_dir, 'desire_distribution_pie.png'))
    plt.close()
    
    # 打印统计信息
    print("分析完成！结果已保存到", result_dir)
    print("\n各维度统计：")
    print("\nActive维度：")
    for value, count in active_counts.items():
        print(f"{value}: {count}")
    print("\nSocial维度：")
    for value, count in social_counts.items():
        print(f"{value}: {count}")
    print("\nHelpful维度：")
    for value, count in helpful_counts.items():
        print(f"{value}: {count}")
    print("\n组合统计（前10个最常见的组合）：")
    sorted_tuples = sorted(tuple_counts.items(), key=lambda x: x[1], reverse=True)
    for (active, social, helpful), count in sorted_tuples[:10]:
        print(f"({active}, {social}, {helpful}): {count}")

if __name__ == "__main__":
    analyze_other_desire_data()

