from enum import Enum
from typing import Optional
from datetime import datetime, date
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

# Certificate Schemas
class CertificateBase(BaseModel):
    certificate_number: str
    student_name: str
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