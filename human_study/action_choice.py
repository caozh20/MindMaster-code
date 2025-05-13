# question_list_active store all active-dimension questions.
# question_list_social store all social-dimension questions.
# question id 从question_idx_init开始，先active的题（从1+question_idx_init开始），然后social的题
import pandas as pd
import numpy as np
# df = pd.read_csv("E:\\tom_lifeng\\NonverbalGame\\NonverbalGame\\control_test\\silent social game_July 30, 2024_04.24.csv",encoding="utf-8")
# df_array = np.array(df)#将pandas读取的数据转化为array
# df_list = df_array.tolist()#将数组转化为list

# print(df_list[0])
import csv

with open("D:\\文档\\GitHub\\NonverbalGame\\silent social game_July 30, 2024_19.44.csv", "r", encoding="utf-8") as file:
    csv_reader = csv.reader(file)
    rows = []
    for row in csv_reader:
        rows.append(row)

# csv_reader = csv.reader(open("D:\\文档\\GitHub\\NonverbalGame\\silent social game_July 30, 2024_19.44.csv"))
# rows = []
# for row in csv_reader:
# 	# print(row)
#     rows.append(row)

#rows[0] title
# from rows[3],开始记录的是数据，每增加一条数据，增加一个row

questions_column = [i for i,item in enumerate(rows[0]) if 'QID' in item]

QID = []
QVALUE = []
# 解析csv
for row in rows[3:]:
    answered_questions_idx = [idx for idx in questions_column if row[idx]]
    answered_questions_value = np.array(row)[np.array(answered_questions_idx)]
    question_idx_list = np.array(rows[0])[np.array(answered_questions_idx)]
    question_idx = [item.split(',')[0] for item in question_idx_list]
    QID.append(question_idx)
    QVALUE.append(answered_questions_value)

print(QID)
print(QVALUE)

ACTION_COMPARE_DICT = {}
ACTION_IDX_DICT = {}

with open("D:\\文档\\GitHub\\NonverbalGame\\qualtrics_test.txt", "r") as f:
    data = f.read()
    question_list_active = data.split("AAAAAAAA")[1:]

with open("D:\\文档\\GitHub\\NonverbalGame\\qualtrics_social_test.txt", "r") as f:
    data = f.read()
    question_list_social = data.split("AAAAAAAA")[1:]
question_idx_init = 2220
all_questions_list = question_list_active + question_list_social
answer = []
for idx_person, qid in enumerate(QID):
    qvalue = QVALUE[idx_person]
    anwser_per_person = []
    for i,v in enumerate(qid):
        idx_in_list = int(v.split("QID")[1]) - question_idx_init - 1
        question = all_questions_list[idx_in_list]
        
        question_content_element = question.split("\n")[1:-1] ###generally shoule be three element in one question
        
        corresponding_actions = []
        for ii,option in enumerate(question_content_element):
            if ii <=1 :
                action = (option.split('<div style=\'flex: 1; text-align: center; font-size: 20px;\'>')[1]).split('</div>')[0]
                corresponding_actions.append(action)

        before_action_name = corresponding_actions[0].strip()
        after_action_name = corresponding_actions[1].strip()

        # find new action
        if ACTION_COMPARE_DICT.get(before_action_name) is None:
            ACTION_COMPARE_DICT[before_action_name] = {}
            ACTION_COMPARE_DICT[before_action_name][after_action_name] = [0, 0, 0, v]
            if ACTION_IDX_DICT.get(before_action_name) is None:
                ACTION_IDX_DICT[before_action_name] = len(ACTION_IDX_DICT)
            if ACTION_IDX_DICT.get(after_action_name) is None:
                ACTION_IDX_DICT[after_action_name] = len(ACTION_IDX_DICT)
        elif ACTION_COMPARE_DICT[before_action_name].get(after_action_name) is None:
            ACTION_COMPARE_DICT[before_action_name][after_action_name] = [0, 0, 0, v]
            if ACTION_IDX_DICT.get(after_action_name) is None:
                ACTION_IDX_DICT[after_action_name] = len(ACTION_IDX_DICT)


        if int(qvalue[i]) == 1:
            ACTION_COMPARE_DICT[before_action_name][after_action_name][0] += 1
            # answer_string = corresponding_actions[0].strip()+'>'+corresponding_actions[1].strip()
            # print(corresponding_actions[0]+'>'+corresponding_actions[1])        
        elif int(qvalue[i]) == 2:
            ACTION_COMPARE_DICT[before_action_name][after_action_name][1] += 1
            # answer_string = corresponding_actions[0].strip()+'<'+corresponding_actions[1].strip()
            # print(corresponding_actions[0]+'<'+corresponding_actions[1])
        elif int(qvalue[i]) == 3:
            ACTION_COMPARE_DICT[before_action_name][after_action_name][2] += 1
            # answer_string = corresponding_actions[0].strip()+'='+corresponding_actions[1].strip()
            # print(corresponding_actions[0]+'='+corresponding_actions[1])

print(ACTION_COMPARE_DICT)
print(ACTION_IDX_DICT)

MIN_USEFUL_RATE = 0.6
possible_error_qids = []

for i, before_action_name in enumerate(ACTION_COMPARE_DICT.keys()):
    for j, after_action_name in enumerate(ACTION_COMPARE_DICT[before_action_name].keys()):
        vote_list = ACTION_COMPARE_DICT[before_action_name][after_action_name]
        rate = max(vote_list[:3]) / sum(vote_list[:3])
        if rate < MIN_USEFUL_RATE:
            possible_error_qids.append(vote_list[3])

print(possible_error_qids)

