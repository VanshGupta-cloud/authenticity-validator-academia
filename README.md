# 🎓 Authenticity Validator for Academia (AVFA)

![SIH Header](https://img.shields.io/badge/Smart_India_Hackathon-2025--2026-orange?style=for-the-badge)
![Problem Statement](https://img.shields.io/badge/Problem_Statement-SIH25029-blue?style=for-the-badge)
![Organization](https://img.shields.io/badge/Organization-Govt_of_Jharkhand-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Project_Status-Production_Ready-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

An automated, tamper-proof academic document verification system designed to eradicate degree fraud using cryptographic hashing and simulated decentralized consensus. Built for **Smart India Hackathon** under Problem Statement **SIH25029** (Government of Jharkhand).

---

## 📚 Repository Documentation

- [📖 User Manual & Operations Guide](docs/user_manual.md)
- [System Architecture & Workflow Flowchart](docs/architecture_flow.md)
- [Database Schema Documentation](docs/docs_db_schema.md)
- [API Contract Documentation](docs/api_contract.md)

---

## 🎯 Problem Statement Overview

Academic credential fraud poses a severe threat to educational standards and employment integrity. Manual verification processes are slow, inefficient, and vulnerable to forgery. **AVFA** provides a high-trust digital ecosystem where institutions issue cryptographically signed certificates, and verifiers (employers/universities) can validate their authenticity in seconds.

---

## 👥 Team Members & Responsibilities

* **Hriddhima** *(Team Lead)* — FastAPI Architecture, Cryptography, Hashing
* **Avika Srivastava** — PDF + QR Generation, RapidFuzz Comparison
* **Anmol Sachan** — OpenCV, OCR Processing Engine
* **Vansh Gupta** — Database (PostgreSQL & SQLite Fallback), Version Control (Git/GitHub), Deployment
* **Arpit Kesarvani** — System Design & Architecture, End-to-End Test Automation
* **Divyansh Dubey** — Frontend Development (HTML, CSS, JavaScript, Midnight Academy Theme, Camera Scanner)

---

## 🌟 Key Features

- **🔐 Cryptographic Certificate Hashing:** Generates deterministic SHA-256 digital signatures for academic certificates embedded into QR codes and signed with RSA-2048 institutional keys.
- **📄 Automated Certificate & QR PDF Generation:** Vector-grade PDF generation via ReportLab with embedded high-contrast QR codes pointing directly to instant verification endpoints.
- **📷 Dual-Mode Public Verifier (Pages 9 & 10):**
  - **Tab A (Certificate Number / QR Scanner):** Scan physical certificate QR codes using device cameras (rear/front toggle) or upload QR image captures.
  - **Tab B (Drag-and-Drop Document Verification):** Upload user-submitted PDF files for text extraction, hash comparison, and side-by-side mismatch breakdown highlighting tampered fields (e.g., altered CGPA or Total Marks).
- **📊 Interactive Institutional Dashboard:** Real-time metrics for issued, active, revoked certificates, total verifications, and instant search filter.
- **⚡ Bulk CSV Certificate Issuance:** Issue hundreds of academic certificates in batch with one API call or automated script.
- **⛓️ Simulated Blockchain Ledger:** Immutable block explorer displaying parent hashes, block hashes, timestamps, and cryptographic proof of consensus.
- **🚫 Revocation Management:** Allows authorized institutions to mark compromised credentials as revoked in real time with reason tracking and immediate public lookup flagging.
- **✉️ Multi-Tier OTP Email Service:** Supports direct Gmail SMTP, Resend API with notification inbox forwarding, and terminal console fallback.

---

## 🏗️ System Architecture & Workflow

```text
[ Educational Institution / Issuer ]
         │
         ├── 1. Enters / Imports Student Degree Records
         ├── 2. Builds Canonical Payload (Name, Roll No, Degree, Marks, CGPA, Issue Date)
         ├── 3. Computes SHA-256 Hash + Signs with RSA Private Key (institution_private_key.pem)
         ├── 4. Renders Vector PDF & Embeds Verification QR (generated_certificates/)
         └── 5. Commits Cryptographic Hash into Immutable Ledger & Database
         
[ Verifier / Public User / Employer ]
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
│   ├── email_service.py               # 3-tier OTP email transmission (SMTP / Resend / Console)
│   ├── init_demo_data.py              # Startup database table initialization
│   ├── log_service.py                 # Verification audit logging
│   └── routers/                       # Modular API router endpoints
│       ├── auth.py                    # User authentication (register, login, JWT)
│       ├── institutions.py            # Institution onboarding, OTP, and password setup
│       ├── certificate_issue.py       # Single & batch certificate issuance
│       ├── certificates.py            # Verification, search, download, stats & revocation
│       └── certificate_verify.py      # Verification alias router
├── frontend/                          # Client-side Single Page Application
│   ├── index.html                     # 10-page single page interface
│   ├── css/style.css                  # Midnight Academy responsive stylesheet & design tokens
│   ├── js/app.js                      # UI routing, camera QR scanner, API requests, toast alerts
│   └── README.md
├── static/                            # Synchronized static mount for FastAPI backend
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── PDF/                               # PDF Generation Subsystem
│   ├── __init__.py
│   └── certificate_generator.py       # ReportLab PDF generator with embedded QR codes
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
│   ├── document_comparison.py         # RapidFuzz field-by-field similarity scoring
│   └── requirements.txt
├── hashing/                           # File hashing utilities
│   ├── hash_doc.py                    # Document SHA-256 calculator
│   ├── certificate.pdf                # Reference test document
│   └── modified.pdf
├── docs/                              # Technical specifications & database schemas
│   ├── user_manual.md                 # Complete 10-page User Operations Manual
│   ├── api_contract.md                # REST API specifications
│   ├── architecture_flow.md           # Mermaid sequence and flow diagrams
│   └── docs_db_schema.md              # Database entity relationships
├── tests/                             # Automated Test Suites & Validation
│   ├── __init__.py
│   ├── test_workflow.py               # Full 10-page end-to-end user workflow test
│   ├── test_e2e.py                    # 12-point capability & cryptography test suite
│   ├── test_verify_doc.py             # Forensic PDF document upload & tampering test
│   ├── test_qr_urls.py                # Multi-format QR code URL decoder test
│   ├── test_email.py                  # OTP email dispatch verification test
│   ├── test_user_file.py              # User document verification test
│   └── capture_all_pages.py           # Automated UI screenshot capture script
├── screenshots/                       # 12 UI Flow Screenshots
├── smart-contracts/                   # Smart contract placeholder
├── AVFA_FRONTEND_Complete/            # Fully synchronized standalone directory
├── .env.example                       # Template for environment variables
├── .gitignore                         # Git ignore rules
├── requirements.txt                   # Complete Python dependencies
├── generate_keys.py                   # Generates 2048-bit RSA institutional keypairs
├── create_zip.py                      # Packaging script for release distributions
├── database.py                        # Root database exporter
├── LICENSE                            # MIT License
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
| **Email Service** | Direct Gmail SMTP (TLS/SSL) / Resend API / Terminal Console Fallback |

---

## 🚀 Quickstart: Local Installation & Hosting

### 1. Prerequisites
- Python 3.10+ or Python 3.14
- Git

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/VanshGupta-cloud/authenticity-validator-academia.git
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

### 5. Generate Institutional Keys & Initialize Database
```bash
# Generate RSA keypair (institution_private_key.pem & institution_public_key.pem)
python generate_keys.py

# Initialize database schema
python src/init_demo_data.py
```

### 6. Start Local Web Server
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access Application in Browser
- 🌐 **Web Interface:** [http://localhost:8000](http://localhost:8000)
- 📚 **Interactive Swagger API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- 📖 **ReDoc Alternative API Reference:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Contract & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Serves the Single Page Application UI | None |
| `GET` | `/health` | Application health and platform status | None |
| `GET` | `/health/db` | Database connectivity verification | None |
| `POST` | `/auth/register` | Register a new user (`VERIFIER`, `ISSUER`, `ADMIN`) | None |
| `POST` | `/auth/login` | Authenticate user & retrieve JWT access token | None |
| `POST` | `/institutions/register` | Onboard an institution & dispatch verification OTP | None |
| `POST` | `/institutions/verify-otp` | Verify 6-digit OTP code | None |
| `POST` | `/institutions/set-password` | Set institution administrator password | None |
| `POST` | `/institutions/login` | Institution login & issue institutional JWT | None |
| `GET` | `/certificates/stats` | Dashboard statistics (issued, active, revoked, verifications) | Optional |
| `GET` | `/certificates/` | Search and filter registered academic certificates | Optional |
| `POST` | `/certificates/issue` | Issue certificate, compute SHA-256, sign RSA & generate PDF | Bearer JWT |
| `POST` | `/certificates/batch-issue` | Batch issue multiple student certificate records | Bearer JWT |
| `POST` | `/certificates/verify` | Verify certificate by Certificate Number, QR URL, or SHA-256 hash | None |
| `POST` | `/certificates/verify-document` | Upload PDF document for forensic field extraction & mismatch detection | None |
| `GET` | `/certificates/download/{cert_id}` | Download generated certificate PDF file | None |
| `GET` | `/certificates/blockchain-ledger` | Retrieve synchronized cryptographic block explorer | None |
| `PATCH` | `/certificates/{cert_id}/revoke` | Mark a compromised certificate as revoked with reason | Bearer JWT |
| `POST` | `/certificates/ocr-compare` | Perform RapidFuzz comparison between OCR fields and database | Optional |

---

## 🧪 Automated Verification & Test Suites

The repository contains automated test suites to ensure 100% test coverage across all layers:

```bash
# 1. Test full 10-page end-to-end user workflow:
python tests/test_workflow.py

# 2. Run 12-point capability test (Auth, Issue, Verify, Ledger, Revoke, RapidFuzz):
python tests/test_e2e.py

# 3. Test forensic document verification (authentic vs tampered PDF):
python tests/test_verify_doc.py

# 4. Test multi-format QR code URL parsing:
python tests/test_qr_urls.py

# 5. Test OTP email dispatch pipeline:
python tests/test_email.py
```

---

## 📄 License

This project is licensed under the MIT License. Developed for Smart India Hackathon (SIH25029).
