# Database Schema (DB Schema)

This document defines the relational database schema for the **Authenticity Validator for Academia (AVFA)** platform (SIH25029).

---

## Entity Relationship Overview

- **institutions**: Stores registered academic bodies authorized to issue credentials.
- **users**: Stores administrative accounts, issuers, and system operators linked to institutions.
- **batch_logs**: Records bulk processing jobs when institutions upload batches of certificates.
- **certificates**: Core ledger table storing student metadata, SHA-256 hashes, QR URLs, and blockchain transaction references.
- **verification_logs**: Audit trail tracking public verification attempts, query hashes, and status results.

---

## Table Structures

### 1. `institutions`
```text
id            UUID / INTEGER    PRIMARY KEY
name          VARCHAR           NOT NULL
code          VARCHAR           UNIQUE
email         VARCHAR           UNIQUE
public_key    TEXT
is_verified   BOOLEAN
created_at    TIMESTAMP
```

---

### 2. `users`
```text
id              UUID / INTEGER    PRIMARY KEY
institution_id  UUID / INTEGER    FOREIGN KEY -> institutions(id)
full_name       VARCHAR           NOT NULL
email           VARCHAR           UNIQUE
password_hash   VARCHAR           NOT NULL
role            VARCHAR           CHECK ('ADMIN', 'ISSUER', 'VERIFIER')
created_at      TIMESTAMP
```

---

### 3. `certificates`
```text
id                  UUID / INTEGER    PRIMARY KEY
certificate_number  VARCHAR           UNIQUE NOT NULL
institution_id      UUID / INTEGER    FOREIGN KEY -> institutions(id)
issued_by           UUID / INTEGER    FOREIGN KEY -> users(id)
batch_id            UUID / INTEGER    FOREIGN KEY -> batch_logs(id)
student_name        VARCHAR           NOT NULL
student_roll_no     VARCHAR           NOT NULL
degree_name         VARCHAR           NOT NULL
issue_date          DATE              NOT NULL
sha256_hash         VARCHAR(64)       UNIQUE NOT NULL
qr_code_url         TEXT
pdf_url             TEXT
blockchain_tx_hash  VARCHAR(66)
block_number        BIGINT
status              VARCHAR           CHECK ('ISSUED', 'REVOKED')
revocation_reason   TEXT
revoked_at          TIMESTAMP
created_at          TIMESTAMP
```

---

### 4. `batch_logs`
```text
id                  UUID / INTEGER    PRIMARY KEY
institution_id      UUID / INTEGER    FOREIGN KEY -> institutions(id)
uploaded_by         UUID / INTEGER    FOREIGN KEY -> users(id)
total_records       INTEGER           NOT NULL
successful_records  INTEGER
failed_records      INTEGER
status              VARCHAR           CHECK ('PROCESSING', 'COMPLETED', 'FAILED')
created_at          TIMESTAMP
```

---

### 5. `verification_logs`
```text
id                   UUID / INTEGER    PRIMARY KEY
certificate_id       UUID / INTEGER    FOREIGN KEY -> certificates(id)
queried_hash         VARCHAR(64)       NOT NULL
verification_status  VARCHAR           CHECK ('VALID', 'TAMPERED', 'REVOKED', 'NOT_FOUND')
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
    is_verified BOOLEAN DEFAULT TRUE,
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
    qr_code_url TEXT,
    pdf_url TEXT,
    blockchain_tx_hash VARCHAR(66),
    block_number BIGINT,
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
