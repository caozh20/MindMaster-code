# MyLibrary.py
import numpy as np
import math
import pygame
from pygame.locals import *
from PIL import Image
from core.const import DOWN_SCALED_ALPHA


# prints text using the supplied font
def print_text(font, x, y, text, color=(255, 255, 255)):
    imgText = font.render(text, True, color)
    # req'd when function moved into MyLibrary
    screen = pygame.display.get_surface()
    screen.blit(imgText, (x, y))


def convert_angle(angle):
    while angle < -180 or angle > 180:
        if angle > 180:
            angle -= 360
        elif angle < -180:
            angle += 360
    return angle


def convert_action_pos_right(pos, angle, image_rect, action_rect):
    angle = convert_angle(angle)
    pos = list(pos)
    # current center
    agent_center = np.array([pos[0] + image_rect.w/2, pos[1] + image_rect.h/2])
    # 50: agent radius
    dis_1 = np.sqrt(2*np.square(50))
    dis_2 = 30
    dis_3 = 54

    if -90 <= angle and angle < 0:
        rect_left_top = np.array(
            [agent_center[0]+dis_1*math.cos(math.radians(45+angle)), agent_center[1]-dis_1*math.sin(math.radians(45+angle))])
        rect_left_bottom = np.array(
            [rect_left_top[0]-dis_3*math.sin(-math.radians(angle)), rect_left_top[1]+dis_3*math.cos(-math.radians(angle))])
        return [rect_left_bottom[0], rect_left_top[1]]
    elif -180 <= angle and angle < -90:
        rect_left_top = np.array(
            [agent_center[0]+dis_1*math.sin(math.radians(45-angle)), agent_center[1]-dis_1*math.cos(math.radians(45-angle))])
        rect_right_top = np.array(
            [rect_left_top[0]-dis_2*math.sin(math.radians(-angle-90)), rect_left_top[1]+dis_2*math.cos(math.radians(-angle-90))])
        return [rect_left_top[0] - action_rect.w, rect_right_top[1] - action_rect.h]
    elif 90 < angle and angle < 180:
        rect_left_top = np.array(
            [agent_center[0]-dis_1*math.cos(math.radians(135-angle)), agent_center[1]-dis_1*math.sin(math.radians(135-angle))])
        rect_left_bottom = np.array(
            [rect_left_top[0]+dis_3*math.cos(math.radians(angle-90)), rect_left_top[1]-dis_3*math.cos(math.radians(angle-90))])
        # return rect_left_top
        return [rect_left_bottom[0] - action_rect.h, rect_left_top[1] - action_rect.w]
    elif 0 <= angle and angle <= 90:
        rect_left_top = np.array(
            [agent_center[0]+dis_1*math.cos(math.radians(45+angle)), agent_center[1]-dis_1*math.sin(math.radians(45+angle))])
        rect_right_top = np.array(
            [rect_left_top[0]+dis_2*math.cos(math.radians(angle)), rect_left_top[1]-dis_2*math.sin(math.radians(angle))])
        return [rect_left_top[0], rect_right_top[1]]
    # print(angle)


def render_agent_right_pos(render_agent, offset=25):
    # 50 means agent radius
    fix_distance = 50 + offset
    # minus 90 means right hand
    direction = render_agent.rotation - 90
    direction = 360 + direction + 90
    x0, y0 = render_agent.rect.centerx, render_agent.rect.centery
    # offset relative to center of agent
    x = np.cos(direction/180*np.pi) * fix_distance
    y = -np.sin(direction/180*np.pi) * fix_distance
    return x0+x, y+y0


def render_agent_left_pos(render_agent, offset=25):
    # 50 means agent radius
    fix_distance = 50 + offset
    # plus 90 means left hand
    direction = render_agent.rotation + 90
    # direction = 360 + direction + 90
    x0, y0 = render_agent.rect.centerx, render_agent.rect.centery
    # offset relative to center of agent
    x = -np.sin(direction/180*np.pi) * fix_distance
    y = -np.cos(direction/180*np.pi) * fix_distance
    return x0+x, y+y0


def render_agent_left_upper_pos(render_agent, offset=23):
    # 50 means agent radius
    fix_distance = 50 + offset
    # plus 90 means left hand
    direction = render_agent.rotation + 63 + np.arctan(33/73)*180/np.pi
    # direction = 360 + direction + 90
    centerx, centery = render_agent.rect.centerx, render_agent.rect.centery
    # offset relative to center of agent
    x = -np.sin(direction/180*np.pi) * fix_distance
    y = -np.cos(direction/180*np.pi) * fix_distance
    return centerx+x, centery+y


def render_agent_middle_left_pos(render_agent, offset=23):
    # 50 means agent radius
    fix_distance = 50 + offset
    # plus 90 means left hand
    direction = render_agent.rotation + 90 + np.arctan(33/73)*180/np.pi
    # direction = 360 + direction + 90
    centerx, centery = render_agent.rect.centerx, render_agent.rect.centery
    # offset relative to center of agent
    x = -np.sin(direction/180*np.pi) * fix_distance
    y = -np.cos(direction/180*np.pi) * fix_distance
    return centerx+x, centery+y


