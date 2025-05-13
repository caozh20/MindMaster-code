import pandas as pd
import re
import matplotlib.pyplot as plt
from collections import Counter
import os
import ast  # 用于安全地将字符串转换为Python对象
import numpy as np
import seaborn as sns
from collections import defaultdict

SCENARIO_NAME_TO_INTENT = {
    'chimpanzee': '1_open_3', 
    'container': '1_get_3', 
    'cuptotable': '1_put_onto_4_3', 
    'multipointing': '1_get_3', 
    'play_game': '1_play_with_2_3', 
}

def plot_distribution_bar_chart(item_counts, top_n=20, show_all=False, save_path=None, item_type='Item'):
    """
    绘制分布柱状图
    
    参数:
    item_counts: 统计项目频次的字典或Counter对象
    top_n: 显示频次最高的前N项
    show_all: 是否显示所有项目
    save_path: 保存图表的路径，如果为None则只显示不保存
    item_type: 项目类型名称，用于图表标题和标签
    
    返回:
    生成的图表对象
    """
    # 转换为pandas DataFrame便于处理
    df = pd.DataFrame(list(item_counts.items()), columns=[item_type, 'Count'])
    df = df.sort_values('Count', ascending=False)
    
    # 计算百分比
    total = df['Count'].sum()
    df['Percentage'] = df['Count'] / total * 100
    
    # 确定要显示的项目数
    if show_all:
        display_df = df
    else:
        display_df = df.head(top_n)
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 绘制柱状图
    bars = plt.bar(display_df[item_type], display_df['Count'])
    
    # 在柱状图上添加计数和百分比标签
    for i, bar in enumerate(bars):
        count = display_df.iloc[i]['Count']
        percentage = display_df.iloc[i]['Percentage']
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f'{count} ({percentage:.1f}%)',
            ha='center', va='bottom',
            rotation=45 if len(display_df) > 10 else 0
        )
    
    # 设置图表标题和标签
    plt.title(f'{item_type} 频率分布 (Top {len(display_df)})')
    plt.xlabel(item_type)
    plt.ylabel('频次')
    
    # 设置x轴标签
    plt.xticks(rotation=45, ha='right')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"柱状图已保存至: {save_path}")
    
    # 显示统计信息
    total_items = len(item_counts)
    print(f"\n{item_type}分布统计:")
    print(f"总{item_type}数量: {total}")
    print(f"不同{item_type}类型数量: {total_items}")
    print(f"显示的{item_type}类型数量: {len(display_df)}")
    
    # 返回图表对象
    return plt.gcf()

def plot_distribution_pie_chart(item_counts, top_n=10, save_path=None, item_type='Item'):
    """
    绘制分布饼图
    
    参数:
    item_counts: 统计项目频次的字典或Counter对象
    top_n: 显示频次最高的前N项，其他项合并为"其他"
    save_path: 保存图表的路径，如果为None则只显示不保存
    item_type: 项目类型名称，用于图表标题和标签
    
    返回:
    生成的图表对象
    """
    # 转换为pandas DataFrame便于处理
    df = pd.DataFrame(list(item_counts.items()), columns=[item_type, 'Count'])
    df = df.sort_values('Count', ascending=False)
    
    # 准备饼图数据：将top_n之后的项目归类为"其他"
    if len(df) > top_n:
        top_items = df.head(top_n)
        others_count = df.iloc[top_n:]['Count'].sum()
        
        # 创建新的DataFrame
        pie_df = pd.concat([
            top_items,
            pd.DataFrame([['Others', others_count]], columns=top_items.columns)
        ])
    else:
        pie_df = df
    
    # 计算百分比
    total = pie_df['Count'].sum()
    pie_df['Percentage'] = pie_df['Count'] / total * 100
    
    # 创建图表
    plt.figure(figsize=(10, 8))
    
    # 绘制饼图
    explode = [0.1 if i == 0 else 0 for i in range(len(pie_df))]  # 突出显示最大的项
    plt.pie(
        pie_df['Count'],
        explode=explode,
        labels=None,  # 不在饼图上直接显示标签，使用图例
        autopct='%1.1f%%',
        startangle=90,
        shadow=True
    )
    
    # 添加图例
    labels = [
        f"{row[item_type]}: {row['Count']} ({row['Percentage']:.1f}%)"
        for _, row in pie_df.iterrows()
    ]
    plt.legend(
        labels,
        title=f"{item_type} 分布",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1)
    )
    
    # 设置图表标题
    plt.title(f'{item_type} 频率分布饼图 (Top {min(top_n, len(df))})')
    
    # 保持饼图是圆形的
    plt.axis('equal')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"饼图已保存至: {save_path}")
    
    # 返回图表对象
    return plt.gcf()

def generate_distribution_table(item_counts, save_path=None, save_format='csv', item_column_name='Item', add_mapping=False, mapping_function=None, mapping_column_name=None):
    """
    生成分布表格
    
    参数:
    item_counts: 统计项目频次的字典或Counter对象
    save_path: 保存表格的路径，如果为None则只显示不保存
    save_format: 保存格式，可以是'csv', 'excel', 或'both'
    item_column_name: 项目列名称
    add_mapping: 是否添加映射列
    mapping_function: 映射函数，输入项目名称，返回映射结果
    mapping_column_name: 映射列名称
    
    返回:
    生成的DataFrame对象
    """
    # 转换为pandas DataFrame便于处理
    df = pd.DataFrame(list(item_counts.items()), columns=[item_column_name, 'Count'])
    df = df.sort_values('Count', ascending=False)
    
    # 计算百分比
    total = df['Count'].sum()
    df['Percentage'] = df['Count'] / total * 100
    
    # 计算累计百分比
    df['Cumulative Percentage'] = df['Percentage'].cumsum()
    
    # 如果需要添加映射列
    if add_mapping and mapping_function and mapping_column_name:
        df[mapping_column_name] = df[item_column_name].apply(mapping_function)
    
    # 显示表格
    print(f"\n{item_column_name}频率分布表:")
    print(df)
    
    # 保存表格
    if save_path:
        # 创建不同格式的保存路径
        if save_format in ['csv', 'both']:
            csv_path = f"{save_path}.csv"
            df.to_csv(csv_path, index=False)
            print(f"CSV表格已保存至: {csv_path}")
        
        if save_format in ['excel', 'both']:
            excel_path = f"{save_path}.xlsx"
            df.to_excel(excel_path, index=False)
            print(f"Excel表格已保存至: {excel_path}")
    
    return df

