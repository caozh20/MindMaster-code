from core.intent import Intent

GET_3 = Intent()
GET_3.ind_intent = ["get", 3, None]

MULTIPOINTING = {
    "name": "1_request_help_2_get_3",
    "agents": [
        {
            'id': 1,
            'name': 'Alice',
            'belief_obj_ids': [3],
            'desire': {'social': 2},
            'intent': {'ind': None, 'soc': ["request_help", 2, GET_3], 'comm': None, 'ref': None, 'type':"HIHU"},
        },

        {
            'id': 2,
            'name': 'Bob',
            'desire': {'helpful': 2},
            'intent': {'ind': ['explore'], 'soc': None, 'comm': None, 'ref': None, 'type':"LILU"},
        }],
    "objects": [
        {'id': 3,
         'name': 'cup',
         'size': [50, 29],
         }],
    "landmarks": None
}