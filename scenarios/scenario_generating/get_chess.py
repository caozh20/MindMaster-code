
GET_CHESS = {
    "name": "1_get_3",
    "agents": [
        {
            'id': 1,
            'name': 'agent 1',
            'intent': {'ind': ['get', 3, None], 'soc': None, 'comm': None, 'ref': None, 'type':"HIHU"},
            'rotate': 0.3
        },

        {
            'id': 2,
            'name': 'agent 2',
            'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
            'rotate': -0.8,
        }],
    "objects": [
        {'id': 3,
         'name': 'chess',
         'size': [83, 78],
         'is_game': 1,
         'is_multiplayer_game': 1}],
    "landmarks": None
}