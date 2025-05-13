import pickle
import sys

sys.path.append("..")
sys.path.append("../../")
from core.intent import Intent

test_intent = Intent()

test_intent.ind_intent = ['open', 3, None]

AGENTS = [{
    'id': 1,
    'name': 'agent 1',
    'color': [0.35, 0.35, 0.25],
    'pos': [-500, -300],
    'attention': 0.4,
    'rotate': 0.4,
    'desire': {
        'active': 1,
        'social': 1,
        'helpful': 1
    },
    'intent': {
        'ind': None,
        'soc': ['request_help', 2, test_intent],
        'comm': None,
        'ref': None,
        'type': "HIHU"
    }
}, {
    'id': 2,
    'name': 'agent 2',
    'color': [0.35, 0.35, 0.25],
    'pos': [500, -400],
    'attention': 0.6,
    'desire': {
        'active': 1,
        'social': 1,
        'helpful': 1
    },
    'rotate': 0.6
}]

OBJS = [
    {
        'id': 3,
        'name': 'object box',
        'color': [1, 1, 240],
        'size': [100, 100],
        'rotate': 0,
        'is_container': True,
        'pos': [-400, 200],
        'open': False,
        'locked': True,
    },
    {
        'id': 4,
        'name': 'object key',
        'color': [0.85, 0.15, 0.35],
        'size': [100, 100],
        'rotate': 0,
        'size': [60, 30],
        'is_key': True,
        'pos': [100, 300]
    },
]

LANDMARKS = [{
    'id': 5,
    'name': 'landmark wall',
    'color': [0.85, 0.85, 0.35],
    'size': [67, 461],
    'rotate': 0.2,
    'pos': [0, 300]
}]

with open("chimpanzee.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
