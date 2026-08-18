import uuid as uuid_lib
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.database import get_db
from src import schemas, models
from src.security import decode_access_token
from src.certificate_crypto import (
    build_canonical_payload,
    hash_certificate,
    sign_hash_from_pem,
    sign_hash,
)
from PDF.certificate_generator import (
    Certificate,
    generate_certificate_pdf,
)


router = APIRouter(
    prefix="/certificates",
    tags=["certificate-issuance"],
)

security = HTTPBearer(auto_error=False)


@router.post(
    "/issue",
    response_model=schemas.CertificateIssueResponse,
    status_code=status.HTTP_201_CREATED,
)
def issue_certificate(
    payload: schemas.CertificateIssueRequest,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    # ---------------------------------------------------------
    # AUTHENTICATION / INSTITUTION IDENTIFICATION
    # ---------------------------------------------------------

    token = (
        credentials.credentials
        if credentials
        else None
    )

    institution_id = None
    institution_name = "Global Institute of Technology"
    private_key = None

    if token:
        try:
            token_data = decode_access_token(token)

            institution_id = (
                token_data.get("institution_id")
                or token_data.get("sub")
            )

            if token_data.get("institution_name"):
                institution_name = token_data[
                    "institution_name"
                ]

        except Exception:
            # Keep the prototype's fallback behavior.
            pass

    if institution_id:
        inst = (
            db.query(models.Institution)
            .filter(
                models.Institution.id
                == str(institution_id)
            )
            .first()
        )

        if inst:
            institution_name = inst.name
            private_key = getattr(
                inst,
                "private_key",
                None,
            )

    # If no institution was identified from the token,
    # use the first institution available in the database.
    if not institution_id:
        inst = db.query(models.Institution).first()

        if inst:
            institution_id = inst.id
            institution_name = inst.name
            private_key = getattr(
                inst,
                "private_key",
                None,
            )
        else:
            institution_id = str(
                uuid_lib.uuid4()
            )

    # ---------------------------------------------------------
    # BUILD CANONICAL CERTIFICATE PAYLOAD
    # ---------------------------------------------------------

    cert_payload = build_canonical_payload(
        student_name=payload.student_name,
        student_roll_no=payload.student_roll_no,
        degree_name=payload.course_name,
        issue_date=str(payload.issue_date),
        institution_id=str(institution_id),
        marks=payload.marks,
        cgpa=payload.cgpa,
    )

    print("PAYLOAD:", cert_payload)

    # ---------------------------------------------------------
    # HASH
    # ---------------------------------------------------------

    cert_hash = hash_certificate(cert_payload)

    # ---------------------------------------------------------
    # DIGITAL SIGNATURE
    # ---------------------------------------------------------

    if private_key:
        signature = sign_hash_from_pem(
            cert_hash,
            private_key,
        )
    else:
        signature = sign_hash(cert_hash)

    # ---------------------------------------------------------
    # CERTIFICATE IDENTIFIERS
    # ---------------------------------------------------------

    cert_number = (
        f"CERT-{datetime.utcnow().year}-"
        f"{str(uuid_lib.uuid4())[:8].upper()}"
    )

    cert_id = str(uuid_lib.uuid4())

    # ---------------------------------------------------------
    # PARSE DATE FOR PDF GENERATION
    # ---------------------------------------------------------

    parsed_date = date.today()

    if isinstance(payload.issue_date, str):
        for fmt in (
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ):
            try:
                parsed_date = datetime.strptime(
                    payload.issue_date.strip(),
                    fmt,
                ).date()
                break
            except ValueError:
                pass

    elif isinstance(payload.issue_date, datetime):
        parsed_date = payload.issue_date.date()

    elif isinstance(payload.issue_date, date):
        parsed_date = payload.issue_date

    # ---------------------------------------------------------
    # PDF + QR GENERATION
    # ---------------------------------------------------------

    output_path = (
        f"generated_certificates/"
        f"{cert_number}.pdf"
    )

    Path("generated_certificates").mkdir(
        parents=True,
        exist_ok=True,
    )

    certificate_obj = Certificate(
        id=cert_id,
        certificate_number=cert_number,
        institution_id=institution_id,
        issuer_id=institution_id,
        student_name=payload.student_name,
        student_roll_no=payload.student_roll_no,
        course_name=payload.course_name,
        issue_date=parsed_date,
        marks=payload.marks,
        cgpa=payload.cgpa,
        sha256_hash=cert_hash,
        digital_signature=signature,
        status="ISSUED",
    )

    pdf_path = generate_certificate_pdf(
        certificate=certificate_obj,
        certificate_number=cert_number,
        output_path=output_path,
        institution_name=institution_name,
        verification_base_url=(
            "http://localhost:8000/verify"
        ),
    )

    # Standardize PDF URL path.
    pdf_url_clean = (
        f"generated_certificates/"
        f"{cert_number}.pdf"
    )

    # ---------------------------------------------------------
    # DATABASE RECORD
    # ---------------------------------------------------------

    new_cert = models.Certificate(
        id=cert_id,
        certificate_number=cert_number,
        institution_id=str(institution_id),
        issuer_id=str(institution_id),
        student_name=payload.student_name.strip(),
        student_roll_no=payload.student_roll_no.strip(),
        course_name=payload.course_name.strip(),
        issue_date=str(payload.issue_date).strip(),
        marks=payload.marks,
        cgpa=payload.cgpa,
        sha256_hash=cert_hash,
        digital_signature=signature,
        status="ISSUED",
        qr_code_url=(
            f"/verify?cert_id={cert_number}"
        ),
        pdf_url=pdf_url_clean,
        created_at=datetime.utcnow(),
    )

    db.add(new_cert)
    db.commit()
    db.refresh(new_cert)

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return {
        "id": new_cert.id,
        "certificate_number": new_cert.certificate_number,
        "student_name": new_cert.student_name,
        "student_roll_no": new_cert.student_roll_no,
        "course_name": new_cert.course_name,
        "issue_date": new_cert.issue_date,
        "marks": new_cert.marks,
        "cgpa": new_cert.cgpa,
        "sha256_hash": new_cert.sha256_hash,
        "digital_signature": new_cert.digital_signature,
        "status": new_cert.status,
        "qr_code_url": new_cert.qr_code_url,
        "pdf_url": pdf_url_clean,
    }