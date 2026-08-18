import uuid
import sys
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src import models
from src.security import hash_password, verify_password, create_access_token
from src.email_service import send_otp_email

logger = logging.getLogger("uvicorn.error")


router = APIRouter(
    prefix="/institutions",
    tags=["institutions"]
)


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

    # Generate a real random 6-digit cryptographic OTP
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Invalidate prior OTPs for this email
    db.query(models.OtpVerification).filter(models.OtpVerification.email == target_email).delete()

    otp_record = models.OtpVerification(
        id=str(uuid.uuid4()),
        email=target_email,
        otp_code=otp_code,
        institution_name=payload.name.strip(),
        address=(payload.address or "").strip(),
        is_verified=False,
        expires_at=expires_at,
        created_at=datetime.utcnow()
    )
    db.add(otp_record)
    db.commit()

    # Prominently print and flush OTP to server console immediately
    print(f"\n=======================================================", flush=True)
    print(f" [INSTITUTION REGISTRATION]", flush=True)
    print(f" Institution: {payload.name.strip()}", flush=True)
    print(f" Target Email: {target_email}", flush=True)
    print(f" REAL OTP CODE: >>> {otp_code} <<<", flush=True)
    print(f" Expires: 10 minutes", flush=True)
    print(f"=======================================================\n", flush=True)
    sys.stdout.flush()

    # Dispatch real email via Resend / SMTP
    sent, msg = send_otp_email(target_email, otp_code)

    return {
        "message": f"Verification code sent to {target_email}. Please check your inbox or terminal.",
        "official_email": target_email,
        "email_delivered": sent,
        "otp_debug": otp_code
    }


# ============================================================
# OTP Verification
# ============================================================

@router.post(
    "/verify-otp",
    status_code=status.HTTP_200_OK
)
def verify_otp(
    payload: VerifyOtpModel,
    db: Session = Depends(get_db)
):
    target_email = (
        payload.official_email
        or payload.email
        or ""
    ).lower().strip()

    clean_code = payload.otp_code.strip()

    otp_record = db.query(models.OtpVerification).filter(
        models.OtpVerification.email == target_email
    ).order_by(models.OtpVerification.created_at.desc()).first()

    if not otp_record or otp_record.otp_code != clean_code:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP code. Please enter the 6-digit code sent to your email or terminal."
        )

    if datetime.utcnow() > otp_record.expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP code has expired. Please register again to receive a new code."
        )

    otp_record.is_verified = True
    db.commit()

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
def set_institution_password(
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

    if len(payload.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters."
        )

    if (
        payload.confirm_password
        and payload.password != payload.confirm_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match."
        )

    otp_record = db.query(models.OtpVerification).filter(
        models.OtpVerification.email == target_email
    ).order_by(models.OtpVerification.created_at.desc()).first()

    inst_name = otp_record.institution_name if otp_record else "Academic Institution"

    existing_inst = db.query(models.Institution).filter(models.Institution.email == target_email).first()
    if existing_inst:
        existing_inst.password_hash = hash_password(payload.password)
        existing_inst.is_verified = True
        if inst_name and inst_name != "Academic Institution":
            existing_inst.name = inst_name
        db.commit()
        db.refresh(existing_inst)
    else:
        new_inst = models.Institution(
            id=str(uuid.uuid4()),
            name=inst_name,
            code="GIT",
            email=target_email,
            official_email=target_email,
            password_hash=hash_password(payload.password),
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db.add(new_inst)
        db.commit()
        db.refresh(new_inst)

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
        db.query(models.Institution)
        .filter(models.Institution.email == target_email)
        .first()
    )

    # Pre-seeded credentials fallback for demo.
    if (
        not inst
        and target_email == "issuer@git.edu"
        and payload.password == "issuer123"
    ):
        inst = models.Institution(
            id=str(uuid.uuid4()),
            name="Global Institute of Technology",
            code="GIT",
            email="issuer@git.edu",
            official_email="issuer@git.edu",
            password_hash=hash_password("issuer123"),
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
    return db.query(models.Institution).all()
