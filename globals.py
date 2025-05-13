import pygame
import threading
from typing import Dict

# screen = pygame.display.set_mode((1400, 1400), flags=pygame.HIDDEN)
# screen.fill([255, 255, 255])

mutex = threading.Lock()

# common global variables
# key: uuid, value: username (email)
global_user_dict = {}
# for u2m only
global_user_args = {}
# for u2u only
# key, uuid, value: user_state (ClientUserState instance)
global_user_u2u_args = {}
# key: uuid, value: room (ScenarioRoom instance)
global_rooms_dict = None
global_fix_time_per_round = False

global_scenario_record = {}
global_user_task_dict = {}

global_task_id = 0
def increment_task_id():
    global global_task_id
    global_task_id += 1
    return global_task_id

