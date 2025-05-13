import random
from copy import deepcopy
import json
from typing import Dict
import numpy as np


# class Desire():
#     def __init__(self):
#         # [0, 1
#         self.active=0 # -1, 0, 1
#         self.social=0 # -1, 0, 1
#         self.helpful=0 # -2, -1, 0, 1, 2
#
#     def __call__(self):
#         return [self.active, self.social, self.helpful]


desire_config = {
    "active":
        {
            1: "energetic and prefer physical motion",
            0: "not energetic and prefer no physical motion"
        },
    "social":
        {
            1: "prefer to engage in social communication and interactions with other agents, and prefer to seek help",
            0: "prefer not to engage in social communication or interaction with other agents"
        },
    "helpful":
        {
            1: "willing to help others",
            0: "don't want to help others"
        }
}


class Desire:
    def __init__(self, active=0, social=0, helpful=0):
        # [0, 1] continuous value
        # 0 means prefer no physical actions, 1 means prefer physical actions
        # self.active = max(0, min(1, active))
        self.active = active
        # [0, 1]
        # 0 means prefer no social interactions, 1 means prefer social interactions
        # self.social = max(0, min(1, social))
        self.social = social
        # [0, 1]
        # 0 means prefer no helpful actions, 1 means prefer helpful actions
        # self.helpful = max(0, min(1, helpful))
        self.helpful = helpful

    def __call__(self):
        return [round(self.active, 2), round(self.social, 2), round(self.helpful, 2)]

    # def parse(self):
    #     return f'{self.active} in active dimension, {self.social} in social dimension, {self.helpful} in helpful dimension'

    def parse(self):
        # 从最低值到最高值逐渐搜索
        def get_description(value, thresholds: Dict[float, str]):
            for threshold, description in thresholds.items():
                if value <= threshold:
                    return description
            return ''

        helpful_desc = get_description(self.helpful, {
            -1: 'harmful',
            0: 'unhelpful',
            1: 'helpful',
            2: 'very helpful'
        })

        active_desc = get_description(self.active, {
            0: 'inactive',
            0.5: 'neutral in active dimension',
            1: 'active'
        })

        social_desc = get_description(self.social, {
            0: 'unsocial',
            0.5: 'neutral in social dimension',
            1: 'social'
        })

        return f'{helpful_desc}, {active_desc}, {social_desc}'.strip(', ')

    def symbolize(self):

        symbols = []

        if self.active < 0.5:
            symbols.append(0)
        else:
            symbols.append(1)

        if self.social < 0.5:
            symbols.append(0)
        else:
            symbols.append(1)

        # todo 0806
        # -0.5, harmful
        # 0, unhelpful
        # 0.5, helpful
        # 1, very helpful
        if self.helpful < 0:
            symbols.append(0)
        else:
            symbols.append(1)

        return symbols

    @staticmethod
    def sample_dict():
        return {"active": random.choice([0, .5, 1]),
                "social": random.choice([0, .5, 1]),
                "helpful": random.choice([-1, 0, 1, 2])}

    @classmethod
    def sample(cls):
        return cls(**cls.sample_dict())

    def clone(self):
        return deepcopy(self)

    def to_dict(self):
        return {
            'active': float(self.active),
            'social': float(self.social),
            'helpful': float(self.helpful)
        }

    def to_list(self):
        return [float(self.active), float(self.social), float(self.helpful)]

    @classmethod
    def from_dict(cls, data):
        return cls(
            active=data.get('active', 0),
            social=data.get('social', 0),
            helpful=data.get('helpful', 0)
        )

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, data):
        return cls.from_dict(json.loads(data))
