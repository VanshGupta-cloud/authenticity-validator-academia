import os
import sys

# Ensure repository root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import urllib.request
import json
import uuid
from datetime import date
from PDF.certificate_generator import Certificate, generate_certificate_pdf

def upload_pdf(filepath):
    boundary = uuid.uuid4().hex
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    
    filename = filepath.replace("\\", "/").split("/")[-1]
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    req = urllib.request.Request(
        "http://127.0.0.1:8000/certificates/verify-document",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print("==================================================================")
print("TEST 1: Uploading ORIGINAL Certificate (CERT-2026-B97DA3E5 - 1000 Marks, CGPA 4)")
print("==================================================================")
cert_orig = Certificate(
    id=uuid.uuid4(),
    certificate_number="CERT-2026-B97DA3E5",
    institution_id=uuid.uuid4(),
    issuer_id=uuid.uuid4(),
    student_name="Arpit",
    student_roll_no="25252525252",
    course_name="Bachelors of Science in Computer Science",
    issue_date=date(2008, 3, 18),
    marks="1000",
    cgpa="4"
)
orig_pdf_path = os.path.join(root_dir, "generated_certificates", "CERT-2026-B97DA3E5.pdf")
generate_certificate_pdf(cert_orig, "CERT-2026-B97DA3E5", orig_pdf_path, "NAME", "http://localhost:8000")

res_orig = upload_pdf(orig_pdf_path)
print("Found:", res_orig["found"])
print("Matches Record:", res_orig["document_matches_record"])
print("Status:", res_orig["status"])
print("Mismatches:", res_orig["mismatches"])

print("\n==================================================================")
print("TEST 2: Uploading EDITED/TAMPERED Certificate (Marks changed to 1025, CGPA changed to 5)")
print("==================================================================")
cert_edited = Certificate(
    id=uuid.uuid4(),
    certificate_number="CERT-2026-B97DA3E5",
    institution_id=uuid.uuid4(),
    issuer_id=uuid.uuid4(),
    student_name="Arpit",
    student_roll_no="25252525252",
    course_name="Bachelors of Science in Computer Science",
    issue_date=date(2008, 3, 18),
    marks="1025",
    cgpa="5"
)
edited_pdf_path = os.path.join(root_dir, "test_tampered_edited.pdf")
generate_certificate_pdf(cert_edited, "CERT-2026-B97DA3E5", edited_pdf_path, "NAME", "http://localhost:8000")

res_edited = upload_pdf(edited_pdf_path)
print("Found:", res_edited["found"])
print("Matches Record:", res_edited["document_matches_record"])
print("Status:", res_edited["status"])
print("Mismatches Detected:", res_edited["mismatches"])
