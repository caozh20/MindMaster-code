import pickle
import os, sys
sys.path.append("..")
sys.path.append("../../")

AGENTS = [
            {
            'id': 1,
            'name': 'agent 1',
            'color': [0.35,0.35,0.25],
            'pos': [-200, 0],
            'attention': 10,
            'desire':{'active': 0, 'social': 1, 'helpful': 0},
            'intent':{'ind': ["put_into", 3, 5], 'soc': None, 'comm': None,  'ref': None},
            'rotate': 0,
            'belief_obj_ids': [3]},

            {
            'id': 2,
            'name': 'agent 2',
            'color': [0.35,0.35,0.5],
            'pos': [0, 200],
            'attention': -0.5,
            'desire':{'active': 0, 'social': 1, 'helpful': 0},
            'intent':[{'ind': ['play', 3], 'soc': None, 'comm': None,  'ref': None},
                      {'ind': ['move_to', [0, 200]], 'soc': None, 'comm': None,  'ref': None},
                      {'ind': ['move_to', [-200, 200]], 'soc': None, 'comm': None,  'ref': None},
                      {'ind': ['move_to', [-400, 200]], 'soc': None, 'comm': None,  'ref': None},
                      {'ind': ['move_to', [-200, 200]], 'soc': None, 'comm': None,  'ref': None}],
            'rotate': -0.5,
            'belief_obj_ids': [3]
            }
        ]

OBJS = [{'id': 3,
        'name': 'toy',
        'color': [0.25,0.35,0.35],
        'size':[5, 5],
        'pos': [0, 0],
        'rotate': 0,
        'is_game': 0,
        'being_held_id': [4]},
        {'id': 4,
         'name': 'box1',
         'color': [0.25, 0.25, 0.53],
         'size': [50, 50],
         'pos': [0, 0],
         'rotate': 0,
         'is_game': 0,
         'is_container': 1,
         'containing': [3]},
        {'id': 5,
        'name': 'box2',
        'color': [0.25,0.5,0.25],
        'size':[50, 50],
        'pos': [200, 0],
        'rotate': 0,
        'is_game': 0,
        'is_container': 1}
        ]


LANDMARKS = []

with open("sally_anne.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
