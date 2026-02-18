from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss  # type: ignore
    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False


@dataclass
class SearchResult:
    pet_id: str
    score: float
    meta: Dict


class VectorIndex:
    """
    FAISS-based vector index for PetGuard AI (MVP Demo).

    ✅ Uses cosine similarity via IndexFlatIP (inner product).
    ✅ Assumes embeddings are L2-normalized.
    ✅ Supports multi-sample per pet_id:
        dog_0001 can have 3-4 embeddings from different photos.
    ✅ Search returns 1 row per pet_id (best score wins) by default (dedupe=True).
    ✅ Persists to disk (index.faiss + meta.json) and reloads safely.
    """

    def __init__(self, dim: int, storage_dir: str):
        if not _HAS_FAISS:
            raise RuntimeError("faiss is not installed. Install faiss-cpu.")

        self.dim = int(dim)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.faiss_path = self.storage_dir / "index.faiss"
        self.meta_path = self.storage_dir / "meta.json"

        self._faiss_index: Optional[faiss.Index] = None

        # One embedding = one sample_id, stored at same position in FAISS
        self._sample_ids: List[str] = []
        self._sample_meta: Dict[str, Dict] = {}
        self._pet_counters: Dict[str, int] = {}

        self._load_if_exists()

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------

    def _create_new_index(self) -> None:
        self._faiss_index = faiss.IndexFlatIP(self.dim)
        self._sample_ids = []
        self._sample_meta = {}
        self._pet_counters = {}

    def _load_if_exists(self) -> None:
        """
        Load FAISS index + meta.json if present.
        If corrupted or dim mismatch, rebuild safely.
        """
        if self.faiss_path.exists() and self.meta_path.exists():
            try:
                self._faiss_index = faiss.read_index(str(self.faiss_path))

                # Dimension mismatch safety
                if getattr(self._faiss_index, "d", None) != self.dim:
                    self._create_new_index()
                    return

                with self.meta_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                self._sample_ids = data.get("sample_ids", [])
                self._sample_meta = data.get("sample_meta", {})
                self._pet_counters = data.get("pet_counters", {})

                if not isinstance(self._sample_ids, list) or not isinstance(self._sample_meta, dict):
                    self._create_new_index()

            except Exception:
                self._create_new_index()
        else:
            self._create_new_index()

    def _next_sample_id(self, pet_id: str) -> str:
        n = int(self._pet_counters.get(pet_id, 0)) + 1
        self._pet_counters[pet_id] = n
        return f"{pet_id}__{n:04d}"

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def add(self, pet_id: str, embedding: np.ndarray, meta: Optional[Dict] = None) -> str:
        """
        Add ONE embedding sample for pet_id.
        Returns created sample_id.
        """
        if embedding is None:
            raise ValueError("embedding is None")

        emb = np.asarray(embedding, dtype="float32").reshape(-1)
        if emb.ndim != 1:
            raise ValueError("Embedding must be a 1D vector")

        if emb.shape[0] != self.dim:
            raise ValueError(f"Embedding dim {emb.shape[0]} != index dim {self.dim}")

        emb2 = emb.reshape(1, -1).astype("float32")

        assert self._faiss_index is not None
        self._faiss_index.add(emb2)

        sample_id = self._next_sample_id(pet_id)
        self._sample_ids.append(sample_id)

        m = dict(meta or {})
        m["pet_id"] = pet_id
        m["sample_id"] = sample_id
        self._sample_meta[sample_id] = m

        return sample_id

    def search(self, query_embedding: np.ndarray, top_k: int = 5, dedupe: bool = True) -> List[SearchResult]:
        """
        Search by query embedding.

        If dedupe=True:
            returns at most 1 result per pet_id (best score).
        """
        if self._faiss_index is None:
            return []

        if len(self._sample_ids) == 0:
            return []

        top_k = int(top_k)
        if top_k < 1:
            return []

        q = np.asarray(query_embedding, dtype="float32").reshape(-1)
        if q.ndim != 1:
            raise ValueError("Query embedding must be 1D")

        if q.shape[0] != self.dim:
            raise ValueError(f"Query embedding dim {q.shape[0]} != index dim {self.dim}")

        q2 = q.reshape(1, -1).astype("float32")

        # Over-fetch when deduping
        if dedupe:
            fetch_k = min(len(self._sample_ids), max(top_k * 6, top_k))
        else:
            fetch_k = min(len(self._sample_ids), top_k)

        scores, idxs = self._faiss_index.search(q2, fetch_k)

        hits: List[Tuple[str, float, Dict]] = []

        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(self._sample_ids):
                continue

            sample_id = self._sample_ids[idx]
            meta = dict(self._sample_meta.get(sample_id, {}))
            meta["sample_id"] = sample_id

            pet_id = meta.get("pet_id") or sample_id.split("__")[0]
            hits.append((pet_id, float(score), meta))

        if not dedupe:
            return [SearchResult(pet_id=pid, score=s, meta=m) for pid, s, m in hits[:top_k]]

        best: Dict[str, Tuple[float, Dict]] = {}
        for pid, s, m in hits:
            if pid not in best or s > best[pid][0]:
                best[pid] = (s, m)

        deduped = sorted(best.items(), key=lambda x: x[1][0], reverse=True)[:top_k]

        return [
            SearchResult(pet_id=pid, score=score, meta=meta)
            for pid, (score, meta) in deduped
        ]

    def save(self) -> None:
        """Persist FAISS index + meta.json."""
        if self._faiss_index is None:
            return

        faiss.write_index(self._faiss_index, str(self.faiss_path))

        payload = {
            "sample_ids": self._sample_ids,
            "sample_meta": self._sample_meta,
            "pet_counters": self._pet_counters,
        }

        with self.meta_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    # -------------------------------------------------
    # Demo helpers
    # -------------------------------------------------

    def total_samples(self) -> int:
        return len(self._sample_ids)

    def count_samples(self, pet_id: str) -> int:
        prefix = f"{pet_id}__"
        return sum(1 for sid in self._sample_ids if sid.startswith(prefix))
