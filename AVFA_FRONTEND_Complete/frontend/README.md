# 🎓 AVFA Frontend — User Interface & Verification Suite

**Authenticity Validator for Academia (AVFA)** — SIH25029 (Government of Jharkhand)

---

## 📁 Directory Structure

```tree
frontend/
├── index.html           # Main Single Page Application (All views & modals)
├── css/
│   └── style.css        # Responsive stylesheet with tokens, animations, certificate gold borders
├── js/
│   └── app.js           # Client state, API services, Web Crypto SHA-256, QR generation, pipeline animations
└── README.md            # Frontend documentation & quickstart
```

---

## 🌟 Key Features Included in the Frontend

1. **Main Landing Page & Hero**:
   - Header brand mark and navigation links.
   - Dynamic headline and **Live Verification Preview Card** displaying real-time certificate credentials, SHA-256 hash, and valid status badge.
   - 4-item Trust feature bar.
   - 5-step interactive process stepper pipeline.
   - Dual-column ecosystem cards for Universities vs. Employers.
   - Security checklist and zero-trust audit card.

2. **Public Verifier Suite**:
   - Multi-modal verification supporting drag-and-drop PDF/image files, raw SHA-256 hashes, or Certificate IDs.
   - 1-click testing buttons for **Valid**, **Revoked**, and **Tampered** credentials.
   - 4-point cryptographic audit matrix (SHA-256 hash match, RSA-2048 digital signature check, zero tampering, immutable ledger anchor).

3. **OCR Field Extractor & RapidFuzz Similarity Visualizer**:
   - Interactive tester demonstrating OpenCV image preprocessing + EasyOCR field extraction (`student_name`, `student_roll_no`, `degree_name`, `issue_date`, `institution`).
   - Dynamic animated similarity progress bars (0–100%) and instant `VERIFIED` vs. `FLAGGED` status.

4. **Simulated Blockchain Ledger Explorer**:
   - Real-time block stream cards (`Block #104,832`), Merkle root hashes, gas fee tracking, validator node info, and transaction ledger.

5. **Authentication Suite**:
   - "Welcome Back" account type selection (Student / Verifier vs. Institutional Issuer).
   - Student Login and Student Registration forms.
   - Institutional Issuer Login.

6. **Issuer Institutional Dashboard**:
   - Responsive sidebar navigation (Dashboard, Issue Certificate, Bulk CSV, Blockchain Ledger, OCR Checker).
   - 4 real-time metric cards (Issued, Active, Revoked, Verification Checks).
   - Recent certificates data table with real-time text search and status filter (`Active` vs. `Revoked`).
   - Instant credential **Revocation** with reason modal and database update.

7. **Issue Certificate Flow & 6-Step Animated Cryptographic Pipeline**:
   - Dual-column student data entry with automatic generation summary.
   - **6-step animated modal** simulating validation, SHA-256 hashing, RSA-2048 signing, QR generation, PDF assembly, and ledger enrollment.

8. **Authentic Academic Certificate Viewer**:
   - High-fidelity diploma with institution header seal, ornate borders, recipient name, degree program, CGPA, dean signatures, and embedded scannable QR code.
   - Printable PDF export (`window.print()`).

9. **Bulk CSV Batch Issuance**:
   - High-volume batch issuance modal for uploading and processing multiple graduate records at once with progress bar.

10. **Student Credential Wallet**:
    - Personal verifiable credential wallet for students to view, share, and verify their degrees.

---

## 🚀 How to Run the Frontend

### Method 1: Run with FastAPI Backend (Recommended)
From the repository root:
```bash
uvicorn src.main:app --reload --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)**

### Method 2: Standalone Static Server
You can open `frontend/index.html` with VS Code Live Server or python http server:
```bash
cd frontend
python -m http.server 3000
```
Open **[http://localhost:3000](http://localhost:3000)**

---

## 🔑 Demo Login Credentials

- **Issuer Account**: `issuer@git.edu` / `issuer123`
- **Student Account**: `student@git.edu` / `student123`
