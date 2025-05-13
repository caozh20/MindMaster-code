PLAY_GAME = {
    "name": "1_play_with_2_3",
    "agents": [
        {
            'id': 1,
            'name': 'Alice',
            'belief_obj_ids': [3],
            'desire': {'social': 2},
            'intent': {'ind': None, 'soc': ['play_with', 2, 3], 'comm': None, 'ref': None, 'type':"HIHU"},
        },
        {
            'id': 2,
            'name': 'Bob',
            'desire': {'helpful': 2},
            'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
        }],
    "objects": [
        {'id': 3,
         'name': 'chess',
         'size': [100, 100],
         'is_game': 1,
         'is_multiplayer_game': 1
        }],
    "landmarks": None
}
