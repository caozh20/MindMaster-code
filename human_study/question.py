import glob
import os
import random
import sys
import re
import copy
sys.path.append(".")
sys.path.append("../")
from control_test.sample_action import KEY_ACTION_TO_SHOW

# string_name = '["MoveToAttention","agent_2"]'
# string_name = '["RotateTo","[50, 100]"]'
def name_to_sentence(string_name):
    s=str(copy.deepcopy(string_name[-15:-2]))
    item_list = string_name.split(',')
    if item_list[0][2:-1] == "RotateTo" and "[" in item_list[1]:
        action_item_list = re.findall('[A-Z][^A-Z]*', item_list[0][2:-1])
        return action_item_list[0].lower()+ " "+action_item_list[1].lower()+ " "+s
        
    cnt = 0
    action = None
    for item in item_list:
        if cnt == 0:
            action = item[2:-1]
            action_item_list = action.split("..")
            if len(action_item_list) == 1:
                # print(action_item_list[0])
                action_item_list = re.findall('[A-Z][^A-Z]*', action_item_list[0])
                # print(action_item_list)
                action_name = action_item_list[0].lower()
                if action_name == "speak":
                    return action_name+" "+ item_list[1][:-1]
                if action_name == "point":
                    return action_name + " "+action_item_list[1].lower()+" "+item_list[1][1:-2]
                if action_name =="play":
                    return action_name+ " "+item_list[1][1:-1]+" with agent_2"
                if action_name == "follow":
                    return action_name+ " "+item_list[1][1:-2]+"'s pointing"
                if action_name == "move" and len(action_item_list) == 3:
                    return action_name+" "+action_item_list[1].lower()+" "+item_list[1][1:-2]+"'s attention field"
                if action_name in ["move","rotate"] and len(action_item_list) == 2:
                    return action_name+" "+action_item_list[1].lower()+" "+item_list[1][1:-2]
                if action_name in ["grab","smash","eat","open","close"]:
                    return action_name+" "+item_list[1][1:-2]
                if action_name in ["nod","shake","wave"]:
                    return action_name+" "+action_item_list[1].lower()[0:-1] #+" to "+item_list[1][1:-2]
                if action_name == "unlock":
                    return action_name+" "+item_list[1][1:-1]+" with "+item_list[2][1:-2]
                if action_name == "perform":
                    return action_name+ " "+item_list[1][1:-2]+"ing"
            else:
                action_name = action_item_list[0].lower()
                prep_name = action_item_list[1].lower()
                if action_name == "put" and prep_name == "onto" and item_list[2][1:-2] != "ground":
                    return action_name+ " "+item_list[1][1:-1]+" "+prep_name+" "+item_list[2][1:-2]
                if action_name == "put" and prep_name == "into":
                    return action_name+ " "+item_list[1][1:-1]+" "+prep_name+" "+item_list[2][1:-2]
                if action_name == "give" and prep_name == "to":
                    return action_name + " " + item_list[1][1:-1]+" "+prep_name+" "+item_list[2][1:-2]
                if action_name == "put" and prep_name == "down":
                    return action_name+ " "+item_list[1][1:-2]+" down on the ground"
                
                
        cnt = cnt + 1
        # elif cnt==len(item_list):
        #     param_last = item[1:-2]
        # else:
        #     param = item[1:-1]

# print(string_name[-11:-2])       
# print(name_to_sentence(string_name))

