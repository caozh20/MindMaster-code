from core.intent import Intent

HELPING = {
    "name": "1_put_into_4_3",
    "agents": [
        {
            'id': 1,
            'name': 'agent 1',
            'belief_obj_ids': [3, 4],
            'intent': {'ind': ['put_into', 4, 3], 'soc': None, 'comm': None, 'ref': None, 'type':"HIHU"},
        },

        {
            'id': 2,
            'name': 'agent 2',
            'desire': {'helpful': 2},
            'holding_ids': [4],
            'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
        }],
    "objects": [
        {'id': 3,
         'name': 'cabinet',
         'size': [120, 120],
         'is_container':True,
            'open':True
         },
        {'id': 4,
         'name': 'books',
         'size': [93, 80],
        'being_held_id':[2],
         }],
    "landmarks": None
}