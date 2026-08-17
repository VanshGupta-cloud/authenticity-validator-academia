from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from pathlib import Path
import uuid as uuid_lib
from src.database import get_db
from src import schemas
from src.security import decode_access_token
from src.certificate_crypto import build_canonical_payload, hash_certificate, sign_hash_from_pem
from PDF.certificate_generator import Certificate, generate_certificate_pdf

router = APIRouter(prefix="/certificates", tags=["certificate-issuance"])
security = HTTPBearer()

@router.post("/issue", response_model=schemas.CertificateIssueResponse, status_code=status.HTTP_201_CREATED)
def issue_certificate(
    payload: schemas.CertificateIssueRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        token_data = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    institution_id = token_data.get("sub")
    if not institution_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    inst_row = db.execute(
        text("SELECT private_key, name FROM institutions WHERE id = :id"),
        {"id": institution_id}
    ).fetchone()

    if not inst_row or not inst_row.private_key:
        raise HTTPException(status_code=500, detail="Institution signing key not found")

    cert_payload = build_canonical_payload(
        student_name=payload.student_name,
        student_roll_no=payload.student_roll_no,
        degree_name=payload.course_name,
        issue_date=payload.issue_date,
        institution_id=institution_id,
        marks=payload.marks,
        cgpa=payload.cgpa,
    )
    print("PAYLOAD:", cert_payload)
    cert_hash = hash_certificate(cert_payload)
    signature = sign_hash_from_pem(cert_hash, inst_row.private_key)
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

    # --- PDF + QR generation ---
    certificate_obj = Certificate(
        id=result.id,
        certificate_number=result.certificate_number,
        institution_id=institution_id,
        issuer_id=institution_id,
        student_name=result.student_name,
        student_roll_no=result.student_roll_no,
        course_name=result.course_name,
        issue_date=result.issue_date,
        marks=result.marks,
        cgpa=result.cgpa,
        sha256_hash=result.sha256_hash,
        digital_signature=result.digital_signature,
        status="ISSUED",
    )

    output_path = f"generated_certificates/{cert_number}.pdf"

    pdf_path = generate_certificate_pdf(
        certificate=certificate_obj,
        certificate_number=cert_number,
        output_path=output_path,
        institution_name=inst_row.name,
        verification_base_url="http://localhost:8000/verify",
    )

    db.execute(
        text("UPDATE certificates SET pdf_url = :pdf_url WHERE id = :id"),
        {"pdf_url": pdf_path, "id": result.id}
    )
    db.commit()

    response_data = dict(result._mapping)
    response_data["pdf_url"] = pdf_path

    return response_data