def generate_qualtrics_txt_active(questions, filename, gif_filenames, ATT_CHECK_LEVEL0 = None, ATT_CHECK_LEVEL1 = None):
    # active dimension, 每个action都会和其他的action配对
    with open(filename, 'w', encoding='utf-8') as file:
        # 不同动作间作为Action 对比
        for i, choiceA in enumerate(gif_filenames) :
            # if i > 0:
            #     continue
            for j, choiceB in enumerate(gif_filenames):
                if choiceA == choiceB:
                    continue
                if j < i:
                    continue
                
                if ATT_CHECK_LEVEL0 and ATT_CHECK_LEVEL1:
                    action_name_A = choiceA.split('_')[0]
                    action_name_B = choiceB.split('_')[0]
                    if (
                        (action_name_A in ATT_CHECK_LEVEL0 and 'nd' in choiceA) and (action_name_B in ATT_CHECK_LEVEL1 and 'fd' in choiceB) or
                        (action_name_A in ATT_CHECK_LEVEL1 and 'fd' in choiceA) and (action_name_B in ATT_CHECK_LEVEL0 and 'nd' in choiceB)
                    ):
                        continue
                
                name_choice_A = transform(choiceA)
                name_choice_B = transform(choiceB)
                # file.write(f'Which action is more active?\n')
                file.write(f'AAAAAAAA\n')
                
                name_to_sentenceA = name_to_sentence(name_choice_A)
                name_to_sentenceB = name_to_sentence(name_choice_B)
                
                # file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://github.com/caozh20/gif_for_ssg/blob/main/{choiceA}?raw=true' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A}    </div></div>\n")
                # https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay
                # file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://github.com/caozh20/gif_for_ssg/blob/main/{choiceB}?raw=true' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B}    </div></div>\n")
                
                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{choiceA}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A} <br><br><span style=\"color:#3498db;\"> {name_to_sentenceA} </span>   </div></div>\n")
                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{choiceB}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B} <br><br><span style=\"color:#3498db;\"> {name_to_sentenceB} </span>  </div></div>\n")
                
                
                # file.write('两个动作active程度相同。 They are equally active. \n')
                file.write('They are equally active. \n')

                # file.write(f'[[PageBreak]]\n')
        
        # 同类动作作为Attention check
        # for i, choiceA in enumerate(PURE_MOVE) :
        #     for j, choiceB in enumerate(gif_filenames):
        #         if choiceA == choiceB:
        #             continue
        #         file.write(f'MC_{i}_{j}. Which action is more active?\n')

        #         file.write(f'\n')
                
        #         file.write(f"<div style='width: 600px'><div style='float: left;width: 50%;'><img src='https://github.com/caozh20/gif_for_ssg/blob/main/{choiceA}?raw=true' style='height: 90%; width: 90%;'></div>\n")

        #         file.write(f"<div style='width: 600px'><div style='float: left;width: 50%;'><img src='https://github.com/caozh20/gif_for_ssg/blob/main/{choiceB}?raw=true' style='height: 90%; width: 90%;'></div>\n")
                
        #         file.write('They are equally active. \n')

        #         file.write(f'\n')
        #         file.write(f'\n')

        #         file.write(f'[[PageBreak]]\n')
        # for i, question in enumerate(questions):
        #     file.write(f'MC{i}. Which action is more active?\n')

        #     file.write(f'\n')
            
        #     file.write(f"<div style='width: 600px'><div style='float: left;width: 50%;'><img src='https://github.com/caozh20/gif_for_ssg/blob/main/move_to_box_far.gif?raw=true' style='height: 90%; width: 90%;'></div>\n")

        #     file.write(f"<div style='width: 600px'><div style='float: left;width: 50%;'><img src='https://github.com/caozh20/gif_for_ssg/blob/main/move_to_box_middle.gif?raw=true' style='height: 90%; width: 90%;'></div>\n")
            
        #     file.write('They are equally active. \n')


