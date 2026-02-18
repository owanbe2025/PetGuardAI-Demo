\# PetGuard AI — Demo Repository (Public)



PetGuard AI is an AI-powered pet identification \& recovery platform that helps match lost pets using a photo — without relying on microchips or tags.



This public repository is a \*\*sanitized demo\*\* that showcases the \*\*architecture, API design, and end-to-end workflow\*\* (Register → Search → Match → Missing/Contact flows).  

✅ \*\*Model weights, private datasets, and secrets are intentionally excluded\*\* for IP/security hygiene.



---



\## What this demo repo contains



\- \*\*FastAPI backend (API design + endpoints)\*\*

&nbsp; - Register pet (ingest photos + metadata)

&nbsp; - Declare missing / mark found

&nbsp; - Finder search (photo → embedding → similarity search)

&nbsp; - Contact owner (masked contact + share code)

\- \*\*Streamlit demo UI\*\*

&nbsp; - Investor-grade demo flow for registration + search + results display



---



\## What is NOT included (by design)



To protect IP and user privacy, this repo does \*\*not\*\* include:

\- Trained model weights (`\*.keras`, `\*.h5`, etc.)

\- Any private datasets / real pet images

\- `.env`, Streamlit secrets, API keys

\- Production infra configs containing sensitive values



---



\## High-level AI approach (architecture)



PetGuard AI uses \*\*embedding-based recognition\*\* (similar to biometric verification):



1\) \*\*Image → Preprocessing\*\* (resize/normalize)

2\) \*\*Deep model → Embedding vector\*\* (e.g., 128-dim signature per photo)

3\) \*\*Vector search\*\* over enrolled pets (FAISS or similar)

4\) \*\*Decision logic\*\* (MATCH / POSSIBLE / NO\_MATCH) based on similarity + thresholds

5\) \*\*Registry layer\*\* stores owner/missing metadata and enforces masked contact



---



\## Repository structure

## Repository structure

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






