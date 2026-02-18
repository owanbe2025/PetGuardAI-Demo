import numpy as np

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1D vectors.
    Assumes vectors are already L2-normalized.
    """
    return float(np.dot(a, b))


def is_same_pet(similarity: float, threshold: float = 0.80) -> bool:
    """
    Decide if two embeddings belong to the same pet.
    """
    return similarity >= threshold
