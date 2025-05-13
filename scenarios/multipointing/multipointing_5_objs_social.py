import pickle
import sys

sys.path.append("..")
sys.path.append("../../")

from core.intent import Intent

test_intent = Intent()
test_intent.ind_intent = ['get', 3, None]

AGENTS = [{'id': 1,
           'name': 'agent 1',
           'pos': [-500, -500],
           'attention': 0.12,
           # 'desire': {'active': 1, 'social': 1, 'helpful': 0},
           'desire': {'active': 0, 'social': 1, 'helpful': 0},
           # 'desire': {'active': 1, 'social': 0, 'helpful': 0},
           'intent': {
               # 'ind': None,
               # 'soc': ['request_help', 2, test_intent],
               'ind': test_intent.ind_intent,
               'soc': None,
               'comm': None,
               'ref': None,
               'type': 'HIHU'
           },
           'rotate': 0.12
           },
          {'id': 2,
           'name': 'agent 2',
           'desire': {'active': 1, 'social': 1, 'helpful': 1},
           # 'belief_obj_ids': [3],
           # 'intent': {'ind': ['explore', None, None], 'soc': None, 'comm': None, 'ref': None},
           'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type': 'LILU'},
           'pos': [400, -300],
           'attention': -0.9,
           'rotate': -0.9}]

OBJS = [{'id': 3,
         'name': 'cup',
         'size': [64, 46],
         'pos': [-100, 300],
         'rotate': 0.5
         },
        {
            'id': 4,
            'name': 'chess',
            'size': [83, 78],
            'pos': [-400, 200],
            'rotate': 0.5
        },
        {
            'id': 6,
            'name': 'banana',
            'size': [78, 69],
            'pos': [100, 300],
            'rotate': 0.5
        },
        {
            'id': 7,
            'name': 'table',
            'size': [150, 160],
            'pos': [500, 250],
            'rotate': 0.5,
            'is_supporter': True
        }
        ]

LANDMARKS = []

with open("multipointing.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
