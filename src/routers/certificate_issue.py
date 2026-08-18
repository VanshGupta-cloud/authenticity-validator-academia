import re
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
    user_issuer_id = None

    if token:
        try:
            token_data = decode_access_token(token)

            sub_id = token_data.get("sub")
            inst_id_token = token_data.get("institution_id")

            # 1. Check if token contains a valid institution_id
            if inst_id_token and str(inst_id_token).strip():
                inst_match = db.query(models.Institution).filter(
                    models.Institution.id == str(inst_id_token).strip()
                ).first()
                if inst_match:
                    institution_id = inst_match.id
                    institution_name = inst_match.name
                    private_key = getattr(inst_match, "private_key", None)

            # 2. Check if sub is directly an institution
            if not institution_id and sub_id:
                inst_match = db.query(models.Institution).filter(
                    models.Institution.id == str(sub_id).strip()
                ).first()
                if inst_match:
                    institution_id = inst_match.id
                    institution_name = inst_match.name
                    private_key = getattr(inst_match, "private_key", None)
                else:
                    # Check if sub is a User
                    user_match = db.query(models.User).filter(
                        models.User.id == str(sub_id).strip()
                    ).first()
                    if user_match:
                        user_issuer_id = user_match.id
                        if user_match.institution_id:
                            inst_match = db.query(models.Institution).filter(
                                models.Institution.id == str(user_match.institution_id).strip()
                            ).first()
                            if inst_match:
                                institution_id = inst_match.id
                                institution_name = inst_match.name
                                private_key = getattr(inst_match, "private_key", None)

            if token_data.get("institution_name"):
                institution_name = token_data["institution_name"]

        except Exception as e:
            print(f"[AUTH TOKEN DECODE NOTICE] {e}")

    # Fallback to first registered institution if none was resolved
    if not institution_id:
        inst_fallback = db.query(models.Institution).first()
        if inst_fallback:
            institution_id = inst_fallback.id
            institution_name = inst_fallback.name
            private_key = getattr(inst_fallback, "private_key", None)
        else:
            # Create a default institution record so FK constraint is always valid
            new_inst_id = str(uuid_lib.uuid4())
            new_inst = models.Institution(
                id=new_inst_id,
                name=institution_name,
                code=f"{''.join([w[0] for w in (institution_name or 'INST').split() if w.isalnum()])[:4].upper() or 'INST'}-{uuid_lib.uuid4().hex[:6].upper()}",
                official_email="admin@git.edu",
                is_verified=True,
                created_at=datetime.utcnow()
            )
            db.add(new_inst)
            db.commit()
            db.refresh(new_inst)
            institution_id = new_inst.id

    # Verify user_issuer_id foreign key existence in users table
    valid_issuer_id = None
    if user_issuer_id:
        u_chk = db.query(models.User).filter(models.User.id == str(user_issuer_id)).first()
        if u_chk:
            valid_issuer_id = str(u_chk.id)

    # ---------------------------------------------------------
    # BUILD CANONICAL CERTIFICATE PAYLOAD
    # ---------------------------------------------------------

    cert_payload = build_canonical_payload(
        student_name=payload.student_name,
        student_roll_no=payload.student_roll_no,
        degree_name=payload.course_name,
        issue_date=str(payload.issue_date),
        institution_id=str(institution_id),
        marks=float(re.search(r"(\d+(?:\.\d+)?)", str(payload.marks)).group(1)) if payload.marks and re.search(r"(\d+(?:\.\d+)?)", str(payload.marks)) else None,
        cgpa=float(re.search(r"(\d+(?:\.\d+)?)", str(payload.cgpa)).group(1)) if payload.cgpa and re.search(r"(\d+(?:\.\d+)?)", str(payload.cgpa)) else None,
    )

    # ---------------------------------------------------------
    # HASH
    # ---------------------------------------------------------

    cert_hash = hash_certificate(cert_payload)

    # Check for duplicate issuance of identical certificate
    existing = db.query(models.Certificate).filter(models.Certificate.sha256_hash == cert_hash).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Certificate already issued for this student record (Certificate #{existing.certificate_number})."
        )

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
            "%d/%m/%Y"
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
        marks=float(re.search(r"(\d+(?:\.\d+)?)", str(payload.marks)).group(1)) if payload.marks and re.search(r"(\d+(?:\.\d+)?)", str(payload.marks)) else None,
        cgpa=float(re.search(r"(\d+(?:\.\d+)?)", str(payload.cgpa)).group(1)) if payload.cgpa and re.search(r"(\d+(?:\.\d+)?)", str(payload.cgpa)) else None,
        sha256_hash=cert_hash,
        digital_signature=signature,
        status="ISSUED",
    )

    generate_certificate_pdf(
        certificate=certificate_obj,
        certificate_number=cert_number,
        output_path=output_path,
        institution_name=institution_name,
        verification_base_url=(
            "http://localhost:8000/verify"
        ),
    )

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
        issuer_id=valid_issuer_id,
        student_name=payload.student_name.strip(),
        student_roll_no=payload.student_roll_no.strip(),
        course_name=payload.course_name.strip(),
        issue_date=str(payload.issue_date).strip(),
        marks=float(re.search(r"(\d+(?:\.\d+)?)", str(payload.marks)).group(1)) if payload.marks and re.search(r"(\d+(?:\.\d+)?)", str(payload.marks)) else None,
        cgpa=float(re.search(r"(\d+(?:\.\d+)?)", str(payload.cgpa)).group(1)) if payload.cgpa and re.search(r"(\d+(?:\.\d+)?)", str(payload.cgpa)) else None,
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
        "pdf_url": pdf_url_clean
    }


@router.post("/batch-issue")
def batch_issue_certificates(
    records: list[dict],
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    issued = []
    for r in records:
        req = schemas.CertificateIssueRequest(
            student_name=r.get("student_name", "Student"),
            student_roll_no=r.get("student_roll_no", "CS-2026-000"),
            course_name=r.get("course_name", "Bachelor of Technology"),
            issue_date=r.get("issue_date", str(date.today())),
            marks=r.get("marks"),
            cgpa=r.get("cgpa")
        )
        try:
            res = issue_certificate(req, db, credentials)
            issued.append(res)
        except HTTPException as he:
            if he.status_code == 409:
                existing_cert = db.query(models.Certificate).filter(
                    models.Certificate.student_roll_no == req.student_roll_no
                ).first()
                if existing_cert:
                    issued.append({
                        "id": existing_cert.id,
                        "certificate_number": existing_cert.certificate_number,
                        "student_name": existing_cert.student_name,
                        "student_roll_no": existing_cert.student_roll_no,
                        "course_name": existing_cert.course_name,
                        "issue_date": existing_cert.issue_date,
                        "marks": existing_cert.marks,
                        "cgpa": existing_cert.cgpa,
                        "sha256_hash": existing_cert.sha256_hash,
                        "digital_signature": existing_cert.digital_signature,
                        "status": existing_cert.status,
                        "qr_code_url": existing_cert.qr_code_url,
                        "pdf_url": existing_cert.pdf_url
                    })
            else:
                raise he
        
    return {
        "total_records": len(issued),
        "certificates": issued,
        "message": f"Successfully processed {len(issued)} certificates in batch."
    }
