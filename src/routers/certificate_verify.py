from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db
from src.schemas import CertificateVerifyRequest, CertificateVerifyResponse
from src.certificate_crypto import build_canonical_payload, hash_certificate, verify_signature
from src.log_service import log_verification
import shutil
import tempfile
import os
import cv2
from datetime import datetime

router = APIRouter(prefix="/certificates", tags=["certificate-verification"])


def normalize_date(date_str):
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return date_str


@router.post("/verify", response_model=CertificateVerifyResponse)
def verify_certificate(payload: CertificateVerifyRequest, request: Request, db: Session = Depends(get_db)):
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

    inst_row = db.execute(
        text("SELECT public_key FROM institutions WHERE id = :id"),
        {"id": str(row.institution_id)}
    ).fetchone()

    if not inst_row or not inst_row.public_key:
        raise HTTPException(status_code=500, detail="Institution public key not found")

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
    signature_valid = verify_signature(row.sha256_hash, row.digital_signature, inst_row.public_key)

    hash_signature_valid = hash_match and signature_valid
    tamper_detected = not hash_match

    log_verification(
        db=db,
        queried_hash=recomputed_hash,
        verification_status="VALID" if hash_signature_valid else "TAMPERED",
        certificate_id=row.id,
        request=request,
    )

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


@router.post("/verify-document")
async def verify_certificate_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        from doc_processing.pdf_processor import pdf_to_images
        from doc_processing.image_preprocessing import preprocess_image
        from doc_processing.ocr import extract_text
        from doc_processing.field_extractor import extract_certificate_fields
        from doc_processing.document_comparison import compare_certificate

        images = pdf_to_images(tmp_path)
        all_ocr_results = []
        for i, img in enumerate(images):
            page_temp_path = f"{tmp_path}_page{i}.jpg"
            cv2.imwrite(page_temp_path, img)
            processed = preprocess_image(page_temp_path)
            ocr_results = extract_text(processed)
            all_ocr_results.extend(ocr_results)
            os.remove(page_temp_path)

        ocr_fields = extract_certificate_fields(all_ocr_results)

        if ocr_fields.get("issue_date"):
            ocr_fields["issue_date"] = normalize_date(ocr_fields["issue_date"])

        row = db.execute(
            text("SELECT * FROM certificates WHERE student_roll_no = :roll"),
            {"roll": ocr_fields.get("student_roll_no")}
        ).fetchone()

        if not row:
            return {"found": False, "message": "No matching certificate record found in our system."}

        inst_row = db.execute(
            text("SELECT name FROM institutions WHERE id = :id"),
            {"id": str(row.institution_id)}
        ).fetchone()

        db_fields = {
            "student_name": row.student_name,
            "student_roll_no": row.student_roll_no,
            "course_name": row.course_name,
            "issue_date": str(row.issue_date),
            "institution_name": inst_row.name if inst_row else "",
        }

        comparison = compare_certificate(ocr_fields, db_fields)

        marks_match = str(ocr_fields.get("marks", "")).strip() == str(row.marks).strip()
        cgpa_match = str(ocr_fields.get("cgpa", "")).strip() == str(row.cgpa).strip()

        field_mismatches = []
        for field, score in comparison["field_scores"].items():
            if score < 85:
                field_mismatches.append({
                    "field": field,
                    "document_value": ocr_fields.get(field),
                    "record_value": db_fields.get(field),
                })
        if not marks_match:
            field_mismatches.append({"field": "marks", "document_value": ocr_fields.get("marks"), "record_value": str(row.marks)})
        if not cgpa_match:
            field_mismatches.append({"field": "cgpa", "document_value": ocr_fields.get("cgpa"), "record_value": str(row.cgpa)})

        document_matches_record = (
            comparison["overall_score"] >= 85
            and comparison["matched_fields"] == comparison["total_fields"]
            and marks_match
            and cgpa_match
        )

        return {
            "found": True,
            "document_matches_record": document_matches_record,
            "overall_similarity": comparison["overall_score"],
            "field_mismatches": field_mismatches,
            "certificate_number": row.certificate_number,
            "status": row.status,
        }
    finally:
        os.unlink(tmp_path)