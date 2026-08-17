from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from src.database import get_db
from src import schemas, models
from src.security import decode_access_token
from src.certificate_crypto import build_canonical_payload, hash_certificate, sign_hash

router = APIRouter(prefix="/certificates", tags=["certificate-issuance"])

@router.post("/issue", response_model=schemas.CertificateResponse, status_code=status.HTTP_201_CREATED)
def issue_certificate(
    payload: schemas.CertificateIssueRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    institution_id = None
    issuer_id = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
        try:
            token_data = decode_access_token(token)
            institution_id = token_data.get("institution_id") or token_data.get("sub")
            issuer_id = token_data.get("sub")
        except Exception:
            pass

    if not institution_id:
        inst = db.query(models.Institution).first()
        if inst:
            institution_id = inst.id
        else:
            institution_id = str(uuid.uuid4())

    cert_number = f"CERT-2026-{str(uuid.uuid4())[:8].upper()}"

    cert_payload = build_canonical_payload(
        student_name=payload.student_name,
        student_roll_no=payload.student_roll_no,
        degree_name=payload.course_name,
        issue_date=payload.issue_date,
        institution_id=institution_id,
    )
    cert_hash = hash_certificate(cert_payload)
    signature = sign_hash(cert_hash)

    new_cert = models.Certificate(
        id=str(uuid.uuid4()),
        certificate_number=cert_number,
        institution_id=institution_id,
        issuer_id=issuer_id,
        student_name=payload.student_name.strip(),
        student_roll_no=payload.student_roll_no.strip(),
        course_name=payload.course_name.strip(),
        issue_date=str(payload.issue_date).strip(),
        marks=payload.marks,
        cgpa=payload.cgpa,
        sha256_hash=cert_hash,
        digital_signature=signature,
        status="ISSUED",
        qr_code_url=f"/verify?hash={cert_hash}",
        pdf_url=f"/api/v1/certificates/download/{cert_number}",
        created_at=datetime.utcnow()
    )

    db.add(new_cert)
    db.commit()
    db.refresh(new_cert)

    return new_cert