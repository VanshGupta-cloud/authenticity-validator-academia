# authenticity-validator-academia
Authenticity Validator for Academia (AVFA) is a tamper-proof document verification platform for Smart India Hackathon (PS: SIH25029). It leverages cryptographic SHA-256 hashing and simulated blockchain ledger technology to enable instant, single-click verification of academic credentials and eliminate degree forgery.
# 🎓 Authenticity Validator for Academia (AVFA)

![SIH Header](https://img.shields.io/badge/Smart_India_Hackathon-2025--2026-orange?style=for-the-badge)
![Problem Statement](https://img.shields.io/badge/Problem_Statement-SIH25029-blue?style=for-the-badge)
![Organization](https://img.shields.io/badge/Organization-Govt_of_Jharkhand-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Project_Status-Prototype-brightgreen?style=for-the-badge)

An automated, tamper-proof academic document verification system designed to eradicate degree fraud using cryptographic hashing and simulated decentralized consensus. Built for **Smart India Hackathon** under Problem Statement **SIH25029** (Government of Jharkhand).

---

## 📌 Problem Statement Overview

Academic credential fraud poses a severe threat to educational standards and employment integrity. Manual verification processes are slow, inefficient, and vulnerable to forgery. **AVFA** provides a high-trust digital ecosystem where institutions issue cryptographically signed certificates, and verifiers (employers/universities) can validate their authenticity in seconds.

---
## Team Members & Responsibilities

* **Hriddhima** *(Team Lead)* – FastAPI, Cryptography, Hashing
* **Avika Srivastava** – PDF + QR Generation, RapidFuzz
* **Anmol Sachan** – OpenCV, OCR Processing
* **Vansh Gupta** – Database (PostgreSQL), Version Control (Git/GitHub), Decentralized Storage (IPFS/Pinata)
* **Arpit Kesarvani** – System Design & Architecture
* **Divyansh Dubey** – Frontend Development (HTML, CSS, JavaScript, Tailwind CSS)
  
---
  
## 🚀 Key Features (Prototype Scope)

- **📄 Cryptographic Certificate Hashing:** Generates SHA-256 digital signatures for academic PDFs embedded into QR codes.
- **🔍 Drag-and-Drop Public Verifier:** One-click document verification interface showing instant **VALID** (Green) or **TAMPERED** (Red) feedback.
- **⚡ Bulk CSV & PDF Verification:** Simulates batch verification for high-volume HR and institutional workflows.
- **🔒 Mock Decentralized Ledger:** Uses smart contract mechanisms to guarantee immutable record-keeping without altering raw student PII.
- **🛡️ Revocation Management:** Allows authorized institutions to mark compromised credentials as revoked in real time.

---

## 🏗️ System Architecture

```text
[ Issuer / University ]
        │
        ▼ (Uploads PDF / Metadata)
[ Hashing Pipeline ] ──► Computes SHA-256 Hash & Embeds QR Code
        │
        ▼
[ Blockchain Ledger / Mock JSON ] ◄── Stores Salted Cryptographic Hashes
        │
        ▼
[ Verifier / Employer ] ──► Scans QR / Drops PDF ──► Instant Validation Screen
