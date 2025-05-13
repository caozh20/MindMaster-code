import sqlite3
import pickle
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

import sys
from collections import Counter

sys.path.append('.')

import core

def plt_data_from_db(db_path, select_column, select_value, target_column, method=None):
    conn = sqlite3.connect(db_path)
    try:
        # 创建一个 Cursor 对象并利用它执行 SQL 命令
        cursor = conn.cursor()
        query = f"""
        SELECT {target_column}
        FROM user_interaction
        WHERE {select_column} = ?
        """

        # 执行查询
        # 使用参数替换而非字符串拼接可以防止 SQL 注入
        cursor.execute(query, (select_value,))

        # 获取查询结果
        rows = cursor.fetchall()

        target_list = []

        # 打印结果
        for row in rows:
            if method is None:
                target_list.append(row[0])
            else:
                target_list.append(method(row[0]))

        # 数据处理
        df = pd.DataFrame(target_list, columns=['Action'])
        action_counts = df['Action'].value_counts()

        # 放大图表尺寸
        plt.figure(figsize=(15, 12))

        # 使用explode拉出小切片
        explode = [0.1 if freq < 2 else 0 for freq in action_counts]  # 假设小于3次的动作视为小切片

        # 绘制饼状图，使用图例
        plt.pie(action_counts, labels=None, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired(range(len(action_counts))), explode=explode)
        plt.title(f'{target_column}_frequency_pie_chart_{select_column}_{select_value}')
        plt.legend(labels=action_counts.index, title="Actions", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.axis('equal')  # 保证饼状图是圆形的

        # 保存图像到文件
        plt.savefig(f'{target_column}_frequency_pie_chart_{select_column}_{select_value}.png')
        plt.close()  # 关闭图形窗口
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # 关闭 Cursor 和连接
        cursor.close()
        conn.close()
        
def split_data_from_db(db_path):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_path)
    
    try:
        # 创建一个 Cursor 对象并利用它执行 SQL 命令
        cursor = conn.cursor()
        
        # 执行查询
        # cursor.execute("SELECT user_agent_action FROM user_interaction")

        query = "SELECT * FROM user_interaction"
        df = pd.read_sql_query(query, conn)
        # 识别新的轮次开始
        df['new_round'] = df['iteration'].diff().fillna(1).lt(0).cumsum()

        # 分组处理
        grouped = df.groupby('new_round')

        len_list = []

        # 打印每轮的数据
        for name, group in grouped:
            group = group.reset_index(drop=True)  # 重置索引，并丢弃原来的索引
            # print(f"Round {name}:")
            # print(len(group['user_name']))
            len_list.append(len(group['user_name']))
            # print(type(group))

        # 计算每个值的出现次数
        values, counts = zip(*[(val, len_list.count(val)) for val in set(len_list)])

        # 使用matplotlib来绘制柱状图
        plt.bar(values, counts)

        # 添加标题和轴标签
        plt.title('Histogram of Len')
        plt.xlabel('Len')
        plt.ylabel('Frequency')

        # 保存图像到文件
        plt.savefig(f'len.png')
        plt.close()  # 关闭图形窗口
            
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # 关闭 Cursor 和连接
        cursor.close()
        conn.close()


def read_data_from_db(db_path):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_path)
    
    try:
        # 创建一个 Cursor 对象并利用它执行 SQL 命令
        cursor = conn.cursor()
        
        # 执行查询
        # cursor.execute("SELECT user_agent_action FROM user_interaction")

        query = "SELECT * FROM user_interaction"
        df = pd.read_sql_query(query, conn)
        
        # 获取所有行
        rows = cursor.fetchall()
        
        action_name_list = []

        # 打印结果
        for row in rows:
            if not row[0] is None:
                action = pickle.loads(row[0])
                action_name_list.append(action.name()[0])
            else:
                action = None
            # print("Loaded object:", object)
            # print(row[0])
            # return
        print(action_name_list)

        
        # 识别新的轮次开始
        df['new_round'] = df['iteration'].diff().fillna(1).lt(0).cumsum()

        # 分组处理
        grouped = df.groupby('new_round')

        len_list = []

        # 打印每轮的数据
        for name, group in grouped:
            group = group.reset_index(drop=True)  # 重置索引，并丢弃原来的索引
            print(f"Round {name}:")
            print(group['user_name'][0])
            len_list.append(group['user_name'][0])
            print(type(group))
            
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # 关闭 Cursor 和连接
        cursor.close()
        conn.close()

# 调用函数，替换 'your_database_file.db' 和 'your_table_name'
# read_data_from_db('./instance/database.db')


def get_action_name(action_pickle):
    if not action_pickle is None:
        action = pickle.loads(action_pickle)
        return action.name()[0]
    else:
        return None

