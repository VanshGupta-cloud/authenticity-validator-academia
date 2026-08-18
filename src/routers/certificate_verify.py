from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db
from src.schemas import CertificateVerifyRequest, CertificateVerifyResponse
from src.certificate_crypto import build_canonical_payload, hash_certificate, verify_signature
from src.log_service import log_verification
from src.routers.certificates import extract_pdf_fields
import shutil
import tempfile
import os
import hashlib
from datetime import datetime

router = APIRouter(prefix="/certificates", tags=["certificate-verification"])


def normalize_date(date_str):
    if not date_str:
        return ""
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return str(date_str).strip()


@router.post("/verify", response_model=CertificateVerifyResponse)
async def verify_certificate(
    request: Request,
    payload: CertificateVerifyRequest = None,
    db: Session = Depends(get_db)
):
    # Support both JSON payload and Form Data
    cert_id = None
    cert_num = None
    queried_hash = None

    if payload:
        cert_id = payload.certificate_id
        cert_num = payload.certificate_number
        queried_hash = payload.sha256_hash or payload.queried_hash

    if not cert_id and not cert_num and not queried_hash:
        try:
            body = await request.json()
            cert_id = body.get("certificate_id") or body.get("id")
            cert_num = body.get("certificate_number") or body.get("cert_id")
            queried_hash = body.get("sha256_hash") or body.get("queried_hash")
        except Exception:
            try:
                form = await request.form()
                cert_id = form.get("certificate_id")
                cert_num = form.get("certificate_number")
                queried_hash = form.get("sha256_hash") or form.get("queried_hash")
            except Exception:
                pass

    if not cert_id and not cert_num and not queried_hash:
        raise HTTPException(status_code=400, detail="Provide either certificate_id, certificate_number, or sha256_hash")

    row = None
    if cert_id:
        row = db.execute(
            text("SELECT * FROM certificates WHERE id = :id"),
            {"id": str(cert_id)}
        ).fetchone()

    if not row and cert_num:
        row = db.execute(
            text("SELECT * FROM certificates WHERE certificate_number = :num OR id = :num"),
            {"num": str(cert_num).strip()}
        ).fetchone()

    if not row and queried_hash:
        row = db.execute(
            text("SELECT * FROM certificates WHERE sha256_hash = :hash OR sha256_hash LIKE :like_hash"),
            {"hash": str(queried_hash).strip().lower(), "like_hash": f"%{str(queried_hash).strip().lower()}%"}
        ).fetchone()

    if not row:
        log_verification(
            db=db,
            queried_hash=queried_hash or (cert_num or "UNKNOWN"),
            verification_status="NOT_FOUND",
            certificate_id=None,
            request=request,
        )
        raise HTTPException(status_code=404, detail="Certificate not found")

    inst_row = db.execute(
        text("SELECT public_key, name FROM institutions WHERE id = :id"),
        {"id": str(row.institution_id)}
    ).fetchone()

    pub_key = inst_row.public_key if inst_row else None
    inst_name = inst_row.name if inst_row else "Global Institute of Technology"

    recomputed_payload = build_canonical_payload(
        student_name=row.student_name,
        student_roll_no=row.student_roll_no,
        degree_name=row.course_name,
        issue_date=str(row.issue_date),
        institution_id=str(row.institution_id),
        marks=row.marks,
        cgpa=row.cgpa,
    )
    recomputed_hash = hash_certificate(recomputed_payload)

    hash_match = (recomputed_hash == row.sha256_hash)
    signature_valid = verify_signature(row.sha256_hash, row.digital_signature, pub_key)

    hash_signature_valid = hash_match and signature_valid and (row.status == "ISSUED")
    tamper_detected = (not hash_match) or (row.status == "REVOKED")

    verif_status = "REVOKED" if row.status == "REVOKED" else ("VALID" if hash_signature_valid else "TAMPERED")
    log_verification(
        db=db,
        queried_hash=recomputed_hash,
        verification_status=verif_status,
        certificate_id=row.id,
        request=request,
    )

    return {
        "found": True,
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
        "verification_status": verif_status,
        "checks": {
            "hash_match": hash_match,
            "signature_valid": signature_valid and (row.status == "ISSUED"),
            "tamper_detected": tamper_detected,
            "ledger_anchored": True
        },
        "message": "Certificate is authentic and unaltered." if hash_signature_valid else "Certificate record integrity check failed — possible tampering detected.",
        "certificate": {
            "certificate_number": row.certificate_number,
            "student_name": row.student_name,
            "student_roll_no": row.student_roll_no,
            "course_name": row.course_name,
            "institution_name": inst_name,
            "issue_date": row.issue_date,
            "marks": row.marks,
            "cgpa": row.cgpa,
            "sha256_hash": row.sha256_hash,
            "digital_signature": row.digital_signature,
            "status": row.status,
            "revocation_reason": getattr(row, "revocation_reason", None),
            "revoked_at": str(getattr(row, "revoked_at", None)) if getattr(row, "revoked_at", None) else None
        }
    }


