from core.intent import Intent

OPEN_3 = Intent()
OPEN_3.ind_intent = ['open', 3]

CHIMPANZEE = {
    "name": "1_request_help_2_open_3",
    "agents": [{
    'id': 1,
    'name': 'agent 1',
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
        'soc': ['request_help', 2, OPEN_3],
        'comm': None,
        'ref': None,
        'type': "HIHU"
    }
}, {
    'id': 2,
    'name': 'agent 2',
    'pos': [500, -400],
    'rotate': 0.6,
    'attention': 0.6,
    'desire': {
        'active': 1,
        'social': 1,
        'helpful': 1
    }}],
    "objects": [
        {
            'id': 3,
            'name': 'box',
            'size': [79, 101],
            'rotate': 0.5,
            'is_container': True,
            'pos': [-400, 200],
            'open': False,
            'locked': True,
        },
        {
            'id': 4,
            'name': 'key',
            'size': [100, 100],
            'rotate': 0.5,
            'is_key': True,
            'pos': [100, 300]
        }],
    "landmarks": [{
        'id': 5,
        'name': 'landmark wall',
        'size': [50, 400],
        'rotate': 0.5,
        'pos': [0, 300]
    }]
}