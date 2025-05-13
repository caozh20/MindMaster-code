import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 设置样式
plt.style.use('ggplot')
plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文显示
plt.rcParams['axes.unicode_minus'] = False    # 负号显示

models = ['Claude', 'DeepSeek-R1', 'Gemini', 'gpt-4o', 'Llama3', 'Qwen3-8B', 'Random']

# 存储所有模型的数据
combined_data = []

for model in models:
    # 读取CSV文件
    df = pd.read_csv(f'./experiment_codes/llms/analysis/{model}/intent_analysis/regular_most_possible_intention_intent_frequency_table.csv')
    
    # 转换百分比为数值（假设原始格式是字符串"XX%"）
    if df['Count'].dtype == object:
        df['Count'] = df['Count'].str.rstrip('%').astype(float)
    
    # 添加模型名称列
    df['Model'] = model
    
    # 添加到总数据
    combined_data.append(df.head(10))

# 合并所有数据
final_df = pd.concat(combined_data)
print(final_df)

# 绘制柱状图
plt.figure(figsize=(14, 8))

# 使用seaborn绘制分组柱状图
sns.barplot(
    x='Intent',       # x轴为意图类型
    y='Count',   # y轴为百分比
    hue='Model',      # 按模型分组
    data=final_df,
    palette='tab20'   # 使用丰富的颜色方案
)

plt.title('各模型在不同意图上的分布对比', fontsize=16)
plt.xlabel('意图类型', fontsize=12)
plt.ylabel('占比 (%)', fontsize=12)
plt.xticks(rotation=45, ha='right')  # 旋转x轴标签

# 调整图例位置
plt.legend(
    title='模型',
    bbox_to_anchor=(1.05, 1),
    loc='upper left',
    borderaxespad=0
)

plt.tight_layout()
plt.show()