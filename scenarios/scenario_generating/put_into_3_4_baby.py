PUT_INTO_3_4_BABY = {
    "name": "2_put_into_3_4",
    "agents": [
        {'id': 1,
         'name': 'baby',
         'belief_obj_ids': [3, 4],
         'desire': {'active': 1, 'social': 1, 'helpful': 1},
         'intent': {'ind': ['gaze_follow', 2], 'soc': None, 'comm': None, 'ref': None, 'type': "LILU"}
         },
        {'id': 2,
         'name': 'man',
         'hands_occupied': True,
         'desire': {'active': 1, 'social': 0, 'helpful': 0},
         'holding_ids': [3],
         'intent': {'ind': ['put_into', 3, 4], 'soc': None, 'comm': None, 'ref': None, 'type': "HILU"}}],
    "objects": [
        {'id': 3,
         'name': 'books',
         "size": [67, 75],
         'is_game': False,
         'being_held_id': [2]},
        {'id': 4,
         'name': 'shelf',
         "size": [160, 220],
         'is_container': True,
         'open': False}
        ],
    "landmarks": None
}
