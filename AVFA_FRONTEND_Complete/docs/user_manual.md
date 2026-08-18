# 📖 Authenticity Validator for Academia (AVFA) — User Manual & Operations Guide

![SIH Header](https://img.shields.io/badge/Smart_India_Hackathon-SIH25029-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Guide_Version-1.0_Final-brightgreen?style=for-the-badge)
![Platform](https://img.shields.io/badge/Host-localhost%3A8000-orange?style=for-the-badge)

Welcome to the **AVFA (Authenticity Validator for Academia)** User Manual. This guide provides comprehensive, step-by-step instructions for all platform roles: **Institutional Authorities (Deans, Registrars, Exam Controllers)**, **Students/Graduates**, and **Public Verifiers (Employers, Background Check Agencies, Universities)**.

---

## 📑 Table of Contents

1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Quick Access & Pre-Seeded Accounts](#2-quick-access--pre-seeded-accounts)
3. [User Persona Workflows](#3-user-persona-workflows)
   - [Workflow A: Institution Registration & Setup (Pages 3, 4, 5, 2)](#workflow-a-institution-registration--setup)
   - [Workflow B: Dashboard & Certificate Issuance (Pages 6, 7, 8)](#workflow-b-dashboard--certificate-issuance)
   - [Workflow C: Bulk CSV Certificate Issuance](#workflow-c-bulk-csv-certificate-issuance)
   - [Workflow D: Public Verification via ID & Camera QR (Tab A)](#workflow-d-public-verification-via-id--camera-qr-tab-a)
   - [Workflow E: Public Forensic PDF Document Upload (Tab B)](#workflow-e-public-forensic-pdf-document-upload-tab-b)
   - [Workflow F: Revoking a Compromised Certificate](#workflow-f-revoking-a-compromised-certificate)
   - [Workflow G: Blockchain Ledger Explorer](#workflow-g-blockchain-ledger-explorer)
4. [Verification Status Indicators & Forensic Breakdown](#4-verification-status-indicators--forensic-breakdown)
5. [Troubleshooting & Frequently Asked Questions (FAQ)](#5-troubleshooting--frequently-asked-questions-faq)
6. [API Quick Reference](#6-api-quick-reference)

---

## 1. System Overview & Architecture

AVFA is a tamper-proof academic degree validation ecosystem engineered under **Smart India Hackathon (SIH25029 - Government of Jharkhand)**. 

### How AVFA Protects Documents:
1. **Deterministic Canonical Hashing:** Standardizes student data (Name, Roll No, Degree, Marks, CGPA, Issue Date) into a canonical JSON string and computes its unique **SHA-256 cryptographic hash**.
2. **Asymmetric Digital Signing:** Signs the SHA-256 hash using the issuing institution's private RSA-2048 key (`institution_private_key.pem`).
3. **Vector PDF & QR Generation:** Renders a high-resolution PDF certificate embedding a high-contrast QR code pointing directly to the verification endpoint.
4. **Immutable Blockchain Ledger:** Chained block records track every issuance and status change without exposing unencrypted student PII.
5. **Forensic Document Verification:** PyMuPDF and RapidFuzz compare uploaded PDF documents against trusted records and pinpoint exact tampered fields.

---

## 2. Quick Access & Pre-Seeded Accounts

| Interface | URL | Description |
|---|---|---|
| **Web Application UI** | [http://localhost:8000](http://localhost:8000) | 10-page single page web interface |
| **Interactive API Documentation** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI for testing API endpoints |
| **Alternative API Reference** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | ReDoc schema viewer |

### Pre-Seeded Testing Accounts
If you want to skip registration and test immediately:

* **Institution Official (Global Institute of Technology):**
  * Email: `admin@git.edu` (or `issuer@git.edu`)
  * Password: `admin123` (or `issuer123`)
* **Student / Public Verifier:**
  * Email: `student@git.edu`
  * Password: `student123`

---

## 3. User Persona Workflows

---

### Workflow A: Institution Registration & Setup
*(For new universities and colleges onboarding onto the network)*

```
[ Page 1: Landing ] ➔ [ Page 3: Register ] ➔ [ Page 4: OTP ] ➔ [ Page 5: Password ] ➔ [ Page 2: Login ]
```

1. Open **[http://localhost:8000](http://localhost:8000)** in your web browser.
2. Click **Institution Portal** in the navigation bar ➔ Click **Register Institution** (or navigate to Page 3).
3. Fill in your institution details:
   - **Institution Name:** e.g., `National University of Technology`
   - **Official Email:** e.g., `dean.academics@nationaltech.edu` *(You can use any real or dummy email)*
   - **Address:** e.g., `Ranchi, Jharkhand`
4. Click **"Register & Send Verification Code"**.
5. **Enter the 6-Digit OTP (Page 4):**
   - The OTP code is dispatched via email (if configured) and **instantly printed in your backend terminal console**:
     ```text
     =======================================================
      [INSTITUTION REGISTRATION]
      Institution: National University of Technology
      Target Email: dean.academics@nationaltech.edu
      REAL OTP CODE: >>> 724254 <<<
     =======================================================
     ```
   - Type the 6 digits into the OTP boxes on the screen and click **"Verify OTP Code"**.
6. **Set Institutional Password (Page 5):**
   - Enter your desired password (e.g., `Password@123`) in both fields and click **"Set Password & Complete Setup"**.
7. **Log In (Page 2):**
   - Enter your registered official email and password to log in.

---

### Workflow B: Dashboard & Certificate Issuance
*(For authorized institutional officials issuing student degrees)*

```
[ Page 6: Dashboard ] ➔ [ Page 7: Issue Form ] ➔ [ Page 8: Confirmation & Download ]
```

1. Once logged in, you will arrive at the **Institution Dashboard (Page 6)**:
   - View real-time metrics: **Total Issued**, **Active**, **Revoked**, and **Total Verification Checks**.
   - Use the **Search Bar** to instantly filter certificates by student name, roll number, or degree.
2. Click the **"+ Issue New Certificate"** button in the dashboard header (navigates to Page 7).
3. Complete the academic certificate form:
   - **Student Full Name:** e.g., `Aarav Sharma`
   - **Student Roll Number:** e.g., `CS-2026-901`
   - **Degree / Course Name:** e.g., `Bachelor of Technology in Computer Science`
   - **Issue Date:** e.g., `2026-05-20`
   - **Total Marks:** e.g., `490`
   - **CGPA / GPA:** e.g., `9.85`
4. Click **"Sign & Issue Certificate"**:
   - The platform generates a canonical SHA-256 payload.
   - Signs the hash with the institutional RSA-2048 private key.
   - Renders a formal vector PDF with embedded QR code.
   - Commits the record to the immutable database and blockchain ledger.
5. **Confirmation & Instant Download (Page 8):**
   - You will see the **Certificate Number** (e.g., `CERT-2026-XXXX`), **SHA-256 Hash**, and an interactive preview.
   - Click **"Download PDF Certificate"** to save the authentic PDF to your computer.

---

### Workflow C: Bulk CSV Certificate Issuance
*(For high-volume graduation cohorts)*

Institutions can issue hundreds of certificates in seconds using the batch endpoint:

1. Send a `POST` request to `/certificates/batch-issue` with an array of student records:
   ```json
   [
     {
       "student_name": "Rohan Deshmukh",
       "student_roll_no": "CS-2026-101",
       "course_name": "B.Tech in Artificial Intelligence",
       "issue_date": "2026-08-16",
       "marks": "488",
       "cgpa": "9.76"
     },
     {
       "student_name": "Pooja Hegde",
       "student_roll_no": "CS-2026-102",
       "course_name": "B.Tech in Computer Science",
       "issue_date": "2026-08-16",
       "marks": "495",
       "cgpa": "9.90"
     }
   ]
   ```
2. The response returns generated certificate numbers and download paths for the entire batch.

---

### Workflow D: Public Verification via ID & Camera QR (Tab A)
*(For employers, background check agents, and students validating credentials)*

```
[ Page 1: Landing ] ➔ [ Click "Public Verifier" (Page 9 Tab A) ] ➔ [ Result (Page 10) ]
```

1. Navigate to **Public Verifier** in the top navigation bar.
2. Select **Tab A: "Verify by Certificate Number / QR Code"**.
3. **Choose your verification method:**
   - **Method 1 (Manual Entry):** Type or paste the Certificate Number (e.g., `CERT-2026-B97DA3E5` or `AVFA-GIT-2024-001`) into the search box and click **"Verify Authenticity"**.
   - **Method 2 (Live Device Camera):** Click **"Start Camera Scanner"** to open your device webcam / phone camera. Align the QR code within the target box. You can toggle between front and rear cameras using **"Switch Camera"**.
   - **Method 3 (Upload QR Image):** Drag and drop or browse for a captured QR code image (`sample_certificate_qr.png`).
4. **Verification Result (Page 10):**
   - Displays a prominent **🟢 VERIFIED AUTHENTIC** badge.
   - Shows verified student details, issuing institution, degree title, issue date, marks, and CGPA.
   - Shows the verified cryptographic SHA-256 hash and RSA digital signature.

---

### Workflow E: Public Forensic PDF Document Upload (Tab B)
*(Detecting tampered or edited degree certificates)*

```
[ Page 9: Public Verifier ] ➔ [ Select Tab B: Document Upload ] ➔ [ Drag PDF ] ➔ [ Result Page 10 ]
```

1. On the **Public Verifier** page, select **Tab B: "Verify by Document Upload"**.
2. Drag and drop any certificate PDF file into the designated upload area (or click to browse).
3. Click **"Run Forensic Verification"**.
4. **Result Scenarios:**
   - **Scenario 1 (Original / Authentic PDF):**
     - Shows **🟢 DOCUMENT VERIFIED & AUTHENTIC**.
     - All extracted fields match the institutional database records with 0 mismatches.
   - **Scenario 2 (Tampered / Altered PDF):**
     - Shows **🔴 DOCUMENT FLAGGED — TAMPERING DETECTED**.
     - **Granular Mismatch Table:** Compares extracted PDF values side-by-side against the official institutional record:
       ```text
       Field: Total Marks | Uploaded PDF: 1025 | Institutional Registry: 1000.00 (TAMPERED)
       Field: CGPA        | Uploaded PDF: 5.00 | Institutional Registry: 4.00    (TAMPERED)
       ```

---

### Workflow F: Revoking a Compromised Certificate
*(For institutional authorities revoking fraudulent or error-issued certificates)*

1. Log in to the **Institution Dashboard (Page 6)**.
2. Locate the certificate in the registry table.
3. Click the **"Revoke"** action button next to the certificate.
4. Enter the official audit revocation reason:
   - *e.g., "Administrative credential audit failed - incomplete prerequisite credits"*.
5. Click **"Confirm Revocation"**.
6. **Immediate Effect:**
   - The status in the dashboard instantly changes to **🔴 REVOKED**.
   - Any public scan or lookup on that certificate immediately displays:
     `🔴 STATUS: REVOKED | Reason: Administrative credential audit failed`.

---

### Workflow G: Blockchain Ledger Explorer
*(For auditors and verifiers inspecting cryptographic consensus)*

1. Navigate to `/certificates/blockchain-ledger` or use the dashboard ledger link.
2. View chained cryptographic blocks:
   - **Block Index** & Timestamp
   - **Merkle Root (Certificate Hash)**
   - **Previous Block Hash**
   - **Current Block Hash** (SHA-256 chained consensus)
3. Confirms that all certificate records are permanently anchored in an immutable ledger.

---

## 4. Verification Status Indicators & Forensic Breakdown

| Status Badge | Meaning | System Action |
|---|---|---|
| **🟢 VALID / ISSUED** | Certificate exists, cryptographic signature matches institutional public key, and all fields are intact. | Full verification details displayed with green authenticity seal. |
| **🔴 TAMPERED** | Document fields (such as CGPA, Marks, or Name) do not match the institutional database or signature is invalid. | Granular mismatch comparison table displayed highlighting exact tampered lines. |
| **🟠 REVOKED** | Certificate was officially issued in the past but has been formally invalidated by the university. | Displays red revoked banner with official revocation reason and audit timestamp. |
| **⚪ NOT_FOUND** | Certificate number or cryptographic hash does not exist in any registered university database. | Displays unregistered credential warning. |

---

## 5. Troubleshooting & Frequently Asked Questions (FAQ)

### Q1: I am using a made-up email for testing. Where do I find the OTP?
**Answer:** The OTP is automatically printed in your terminal running uvicorn (`REAL OTP CODE: >>> 123456 <<<`) and in your browser's Developer Console (`F12` ➔ Console tab).

### Q2: How do I restart the server if I close the terminal?
**Answer:** Open PowerShell in the project directory and run:
```powershell
cd C:\projectuthenticity-validator-academia
.env\Scripts\Activate.ps1
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

### Q3: Where are issued certificate PDFs stored?
**Answer:** All issued PDFs are saved in `C:\projectuthenticity-validator-academia\generated_certificates\` and can also be downloaded directly via the API at `http://localhost:8000/certificates/download/{cert_number}`.

### Q4: Can I test document tampering myself?
**Answer:** Yes!
1. Issue a certificate (e.g. 485 Marks, 9.7 CGPA) and download the PDF.
2. Run `python test_verify_doc.py` to see how AVFA automatically detects altered marks (1025) and altered CGPA (5.00) and displays the mismatch breakdown.

---

## 6. API Quick Reference

| Endpoint | Method | Purpose | Auth Required |
|---|---|---|---|
| `/` | `GET` | Serves the 10-page SPA UI | None |
| `/health` | `GET` | API Health & status | None |
| `/institutions/register` | `POST` | Onboard institution & dispatch OTP | None |
| `/institutions/verify-otp` | `POST` | Verify 6-digit OTP | None |
| `/institutions/set-password` | `POST` | Set password | None |
| `/institutions/login` | `POST` | Institution login & issue JWT | None |
| `/certificates/stats` | `GET` | Dashboard statistics | Optional |
| `/certificates/` | `GET` | Search and filter certificates | Optional |
| `/certificates/issue` | `POST` | Issue degree certificate with PDF & QR | Bearer JWT |
| `/certificates/batch-issue` | `POST` | Bulk issue certificate records | Bearer JWT |
| `/certificates/verify` | `POST` | Verify certificate by ID/QR | None |
| `/certificates/verify-document` | `POST` | Upload PDF for forensic text check | None |
| `/certificates/download/{cert_id}` | `GET` | Download certificate PDF file | None |
| `/certificates/blockchain-ledger` | `GET` | View cryptographic ledger explorer | None |
| `/certificates/{cert_id}/revoke` | `PATCH` | Revoke a certificate with audit reason | Bearer JWT |

---

*Authenticity Validator for Academia (AVFA) — Tamper-Proof Document Verification Platform*
