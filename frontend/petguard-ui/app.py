# app.py
# PetGuard AI — Streamlit Demo UI (Production-Quality MVP)
# Run: streamlit run app.py

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import time
import requests
import streamlit as st


# =========================
# Paths
# =========================
APP_DIR = Path(__file__).resolve().parent
ASSETS_DIR = APP_DIR / "assets"


# =========================
# Backend URL resolver
# =========================

API_BASE_URL = st.secrets["API_BASE_URL"].rstrip("/")

import time
import requests


def api_health(base_url: str):
    """
    Checks FastAPI health endpoint.
    Handles Render cold starts with retry.
    Returns:
        ok (bool), latency_ms (float | None)
    """
    health_url = f"{base_url.rstrip('/')}/health"

    for _ in range(2):  # retry once for cold start
        try:
            t0 = time.perf_counter()
            r = requests.get(
                health_url,
                timeout=30,  # important for Render free tier
                allow_redirects=True,
                headers={"User-Agent": "PetGuardAI-Healthcheck"},
            )
            latency_ms = (time.perf_counter() - t0) * 1000

            if r.status_code == 200:
                return True, latency_ms

        except Exception:
            pass

        time.sleep(1)

    return False, None


def read_api_base_url() -> str:
    """
    Read API base URL from Streamlit secrets first, then env var, then fallback.
    Safe even if Streamlit secrets are missing.
    """
    # 1) Streamlit Cloud Secrets
    try:
        v = str(st.secrets.get("API_BASE_URL", "")).strip()
        if v:
            return v
    except Exception:
        pass

    # 2) Environment variable
    v = (os.getenv("API_BASE_URL") or "").strip()
    if v:
        return v

    # 3) Fallback (local FastAPI)
    return "http://127.0.0.1:8000"


def safe_secret(key: str, default: str = "<missing>") -> str:
    """Never crash if secrets are not configured."""
    try:
        return str(st.secrets.get(key, default)).strip()
    except Exception:
        return default


# Compute "cloud default" every run (so when you fix secrets it auto-picks it up)
CLOUD_DEFAULT_API_BASE_URL = read_api_base_url()

TIMEOUT_SECONDS = 30