def generate_comprehensive_excel_report(item_counts, stats, save_path, item_name='Item', sheet_prefix='', add_mapping=False, mapping_function=None, mapping_column_name=None):
    """
    生成综合Excel报告
    
    参数:
    item_counts: 统计项目频次的字典或Counter对象
    stats: 处理统计信息字典
    save_path: 保存报告的路径
    item_name: 项目类型名称
    sheet_prefix: 工作表前缀
    add_mapping: 是否添加映射信息
    mapping_function: 映射函数，输入项目名称，返回映射结果
    mapping_column_name: 映射列名称
    
    返回:
    None
    """
    try:
        # 创建ExcelWriter对象
        with pd.ExcelWriter(save_path, engine='xlsxwriter') as writer:
            # 1. 频率分布表
            df = pd.DataFrame(list(item_counts.items()), columns=[item_name, 'Count'])
            df = df.sort_values('Count', ascending=False)
            
            # 计算百分比
            total = df['Count'].sum()
            df['Percentage'] = df['Count'] / total * 100
            df['Cumulative Percentage'] = df['Percentage'].cumsum()
            
            # 如果需要添加映射列
            if add_mapping and mapping_function and mapping_column_name:
                df[mapping_column_name] = df[item_name].apply(mapping_function)
            
            # 保存到第一个工作表
            df.to_excel(writer, sheet_name=f'{sheet_prefix}{item_name} Distribution', index=False)
            
            # 2. 处理统计信息表
            if stats:
                # 将嵌套字典扁平化
                flat_stats = {}
                
                def flatten_dict(d, prefix=''):
                    for key, value in d.items():
                        if isinstance(value, dict):
                            flatten_dict(value, prefix + key + '_')
                        else:
                            flat_stats[prefix + key] = value
                
                flatten_dict(stats)
                
                # 创建统计信息表
                stats_df = pd.DataFrame({
                    'Statistic': list(flat_stats.keys()),
                    'Value': list(flat_stats.values())
                })
                
                # 保存到第二个工作表
                stats_df.to_excel(writer, sheet_name=f'{sheet_prefix}Processing Stats', index=False)
            
            # 3. 将前10个项目的频率数据保存为饼图
            if len(item_counts) > 0:
                # 准备前10个项目的数据
                top_df = df.head(10)
                
                # 获取工作簿和工作表对象
                workbook = writer.book
                worksheet = writer.sheets[f'{sheet_prefix}{item_name} Distribution']
                
                # 创建饼图
                chart = workbook.add_chart({'type': 'pie'})
                
                # 设置数据范围
                end_row = min(11, len(df) + 1)  # 考虑标题行和实际数据条数
                chart.add_series({
                    'name': f'Top {min(10, len(df))} {item_name}',
                    'categories': [f'{sheet_prefix}{item_name} Distribution', 1, 0, end_row, 0],
                    'values': [f'{sheet_prefix}{item_name} Distribution', 1, 1, end_row, 1],
                    'data_labels': {'percentage': True}
                })
                
                # 设置图表标题
                chart.set_title({'name': f'Top {min(10, len(df))} {item_name} Distribution'})
                
                # 插入图表
                worksheet.insert_chart('H2', chart, {'x_offset': 25, 'y_offset': 10, 'x_scale': 1.5, 'y_scale': 1.5})
        
        print(f"综合Excel报告已保存至: {save_path}")
        
    except Exception as e:
        print(f"生成Excel报告时出错: {e}")


def examine_csv_file(csv_file_path):
    """
    检查CSV文件的基本信息
    
    参数:
    csv_file_path: CSV文件路径
    """
    try:
        df = pd.read_csv(csv_file_path)
        print(f"CSV文件路径: {csv_file_path}")
        print(f"CSV文件总行数: {len(df)}")
        print(f"CSV文件列名: {list(df.columns)}")
        print(f"CSV文件前5行数据预览:")
        print(df.head())
        print(f"数据类型信息:")
        print(df.dtypes)
        print(f"缺失值统计:")
        print(df.isnull().sum())
        return df
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        return None


def extract_intent_from_string(intent_str):
    """
    从意图字符串中提取意图部分
    
    参数:
    intent_str: 意图字符串
    
    返回:
    提取的意图
    """
    # 处理NA作为一种意图
    if intent_str == 'NA' or intent_str == 'Na' or intent_str.lower() == 'na':
        return 'NA'
    
    # 提取Agent_id-Intent-xxx中的Intent部分的正则表达式
    intent_pattern = re.compile(r'Agent_\d+-([A-Za-z]+)-')
    
    # 额外添加一个模式匹配形如"Agent_2-Na"的情况
    na_pattern = re.compile(r'Agent_\d+-([A-Za-z]+)$')
    
    # 首先尝试标准模式
    match = intent_pattern.search(str(intent_str))
    if match:
        return match.group(1)
    
    # 如果标准模式不匹配，尝试匹配"Agent_数字-Na"格式
    na_match = na_pattern.search(str(intent_str))
    if na_match:
        return na_match.group(1)
    
    # 如果两种模式都不匹配，返回None
    return None

def parse_intent_row(row_value):
    """
    解析包含意图的数据行
    
    参数:
    row_value: 数据行，可能是字符串或列表
    
    返回:
    解析出的意图列表和处理信息
    """
    intents = []
    unmatched = []
    intent_count = 0
    processed_count = 0
    
    try:
        # 尝试将字符串转换为列表
        if isinstance(row_value, str):
            if row_value.startswith('[') and row_value.endswith(']'):
                # 使用ast.literal_eval安全地解析字符串为列表
                intent_list = ast.literal_eval(row_value)
            else:
                # 单个意图字符串，放入列表中
                intent_list = [row_value]
        else:
            # 如果已经是列表类型，直接使用
            intent_list = row_value if isinstance(row_value, list) else [row_value]
        
        # 处理列表中的每个意图字符串
        for intent_str in intent_list:
            intent_count += 1
            
            extracted_intent = extract_intent_from_string(intent_str)
            if extracted_intent:
                intents.append(extracted_intent)
                processed_count += 1
            else:
                unmatched.append(intent_str)
        
        return intents, unmatched, intent_count, processed_count, None
    
    except Exception as e:
        return [], [row_value], 0, 0, str(e)

def extract_intents_from_csv(csv_file_path, intent_column='intent', verbose=True):
    """
    从CSV文件中提取意图数据，这是意图处理的通用基础函数
    
    参数:
    csv_file_path: CSV文件的路径
    intent_column: 意图列的名称，可以是'intent'或'infer_intent'
    verbose: 是否打印详细处理信息
    
    返回:
    all_intents: 提取的所有意图列表
    stats: 处理统计信息字典
    df: 加载的DataFrame对象，可供进一步处理
    """
    # 统计信息初始化
    stats = {
        'total_rows': 0,
        'non_null_rows': 0,
        'null_rows': 0,
        'total_intents': 0,
        'processed_intents': 0,
        'unmatched_patterns': 0,
        'unmatched_examples': [],
        'intent_column_used': intent_column
    }
    
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_file_path)
        if verbose:
            print(f"成功读取CSV文件: {csv_file_path}")
            print(f"CSV文件总行数: {len(df)}")
            print(f"CSV文件列名: {list(df.columns)}")
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        return None, None, None
    
    # 检查是否存在指定的意图列
    if intent_column not in df.columns:
        print(f"警告: CSV文件中没有'{intent_column}'列。请检查列名。")
        if intent_column == 'intent' and 'intentions_true' in df.columns:
            print("找到'intentions_true'列，将使用它替代'intent'列")
            intent_column = 'intentions_true'
        else:
            print("无法找到意图数据列。可用的列有:", list(df.columns))
            return None, None, None
    
    # 更新统计信息
    stats['total_rows'] = len(df)
    stats['non_null_rows'] = df[intent_column].notna().sum()
    stats['null_rows'] = df[intent_column].isna().sum()
    
    all_intents = []
    all_unmatched = []
    
    # 处理每一行
    for row_value in df[intent_column].dropna():
        intents, unmatched, intent_count, processed_count, error = parse_intent_row(row_value)
        
        all_intents.extend(intents)
        all_unmatched.extend(unmatched)
        
        stats['total_intents'] += intent_count
        stats['processed_intents'] += processed_count
        stats['unmatched_patterns'] += len(unmatched)
        
        # 保存一些未匹配的例子用于调试
        for uitem in unmatched:
            if len(stats['unmatched_examples']) < 10:
                if error:
                    stats['unmatched_examples'].append(f"{uitem} (错误: {error})")
                else:
                    stats['unmatched_examples'].append(uitem)
    
    if verbose:
        print("\n数据处理统计:")
        print(f"总行数: {stats['total_rows']}")
        print(f"非空意图行数: {stats['non_null_rows']}")
        print(f"空意图行数: {stats['null_rows']}")
        print(f"总意图数量: {stats['total_intents']}")
        print(f"成功处理的意图数量: {stats['processed_intents']}")
        print(f"不匹配意图模式的数量: {stats['unmatched_patterns']}")
        print(f"使用的意图列: {stats['intent_column_used']}")
        
        if stats['unmatched_patterns'] > 0:
            print("\n未匹配意图模式示例:")
            for i, example in enumerate(stats['unmatched_examples']):
                print(f"  {i+1}. {example}")
        
        # 检查处理完整性
        if stats['total_intents'] > 0:
            coverage = (stats['processed_intents'] / stats['total_intents']) * 100
            print(f"\n意图处理覆盖率: {coverage:.2f}%")
            
            if stats['processed_intents'] + stats['unmatched_patterns'] == stats['total_intents']:
                print("✅ 所有意图已处理（成功或失败）")
            else:
                print(f"⚠️ 意图处理不完整: 总意图 {stats['total_intents']}, 已处理 {stats['processed_intents']}, 未匹配 {stats['unmatched_patterns']}")
    
    return all_intents, stats, df

