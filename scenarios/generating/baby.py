BABY = {
    "name": "1_put_into_3_4",
    "agents": [
        {'id': 1,
         'name': 'baby',
         'belief_obj_ids': [3, 4],
         'desire': {'helpful': 2},
         'intent': {'ind': ['gaze_follow', 2], 'soc': None, 'comm': None, 'ref': None, 'type': "LILU"}
         },
        {'id': 2,
         'name': 'man',
         'hands_occupied': True,
         'desire': {'active': 1},
         'holding_ids': [3],
         'intent': {'ind': ['put_into', 3, 4], 'soc': None, 'comm': None, 'ref': None, 'type': "HILU"}}],
    "objects": [{'id': 3,
                 'name': 'books',
                 'size': [93, 80],
                 'being_held_id': [2]},
                {'id': 4,
                 'name': 'shelf',
                 'size': [255, 300],
                 'is_container': True,
                 'open': False}
                ],
    "landmarks": None
}