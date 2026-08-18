from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


# ============================================================
# Auth & User Schemas
# ============================================================

class RegisterRequest(BaseModel):
    institution_id: Optional[str] = None
    full_name: str
    email: EmailStr
    password: str
    role: str = "STUDENT"  # ADMIN, ISSUER, VERIFIER, STUDENT


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    institution_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class InstitutionRegisterRequest(BaseModel):
    name: str
    code: Optional[str] = "GIT"
    email: EmailStr
    password: Optional[str] = "admin123"


class InstitutionLoginRequest(BaseModel):
    email: EmailStr
    password: str


class InstitutionLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    institution_id: str
    name: str
    email: str


# ============================================================
# Certificate Issuance Schemas
# ============================================================

class CertificateIssueRequest(BaseModel):
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: str
    marks: Optional[str] = None
    cgpa: Optional[str] = None


class CertificateIssueResponse(BaseModel):
    id: str
    certificate_number: str
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: str
    marks: Optional[str] = None
    cgpa: Optional[str] = None
    sha256_hash: str
    digital_signature: str
    status: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Certificate Verification Schemas
# ============================================================

class CertificateVerifyRequest(BaseModel):
    certificate_id: Optional[UUID] = None
    certificate_number: Optional[str] = None


class FieldMismatch(BaseModel):
    field: str
    document_value: Optional[str] = None
    record_value: Optional[str] = None


class CertificateVerifyResponse(BaseModel):
    hash_signature_valid: bool
    tamper_detected: bool
    certificate_number: Optional[str] = None
    student_name: Optional[str] = None
    student_roll_no: Optional[str] = None
    course_name: Optional[str] = None
    issue_date: Optional[date] = None
    marks: Optional[Decimal] = None
    cgpa: Optional[Decimal] = None
    status: Optional[str] = None
    message: str


# ============================================================
# Certificate Schemas (CRUD)
# ============================================================

class CertificateBase(BaseModel):
    certificate_number: str
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: str
    marks: Optional[str] = None
    cgpa: Optional[str] = None
    sha256_hash: str
    digital_signature: str


class CertificateCreate(CertificateBase):
    institution_id: Optional[str] = None
    issuer_id: Optional[str] = None
    batch_id: Optional[str] = None


class CertificateUpdate(BaseModel):
    status: Optional[str] = None
    revocation_reason: Optional[str] = None


class CertificateResponse(CertificateBase):
    id: str
    institution_id: Optional[str] = None
    issuer_id: Optional[str] = None
    batch_id: Optional[str] = None
    status: str
    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Verification & Revocation
# ============================================================

class VerifyRequest(BaseModel):
    queried_hash: Optional[str] = None
    certificate_number: Optional[str] = None


class CertificateDetail(BaseModel):
    certificate_number: str
    student_name: str
    student_roll_no: str
    degree_name: str
    institution_name: str
    issue_date: str
    cgpa: Optional[str] = None
    sha256_hash: str
    status: str
    revocation_reason: Optional[str] = None
    revoked_at: Optional[str] = None


class VerificationChecks(BaseModel):
    hash_match: bool
    signature_valid: bool
    tamper_detected: bool
    ledger_anchored: bool


class VerifyResponse(BaseModel):
    verification_status: str  # VALID, TAMPERED, REVOKED, NOT_FOUND
    certificate: Optional[CertificateDetail] = None
    checks: VerificationChecks
    message: str


class RevokeRequest(BaseModel):
    revocation_reason: str


class RevokeResponse(BaseModel):
    id: str
    status: str
    revocation_reason: str
    revoked_at: datetime