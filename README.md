# 🐾 PetGuard AI / PetFound AI — Public Demo Repository

![Status](https://img.shields.io/badge/status-MVP--Validated-blue)
![Architecture](https://img.shields.io/badge/architecture-Embedding--Based-green)
![Backend](https://img.shields.io/badge/backend-FastAPI-orange)
![Frontend](https://img.shields.io/badge/frontend-Streamlit-red)

PetGuard AI is an **AI-powered pet identification and recovery platform** that matches lost pets using only a photo — without relying on microchips or tags.

This repository contains a **sanitized public demo** of the system architecture, backend services, and AI workflow.

⚠️ **Sensitive components such as model weights, datasets, and production infrastructure are intentionally excluded for IP and security protection.**

---

## 🚀 Live Demo & What It Does

### ⚡ Core Capability
- Upload a pet image
- Generate AI embeddings
- Perform similarity search
- Return match confidence

### 🧪 Demo Features
- Pet registration (image + metadata)
- Missing pet reporting
- Finder upload & search
- AI similarity matching
- Decision output:
  - `MATCH`
  - `POSSIBLE_MATCH`
  - `NO_MATCH`

---

## 💡 How It Works (1-Minute Overview)

PetGuard AI uses **deep metric learning** instead of traditional classification.

Instead of predicting a class (e.g., “dog”), the system:

1. Converts each image into a **numerical embedding vector**
2. Stores embeddings in a **vector index**
3. Compares new images using **similarity search**
4. Determines identity based on similarity thresholds

👉 This enables identification of **individual pets**, not just species.

---

## 🧠 System Architecture

Frontend (Streamlit UI)
↓
FastAPI Backend
↓
Image Preprocessing Pipeline
↓
Embedding Model (TensorFlow/Keras)
↓
Vector Index (FAISS / Similarity Engine)
↓
Decision Logic (Threshold-Based)
↓
Pet Registry (Metadata + Status + Contact Layer)



---

## 🔍 AI Pipeline Breakdown

### 1️⃣ Image Preprocessing
- Resize & normalize
- Format validation
- Input standardization

### 2️⃣ Embedding Generation
- Deep learning model converts image → vector (e.g., 128-dim)
- Each pet has a unique numerical signature

### 3️⃣ Similarity Search
- Cosine similarity / nearest neighbor search
- Efficient lookup via FAISS (or equivalent)

### 4️⃣ Decision Engine
Based on similarity score thresholds:

- `MATCH` → Strong identity match  
- `POSSIBLE_MATCH` → Requires verification  
- `NO_MATCH` → No close similarity  

### 5️⃣ Registry Layer
Handles:
- Pet metadata storage
- Missing/Found state
- Masked owner contact
- Share-code security logic

---

## ⚙️ Key Engineering Features

- Embedding-based recognition (metric learning approach)
- Modular FastAPI backend architecture
- Vector similarity search pipeline
- Threshold-based decision system
- Image preprocessing service layer
- Clean separation of backend and UI
- Streamlit interface for rapid prototyping & demo

---

## 🏗 Repository Structure


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


---

## 🛠️ Run Locally (Demo Setup)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

Frontend

cd frontend/petguard-ui
streamlit run app.py

⚙️ Technology Stack
Python
FastAPI
Streamlit
TensorFlow / Keras (architecture demo)
FAISS (vector similarity search)
NumPy

🔒 Security & IP Notice

This repository is a public demo version of PetGuard AI.

The following are intentionally excluded:

Trained model weights
Datasets
Real pet images / user data
API keys and environment secrets
Production infrastructure & deployment configs
Scaling and optimization strategies

This ensures intellectual property protection while demonstrating system design and capabilities.

🎯 Purpose of This Repository

This demo is designed to:

Showcase AI system architecture
Demonstrate backend + ML integration
Present a working similarity-based recognition pipeline
Support discussions with employers, collaborators, and investors.

📌 Project Status

✅ MVP architecture validated
🚧 Production hardening and scaling in progress...


🧠 Author

Adekunle Adegoke
AI Systems Engineer | FastAPI | Machine Learning | AI Infrastructure

© 2026 PetGuard AI

