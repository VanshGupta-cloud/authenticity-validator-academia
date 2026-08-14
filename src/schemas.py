from pydantic import BaseModel, EmailStr
from uuid import UUID
from enum import Enum

class Role(str, Enum):
    ADMIN = "ADMIN"
    ISSUER = "ISSUER"
    VERIFIER = "VERIFIER"

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