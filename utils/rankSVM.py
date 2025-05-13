import sys

sys.path.append('.')

import numpy as np
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import json
from core.const import ATTENTION_RADIUS
from utils.base import angle
import pandas as pd
import math
from utils.word2vec import words as WORDS
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np

ACTION2WORD = {
    'ActionMoveTo': ["move"],
    'ActionRotateTo': ["rotate"],
    'ActionOpen': ["open"],
    'ActionUnlock': ['unlock'],
    'ActionGrab': ["grab"],
    'ActionGiveTo': ["give"],
    'ActionWaveHand': ['wave', 'hand'],
    'ActionMoveToAttention': ['move', 'attention'],
    'ActionPointTo': ["point"],
    'ActionNodHead': ['nod', 'head'],
    'ActionShakeHead': ['shake', 'head'],
    'ActionPlay': ["play"],
    'ActionPutInto': ['put', 'into'],
    'ActionPutOnto': ['put', 'onto'],
    'ActionPutDown': ['put', 'down'],
    'ActionFollowPointing': ['follow', 'pointing'],
    "ActionEat": ["eat"],
    "ActionSmash": ["smash"],
    "ActionSpeak": ["speak"],
    "ActionPerform": ["perform"],
    "ActionClose": ["close"],
}

with open('./human_study/qualtrics/metadata/active_action_meta_data.json', 'r') as file:
    ACTION_DESCRIPTION = json.load(file)

with open('./human_study/qualtrics/metadata/social_action_meta_data.json', 'r') as file:
    ACTION_DESCRIPTION_SOCIAL = json.load(file)

with open('./control_test/20250116/meta_data.json', 'r') as file:
    ACTION_DESCRIPTION_ADD = json.load(file)

ACTION_DESCRIPTION = {**ACTION_DESCRIPTION, **ACTION_DESCRIPTION_SOCIAL, **ACTION_DESCRIPTION_ADD}

with open('./list_padding.json', 'r') as file:
    ACTION_VECTOR = json.load(file)

ALL_ACTIONS_LIST = ACTION_DESCRIPTION.keys()
print(ALL_ACTIONS_LIST)

# return: [[feature, label], [...]]
def question2vector(question_dict, ):
    # print(question_dict)
    print(question_dict["question_description"])
    choice = question_dict['user_chosen']['choice_metadata']
    if choice in ["They are equally active.", "I like them both equally.", "I dislike them both equally."]:
        action1 = action2vector(action_name=question_dict['user_rejected'][0]['choice_metadata'][:-4])
        action2 = action2vector(action_name=question_dict['user_rejected'][1]['choice_metadata'][:-4])
        feature = np.asarray(action1) - np.asarray(action2)
        label = 0
        return [[feature, label]]
    else:
        action1 = action2vector(action_name=question_dict['user_chosen']['choice_metadata'][:-4])
        action2 = None
        for choice in question_dict['user_rejected']:
            if choice['choice_metadata'] in ["They are equally active.", "I like them both equally.", "I dislike them both equally."]:
                continue
            else:
                action2 = action2vector(action_name=choice['choice_metadata'][:-4])
        feature = np.asarray(action1) - np.asarray(action2)
        vs_feature = np.asarray(action2) - np.asarray(action1)
        # handle social
        if "like" in question_dict["question_description"]:
            if ("dislike" in question_dict["question_description"] and "anxious" in question_dict["question_description"]):
                # selected is more social
                return [[feature, 1], [vs_feature, -1]]
            elif ("dislike" in question_dict["question_description"] and "outgoing" in question_dict["question_description"]):
                # selected is less social
                return [[feature, -1], [vs_feature, 1]]
            elif ("like" in question_dict["question_description"] and "anxious" in question_dict["question_description"]):
                # selected is less social
                return [[feature, -1], [vs_feature, 1]]
            elif ("dislike" in question_dict["question_description"] and "outgoing" in question_dict["question_description"]):
                # selected is more social
                return [[feature, 1], [vs_feature, -1]]
        # handle active
        return [[feature, 1], [vs_feature, -1]]

def in_attention_check(agent_pos, target_pos, agent_att, Att_R=None):

    if Att_R is not None:
        R=Att_R
    else:
        R=ATTENTION_RADIUS

    # target is position
    if (np.asarray(agent_pos) == target_pos).all():
        return True
    angle_entity = angle([1, 0], np.asarray(target_pos) - np.asarray(target_pos)) / 180
    # min(origin, complementary), min(origin, 2-origin)
    diff = abs(angle_entity - agent_att)
    if diff > 1:
        diff = 2 - diff
    if diff <= (R / 2 + 0.006):
        return True
    else:
        return False

def action2vector(action_name):
    action_data = ACTION_DESCRIPTION[action_name]
    agent1 = action_data['context']['agents'][0]
    agent2 = action_data['context']['agents'][1]
    in_attention = 0
    if in_attention_check(agent_pos=agent1['pos'], target_pos=agent2['pos'], agent_att=agent1['attention']):
        in_attention += 1
        if in_attention_check(agent_pos=agent2['pos'], target_pos=agent1['pos'], agent_att=agent2['attention']):
            in_attention += 1
    action_name_vec = ACTION_VECTOR[WORDS.index(ACTION2WORD[action_name[:action_name.find('_')]])]
    distance = 0
    if '_nd' in action_name:
        distance = 1
    elif '_fd' in action_name:
        distance = 2
    angle = 0
    if '_sa' in action_name:
        angle = 1
    elif '_la' in action_name:
        angle = 2
    related_to_heavy_obj = 0
    if 'dumbbell' in action_name:
        related_to_heavy_obj = 1
    hold_heavy_obj = 0
    if agent1.get("holding_ids") is not None:
        if len(agent1['holding_ids']):
            for obj in action_data['context']['objects']:
                if obj['id'] == agent1['holding_ids'][0]:
                    if obj['name'] == 'dumbbell':
                        hold_heavy_obj = 1
    return action_name_vec + [in_attention, distance, angle, related_to_heavy_obj, hold_heavy_obj]