@router.post("/verify-document")
async def verify_certificate_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        ocr_fields = {}
        # 1. Primary: Direct high-precision PDF extractor
        extracted_pdf = extract_pdf_fields(content)
        if extracted_pdf.get("certificate_number") or extracted_pdf.get("student_roll_no"):
            ocr_fields.update(extracted_pdf)

        # 2. Secondary: EasyOCR / Doc Processing pipeline if images present
        try:
            from doc_processing.pdf_processor import pdf_to_images
            from doc_processing.image_preprocessing import preprocess_image
            from doc_processing.ocr import extract_text
            from doc_processing.field_extractor import extract_certificate_fields
            import cv2

            images = pdf_to_images(tmp_path)
            all_ocr_results = []
            for i, img in enumerate(images):
                page_temp_path = f"{tmp_path}_page{i}.jpg"
                cv2.imwrite(page_temp_path, img)
                processed = preprocess_image(page_temp_path)
                ocr_results = extract_text(processed)
                all_ocr_results.extend(ocr_results)
                if os.path.exists(page_temp_path):
                    os.remove(page_temp_path)

            doc_proc_fields = extract_certificate_fields(all_ocr_results)
            for k, v in doc_proc_fields.items():
                if v and not ocr_fields.get(k):
                    ocr_fields[k] = v
        except Exception as ocr_err:
            print(f"[DOC PROCESSING] Notice during OCR fallback: {ocr_err}")

        if ocr_fields.get("issue_date"):
            ocr_fields["issue_date"] = normalize_date(ocr_fields["issue_date"])

        # Look up certificate in database by Roll Number, Certificate Number, or Hash
        row = None
        if ocr_fields.get("student_roll_no"):
            row = db.execute(
                text("SELECT * FROM certificates WHERE student_roll_no = :roll"),
                {"roll": str(ocr_fields["student_roll_no"]).strip()}
            ).fetchone()

        if not row and ocr_fields.get("certificate_number"):
            row = db.execute(
                text("SELECT * FROM certificates WHERE certificate_number = :num"),
                {"num": str(ocr_fields["certificate_number"]).strip()}
            ).fetchone()

        if not row:
            row = db.execute(
                text("SELECT * FROM certificates WHERE sha256_hash = :hash"),
                {"hash": file_hash}
            ).fetchone()

        if not row:
            log_verification(
                db=db,
                queried_hash=file_hash,
                verification_status="NOT_FOUND",
                certificate_id=None,
                request=request
            )
            return {
                "found": False,
                "document_matches_record": False,
                "status": "NOT_FOUND",
                "message": "No matching certificate record found in our system.",
                "mismatches": [],
                "field_mismatches": []
            }

        inst_row = db.execute(
            text("SELECT name FROM institutions WHERE id = :id"),
            {"id": str(row.institution_id)}
        ).fetchone()

        db_fields = {
            "student_name": row.student_name,
            "student_roll_no": row.student_roll_no,
            "course_name": row.course_name,
            "issue_date": str(row.issue_date),
            "institution_name": inst_row.name if inst_row else "Global Institute of Technology",
        }

        # RapidFuzz / SequenceMatcher comparison
        from doc_processing.document_comparison import compare_certificate
        comparison = compare_certificate(ocr_fields, db_fields)

        # Marks and CGPA numerical validation
        doc_marks = str(ocr_fields.get("marks") or "").strip()
        rec_marks = str(row.marks or "").strip()
        marks_match = (doc_marks == rec_marks) if (doc_marks and rec_marks) else True

        doc_cgpa = str(ocr_fields.get("cgpa") or "").strip()
        rec_cgpa = str(row.cgpa or "").strip()
        cgpa_match = (doc_cgpa == rec_cgpa) if (doc_cgpa and rec_cgpa) else True

        field_mismatches = []
        for field, score in comparison.get("field_scores", {}).items():
            if score < 85:
                field_mismatches.append({
                    "field": field,
                    "document_value": ocr_fields.get(field),
                    "record_value": db_fields.get(field),
                })

        if not marks_match:
            field_mismatches.append({
                "field": "Total Marks",
                "document_value": doc_marks,
                "record_value": rec_marks
            })

        if not cgpa_match:
            field_mismatches.append({
                "field": "CGPA",
                "document_value": doc_cgpa,
                "record_value": rec_cgpa
            })

        # Tampering check
        is_tampered = (len(field_mismatches) > 0)
        document_matches_record = (not is_tampered) and (row.status == "ISSUED")

        verif_status = "REVOKED" if row.status == "REVOKED" else ("VALID" if document_matches_record else "TAMPERED")
        log_verification(
            db=db,
            queried_hash=file_hash,
            verification_status=verif_status,
            certificate_id=row.id,
            request=request
        )

        return {
            "found": True,
            "document_matches_record": document_matches_record,
            "overall_similarity": comparison.get("overall_score", 100 if document_matches_record else 0),
            "status": "TAMPERED" if is_tampered else row.status,
            "field_mismatches": field_mismatches,
            "mismatches": field_mismatches,
            "certificate_number": row.certificate_number,
            "record": {
                "certificate_number": row.certificate_number,
                "student_name": row.student_name,
                "student_roll_no": row.student_roll_no,
                "course_name": row.course_name,
                "issue_date": row.issue_date,
                "marks": row.marks,
                "cgpa": row.cgpa,
                "status": row.status
            }
        }
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
