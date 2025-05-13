import pickle

AGENTS=[    {'id': 1,
            'name': 'agent 1',
            'color': [1, 0, 0],
            'pos': [400, 400],
            'attention': -0.5,
            'rotate': -0.5,
            'desire':{'active': 0, 'social': 1, 'helpful': 0}},

            {'id': 2,
            'name': 'agent 2',
            'color': [0, 1, 0],
            'pos': [-400, -400],
            'attention': 0.25,
            'rotate': 0.25,
            'desire':{'active': -1, 'social': 0, 'helpful': 0},
            'intent':{'ind': None, 'soc': ["inform", 1, 4], 'comm': None,  'ref': [1, 4], 'type':"HIHU"}},

            {'id': 3,
            'name': 'agent 3',
            'color': [0,0,1],
            'pos': [400, -400],
            'attention': 0.5,
            'rotate': 0.5,
            'desire':{'active': 1, 'social': 1, 'helpful': 2}}]

OBJS=[  {'id': 4,
        'name': 'clock',
        'color': [2, 0.05, 0.05],
        'size': [70, 80],
        # 'pos': [-350, -350],
        'pos': [-250, -350],
        'rotate':0.5}]

LANDMARKS= []

with open("classroom.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)





