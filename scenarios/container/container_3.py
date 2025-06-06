import pickle

AGENTS = [{'id': 1,
           'name': 'agent 1',
           'color': [0.35, 0.35, 0.25],
           'pos': [-500, -500],
           'attention': 0.0,
           'rotate': 0.0,
           'desire': {'active': 1, 'social': 0, 'helpful': 0},
           'intent': {'ind': ['get', 3, None], 'soc': None, 'comm': None, 'ref': None, 'type':"HILU"}},
          {'id': 2,
           'name': 'agent 2',
           'color': [0.35, 0.35, 0.25],
           'pos': [400, -300],
           'attention': -0.9,
           'rotate': -0.9,
           'belief_obj_ids': [3, 4],
           'desire': {'active': 0, 'social': 0, 'helpful': 2},
           'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"}
           }]

OBJS = [{'id': 3,
         'name': 'object toy',
         'color': [0.85, 0.15, 0.35],
         'size': [50, 50],
         'pos': [0, 300],
         'rotate': 0,
         'is_game': True,
         'being_held_id': [4]},
        {'id': 4,
         'name': 'object box',
         'color': [1, 1, 240],
         'size': [80, 80],
         'pos': [0, 300],
         'rotate': 0,
         'is_container': True,
         'open': False,
         'containing': [3]}
        ]

LANDMARKS = []

with open("container.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