def generate_qualtrics_txt_social(questions, filename, gif_filenames,ACTION_SOCIAL_LEVEL0, ATT_CHECK_LEVEL0 = None, ATT_CHECK_LEVEL1 = None):
    with open(filename, 'w', encoding='utf-8') as file:
        # 对social_level0中的action，内部不进行采样
        for i, choiceA in enumerate(gif_filenames) :
            # if i > 0:
            #     continue
            for j, choiceB in enumerate(gif_filenames):
                if choiceA == choiceB:
                    continue
                action_name_A = choiceA.split('_')[0]
                action_name_B = choiceB.split('_')[0]
                if action_name_A in ACTION_SOCIAL_LEVEL0 and action_name_B in ACTION_SOCIAL_LEVEL0:
                    continue
                if j < i:
                    continue
                
                
                if ATT_CHECK_LEVEL0 and ATT_CHECK_LEVEL1:
                    action_name_A = choiceA.split('_')[0]
                    action_name_B = choiceB.split('_')[0]
                    if (
                        (action_name_A in ATT_CHECK_LEVEL0 and 'nd' in choiceA) and (action_name_B in ATT_CHECK_LEVEL1 and 'nd' in choiceB) or
                        (action_name_A in ATT_CHECK_LEVEL1 and 'nd' in choiceA) and (action_name_B in ATT_CHECK_LEVEL0 and 'nd' in choiceB)
                    ):
                        continue
                
                
                
                name_choice_A = transform(choiceA)
                name_choice_B = transform(choiceB)
                # file.write(f'Which action is more social?\n')
                name_to_sentenceA = name_to_sentence(name_choice_A)
                name_to_sentenceB = name_to_sentence(name_choice_B)
                
                
                file.write(f'AAAAAAAA\n')
                
                # file.write(f'\n')
                
                # file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://github.com/caozh20/gif_for_ssg/blob/main/{choiceA}?raw=true' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A}    </div></div>\n")

                # file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://github.com/caozh20/gif_for_ssg/blob/main/{choiceB}?raw=true' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B}    </div></div>\n")
                
                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{choiceA}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceA} </span>  </div></div>\n")

                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{choiceB}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceB} </span>  </div></div>\n")
                
                
                # file.write('两个动作social程度相同。 They are equally social. \n')
                file.write('I like them both equally. \n')

                # file.write(f'\n')
                # file.write(f'\n')

                # file.write(f'[[PageBreak]]\n')


def transform(gif_name):
    gif_no_suffix = gif_name[0:-12]
    string = '['
    idx = 0
    gif_name_elements = gif_no_suffix.split("_")
    # print(gif_name_elements)
    while idx<len(gif_name_elements):
        if idx > 1 and gif_name_elements[idx] in ['1','2','3','4','5'] :
            string = string[0:-2] + "_" + gif_name_elements[idx]+'"'+','
        elif idx == 0 and 'Action' in gif_name_elements[idx]:
            string = string +'"' +KEY_ACTION_TO_SHOW[gif_name_elements[idx]] +'"'+ ','
            if "NodHead" in gif_name_elements[idx] or "ShakeHead" in gif_name_elements[idx] or "WaveHand" in gif_name_elements[idx]:
                string = string[0:-1]+']'
                return string
        else:
            string = string +'"'+ gif_name_elements[idx]+'"'+','
        
        if "agent" in gif_name_elements[idx]:
            idx = idx + 1
        
        idx = idx + 1
    
    # if 'ActionPutDown' in gif_name_elements[0]:
    #     string = string+ "\"ground\"" + ']'
    string = string[0:-1]+']'
    if 'ActionRotateTo' in gif_name_elements[0] and '[' in gif_name_elements[1]:
        s=str(copy.deepcopy(string[-11:-1]))
        s_list = s.split(",")
        prev = copy.deepcopy(string[0:-11])
        string = prev + s_list[0][0]+"X:"+s_list[0][1:]+", Y:"+s_list[1][1:]+']'
    
    return string



# 示例数据
questions = [
    {
        "id": "q1",
        "text": "This is a multiple choice question. With one value recoded.",
        "choices": [
            {"text": "choice a\nwith text on\nmultiple lines"},
            {"text": "choice b"},
            {"text": "choice c"},
            {"text": "N/A with recode 99", "recode": 99}
        ]
    }
]

def find_gif_files_using_glob(directory):
    # 构建搜索模式来匹配所有的 .gif 文件
    pattern = os.path.join(directory, '**', '*.gif')
    
    # 使用 glob.glob 查找所有匹配的文件，recursive=True 允许递归搜索子目录
    gif_files = glob.glob(pattern, recursive=True)

    # 只获取文件名
    gif_filenames = [os.path.basename(gif) for gif in gif_files]
    
    return gif_filenames

# 指定要搜索的目录
# directory_path = './assets/resize_gifs'
# directory_path = "./save_gif_prepared"
directory_path_active = "./control_test/20240929/active"


# 调用函数并打印结果
gif_filenames_active = find_gif_files_using_glob(directory_path_active)
# for filename in gif_filenames:
#     print(filename)

