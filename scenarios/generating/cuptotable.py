from core.intent import Intent

PUT_INTO_4_3 = Intent()
PUT_INTO_4_3.ind_intent = ['put_onto', 4, 3]

CUPTOTABLE = {
    "name": "1_request_help_2_put_onto_4_3",
    "agents": [
        {
            'id': 1,
            'name': 'agent 1',
            'desire': {'social': 2},
            'belief_obj_ids': [3, 4],
            'intent': {'ind': None, 'soc': ['request_help', 2, PUT_INTO_4_3], 'comm': None, 'ref': None, 'type':"HIHU"},
        },

        {
            'id': 2,
            'name': 'agent 2',
            'desire': {'helpful': 2},
            'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
        }],
    "objects": [
        {'id': 3,
         'name': 'table',
         'size': [299, 193],
         'is_supporter': True,
         },
        {'id': 4,
         'name': 'cup',
         'size': [50, 29],
         }],
    "landmarks": None
}