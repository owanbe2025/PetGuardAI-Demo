# backend/app/services/pet_registry.py
from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

_LOCK = threading.Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    _ensure_parent(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"pets": {}}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"pets": {}}
        if "pets" not in data or not isinstance(data["pets"], dict):
            data["pets"] = {}
        return data
    except Exception:
        # if corrupted: start clean (demo-safe)
        return {"pets": {}}


def mask_contact(contact: str) -> str:
    """
    Mask email/phone for safe demo sharing.
    """
    contact = (contact or "").strip()
    if not contact:
        return ""

    # Email
    if "@" in contact:
        name, domain = contact.split("@", 1)
        if len(name) <= 2:
            masked_name = name[:1] + "*"
        else:
            masked_name = name[:2] + "*" * max(3, len(name) - 2)

        parts = domain.split(".")
        if len(parts) >= 2:
            d0 = parts[0]
            masked_d0 = (d0[:1] + "*" * max(2, len(d0) - 1)) if d0 else "***"
            masked_domain = masked_d0 + "." + ".".join(parts[1:])
        else:
            masked_domain = "***"

        return f"{masked_name}@{masked_domain}"

    # Phone-ish: keep last 3 digits
    digits = re.sub(r"\D+", "", contact)
    if len(digits) >= 7:
        return re.sub(r"\d", "*", digits[:-3]) + digits[-3:]

    # fallback
    if len(contact) <= 3:
        return "*" * len(contact)
    return contact[:1] + "*" * (len(contact) - 3) + contact[-2:]


class PetRegistry:
    """
    Very small disk-backed registry (JSON) for MVP demo:
      pet_id -> owner + missing status + share_code
      + missing_report + found_reports
    """

    def __init__(self, json_path: str | Path):
        self.path = Path(json_path)

    def _read(self) -> Dict[str, Any]:
        with _LOCK:
            return _load_json(self.path)

    def _write(self, data: Dict[str, Any]) -> None:
        with _LOCK:
            _atomic_write_json(self.path, data)

    def upsert_pet(
        self,
        pet_id: str,
        owner_name: Optional[str] = None,
        owner_contact: Optional[str] = None,
        consent_to_contact: bool = False,
        share_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        pet_id = (pet_id or "").strip()
        if not pet_id:
            raise ValueError("pet_id is required")

        data = self._read()
        pets: Dict[str, Any] = data["pets"]

        existing = pets.get(pet_id, {})
        created_at = existing.get("created_at") or _utc_now_iso()

        record = {
            "pet_id": pet_id,
            "owner_name": (owner_name or existing.get("owner_name") or "").strip(),
            "owner_contact": (owner_contact or existing.get("owner_contact") or "").strip(),
            "consent_to_contact": (
                bool(consent_to_contact) if owner_contact else bool(existing.get("consent_to_contact", False))
            ),
            "share_code": (share_code or existing.get("share_code") or "").strip(),
            "missing": bool(existing.get("missing", False)),

            # NEW: store missing/found info
            "missing_report": existing.get("missing_report") or {},
            "found_reports": existing.get("found_reports") or [],

            "created_at": created_at,
            "updated_at": _utc_now_iso(),
        }

        pets[pet_id] = record
        data["pets"] = pets
        self._write(data)
        return record

    def set_missing(self, pet_id: str, missing: bool) -> Dict[str, Any]:
        data = self._read()
        pets: Dict[str, Any] = data["pets"]
        if pet_id not in pets:
            raise KeyError(f"Unknown pet_id: {pet_id}")

        pets[pet_id]["missing"] = bool(missing)
        pets[pet_id]["updated_at"] = _utc_now_iso()

        # Optional: if marking found, you may want to clear missing_report
        # Keep it for demo history unless you prefer clearing:
        # if not missing:
        #     pets[pet_id]["missing_report"] = {}

        data["pets"] = pets
        self._write(data)
        return pets[pet_id]

    def get_pet(self, pet_id: str) -> Optional[Dict[str, Any]]:
        data = self._read()
        return data["pets"].get(pet_id)

    # -----------------------------
    # NEW: missing/found reporting
    # -----------------------------

    def set_missing_report(self, pet_id: str, report: Dict[str, Any]) -> Dict[str, Any]:
        data = self._read()
        pets: Dict[str, Any] = data["pets"]
        if pet_id not in pets:
            raise KeyError(f"Unknown pet_id: {pet_id}")

        rep = dict(report or {})
        rep["updated_at"] = _utc_now_iso()
        pets[pet_id]["missing_report"] = rep
        pets[pet_id]["updated_at"] = _utc_now_iso()

        data["pets"] = pets
        self._write(data)
        return pets[pet_id]

    def get_missing_report(self, pet_id: str) -> Dict[str, Any]:
        pet = self.get_pet(pet_id)
        if not pet:
            raise KeyError(f"Unknown pet_id: {pet_id}")
        return pet.get("missing_report") or {}

    def add_found_report(self, pet_id: str, report: Dict[str, Any]) -> Dict[str, Any]:
        data = self._read()
        pets: Dict[str, Any] = data["pets"]
        if pet_id not in pets:
            raise KeyError(f"Unknown pet_id: {pet_id}")

        rep = dict(report or {})
        rep["created_at"] = _utc_now_iso()

        pets[pet_id].setdefault("found_reports", [])
        if not isinstance(pets[pet_id]["found_reports"], list):
            pets[pet_id]["found_reports"] = []

        pets[pet_id]["found_reports"].append(rep)
        pets[pet_id]["updated_at"] = _utc_now_iso()

        data["pets"] = pets
        self._write(data)
        return pets[pet_id]

    def list_found_reports(self, pet_id: str) -> List[Dict[str, Any]]:
        pet = self.get_pet(pet_id)
        if not pet:
            raise KeyError(f"Unknown pet_id: {pet_id}")
        fr = pet.get("found_reports") or []
        return fr if isinstance(fr, list) else []

    # -----------------------------
    # Contact gate for demo
    # -----------------------------

    def contact_for_demo(self, pet_id: str, share_code: Optional[str]) -> Dict[str, Any]:
        pet = self.get_pet(pet_id)
        if not pet:
            raise KeyError(f"Unknown pet_id: {pet_id}")

        consent = bool(pet.get("consent_to_contact", False))
        full = (pet.get("owner_contact") or "").strip()
        masked = mask_contact(full)

        # Safety: if no consent or no contact stored -> never reveal
        if (not consent) or (not full):
            return {
                "pet_id": pet_id,
                "allowed": False,
                "contact_masked": masked,
                "contact_full": None,
                "reason": "Owner has not provided consent/contact.",
            }

        expected = (pet.get("share_code") or "").strip()
        provided = (share_code or "").strip()

        if expected and provided and provided == expected:
            return {
                "pet_id": pet_id,
                "allowed": True,
                "contact_masked": masked,
                "contact_full": full,
                "reason": "Share code verified.",
            }

        return {
            "pet_id": pet_id,
            "allowed": False,
            "contact_masked": masked,
            "contact_full": None,
            "reason": "Share code missing/invalid. Use masked contact or request share code from owner.",
        }

    # Optional: wipe registry for demo resets
    def clear_all(self) -> None:
        self._write({"pets": {}})
