from copy import deepcopy
import numpy as np
from core.const import NEAR_DIS

from utils.base import *


def _no_obstacle_check(agent, target, W):
    """
    :return, True: means pass the check there is no landmark
    """
    # target is held by a lock container
    if isinstance(target, Object) and not target.can_be_observed(W) and target.id not in agent.belief.all_ids:
        return False

    target_pos = target.position if isinstance(target, Entity) else np.asarray(target)
    if isinstance(target, Landmark):
        return True

    # if isinstance(target, Entity):
    #     id = None
    #     if isinstance(target, Landmark):
    #         id = target.id
    for landmark in W.landmarks:
        # if id is not None:
        #     if landmark.id == target.id:
        #         continue
        obstacle_line1 = [
            [landmark.position[0] - landmark.size[0] / 2, landmark.position[1] - landmark.size[1] / 2],
            [landmark.position[0] + landmark.size[0] / 2, landmark.position[1] + landmark.size[1] / 2]]
        obstacle_line2 = [
            [landmark.position[0] - landmark.size[0] / 2, landmark.position[1] + landmark.size[1] / 2],
            [landmark.position[0] + landmark.size[0] / 2, landmark.position[1] - landmark.size[1] / 2]]
        if segment(agent.position, target_pos, obstacle_line1[0], obstacle_line1[1]):
            return False
        if segment(agent.position, target_pos, obstacle_line2[0], obstacle_line2[1]):
            return False
    return True


