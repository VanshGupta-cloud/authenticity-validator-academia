from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import uuid as uuid_lib
from src.database import get_db
from src import schemas
from src.security import decode_access_token
from src.certificate_crypto import build_canonical_payload, hash_certificate, sign_hash

router = APIRouter(prefix="/certificates", tags=["certificate-issuance"])

@router.post("/issue", response_model=schemas.CertificateIssueResponse, status_code=status.HTTP_201_CREATED)
def issue_certificate(
    payload: schemas.CertificateIssueRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(...)
):
    token = authorization.replace("Bearer ", "")
    try:
        token_data = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    institution_id = token_data.get("sub")
    if not institution_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    cert_payload = build_canonical_payload(
        student_name=payload.student_name,
        student_roll_no=payload.student_roll_no,
        degree_name=payload.course_name,
        issue_date=payload.issue_date,
        institution_id=institution_id,
    )
    cert_hash = hash_certificate(cert_payload)
    signature = sign_hash(cert_hash, "institution_private_key.pem")
    cert_number = f"CERT-{datetime.utcnow().year}-{str(uuid_lib.uuid4())[:8].upper()}"

    result = db.execute(
        text("""
            INSERT INTO certificates (
                certificate_number, institution_id, student_name, student_roll_no,
                course_name, issue_date, marks, cgpa, sha256_hash, digital_signature, status
            )
            VALUES (
                :cert_number, :institution_id, :student_name, :student_roll_no,
                :course_name, :issue_date, :marks, :cgpa, :hash, :signature, 'ISSUED'
            )
            RETURNING id, certificate_number, student_name, student_roll_no,
                      course_name, issue_date, marks, cgpa, sha256_hash, digital_signature, status
        """),
        {
            "cert_number": cert_number,
            "institution_id": institution_id,
            "student_name": payload.student_name,
            "student_roll_no": payload.student_roll_no,
            "course_name": payload.course_name,
            "issue_date": payload.issue_date,
            "marks": payload.marks,
            "cgpa": payload.cgpa,
            "hash": cert_hash,
            "signature": signature,
        }
    ).fetchone()
    db.commit()

    return dict(result._mapping)