# PURE_MOVE = ["move_to_box_far.gif", "move_to_box_middle.gif", "move_to_box_near.gif", "move_to_shelf_far.gif", "move_to_shelf_middle.gif", "move_to_shelf_near.gif"]

# MOVE_WITH = ["move_to_box_with_cup_far.gif", "move_to_box_with_cup_middle.gif", "move_to_box_with_cup_near.gif", "move_to_box_with_key_far.gif", "move_to_box_with_key_middle.gif", "move_to_box_with_key_near.gif"]

# # 输出文件名
filename_active = 'qualtrics_active_20240929.txt'

# # 生成文件
generate_qualtrics_txt_active(questions, filename_active, gif_filenames_active)

print("active文件已生成。")

directory_path_social = "./control_test/20240929/social"
gif_filenames_social = find_gif_files_using_glob(directory_path_social)

ACTION_SOCIAL_LEVEL0 = ['ActionRotateTo','ActionGrab','ActionOpen','ActionClose','ActionPutOnto','ActionPutDown','ActionUnlock','ActionEat','ActionSmash','ActionMoveTo','ActionExplore','ActionPutInto']

filename_social = 'qualtrics_social_20240929.txt'
generate_qualtrics_txt_social(questions, filename_social, gif_filenames_social, ACTION_SOCIAL_LEVEL0)

print("social文件已生成")

ATT_CHECK_ACTIVE_LEVEL1 = ['ActionMoveTo','ActionMoveToAttention']
ATT_CHECK_ACTIVE_LEVEL0 = ['ActionPerform','ActionSpeak','ActionOpen','ActionClose','ActionGiveTo','ActionEat','ActionUnlock']

ATT_CHECK_SOCIAL_LEVEL0 = ['ActionGrab','ActionOpen','ActionClose','ActionPutOnto','ActionPutDown','ActionUnlock','ActionEat','ActionPutInto']
ATT_CHECK_SOCIAL_LEVEL1 = ['ActionSpeak','ActionWaveHand','ActionMoveToAttention']


# def generate_qualtrics_txt_active_att_check(filename_att_active, ATT_CHECK_LEVEL0, ATT_CHECK_LEVEL1, gif_filenames_active):
#     with open(filename_att_active, 'w', encoding='utf-8') as file:
#         # 对social_level0中的action，内部不进行采样
#         for i, choiceA in enumerate(gif_filenames_active) :
#             # if i > 0:
#             #     continue
#             for j, choiceB in enumerate(gif_filenames_active):
#                 if choiceA == choiceB:
#                     continue
#                 # print(choiceA+" "+choiceB)
#                 # print("==========")
#                 action_name_A = choiceA.split('_')[0]
#                 action_name_B = choiceB.split('_')[0]
#                 if action_name_A not in ATT_CHECK_LEVEL0 or action_name_B not in ATT_CHECK_LEVEL1:
#                     continue
#                 if 'nd' not in choiceA:
#                     continue
#                 if 'fd' not in choiceB:
#                     continue
                
#                 rdn = random.randint(0,1)
                
#                 if rdn == 1:
#                     tmp_A = choiceA
#                     tmp_B = choiceB
#                 else:
#                     tmp_A = choiceB
#                     tmp_B = choiceA
                
#                 # print(choiceB+' > '+choiceA)
#                 name_choice_A = transform(tmp_A)
#                 name_choice_B = transform(tmp_B)
#                 # file.write(f'Which action is more social?\n')
#                 name_to_sentenceA = name_to_sentence(name_choice_A)
#                 name_to_sentenceB = name_to_sentence(name_choice_B)
                
                
                    
                
#                 file.write(f'AAAAAAAA\n')
                
#                 # file.write(f'\n')
                
#                 file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_A}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceA} </span>  </div></div>\n")

#                 file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_B}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceB} </span>  </div></div>\n")
                
#                 # file.write('两个动作active程度相同。 They are equally active. \n')
#                 file.write('They are equally active. \n')
                
#                 file.write(f'Answer:{choiceB} \n')

#                 # file.write(f'\n')
#                 # file.write(f'\n')

#                 # file.write(f'[[PageBreak]]\n')
    
