from core.intent import Intent

OPEN_3 = Intent()
OPEN_3.ind_intent = ['open', 3, None]

CHIMPANZEE = {
    "name": "1_request_help_2_open_3",
    "agents": [{
    'id': 1,
    'name': 'Alice',
    'desire': {
        'helpful': 1,
    },
    'intent': {
        'ind': None,
        'soc': ['request_help', 2, OPEN_3],
        'comm': None,
        'ref': None,
        'type': "HIHU"
    },
    'belief_obj_ids': [3],
}, {
    'id': 2,
    'name': 'Bob',
    'desire': {
        'helpful': 1
    }}],
    "objects": [
        {
            'id': 3,
            'name': 'box',
            'size': [100, 100],
            'is_container': True,
            'open': False,
            'locked': True,
        },
        {
            'id': 4,
            'name': 'key',
            'size': [60, 30],
            'is_key': True,
        }],
    "landmarks": [{
        'id': 5,
        'name': 'landmark wall',
        'color': [0.85, 0.85, 0.35],
        'size': [67, 461],
        'rotate': 0.2,
        'pos': [0, 300]
    }]
}