def analyze_intent_frequency(csv_file_path, intent_column='intent', verbose=True):
    """
    分析CSV文件中的意图(intent)频次
    
    参数:
    csv_file_path: CSV文件的路径
    intent_column: 意图列的名称，可以是'intent'或'infer_intent'
    verbose: 是否打印详细处理信息
    
    返回:
    统计结果的Counter对象，处理统计信息字典
    """
    # 使用通用函数提取意图
    all_intents, stats, _ = extract_intents_from_csv(csv_file_path, intent_column, verbose)
    
    if all_intents is None:
        return None, None
    
    # 统计频次
    intent_counts = Counter(all_intents)
    
    # 更新统计信息，添加不同意图类型的数量
    if verbose:
        print(f"不同意图类型数量: {len(intent_counts)}")
    
    return intent_counts, stats

def simplify_intent(intent):
    """
    将意图字符串简化为标准形式
    
    参数:
    intent: 原始意图字符串，格式为Agent_2-Observe-World
    
    返回:
    简化后的意图字符串
    """
    # 处理无效输入
    if intent is None:
        return "null_input"
    
    if not isinstance(intent, str):
        # 尝试转换为字符串
        try:
            intent = str(intent)
        except:
            return "null_input"
    
    # 处理空字符串或纯空格字符串
    if not intent.strip():
        return "empty_string"
    
    # 处理NA作为特殊意图
    if intent.lower() == "na":
        return "NA"
    
    # 按照新规则处理意图字符串
    # 格式为Agent_2-Observe-World
    parts = intent.split('-')
    
    # 检查是否有足够的部分
    if len(parts) < 2:
        return "unknown"

    # 获取第一个-和第二个-之间的内容
    first_part = parts[1]
    
    # 检查第一个部分是否包含na
    if 'na' in first_part.lower():
        return "NA"

    # 检查是否有足够的部分
    if len(parts) < 3:
    return "unknown"
    
    
    
    # 获取第二个-和第三个-之间的内容
    second_part = parts[2]
    
    # 检查第二个部分是否包含_、na或world
    if '_' in second_part or 'na' in second_part.lower() or 'world' in second_part.lower():
        # 如果有_、na或world，则只保留第一个部分
        return first_part
    else:
        # 如果没有_、na或world，则将两个部分拼在一起
        return first_part + second_part

def simplify_intent_list(intents, verbose=True):
    """
    将意图列表中的所有意图简化为标准形式
    
    参数:
    intents: 原始意图列表
    verbose: 是否打印详细的简化过程信息
    
    返回:
    simplified_intents: 简化后的意图列表
    stats: 简化过程的统计信息
    """
    simplified_intents = []
    stats = {
        "total_intents": len(intents),
        "null_inputs": 0,
        "empty_strings": 0,
        "unknown_intents": 0,
        "simplified_intents": {}
    }
    
    # 遍历所有意图并简化
    for intent in intents:
        simplified = simplify_intent(intent)
        simplified_intents.append(simplified)
        
        # 更新统计信息
        if simplified == "null_input":
            stats["null_inputs"] += 1
        elif simplified == "empty_string":
            stats["empty_strings"] += 1
        elif simplified == "unknown":
            stats["unknown_intents"] += 1
        
        # 统计简化后各类意图的数量
        if simplified not in stats["simplified_intents"]:
            stats["simplified_intents"][simplified] = 0
        stats["simplified_intents"][simplified] += 1
    
    # 打印简化过程信息
    if verbose:
        print(f"意图简化统计:")
        print(f"总意图数: {stats['total_intents']}")
        print(f"无效输入: {stats['null_inputs']}")
        print(f"空字符串: {stats['empty_strings']}")
        print(f"未知意图: {stats['unknown_intents']}")
        print("各类简化意图数量:")
        for intent, count in stats["simplified_intents"].items():
            print(f"  {intent}: {count}")
    
    return simplified_intents, stats

