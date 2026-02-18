# backend/app/services/embedding_service.py
from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
import tensorflow as tf

from app.services.custom_layers import L2Normalize

# -------------------------------------------------
# Paths
# This file: PetGuardAI_MVP/backend/app/services/embedding_service.py
# parents[0]=services, [1]=app, [2]=backend, [3]=PetGuardAI_MVP
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "petguard_embedding_v1_1_prod.keras"

# If you ever change these in training, change them here too
IMAGE_SIZE = (128, 128)
EXPECTED_EMBED_DIM = 128

_model: tf.keras.Model | None = None
_model_lock = threading.Lock()


def get_model() -> tf.keras.Model:
    """Load embedding model once per process (thread-safe)."""
    global _model

    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        print(f"🔍 Loading embedding model from: {MODEL_PATH}")

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"❌ Model not found: {MODEL_PATH}")

        _model = tf.keras.models.load_model(
            str(MODEL_PATH),
            custom_objects={"L2Normalize": L2Normalize},
            compile=False,
        )

        # Warm-up (helps first request latency)
        try:
            dummy = tf.zeros((1, IMAGE_SIZE[0], IMAGE_SIZE[1], 3), dtype=tf.float32)
            out = _model(dummy, training=False)
            _ = out.numpy()
        except Exception as e:
            # Don't crash startup; just log
            print(f"⚠️ Model warm-up skipped due to: {repr(e)}")

        print("✅ PetGuard embedding model loaded")

    return _model


def image_to_embedding(image_path: str) -> np.ndarray:
    """
    Convert an image path to a 1D float32 embedding vector.
    Enforces L2-normalization for cosine similarity (FAISS IndexFlatIP).
    """
    model = get_model()

    try:
        img = tf.keras.utils.load_img(image_path, target_size=IMAGE_SIZE)
        img = tf.keras.utils.img_to_array(img).astype("float32") / 255.0
    except Exception as e:
        raise RuntimeError(f"Failed to load/parse image '{image_path}': {repr(e)}")

    x = np.expand_dims(img, axis=0).astype("float32")  # (1, 128, 128, 3)

    y = model(x, training=False)
    emb = y.numpy().astype("float32")

    # emb should be shape (1, D) -> take [0]
    if emb.ndim != 2 or emb.shape[0] != 1:
        raise RuntimeError(f"Unexpected model output shape: {emb.shape}")

    emb = emb[0].reshape(-1).astype("float32")  # (D,)

    if emb.size == 0:
        raise RuntimeError("Model returned empty embedding")

    # Optional check (helps catch wrong model loaded)
    if EXPECTED_EMBED_DIM is not None and emb.shape[0] != EXPECTED_EMBED_DIM:
        raise RuntimeError(
            f"Embedding dim mismatch: got {emb.shape[0]}, expected {EXPECTED_EMBED_DIM}. "
            f"Check you're loading the correct .keras model."
        )

    # L2 normalize
    norm = float(np.linalg.norm(emb))
    if norm > 0.0:
        emb = emb / norm

    return emb
