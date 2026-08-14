import re
import secrets
import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db
from src.schemas import (
    InstitutionRegisterRequest, InstitutionRegisterResponse,
    OTPVerifyRequest, OTPVerifyResponse, SetPasswordRequest
)
from src.email_service import send_otp_email
from src.security import hash_password

def generate_institution_code(name: str) -> str:
    slug = re.sub(r'[^A-Z0-9]', '', name.upper())[:10]
    suffix = secrets.token_hex(2).upper()
    return f"{slug}-{suffix}"

router = APIRouter(
    prefix="/institutions",
    tags=["institutions"]
)

@router.post(
    "/register",
    response_model=InstitutionRegisterResponse,
    status_code=201
)
def register_institution(
    payload: InstitutionRegisterRequest,
    db: Session = Depends(get_db)
):
    existing = db.execute(
        text("""
            SELECT id
            FROM institutions
            WHERE official_email = :email
        """),
        {"email": payload.official_email}
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Institution already registered with this email"
        )
    institution_code = generate_institution_code(payload.name)
    otp_code = str(random.randint(100000, 999999))
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    result = db.execute(
    text("""
        INSERT INTO institutions (name, code, email, official_email, otp_code, otp_expires_at, is_email_verified, is_verified)
        VALUES (:name, :code, :email, :email, :otp, :expires, false, false)
        RETURNING id, name, official_email, is_email_verified
    """),
    {
        "name": payload.name,
        "code": institution_code,
        "email": payload.official_email,
        "otp": otp_code,
        "expires": otp_expires_at
    }
).fetchone()
    db.commit()

    send_otp_email(
        payload.official_email,
        otp_code
    )

    return {
        "id": result.id,
        "name": result.name,
        "official_email": result.official_email,
        "is_email_verified": result.is_email_verified,
    }

@router.post(
    "/verify-otp",
    response_model=OTPVerifyResponse
)
def verify_otp(
    payload: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    row = db.execute(
        text("""
            SELECT otp_code, otp_expires_at
            FROM institutions
            WHERE official_email = :email
        """),
        {"email": payload.official_email}
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    if row.otp_code != payload.otp_code:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    if datetime.now(timezone.utc) > row.otp_expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )

    db.execute(
        text("""
            UPDATE institutions
            SET is_email_verified = true
            WHERE official_email = :email
        """),
        {"email": payload.official_email}
    )

    db.commit()

    return {
        "message": "Email verified successfully",
        "is_email_verified": True
    }

@router.post("/set-password")
def set_password(
    payload: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    row = db.execute(
        text("""
            SELECT is_email_verified
            FROM institutions
            WHERE official_email = :email
        """),
        {"email": payload.official_email}
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    if not row.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email not verified yet"
        )

    hashed = hash_password(payload.password)

    db.execute(
        text("""
            UPDATE institutions
            SET password_hash = :password_hash,
                is_verified = true
            WHERE official_email = :email
        """),
        {
            "password_hash": hashed,
            "email": payload.official_email
        }
    )

    db.commit()

    return {
        "message": "Password set successfully. You can now log in."
    }