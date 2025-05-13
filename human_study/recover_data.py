import sys

sys.path.append(".")

import pickle
import sqlite3
from typing import List
from core.agent import Agent
from core.entity import Object, Landmark
from pathlib import Path
from core.scenario import Scenario
from core.world import World

import cv2
import numpy as np

import base64
import io
from PIL import Image
import numpy as np
import pygame
from core.intent import Intent
from core.check_fn import Is_Near

def get_db_connection():
    """获取SQLite数据库连接"""
    db_path = Path("./instance/database.db")
    return sqlite3.connect(db_path)
    
def create_recover_template(target_class):
    def recover_template(db_data):
        """将数据库中的pickle数据转换为target_class对象列表"""
        if not db_data:
            return []
        
        try:
            # 直接使用pickle加载数据
            target_classs_data = pickle.loads(db_data)
            
            # 如果target_classs_data已经是target_class对象列表，直接返回
            if isinstance(target_classs_data, list) and all(isinstance(x, target_class) for x in target_classs_data):
                return target_classs_data
                
            # 如果是字典列表，转换为target_class对象
            if isinstance(target_classs_data, list) and all(isinstance(x, dict) for x in target_classs_data):
                return [target_class(**target_class_dict) for target_class_dict in target_classs_data]
                
            # 如果是空列表，则返回空列表
            if isinstance(target_classs_data, list) and len(target_classs_data) == 0:
                return []

            print(target_classs_data)
            print(f"意外的数据类型: {type(target_classs_data)}")
            return []
            
        except pickle.UnpicklingError as e:
            print(f"Pickle解析错误: {str(e)}")
            return []
        except Exception as e:
            print(f"转换错误: {str(e)}")
            print(f"数据类型: {type(db_data)}")
            return []
    return recover_template

recover_agents = create_recover_template(Agent)
recover_objects = create_recover_template(Object)
recover_landmarks = create_recover_template(Landmark)


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

def recover_world(agents, objects, landmarks):
    world = World()
    world.agents = agents
    world.objects = objects
    world.landmarks = landmarks
    world.render_init()
    return world


def translate_target_intent2list(target_intent: Intent):
    # soc_intent 优先
    # soc_intent 目前只有request_help 和 help
    if target_intent.soc_intent is not None:
        if isinstance(target_intent.soc_intent[2], Intent):
            # 会不会出现soc_intent嵌套的现象？
            # 暂时假设soc_intent最后如若要接intent则必须接ind_intent
            target_intent = target_intent.soc_intent[2].ind_intent
        else:
            target_intent = target_intent.soc_intent
    else:
        # 处理ind_intent
        target_intent = target_intent.ind_intent
    
    assert isinstance(target_intent, list)
    # 经过如上处理，下面的target_intent应该只有list
    return target_intent

# 输出0， 1
# 使用目标距离来获取heuristic
# target_intent: [intent, agent, obj]
# 问题：intent似乎不会涉及到完成它的agent？
def heuristic(W, target_intent: Intent, agent_id):
    target_intent = translate_target_intent2list(target_intent=target_intent)
    
    # 判断目标数量
    if len(target_intent) > 2:
        # 目标多于两个，判断两个的距离
        return Is_Near(W, target_intent[1], target_intent[2])
    else:
        # 目标只有一个，判断agent和obj的距离
        return Is_Near(W, agent_id, target_intent[1])

def get_world_agents(user_id: int = None) -> List[Agent]:
    """从SQLite数据库读取并转换world_agents数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_id is not None:
            query = "SELECT world_agents, world_objs, world_landmarks FROM user_interaction WHERE user_id = ?"
            cursor.execute(query, (user_id,))
        else:
            query = "SELECT world_agents, world_objs, world_landmarks FROM user_interaction"
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        all_agents = []
        for row in results:
            print(type(row))
            if row[0]:
                agents = recover_agents(row[0])
                all_agents.extend(agents)
            if row[1]:
                print("objects")
                objects = recover_objects(row[1])
                print(objects[0])
            if row[2]:
                print("landmark")
                print(row[2])
                landmarks = recover_landmarks(row[2])
                # print(landmarks[0])
            world = recover_world(agents, objects, landmarks)
            frame_list = world.render()
            render_frames(frame_list)
            # exit()
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

def decompress_and_decode(frame_data):
    if frame_data.startswith('data:image/jpeg;base64,'):
        frame_data = frame_data[len('data:image/jpeg;base64,'):]
    
    image_data = base64.b64decode(frame_data)
    buffer = io.BytesIO(image_data)
    image = Image.open(buffer)
    frame = np.array(image)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame

def render_frames(frame_list):
    if not frame_list:
        print("No frames to display")
        return

    paused = True  # 默认开始时暂停
    current_frame_idx = 0
    
    # 显示第一帧
    decoded_frame = decompress_and_decode(frame_list[current_frame_idx])
    
    while True:  # 改用无限循环
        if not paused:
            if current_frame_idx < len(frame_list):
                decoded_frame = decompress_and_decode(frame_list[current_frame_idx])
                current_frame_idx += 1
            else:
                # 播放到最后一帧时自动暂停
                paused = True
                current_frame_idx = len(frame_list) - 1
        
        if decoded_frame is not None and decoded_frame.size > 0:
            frame_with_text = decoded_frame.copy()
            
            # 添加状态文字
            status = f"Frame: {current_frame_idx+1}/{len(frame_list)} {'PAUSED' if paused else 'PLAYING'}"
            cv2.putText(frame_with_text, status, (10, 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 添加控制说明
            controls = "Space: Pause/Play | N: Next | P: Previous | Q: Quit"
            cv2.putText(frame_with_text, controls, (10, 60),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Frame', frame_with_text)
        
        # 键盘控制
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('q'):  # 按 'q' 退出
            break
        elif key == ord(' '):  # 空格键暂停/继续
            paused = not paused
        elif key == ord('n'):  # 'n' 键下一帧
            if current_frame_idx < len(frame_list) - 1:
                current_frame_idx += 1
                decoded_frame = decompress_and_decode(frame_list[current_frame_idx])
        elif key == ord('p'):  # 'p' 键上一帧
            if current_frame_idx > 0:
                current_frame_idx -= 1
                decoded_frame = decompress_and_decode(frame_list[current_frame_idx])

    cv2.destroyAllWindows()

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