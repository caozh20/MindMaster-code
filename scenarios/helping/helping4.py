import pickle

AGENTS = [
            {
            'id': 1,
            'name': 'agent 1',
            'color': [1,0,0], # red
            'pos': [-200, -300],
            'attention': 0,
            'rotate': -0.4,
            'desire':{'active': 1, 'social': 1, 'helpful': 1},
            'intent':{'ind': ['put_into', 4, 3], 'soc': None, 'comm': None,  'ref': None, 'type': "HILU"},
           },

            {
            'id': 2,
            'name': 'agent 2',
            'color': [0,1,0], # green
            'pos': [100, 150],
            'attention': 0,
            'rotate': 0.7,
            'holding_ids': [4],
            'desire':{'active': 1, 'social': 1, 'helpful': 2},
            }
        ]

OBJS = [
            {
            'id':3,
            'name': 'cabinet',
            'color': [0.25,0.35,0.35],
            'size': [120, 120],
            'pos': [-400, 280],
            'rotate':0.5,
            'is_container':True,
            'open':True
            },


            {
            'id': 4,
            'name': 'books',
            'color': [0.45,1.95,1.95],
            'size': [93, 80],
            'pos': [22, 94],
            'rotate':0.7,
            'being_held_id':[2],
            }
        ]

LANDMARKS = []

with open("helping.pkl", "wb") as f:
    pickle.dump([AGENTS, OBJS, LANDMARKS], f)

# {'name': 'door',
# 'color': [0.45,0.35,0.35],
# 'size': [300, 20],
# 'pos': [0, 280]},