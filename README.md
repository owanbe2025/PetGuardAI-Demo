# 🐾 PetGuard AI — Public Demo Repository

PetGuard AI is an AI-powered pet identification and recovery platform that matches lost pets using only a photo — without relying on microchips or tags.

This repository contains a **sanitized demonstration version** of the system architecture, API structure, and end-to-end workflow.

⚠️ Model weights, private datasets, and production infrastructure are intentionally excluded for IP and security protection.

---

## 🚀 What This Demo Showcases

### 1️⃣ FastAPI Backend (Architecture Demonstration)

- Pet registration (photo ingestion + metadata)
- Mark pet as missing / found
- Finder photo search
- Similarity-based matching
- Masked owner contact flow

### 2️⃣ Streamlit Demo Interface

- Registration flow
- Search flow
- Match result display
- Decision explanation (MATCH / POSSIBLE / NO_MATCH)

---

## 🧠 High-Level AI Architecture

PetGuard AI uses an **embedding-based recognition system**, similar to biometric verification systems.

### Step 1 — Image Preprocessing
- Resize
- Normalize
- Format validation

### Step 2 — Deep Model → Embedding Vector
Each image is converted into a fixed-length numerical signature  
(e.g., 128-dimensional embedding vector).

### Step 3 — Vector Search
Embeddings are compared using similarity search  
(FAISS or equivalent vector index).

### Step 4 — Decision Logic
Based on similarity scores:
- MATCH_FOUND
- POSSIBLE_MATCH
- NO_MATCH

### Step 5 — Registry Layer
Stores:
- Pet metadata
- Missing status
- Masked contact logic
- Share-code protection

---

## 🏗 Repository Structure

```
backend/
  app/
    main.py
    services/
    utils/
  requirements.txt

frontend/
  petguard-ui/
    app.py

.gitignore
README.md
```

---

## 🔐 What Is NOT Included (By Design)

To protect intellectual property and user data, this repository does NOT include:

- Trained model weights (*.keras, *.h5, *.onnx, etc.)
- Private datasets or real pet images
- API keys or environment secrets
- Production deployment configuration
- Scaling infrastructure details

---

## 🧪 How To Run (Demo Only)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend/petguard-ui
streamlit run app.py
```

---

## ⚙️ Technology Stack

- Python
- FastAPI
- Streamlit
- TensorFlow / Keras (architecture demo)
- FAISS (vector similarity search)
- NumPy

---

## 🎯 Purpose of This Repository

This public demo is intended to:

- Demonstrate technical capability
- Showcase system design
- Provide architectural transparency
- Support investor and collaborator discussions

It is not the full production system.

---

## 📌 Project Status

MVP architecture validated.  
Production hardening and scaling in progress.

---

© 2026 PetGuard AI
