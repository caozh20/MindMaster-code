import numpy as np
import math
import random
import time
from scipy.stats import vonmises
import sys
from operator import itemgetter
import base64
import io
from PIL import Image
import logging
import pygame

sys.path.append('../')

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = logging.FileHandler('app.log', mode='a')
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s, %(levelname)s, %(filename)15s, %(funcName)10s, %(lineno)3d] %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # 控制台处理器  
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s, %(levelname)s, %(filename)15s, %(funcName)10s, %(lineno)3d] %(message)s'
    ))
    logger.addHandler(console_handler)
    
    sys.stdout = LoggerWriter(logger, logging.INFO)
    sys.stderr = LoggerWriter(logger, logging.ERROR)

    return logger

class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message and message.strip():
            # 将字节字符串解码为普通字符串
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            self.logger.log(self.level, message.strip())
    
    def flush(self):
        pass

log = setup_logging()


# [-180, 180]
# The angle between the line segment and the positive direction of the x-axis
def angle(v1, v2):
    dx1 = v1[0]
    dy1 = v1[1]
    dx2 = v2[0]
    dy2 = v2[1]
    angle1 = math.atan2(dy1, dx1)
    angle1 = int(angle1 * 180/math.pi)
    angle2 = math.atan2(dy2, dx2)
    angle2 = int(angle2 * 180/math.pi)
    included_angle = angle2-angle1
    if included_angle > 180:
        included_angle -= 360
    elif included_angle < -180:
        included_angle += 360
    return included_angle


def angle_clip(angle):
    if angle > 1:
        angle -= 2
    elif angle < -1:
        angle += 2
    return angle


# 三点共线但不保证同向（从p1出发, p1p2, p1p3）
def colinear(p1, p2, p3, eps=1e-4):
    line1 = [j - i for i, j in zip(p1, p2)]
    line2 = [j - i for i, j in zip(p1, p3)]
    if line1[0] == line2[0] == 0:
        return True
    return abs(line1[1]/line1[0] - line2[1]/line2[0]) <= eps


# 三点共线且同向（从p1出发，p1p2, p1p3）
def same_direction(p1, p2, p3, eps=1e-4):
    line1 = [j - i for i, j in zip(p1, p2)]
    line2 = [j - i for i, j in zip(p1, p3)]
    cos_sim = np.dot(line1, line2) / (np.linalg.norm(line1) * np.linalg.norm(line2))
    return abs(cos_sim - 1) <= eps


def get_same_direction_objs(world, agent, target):
    objs = []
    for obj in world.objects:
        if obj.position is None:
            continue
        if same_direction(agent.position, target.position, obj.position):
            objs.append(obj.id)
    return objs


def check_visibility(agent, entity):

    angle_entity = angle([1, 0], entity.position - agent.position)/180
    if abs(angle_entity - agent.attention) < 0.1:
        return True
    else:
        return False


def dis(obj1, obj2):
    return np.sqrt(np.sum(np.square(np.asarray(obj1.position) - np.asarray(obj2.position))))


def euclidean_dist(pos1, pos2):
    return np.sqrt(np.sum(np.square(np.asarray(pos1) - np.asarray(pos2))))


def include(obj, set):
    for o in set:
        if o.name == obj.name:
            return True
    return False


def cross(p1,p2,p3): # 叉积判定
    x1=p2[0]-p1[0]
    y1=p2[1]-p1[1]
    x2=p3[0]-p1[0]
    y2=p3[1]-p1[1]
    return x1*y2-x2*y1


def segment(p1,p2,p3,p4): # 判断两线段是否相交
    #矩形判定，以l1、l2为对角线的矩形必相交，否则两线段不相交
    if(max(p1[0],p2[0])>=min(p3[0],p4[0]) #矩形1最右端大于矩形2最左端
    and max(p3[0],p4[0])>=min(p1[0],p2[0]) #矩形2最右端大于矩形1最左端
    and max(p1[1],p2[1])>=min(p3[1],p4[1]) #矩形1最高端大于矩形2最低端
    and max(p3[1],p4[1])>=min(p1[1],p2[1])): #矩形2最高端大于矩形1最低端
        if(cross(p1,p2,p3)*cross(p1,p2,p4)<=0
        and cross(p3,p4,p1)*cross(p3,p4,p2)<=0):
            D=1
        else:
            D=0
    else:
        D=0
    return D