def analyze_simplified_intent_frequency(csv_file_path, intent_column='intent', verbose=True):
    """
    分析简化后意图的频率统计
    
    参数:
    csv_file_path: CSV文件路径
    intent_column: 意图列的名称，可以是'intent'或'infer_intent'
    verbose: 是否打印详细处理信息
    
    返回:
    simplified_intent_counts: 简化后意图的频次字典
    stats: 统计信息字典
    """
    # 先使用常规意图分析获取所有原始意图
    intent_counts, stats = analyze_intent_frequency(csv_file_path, intent_column, verbose=verbose)
    
    if intent_counts is None:
        return None, None
    
    # 通过所有意图列表创建一个所有意图的展平列表
    all_intents = []
    for intent, count in intent_counts.items():
        all_intents.extend([intent] * count)
    
    # 简化意图列表
    simplified_intents, simplify_stats = simplify_intent_list(all_intents, verbose)
    
    # 统计简化后意图的频次
    simplified_intent_counts = Counter(simplified_intents)
    
    # 更新统计信息
    stats.update({
        "simplified_intent_stats": simplify_stats,
        "unique_simplified_intents": len(simplified_intent_counts)
    })
    
    # 打印简化后意图的频次统计
    if verbose:
        print(f"\n简化后意图频次统计:")
        print(f"共有{len(simplified_intent_counts)}种不同的简化意图")
        for intent, count in sorted(simplified_intent_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{intent}: {count}次 ({count/len(simplified_intents)*100:.2f}%)")
    
    return simplified_intent_counts, stats

def main_intent_analysis(csv_file_path, output_dir=None, verbose=True, intent_type='regular', intent_column='intent'):
    """
    意图分析的主函数，集成了所有意图分析相关功能
    
    参数:
    csv_file_path: CSV文件路径
    output_dir: 输出目录，如果为None则不保存结果
    verbose: 是否显示详细信息
    intent_type: 意图类型，'regular'表示常规意图，'simplified'表示简化意图
    intent_column: 意图列的名称，可以是'intent'或'infer_intent'
    
    返回:
    分析结果字典
    """
    results = {}
    
    # 检查CSV文件并显示基本信息
    if verbose:
        print("="*50)
        print("开始检查CSV文件...")
        examine_csv_file(csv_file_path)
    
    # 分析意图频次
    print("="*50)
    if intent_type == 'simplified':
        print("开始分析简化意图频次...")
        intent_counts, stats = analyze_simplified_intent_frequency(csv_file_path, intent_column, verbose)
        item_type = 'Simplified Intent'
    else:
        print("开始分析意图频次...")
        intent_counts, stats = analyze_intent_frequency(csv_file_path, intent_column, verbose)
        item_type = 'Intent'
    
    if intent_counts is None:
        print("分析失败，无法继续执行后续分析。")
        return None
    
    results['intent_counts'] = intent_counts
    results['stats'] = stats
    
    # 可视化分析结果 - 柱状图
    if verbose:
        print("="*50)
        print(f"生成{item_type}频次柱状图...")
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        # 在文件名中添加意图列信息
        bar_chart_path = os.path.join(output_dir, f'{intent_type}_{intent_column}_intent_bar_chart.png')
    else:
        bar_chart_path = None
    
    plot_distribution_bar_chart(
        intent_counts, 
        top_n=20, 
        show_all=False, 
        save_path=bar_chart_path, 
        item_type=item_type
    )
    
    # 可视化分析结果 - 饼图
    if verbose:
        print("="*50)
        print(f"生成{item_type}频次饼图...")
    
    if output_dir:
        # 在文件名中添加意图列信息
        pie_chart_path = os.path.join(output_dir, f'{intent_type}_{intent_column}_intent_pie_chart.png')
    else:
        pie_chart_path = None
    
    plot_distribution_pie_chart(
        intent_counts, 
        top_n=10, 
        save_path=pie_chart_path, 
        item_type=item_type
    )
    
    # 生成表格
    if verbose:
        print("="*50)
        print(f"生成{item_type}频次表格...")
    
    if output_dir:
        # 在文件名中添加意图列信息
        table_path = os.path.join(output_dir, f'{intent_type}_{intent_column}_intent_frequency_table')
    else:
        table_path = None
    
    # 判断是否需要添加映射函数
    add_mapping = False
    mapping_function = None
    if intent_type == 'simplified':
        # 添加一个映射函数，显示哪些原始意图映射到了这个简化意图
        def get_original_intents(simplified_intent):
            return [intent for intent in SCENARIO_NAME_TO_INTENT.values() if simplify_intent(intent) == simplified_intent]
        add_mapping = True
        mapping_function = get_original_intents
    
    generate_distribution_table(
        intent_counts, 
        save_path=table_path, 
        save_format='both',
        item_column_name=item_type,
        add_mapping=add_mapping,
        mapping_function=mapping_function,
        mapping_column_name='Original Intents'
    )
    
    # 生成综合Excel报告
    if output_dir:
        if verbose:
            print("="*50)
            print("生成综合Excel报告...")
        
        # 在文件名中添加意图列信息
        excel_path = os.path.join(output_dir, f'{intent_type}_{intent_column}_intent_analysis_report.xlsx')
        generate_comprehensive_excel_report(
            intent_counts, 
            stats, 
            excel_path,
            item_name=item_type,
            sheet_prefix='',
            add_mapping=add_mapping,
            mapping_function=mapping_function,
            mapping_column_name='Original Intents'
        )
    
    if verbose:
        print("="*50)
        print(f"{item_type}分析完成！")
        if output_dir:
            print(f"所有结果已保存到目录: {output_dir}")
    
    return results

def analyze_intent_transitions(csv_file_path='./data/dataset_intent_pred_relation_view_segment_False.csv', verbose=True, simplified=False, save_dir=None, intent_column='intent'):
    """
    分析意图转换模式并生成热图
    
    参数:
    csv_file_path: 包含意图数据的CSV文件路径
    verbose: 是否打印详细处理信息
    simplified: 是否使用简化的意图字符串
    save_dir: 保存结果的目录，默认为None（使用intent_analysis_results目录）
    intent_column: 意图列的名称，可以是'intent'或'infer_intent'
    
    返回:
    transition_matrix: 意图转换矩阵（pandas DataFrame）
    stats: 处理统计信息字典
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import os
    from collections import defaultdict
    
    # 如果未指定保存目录，使用默认目录
    if save_dir is None:
        save_dir = 'intent_analysis_results'
    
    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    # 检查文件是否存在
    if not os.path.exists(csv_file_path):
        print(f"错误: 文件不存在: {csv_file_path}")
        return None, None
    
    # 统计信息初始化
    stats = {
        'total_rows': 0,
        'rows_with_intents': 0,
        'total_transitions': 0,
        'unique_intents': 0,
        'error_rows': 0,
        'error_examples': [],
        'intent_column_used': intent_column
    }
    
    # 使用字典记录意图转换
    transitions = defaultdict(int)
    all_intents = set()
    
    try:
        # 读取CSV文件
        print(f"正在读取文件: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # 检查是否包含指定的意图列
        if intent_column not in df.columns:
            print(f"错误: CSV文件中不包含'{intent_column}'列")
            return None, None
        
        # 获取总行数
        stats['total_rows'] = len(df)
        
        # 处理每一行
        for index, row in df.iterrows():
            try:
                if pd.notna(row[intent_column]):
                    intent_value = str(row[intent_column])
                    
                    # 将意图拆分成列表（假设以某种方式分隔，例如逗号或空格）
                    # 这里需要根据实际数据格式调整分隔方式
                    if ',' in intent_value:
                        intent_list = [i.strip() for i in intent_value.split(',')]
                    elif ' ' in intent_value:
                        intent_list = [i.strip() for i in intent_value.split()]
                    else:
                        # 如果没有明显的分隔符，可能是单个意图，无法分析转换
                        continue
                    
                    # 如果解析成功并且有至少两个意图，才能分析转换
                    if len(intent_list) >= 2:
                        stats['rows_with_intents'] += 1
                        
                        # 处理每个意图
                        processed_intents = []
                        for intent in intent_list:
                            # 如果需要简化意图字符串
                            if simplified:
                                intent = simplify_intent(intent)
                            
                            processed_intents.append(intent)
                            all_intents.add(intent)
                        
                        # 分析转换 (第i个到第i+1个)
                        for i in range(len(processed_intents) - 1):
                            from_intent = processed_intents[i]
                            to_intent = processed_intents[i + 1]
                            transitions[(from_intent, to_intent)] += 1
                            stats['total_transitions'] += 1
            
            except Exception as e:
                stats['error_rows'] += 1
                if len(stats['error_examples']) < 10:
                    stats['error_examples'].append(f"行 {index+1}: {e}")
                if verbose:
                    print(f"处理第 {index+1} 行时出错: {e}")
    
    except Exception as e:
        print(f"读取或处理文件时出错: {e}")
        return None, None
    
    # 如果未找到有效的意图转换，返回None
    if not transitions:
        print("警告: 未找到有效的意图转换")
        return None, stats
    
    # 转换为有序的意图列表，以便构建矩阵
    unique_intents = sorted(list(all_intents))
    stats['unique_intents'] = len(unique_intents)
    
    # 创建转换矩阵（行是来源，列是目标）
    transition_matrix = pd.DataFrame(0, 
                                     index=unique_intents, 
                                     columns=unique_intents)
    
    # 填充转换矩阵
    for (from_intent, to_intent), count in transitions.items():
        transition_matrix.at[from_intent, to_intent] = count
    
    # 创建三列格式的转换数据（出发intent，变化intent，频率）
    transitions_data = []
    for from_intent in unique_intents:
        for to_intent in unique_intents:
            count = transition_matrix.at[from_intent, to_intent]
            transitions_data.append({
                'From Intent': from_intent,
                'To Intent': to_intent,
                'Frequency': count
            })
    
    # 创建DataFrame并保存为Excel
    transitions_df = pd.DataFrame(transitions_data)
    excel_filename = os.path.join(save_dir, f'{intent_column}_intent_transitions.xlsx')
    transitions_df.to_excel(excel_filename, index=False)
    print(f"意图转换数据已保存至: {excel_filename}")
    
    # 保存矩阵格式的Excel（保持原有格式）
    matrix_excel_filename = os.path.join(save_dir, f'{intent_column}_intent_transitions_matrix.xlsx')
    transition_matrix.to_excel(matrix_excel_filename)
    print(f"意图转换矩阵已保存至: {matrix_excel_filename}")
    
    # 计算转换概率（行正规化）
    row_sums = transition_matrix.sum(axis=1)
    # 避免除以零
    row_sums = row_sums.replace(0, 1)
    probability_matrix = transition_matrix.div(row_sums, axis=0)
    
    # 创建两个热图
    plt.figure(figsize=(15, 12))
    
    # 1. 转换频次热图
    plt.subplot(2, 1, 1)
    sns.heatmap(transition_matrix, annot=True, fmt='d', cmap='YlGnBu')
    plt.title(f'{intent_column}意图转换频次热图')
    plt.xlabel('目标意图')
    plt.ylabel('来源意图')
    
    # 2. 转换概率热图
    plt.subplot(2, 1, 2)
    sns.heatmap(probability_matrix, annot=True, fmt='.2f', cmap='YlGnBu')
    plt.title(f'{intent_column}意图转换概率热图 (行归一化)')
    plt.xlabel('目标意图')
    plt.ylabel('来源意图')
    
    plt.tight_layout()
    
    # 保存热图
    heatmap_filename = os.path.join(save_dir, f'{intent_column}_intent_transitions_heatmap.png')
    plt.savefig(heatmap_filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"意图转换热图已保存至: {heatmap_filename}")
    
    # 如果verbose模式，打印处理统计信息
    if verbose:
        print("\n意图转换处理统计:")
        print(f"总行数: {stats['total_rows']}")
        print(f"包含有效意图序列的行数: {stats['rows_with_intents']}")
        print(f"总转换次数: {stats['total_transitions']}")
        print(f"唯一意图数量: {stats['unique_intents']}")
        print(f"处理出错的行数: {stats['error_rows']}")
        print(f"使用的意图列: {stats['intent_column_used']}")
        
        if stats['error_rows'] > 0:
            print("\n处理出错的行示例:")
            for i, example in enumerate(stats['error_examples']):
                print(f"  {i+1}. {example}")
    
    # 保存详细统计信息到Excel
    excel_stats_filename = os.path.join(save_dir, f'{intent_column}_intent_transitions_stats.xlsx')
    with pd.ExcelWriter(excel_stats_filename, engine='xlsxwriter') as writer:
        # 1. 转换频次矩阵
        transition_matrix.to_excel(writer, sheet_name='转换频次矩阵')
        
        # 2. 转换概率矩阵
        probability_matrix.to_excel(writer, sheet_name='转换概率矩阵')
        
        # 3. 三列格式的转换数据
        transitions_df.to_excel(writer, sheet_name='转换数据', index=False)
        
        # 4. 处理统计信息
        stats_df = pd.DataFrame({
            '指标': [
                '总行数',
                '包含有效意图序列的行数',
                '总转换次数',
                '唯一意图数量',
                '处理出错的行数',
                '使用的意图列'
            ],
            '值': [
                stats['total_rows'],
                stats['rows_with_intents'],
                stats['total_transitions'],
                stats['unique_intents'],
                stats['error_rows'],
                stats['intent_column_used']
            ]
        })
        stats_df.to_excel(writer, sheet_name='处理统计', index=False)
        
        # 5. 处理出错的行示例
        if stats['error_examples']:
            failed_df = pd.DataFrame({
                '错误信息': stats['error_examples']
            })
            failed_df.to_excel(writer, sheet_name='处理出错的行', index=False)
    
    print(f"详细统计信息已保存至: {excel_stats_filename}")
    
    return transition_matrix, stats

def analyze_simplified_intent_transitions(csv_file_path='./data/dataset_intent_pred_relation_view_segment_False.csv', verbose=True, save_dir=None, intent_column='intent'):
    """
    分析简化后的意图转换模式并生成热图
    
    参数:
    csv_file_path: 包含意图数据的CSV文件路径
    verbose: 是否打印详细处理信息
    save_dir: 保存结果的目录，默认为None（使用intent_analysis_results目录）
    intent_column: 意图列的名称，可以是'intent'或'infer_intent'
    
    返回:
    transition_matrix: 简化意图转换矩阵（pandas DataFrame）
    stats: 处理统计信息字典
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import os
    from collections import defaultdict
    
    # 如果未指定保存目录，使用默认目录
    if save_dir is None:
        save_dir = 'simplified_intent_transitions_analysis'
    
    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    # 检查文件是否存在
    if not os.path.exists(csv_file_path):
        print(f"错误: 文件不存在: {csv_file_path}")
        return None, None
    
    # 统计信息初始化
    stats = {
        'total_rows': 0,
        'rows_with_intents': 0,
        'total_transitions': 0,
        'unique_intents': 0,
        'error_rows': 0,
        'error_examples': [],
        'intent_column_used': intent_column,
        'unknown_intents': []  # 添加未知意图列表
    }
    
    # 使用字典记录意图转换
    transitions = defaultdict(int)
    all_intents = set()
    
    try:
        # 读取CSV文件
        print(f"正在读取文件: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # 检查是否包含指定的意图列
        if intent_column not in df.columns:
            print(f"错误: CSV文件中不包含'{intent_column}'列")
            return None, None
        
        # 获取总行数
        stats['total_rows'] = len(df)
        
        # 处理每一行
        for index, row in df.iterrows():
            try:
                if pd.notna(row[intent_column]):
                    intent_value = str(row[intent_column])
                    
                    # 将意图拆分成列表（假设以某种方式分隔，例如逗号或空格）
                    # 这里需要根据实际数据格式调整分隔方式
                    if ',' in intent_value:
                        intent_list = [i.strip() for i in intent_value.split(',')]
                    elif ' ' in intent_value:
                        intent_list = [i.strip() for i in intent_value.split()]
                    else:
                        # 如果没有明显的分隔符，可能是单个意图，无法分析转换
                        continue
                    
                    # 如果解析成功并且有至少两个意图，才能分析转换
                    if len(intent_list) >= 2:
                        stats['rows_with_intents'] += 1
                        
                        # 处理每个意图
                        processed_intents = []
                        for intent in intent_list:
                            # 简化意图字符串
                            simplified_intent = simplify_intent(intent)
                            processed_intents.append(simplified_intent)
                            all_intents.add(simplified_intent)
                            
                            # 记录未知意图
                            if simplified_intent == "unknown":
                                stats['unknown_intents'].append(intent)
                        
                        # 分析转换 (第i个到第i+1个)
                        for i in range(len(processed_intents) - 1):
                            from_intent = processed_intents[i]
                            to_intent = processed_intents[i + 1]
                            transitions[(from_intent, to_intent)] += 1
                            stats['total_transitions'] += 1
            
            except Exception as e:
                stats['error_rows'] += 1
                if len(stats['error_examples']) < 10:
                    stats['error_examples'].append(f"行 {index+1}: {e}")
                if verbose:
                    print(f"处理第 {index+1} 行时出错: {e}")
    
    except Exception as e:
        print(f"读取或处理文件时出错: {e}")
        return None, None
    
    # 如果未找到有效的意图转换，返回None
    if not transitions:
        print("警告: 未找到有效的意图转换")
        return None, stats
    
    # 转换为有序的意图列表，以便构建矩阵
    unique_intents = sorted(list(all_intents))
    stats['unique_intents'] = len(unique_intents)
    
    # 创建转换矩阵（行是来源，列是目标）
    transition_matrix = pd.DataFrame(0, 
                                     index=unique_intents, 
                                     columns=unique_intents)
    
    # 填充转换矩阵
    for (from_intent, to_intent), count in transitions.items():
        transition_matrix.at[from_intent, to_intent] = count
    
    # 创建三列格式的转换数据（出发intent，变化intent，频率）
    transitions_data = []
    for from_intent in unique_intents:
        for to_intent in unique_intents:
            count = transition_matrix.at[from_intent, to_intent]
            transitions_data.append({
                'From Intent': from_intent,
                'To Intent': to_intent,
                'Frequency': count
            })
    
    # 创建DataFrame并保存为Excel
    transitions_df = pd.DataFrame(transitions_data)
    excel_filename = os.path.join(save_dir, f'simplified_{intent_column}_intent_transitions.xlsx')
    transitions_df.to_excel(excel_filename, index=False)
    print(f"简化意图转换数据已保存至: {excel_filename}")
    
    # 保存矩阵格式的Excel（保持原有格式）
    matrix_excel_filename = os.path.join(save_dir, f'simplified_{intent_column}_intent_transitions_matrix.xlsx')
    transition_matrix.to_excel(matrix_excel_filename)
    print(f"简化意图转换矩阵已保存至: {matrix_excel_filename}")
    
    # 计算转换概率（行正规化）
    row_sums = transition_matrix.sum(axis=1)
    # 避免除以零
    row_sums = row_sums.replace(0, 1)
    probability_matrix = transition_matrix.div(row_sums, axis=0)
    
    # 创建两个热图
    plt.figure(figsize=(15, 12))
    
    # 1. 转换频次热图
    plt.subplot(2, 1, 1)
    sns.heatmap(transition_matrix, annot=True, fmt='d', cmap='YlGnBu')
    plt.title(f'简化{intent_column}意图转换频次热图')
    plt.xlabel('目标意图')
    plt.ylabel('来源意图')
    
    # 2. 转换概率热图
    plt.subplot(2, 1, 2)
    sns.heatmap(probability_matrix, annot=True, fmt='.2f', cmap='YlGnBu')
    plt.title(f'简化{intent_column}意图转换概率热图 (行归一化)')
    plt.xlabel('目标意图')
    plt.ylabel('来源意图')
    
    plt.tight_layout()
    
    # 保存热图
    heatmap_filename = os.path.join(save_dir, f'simplified_{intent_column}_intent_transitions_heatmap.png')
    plt.savefig(heatmap_filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"简化意图转换热图已保存至: {heatmap_filename}")
    
    # 如果verbose模式，打印处理统计信息
    if verbose:
        print("\n简化意图转换处理统计:")
        print(f"总行数: {stats['total_rows']}")
        print(f"包含有效意图序列的行数: {stats['rows_with_intents']}")
        print(f"总转换次数: {stats['total_transitions']}")
        print(f"唯一意图数量: {stats['unique_intents']}")
        print(f"处理出错的行数: {stats['error_rows']}")
        print(f"使用的意图列: {stats['intent_column_used']}")
        print(f"未知意图数量: {len(stats['unknown_intents'])}")
        
        if stats['error_rows'] > 0:
            print("\n处理出错的行示例:")
            for i, example in enumerate(stats['error_examples']):
                print(f"  {i+1}. {example}")
    
    # 保存详细统计信息到Excel
    excel_stats_filename = os.path.join(save_dir, f'simplified_{intent_column}_intent_transitions_stats.xlsx')
    with pd.ExcelWriter(excel_stats_filename, engine='xlsxwriter') as writer:
        # 1. 转换频次矩阵
        transition_matrix.to_excel(writer, sheet_name='转换频次矩阵')
        
        # 2. 转换概率矩阵
        probability_matrix.to_excel(writer, sheet_name='转换概率矩阵')
        
        # 3. 三列格式的转换数据
        transitions_df.to_excel(writer, sheet_name='转换数据', index=False)
        
        # 4. 处理统计信息
        stats_df = pd.DataFrame({
            '指标': [
                '总行数',
                '包含有效意图序列的行数',
                '总转换次数',
                '唯一意图数量',
                '处理出错的行数',
                '使用的意图列',
                '未知意图数量'
            ],
            '值': [
                stats['total_rows'],
                stats['rows_with_intents'],
                stats['total_transitions'],
                stats['unique_intents'],
                stats['error_rows'],
                stats['intent_column_used'],
                len(stats['unknown_intents'])
            ]
        })
        stats_df.to_excel(writer, sheet_name='处理统计', index=False)
        
        # 5. 处理出错的行示例
        if stats['error_examples']:
            failed_df = pd.DataFrame({
                '错误信息': stats['error_examples']
            })
            failed_df.to_excel(writer, sheet_name='处理出错的行', index=False)
        
        # 6. 未知意图列表
        if stats['unknown_intents']:
            unknown_df = pd.DataFrame({
                '原始意图': stats['unknown_intents']
            })
            unknown_df.to_excel(writer, sheet_name='未知意图', index=False)
    
    print(f"详细统计信息已保存至: {excel_stats_filename}")
    
    return transition_matrix, stats

def analyze_scenario_frequency(data_dir, verbose=True, map_to_intent=False):
    """
    分析场景频率
    
    参数:
    data_dir: 数据目录路径，其中包含场景文件夹或直接包含CSV文件
    verbose: 是否打印详细处理信息
    map_to_intent: 是否将场景名称映射到意图
    
    返回:
    scenario_counts: 场景频次统计字典
    stats: 处理统计信息
    """
    # 统计信息初始化
    stats = {
        'total_scenarios': 0,
        'processed_files': 0,
        'skipped_files': 0,
        'mapped_to_intent': map_to_intent
    }
    
    # 检查目录是否存在
    if not os.path.exists(data_dir):
        print(f"错误: 目录不存在: {data_dir}")
        return None, None
    
    # 获取目录下的所有CSV文件（可能在子文件夹中）
    csv_files = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    stats['total_files'] = len(csv_files)
    
    if verbose:
        print(f"在目录 {data_dir} 及其子目录中发现 {stats['total_files']} 个CSV文件")
    
    # 统计场景频次
    scenario_counts = Counter()
    
    # 处理CSV文件
    for csv_file in csv_files:
        try:
            # 读取CSV文件，查看是否包含scenario列
            df = pd.read_csv(csv_file)
            
            # 检查是否包含scenario列
            if 'scenario' in df.columns:
                # 获取文件中的所有场景值
                file_scenarios = df['scenario'].dropna().unique()
                
                for scenario in file_scenarios:
                    # 更新场景计数
                    if map_to_intent:
                        if scenario in SCENARIO_NAME_TO_INTENT:
                            mapped_scenario = SCENARIO_NAME_TO_INTENT[scenario]
                            scenario_counts[mapped_scenario] += 1
                        else:
                            scenario_counts[scenario] += 1
                            if verbose:
                                print(f"警告: 没有找到场景 {scenario} 的意图映射关系")
                    else:
                        scenario_counts[scenario] += 1
                    
                    stats['total_scenarios'] += 1
                
                stats['processed_files'] += 1
                
                if verbose and stats['processed_files'] % 10 == 0:
                    print(f"已处理 {stats['processed_files']}/{stats['total_files']} 个文件")
            else:
                # 如果CSV文件中没有scenario列，尝试从文件名中提取
                if '_scenario_' in csv_file:
                    # 从文件名中提取场景名称
                    scenario_part = csv_file.split('_scenario_')[-1]
                    scenario = scenario_part.split('.')[0]
                    
                    # 更新场景计数
                    if map_to_intent:
                        if scenario in SCENARIO_NAME_TO_INTENT:
                            mapped_scenario = SCENARIO_NAME_TO_INTENT[scenario]
                            scenario_counts[mapped_scenario] += 1
                        else:
                            scenario_counts[scenario] += 1
                            if verbose:
                                print(f"警告: 没有找到场景 {scenario} 的意图映射关系")
                    else:
                        scenario_counts[scenario] += 1
                    
                    stats['total_scenarios'] += 1
                    stats['processed_files'] += 1
                else:
                    stats['skipped_files'] += 1
                    if verbose:
                        print(f"警告: 文件 {csv_file} 不包含scenario列且无法从文件名中提取场景信息")
        
        except Exception as e:
            stats['skipped_files'] += 1
            if verbose:
                print(f"处理文件 {csv_file} 时出错: {e}")
    
    if verbose:
        print(f"\n场景频次统计:")
        print(f"总场景数量: {stats['total_scenarios']}")
        print(f"成功处理的文件数: {stats['processed_files']}")
        print(f"跳过的文件数: {stats['skipped_files']}")
        print(f"不同场景类型数量: {len(scenario_counts)}")
        
        for scenario, count in sorted(scenario_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{scenario}: {count}次 ({count/stats['total_scenarios']*100:.2f}%)")
    
    return scenario_counts, stats

def main_scenario_analysis(data_dir='./data/grouped_data_csv', output_dir=None, verbose=True, map_to_intent=False):
    """
    场景分析的主函数，集成了所有场景分析相关功能
    
    参数:
    data_dir: 数据目录路径
    output_dir: 输出目录，如果为None则不保存结果
    verbose: 是否显示详细信息
    map_to_intent: 是否将scenario映射到intent
    
    返回:
    分析结果字典
    """
    results = {}
    
    # 分析场景频次
    print("="*50)
    print("开始分析场景频次...")
    scenario_counts, stats = analyze_scenario_frequency(data_dir, verbose, map_to_intent)
    
    if scenario_counts is None:
        print("分析失败，无法继续执行后续分析。")
        return None
    
    results['scenario_counts'] = scenario_counts
    results['stats'] = stats
    
    # 设置数据类型名称
    item_type = 'Mapped Scenario' if map_to_intent else 'Scenario'
    type_prefix = 'mapped_' if map_to_intent else ''
    
    # 可视化分析结果 - 柱状图
    if verbose:
        print("="*50)
        print(f"生成{item_type}频次柱状图...")
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        bar_chart_path = os.path.join(output_dir, f'{type_prefix}scenario_bar_chart.png')
    else:
        bar_chart_path = None
    
    plot_distribution_bar_chart(
        scenario_counts, 
        top_n=20, 
        show_all=False, 
        save_path=bar_chart_path,
        item_type=item_type
    )
    
    # 可视化分析结果 - 饼图
    if verbose:
        print("="*50)
        print(f"生成{item_type}频次饼图...")
    
    if output_dir:
        pie_chart_path = os.path.join(output_dir, f'{type_prefix}scenario_pie_chart.png')
    else:
        pie_chart_path = None
    
    plot_distribution_pie_chart(
        scenario_counts, 
        top_n=10, 
        save_path=pie_chart_path,
        item_type=item_type
    )
    
    # 生成表格
    if verbose:
        print("="*50)
        print(f"生成{item_type}频次表格...")
    
    if output_dir:
        table_path = os.path.join(output_dir, f'{type_prefix}scenario_frequency_table')
    else:
        table_path = None
    
    # 判断是否需要添加映射函数
    add_mapping = map_to_intent
    mapping_function = None
    
    if map_to_intent:
        # 添加一个映射函数，显示映射关系
        def get_original_scenario(mapped_intent):
            return [scenario for scenario, intent in SCENARIO_NAME_TO_INTENT.items() if intent == mapped_intent]
        
        mapping_function = get_original_scenario
    
    generate_distribution_table(
        scenario_counts, 
        save_path=table_path, 
        save_format='both',
        item_column_name=item_type,
        add_mapping=add_mapping,
        mapping_function=mapping_function,
        mapping_column_name='Original Scenarios'
    )
    
    # 生成综合Excel报告
    if output_dir:
        if verbose:
            print("="*50)
            print("生成综合Excel报告...")
        
        excel_path = os.path.join(output_dir, f'{type_prefix}scenario_analysis_report.xlsx')
        generate_comprehensive_excel_report(
            scenario_counts, 
            stats, 
            excel_path,
            item_name=item_type,
            sheet_prefix='',
            add_mapping=add_mapping,
            mapping_function=mapping_function,
            mapping_column_name='Original Scenarios'
        )
    
    if verbose:
        print("="*50)
        print(f"{item_type}分析完成！")
        if output_dir:
            print(f"所有结果已保存到目录: {output_dir}")
    
    return results

def process_data_for_analysis(intent_path, scenario_path, output_dir=None, analyze_type='all', verbose=True, intent_column='intent'):
    """
    处理数据并执行指定类型的分析
    
    参数:
    intent_path: 意图数据路径（CSV文件）
    scenario_path: 场景数据路径（目录）
    output_dir: 输出目录
    analyze_type: 分析类型 ('intent', 'simplified_intent', 'scenario', 'all')
    verbose: 是否显示详细信息
    intent_column: 意图列的名称，可以是'intent'或'infer_intent'
    
    返回:
    分析结果字典
    """
    results = {}
    
    # 创建输出目录
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 根据分析类型执行相应的分析
    if analyze_type in ['intent', 'all']:
        if os.path.isfile(intent_path) and intent_path.endswith('.csv'):
            intent_output_dir = output_dir and os.path.join(output_dir, 'intent_analysis')
            intent_results = main_intent_analysis(intent_path, intent_output_dir, verbose, intent_type='regular', intent_column=intent_column)
            results['intent'] = intent_results
        else:
            print(f"错误: 意图分析需要指定一个CSV文件路径: {intent_path}")
    
    if analyze_type in ['simplified_intent', 'all']:
        if os.path.isfile(intent_path) and intent_path.endswith('.csv'):
            simplified_intent_output_dir = output_dir and os.path.join(output_dir, 'simplified_intent_analysis')
            simplified_intent_results = main_intent_analysis(
                intent_path, 
                simplified_intent_output_dir, 
                verbose, 
                intent_type='simplified',
                intent_column=intent_column
            )
            results['simplified_intent'] = simplified_intent_results
        else:
            print(f"错误: 简化意图分析需要指定一个CSV文件路径: {intent_path}")
    
    if analyze_type in ['scenario', 'all']:
        if os.path.isdir(scenario_path):
            scenario_output_dir = output_dir and os.path.join(output_dir, 'scenario_analysis')
            scenario_results = main_scenario_analysis(scenario_path, scenario_output_dir, verbose)
            results['scenario'] = scenario_results
            
            # 也执行映射到intent的分析
            if analyze_type == 'all':
                mapped_scenario_output_dir = output_dir and os.path.join(output_dir, 'mapped_scenario_analysis')
                mapped_results = main_scenario_analysis(scenario_path, mapped_scenario_output_dir, verbose, map_to_intent=True)
                results['mapped_scenario'] = mapped_results
        else:
            print(f"错误: 场景分析需要指定一个目录路径: {scenario_path}")
    
    # 执行意图转换分析 - 只分析simplified intent transitions
    if analyze_type in ['transitions', 'all'] and os.path.isfile(intent_path) and intent_path.endswith('.csv'):
        # 简化意图的转换分析
        simplified_transitions_output_dir = output_dir and os.path.join(output_dir, 'simplified_intent_transitions_analysis')
        simplified_transition_results = analyze_simplified_intent_transitions(
            intent_path, 
            verbose, 
            save_dir=simplified_transitions_output_dir,
            intent_column=intent_column
        )
        results['simplified_intent_transitions'] = simplified_transition_results
    
    return results

# 如果直接运行此脚本


# 添加兼容性包装函数
def plot_intent_bar_chart(intent_counts, top_n=10, show_all=False, save_path=None):
    """已被通用函数plot_distribution_bar_chart替代，保留此函数以兼容旧代码"""
    return plot_distribution_bar_chart(intent_counts, top_n, show_all, save_path, item_type='Intent')

def plot_intent_pie_chart(intent_counts, top_n=10, save_path=None):
    """已被通用函数plot_distribution_pie_chart替代，保留此函数以兼容旧代码"""
    return plot_distribution_pie_chart(intent_counts, top_n, save_path, item_type='Intent')

def generate_intent_table(intent_counts, save_path=None, save_format='csv'):
    """已被通用函数generate_distribution_table替代，保留此函数以兼容旧代码"""
    return generate_distribution_table(intent_counts, save_path, save_format, item_column_name='Intent')

def generate_comprehensive_excel(intent_counts, stats, save_path):
    """已被通用函数generate_comprehensive_excel_report替代，保留此函数以兼容旧代码"""
    return generate_comprehensive_excel_report(intent_counts, stats, save_path, item_name='Intent')

def plot_scenario_bar_chart(scenario_counts, top_n=10, show_all=False, save_path=None):
    """已被通用函数plot_distribution_bar_chart替代，保留此函数以兼容旧代码"""
    return plot_distribution_bar_chart(scenario_counts, top_n, show_all, save_path, item_type='Scenario')

def plot_scenario_pie_chart(scenario_counts, top_n=10, save_path=None):
    """已被通用函数plot_distribution_pie_chart替代，保留此函数以兼容旧代码"""
    return plot_distribution_pie_chart(scenario_counts, top_n, save_path, item_type='Scenario')

def generate_scenario_table(scenario_counts, save_path=None, save_format='csv', is_mapped=False):
    """已被通用函数generate_distribution_table替代，保留此函数以兼容旧代码"""
    item_type = 'Mapped Scenario' if is_mapped else 'Scenario'
    return generate_distribution_table(scenario_counts, save_path, save_format, item_column_name=item_type)

def generate_scenario_comprehensive_excel(scenario_counts, stats, save_path, is_mapped=False):
    """已被通用函数generate_comprehensive_excel_report替代，保留此函数以兼容旧代码"""
    item_type = 'Mapped Scenario' if is_mapped else 'Scenario'
    return generate_comprehensive_excel_report(scenario_counts, stats, save_path, item_name=item_type)

def plot_simplified_intent_bar_chart(simplified_intent_counts, top_n=10, show_all=False, save_path=None):
    """已被通用函数plot_distribution_bar_chart替代，保留此函数以兼容旧代码"""
    return plot_distribution_bar_chart(simplified_intent_counts, top_n, show_all, save_path, item_type='Simplified Intent')

def plot_simplified_intent_pie_chart(simplified_intent_counts, top_n=10, save_path=None):
    """已被通用函数plot_distribution_pie_chart替代，保留此函数以兼容旧代码"""
    return plot_distribution_pie_chart(simplified_intent_counts, top_n, save_path, item_type='Simplified Intent')

def generate_simplified_intent_table(simplified_intent_counts, save_path=None, save_format='csv'):
    """已被通用函数generate_distribution_table替代，保留此函数以兼容旧代码"""
    # 添加一个映射函数，显示哪些原始意图映射到了这个简化意图
    def get_original_intents(simplified_intent):
        return [intent for intent in SCENARIO_NAME_TO_INTENT.values() if simplify_intent(intent) == simplified_intent]
    
    return generate_distribution_table(
        simplified_intent_counts, 
        save_path, 
        save_format, 
        item_column_name='Simplified Intent',
        add_mapping=True,
        mapping_function=get_original_intents,
        mapping_column_name='Original Intents'
    )

def generate_simplified_intent_comprehensive_excel(simplified_intent_counts, stats, save_path):
    """已被通用函数generate_comprehensive_excel_report替代，保留此函数以兼容旧代码"""
    # 添加一个映射函数，显示哪些原始意图映射到了这个简化意图
    def get_original_intents(simplified_intent):
        return [intent for intent in SCENARIO_NAME_TO_INTENT.values() if simplify_intent(intent) == simplified_intent]
    
    return generate_comprehensive_excel_report(
        simplified_intent_counts, 
        stats, 
        save_path, 
        item_name='Simplified Intent',
        add_mapping=True,
        mapping_function=get_original_intents,
        mapping_column_name='Original Intents'
    )


if __name__ == "__main__":
    import argparse
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='数据分析工具')
    parser.add_argument('--intent_path', type=str, default='./data/dataset_intent_pred_world_view_segment_False.csv', 
                        help='意图数据路径 (CSV文件)')
    parser.add_argument('--scenario_path', type=str, default='./data/grouped_data_csv/',
                        help='场景数据目录路径')
    parser.add_argument('--output_dir', type=str, default='./analysis_results',
                        help='输出目录路径')
    parser.add_argument('--analyze_type', type=str, 
                        choices=['intent', 'simplified_intent', 'scenario', 'transitions', 'all'], 
                        default='all', help='分析类型')
    parser.add_argument('--verbose', action='store_true', default=True,
                        help='是否显示详细处理信息')
    parser.add_argument('--intent_column', type=str, default='intent',
                        choices=['intent', 'infer_intent'],
                        help='意图列的名称，可以是\'intent\'或\'infer_intent\'')
    
    args = parser.parse_args()
    
    # 执行分析
    results = process_data_for_analysis(
        args.intent_path,
        args.scenario_path, 
        args.output_dir,
        args.analyze_type,
        args.verbose,
        args.intent_column
    )
    
    if results:
        print("\n分析完成！所有结果已保存。")