from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db
from src.schemas import CertificateVerifyRequest, CertificateVerifyResponse
from src.certificate_crypto import build_canonical_payload, hash_certificate, verify_signature

router = APIRouter(prefix="/certificates", tags=["certificate-verification"])

@router.post("/verify", response_model=CertificateVerifyResponse)
def verify_certificate(payload: CertificateVerifyRequest, db: Session = Depends(get_db)):
    if not payload.certificate_id and not payload.certificate_number:
        raise HTTPException(status_code=400, detail="Provide either certificate_id or certificate_number")

    if payload.certificate_id:
        row = db.execute(
            text("SELECT * FROM certificates WHERE id = :id"),
            {"id": str(payload.certificate_id)}
        ).fetchone()
    else:
        row = db.execute(
            text("SELECT * FROM certificates WHERE certificate_number = :num"),
            {"num": payload.certificate_number}
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Get the institution's public key to verify the signature
    inst_row = db.execute(
        text("SELECT public_key FROM institutions WHERE id = :id"),
        {"id": str(row.institution_id)}
    ).fetchone()

    if not inst_row or not inst_row.public_key:
        raise HTTPException(status_code=500, detail="Institution public key not found")

    # Recompute the hash from the DB's own stored fields
    recomputed_payload = build_canonical_payload(
        student_name=row.student_name,
        student_roll_no=row.student_roll_no,
        degree_name=row.course_name,
        issue_date=str(row.issue_date),
        institution_id=str(row.institution_id),
    )
    recomputed_hash = hash_certificate(recomputed_payload)

    hash_match = (recomputed_hash == row.sha256_hash)
    signature_valid = verify_signature(row.sha256_hash, row.digital_signature, inst_row.public_key)

    hash_signature_valid = hash_match and signature_valid
    tamper_detected = not hash_match

    return {
        "hash_signature_valid": hash_signature_valid,
        "tamper_detected": tamper_detected,
        "certificate_number": row.certificate_number,
        "student_name": row.student_name,
        "student_roll_no": row.student_roll_no,
        "course_name": row.course_name,
        "issue_date": row.issue_date,
        "marks": row.marks,
        "cgpa": row.cgpa,
        "status": row.status,
        "message": "Certificate is authentic and unaltered." if hash_signature_valid else "Certificate record integrity check failed — possible tampering detected.",
    }