import pickle
import os, sys
sys.path.append("..")
sys.path.append("../../")

AGENTS = [
{
            'id': 1,
            'name': 'agent 1',
            'color': [0.35, 0.35, 0.5],
            'pos': [100, -300],
            'attention': 0.794,
            'desire':{'active': 0, 'social': 1, 'helpful': 0},
            'intent':[
                      # {'ind': ['play', 3], 'soc': None, 'comm': None,  'ref': None,'type': 'HILU'},
                      {'ind': ['move_to', [100, -300]], 'soc': None, 'comm': None,  'ref': None, 'type': 'HILU'},
                      {'ind': ['gaze_follow', 2], 'soc': None, 'comm': None,  'ref': None, 'type': 'HILU'},
            ],
            'rotate': 0.794,
            # 'belief_obj_ids': [3]
            },
            {
            'id': 2,
            'name': 'agent 2',
            'color': [0.35,0.35,0.25],
            'pos': [100, 300],
            'attention': 0.7,
            # 'desire':{'active': 0, 'social': 1, 'helpful': 0},
            'desire':{'active': 1, 'social': 1, 'helpful': 2},
            # 'intent':[],
            'rotate': 0.7,
            },


        ]

OBJS = [{'id': 3,
        'name': 'banana',
        'color': [0.25,0.35,0.35],
        'size':[50, 50],
        'pos': [-300, 0],
        'rotate': 0.5,
        'is_game': 0,
        },

        ]


LANDMARKS = []

with open("sally_anne.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
