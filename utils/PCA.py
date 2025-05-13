import json

from sklearn.decomposition import PCA
import numpy as np

# 从 JSON 文件读取数据
with open('list_padding.json', 'r') as file:
    data = json.load(file)

# 假设 vectors 是你的 10 个 300 维向量
vectors = np.asarray(data)

# 使用 PCA 将向量降维到 8 维
pca = PCA(n_components=8)
reduced_vectors = pca.fit_transform(vectors)

print(reduced_vectors)

reduced_vectors = reduced_vectors.tolist()

with open('word2vec_padding.json', 'w') as file:
    json.dump(reduced_vectors, file)

# print(data)