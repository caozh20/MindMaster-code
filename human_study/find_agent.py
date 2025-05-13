import pickle
from typing import Optional, List
from core.agent import Agent

def find_agent_by_id(raw_data: bytes, agent_id: int) -> Optional[Agent]:
    """
    从pickle序列化的数据中查找指定ID的Agent对象
    
    Args:
        raw_data (bytes): 从数据库中读取的原始pickle数据
        agent_id (int): 要查找的agent ID
    
    Returns:
        Optional[Agent]: 找到的Agent对象，如果未找到则返回None
    """
    try:
        # 反序列化数据得到Agent列表
        agents_list = pickle.loads(raw_data)
        
        # 确保得到的是列表
        if not isinstance(agents_list, list):
            print(f"意外的数据类型: {type(agents_list)}")
            return None
            
        # 查找指定ID的Agent
        for agent in agents_list:
            if hasattr(agent, 'id') and agent.id == agent_id:
                return agent
                
        # 未找到指定ID的Agent
        return None
        
    except pickle.UnpicklingError as e:
        print(f"Pickle解析错误: {str(e)}")
        return None
    except Exception as e:
        print(f"查找过程出错: {str(e)}")
        print(f"数据类型: {type(raw_data)}")
        return None
    
# 用来输出desire
# agent.desire.to_dict()