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

import torch
from torch.utils.data import Dataset, DataLoader
import os, os.path
import argparse
import pickle
import pandas as pd
import csv
from human_study.recover_data import recover_world
from experiment_codes.llms.parse_state import parse_current_attention, parse_world_state
import re
from parse_relation_state import extract_relation_state 
from core.agent import Agent
from core.entity import Object, Landmark

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

def csv_to_video(csv_file_path):
    with open(csv_file_path, "rb") as f:
        data_raw_tmp=pd.read_pickle(f)

    data_raw_tmp=data_raw_tmp.reset_index(drop=True)
    objects = data_raw_tmp['world_objs'].apply(pickle.loads)
    landmarks = data_raw_tmp['world_landmarks'].apply(pickle.loads)
    agents = data_raw_tmp['world_agents'].apply(pickle.loads)
    actions = data_raw_tmp['user_agent_action'].apply(lambda x: pickle.loads(x) if x is not None else None)
    inferred_intents = data_raw_tmp['other_high_intent_estimated']
    intents_your_high = data_raw_tmp['your_high_intent']

    world = recover_world(agents=agents[0], objects=objects[0], landmarks=landmarks[0])

    all_frame_list = []

    for action in actions:
        print(action.name())
        world.step([action])
        frame_list = world.render()
        all_frame_list.extend(frame_list)
    
    render_frames(all_frame_list)

if __name__ == "__main__":
    csv_to_video("./data/grouped_data_pickle/date_2024-11-03_users_赵文菁_邓润_game_17709_scenario_2_get_3.pkl")
