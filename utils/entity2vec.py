import sys

sys.path.append('.')

import pickle
import sqlite3
from typing import List
from core.agent import Agent
from core.entity import Object
from pathlib import Path
import numpy as np

def get_db_connection():
    """获取SQLite数据库连接"""
    db_path = Path("./human_study/database.db")
    return sqlite3.connect(db_path)

def convert_db_agents_to_objects(db_data) -> List[Agent]:
    """将数据库中的pickle数据转换为Agent对象列表"""
    if not db_data:
        return []
    
    try:
        # 直接使用pickle加载数据
        agents_data = pickle.loads(db_data)
        
        # 如果agents_data已经是Agent对象列表，直接返回
        if isinstance(agents_data, list) and all(isinstance(x, Agent) for x in agents_data):
            return agents_data
            
        # 如果是字典列表，转换为Agent对象
        if isinstance(agents_data, list) and all(isinstance(x, dict) for x in agents_data):
            return [Agent(**agent_dict) for agent_dict in agents_data]
            
        print(f"意外的数据类型: {type(agents_data)}")
        return []
        
    except pickle.UnpicklingError as e:
        print(f"Pickle解析错误: {str(e)}")
        return []
    except Exception as e:
        print(f"转换错误: {str(e)}")
        print(f"数据类型: {type(db_data)}")
        return []

def convert_db_objs_to_objects(db_data) -> List[Object]:
    """将数据库中的pickle数据转换为Object对象列表"""
    if not db_data:
        return []
    
    try:
        # 直接使用pickle加载数据
        objs_data = pickle.loads(db_data)
        
        # 如果objs_data已经是Object对象列表，直接返回
        if isinstance(objs_data, list) and all(isinstance(x, Object) for x in objs_data):
            return objs_data
            
        # 如果是字典列表，转换为Object对象
        if isinstance(objs_data, list) and all(isinstance(x, dict) for x in objs_data):
            return [Object(**Object_dict) for Object_dict in objs_data]
            
        print(f"意外的数据类型: {type(objs_data)}")
        return []
        
    except pickle.UnpicklingError as e:
        print(f"Pickle解析错误: {str(e)}")
        return []
    except Exception as e:
        print(f"转换错误: {str(e)}")
        print(f"数据类型: {type(db_data)}")
        return []

