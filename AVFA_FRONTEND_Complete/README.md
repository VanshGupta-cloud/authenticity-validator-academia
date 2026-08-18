# Authenticity Validator for Academia (AVFA)

![SIH Header](https://img.shields.io/badge/Smart_India_Hackathon-2025--2026-orange?style=for-the-badge)
![Problem Statement](https://img.shields.io/badge/Problem_Statement-SIH25029-blue?style=for-the-badge)
![Organization](https://img.shields.io/badge/Organization-Govt_of_Jharkhand-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Project_Status-Production_Ready-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

**Authenticity Validator for Academia (AVFA)** is a tamper-proof, high-speed academic document verification platform engineered for **Smart India Hackathon (Problem Statement: SIH25029 - Government of Jharkhand)**. AVFA combines cryptographic SHA-256 canonical hashing, RSA-2048 asymmetric digital signatures, OpenCV/PyMuPDF document forensics, RapidFuzz fuzzy OCR comparison, and an immutable decentralized blockchain ledger explorer to eradicate degree fraud and enable single-click instant verification of academic credentials.

---

## 📑 Table of Contents

- [Problem Statement & Background](#-problem-statement--background)
- [Key Features](#-key-features)
- [System Architecture & Workflow](#-system-architecture--workflow)
- [Repository Directory Structure](#-repository-directory-structure)
- [Technology Stack](#-technology-stack)
- [Quickstart: Local Installation & Hosting](#-quickstart-local-installation--hosting)
- [API Contract & Endpoints](#-api-contract--endpoints)
- [Automated Verification & Test Suites](#-automated-verification--test-suites)
- [Team Members & Responsibilities](#-team-members--responsibilities)

---

## 🎯 Problem Statement & Background

Academic credential forgery poses severe threats to higher education standards, employment authenticity, and governmental trust. Conventional document verification relies on slow, paper-based transcripts, manual phone/email verifications, or easily forgeable seals. 

**AVFA** delivers an automated, cryptographically guaranteed digital verification infrastructure:
1. **Institutions** digitally sign and issue academic degrees with canonical payload hashing and tamper-evident QR codes.
2. **Employers, Verifiers, and Universities** validate certificates in milliseconds via Camera QR scan, Certificate ID lookup, or direct PDF drag-and-drop document upload with granular field-level mismatch forensics.
3. **Decentralized Ledger Explorer** simulates Merkle root chained blocks guaranteeing tamper resistance and non-repudiation without storing unencrypted student PII.

---

## 🌟 Key Features

- **🔐 Cryptographic SHA-256 & RSA-2048 Signatures:** Canonical JSON payload serialization ensures deterministic hashing resistant to spacing or ordering changes.
- **📄 Automated Certificate & QR PDF Generation:** Vector-grade PDF generation via ReportLab with embedded high-contrast QR codes pointing directly to instant verification endpoints.
- **📷 Dual-Mode Public Verifier (Page 9 & 10):**
  - **Tab A (Certificate Number / QR Scanner):** Scan physical certificate QR codes using device cameras (rear/front toggle) or upload QR image captures.
  - **Tab B (Drag-and-Drop Document Verification):** Upload user-submitted PDF files for text extraction, hash comparison, and side-by-side mismatch breakdown highlighting tampered fields (e.g., altered CGPA or Total Marks).
- **📊 Interactive Institutional Dashboard:** Real-time metrics for issued, active, revoked certificates, total verifications, and instant search filter.
- **⚡ Batch CSV Certificate Issuance:** Issue hundreds of academic certificates in batch with one API call or automated script.
- **⛓️ Simulated Blockchain Ledger:** Immutable block explorer displaying parent hashes, block hashes, timestamps, and cryptographic proof of consensus.
- **🚫 Real-Time Revocation Management:** Instantly invalidate compromised credentials with audit reason tracking and immediate public lookup flagging.
- **✉️ Automated OTP Email Service:** Supports both Resend API delivery and direct Gmail / standard SMTP with automatic fallback logging.

---

## 🏗️ System Architecture & Workflow

```
[ Educational Institution ]
         │
         ├── 1. Enters / Imports Student Degree Records
         ├── 2. Builds Canonical Payload (Name, Roll No, Degree, Marks, CGPA, Issue Date)
         ├── 3. Computes SHA-256 Hash + Signs with RSA Private Key (institution_private_key.pem)
         ├── 4. Renders Vector PDF & Embeds Verification QR (generated_certificates/)
         └── 5. Commits Cryptographic Hash into Immutable Ledger & Database
         
[ Verifier / Public User ]
         │
         ├── Option A: Live Camera QR Scan / Certificate ID Input
         │       └── Fast-path DB & RSA Public Key Signature Verification -> Valid / Revoked / Tampered
         │
         └── Option B: Upload PDF Document (Forensic Inspection)
                 ├── Extracts Text & Bounding Boxes via PyMuPDF / OCR
                 ├── Compares Field Similarity via RapidFuzz
                 └── Detects exact field tampering (e.g. Marks altered 485 -> 999)
```

---

## 📁 Repository Directory Structure

```text
authenticity-validator-academia/
├── src/                               # Backend FastAPI application
│   ├── main.py                        # FastAPI entry point, static routes, and CORS setup
│   ├── config.py                      # Environment configuration & secret keys
│   ├── database.py                    # SQLAlchemy session & PostgreSQL / SQLite resilient fallback
│   ├── models.py                      # Database models (Institutions, Users, Certificates, Logs)
│   ├── schemas.py                     # Pydantic validation schemas & API contracts
│   ├── security.py                    # Password hashing (bcrypt) & JWT token handlers
│   ├── certificate_crypto.py          # SHA-256 canonical hashing & RSA asymmetric signing
│   ├── email_service.py               # Resend API & SMTP OTP email transmission
│   ├── init_demo_data.py              # Automated database seeding & PDF generation
│   ├── log_service.py                 # Verification audit logging
│   └── routers/                       # Modular API router endpoints
│       ├── auth.py                    # User authentication (register, login, JWT)
│       ├── institutions.py            # Institution onboarding, OTP, and password setup
│       ├── certificate_issue.py       # Single & batch certificate issuance
│       ├── certificates.py            # Verification, search, download, stats & revocation
│       └── certificate_verify.py      # Verification alias router
├── frontend/                          # Client-side SPA assets
│   ├── index.html                     # 10-page single page interface
│   ├── css/style.css                  # Midnight Academy responsive stylesheet & design tokens
│   └── js/app.js                      # UI routing, camera QR scanner, API requests, toast alerts
├── static/                            # Synchronized static mount for FastAPI backend
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── PDF/                               # PDF Generation Subsystem
│   ├── certificate_generator.py       # ReportLab PDF generator with embedded QR codes
│   └── __init__.py
├── qr/                                # QR Code Subsystem
│   ├── qr_generator.py                # QR code image generator
│   ├── qr_extractor.py                # OpenCV / PyMuPDF QR decoder
│   └── sample_certificate_qr.png      # Test QR image
├── doc_processing/                    # Document Analysis & OCR Forensics
│   ├── main.py                        # Standalone document comparison pipeline
│   ├── pdf_processor.py               # PDF-to-image extraction
│   ├── image_preprocessing.py         # Grayscale, normalization & unsharp masking
│   ├── ocr.py                         # OCR text extraction engine with fallback
│   ├── field_extractor.py             # Regex & structural certificate field parser
│   └── document_comparison.py         # RapidFuzz field-by-field similarity scoring
├── hashing/                           # File hashing utilities
│   ├── hash_doc.py                    # Document SHA-256 calculator
│   └── certificate.pdf                # Reference test document
├── generated_certificates/            # Storage for issued certificate PDFs
├── docs/                              # Technical specifications & database schemas
│   ├── api_contract.md                # REST API specifications
│   ├── architecture_flow.md           # Mermaid sequence and flow diagrams
│   └── docs_db_schema.md              # Database entity relationships
├── .env.example                       # Template for environment variables
├── requirements.txt                   # Complete Python dependencies
├── generate_keys.py                   # Generates 2048-bit RSA institutional keypairs
├── create_zip.py                      # Packaging script for release distributions
├── test_workflow.py                   # Automated 10-page workflow validator
├── test_e2e.py                        # 12-point end-to-end API & cryptography test suite
├── test_verify_doc.py                 # Authentic vs tampered PDF upload test
├── test_qr_urls.py                    # Multi-format QR URL decoder test
├── test_email.py                      # OTP email delivery test script
└── README.md                          # Project documentation
```

---

## 💻 Technology Stack

| Domain | Technology |
|---|---|
| **Backend API** | FastAPI (Python 3.10+ / 3.14), Starlette, Uvicorn (ASGI) |
| **Database ORM** | PostgreSQL (Supabase pooler) with automatic SQLite fallback (`avfa.db`), SQLAlchemy 2.0 |
| **Cryptography** | `cryptography` (RSA PKCS#1 v2.1 PSS padding, SHA-256), `python-jose`, `passlib` (`bcrypt`) |
| **Document Processing & PDF** | ReportLab 5.0, PyMuPDF (fitz) 1.28, OpenCV (`cv2`), Pillow, RapidFuzz 3.14 |
| **QR Code Processing** | `qrcode 8.2`, OpenCV QR detector |
| **Frontend UI** | HTML5, Vanilla CSS (Design Tokens, Glassmorphism, Midnight theme), Vanilla JS, HTML5-QRCode |
| **Email Service** | Resend API / Python `smtplib` (SSL / STARTTLS) |

---

## 🚀 Quickstart: Local Installation & Hosting

### 1. Prerequisites
- Python 3.10+ or Python 3.14
- Git

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/your-org/authenticity-validator-academia.git
cd authenticity-validator-academia

# Create and activate virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Default settings automatically use SQLite and console OTP fallback if PostgreSQL or Resend keys are not configured).*

### 5. Generate Institutional Keys & Seed Demo Data
```bash
# Generate RSA keypair (institution_private_key.pem & institution_public_key.pem)
python generate_keys.py

# Initialize database schema and pre-generate demo certificate PDFs
python src/init_demo_data.py
```

### 6. Start Local Web Server
```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

### 7. Access Application in Browser
- 🌐 **Web Interface:** [http://localhost:8000](http://localhost:8000)
- 📚 **Interactive Swagger API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- 📖 **ReDoc Alternative API Reference:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Contract & Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the Single Page Application UI |
| `GET` | `/health` | Application health and platform status |
| `GET` | `/health/db` | Database connectivity verification |
| `POST` | `/auth/register` | Register a new user (`VERIFIER`, `ISSUER`, `ADMIN`) |
| `POST` | `/auth/login` | Authenticate user & retrieve JWT access token |
| `POST` | `/institutions/register` | Onboard an institution & dispatch verification OTP |
| `POST` | `/institutions/verify-otp` | Verify 6-digit OTP code |
| `POST` | `/institutions/set-password` | Set institution administrator password |
| `POST` | `/institutions/login` | Institution login & issue institutional JWT |
| `GET` | `/certificates/stats` | Dashboard statistics (issued, active, revoked, verifications) |
| `GET` | `/certificates/` | Search and filter registered academic certificates |
| `POST` | `/certificates/issue` | Issue certificate, compute SHA-256, sign RSA & generate PDF |
| `POST` | `/certificates/batch-issue` | Batch issue multiple student certificate records |
| `POST` | `/certificates/verify` | Verify certificate by Certificate Number, QR URL, or SHA-256 hash |
| `POST` | `/certificates/verify-document` | Upload PDF document for forensic field extraction & mismatch detection |
| `GET` | `/certificates/download/{cert_id}` | Download generated certificate PDF file |
| `GET` | `/certificates/blockchain-ledger` | Retrieve synchronized cryptographic block explorer |
| `PATCH` | `/certificates/{cert_id}/revoke` | Mark a compromised certificate as revoked with reason |
| `POST` | `/certificates/ocr-compare` | Perform RapidFuzz comparison between OCR fields and database |

---

## 🧪 Automated Verification & Test Suites

The repository contains automated test suites to ensure 100% test coverage across all layers:

```bash
# 1. Test full 10-page end-to-end user workflow:
python test_workflow.py

# 2. Run 12-point capability test (Auth, Issue, Verify, Ledger, Revoke, RapidFuzz):
python test_e2e.py

# 3. Test forensic document verification (authentic vs tampered PDF):
python test_verify_doc.py

# 4. Test multi-format QR code URL parsing:
python test_qr_urls.py
```

---

## 👥 Team Members & Responsibilities

* **Hriddhima** *(Team Lead)* — FastAPI Architecture, Cryptographic Hashing & Asymmetric Signing
* **Avika Srivastava** — PDF Vector Generation, ReportLab Engine & RapidFuzz Comparison
* **Anmol Sachan** — OpenCV Image Preprocessing & OCR Field Extraction Pipeline
* **Vansh Gupta** — Database Architecture (PostgreSQL & SQLite Fallback), Git Version Control & Deployment
* **Arpit Kesarvani** — System Design, Blockchain Ledger Mechanics & End-to-End Test Automation
* **Divyansh Dubey** — Frontend Development (Single Page Application, Midnight Theme & Camera Scanner)

---

## 📄 License

This project is licensed under the MIT License. Developed for Smart India Hackathon (SIH25029).
