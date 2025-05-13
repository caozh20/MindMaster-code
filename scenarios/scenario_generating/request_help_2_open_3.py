from core.intent import Intent

OPEN_3 = Intent()
OPEN_3.ind_intent = ['open', 3, None]

REQUEST_HELP_2_OPEN_3 = {
    "name": "1_request_help_2_open_3",
    "agents": [{
        'id': 1,
        'name': 'agent 1',
        'desire': {
            'social': 1
        },
        'intent': {
            'ind': None,
            'soc': ['request_help', 2, OPEN_3],
            'comm': None,
            'ref': None,
            'type': "HIHU"
                    }
            },
    {
        'id': 2,
        'name': 'agent 2',
        'desire': {
            'helpful': 1
                },
    }],
    "objects": [
    {
        'id': 3,
        'name': 'box',
        "size": [120, 120],
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
        'size': [67, 461],
        'rotate': 0.2,
        'pos': [0, 200]
}]
}
