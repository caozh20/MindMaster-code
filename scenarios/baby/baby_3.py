import pickle

AGENTS = [
    {'id': 1,
     'name': 'agent 1',
     'color': [0, 0.5, 1],
     'pos': [400, 300],
     'attention': -0.5,
     'rotate': -0.5,
     'belief_obj_ids': [3, 4],
     'desire': {'active': 1, 'social': 0, 'helpful': 1},
     'intent': {'ind': ['gaze_follow', 2], 'soc': None, 'comm': None, 'ref': None, 'type': "HILU"}
     },
    {'id': 2,
     'name': 'agent 2',
     'color': [0.1, 0, 0],
     'pos': [400, -300],
     'attention': 0.5,
     'rotate': 0.5,
     'hands_occupied': True,
     'desire': {'active': 1, 'social': 0, 'helpful': 0},
     'holding_ids': [3],
     'intent': {'ind': ['put_into', 3, 4], 'soc': None, 'comm': None, 'ref': None, 'type': "HILU"}},
]

OBJS = [{'id': 3,
         'name': 'books',
         'color': [0.5, 0.5, 0.5],
         'size': [67, 75],
         'pos': [304, -300],
         'rotate': 0.5,
         'is_game': False,
         'being_held_id': [2]},
        {'id': 4,
         'name': 'shelf',
         'color': [1, 1, 240],
         'size': [160, 220],
         'pos': [-100, 0],
         'rotate': 0.5,
         'is_container': True,
         'open': False}
        ]

LANDMARKS = []

with open("baby.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
