import pickle
from core.intent import Intent

test_intent = Intent()
test_intent.ind_intent = ['get', 4, None]

AGENTS = [
    {
        'id': 1,
        'name': 'requirer',
        'color': [0.35, 0.35, 0.25],
        'pos': [200, -200],
        'attention': 0.75,
        'desire': {'active': 0, 'social': 2, 'helpful': 0},
        'intent': {'ind': None, 'soc': ['request_help', 2, test_intent], 'comm': None, 'ref': None, 'type':"HILU"},
        'rotate': 0.75
    },
    {
        'id': 2,
        'name': 'agent 2',
        'color': [0.35, 0.35, 0.5],
        'pos': [-500, 0],
        'attention': -0.5,
        'desire': {'active': 2, 'social': 1, 'helpful': 2},
        'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
        'rotate': -0.5,
    }
]

OBJS = [
    {'id': 3,
     'name': 'banana',
     'color': [1, 1, 240],
     'size': [50, 50],
     'pos': [-200, 200],
     'rotate': 0.5,
     # 'is_container': True,
     # 'open': True,
     },

    {'id': 4,
     'name': 'cup',
     'color': [0.85, 0.15, 0.35],
     'size': [50, 29],
     'pos': [-300, 300],
     'rotate': 0.5,
     },
]

LANDMARKS = []

with open("refer_disambiguation.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)