import numpy as np


def normalize_helpful(helpful):
    # [-1, 0, 1, 2] + 1 -> [0, 1, 2, 3]
    return (helpful + 1) / 3


def euclidean_similarity(truth, prediction):
    # 归一化 helpful 维度
    truth_normalized = np.array([truth[0], truth[1], normalize_helpful(truth[2])])
    # prediction_normalized = np.array([prediction[0], prediction[1], normalize_helpful(prediction[2])])
    prediction_normalized = np.array([prediction[0], prediction[1], prediction[2]])

    # 计算欧几里得距离
    distance = np.linalg.norm(truth_normalized - prediction_normalized)

    # 归一化距离
    max_distance = np.sqrt(3)
    similarity = 1 - (distance / max_distance)

    return similarity


def manhattan_similarity(truth, prediction):
    truth_normalized = np.array([truth[0], truth[1], normalize_helpful(truth[2])])
    # prediction_normalized = np.array([prediction[0], prediction[1], normalize_helpful(prediction[2])])
    prediction_normalized = np.array([prediction[0], prediction[1], prediction[2]])

    distance = np.sum(np.abs(truth_normalized - prediction_normalized))
    similarity = 1 - (distance / 3)
    return similarity


def cosine_similarity(truth, prediction):
    truth_normalized = np.array([truth[0], truth[1], normalize_helpful(truth[2])])
    # prediction_normalized = np.array([prediction[0], prediction[1], normalize_helpful(prediction[2])])
    prediction_normalized = np.array([prediction[0], prediction[1], prediction[2]])

    dot_product = np.dot(truth_normalized, prediction_normalized)
    norm_truth = np.linalg.norm(truth_normalized)
    norm_prediction = np.linalg.norm(prediction_normalized)
    cos_similarity = dot_product / (norm_truth * norm_prediction)

    similarity = (1 + cos_similarity) / 2
    return similarity


def minkowski_similarity(truth, prediction, p=3):
    truth_normalized = np.array([truth[0], truth[1], normalize_helpful(truth[2])])
    # prediction_normalized = np.array([prediction[0], prediction[1], normalize_helpful(prediction[2])])
    prediction_normalized = np.array([prediction[0], prediction[1], prediction[2]])

    distance = np.sum(np.abs(truth_normalized - prediction_normalized) ** p) ** (1 / p)
    similarity = 1 - (distance / 3 ** (1 / p))
    return similarity


if __name__ == '__main__':
    truth = [0.8, 0.4, 1.5]
    prediction = [0.2, 0.6, 1.0]

    truth = [1, 1, 1]
    prediction = [1, 1, 1]

    truth = [1, 1, 1]
    prediction = [0.5, 0.5, 0.5]

    euclidean_sim = euclidean_similarity(truth, prediction)
    manhattan_sim = manhattan_similarity(truth, prediction)
    cosine_sim = cosine_similarity(truth, prediction)
    minkowski_sim = minkowski_similarity(truth, prediction)

    print(f"euclidean Similarity: {euclidean_sim:.4f}")
    print(f"Manhattan Similarity: {manhattan_sim:.4f}")
    print(f"Cosine Similarity: {cosine_sim:.4f}")
    print(f"Minkowski Similarity (p=3): {minkowski_sim:.4f}")