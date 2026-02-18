import os
import sys
from pathlib import Path
import numpy as np

# Silence TensorFlow logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.embedding_service import image_to_embedding

TEST_IMAGE_PATH = r"C:\Users\kunle\OneDrive\Documents\PetGuardAI_MVP\test_images\dog.jpg"

embedding = image_to_embedding(TEST_IMAGE_PATH)

# Save embedding to disk (NO printing)
output_path = PROJECT_ROOT / "test_embedding_output.npy"
np.save(output_path, embedding)

print(f"✅ Embedding saved to {output_path}")
print(f"Shape: {embedding.shape}, L2 norm: {np.linalg.norm(embedding)}")

sys.exit(0)
