import pickle
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# 将项目根目录添加到sys.path
sys.path.insert(0, project_root)
from core.intent import Intent
from core.const import ENTITY_SIZE_CONFIG

test_intent = Intent()
test_intent.ind_intent = ['put_onto', 4, 3]

AGENTS = [
    {
        'id': 1,
        'name': 'agent 1',
        'color': [0.35, 0.35, 0.25],
        'pos': [-600, -600],
        'attention': 0.3,
        'desire': {'active': 0, 'social': 2, 'helpful': 0},
        'intent': {'ind': ['put_onto', 4, 3], 'soc': None, 'comm': None, 'ref': None, 'type':"HIHU"},
        'rotate': 0.3
    },

    {
        'id': 2,
        'name': 'agent 2',
        'color': [0.35, 0.35, 0.5],
        'pos': [100, 0],
        'attention': -0.95,
        'desire': {'active': 2, 'social': 1, 'helpful': 2},
        'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
        'rotate': -0.95,
    }
]

OBJS = [
    {'id': 7,
     'name': 'box',
     'color': [1, 1, 240],
     'size': ENTITY_SIZE_CONFIG['box'],
     'pos': [600, -200],
     'rotate': 0.5,
     'is_container': True,
     'open': True,
     },

    {'id': 4,
     'name': 'cup',
     'color': [0.85, 0.15, 0.35],
     'size': ENTITY_SIZE_CONFIG['cup'],
     'pos': [500, 150],
     'rotate': 0.5,
     },

    {
        'id': 5,
        'name': 'chess',
        'color': [0.85, 0.15, 0.35],
        'size': ENTITY_SIZE_CONFIG['chess'],
        'pos': [400, 400],
        'rotate': 0.5
    },
    {
        'id': 6,
        'name': 'banana',
        'color': [0.85, 0.15, 0.35],
        'size': ENTITY_SIZE_CONFIG['banana'],
        'pos': [100, 400],
        'rotate': 0.5
    },
    {
        'id': 3,
        'name': 'table',
        'color': [0.85, 0.15, 0.35],
        'size': ENTITY_SIZE_CONFIG['table'],
        'pos': [-400, 150],
        'rotate': 0.5,
        'is_supporter': True
    }
]

LANDMARKS = []

with open("cuptotable.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
