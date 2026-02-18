import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.embedding_service import image_to_embedding
from backend.app.services.vector_index import VectorIndex

IMG_A = r"C:\Users\kunle\OneDrive\Documents\PetGuardAI_MVP\test_images\dog.jpg"
IMG_B = r"C:\Users\kunle\OneDrive\Documents\PetGuardAI_MVP\test_images\dog.jpg"

print("▶ Generating embeddings...")

emb_a = image_to_embedding(IMG_A)
emb_b = image_to_embedding(IMG_B)

print("▶ Creating / loading vector index...")

index = VectorIndex(
    dim=emb_a.shape[0],
    storage_dir=str(PROJECT_ROOT / "data" / "vector_index")
)

print("▶ Adding pets to index...")

index.add("pet_001", emb_a, meta={"image": IMG_A})
index.add("pet_002", emb_b, meta={"image": IMG_B})

index.save()

print("▶ Searching index with pet_001 embedding...")

results = index.search(emb_a, top_k=5)

print("✅ Search results:")
for r in results:
    print(f"pet_id={r.pet_id}, score={round(r.score, 4)}, meta={r.meta}")
