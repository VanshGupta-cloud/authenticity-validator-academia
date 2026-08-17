from enum import Enum
from typing import Optional

from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr

# Enums
class Role(str, Enum):
    ADMIN = "ADMIN"
    ISSUER = "ISSUER"
    VERIFIER = "VERIFIER"

# Auth & User Schemas
class RegisterRequest(BaseModel):
    institution_id: UUID
    full_name: str
    email: EmailStr
    password: str
    role: Role

class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: Role
    institution_id: UUID

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class InstitutionRegisterRequest(BaseModel):
    name: str
    official_email: EmailStr
    address: str | None = None


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
    pdf_url: Optional[str] = None

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

# Certificate Schemas (Vansh's CRUD)
class CertificateBase(BaseModel):
    certificate_number: str
    student_name: str
    student_roll_no: str
    course_name: str
    issue_date: date
    sha256_hash: str
    digital_signature: str

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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)