# def generate_qualtrics_txt_social_att_check(filename_att_social, ATT_CHECK_LEVEL0, ATT_CHECK_LEVEL1, gif_filenames_social):
#     with open(filename_att_social, 'w', encoding='utf-8') as file:
#         # 对social_level0中的action，内部不进行采样
#         for i, choiceA in enumerate(gif_filenames_social) :
#             # if i > 0:
#             #     continue
#             for j, choiceB in enumerate(gif_filenames_social):
#                 if choiceA == choiceB:
#                     continue
#                 action_name_A = choiceA.split('_')[0]
#                 action_name_B = choiceB.split('_')[0]
#                 if action_name_A not in ATT_CHECK_LEVEL0 or action_name_B not in ATT_CHECK_LEVEL1:
#                     continue
#                 if 'nd' not in choiceA:
#                     continue
#                 if 'nd' not in choiceB:
#                     continue
                
#                 print(choiceB+' > '+choiceA)
                
#                 rdn = random.randint(0,1)
                
#                 if rdn == 1:
#                     tmp_A = choiceA
#                     tmp_B = choiceB
#                 else:
#                     tmp_A = choiceB
#                     tmp_B = choiceA
                
#                 name_choice_A = transform(tmp_A)
#                 name_choice_B = transform(tmp_B)
#                 # file.write(f'Which action is more social?\n')
                
#                 name_to_sentenceA = name_to_sentence(name_choice_A)
#                 name_to_sentenceB = name_to_sentence(name_choice_B)
                    
#                 file.write(f'AAAAAAAA\n')
                
#                 # file.write(f'\n')
                
#                 file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_A}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceA} </span>  </div></div>\n")

#                 file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_B}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceB} </span>  </div></div>\n")
                
#                 # file.write('两个动作social程度相同。 They are equally social. \n')
#                 file.write('I like them both equally. \n')
                
#                 file.write(f'Anwser:{choiceB} \n')

#                 # file.write(f'\n')
#                 # file.write(f'\n')

#                 # file.write(f'[[PageBreak]]\n')

def generate_qualtrics_txt_active_att_check(filename_att_active, gif_filenames_active_large, gif_filenames_active_small):
    with open(filename_att_active, 'w', encoding='utf-8') as file:
        # 对social_level0中的action，内部不进行采样
        for i, choiceA in enumerate(gif_filenames_active_small) :
            # if i > 0:
            #     continue
            for j, choiceB in enumerate(gif_filenames_active_large):
                # print(choiceA+" "+choiceB)
                # print("==========")
                action_name_A = choiceA.split('_')[0]
                action_name_B = choiceB.split('_')[0]
                
                rdn = random.randint(0,1)
                
                if rdn == 1:
                    tmp_A = choiceA
                    tmp_B = choiceB
                else:
                    tmp_A = choiceB
                    tmp_B = choiceA
                
                # print(choiceB+' > '+choiceA)
                name_choice_A = transform(tmp_A)
                name_choice_B = transform(tmp_B)
                # file.write(f'Which action is more social?\n')
                name_to_sentenceA = name_to_sentence(name_choice_A)
                name_to_sentenceB = name_to_sentence(name_choice_B)
                
                
                    
                
                file.write(f'AAAAAAAA\n')
                
                # file.write(f'\n')
                
                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_A}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceA} </span>  </div></div>\n")

                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_B}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceB} </span>  </div></div>\n")
                
                # file.write('两个动作active程度相同。 They are equally active. \n')
                file.write('They are equally active. \n')
                
                file.write(f'Answer:{choiceB} \n')

                # file.write(f'\n')
                # file.write(f'\n')

                # file.write(f'[[PageBreak]]\n')
    