def Is_Near(entity_1, entity_2, W, offset=5):

    # print(entity_1.name, entity_2.name)
    # print("entity1_rotate", entity_1.rotate)
    # print("entity2_rotate", entity_2.rotate)
    # 判断两个物体是否邻近
    # 由于这是物理属性，如果传入id的话应该可以直接从world读取
    if isinstance(entity_1, int):
        entity_1 = W.retrieve_by_id(entity_1)
    if isinstance(entity_2, int):
        entity_2 = W.retrieve_by_id(entity_2)

    if np.allclose(entity_1.position, entity_2.position):
        return True

    if hasattr(entity_2, 'being_contained') and len(entity_2.being_contained) > 0:
        # if dis(entity_1, W.retrieve_by_id(entity_2.being_contained[0])) < dis(entity_1, entity_2):
        entity_2 = W.retrieve_by_id(entity_2.being_contained[0])

    # For agent
    if isinstance(entity_1.size, int):
        w1, h1 = entity_1.size, entity_1.size
    else:
        w1, h1 = entity_1.size[0] / 2, entity_1.size[1] / 2
    if isinstance(entity_2.size, int):
        w2, h2 = entity_2.size, entity_2.size
    else:
        w2, h2 = entity_2.size[0] / 2, entity_2.size[1] / 2
    # 互换
    # temp = w1
    # w1 = h1
    # h1 = temp
    # temp = w2
    # w2 = h2
    # h2 = temp
    rotate1 = entity_1.rotate * math.pi
    rotate2 = entity_2.rotate * math.pi
    # 将entity_1适度扩大
    w1 += NEAR_DIS
    h1 += NEAR_DIS
    # 先拿出entity_1的四个顶点
    theta = math.atan(h1/w1)
    R = math.sqrt(w1**2 + h1**2)
    beta = rotate1 + theta
    # print("entity1_theta", theta)
    # print("entity1_R", R)
    x_list = []
    y_list = []
    x_list.append(entity_1.position[0] + R * math.sin(beta))
    y_list.append(entity_1.position[1] - R * math.cos(beta))
    beta = beta + math.pi - 2 * theta
    x_list.append(entity_1.position[0] + R * math.sin(beta))
    y_list.append(entity_1.position[1] - R * math.cos(beta))
    beta = beta + 2 * theta
    x_list.append(entity_1.position[0] + R * math.sin(beta))
    y_list.append(entity_1.position[1] - R * math.cos(beta))
    beta = beta + math.pi - 2 * theta
    x_list.append(entity_1.position[0] + R * math.sin(beta))
    y_list.append(entity_1.position[1] - R * math.cos(beta))
    # # 最后一个防止数组越界
    beta = rotate1 + theta
    x_list.append(entity_1.position[0] + R * math.sin(beta))
    y_list.append(entity_1.position[1] - R * math.cos(beta))
    # 先拿出entity_2的四个顶点
    theta = math.atan(h2 / w2)
    R = math.sqrt(w2 ** 2 + h2 ** 2)
    # print("entity2_theta", theta)
    # print("entity2_R", R)
    beta = rotate2 + theta
    x_list_2 = []
    y_list_2 = []
    x_list_2.append(entity_2.position[0] + R * math.sin(beta))
    y_list_2.append(entity_2.position[1] - R * math.cos(beta))
    beta = beta + math.pi - 2 * theta
    x_list_2.append(entity_2.position[0] + R * math.sin(beta))
    y_list_2.append(entity_2.position[1] - R * math.cos(beta))
    beta = beta + 2 * theta
    x_list_2.append(entity_2.position[0] + R * math.sin(beta))
    y_list_2.append(entity_2.position[1] - R * math.cos(beta))
    beta = beta + math.pi - 2 * theta
    x_list_2.append(entity_2.position[0] + R * math.sin(beta))
    y_list_2.append(entity_2.position[1] - R * math.cos(beta))
    # # 最后一个防止数组越界
    beta = rotate2 + theta
    x_list_2.append(entity_2.position[0] + R * math.sin(beta))
    y_list_2.append(entity_2.position[1] - R * math.cos(beta))
    #提取出entity_1被拓展之后的边线
    xc = entity_1.position[0]
    yc = entity_1.position[1]
    A_list_1 = []
    B_list_1 = []
    C_list_1 = []
    rotate1 = entity_1.rotate
    rotate2 = entity_2.rotate
    # print("entity1_rotate", rotate1)
    # print("entity2_rotate", rotate2)
    if -1 < rotate1 < -0.5 or 0 < rotate1 < 0.5:
        B_list_1 += [1, 1, 1, 1]
        A1 = -abs(math.tan(rotate1 * math.pi))
        A2 = -1 / A1
        A_list_1 += [A1, A1, A2, A2]
        C1 = -A1 * xc - yc + w1 * math.sqrt(A1 ** 2 + 1)
        C2 = -A1 * xc - yc - w1 * math.sqrt(A1 ** 2 + 1)
        C3 = -A2 * xc - yc + h1 * math.sqrt(A2 ** 2 + 1)
        C4 = -A2 * xc - yc - h1 * math.sqrt(A2 ** 2 + 1)
        C_list_1 += [C1, C2, C3, C4]
    elif -0.5 < rotate1 < 0 or 0.5 < rotate1 < 1:
        B1 = 1
        B2 = 1
        B_list_1 += [B1, B1, B2, B2]
        A1 = abs(math.tan(rotate1 * math.pi))
        A2 = -1 / A1
        A_list_1 += [A1, A1, A2, A2]
        C1 = -A1 * xc - yc + h1 * math.sqrt(A1 ** 2 + 1)
        C2 = -A1 * xc - yc - h1 * math.sqrt(A1 ** 2 + 1)
        C3 = -A2 * xc - yc + w1 * math.sqrt(A2 ** 2 + 1)
        C4 = -A2 * xc - yc - w1 * math.sqrt(A2 ** 2 + 1)
        C_list_1 += [C1, C2, C3, C4]
    elif -0.51 <= rotate1 <= -0.49 or 0.49 <= rotate1 <= 0.51:
        B1 = 0
        A1 = 1
        C1 = -(xc + w1)
        C2 = -(xc - w1)
        B2 = 1
        A2 = 0
        C3 = -(yc + h1)
        C4 = -(yc - h1)
        A_list_1 += [A1, A1, A2, A2]
        B_list_1 += [B1, B1, B2, B2]
        C_list_1 += [C1, C2, C3, C4]
    else:
        B1 = 0
        A1 = 1
        C1 = -(xc + h1)
        C2 = -(xc - h1)
        B2 = 1
        A2 = 0
        C3 = -(yc + w1)
        C4 = -(yc - w1)
        A_list_1 += [A1, A1, A2, A2]
        B_list_1 += [B1, B1, B2, B2]
        C_list_1 += [C1, C2, C3, C4]
    # 提取entity_2的边线
    xc = entity_2.position[0]
    yc = entity_2.position[1]
    A_list = []
    B_list = []
    C_list = []
    if -1 < rotate2 < -0.5 or 0 < rotate2 < 0.5:
        B_list = [1, 1, 1, 1]
        A1 = -abs(math.tan(rotate2 * math.pi))
        A2 = -1/A1
        A_list += [A1, A1, A2, A2]
        C1 = -A1 * xc - yc + w2 * math.sqrt(A1 ** 2+1)
        C2 = -A1 * xc - yc - w2 * math.sqrt(A1 ** 2+1)
        C3 = -A2 * xc - yc + h2 * math.sqrt(A2 ** 2+1)
        C4 = -A2 * xc - yc - h2 * math.sqrt(A2 ** 2 + 1)
        C_list += [C1, C2, C3, C4]
    elif -0.5 < rotate2 < 0 or 0.5 < rotate2 < 1:
        B1 = 1
        B2 = 1
        B_list += [B1, B1, B2, B2]
        A1 = abs(math.tan(rotate2 * math.pi))
        A2 = -1 / A1
        A_list += [A1, A1, A2, A2]
        C1 = -A1 * xc - yc + h2 * math.sqrt(A1 ** 2 + 1)
        C2 = -A1 * xc - yc - h2 * math.sqrt(A1 ** 2 + 1)
        C3 = -A2 * xc - yc + w2 * math.sqrt(A2 ** 2 + 1)
        C4 = -A2 * xc - yc - w2 * math.sqrt(A2 ** 2 + 1)
        C_list += [C1, C2, C3, C4]
    elif -0.51 <= rotate2 <= -0.49 or 0.49 <= rotate2 <= 0.51:
        B1 = 0
        A1 = 1
        C1 = -(xc + w2)
        C2 = -(xc - w2)
        B2 = 1
        A2 = 0
        C3 = -(yc + h2)
        C4 = -(yc - h2)
        A_list += [A1, A1, A2, A2]
        B_list += [B1, B1, B2, B2]
        C_list += [C1, C2, C3, C4]
    else:
        B1 = 0
        A1 = 1
        C1 = -(xc + h2)
        C2 = -(xc - h2)
        B2 = 1
        A2 = 0
        C3 = -(yc + w2)
        C4 = -(yc - w2)
        A_list += [A1, A1, A2, A2]
        B_list += [B1, B1, B2, B2]
        C_list += [C1, C2, C3, C4]
    # 依次判断entity_1的边线与entity_2的是否有交点
    # 如果有，再根据entity_1的顶点确定交点是否在有效范围内
    for i in range(4):
        for j in range(4):
            A1 = A_list_1[i]
            B1 = B_list_1[i]
            C1 = C_list_1[i]
            A2 = A_list[j]
            B2 = B_list[j]
            C2 = C_list[j]
            # 近似平行
            if -0.0005 < A1 * B2 - A2 * B1 < 0.0005:
                continue
            # 发现有交点
            x = (C2 * B1 - C1 * B2) / (A1 * B2 - A2 * B1)
            y = (A1 * C2 - C1 * A2) / (B1 * A2 - A1 * B2)
            # print("交点为", x, y)
            temp_x = []
            temp_y = []
            temp = []
            for k in range(4):
                # print(A1 * x_list[k] + B1 * y_list[k] + C1)
                # if -5 < A1 * x_list[k] + B1 * y_list[k] + C1 < 5:
                #     temp_x.append(x_list[k])
                #     temp_y.append(y_list[k])
                temp.append(abs(A1 * x_list[k] + B1 * y_list[k] + C1))
            temp = np.asarray(temp)
            index = np.argsort(temp)
            # print(index)
            temp_x.append(x_list[index[0]])
            temp_x.append(x_list[index[1]])
            temp_y.append(y_list[index[0]])
            temp_y.append(y_list[index[1]])
            # print(temp)
            # print(index)
            # print(temp_x)
            # print(temp_y)
            temp_x_2 = []
            temp_y_2 = []
            temp_2 = []
            for k in range(4):
                # print(A2 * x_list_2[k] + B2 * y_list_2[k] + C2)
                # if -10 < A2 * x_list_2[k] + B2 * y_list_2[k] + C2 < 10:
                #     temp_x_2.append(x_list_2[k])
                #     temp_y_2.append(y_list_2[k])
                temp_2.append(abs(A2 * x_list_2[k] + B2 * y_list_2[k] + C2))
            temp_2 = np.asarray(temp_2)
            index = np.argsort(temp_2)
            temp_x_2.append(x_list_2[index[0]])
            temp_x_2.append(x_list_2[index[1]])
            temp_y_2.append(y_list_2[index[0]])
            temp_y_2.append(y_list_2[index[1]])
            # print(temp_2)
            # print(index)
            # print(temp_x_2)
            # print(temp_y_2)
            # 此时拿到了两个位于直线上的x
            # 交点应该位于这两个x之间
            if min(temp_x[0], temp_x[1]) - offset < x < max(temp_x[0], temp_x[1]) + offset and \
                    min(temp_x_2[0], temp_x_2[1]) - offset < x < max(temp_x_2[0], temp_x_2[1]) + offset and \
                    min(temp_y[0], temp_y[1]) - offset < y < max(temp_y[0], temp_y[1]) + offset and \
                    min(temp_y_2[0], temp_y_2[1]) - offset < y < max(temp_y_2[0], temp_y_2[1]) + offset:
                # print(entity_1.name, "near", entity_2.name)
                return True
    # 方便临近检测
    # if dis(entity_1, entity_2) < max(w1, h1) + max(w2, h2) + NEAR_DIS:
    #     return True
    # 如果没有检测到碰撞，则返回否
    return False

from core.entity import Object, Landmark, Entity