# find the edge loc of the target object
def edge_location(src_pos, src_size, target, W):
    target_loc, target_size = target.position, target.size
    x, y = target_loc
    if isinstance(target_size, int):
        w = h = target_size*2
    else:
        w, h = target_size
    up = (x, y + h/2 + src_size)
    down = (x, y - h/2 - src_size)
    left = (x - w/2 - src_size, y)
    right = (x + w/2 + src_size, y)
    dis = lambda src, trg: np.sqrt(np.sum(np.square(np.asarray(src_pos) - np.asarray(trg))))
    locs = [up, down, left, right]

    filtered_locs = []
    for edge_type in range(4):
        # only Object has edge occupied
        # filter the edge loc that has been occupied
        if hasattr(target, 'edge_occupied') and edge_type not in target.edge_occupied:
            filtered_locs.append([edge_type, locs[edge_type]])
    if len(filtered_locs) == 0:
        filtered_locs = [(0, up), (1, down), (2, left), (3, right)]

    distances = [dis(src_pos, loc) for loc in locs]
    filtered_dists = [(edge_type, dis(src_pos, loc)) for edge_type, loc in filtered_locs]
    filtered_dists = sorted(filtered_dists, key=itemgetter(1), reverse=False)

    if hasattr(target, 'is_supporter') and target.is_supporter:
        # left center
        return 2, np.asarray(locs[2])
    elif 'shelf' in target.name:
        occupied = W.location_has_been_occupied(locs[1])
        if occupied[0]:
            entity = occupied[1]

            if isinstance(entity.size, int):
                t_w = t_h = entity.size * 2
            else:
                t_w, t_h = target_size
            return 1, np.asarray(locs[1]) + (t_w//2 + src_size, 0)
        return 1, np.asarray(locs[1])
    else:
        edge_type = filtered_dists[0][0]
        for e, p in filtered_locs:
            if e == edge_type:
                return edge_type, p


def attention_location(target, dis=200):
    target_loc, target_angle = target.position, target.attention
    x, y = target_loc
    x += np.cos(target_angle * math.pi) * dis
    y += np.sin(target_angle * math.pi) * dis
    return np.asarray([x, y])


# def agent_left_with_offset(agent, target, more=0):
#     # anti clockwise rotate 90
#     left_center_angle = agent.rotate + 0.5
#     if left_center_angle > 1:
#         left_center_angle -= 2
#     radius = agent.size + (target.size[0] + more)//2
#     x0, y0 = agent.position
#     x = np.cos(left_center_angle * np.pi) * radius
#     y = np.sin(left_center_angle * np.pi) * radius
#     return np.asarray([x+x0, y+y0])


def agent_left_upper_with_offset(agent, target, more=0):
    # anti clockwise rotate (0.35/0.5)*90 = 63
    left_center_angle = agent.rotate + 0.35
    if left_center_angle > 1:
        left_center_angle -= 2
    radius = agent.size + (target.size[0] + more)//2
    x0, y0 = agent.position
    x = np.cos(left_center_angle * np.pi) * radius
    y = np.sin(left_center_angle * np.pi) * radius
    return np.asarray([x+x0, y+y0])


def agent_left_no_offset(agent):
    left_center_angle = agent.rotate + 0.5
    if left_center_angle > 1:
        left_center_angle -= 2
    radius = agent.size
    x0, y0 = agent.position
    x = np.cos(left_center_angle * np.pi) * radius
    y = np.sin(left_center_angle * np.pi) * radius
    return np.asarray([x + x0, y + y0])


def agent_right_no_offset(agent):
    right_center_angle = agent.rotate - 0.5
    if right_center_angle < -1:
        right_center_angle += 2
    radius = agent.size
    x0, y0 = agent.position
    x = np.cos(right_center_angle * np.pi) * radius
    y = np.sin(right_center_angle * np.pi) * radius
    return np.asarray([x + x0, y + y0])


def frame_to_b64(frame):
    file_object = io.BytesIO()
    img = Image.fromarray(frame)
    img.save(file_object, 'PNG')
    frame_data = "data:image/png;base64," + base64.b64encode(file_object.getvalue()).decode('ascii')
    return frame_data

def compress_image(screen: pygame.Surface, quality=85):
    """
    Compress the Pygame screen surface to a JPEG image and return as a byte array.
    
    :param screen: Pygame screen surface
    :param quality: JPEG quality (1-100)
    :return: Compressed image as a byte array
    """
    # Compression ratio: 24.11%
    t0 = time.time()

    # method1
    # image = Image.fromarray(np.frombuffer(pygame.image.tostring(screen, "RGB"), dtype=np.uint8).reshape((1400, 1400, 3)))
    image = Image.frombytes("RGB", screen.get_size(), pygame.image.tostring(screen, "RGB"))
    compressed_buffer = io.BytesIO()
    image.save(compressed_buffer, format="JPEG", quality=quality)
    compressed_buffer.seek(0)
    compressed_image = Image.open(compressed_buffer)

    # print(f"compress time: {time.time() - t0}")
    return compressed_image

# todo, 0906, 待验证
def compress_and_encode(screen: pygame.Surface, quality=85):
    # 直接从Pygame surface创建PIL Image
    image = Image.frombytes("RGB", screen.get_size(), pygame.image.tostring(screen, "RGB"))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode('ascii')

def rel_pos_in_shelf(shelf, entity):
    shelf_pos, shelf_size = shelf.position, shelf.size
    entity_size = entity.size
    x = shelf_pos[0]
    y = shelf_pos[1] - shelf_size[1]//2 + entity_size[1]//2 + 20
    return np.asarray([x, y])


# def rel_pos_on_table(table, entity):
#     table_pos, table_size = table.position, table.size
#     entity_size = entity.size
#     x = table_pos[0]
#     y = table_pos[1] + table_size[1]//2 + entity_size[1]//2 + 50
#     return np.asarray([x, y])


if __name__ == '__main__':
    # print(angle([1, 0], np.asarray([-500, 0]) - np.asarray([200, -200])) / 180)
    # print(same_direction([1, 1], [2, 2], [3, 3]))
    class Agent:
        pass
    class Target:
        pass
    # fake_agent = Agent()
    # fake_agent.size = 50
    # fake_agent.rotate = 0.5
    # fake_agent.position = [400, -300]
    # fake_target = Target()
    # fake_target.size = [93, 80]
    # print(agent_left_with_offset(fake_agent, target=fake_target))
    # target - current
    # print(angle([1, 0], np.asarray([-250, -350]) - np.asarray([400, 400])) / 180)

    fake_agent = Agent()
    fake_agent.position = [-236.48845796, 273.62054649]
    fake_agent.size = 50
    fake_agent.rotate = 0
    fake_target = Target()
    fake_target.position = [-144.98845796, 273.62054649]
    fake_target.size = [83, 78]
    fake_target.rotate = 0
    import sys
    sys.path.append('.')
    sys.path.append('..')
    from core.entity_utils import Is_Near
    print(Is_Near(fake_agent, fake_target, None))

