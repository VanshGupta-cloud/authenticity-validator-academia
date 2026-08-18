from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class Role(str, Enum):
    ADMIN = "ADMIN"
    ISSUER = "ISSUER"
    VERIFIER = "VERIFIER"


# ============================================================
# Individual User Auth (used by auth.py)
# ============================================================

class RegisterRequest(BaseModel):
    institution_id: Optional[UUID] = None
    full_name: str
    email: EmailStr
    password: str
    role: Role = Role.ISSUER


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: Role
    institution_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================================
# Institution Onboarding (used by institutions.py)
# ============================================================

class InstitutionRegisterRequest(BaseModel):
    name: str
    official_email: EmailStr
    address: Optional[str] = None


class InstitutionRegisterResponse(BaseModel):
    id: UUID
    name: str
    official_email: EmailStr
    is_email_verified: bool


class OTPVerifyRequest(BaseModel):
    official_email: EmailStr
    otp_code: str


class OTPVerifyResponse(BaseModel):
    message: str
    is_email_verified: bool


class SetPasswordRequest(BaseModel):
    official_email: EmailStr
    password: str


class InstitutionLoginRequest(BaseModel):
    official_email: EmailStr
    password: str


class InstitutionLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    institution_id: UUID
    name: str


# ============================================================
# Certificate Issuance (used by certificate_issue.py)
# ============================================================

class CertificateIssueRequest(BaseModel):
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: str
    marks: Optional[str] = None
    cgpa: Optional[str] = None


class CertificateIssueResponse(BaseModel):
    id: UUID
    certificate_number: str
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: date
    marks: Optional[Decimal] = None
    cgpa: Optional[Decimal] = None
    sha256_hash: str
    digital_signature: str
    status: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Certificate Verification (used by certificate_verify.py)
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
# Certificate CRUD (used by certificates.py — Vansh's endpoints)
# ============================================================

class CertificateBase(BaseModel):
    certificate_number: str
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: date
    marks: Optional[Decimal] = None
    cgpa: Optional[Decimal] = None
    sha256_hash: str
    digital_signature: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None


class CertificateCreate(CertificateBase):
    institution_id: UUID
    issuer_id: UUID
    batch_id: Optional[UUID] = None


class CertificateUpdate(BaseModel):
    status: Optional[str] = None
    revocation_reason: Optional[str] = None


class CertificateResponse(CertificateBase):
    id: UUID
    institution_id: UUID
    issuer_id: UUID
    batch_id: Optional[UUID] = None
    status: str
    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)