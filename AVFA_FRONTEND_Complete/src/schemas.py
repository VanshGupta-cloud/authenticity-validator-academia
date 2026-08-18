from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class Role(str, Enum):
    ADMIN = "ADMIN"
    ISSUER = "ISSUER"
    VERIFIER = "VERIFIER"
    STUDENT = "STUDENT"


# ============================================================
# Individual User Auth (used by auth.py)
# ============================================================

class RegisterRequest(BaseModel):
    institution_id: Optional[Union[UUID, str]] = None
    full_name: str
    email: EmailStr
    password: str
    role: Union[Role, str] = Role.ISSUER


class UserResponse(BaseModel):
    id: Union[UUID, str]
    full_name: str
    email: EmailStr
    role: Union[Role, str]
    institution_id: Optional[Union[UUID, str]] = None

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
    issue_date: Union[str, date]
    marks: Optional[Union[str, Decimal, float]] = None
    cgpa: Optional[Union[str, Decimal, float]] = None


class CertificateIssueResponse(BaseModel):
    id: Union[UUID, str]
    certificate_number: str
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: Union[date, str]
    marks: Optional[Union[Decimal, str, float]] = None
    cgpa: Optional[Union[Decimal, str, float]] = None
    sha256_hash: str
    digital_signature: str
    status: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Certificate Verification & Mismatch Breakdown
# ============================================================

class FieldMismatch(BaseModel):
    field: str
    document_value: Optional[str] = None
    record_value: Optional[str] = None


class CertificateVerifyRequest(BaseModel):
    certificate_id: Optional[Union[UUID, str]] = None
    certificate_number: Optional[str] = None
    sha256_hash: Optional[str] = None
    queried_hash: Optional[str] = None


class CertificateVerifyResponse(BaseModel):
    hash_signature_valid: Optional[bool] = None
    tamper_detected: Optional[bool] = None
    certificate_number: Optional[str] = None
    student_name: Optional[str] = None
    student_roll_no: Optional[str] = None
    course_name: Optional[str] = None
    issue_date: Optional[Any] = None
    marks: Optional[Any] = None
    cgpa: Optional[Any] = None
    status: Optional[str] = None
    verification_status: Optional[str] = None
    message: Optional[str] = None
    found: Optional[bool] = None
    overall_similarity: Optional[float] = None
    field_mismatches: Optional[List[Dict[str, Any]]] = None
    certificate: Optional[Dict[str, Any]] = None


# ============================================================
# Certificate CRUD & Dashboard Details
# ============================================================

class CertificateBase(BaseModel):
    certificate_number: str
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: Union[date, str]
    marks: Optional[Union[Decimal, str, float]] = None
    cgpa: Optional[Union[Decimal, str, float]] = None
    sha256_hash: str
    digital_signature: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None


class CertificateCreate(CertificateBase):
    institution_id: Optional[Union[UUID, str]] = None
    issuer_id: Optional[Union[UUID, str]] = None
    batch_id: Optional[Union[UUID, str]] = None


class CertificateUpdate(BaseModel):
    status: Optional[str] = None
    revocation_reason: Optional[str] = None


class CertificateResponse(CertificateBase):
    id: Union[UUID, str]
    institution_id: Optional[Union[UUID, str]] = None
    issuer_id: Optional[Union[UUID, str]] = None
    batch_id: Optional[Union[UUID, str]] = None
    status: str
    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Verification & Revocation Extended Models
# ============================================================

class VerifyRequest(BaseModel):
    queried_hash: Optional[str] = None
    certificate_number: Optional[str] = None


class CertificateDetail(BaseModel):
    certificate_number: str
    student_name: str
    student_roll_no: str
    degree_name: Optional[str] = None
    course_name: Optional[str] = None
    institution_name: Optional[str] = None
    issue_date: Optional[str] = None
    marks: Optional[str] = None
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
    checks: Optional[VerificationChecks] = None
    message: str


class RevokeRequest(BaseModel):
    revocation_reason: str


class RevokeResponse(BaseModel):
    id: str
    status: str
    revocation_reason: str
    revoked_at: datetime