def process_excel(excel_path):
    # 读取 Excel 文件
    df = pd.read_excel(excel_path, engine='openpyxl')

    X_diff_active = []
    y_diff_active = []

    X_diff_social = []
    y_diff_social = []


    # 按行迭代
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        if not isinstance(row_dict['rank_type'], str):
            continue
        for i in range(1, 65):
            question_str = row_dict[f"rank_q_{i}"]
            question_dict = json.loads(question_str)
            # print(question_dict)

            # attention check
            if (i) % 16 == 0:
                continue
            # try:
            data = (question2vector(question_dict))
            # except:
            #     continue
            if row_dict['rank_type'] == "active":
                for data_point in data:
                    X_diff_active.append(data_point[0])
                    y_diff_active.append(data_point[1])
            elif row_dict['rank_type'] == "social":
                for data_point in data:
                    X_diff_social.append(data_point[0])
                    y_diff_social.append(data_point[1])
    return X_diff_active, y_diff_active, X_diff_social, y_diff_social

class CustomDataset(Dataset):
    def __init__(self, X, y, transform=None):
        """
        初始化数据集类。
        
        参数:
        X (numpy.ndarray): 输入特征数据。
        y (numpy.ndarray): 标签数据。
        transform (callable, optional): 一个可选的变换函数，用于对数据进行预处理。
        """
        self.X = X
        self.y = y
        self.transform = transform

    def __len__(self):
        """
        返回数据集的大小。
        """
        return len(self.X)

    def __getitem__(self, idx):
        """
        根据索引 idx 获取数据集中的一个样本。
        
        参数:
        idx (int): 样本的索引。
        
        返回:
        sample (tuple): 包含输入特征和标签的元组。
        """
        sample = self.X[idx], self.y[idx]
        
        if self.transform:
            sample = self.transform(sample)
        
        return sample

if __name__ == '__main__':
    X_diff_active, y_diff_active, X_diff_social, y_diff_social = process_excel('./human_study/results/Rank Actions20250114_2140_parsed.xlsx')


    # # 示例数据：每行是一个数据点，每列是一个特征
    # X = np.array([
    #     [1, 2],
    #     [2, 3],
    #     [3, 4],
    #     [4, 5]
    # ])

    # # 成对比较结果及其频率
    # # (i, j, freq_greater, freq_equal, freq_less)
    # pairs = [
    #     (0, 1, 10, 2, 3),  # 10 人认为 0 > 1, 2 人认为 0 = 1, 3 人认为 0 < 1
    #     (1, 2, 8, 1, 5),
    #     (2, 3, 6, 4, 4)
    # ]

    # # 构建成对的数据集
    # X_diff = []
    # y_diff = []
    # sample_weight = []

    # for i, j, freq_greater, freq_equal, freq_less in pairs:
    #     total_votes = freq_greater + freq_equal + freq_less
    #     if freq_greater > freq_less:
    #         X_diff.append(X[i] - X[j])
    #         y_diff.append(1)
    #         X_diff.append(X[j] - X[i])
    #         y_diff.append(-1)
    #         weight = (freq_greater - freq_less) / total_votes
    #     elif freq_less > freq_greater:
    #         X_diff.append(X[j] - X[i])
    #         y_diff.append(1)
    #         X_diff.append(X[i] - X[j])
    #         y_diff.append(-1)
    #         weight = (freq_less - freq_greater) / total_votes
    #     else:
    #         continue  # 如果相等投票最多，可以选择忽略或处理

    #     sample_weight.append(weight)
    #     sample_weight.append(weight)

    X_diff_active = np.array(X_diff_active)
    y_diff_active = np.array(y_diff_active)

    X_diff_social = np.array(X_diff_social)
    y_diff_social = np.array(y_diff_social)
    # sample_weight = np.array(sample_weight)

    # 创建Rank SVM模型
    # model = make_pipeline(StandardScaler(), svm.SVC(kernel='poly', C=1.0))
    model = make_pipeline(StandardScaler(), svm.SVR(kernel='poly', C=1.0))

    # 训练模型，使用样本权重

    model.fit(X_diff_active, y_diff_active)

    model_social = make_pipeline(StandardScaler(), svm.SVR(kernel='poly', C=1.0))

    model_social.fit(X_diff_social, y_diff_social)

    # y_pre = model.predict(X_diff)

    # for i, action in enumerate(ALL_ACTIONS_LIST):
    #     if action[-1] == 's':
    #         continue
    #     action_vec = np.asarray(action2vector(action)).reshape(1, -1)

    # 首先收集所有action和对应的预测值
    action_scores = [(action, float(model.predict(np.asarray(action2vector(action)).reshape(1, -1))))
                    for action in ALL_ACTIONS_LIST 
                    if not action.endswith('s')]

    # 按照预测值排序
    sorted_actions = sorted(action_scores, key=lambda x: x[1])

    # 输出排序后的结果
    for action, score in sorted_actions:
        print(f"action: {action}, value: {score:.2f}")

    action_scores = [(action, float(model_social.predict(np.asarray(action2vector(action)).reshape(1, -1))))
                    for action in ALL_ACTIONS_LIST 
                    if not action.endswith('a')]

    # 按照预测值排序
    sorted_actions = sorted(action_scores, key=lambda x: x[1])

    # 输出排序后的结果
    for action, score in sorted_actions:
        print(f"action: {action}, value: {score:.2f}")