def convert_action_pos_left(pos, angle, image_rect, action_rect):
    angle = convert_angle(angle)
    pos = list(pos)
    # current center
    agent_center = np.array([pos[0] + image_rect.w/2, pos[1] + image_rect.h/2])
    # 50: agent radius
    dis_1 = np.sqrt(2*np.square(50))
    dis_2 = 30
    dis_3 = 54

    if -90 <= angle and angle < 0:
        rect_right_top = np.array(
            [agent_center[0]-dis_1*math.sin(math.radians(45+angle)), agent_center[1]-dis_1*math.cos(math.radians(45+angle))])
        rect_right_bottom = np.array(
            [rect_right_top[0]-dis_3*math.sin(-math.radians(angle)), rect_right_top[1]+dis_3*math.cos(-math.radians(angle))])
        return [rect_right_top[0]-action_rect.w, rect_right_bottom[1]-action_rect.h]
    elif -180 <= angle and angle < -90:
        rect_right_top = np.array(
            [agent_center[0]+dis_1*math.sin(math.radians(-45-angle)), agent_center[1]-dis_1*math.cos(math.radians(-45-angle))])
        rect_left_top = np.array(
            [rect_right_top[0]+dis_2*math.sin(math.radians(-angle-90)), rect_right_top[1]-dis_2*math.cos(math.radians(-angle-90))])
        return [rect_left_top[0] - action_rect.w, rect_right_top[1] - action_rect.h]
    elif 90 < angle and angle < 180:
        rect_right_top = np.array(
            [agent_center[0]-dis_1*math.sin(math.radians(135-angle)), agent_center[1]+dis_1*math.cos(math.radians(135-angle))])
        rect_right_bottom = np.array(
            [rect_right_top[0]+dis_3*math.cos(math.radians(angle-90)), rect_right_top[1]-dis_3*math.sin(math.radians(angle-90))])
        # return rect_left_top
        return [rect_right_top[0], rect_right_bottom[1]]
    elif 0 <= angle and angle <= 90:
        rect_right_top = np.array(
            [agent_center[0]-dis_1*math.sin(math.radians(45+angle)), agent_center[1]-dis_1*math.cos(math.radians(45+angle))])
        rect_left_top = np.array(
            [rect_right_top[0]-dis_2*math.cos(math.radians(angle)), rect_right_top[1]+dis_2*math.sin(math.radians(angle))])
        return [rect_left_top[0], rect_right_top[1]]


