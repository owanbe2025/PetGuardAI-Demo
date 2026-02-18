import numpy as np

from backend.app.services.embedding_service import image_to_embedding
from backend.app.services.similarity_service import cosine_similarity, is_same_pet

IMG1 = r"C:\Users\kunle\OneDrive\Documents\PetGuardAI_MVP\test_images\dog.jpg"
IMG2 = r"C:\Users\kunle\OneDrive\Documents\PetGuardAI_MVP\test_images\dog.jpg"

emb1 = image_to_embedding(IMG1)
emb2 = image_to_embedding(IMG2)

sim = cosine_similarity(emb1, emb2)
same = is_same_pet(sim)

print("Similarity:", sim)
print("Same pet?", same)
