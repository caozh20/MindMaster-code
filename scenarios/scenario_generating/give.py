GIVE = {
    "name": "1_give_3_2",
    "agents": [
        {
            'id': 1,
            'name': 'agent 1',
            'color': [0.35, 0.35, 0.25],
            'pos': [-600, -600],
            'attention': 0.3,
            'intent': {'ind': ['give', 3, 2], 'soc': None, 'comm': None, 'ref': None, 'type':"HIHU"},
            'rotate': 0.3, 
            'holding_ids': [3], 
        },

        {
            'id': 2,
            'name': 'agent 2',
            'color': [0.35, 0.35, 0.5],
            'pos': [0, 0],
            'attention': -0.8,
            'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
            'rotate': -0.8,
        }],
    "objects": [
        {'id': 3,
         'name': 'cup',
         'color': [0.85, 0.15, 0.35],
         'size': [64, 46],
         'pos': [-400, 200],
         'rotate': 0.5,
         'being_held_id': [1], 
         }, 
        ],
    "landmarks": None
}