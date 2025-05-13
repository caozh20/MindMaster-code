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
            'intent':{'ind': None, 'soc': ['play_with', 2, 3], 'comm': None,  'ref': None, 'type': "HIHU"},
            'rotate': 0},

            {
            'id': 2,
            'name': 'agent 2',
            'color': [0.35,0.35,0.5],
            'pos': [200, 0],
            'attention': 1,
            'desire':{'active': 0, 'social': 1, 'helpful': 1},
            # 'intent':{'ind': ['explore'], 'soc': None, 'comm': None,  'ref': None},
            'rotate': 1,
            }
        ]

OBJS = [{'id': 3,
        'name': 'object plate',
        'color': [0.25,0.35,0.35],
        'size':[50, 50],
        'pos': [-150, 0],
        'rotate': 0,
        'is_game': 1,
        'is_multiplayer_game': 1}]


LANDMARKS = [{
    'id': 5,
    'name': 'landmark wall',
    'color': [0.85, 0.85, 0.35],
    'size': [30, 500],
    'rotate': 0.2,
    'pos': [0, 200]
}]

with open("play_game.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