def inspect_database_content():
    """详细检查数据库中的原始内容"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有记录用于检查
        cursor.execute("SELECT world_agents FROM user_interaction LIMIT 5")
        rows = cursor.fetchall()
        
        print("=== 数据库内容检查 ===")
        for i, row in enumerate(rows, 1):
            if row and row[0]:
                print(f"\n记录 {i}:")
                data = row[0]
                print(f"数据类型: {type(data)}")
                
                try:
                    unpickled_data = pickle.loads(data)
                    print(f"Unpickled 数据类型: {type(unpickled_data)}")
                    if isinstance(unpickled_data, list):
                        print(f"列表长度: {len(unpickled_data)}")
                        if unpickled_data:
                            print(f"第一个元素类型: {type(unpickled_data[0])}")
                            print(f"第一个元素内容: {unpickled_data[0]}")
                except Exception as e:
                    print(f"Unpickle 失败: {str(e)}")
                
                print("-" * 80)
                
    except Exception as e:
        print(f"检查数据库内容时出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()

def get_world_agents(user_id: int = None) -> List[Agent]:
    """从SQLite数据库读取并转换world_agents数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_id is not None:
            query = "SELECT world_agents FROM user_interaction WHERE user_id = ?"
            cursor.execute(query, (user_id,))
        else:
            query = "SELECT world_agents FROM user_interaction"
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        all_agents = []
        for row in results:
            if row[0]:
                agents = convert_db_agents_to_objects(row[0])
                all_agents.extend(agents)
        
        return all_agents
        
    except sqlite3.Error as e:
        print(f"SQLite错误: {str(e)}")
        return []
    except Exception as e:
        print(f"其他错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []
    finally:
        cursor.close()
        conn.close()

def get_world_objects(user_id: int = None) -> List[Agent]:
    """从SQLite数据库读取并转换world_objects数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_id is not None:
            query = "SELECT world_objs FROM user_interaction WHERE user_id = ?"
            cursor.execute(query, (user_id,))
        else:
            query = "SELECT world_objs FROM user_interaction"
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        all_objs = []
        for row in results:
            if row[0]:
                objs = convert_db_objs_to_objects(row[0])
                all_objs.extend(objs)
        
        return all_objs
        
    except sqlite3.Error as e:
        print(f"SQLite错误: {str(e)}")
        return []
    except Exception as e:
        print(f"其他错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []
    finally:
        cursor.close()
        conn.close()

# 当涉及到agemt, obj 之间的关系时，选择用

# 将Agent类转变为向量
# belief, intent 作为 pg+ 的元素单独处理
# [agent_position, agent_size, agent_size, attention, 
#   body_gesture(pointing, waving, hitting, speaking, performing, nodding, shaking, playing, performing, eating), 
#   desire, ]
def agent2vector(agent: Agent):
    agent_vector_list = []
    agent_vector_list += list(agent.position)
    agent_vector_list.append(agent.size)
    # 为了和obj对齐，再append一次
    agent_vector_list.append(agent.size)
    agent_vector_list.append(agent.attention)
    agent_vector_list += [agent.pointing, agent.waving, agent.hitting, agent.speaking, agent.performing, 
                          agent.nodding, agent.shaking, agent.playing, agent.performing, agent.eating]
    agent_vector_list += agent.desire.to_list()
    print(agent_vector_list)
    return np.asarray(agent_vector_list)

# 将Object类转变为向量
# 怎么样表征不同类obj的属性？（如能不能打开，能不能玩这种）需不需要表征？
# 暂时不表征不同类obj的属性，认为这是一种先验，有intent mask 表征
# [obj_position, size, 
# obj的状态（open, locked, (hidden?, needs_key?), being_played, player_num, is_broken]
def object2vector(obj: Object):
    obj_vector_list = []
    obj_vector_list += list(obj.position)
    obj_vector_list += list(obj.size)
    obj_vector_list += list([obj.open, obj.locked, obj.being_played, obj.player_num])
    print(obj_vector_list)
    return np.asarray(obj_vector_list)

# 得到可以刻画整个房间状态的大vector
# Vector 构成
#   [agent_basic_vec, agent_beleif_vec, agent_2nd_belief_vec?, objs_vec]
#   belief_vec 是由belief 中的agent, obj转变为vector得来
# 每个intent 都对应着一个mask，通过mask从整体vector中取出需要的部分
# 为了更加方便地得到这个mask，我们需要引入一个position_vector，用id来表示整体vector中各个位置对应的obj/agent
# 之后，intent通过读取房间里的状态决定需要哪些obj，再与position_vector进行计算得到最终的mask，从而得到最终的向量

# 针对同类物品有多个的情况，我们可以枚举出所有涉及到的intent，对于每一个Intent，都有一个对应的master得到该intent的对应向量，从而得到距离的分数
# 模型既可以对于每一个intent单独做一个模型，也可以通过word2vec的技术，将intent转变为vec，append到原本的vec上，再通过一个模型进行综合处理

# 补足agent 与 其他物品（涉及到意图的）的连接
# agent 与其他obj可能的交互形式
#   holding
#   (intent specific) in belief



# 使用示例
if __name__ == "__main__":
    # 首先详细检查数据库内容
    print("=== 检查数据库内容 ===")
    inspect_database_content()
    
    print("\n=== 尝试获取数据 ===")
    # 获取所有用户的agents
    all_agents = get_world_agents()
    print(f"Found {len(all_agents)} agents in total")
    
    # 打印第一个agent的信息（如果存在）
    if all_agents:
        print("First agent details:", vars(all_agents[0]))
        agent_vec = agent2vector(all_agents[0])
        print(agent_vec)

    all_objs = get_world_objects()
    print(f"Found {len(all_objs)} objects in total")
    
    # 打印第一个object的信息（如果存在）
    if all_objs:
        print("First object details:", vars(all_objs[0]))
        obj_vec = object2vector(all_objs[0])
        print(obj_vec)