# =========================
# Page setup
# =========================
st.set_page_config(
    page_title="PetGuard AI — Demo",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# Styling
# =========================
def inject_global_css() -> None:
    st.markdown(
        """
        <style>
          .block-container { padding-top: 3.25rem; padding-bottom: 2.5rem; max-width: 1200px; }
          h1, h2, h3, h4 { scroll-margin-top: 80px; }

          html, body, [class*="css"]  { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial; }

          [data-testid="stAppViewContainer"]{
            background: linear-gradient(180deg,
              rgba(255,245,246,0.55) 0%,
              rgba(255,255,255,1) 30%,
              rgba(245,250,255,0.9) 100%);
          }

          [data-testid="stSidebar"]{
            background: rgba(255,255,255,0.92);
            border-right: 1px solid rgba(15, 23, 42, 0.06);
          }

          .pg-home-hero {
            background: linear-gradient(135deg,
              rgba(255, 226, 230, 0.95) 0%,
              rgba(224, 242, 254, 0.95) 55%,
              rgba(255, 255, 255, 0.88) 100%);
            border: 1px solid rgba(15, 23, 42, 0.10);
            border-radius: 24px;
            padding: 26px 26px 18px 26px;
            box-shadow: 0 14px 40px rgba(15, 23, 42, 0.10);
            position: relative;
            overflow: hidden;
          }

          .pg-hero-badge {
            display: inline-flex;
            gap: 8px;
            align-items: center;
            padding: 7px 12px;
            border-radius: 999px;
            font-size: 12px;
            color: rgba(15, 23, 42, 0.82);
            background: rgba(255, 255, 255, 0.65);
            border: 1px solid rgba(15, 23, 42, 0.10);
          }

          .pg-home-title {
            text-align: center;
            font-size: 52px;
            font-weight: 860;
            letter-spacing: -0.035em;
            margin: 14px 0 6px 0;
            color: rgba(15, 23, 42, 0.94);
          }

          .pg-home-tagline {
            text-align: center;
            font-size: 18px;
            font-weight: 820;
            color: rgba(244, 63, 94, 0.95);
            margin: 0 0 10px 0;
          }

          .pg-home-mission {
            text-align: center;
            font-size: 15px;
            line-height: 1.7;
            color: rgba(15, 23, 42, 0.78);
            max-width: 860px;
            margin: 0 auto 6px auto;
          }

          .pg-note {
            margin-top: 14px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(15, 23, 42, 0.07);
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
          }

          .pg-tiles {
            margin-top: 14px;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
          }
          @media (max-width: 1100px) { .pg-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
          @media (max-width: 650px)  { .pg-tiles { grid-template-columns: repeat(1, minmax(0, 1fr)); } }

          .pg-tile {
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 14px 14px;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
            min-height: 96px;
          }
          .pg-tile-top { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
          .pg-icon {
            width: 34px; height: 34px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            background: rgba(224, 242, 254, 0.75);
            border: 1px solid rgba(15, 23, 42, 0.06);
            font-size: 16px;
          }
          .pg-tile-title { font-weight: 800; color: rgba(15, 23, 42, 0.92); letter-spacing: -0.01em; }
          .pg-tile-desc { color: rgba(15, 23, 42, 0.68); font-size: 13.5px; line-height: 1.45; }

          .pg-section-title {
            font-size: 18px;
            font-weight: 760;
            color: rgba(15,23,42,0.92);
            margin: 8px 0 10px 0;
            letter-spacing: -0.01em;
          }

          .pg-result {
            border-radius: 16px;
            padding: 14px 16px;
            border: 1px solid rgba(15, 23, 42, 0.08);
            background: rgba(255,255,255,0.86);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
          }
          .pg-result-title { font-size: 16px; font-weight: 850; letter-spacing: -0.01em; margin: 0 0 8px 0; }
          .pg-kv {
            display: grid;
            grid-template-columns: 160px 1fr;
            gap: 10px;
            align-items: center;
            padding: 8px 0;
            border-top: 1px dashed rgba(15, 23, 42, 0.10);
          }
          .pg-kv:first-of-type { border-top: none; }
          .pg-k { color: rgba(15, 23, 42, 0.62); font-size: 13px; }
          .pg-v { color: rgba(15, 23, 42, 0.92); font-size: 14px; font-weight: 650; }

          .pg-footer {
            margin-top: 26px;
            padding-top: 14px;
            border-top: 1px solid rgba(15, 23, 42, 0.08);
            color: rgba(15, 23, 42, 0.55);
            font-size: 12.5px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# API helpers
# =========================
def get_api_base_url() -> str:
    """
    Session-state aware base url.
    In cloud mode, always use secret default unless DEBUG_UI is enabled.
    Normalizes localhost variants.
    """
    default = read_api_base_url().strip().rstrip("/")  # e.g. https://petguardai-mvp.onrender.com
    debug_ui = bool(st.secrets.get("DEBUG_UI", False))

    current = str(st.session_state.get("api_base_url", "")).strip().rstrip("/")

    # In non-debug (investor/demo) mode: force cloud default every run
    if not debug_ui:
        st.session_state.api_base_url = default
        return default

    # In debug mode: allow override, but auto-correct localhost-ish/empty values to default
    localhost_variants = {
        "",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "127.0.0.1:8000",
        "localhost:8000",
    }

    if current in localhost_variants:
        st.session_state.api_base_url = default
        return default

    # otherwise keep user's override
    st.session_state.api_base_url = current
    return current


def api_url(path: str) -> str:
    base = get_api_base_url().rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}{path}"


def safe_json(resp: requests.Response) -> Dict[str, Any]:
    try:
        return resp.json()
    except Exception:
        return {"raw_text": resp.text}


def request_post(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Dict[str, Any], str]:
    try:
        resp = requests.post(
            url,
            params=params,
            json=json_body,
            files=files,
            data=data,
            timeout=TIMEOUT_SECONDS,
        )
        payload = safe_json(resp)
        if 200 <= resp.status_code < 300:
            return True, payload, ""
        msg = payload.get("detail") or payload.get("message") or payload.get("error") or resp.text
        return False, payload, f"API error ({resp.status_code}): {msg}"
    except requests.exceptions.ConnectionError:
        return False, {}, f"Cannot connect to backend at {get_api_base_url()}."
    except requests.exceptions.Timeout:
        return False, {}, "Request timed out. The backend may be busy or model inference is taking too long."
    except Exception as e:
        return False, {}, f"Unexpected error: {e}"


# =========================
# UI helpers
# =========================
def format_bool(v: Any) -> str:
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if v is None:
        return "—"
    return str(v)


def render_kv_card(title: str, tone: str, fields: Dict[str, Any]) -> None:
    if tone == "success":
        badge = "✅"
        title_color = "rgba(34,197,94,0.95)"
    elif tone == "warning":
        badge = "⚠️"
        title_color = "rgba(245,158,11,0.95)"
    else:
        badge = "ℹ️"
        title_color = "rgba(100,116,139,0.95)"

    rows_html = ""
    for k, v in fields.items():
        rows_html += f"""
          <div class="pg-kv">
            <div class="pg-k">{k}</div>
            <div class="pg-v">{v}</div>
          </div>
        """

    st.markdown(
        f"""
        <div class="pg-result">
          <div class="pg-result-title" style="color:{title_color};">{badge} {title}</div>
          {rows_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_search_status(payload: Dict[str, Any]) -> str:
    candidates = [
        payload.get("status"),
        payload.get("match_status"),
        payload.get("verdict"),
        payload.get("result"),
        payload.get("outcome"),
    ]
    raw = next((c for c in candidates if isinstance(c, str) and c.strip()), "").upper().strip()

    mapping = {
        "MATCH_FOUND": "MATCH_FOUND",
        "FOUND": "MATCH_FOUND",
        "MATCH": "MATCH_FOUND",
        "EXACT_MATCH": "MATCH_FOUND",
        "POSSIBLE_MATCH": "POSSIBLE_MATCH",
        "LIKELY_MATCH": "POSSIBLE_MATCH",
        "CANDIDATE_MATCH": "POSSIBLE_MATCH",
        "NO_MATCH": "NO_MATCH",
        "NOT_FOUND": "NO_MATCH",
        "NONE": "NO_MATCH",
    }
    if raw in mapping:
        return mapping[raw]

    conf = payload.get("confidence") or payload.get("score") or payload.get("similarity")
    try:
        conf_f = float(conf)
        if conf_f >= 0.85:
            return "MATCH_FOUND"
        if conf_f >= 0.65:
            return "POSSIBLE_MATCH"
        return "NO_MATCH"
    except Exception:
        return "NO_MATCH"


#=========================
# Sidebar navigation
# =========================
def sidebar_nav() -> str:
    with st.sidebar:
        st.markdown("### 🐾 PetGuard AI")
        st.caption("Demo Interface • Safety-first • Investor-grade")
        st.write("")

        # --- Base URL setup ---
        cloud_default = read_api_base_url().strip().rstrip("/")
        DEBUG_UI = bool(st.secrets.get("DEBUG_UI", False))

        # Initialize session state once
        if "api_base_url" not in st.session_state:
            st.session_state.api_base_url = cloud_default

        # In investor/demo mode, force cloud URL always
        if not DEBUG_UI:
            st.session_state.api_base_url = cloud_default

        # Resolve actual base URL
        api_url = get_api_base_url().strip().rstrip("/")

        # --- Health check ---
        ok, latency = api_health(api_url)

        st.markdown("**System Status**")

        if ok:
            st.success("API Connected")
            if latency is not None:
                st.caption(f"Latency: {latency:.0f} ms")
        else:
            st.warning("Warming up server…")
            st.caption("If this persists, refresh the page.")

        # --- Developer controls ---
        if DEBUG_UI:
            st.write("")
            st.markdown("**Backend (Developer)**")

            st.session_state.api_base_url = st.text_input(
                "FastAPI Base URL",
                value=st.session_state.api_base_url,
                help="Render URL for cloud, localhost for local testing.",
            ).strip()

            c1, c2 = st.columns(2)

            with c1:
                if st.button("Reset to Cloud", use_container_width=True):
                    st.session_state.api_base_url = cloud_default
                    st.rerun()

            with c2:
                if st.button("Use Localhost", use_container_width=True):
                    st.session_state.api_base_url = "http://127.0.0.1:8000"
                    st.rerun()

        st.write("")
        page = st.radio(
            "Navigate",
            options=[
                "Home",
                "Register Pet",
                "Declare Missing",
                "Finder Upload (Search)",
                "Contact Owner",
            ],
            index=0,
        )

        st.markdown("---")
        st.caption(
            "Tip: Start on **Home**, then **Register Pet**, mark **Missing**, "
            "and test via **Finder Upload**."
        )

        return page


# =========================
# Home Page
# =========================
def page_home() -> None:
    hero_html = """
    <div class="pg-home-hero">
      <div style="display:flex; justify-content:center;">
        <div class="pg-hero-badge">🐾 <span>PetGuard AI Demo • Pet Care • Safety-first • Investor-grade</span></div>
      </div>

      <div class="pg-home-title">PetGuard AI</div>
      <div class="pg-home-tagline"><strong>PetGuard AI — Shaping the Future of Pet Safety</strong></div>

      <div class="pg-home-mission">
        PetGuard AI is an AI-powered mobile platform that helps identify lost pets using just a photo —
        no microchips, collars, or tags required. By harnessing the power of Artificial Intelligence,
        we aim to make pet recovery faster, smarter, and more reliable for pet owners, shelters,
        and communities everywhere.
      </div>
    </div>

    <div class="pg-note">
      <strong>Every year, thousands of pets go missing.</strong><br/>
      PetGuard AI is building a smarter way to bring them home.
    </div>

    <div class="pg-tiles">
      <div class="pg-tile">
        <div class="pg-tile-top">
          <div class="pg-icon">📷</div>
          <div class="pg-tile-title">Photo-based Identification</div>
        </div>
        <div class="pg-tile-desc">Match a found pet to registered photos in seconds — fast and practical.</div>
      </div>

      <div class="pg-tile">
        <div class="pg-tile-top">
          <div class="pg-icon">🔔</div>
          <div class="pg-tile-title">Missing Alerts</div>
        </div>
        <div class="pg-tile-desc">Owners can mark pets as missing so the community can respond quickly.</div>
      </div>

      <div class="pg-tile">
        <div class="pg-tile-top">
          <div class="pg-icon">🛡️</div>
          <div class="pg-tile-title">Privacy-first Contact</div>
        </div>
        <div class="pg-tile-desc">Masked contact by default — owners stay in control of what’s revealed.</div>
      </div>

      <div class="pg-tile">
        <div class="pg-tile-top">
          <div class="pg-icon">❤️</div>
          <div class="pg-tile-title">Community Support</div>
        </div>
        <div class="pg-tile-desc">Built for owners, shelters, and neighbours working together to reunite pets.</div>
      </div>
    </div>
    """

    st.markdown(hero_html, unsafe_allow_html=True)
    st.write("")

    # Images: reliable online
    dog_path = ASSETS_DIR / "dog.png"
    cat_path = ASSETS_DIR / "cat.png"

    # If png not found, fallback to jpg (in case you renamed files)
    if not dog_path.exists():
        dog_path = ASSETS_DIR / "dog.jpg"
    if not cat_path.exists():
        cat_path = ASSETS_DIR / "cat.jpg"

    c1, c2, c3 = st.columns([1, 1, 1], gap="large")
    with c1:
        if dog_path.exists():
            st.image(str(dog_path), width="stretch")
        else:
            st.warning("dog image missing in assets/")
    with c2:
        if cat_path.exists():
            st.image(str(cat_path), width="stretch")
        else:
            st.warning("cat image missing in assets/")
    with c3:
        if dog_path.exists():
            st.image(str(dog_path), width="stretch")

    st.write("")

    st.markdown('<div class="pg-section-title">Get started</div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 1.2], gap="medium")

    with b1:
        if st.button("Register Your Pet", type="primary", width="stretch"):
            st.info("Use the sidebar → **Register Pet** to upload your pet photos and create a secure Pet ID.")
    with b2:
        if st.button("Search for a Found Pet", width="stretch"):
            st.info("Use the sidebar → **Finder Upload (Search)** to upload a photo and check for matches.")
    with b3:
        st.caption("Tip: Register 3–6 clear photos (face + body, different angles, good lighting).")


# =========================
# Workflow Pages
# =========================
def page_register_pet() -> None:
    st.markdown('<div class="pg-section-title">Register Pet</div>', unsafe_allow_html=True)
    st.caption("Owners can upload multiple photos to register their pet securely.")

    colA, colB = st.columns([1.1, 0.9], gap="large")
    with colA:
        with st.form("register_pet_form", clear_on_submit=False):
            pet_id = st.text_input("Pet ID", placeholder="e.g., RABBIT-10293")
            owner_name = st.text_input("Owner Name", placeholder="e.g., Sarah Johnson")
            owner_contact = st.text_input("Owner Contact (email or phone)", placeholder="e.g., sarah@email.com or +44...")
            consent = st.checkbox("I consent to be contacted if my pet is found.", value=False)

            images = st.file_uploader(
                "Upload Pet Images (multiple)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
            )

            submitted = st.form_submit_button("Register Pet", use_container_width=True)

        if submitted:
            if not pet_id.strip():
                st.error("Please enter a Pet ID.")
                return
            if not owner_name.strip():
                st.error("Please enter the Owner Name.")
                return
            if not owner_contact.strip():
                st.error("Please enter the Owner Contact.")
                return
            if not consent:
                st.warning("Consent is required before registration.")
                return
            if not images:
                st.error("Please upload at least one image.")
                return

            st.info("Registering your pet…")
            share_code: Optional[str] = None
            success_count = 0

            for i, img in enumerate(images, start=1):
                files = {"file": (img.name, img.getvalue(), img.type or "application/octet-stream")}
                data = {
                    "owner_name": owner_name,
                    "owner_contact": owner_contact,
                    "consent_to_contact": str(consent).lower(),
                }
                ok, payload, err = request_post(
                    api_url("/register_pet"),
                    params={"pet_id": pet_id},
                    files=files,
                    data=data,
                )

                if ok:
                    success_count += 1
                    sc = payload.get("share_code") or payload.get("shareCode") or payload.get("code")
                    if isinstance(sc, str) and sc.strip():
                        share_code = sc.strip()
                else:
                    st.error(f"Image {i} failed: {err}")

            if success_count == len(images):
                st.success("Pet registered successfully ✅")
            elif success_count > 0:
                st.warning(f"Partially registered: {success_count}/{len(images)} images uploaded.")
            else:
                st.error("Registration failed.")
                return

            if share_code:
                st.session_state.setdefault("share_codes", {})
                st.session_state["share_codes"][pet_id] = share_code

                render_kv_card(
                    "Share Code Returned",
                    "neutral",
                    {
                        "Share Code": f"<code>{share_code}</code>",
                        "What this means": "This code allows finders to securely contact you.",
                    },
                )

    with colB:
        st.markdown("#### ✨ What owners get")
        st.write(
            "- A secure Pet ID record\n"
            "- Photo-based identity matching\n"
            "- Missing status tracking\n"
            "- Privacy-aware contact flow"
        )


def page_declare_missing() -> None:
    st.markdown('<div class="pg-section-title">Declare Pet Missing</div>', unsafe_allow_html=True)
    st.caption("Mark a pet as missing so finders can help reunite them quickly.")

    colA, colB = st.columns([1.05, 0.95], gap="large")
    with colA:
        with st.form("missing_form", clear_on_submit=False):
            pet_id = st.text_input("Pet ID", placeholder="e.g., RABBIT-10293")
            last_seen_location = st.text_input("Last Seen Location", placeholder="e.g., Belfast City Centre")
            last_seen_date = st.date_input("Last Seen Date", value=date.today())
            notes = st.text_area("Notes (optional)", placeholder="e.g., Skittish, responds to 'Milo'…")

            submitted = st.form_submit_button("Mark as Missing", use_container_width=True)

        if submitted:
            if not pet_id.strip():
                st.error("Please enter a Pet ID.")
                return
            if not last_seen_location.strip():
                st.error("Please enter a Last Seen Location.")
                return

            body = {
                "pet_id": pet_id.strip(),
                "last_seen_location": last_seen_location.strip(),
                "last_seen_date": str(last_seen_date),
                "notes": notes.strip(),
            }
            ok, payload, err = request_post(api_url("/mark_missing"), json_body=body)

            if ok:
                st.success("Your pet has been marked as missing ✅")
                render_kv_card(
                    "Missing Report Saved",
                    "warning",
                    {
                        "Pet ID": body["pet_id"],
                        "Last seen": body["last_seen_location"],
                        "Date": body["last_seen_date"],
                        "Notes": body["notes"] or "—",
                    },
                )
            else:
                st.error(err)
                with st.expander("Technical details"):
                    st.json(payload)

    with colB:
        st.markdown("#### 🧡 Gentle guidance")
        st.caption("Post clear photos, contact local shelters, and share the Pet ID with community groups.")


def page_finder_upload_search() -> None:
    st.markdown('<div class="pg-section-title">Found a Pet?</div>', unsafe_allow_html=True)
    st.caption("Upload a photo to check if the pet is registered in PetGuard AI.")

    # Investor-safe threshold (prevents cross-dog false matches like ~0.602)
    DEMO_MATCH_THRESHOLD = 0.65

    colA, colB = st.columns([1.05, 0.95], gap="large")

    with colA:
        img = st.file_uploader(
            "Upload a single photo (Finder)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
        )

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            search_clicked = st.button(
                "Search Pet",
                type="primary",
                use_container_width=True,
                disabled=(img is None),
            )
        with c2:
            st.button(
                "Clear",
                use_container_width=True,
                on_click=lambda: st.session_state.pop("last_search", None),
            )
        with c3:
            st.write("")

        # ✅ Preview using bytes (prevents consuming the file stream)
        if img is not None:
            try:
                st.image(img.getvalue(), caption="Finder upload preview", use_container_width=True)
            except Exception:
                st.image(img, caption="Finder upload preview", use_container_width=True)

        if search_clicked and img is not None:
            # ✅ Read bytes ONCE (critical)
            img_bytes = img.getvalue()
            if not img_bytes:
                render_kv_card(
                    "UPLOAD ERROR",
                    "warning",
                    {"Reason": "Empty upload bytes. Please re-upload the image and try again."},
                )
                return

            files = {
                "file": (img.name, img_bytes, img.type or "application/octet-stream")
            }

            params = {
                "top_k": 5,
                "dedupe": True,
                "match_threshold": DEMO_MATCH_THRESHOLD,
            }

            # ✅ Spinner ends automatically; no stuck "Searching..."
            with st.spinner("Searching…"):
                ok, payload, err = request_post(
                    api_url("/search_pet"),
                    params=params,
                    files=files,
                )

            if not ok:
                st.error(err)
                with st.expander("Technical details"):
                    try:
                        st.json(payload)
                    except Exception:
                        st.write(payload)
                return

            # ✅ Align to backend response shape
            decision = (payload.get("decision") or "NO_MATCH").upper().strip()
            confidence = (payload.get("confidence") or "LOW").upper().strip()
            best_score = payload.get("best_score", None)
            second_score = payload.get("second_score", None)
            score_gap = payload.get("score_gap", None)
            results = payload.get("results") or []

            # top candidate
            top = results[0] if results else {}
            pet_id = top.get("pet_id") or "—"
            owner_name = top.get("owner_name") or "—"
            is_missing = bool(top.get("missing", False))
            score = top.get("score", best_score)

            # pretty scores
            score_str = "—"
            try:
                if score is not None:
                    score_str = f"{float(score):.3f}"
            except Exception:
                if score is not None:
                    score_str = str(score)

            gap_str = ""
            try:
                if score_gap is not None:
                    gap_str = f"{float(score_gap):.3f}"
            except Exception:
                gap_str = ""

            second_str = ""
            try:
                if second_score is not None:
                    second_str = f"{float(second_score):.3f}"
            except Exception:
                second_str = ""

            # Render result cards (investor-grade)
            if decision == "MATCH_FOUND":
                render_kv_card(
                    "MATCH FOUND",
                    "success",
                    {
                        "Pet ID": pet_id,
                        "Owner Name": owner_name,
                        "Missing status": format_bool(is_missing),
                        "Similarity score": score_str,
                        "Confidence": confidence,
                        **({"Second score": second_str} if second_str else {}),
                        **({"Score gap": gap_str} if gap_str else {}),
                    },
                )

            elif decision == "POSSIBLE_MATCH":
                render_kv_card(
                    "POSSIBLE MATCH",
                    "warning",
                    {
                        "Top candidate": pet_id,
                        "Owner Name": owner_name,
                        "Missing status": format_bool(is_missing),
                        "Similarity score": score_str,
                        "Confidence": confidence,
                        "Next step": "Try a clearer photo / closer crop (face/body visible) and search again.",
                        **({"Second score": second_str} if second_str else {}),
                        **({"Score gap": gap_str} if gap_str else {}),
                    },
                )

            else:
                # NO_MATCH: show closest candidate if available (helps credibility)
                if top:
                    render_kv_card(
                        "NO STRONG MATCH",
                        "neutral",
                        {
                            "Closest candidate": pet_id,
                            "Similarity score": score_str,
                            "Confidence": confidence,
                            "Result": f"No match above threshold ({DEMO_MATCH_THRESHOLD:.2f})",
                            "Next step": "Try a clearer photo and search again.",
                            **({"Second score": second_str} if second_str else {}),
                            **({"Score gap": gap_str} if gap_str else {}),
                        },
                    )
                else:
                    render_kv_card(
                        "NO MATCH",
                        "neutral",
                        {
                            "Result": "No candidates returned",
                            "Next step": "Try a clearer photo and search again.",
                        },
                    )

            # Optional debug (enable temporarily if needed)
            # with st.expander("Debug (raw backend response)"):
            #     st.json(payload)

    with colB:
        st.markdown("#### 🧭 What to do if you found a pet")
        st.write(
            "1) Ensure the pet is safe\n"
            "2) Take a clear photo\n"
            "3) Search in PetGuard AI\n"
            "4) If matched, contact the owner securely"
        )


def page_contact_owner() -> None:
    st.markdown('<div class="pg-section-title">Contact Owner</div>', unsafe_allow_html=True)
    st.caption("Masked contact is shown by default; full details require a valid share code.")

    colA, colB = st.columns([1.05, 0.95], gap="large")
    with colA:
        pet_id = st.text_input("Pet ID", placeholder="e.g., RABBIT-10293")

        stored_share = ""
        if pet_id and "share_codes" in st.session_state and pet_id in st.session_state["share_codes"]:
            stored_share = st.session_state["share_codes"][pet_id]

        share_code = st.text_input("Share Code (optional)", value=stored_share, placeholder="e.g., PG-7F9A2C")

        request_clicked = st.button("Request Contact", type="primary", use_container_width=True)

        if request_clicked:
            if not pet_id.strip():
                st.error("Please enter a Pet ID.")
                return

            body = {"pet_id": pet_id.strip()}
            if share_code.strip():
                body["share_code"] = share_code.strip()

            ok, payload, err = request_post(api_url("/request_contact"), json_body=body)

            if not ok:
                st.error(err)
                with st.expander("Technical details"):
                    st.json(payload)
                return

            masked = payload.get("masked_contact") or payload.get("masked") or payload.get("contact_masked") or "—"
            full = payload.get("full_contact") or payload.get("owner_contact") or payload.get("contact_full")

            fields = {"Masked contact": masked}
            if full:
                fields["Full contact"] = full
                tone = "success"
                title = "Contact Verified"
            else:
                fields["Full contact"] = "Hidden (provide valid Share Code to unlock)"
                tone = "warning" if share_code.strip() else "neutral"
                title = "Contact Request Created"

            render_kv_card(title, tone, fields)

    with colB:
        st.markdown("#### 🤝 A secure way to reconnect")
        st.caption("Owner privacy is protected. Full contact is only revealed with a valid Share Code.")


# =========================
# Main
# =========================
def main() -> None:
    inject_global_css()
    page = sidebar_nav()

    if page == "Home":
        page_home()
    elif page == "Register Pet":
        page_register_pet()
    elif page == "Declare Missing":
        page_declare_missing()
    elif page == "Finder Upload (Search)":
        page_finder_upload_search()
    elif page == "Contact Owner":
        page_contact_owner()
    else:
        st.error("Unknown page selection.")

    st.markdown(
        """
        <div class="pg-footer">
          PetGuard AI Demo v1.0 — Built with AI for safer pet recovery.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