# MySprite class extends pygame.sprite.Sprite
class MySprite(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # extend the base Sprite class
        self.master_image = None
        self.frame = 0
        self.frame_width = 1
        self.frame_height = 1
        self.first_frame = 0
        self.old_frame = 0
        self.last_frame = 0
        self.columns = 1
        self.last_time = 0
        self.attention = 4
        self.rotation = 0
        self.nodding = False
        self.screen = None

        # for astar
        self.random_flag = False
        self.astar_cache = []
        self.last_pos = [0, 0]

        # for avoid
        self.avoid = []
        self.avoid_dis = 0
        # show name and id
        self.id = 0
        self.name = ""
        # 决定其 rendering 顺序
        self.first_appear = False
        # 决定是否降低 alpha 值呈现
        self.isin_attention = True

        # 是否再次出现，即当前时刻在视野，上一时刻不再
        self.reappear = False


    # X property
    def _getx(self): return self.rect.x
    def _setx(self, value): self.rect.x = value
    X = property(_getx, _setx)

    # Y property
    def _gety(self): return self.rect.y
    def _sety(self, value): self.rect.y = value
    Y = property(_gety, _sety)

    # position property
    def _getpos(self): return self.rect.topleft
    def _setpos(self, pos): self.rect.topleft = pos
    position = property(_getpos, _setpos)

    def load(self, filename, width, height, columns):
        self.filename = filename
        self.master_image = pygame.image.load(filename).convert_alpha()
        # self.master_image = pygame.image.fromstring(data, size, mode)
        self.frame_width = width
        self.frame_height = height
        self.rect = Rect(0, 0, width, height)
        self.columns = columns
        # try to auto-calculate total frames
        rect = self.master_image.get_rect()
        self.last_frame = (rect.width // width) * (rect.height // height) - 1
        frame_x = (self.frame % self.columns) * self.frame_width
        frame_y = (self.frame // (self.columns)) * self.frame_height
        rect = Rect(frame_x, frame_y, self.frame_width, self.frame_height)
        self.image = self.master_image.subsurface(rect)
        self.raw_image = self.master_image.subsurface(rect)
        self.image_copy = self.image.copy()
        # self.default_alpha = self.master_image.get_alpha()
        self.default_alpha = 255
        self.saved_alpha = pygame.surfarray.pixels_alpha(self.image).copy()

    def update(self):
        self.frame = self.first_frame
        if self.frame > self.last_frame:
            self.frame = self.first_frame
        # build current frame only if it changed
        if self.frame != self.old_frame:
            frame_x = (self.frame % self.columns) * self.frame_width
            frame_y = (self.frame // (self.columns)) * self.frame_height
            rect = Rect(frame_x, frame_y, self.frame_width, self.frame_height)
            self.raw_image = self.master_image.subsurface(rect)
            self.old_frame = self.frame
        self.rotate(self.rotation)

    def rotate(self, angle):
        pos = self.position
        image = self.image
        image_raw = self.raw_image
        self.rotation = angle
        self.blitRotate(self.screen, image, image_raw, pos, self.rotation)

    def blitRotate(self, surf, image, image_raw, pos, angle):
        image_rect = image.get_rect(topleft=(pos[0], pos[1]))
        rotated_image_center = (
            pos[0] + image_rect.w/2, pos[1] + image_rect.h/2)
        rotated_image = pygame.transform.rotate(image_raw, angle)
        rotated_image_rect = rotated_image.get_rect(
            center=rotated_image_center)
        # surf.blit(rotated_image, rotated_image_rect)
        self.image = rotated_image
        self.image_copy = rotated_image.copy()
        self.rect = rotated_image_rect

    def get_raw_top_left(self):
        image_rect = self.image.get_rect(topleft=(self.position[0], self.position[1]))
        rotated_image_center = (
            self.position[0] + image_rect.w / 2, self.position[1] + image_rect.h / 2)
        raw_image_rect = self.raw_image.get_rect(topleft=(self.position[0], self.position[1]))
        top_left = (
            rotated_image_center[0] - raw_image_rect.w / 2, rotated_image_center[1] - raw_image_rect.h / 2
        )
        return top_left

    def get_raw_left_mid(self):
        image_rect = self.image.get_rect(topleft=(self.position[0], self.position[1]))
        rotated_image_center = (
            self.position[0] + image_rect.w / 2, self.position[1] + image_rect.h / 2)
        raw_image_rect = self.raw_image.get_rect(topleft=(self.position[0], self.position[1]))
        left = (rotated_image_center[0] - raw_image_rect.w / 2, rotated_image_center[1])
        return left

    def get_raw_down_mid(self):
        image_rect = self.image.get_rect(topleft=(self.position[0], self.position[1]))
        rotated_image_center = (
            self.position[0] + image_rect.w / 2, self.position[1] + image_rect.h / 2)
        raw_image_rect = self.raw_image.get_rect(topleft=(self.position[0], self.position[1]))
        down = (rotated_image_center[0], rotated_image_center[1] + raw_image_rect.h/2)
        return down

    def get_raw_right(self):
        image_rect = self.image.get_rect(topleft=(self.position[0], self.position[1]))
        rotated_image_center = (
            self.position[0] + image_rect.w / 2, self.position[1] + image_rect.h / 2)
        raw_image_rect = self.raw_image.get_rect(topleft=(self.position[0], self.position[1]))
        right = (rotated_image_center[0] + raw_image_rect.w, rotated_image_center[1])
        return right

    def get_adj_right(self, x_offset, y_offset=0):
        # 右前方
        direction = self.rotation - 45
        # fix_distance = 50 * np.sqrt(2)
        # 50 + offset (20)
        fix_distance = 50 * np.sqrt(2)
        x0, y0 = self.rect.centerx, self.rect.centery
        # offset relative to center of agent
        x = -np.sin(direction / 180 * np.pi) * fix_distance
        y = -np.cos(direction / 180 * np.pi) * fix_distance
        # print(f'{self.id}: {self.rotation}')
        if 45 <= self.rotation <= 135 or -315 <= self.rotation <= -225:
            return x0 + x - x_offset, y + y0 - y_offset
        return x0 + x, y + y0

    # 设置透明度值 (0-255，0 完全透明，255 完全不透明)
    def downscale_alpha(self):
        new_alpha = self.default_alpha // DOWN_SCALED_ALPHA
        new_image = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        new_image.fill((255, 255, 255, new_alpha))
        self.image = self.image_copy.copy()
        self.image.blit(new_image, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def print_image_pixels_with_alpha(self):
        # 将图像表面转换为一个numpy数组，包括alpha通道
        pixel_array = pygame.surfarray.pixels_alpha(self.image)
        # 打印像素值
        print(pixel_array[80-2:80+2, 110-2:110+2])
        # 确保更新后释放对表面的锁定
        pygame.surfarray.use_arraytype("numpy")

    # 设置透明度值 (0-255，0 完全透明，255 完全不透明)
    def reset_alpha(self):
        self.image = self.image_copy.copy()


class Point(object):
    def __init__(self, x, y):
        self.__x = x
        self.__y = y

    # X property
    def getx(self): return self.__x
    def setx(self, x): self.__x = x
    x = property(getx, setx)

    # Y property
    def gety(self): return self.__y
    def sety(self, y): self.__y = y
    y = property(gety, sety)

    def __str__(self):
        return "{X:" + "{:.0f}".format(self.__x) + \
            ",Y:" + "{:.0f}".format(self.__y) + "}"
