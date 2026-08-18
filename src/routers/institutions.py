import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Institution
from src.security import hash_password, verify_password, create_access_token


router = APIRouter(
    prefix="/institutions",
    tags=["institutions"]
)


# ============================================================
# In-memory OTP storage for registration flow
# ============================================================

PENDING_REGISTRATIONS: Dict[str, dict] = {}


# ============================================================
# Request Models
# ============================================================

class InstitutionRegisterModel(BaseModel):
    name: str
    official_email: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class VerifyOtpModel(BaseModel):
    official_email: Optional[str] = None
    email: Optional[str] = None
    otp_code: str


class SetPasswordModel(BaseModel):
    official_email: Optional[str] = None
    email: Optional[str] = None
    password: str
    confirm_password: Optional[str] = None


class InstitutionLoginModel(BaseModel):
    official_email: Optional[str] = None
    email: Optional[str] = None
    password: str


# ============================================================
# Institution Registration
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_200_OK
)
def register_institution(
    payload: InstitutionRegisterModel,
    db: Session = Depends(get_db)
):
    target_email = (
        payload.official_email
        or payload.email
        or ""
    ).lower().strip()

    if not target_email or "@" not in target_email:
        raise HTTPException(
            status_code=422,
            detail="A valid official email is required."
        )

    # Generate 6-digit OTP.
    # Fixed OTP is intentionally retained from the existing
    # prototype/demo implementation.
    otp_code = "123456"

    expires_at = (
        datetime.utcnow()
        + timedelta(minutes=10)
    )

    PENDING_REGISTRATIONS[target_email] = {
        "otp": otp_code,
        "expires_at": expires_at,
        "name": payload.name.strip(),
        "address": (payload.address or "").strip()
    }

    return {
        "message": (
            f"Verification code sent to {target_email}. "
            "Valid for 10 minutes."
        ),
        "official_email": target_email,
        "otp_hint": otp_code
    }


# ============================================================
# OTP Verification
# ============================================================

@router.post(
    "/verify-otp",
    status_code=status.HTTP_200_OK
)
def verify_otp(
    payload: VerifyOtpModel
):
    target_email = (
        payload.official_email
        or payload.email
        or ""
    ).lower().strip()

    clean_code = payload.otp_code.strip()

    pending = PENDING_REGISTRATIONS.get(target_email)

    # Allow the prototype test code or a stored OTP.
    if (
        clean_code != "123456"
        and (
            not pending
            or pending.get("otp") != clean_code
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP code. Please try again."
        )

    if (
        pending
        and datetime.utcnow()
        > pending.get(
            "expires_at",
            datetime.utcnow()
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "OTP code has expired. "
                "Please register again."
            )
        )

    return {
        "message": (
            "OTP verified successfully. "
            "Please set your institutional password."
        ),
        "official_email": target_email
    }


# ============================================================
# Set Institution Password
# ============================================================

@router.post(
    "/set-password",
    status_code=status.HTTP_200_OK
)
def set_password(
    payload: SetPasswordModel,
    db: Session = Depends(get_db)
):
    target_email = (
        payload.official_email
        or payload.email
        or ""
    ).lower().strip()

    if not target_email:
        raise HTTPException(
            status_code=422,
            detail="Official email is required."
        )

    if (
        payload.confirm_password
        and payload.password != payload.confirm_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match."
        )

    if len(payload.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters."
        )

    pending = PENDING_REGISTRATIONS.get(
        target_email,
        {}
    )

    name = pending.get(
        "name",
        "Academic Institution"
    )

    inst = (
        db.query(Institution)
        .filter(Institution.email == target_email)
        .first()
    )

    if inst:
        inst.password_hash = hash_password(
            payload.password
        )
        inst.is_verified = True

        if name and name != "Academic Institution":
            inst.name = name

    else:
        inst = Institution(
            id=str(uuid.uuid4()),
            name=name,
            code=target_email.split("@")[0][:8].upper(),
            email=target_email,
            password_hash=hash_password(
                payload.password
            ),
            is_verified=True,
            created_at=datetime.utcnow()
        )

        db.add(inst)

    db.commit()
    db.refresh(inst)

    # Clean up pending registration.
    if target_email in PENDING_REGISTRATIONS:
        del PENDING_REGISTRATIONS[target_email]

    return {
        "message": (
            "Institutional password successfully "
            "configured. You may now login."
        ),
        "official_email": target_email
    }


# ============================================================
# Institution Login
# ============================================================

@router.post(
    "/login",
    status_code=status.HTTP_200_OK
)
def login_institution(
    payload: InstitutionLoginModel,
    db: Session = Depends(get_db)
):
    target_email = (
        payload.official_email
        or payload.email
        or ""
    ).lower().strip()

    if not target_email:
        raise HTTPException(
            status_code=422,
            detail="Official email is required."
        )

    inst = (
        db.query(Institution)
        .filter(Institution.email == target_email)
        .first()
    )

    # Pre-seeded credentials fallback for demo.
    if (
        not inst
        and target_email == "issuer@git.edu"
        and payload.password == "issuer123"
    ):
        inst = Institution(
            id=str(uuid.uuid4()),
            name="Global Institute of Technology",
            code="GIT",
            email="issuer@git.edu",
            password_hash=hash_password(
                "issuer123"
            ),
            is_verified=True,
            created_at=datetime.utcnow()
        )

        db.add(inst)
        db.commit()
        db.refresh(inst)

    if not inst or not inst.password_hash:
        raise HTTPException(
            status_code=401,
            detail="Invalid institutional credentials."
        )

    if not verify_password(
        payload.password,
        inst.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid institutional credentials."
        )

    token = create_access_token({
        "sub": str(inst.id),
        "institution_id": str(inst.id),
        "role": "ISSUER",
        "institution_name": inst.name,
        "email": inst.email
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "institution_id": str(inst.id),
        "institution_name": inst.name,
        "official_email": inst.email
    }


# ============================================================
# List Institutions
# ============================================================

@router.get("/")
def list_institutions(
    db: Session = Depends(get_db)
):
    return db.query(Institution).all()