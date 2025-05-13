import pickle

AGENTS = [
    {'id': 1,
     'name': 'baby',
     'color': [0.35, 0.35, 0.25],
     'pos': [400, 300],
     'attention': -0.9,
     'rotate': -0.9,
     'belief_obj_ids': [3, 4],
     'desire': {'active': 1, 'social': 0, 'helpful': 2},
     'intent': {'ind': ['gaze_follow', 2], 'soc': None, 'comm': None, 'ref': None, 'type': "HILU"}
     },
    {'id': 2,
     'name': 'man',
     'color': [0.35, 0.35, 0.25],
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
         'color': [0.85, 0.15, 0.35],
         'size': [50, 50],
         'pos': [400, -300],
         'rotate': 0,
         'is_game': False,
         'being_held_id': [2]},
        {'id': 4,
         'name': 'bookshelf',
         'color': [1, 1, 240],
         'size': [100, 250],
         'pos': [-100, 0],
         'rotate': 0,
         'is_container': True,
         'open': False}
        ]

LANDMARKS = []

with open("baby.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
