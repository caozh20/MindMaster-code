import gensim.downloader as api
import json
import numpy as np

ACTION2WORD = {
    'ActionMoveTo': ["move"],
    'ActionRotateTo': ["rotate"],
    'ActionOpen': ["open"],
    'ActionUnlock': ['unlock'],
    'ActionGrab': ["grab"],
    'ActionGiveTo': ["give"],
    'ActionWaveHand': ['wave', 'hand'],
    'ActionMoveToAttention': ['move', 'attention'],
    'ActionPointTo': ["point"],
    'ActionNodHead': ['nod', 'head'],
    'ActionShakeHead': ['shake', 'head'],
    'ActionPlay': ["play"],
    'ActionPutInto': ['put', 'into'],
    'ActionPutOnto': ['put', 'onto'],
    'ActionPutDown': ['put', 'down'],
    'ActionFollowPointing': ['follow', 'pointing'],
    "ActionEat": ["eat"],
    "ActionSmash": ["smash"],
    "ActionSpeak": ["speak"],
    "ActionPerform": ["perform"],
    "ActionClose": ["close"],
}


one_word = [['open'], ['unlock'], ['grab'], ['play'], ['eat'], ['smash'], ['speak'], ['perform'], ['close'], ['move'], ['rotate'], ['give'], ['point']]

two_word = [['wave', 'hand'], ['nod', 'head'], ['shake', 'head'], ['put', 'into'], ['put', 'onto'], ['put', 'down'], ['follow', 'pointing'], ['move', 'attention']]

words = one_word + two_word

# one_word = [['open'], ['unlock'], ['grab'], ['play'], ['eat'], ['smash'], ['speak'], ['perform'], ['close']]

# two_word = [['move', 'to'], ['rotate', 'to'], ['give', 'to'], ['wave', 'hand'], ['point', 'to'], ['nod', 'head'], ['shake', 'head'], ['put', 'into'], 
# ['put', 'onto'], ['put', 'down'], ['follow', 'pointing']]

# three_word = [['move', 'to', 'attention']]


# words = ['move', 'rotate', 'open', 'unlock', 'grab', 'give', 'wave', 'appear', 'point', 'nod', 'shake', 'play', 'put', 'follow', 'eat', 'smash', 'speak', 'perform', 'close']

# # 加载预训练的 Word2Vec 模型
# model = KeyedVectors.load_word2vec_format('path/to/your/model.bin', binary=True)

if __name__ == "__main__":

    model = api.load('word2vec-google-news-300')

    vectors = []

    # 检查单词是否在模型的词汇表中
    for word in words:
        # add
        # word_vector = None
        # for i, word_piece in enumerate(word):
        #     if word_piece in model:
        #         if word_vector is None:
        #             word_vector = model[word_piece]
        #         else:
        #             word_vector = (word_vector * (i) + model[word_piece]) / (i+1)
        #         print(word_vector.shape)
        #         print(type(word_vector))
        #     else:
        #         print(f"The word '{word_piece}' is not in the vocabulary.")
        # vectors.append(word_vector.tolist())

        # padding
        word_vector = np.zeros(600)
        for i, word_piece in enumerate(word):
            if word_piece in model:
                word_vector[i*300: (i+1)*300] = model[word_piece]
                print(word_vector.shape)
            else:
                print(f"The word '{word_piece}' is not in the vocabulary.")
        vectors.append(word_vector.tolist())

    print(len(vectors))

    # 将列表保存为 JSON 文件
    with open('list_padding.json', 'w') as file:
        json.dump(vectors, file)
