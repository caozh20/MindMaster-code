import pickle
import os, sys

sys.path.append("..")
sys.path.append("../../")


from core.intent import Intent
from core.intent_predicates import test_intent_pred, default_intent_pred

test_intent = Intent()
test_intent.ind_intent = ['get', 3, None]


AGENTS = [{'id': 1,
           'name': 'agent 1',
           'color': [0.5, 0.5, 0.5],
           'pos': [-500, -500],
           'attention': 0.12,
           'desire': {'active': 1, 'social': 1, 'helpful': 0},
           'intent': {'ind': None, 'soc': ['request_help', 2, test_intent], 'comm': None, 'ref': None, 'intent_pred': default_intent_pred, 'type': 'HIHU'},
           'rotate': 0.12},
          {'id': 2,
           'name': 'agent 2',
           'color': [0.1, 0, 0],
           'desire': {'active': 2, 'social': 1, 'helpful': 2},
           'belief_obj_ids': [3],
           # 'intent': {'ind': ['explore', None, None], 'soc': None, 'comm': None, 'ref': None},
           'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type': 'LILU'},
           'pos': [400, -300],
           'attention': -0.9,
           'rotate': -0.9}]

OBJS = [{'id': 3,
         'name': 'object cup',
         'color': [0.85, 0.15, 0.35],
         'size': [50, 29],
         'pos': [0, 300],
         'rotate': 0.5}]

LANDMARKS = []

with open("multipointing.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)