def get_max_interaction(db_path):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询相同 game_id 对应的最大 interaction
    query = """
    SELECT game_id, MAX(iteration)
    FROM user_interaction
    GROUP BY game_id
    """
    
    cursor.execute(query)
    
    # 获取结果
    results = cursor.fetchall()
    
    # 关闭连接
    cursor.close()
    conn.close()
    
    return results

def find_median(data):
    sorted_data = sorted(data)
    n = len(sorted_data)
    mid = n // 2

    if n % 2 == 0:
        # 如果是偶数个，返回中间两个数的平均值
        median = (sorted_data[mid - 1] + sorted_data[mid]) / 2
    else:
        # 如果是奇数个，返回中间的数
        median = sorted_data[mid]

    return median

def find_mode(data):
    count = Counter(data)
    max_count = max(count.values())
    mode = [k for k, v in count.items() if v == max_count]
    return mode

def iteration_time(db_path):
    import sqlite3
    import pandas as pd
    from statistics import mean, median, mode

    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_path)

    # 从数据库中读取数据
    query = """
    SELECT game_id, iteration, ts FROM user_interaction
    """
    df = pd.read_sql_query(query, conn)

    # 关闭数据库连接
    conn.close()

    # 将时间戳转换为 datetime 对象
    df['ts'] = pd.to_datetime(df['ts'])

    # # 计算每一轮的持续时间
    # df['time_diff'] = df.groupby('game_id')['ts'].diff().dt.total_seconds()

    # # 去掉NaN值（即第一轮，因为没有前一轮可比较）
    # time_diffs = df['time_diff'].dropna().tolist()

    # 删除重复的 iteration，保留最早的时间戳
    df = df.sort_values('ts').drop_duplicates(subset=['game_id', 'iteration'], keep='first')

    # 初始化一个列表来存储有效的时间差
    valid_time_diffs = []

    # 遍历每个 game_id
    for game_id, group in df.groupby('game_id'):
        # 按 iteration 排序
        group = group.sort_values('iteration')
        # 计算时间差
        for i in range(1, len(group)):
            if group.iloc[i]['iteration'] == group.iloc[i - 1]['iteration'] + 1:
                time_diff = (group.iloc[i]['ts'] - group.iloc[i - 1]['ts']).total_seconds()
                valid_time_diffs.append(time_diff)

    # 计算平均数，中位数和众数
    average_time = mean(valid_time_diffs)
    median_time = median(valid_time_diffs)
    try:
        mode_time = mode(valid_time_diffs)
    except:
        mode_time = "No unique mode"

    # print("Round durations in seconds:", time_diffs)
    print("Average duration:", average_time)
    print("Median duration:", median_time)
    print("Mode duration:", mode_time)

    # 绘制直方图
    plt.figure(figsize=(8, 5))
    sns.histplot(valid_time_diffs, bins=40, kde=True)
    plt.title('Histogram')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.show()

if __name__ == '__main__':
    split_data_from_db('./human_study/database.db')
    db_path = './human_study/database.db'
    max_interactions = get_max_interaction(db_path)
    iteraction_list = []
    less_iteration_list = []
    count = 0
    one_count = 0
    for game_id, max_interaction in max_interactions:
        print(f'Game ID: {game_id}, Max Interaction: {max_interaction}')
        if max_interaction < 20:
            if max_interaction == 15:
                count += 1
            else:
                less_iteration_list.append(max_interaction)
            iteraction_list.append(max_interaction)
        if max_interaction == 1:
            one_count += 1
    mean_iteration = sum(iteraction_list) / len(iteraction_list)
    med = find_median(iteraction_list)
    mode = find_mode(iteraction_list)

    print(mean_iteration)

    print(f"目前总计{len(iteraction_list)}条有效数据")
    print(f"其中一轮就结束游戏的有{one_count}条")
    print(f"占比为{(one_count / len(iteraction_list)):.2f}")

    print(f"交互次数的平均数为：{mean_iteration:.2f}")
    print(f"交互次数的中位数为：{med}")
    print(f"交互次数的众数为：{mode}")

    print(f"目前由于轮数到达限制而终止的游戏数量为：{count}")
    print(f"其占比为：{(count / len(iteraction_list)):.2f}")
    print(f"目前正常完成游戏所需的平均轮次为：{(sum(less_iteration_list) / len(less_iteration_list)):.2f}")
    print(f"其中中位数为{find_median(less_iteration_list)}")
    # print(sum(less_iteration_list) / len(less_iteration_list))
    print(less_iteration_list)
    # plt_data_from_db('./instance/database.db', 'user_name', 'caozh20@foxmail.com', 'user_agent_action', get_action_name)

    iteration_time(db_path)

    
