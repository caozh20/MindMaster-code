
def intent_encoding(intent, user_agent_id):
    user_agent_id = str(user_agent_id)
    tokens = intent.split('-')
    tokens_encoded = [None] * len(tokens)

    assert user_agent_id == '1' or user_agent_id == '2' or user_agent_id == 'agent_1' or user_agent_id == 'agent_2'

    all_entities = []
    entity_id_rec = dict()

    for ind, token in enumerate(tokens):

        if token == '1' or token == 'agent_1':
            if user_agent_id == '1':
                tokens_encoded[ind] = 'me'
            elif user_agent_id == '2':
                tokens_encoded[ind] = 'other'
        elif token == '2' or token == 'agent_2':
            if user_agent_id == '1':
                tokens_encoded[ind] = 'other'
            elif user_agent_id == '2':
                tokens_encoded[ind] = 'me'
        elif '_' in token:
            entity, id = token.split('_')
            all_entities.append(entity)

            if entity in entity_id_rec:
                if token in entity_id_rec[entity]:
                    id_new = str(entity_id_rec[entity].index(token))
                    tokens_encoded[ind] = '_'.join([entity, id_new])
                else:
                    entity_id_rec[entity].append(token)
                    id_new = str(entity_id_rec[entity].index(token))
                    tokens_encoded[ind] = '_'.join([entity, id_new])
            else:
                entity_id_rec[entity] = [token]
                id_new = str(entity_id_rec[entity].index(token))
                tokens_encoded[ind] = '_'.join([entity, id_new])
        else:
            all_entities.append(token)
            tokens_encoded[ind] = token

    # if tokens_encoded[0]=='other':
    #     print('-'.join(tokens_encoded))

    return '-'.join(tokens_encoded), all_entities

def intent_encoding_coarse(intent, user_agent_id):
    user_agent_id = str(user_agent_id)
    tokens = intent.split('-')
    tokens_encoded = [None] * len(tokens)

    assert user_agent_id == '1' or user_agent_id == '2' or user_agent_id == 'agent_1' or user_agent_id == 'agent_2'

    for ind, token in enumerate(tokens):
        if token == '1' or token == 'agent_1':
            if user_agent_id == '1':
                tokens_encoded[ind] = 'me'
            elif user_agent_id == '2':
                tokens_encoded[ind] = 'other'
        elif token == '2' or token == 'agent_2':
            if user_agent_id == '1':
                tokens_encoded[ind] = 'other'
            elif user_agent_id == '2':
                tokens_encoded[ind] = 'me'
        elif '_' in token:
            tokens_encoded[ind] = 'obj'
        else:
            tokens_encoded[ind] = token

    return '-'.join(tokens_encoded)