def generate_qualtrics_txt_social_att_check(filename_att_social, gif_filenames_social_large, gif_filenames_social_small):
    with open(filename_att_social, 'w', encoding='utf-8') as file:
        # 对social_level0中的action，内部不进行采样
        for i, choiceA in enumerate(gif_filenames_social_small) :
            # if i > 0:
            #     continue
            for j, choiceB in enumerate(gif_filenames_social_large):
                
                action_name_A = choiceA.split('_')[0]
                action_name_B = choiceB.split('_')[0]
                
                
                rdn = random.randint(0,1)
                
                if rdn == 1:
                    tmp_A = choiceA
                    tmp_B = choiceB
                else:
                    tmp_A = choiceB
                    tmp_B = choiceA
                
                name_choice_A = transform(tmp_A)
                name_choice_B = transform(tmp_B)
                # file.write(f'Which action is more social?\n')
                
                name_to_sentenceA = name_to_sentence(name_choice_A)
                name_to_sentenceB = name_to_sentence(name_choice_B)
                    
                file.write(f'AAAAAAAA\n')
                
                # file.write(f'\n')
                
                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_A}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_A}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceA} </span>  </div></div>\n")

                file.write(f"<div style='width: 600px; display: flex; align-items: center;'>    <div style='flex: 1;'>        <img src='https://mindmaster-roleplay.s3.ap-northeast-2.amazonaws.com/gif_for_mmrplay/{tmp_B}' style='width: 100%; height: auto;'>    </div>    <div style='flex: 1; text-align: center; font-size: 20px;'>        {name_choice_B}  <br><br><span style=\"color:#3498db;\"> {name_to_sentenceB} </span>  </div></div>\n")
                
                # file.write('两个动作social程度相同。 They are equally social. \n')
                file.write('I like them both equally. \n')
                
                file.write(f'Anwser:{choiceB} \n')

                # file.write(f'\n')
                # file.write(f'\n')

                # file.write(f'[[PageBreak]]\n')

# from shutil import copy
def collect_img(LEVEL,gifs,path,directory_path_org):
    for i, name in enumerate(gifs):
        action_name = name.split('_')[0]
        if action_name in LEVEL:
            path_org = os.path.join(directory_path_org,name)
            path_new = os.path.join(path,name)
            copy(path_org,path_new)
            
    
directory_path = "./control_test/20240929/total_w_black/"
path1 = "./control_test/20240929/attention_check/attention_check_active/large_active/"
path2 = "./control_test/20240929/attention_check/attention_check_active/small_active/"
path3 = "./control_test/20240929/attention_check/attention_check_social/large_social/"
path4 = "./control_test/20240929/attention_check/attention_check_social/small_social/"

# collect_img(ATT_CHECK_ACTIVE_LEVEL0,gif_filenames_active,path2,directory_path)
# collect_img(ATT_CHECK_ACTIVE_LEVEL1,gif_filenames_active,path1,directory_path)
# collect_img(ATT_CHECK_SOCIAL_LEVEL0,gif_filenames_social,path4,directory_path)
# collect_img(ATT_CHECK_SOCIAL_LEVEL1,gif_filenames_social,path3,directory_path)



filename_att_active = "qualtric_attention_check_active_20240929.txt"
print(len(gif_filenames_active))
# generate_qualtrics_txt_active_att_check(filename_att_active, ATT_CHECK_ACTIVE_LEVEL0, ATT_CHECK_ACTIVE_LEVEL1, gif_filenames_active)
active_large=find_gif_files_using_glob(path1)
active_small=find_gif_files_using_glob(path2)
# print(active_large)
# print(active_small)
generate_qualtrics_txt_active_att_check(filename_att_active,active_large,active_small)
print("active attention check 文件生成完成")

filename_att_social = "qualtric_attention_check_social_20240929.txt"
social_large=find_gif_files_using_glob(path3)
social_small=find_gif_files_using_glob(path4)
generate_qualtrics_txt_social_att_check(filename_att_social, social_large, social_small)
# generate_qualtrics_txt_social_att_check(filename_att_social, ATT_CHECK_SOCIAL_LEVEL0, ATT_CHECK_SOCIAL_LEVEL1, gif_filenames_social)
print("social attention check 文件生成完成")

# generate_qualtrics_txt_active(questions, filename_active, gif_filenames_active, ATT_CHECK_ACTIVE_LEVEL0, ATT_CHECK_ACTIVE_LEVEL1)
# print("active文件已生成。")

# generate_qualtrics_txt_social(questions, filename_social, gif_filenames_social, ACTION_SOCIAL_LEVEL0, ATT_CHECK_SOCIAL_LEVEL0, ATT_CHECK_SOCIAL_LEVEL1)
# print("social文件已生成")




