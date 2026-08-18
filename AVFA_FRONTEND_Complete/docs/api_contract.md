# API Contract — v1

**Authenticity Validator for Academia (AVFA)** — SIH25029
Drafted against `docs_db_schema_v2.md`. Covers: `auth`, `issue`, `verify`, `get-certificate`.

Base URL: `/api/v1`
Auth: JWT bearer token (`Authorization: Bearer <token>`) on all protected routes.

---

## 1. Auth

### `POST /auth/register`
Creates a `users` row under an institution. **Not public** — institution must already exist (seeded/onboarded separately for the prototype).

**Request**
```json
{
  "institution_id": "uuid",
  "full_name": "string",
  "email": "string",
  "password": "string",
  "role": "ADMIN | ISSUER | VERIFIER"
}
```
**Response `201`**
```json
{
  "id": "uuid",
  "full_name": "string",
  "email": "string",
  "role": "ISSUER",
  "institution_id": "uuid"
}
```
**Errors**: `409` email already exists · `422` invalid role/missing field

---

### `POST /auth/login`
**Request**
```json
{ "email": "string", "password": "string" }
```
**Response `200`**
```json
{
  "access_token": "jwt-string",
  "token_type": "bearer",
  "user": { "id": "uuid", "full_name": "string", "role": "ISSUER", "institution_id": "uuid" }
}
```
**Errors**: `401` invalid credentials

---

## 2. Issue

### `POST /certificates/issue`
**Auth required**: role `ISSUER` or `ADMIN`.
Server-side flow: build canonical certificate payload → SHA-256 hash it → sign hash with institution's private key → store row → generate QR + PDF.

**Request**
```json
{
  "student_name": "string",
  "student_roll_no": "string",
  "degree_name": "string",
  "issue_date": "YYYY-MM-DD"
}
```
*(`institution_id` and `issued_by` are taken from the JWT, not the body.)*

**Response `201`**
```json
{
  "id": "uuid",
  "certificate_number": "string",
  "sha256_hash": "64-char hex",
  "signature": "base64/hex string",
  "qr_code_url": "string",
  "pdf_url": "string",
  "status": "ISSUED",
  "created_at": "timestamp"
}
```
**Errors**: `401` unauthenticated · `403` wrong role · `422` missing/invalid field

---

## 3. Verify

### `POST /certificates/verify`
**Public — no auth required.**
Accepts either an uploaded certificate file/image (for OCR + tamper check) or a direct hash (from QR scan). Every call writes a row to `verification_logs`.

**Request** — `multipart/form-data`
```
file: <certificate image/PDF>          # optional if hash provided
queried_hash: string                   # optional if file provided
```

**Response `200`**
```json
{
  "verification_status": "VALID | TAMPERED | REVOKED | NOT_FOUND",
  "certificate": {
    "certificate_number": "string",
    "student_name": "string",
    "degree_name": "string",
    "institution_name": "string",
    "issue_date": "YYYY-MM-DD"
  },
  "checks": {
    "hash_match": true,
    "signature_valid": true,
    "tamper_detected": false
  }
}
```
*(`certificate` is `null` if `NOT_FOUND`.)*

**Errors**: `422` neither file nor hash provided

---

## 4. Get Certificate

### `GET /certificates/{id}`
**Auth required**: role `ADMIN` or `ISSUER` within the owning institution.
Lookup by internal `id` (for dashboards — not the public verify flow).

**Response `200`**
```json
{
  "id": "uuid",
  "certificate_number": "string",
  "student_name": "string",
  "student_roll_no": "string",
  "degree_name": "string",
  "issue_date": "YYYY-MM-DD",
  "sha256_hash": "64-char hex",
  "qr_code_url": "string",
  "pdf_url": "string",
  "status": "ISSUED | REVOKED",
  "created_at": "timestamp"
}
```
**Errors**: `401` unauthenticated · `403` not owner institution · `404` not found

---

## 5. Revoke

### `PATCH /certificates/{id}/revoke`
**Auth required**: role `ADMIN` or `ISSUER` within the owning institution.
Flips status to `REVOKED`. The `verify` endpoint will then correctly return `REVOKED` for this certificate instead of `VALID`.

**Request**
```json
{ "revocation_reason": "string" }
```
**Response `200`**
```json
{
  "id": "uuid",
  "status": "REVOKED",
  "revocation_reason": "string",
  "revoked_at": "timestamp"
}
```
**Errors**: `401` unauthenticated · `403` not owner institution · `404` not found · `409` already revoked

---

## Notes for the team

- `signature` and `sha256_hash` are never accepted from the client on `issue` — always server-computed, to prevent forged submissions.
- `verify` is intentionally public/unauthenticated — that's the whole point of the product (anyone can verify without an account).
- `revoke` is a real endpoint, not faked in the DB — this lets the Day 8/9 demo show a genuine revoked-certificate path end-to-end.
- Batch upload endpoints (`batch_logs`) are **not in this contract** — out of scope for the prototype unless we decide we need the bulk-verification demo beat from the Impact slide
- `tamper_detected` is derived as `!hash_match` on file-upload verification (recomputed hash 
  vs. stored hash) — no image-forensics/CV tamper detection is being built for this round.
