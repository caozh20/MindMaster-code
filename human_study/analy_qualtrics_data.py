#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import os
import glob
from datetime import datetime
import re

# 在这里指定要分析的文件路径
# 示例: ["data/file1.xlsx", "data/file2.xlsx"]
# 设置为None则会自动搜索当前目录下的所有Excel文件
FILE_PATHS = [
    # 在此处添加您的文件路径，例如:
    # "path/to/your/file1.csv",
    # "path/to/your/file2.csv",
    './data/qualtrics/MindMaster Roleplay - 第二版_April 27, 2025_23.47.xlsx', 
    './data/qualtrics/MindMaster Roleplay_April 27, 2025_23.47.xlsx', 
]

def analyze_qualtrics_data(excel_files=None):
    """
    分析Qualtrics导出的Excel文件，提取特定列并合并数据。
    
    参数:
    excel_files (list): Excel文件路径列表，默认为None，将使用FILE_PATHS变量中设置的路径
    
    返回:
    merged_df: 合并后的数据框
    """
    # 如果没有提供文件列表，使用FILE_PATHS中的路径
    if excel_files is None:
        if FILE_PATHS and len(FILE_PATHS) > 0:
            excel_files = FILE_PATHS
        else:
            # 如果FILE_PATHS也为空，搜索当前目录下的所有Excel/CSV文件
            excel_files = glob.glob("*.xlsx") + glob.glob("*.xls") + glob.glob("*.csv")
            if not excel_files:
                print("当前目录下未找到Excel或CSV文件！")
                return None
    
    # 目标列的Q编码和对应的中文名
    target_columns = {
        "Q2924": "姓名",
        "Q2933": "性别",
        "Q6561": "受教育程度",
        "StartDate": "开始时间",
        "PassQuiz": "是否通过测验",
        "QuizAttempts": "测验尝试次数"
    }
    
    # Q编码的替代模式（如果Q编码不完全匹配）
    q_code_alternatives = {
        "Q2924": ["Q2924", "姓名", "Name", "RecipientName"],
        "Q2933": ["Q2933", "性别", "Gender"],
        "Q6561": ["Q6561", "受教育程度", "Education"],
        "StartDate": ["StartDate", "Start Date"],
        "PassQuiz": ["PassQuiz", "Quiz"],
        "QuizAttempts": ["QuizAttempts", "Attempts"]
    }
    
    # 用于存储每个文件的数据
    all_data = []
    
    # 处理每个文件
    for file_path in excel_files:
        try:
            print(f"\n正在处理文件: {file_path}")
            
            # 根据文件扩展名决定使用哪种方法读取文件
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 读取文件前5行以检查结构
            if file_ext == '.csv':
                raw_df = pd.read_csv(file_path, header=None, nrows=5)
            else:
                raw_df = pd.read_excel(file_path, header=None, nrows=5)
            
            print(f"文件前5行预览:")
            for i in range(min(5, len(raw_df))):
                print(f"第{i+1}行: {raw_df.iloc[i].tolist()}")
            
            # Qualtrics通常在第一行有Q编码，第二行有可读名称，第三行开始是数据
            # 尝试检测Q编码行（通常是第一行）
            q_code_row = -1
            readable_name_row = -1
            
            # 寻找包含Q编码的行
            for i in range(min(3, len(raw_df))):
                row_content = ' '.join([str(x) for x in raw_df.iloc[i].tolist() if pd.notna(x)])
                # 检查是否包含多个Q开头的编码
                if len(re.findall(r'Q\d+', row_content)) > 2:
                    q_code_row = i
                    # 假设可读名称在下一行
                    readable_name_row = i + 1 if i + 1 < len(raw_df) else -1
                    break
            
            print(f"检测到Q编码行: 第{q_code_row+1}行, 可读名称行: 第{readable_name_row+1}行")
            
            # 读取数据，使用Q编码行作为列名
            if file_ext == '.csv':
                df = pd.read_csv(file_path, header=q_code_row, skiprows=range(1, readable_name_row+1))
            else:
                df = pd.read_excel(file_path, header=q_code_row, skiprows=range(1, readable_name_row+1))
            
            # 获取列名映射，第一行是Q编码，第二行是可读名称
            column_name_mapping = {}
            if q_code_row >= 0 and readable_name_row >= 0:
                q_codes = raw_df.iloc[q_code_row].tolist()
                readable_names = raw_df.iloc[readable_name_row].tolist()
                
                # 创建Q编码到可读名称的映射
                for i in range(min(len(q_codes), len(readable_names))):
                    if pd.notna(q_codes[i]) and pd.notna(readable_names[i]):
                        column_name_mapping[str(q_codes[i])] = str(readable_names[i])
            
            print(f"列名映射: {column_name_mapping}")
            print(f"实际数据列名: {df.columns.tolist()}")
            
            # 创建一个新的DataFrame来存储我们需要的数据
            df_filtered = pd.DataFrame()
            
            # 添加数据来源列
            df_filtered['数据来源'] = os.path.basename(file_path)
            
            # 为每个目标列寻找匹配的列
            for q_code, column_name in target_columns.items():
                found = False
                
                # 1. 直接查找Q编码
                if q_code in df.columns:
                    df_filtered[column_name] = df[q_code]
                    print(f"✓ 直接找到列 '{q_code}'，映射为 '{column_name}'")
                    found = True
                
                # 2. 尝试查找可读名称（如果在列中）
                elif column_name in df.columns:
                    df_filtered[column_name] = df[column_name]
                    print(f"✓ 直接找到列 '{column_name}'")
                    found = True
                
                # 3. 尝试更灵活的匹配
                if not found:
                    alternatives = q_code_alternatives.get(q_code, [])
                    for alt in alternatives:
                        # 精确匹配
                        if alt in df.columns:
                            df_filtered[column_name] = df[alt]
                            print(f"✓ 找到替代列 '{alt}'，映射为 '{column_name}'")
                            found = True
                            break
                        
                        # 模糊匹配
                        for col in df.columns:
                            if re.search(f"(?i){re.escape(alt)}", str(col)):
                                df_filtered[column_name] = df[col]
                                print(f"✓ 模糊匹配: '{col}' 匹配 '{alt}'，映射为 '{column_name}'")
                                found = True
                                break
                        if found:
                            break
                
                # 4. 特殊处理：姓名列可能是RecipientFirstName + RecipientLastName
                if not found and q_code == "Q2924":
                    first_name_col = None
                    last_name_col = None
                    
                    for col in df.columns:
                        if re.search(r'(?i)recipient.*first.*name', str(col)):
                            first_name_col = col
                        elif re.search(r'(?i)recipient.*last.*name', str(col)):
                            last_name_col = col
                    
                    if first_name_col and last_name_col:
                        # 合并姓和名
                        df_filtered[column_name] = df[last_name_col].fillna('') + df[first_name_col].fillna('')
                        print(f"✓ 合并 '{last_name_col}' 和 '{first_name_col}' 为 '{column_name}'")
                        found = True
                    elif first_name_col:
                        df_filtered[column_name] = df[first_name_col]
                        print(f"✓ 仅使用 '{first_name_col}' 作为 '{column_name}'")
                        found = True
                    elif last_name_col:
                        df_filtered[column_name] = df[last_name_col]
                        print(f"✓ 仅使用 '{last_name_col}' 作为 '{column_name}'")
                        found = True
                
                if not found:
                    print(f"✗ 警告: 未找到列 '{q_code}' 或 '{column_name}' 的任何匹配")
                    df_filtered[column_name] = None
            
            # 将过滤后的数据添加到列表中
            all_data.append(df_filtered)
            print(f"\n成功处理文件 {file_path}，读取了 {len(df_filtered)} 行数据")
            
            # 打印数据示例以验证
            if len(df_filtered) > 0:
                print("\n数据示例（前3行）:")
                print(df_filtered.head(3))
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    if not all_data:
        print("没有成功处理任何文件！")
        return None
    
    # 合并所有数据
    merged_df = pd.concat(all_data, ignore_index=True)
    print(f"\n合并后的数据共有 {len(merged_df)} 行")
    
    # 处理日期格式
    try:
        if '开始时间' in merged_df.columns:
            merged_df['开始时间'] = pd.to_datetime(merged_df['开始时间'], errors='coerce')
            print("成功转换日期格式")
    except Exception as e:
        print(f"转换日期格式时出错: {str(e)}")
    
    # 保存合并后的原始数据（去重前）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_output_file = f"merged_qualtrics_data_original_{timestamp}.xlsx"
    merged_df.to_excel(original_output_file, index=False)
    print(f"原始合并数据（去重前）已保存至: {original_output_file}")
    
    # 显示原始数据的统计信息
    print("\n原始数据统计信息（去重前）:")
    for col in merged_df.columns:
        not_null_count = merged_df[col].count()
        print(f"  - {col}: {not_null_count} 个非空值 ({not_null_count/len(merged_df)*100:.1f}%)")
    
    # ===== 数据去重处理 =====
    print("\n开始进行数据去重处理...")
    
    # 确保姓名列和开始时间列存在
    if '姓名' not in merged_df.columns or '开始时间' not in merged_df.columns:
        print("错误: 缺少进行去重所需的'姓名'或'开始时间'列！")
        return merged_df
    
    # 复制DataFrame以进行去重操作
    deduped_df = merged_df.copy()
    
    # 确保测验尝试次数是数值型
    if '测验尝试次数' in deduped_df.columns:
        deduped_df['测验尝试次数'] = pd.to_numeric(deduped_df['测验尝试次数'], errors='coerce').fillna(0)
    
    # 确保是否通过测验是布尔型或可以转换为布尔型
    if '是否通过测验' in deduped_df.columns:
        # 转换各种可能的值为布尔型
        deduped_df['是否通过测验'] = deduped_df['是否通过测验'].apply(
            lambda x: True if str(x).lower() in ('true', 't', 'yes', 'y', '1', 'passed', 'pass') else False
        )
    
    # 添加日期列（不包含时间）用于分组
    deduped_df['日期'] = deduped_df['开始时间'].dt.date
    
    # 按姓名分组进行去重处理
    result_records = []
    
    # 获取所有唯一姓名
    unique_names = deduped_df['姓名'].dropna().unique()
    print(f"共有 {len(unique_names)} 个唯一姓名")
    
    for name in unique_names:
        # 获取该姓名的所有记录
        name_records = deduped_df[deduped_df['姓名'] == name].copy()
        
        if len(name_records) == 0:
            continue
            
        # 按开始时间排序
        name_records = name_records.sort_values('开始时间')
        
        # 获取该姓名最早的记录
        earliest_record = name_records.iloc[0].copy()
        earliest_date = earliest_record['日期']
        
        # 找出同一天的其他记录
        same_day_records = name_records[name_records['日期'] == earliest_date]
        
        if len(same_day_records) > 1:
            print(f"姓名 '{name}' 在 {earliest_date} 有 {len(same_day_records)} 条记录，将合并")
            
            # 合并测验尝试次数
            if '测验尝试次数' in same_day_records.columns:
                total_attempts = same_day_records['测验尝试次数'].sum()
                earliest_record['测验尝试次数'] = total_attempts
                print(f"  - 累计测验尝试次数: {total_attempts}")
                
                # 关键修复：当测验尝试次数叠加后，将"是否通过测验"设置为True
                if total_attempts > 0:
                    earliest_record['是否通过测验'] = True
                    print(f"  - 由于存在测验尝试，自动设置通过测验状态为: True")
            
            # 更新通过测验状态（如果任一记录为TRUE则为TRUE）
            if '是否通过测验' in same_day_records.columns:
                passed_quiz = same_day_records['是否通过测验'].any()
                if passed_quiz:  # 只有当有真实通过记录时才更新状态
                    earliest_record['是否通过测验'] = True
                    print(f"  - 因存在通过记录，更新通过测验状态为: True")
        
        # 添加处理后的记录
        result_records.append(earliest_record)
    
    # 创建去重后的DataFrame
    deduped_result_df = pd.DataFrame(result_records)
    
    # 删除临时使用的日期列
    if '日期' in deduped_result_df.columns:
        deduped_result_df = deduped_result_df.drop('日期', axis=1)
    
    print(f"\n去重后的数据共有 {len(deduped_result_df)} 行（原 {len(merged_df)} 行）")
    
    # 给出通过测验状态的统计信息
    if '是否通过测验' in deduped_result_df.columns:
        passed_count = deduped_result_df['是否通过测验'].sum()
        total_count = len(deduped_result_df)
        print(f"通过测验的记录数: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    # 保存去重后的数据
    deduped_output_file = f"merged_qualtrics_data_deduped_{timestamp}.xlsx"
    deduped_result_df.to_excel(deduped_output_file, index=False)
    print(f"去重后的数据已保存至: {deduped_output_file}")
    
    # 显示去重后的统计信息
    print("\n去重后的数据统计信息:")
    for col in deduped_result_df.columns:
        not_null_count = deduped_result_df[col].count()
        print(f"  - {col}: {not_null_count} 个非空值 ({not_null_count/len(deduped_result_df)*100:.1f}%)")
    
    return deduped_result_df

def main():
    """主函数"""
    # 使用FILE_PATHS中定义的文件路径
    analyze_qualtrics_data(FILE_PATHS if FILE_PATHS else None)

if __name__ == "__main__":
    main()
