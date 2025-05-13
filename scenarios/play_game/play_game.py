import pickle
import os, sys
sys.path.append("..")
sys.path.append("../../")

AGENTS = [
            {
            'id': 1,
            'name': 'agent 1',
            'color': [0.35,0.35,0.25],
            'pos': [-500, 0],
            'attention': 0,
            'desire':{'active': 1, 'social': 1, 'helpful': 0},
            'intent':{'ind': None, 'soc': ['play_with', 2, 3], 'comm': None,  'ref': None, 'type': "HIHU"},
            'rotate': 0},

            {
            'id': 2,
            'name': 'agent 2',
            'color': [0.35,0.35,0.5],
            'pos': [500, 0],
            'attention': -0.8,
            'desire':{'active': 1, 'social': 1, 'helpful': 1},
            # 'intent':{'ind': ['explore'], 'soc': None, 'comm': None,  'ref': None},
            'rotate': -0.8,
            }
        ]

OBJS = [{'id': 3,
        'name': 'chess',
        'color': [0.25,0.35,0.35],
        'size':[83, 78],
        'pos': [0, 200],
        'rotate': 0.5,
        'is_game': 1,
        'is_multiplayer_game': 1}]


LANDMARKS = []

with open("play_game.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
