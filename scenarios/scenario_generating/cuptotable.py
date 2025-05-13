from core.intent import Intent

PUT_INTO_4_3 = Intent()
PUT_INTO_4_3.ind_intent = ['put_into', 4, 3]

CUPTOTABLE = {
    "name": "1_put_into_4_3",
    "agents": [
        {
            'id': 1,
            'name': 'agent 1',
            'color': [0.35, 0.35, 0.25],
            'pos': [-600, -600],
            'attention': 0.3,
            'desire': {'active': 0, 'social': 2, 'helpful': 0},
            'intent': {'ind': ['put_into', 4, 3], 'soc': None, 'comm': None, 'ref': None, 'type':"HIHU"},
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
        }],
    "objects": [
        {'id': 3,
         'name': 'box',
         'color': [1, 1, 240],
         'size': [79, 101],
         'pos': [400, 200],
         'rotate': 0.5,
         'is_container': True,
         'open': False,
         },

        {'id': 4,
         'name': 'cup',
         'color': [0.85, 0.15, 0.35],
         'size': [64, 46],
         'pos': [-400, 200],
         'rotate': 0.5,
         }],
    "landmarks": None
}