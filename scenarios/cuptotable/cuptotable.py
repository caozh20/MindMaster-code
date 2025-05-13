import pickle
from core.intent import Intent

test_intent = Intent()
test_intent.ind_intent = ['put_into', 4, 3]

AGENTS = [
    {
        'id': 1,
        'name': 'agent 1',
        'color': [0.35, 0.35, 0.25],
        'pos': [-600, -600],
        'attention': 0.3,
        'desire': {'active': 0, 'social': 2, 'helpful': 0},
        'intent': {'ind': None, 'soc': ['request_help', 2, test_intent], 'comm': None, 'ref': None, 'type':"HIHU"},
        'rotate': 0.3
    },

    {
        'id': 2,
        'name': 'agent 2',
        'color': [0.35, 0.35, 0.5],
        'pos': [0, 0],
        'attention': -0.8,
        'desire': {'active': 2, 'social': 1, 'helpful': 2},
        'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
        'rotate': -0.8,
    }
]

OBJS = [
    {'id': 3,
     'name': 'object table',
     'color': [1, 1, 240],
     'size': [200, 200],
     'pos': [400, 200],
     'rotate': 0,
     'is_container': True,
     'open': False,
     },

    {'id': 4,
     'name': 'object cup',
     'color': [0.85, 0.15, 0.35],
     'size': [50, 50],
     'pos': [-400, 200],
     'rotate': 0,
     },
]

LANDMARKS = []

with open("cuptotable.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
