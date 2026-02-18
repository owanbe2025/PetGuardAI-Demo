# backend/app/main.py
from __future__ import annotations

import secrets
import string
import traceback
from pathlib import Path
from typing import Optional
from uuid import uuid4

import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.embedding_service import get_model, image_to_embedding
from app.services.vector_index import VectorIndex
from app.services.pet_registry import PetRegistry, mask_contact  # ✅ import mask_contact




# -------------------------
# Paths
# -------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
TMP_DIR = DATA_DIR / "tmp_uploads"
INDEX_DIR = DATA_DIR / "vector_index"
REGISTRY_PATH = DATA_DIR / "pets.json"

TMP_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def _safe_delete(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


# -------------------------
# Payload models (JSON)
# -------------------------
class MarkMissingIn(BaseModel):
    pet_id: str = Field(..., min_length=1)
    last_seen_location: Optional[str] = ""
    last_seen_date: Optional[str] = ""   # keep string for MVP demo
    notes: Optional[str] = ""
    owner_name: Optional[str] = ""
    owner_contact: Optional[str] = ""    # phone/email (demo)
    share_code: Optional[str] = ""       # owner chooses code (optional)


class MarkFoundIn(BaseModel):
    pet_id: str = Field(..., min_length=1)
    found_location: Optional[str] = ""
    found_date: Optional[str] = ""
    finder_name: Optional[str] = ""
    finder_contact: Optional[str] = ""
    notes: Optional[str] = ""


class RequestContactIn(BaseModel):
    pet_id: str = Field(..., min_length=1)
    share_code: Optional[str] = ""


# -------------------------
# App setup
# -------------------------
app = FastAPI(title="PetGuard AI API")
@app.get("/")
def root():
    return {"status": "ok", "service": "PetGuard AI API", "docs": "/docs", "health": "/health"}

##@app.get("/health")
##def health():
##    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_index: Optional[VectorIndex] = None
_registry = PetRegistry(REGISTRY_PATH)

ALLOWED_CT = ("image/jpeg", "image/png", "image/jpg")


@app.on_event("startup")
def startup() -> None:
    # Preload TF model so first request is fast
    try:
        print("🚀 Startup: loading embedding model...")
        get_model()
        print("✅ Startup: model ready")
    except Exception as e:
        print("❌ Startup: failed to load model")
        print(repr(e))


# -------------------------
# Helpers
# -------------------------
def _suffix_for_content_type(ct: str) -> str:
    return ".png" if ct == "image/png" else ".jpg"


def _save_upload_to_temp(file: UploadFile, prefix: str) -> Path:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if file.content_type not in ALLOWED_CT:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    suffix = _suffix_for_content_type(file.content_type)
    safe_name = f"{prefix}_{uuid4().hex}{suffix}"
    return TMP_DIR / safe_name


def _new_share_code() -> str:
    # Example: PG-7F29A1
    alphabet = string.ascii_uppercase + string.digits
    return "PG-" + "".join(secrets.choice(alphabet) for _ in range(6))


def get_or_create_index(dim: int) -> VectorIndex:
    global _index
    if _index is None:
        _index = VectorIndex(dim=int(dim), storage_dir=str(INDEX_DIR))
    return _index


# -------------------------
# Endpoints
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register_pet")
async def register_pet(
    pet_id: str = Query(..., min_length=1),
    file: UploadFile = File(...),
    owner_name: Optional[str] = Form(None),
    owner_contact: Optional[str] = Form(None),
    consent_to_contact: bool = Form(False),
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if file.content_type not in ALLOWED_CT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    temp_path = _save_upload_to_temp(file, prefix=f"reg_{pet_id}")

    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        temp_path.write_bytes(data)

        emb = image_to_embedding(str(temp_path))
        if emb is None:
            raise RuntimeError("image_to_embedding returned None")

        emb = np.asarray(emb, dtype="float32").reshape(-1)
        if emb.ndim != 1 or emb.shape[0] == 0:
            raise RuntimeError(f"Invalid embedding shape: {emb.shape}")

        dim = int(emb.shape[0])
        index = get_or_create_index(dim=dim)

        sample_id = index.add(
            pet_id=pet_id,
            embedding=emb,
            meta={
                "filename": file.filename,
                "stored_as": temp_path.name,
                "content_type": file.content_type,
            },
        )
        index.save()

        # registry upsert + generate share_code if missing
        existing = _registry.get_pet(pet_id) or {}
        share_code = (existing.get("share_code") or "").strip() or _new_share_code()

        rec = _registry.upsert_pet(
            pet_id=pet_id,
            owner_name=owner_name,
            owner_contact=owner_contact,
            consent_to_contact=bool(consent_to_contact),
            share_code=share_code,
        )

        return {
            "ok": True,
            "pet_id": pet_id,
            "sample_id": sample_id,
            "dim": dim,
            "samples_for_pet": index.count_samples(pet_id),
            "missing": bool(rec.get("missing", False)),
            "share_code": rec.get("share_code", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{repr(e)}\n{tb}")

    finally:
        # Never let cleanup errors break the API response
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.post("/mark_missing")
def mark_missing(payload: MarkMissingIn):
    try:
        # ensure pet exists
        _registry.get_pet(payload.pet_id) or (_ for _ in ()).throw(KeyError("Unknown pet_id"))

        # store owner details if provided
        if (payload.owner_name or payload.owner_contact or payload.share_code):
            _registry.upsert_pet(
                pet_id=payload.pet_id,
                owner_name=payload.owner_name,
                owner_contact=payload.owner_contact,
                consent_to_contact=True if (payload.owner_contact and payload.owner_contact.strip()) else False,
                share_code=(payload.share_code or "").strip() or None,
            )

        rec = _registry.set_missing(payload.pet_id, True)

        _registry.set_missing_report(
            payload.pet_id,
            {
                "last_seen_location": payload.last_seen_location,
                "last_seen_date": payload.last_seen_date,
                "notes": payload.notes,
            },
        )

        return {"ok": True, "pet_id": payload.pet_id, "missing": True, "updated_at": rec.get("updated_at")}

    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown pet_id. Register pet first.")
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{repr(e)}\n{tb}")


@app.post("/mark_found")
def mark_found(payload: MarkFoundIn):
    try:
        rec = _registry.set_missing(payload.pet_id, False)

        _registry.add_found_report(
            payload.pet_id,
            {
                "found_location": payload.found_location,
                "found_date": payload.found_date,
                "finder_name": payload.finder_name,
                "finder_contact": payload.finder_contact,
                "notes": payload.notes,
            },
        )

        return {"ok": True, "pet_id": payload.pet_id, "missing": False, "updated_at": rec.get("updated_at")}

    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown pet_id.")
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{repr(e)}\n{tb}")


@app.post("/request_contact")
def request_contact(payload: RequestContactIn):
    try:
        out = _registry.contact_for_demo(payload.pet_id, share_code=payload.share_code)

        pet = _registry.get_pet(payload.pet_id) or {}
        out["missing"] = bool(pet.get("missing", False))
        out["owner_name"] = pet.get("owner_name", "")
        out["missing_report"] = pet.get("missing_report", {}) or {}

        fr = pet.get("found_reports", [])
        out["found_reports"] = fr if isinstance(fr, list) else []   # ✅ always list

        return {"ok": True, **out}

    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown pet_id.")
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{repr(e)}\n{tb}")

@app.post("/search_pet")
async def search_pet(
    file: UploadFile = File(...),
    top_k: int = Query(5, ge=1, le=50),
    dedupe: bool = Query(True),
    match_threshold: float = Query(0.70, ge=0.0, le=1.0),
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if file.content_type not in ALLOWED_CT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    temp_path = _save_upload_to_temp(file, prefix="search")

    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        temp_path.write_bytes(data)

        emb = image_to_embedding(str(temp_path))
        if emb is None:
            raise RuntimeError("image_to_embedding returned None")

        emb = np.asarray(emb, dtype="float32").reshape(-1)
        if emb.ndim != 1 or emb.shape[0] == 0:
            raise RuntimeError(f"Invalid embedding shape: {emb.shape}")

        dim = int(emb.shape[0])
        index = get_or_create_index(dim=dim)

        results = index.search(emb, top_k=int(top_k), dedupe=bool(dedupe))

        enriched = []
        for r in results:
            pet = _registry.get_pet(r.pet_id) or {}

            is_missing = bool(pet.get("missing", False))

            owner_contact = (pet.get("owner_contact") or "").strip()
            contact_masked = mask_contact(owner_contact) if owner_contact else ""

            # Only expose missing_report if the pet is currently missing
            missing_report = pet.get("missing_report") or {}
            if not is_missing:
                missing_report = {}

            enriched.append(
                {
                    "pet_id": r.pet_id,
                    "score": float(r.score),
                    "meta": r.meta,
                    "missing": is_missing,
                    "missing_report": missing_report,
                    "owner_name": pet.get("owner_name", ""),
                    "contact_masked": contact_masked,
                    "consent_to_contact": bool(pet.get("consent_to_contact", False)),
                }
            )

        best_score = enriched[0]["score"] if enriched else None
        second_score = enriched[1]["score"] if len(enriched) > 1 else None
        score_gap = (
            (best_score - second_score)
            if (best_score is not None and second_score is not None)
            else None
        )

        decision = "NO_MATCH"
        confidence = "LOW"
        if best_score is not None:
            if best_score >= match_threshold:
                decision = "MATCH_FOUND"
                confidence = "HIGH" if best_score >= min(0.90, match_threshold + 0.15) else "MEDIUM"
            else:
                decision = "POSSIBLE_MATCH" if best_score >= (match_threshold - 0.10) else "NO_MATCH"
                confidence = "MEDIUM" if decision == "POSSIBLE_MATCH" else "LOW"

        return {
            "ok": True,
            "dim": dim,
            "dedupe": bool(dedupe),
            "match_threshold": float(match_threshold),
            "best_score": best_score,
            "second_score": second_score,
            "score_gap": score_gap,
            "decision": decision,
            "confidence": confidence,
            "results": enriched,
        }

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{repr(e)}\n{tb}")

    finally:
        # Never let cleanup errors break the API response
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.post("/reset_index")
def reset_index(clear_registry: bool = Query(False)):
    global _index

    # Delete FAISS files
    for f in INDEX_DIR.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass
    _index = None

    # Optionally clear registry too
    if clear_registry:
        try:
            Path(REGISTRY_PATH).unlink(missing_ok=True)
        except Exception:
            pass

    return {
        "ok": True,
        "message": "Index cleared. Ready for new demo.",
        "registry_cleared": bool(clear_registry),
    }
