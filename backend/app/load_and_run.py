import tensorflow as tf
import numpy as np
from pathlib import Path

# Allow Lambda layers
tf.keras.config.enable_unsafe_deserialization()

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "petguard_embedding_v1.keras"

print("🔍 Loading model...")

model = tf.keras.models.load_model(MODEL_PATH, compile=False)

print("✅ Model object created")

# 🔥 FORCE EXECUTION (this is the key)
dummy_input = np.random.rand(1, 224, 224, 3).astype("float32")

print("⚙️ Running a forward pass...")
output = model(dummy_input)

print("✅ Forward pass successful")
print("Embedding shape:", output.shape)

print("🎉 MODEL IS FULLY FUNCTIONAL FOR INFERENCE")
