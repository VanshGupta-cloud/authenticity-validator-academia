# Database Schema (FINAL — v2)

**Authenticity Validator for Academia (AVFA)** — SIH25029
Locked Day 1 (Aug 8) — resolves the 3 open flags from the v1 draft.

---

## Changes from v1

| # | Flag | Resolution |
|---|------|------------|
| 1 | `blockchain_tx_hash`, `block_number` on `certificates` | **Removed.** Leftover from the dropped blockchain/IPFS approach — Day 6 decision was hash + signature + Postgres only. |
| 2 | No column stored the actual digital signature | **Added `signature TEXT NOT NULL`** on `certificates`. We hash the certificate, then sign that hash with the institution's private key (Day 5 task) — the schema had nowhere to persist the result. |
| 3 | `institutions.is_verified` defaulted `TRUE` | **Changed default to `FALSE`.** An authenticity platform should not auto-trust every new institution on signup; verification should be a deliberate step. |

Everything else (`users`, `batch_logs`, `verification_logs`) is unchanged from v1.

---

## Entity Relationship Overview

- **institutions** — registered academic bodies authorized to issue credentials.
- **users** — admin/issuer/verifier accounts linked to an institution.
- **certificates** — core table: student metadata, hash, signature, QR/PDF URLs.
- **batch_logs** — bulk-upload job tracking.
- **verification_logs** — audit trail of every verification attempt.

---

## Table Structures

### 1. `institutions`
```text
id            UUID              PRIMARY KEY
name          VARCHAR           NOT NULL
code          VARCHAR           UNIQUE NOT NULL
email         VARCHAR           UNIQUE NOT NULL
public_key    TEXT                              -- used to verify certificate signatures
is_verified   BOOLEAN           DEFAULT FALSE    -- CHANGED from TRUE
created_at    TIMESTAMP
```

### 2. `users`
```text
id              UUID              PRIMARY KEY
institution_id  UUID              FOREIGN KEY -> institutions(id)
full_name       VARCHAR           NOT NULL
email           VARCHAR           UNIQUE NOT NULL
password_hash   VARCHAR           NOT NULL
role            VARCHAR           CHECK ('ADMIN', 'ISSUER', 'VERIFIER') DEFAULT 'ISSUER'
created_at      TIMESTAMP
```

### 3. `certificates`
```text
id                  UUID              PRIMARY KEY
certificate_number  VARCHAR           UNIQUE NOT NULL
institution_id      UUID              FOREIGN KEY -> institutions(id)
issued_by           UUID              FOREIGN KEY -> users(id)
batch_id            UUID              FOREIGN KEY -> batch_logs(id)
student_name        VARCHAR           NOT NULL
student_roll_no     VARCHAR           NOT NULL
degree_name         VARCHAR           NOT NULL
issue_date          DATE              NOT NULL
sha256_hash         VARCHAR(64)       UNIQUE NOT NULL
signature           TEXT              NOT NULL   -- NEW: institution's signature over sha256_hash
qr_code_url         TEXT
pdf_url             TEXT
status              VARCHAR           CHECK ('ISSUED', 'REVOKED') DEFAULT 'ISSUED'
revocation_reason   TEXT
revoked_at          TIMESTAMP
created_at          TIMESTAMP
```
*(`blockchain_tx_hash` and `block_number` removed — no longer applicable.)*

### 4. `batch_logs`
```text
id                  UUID              PRIMARY KEY
institution_id      UUID              FOREIGN KEY -> institutions(id)
uploaded_by         UUID              FOREIGN KEY -> users(id)
total_records       INTEGER           NOT NULL
successful_records  INTEGER           DEFAULT 0
failed_records      INTEGER           DEFAULT 0
status              VARCHAR           CHECK ('PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PROCESSING'
created_at          TIMESTAMP
```

### 5. `verification_logs`
```text
id                   UUID              PRIMARY KEY
certificate_id       UUID              FOREIGN KEY -> certificates(id)
queried_hash         VARCHAR(64)       NOT NULL
verification_status  VARCHAR           CHECK ('VALID', 'TAMPERED', 'REVOKED', 'NOT_FOUND') NOT NULL
verified_by_ip       VARCHAR(45)
user_agent           TEXT
created_at           TIMESTAMP
```

---

## SQL DDL Script

```sql
-- Institutions Table
CREATE TABLE institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    public_key TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE SET NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('ADMIN', 'ISSUER', 'VERIFIER')) DEFAULT 'ISSUER',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Batch Logs Table
CREATE TABLE batch_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES users(id),
    total_records INT NOT NULL,
    successful_records INT DEFAULT 0,
    failed_records INT DEFAULT 0,
    status VARCHAR(20) CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED')) DEFAULT 'PROCESSING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Certificates Table
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_number VARCHAR(100) UNIQUE NOT NULL,
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    issued_by UUID REFERENCES users(id),
    batch_id UUID REFERENCES batch_logs(id) ON DELETE SET NULL,
    student_name VARCHAR(150) NOT NULL,
    student_roll_no VARCHAR(50) NOT NULL,
    degree_name VARCHAR(150) NOT NULL,
    issue_date DATE NOT NULL,
    sha256_hash VARCHAR(64) UNIQUE NOT NULL,
    signature TEXT NOT NULL,
    qr_code_url TEXT,
    pdf_url TEXT,
    status VARCHAR(20) CHECK (status IN ('ISSUED', 'REVOKED')) DEFAULT 'ISSUED',
    revocation_reason TEXT,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Verification Logs Table
CREATE TABLE verification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id UUID REFERENCES certificates(id) ON DELETE SET NULL,
    queried_hash VARCHAR(64) NOT NULL,
    verification_status VARCHAR(20) CHECK (verification_status IN ('VALID', 'TAMPERED', 'REVOKED', 'NOT_FOUND')) NOT NULL,
    verified_by_ip VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Verification
CREATE INDEX idx_certificates_hash ON certificates(sha256_hash);
CREATE INDEX idx_certificates_cert_num ON certificates(certificate_number);
CREATE INDEX idx_certificates_institution ON certificates(institution_id);
CREATE INDEX idx_verification_logs_cert ON verification_logs(certificate_id);
```
