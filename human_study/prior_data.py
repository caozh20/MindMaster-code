import json

def retrive_zero_data(file_path):
    # 读取json文件
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # 获取第一个值为0的三元组
    for value1 in data:
        for value2 in data[value1]:
            for intent in data[value1][value2]:
                if data[value1][value2][intent] == 0:
                    # 找到第一个值为0的三元组后立即更新
                    data[value1][value2][intent] = 1
                    
                    # 保存更新后的json文件
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=4)
                    
                    # 返回找到的三元组
                    return [value1, value2, intent]
    
    # 如果没有找到值为0的三元组，返回None
    return None

def finish_zero_data(file_path, keys_list): 
    # 读取json文件
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    try: 

        data[keys_list[0]][keys_list[1]][keys_list[2]] = 2

        # 保存更新后的json文件
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
                        
        return True
    except:
        return False