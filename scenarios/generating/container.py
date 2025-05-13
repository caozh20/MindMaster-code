CONTAINER = {
    "name": "1_get_3",
    "agents": [{'id': 1,
           'name': 'Alice',
           'desire': {'active': 1},
           'intent': {'ind': ['get', 3, None], 'soc': None, 'comm': None, 'ref': None, 'type':"HILU"}},
          {'id': 2,
           'name': 'Bob',
           'belief_obj_ids': [3, 4],
           'desire': {'active': 2, 'helpful': 2},
           'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"}
           }],
    "objects": [{'id': 3,
         'name': 'key',
         'size': [30, 30],
         'being_contained': [4]},
        {'id': 4,
         'name': 'box',
         'size': [120, 120],
         'is_container': True,
         'open': False,
         'containing': [3]}
        ],
    "landmarks": None
}