import sys
import os
import uuid

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

print("=== STARTING MARKS & PASS/FAIL EVALUATION TESTS ===")

# 1. Register Institution
inst_email = f"eval_dean_{uuid.uuid4().hex[:6]}@apex-university.edu"
r_reg = client.post("/institutions/register", json={
    "name": "Apex University of Science & Technology",
    "official_email": inst_email,
    "address": "Ranchi, Jharkhand"
})
assert r_reg.status_code == 200, f"Register failed: {r_reg.text}"

# 2. Get OTP & Verify
from src.database import SessionLocal
from src import models

db = SessionLocal()
otp_record = db.query(models.OtpVerification).filter(models.OtpVerification.email == inst_email).first()
otp_code = otp_record.otp_code
db.close()

r_otp = client.post("/institutions/verify-otp", json={
    "official_email": inst_email,
    "otp_code": otp_code
})
assert r_otp.status_code == 200, f"OTP verify failed: {r_otp.text}"

# 3. Set Password & Login
client.post("/institutions/set-password", json={
    "official_email": inst_email,
    "password": "Password@123"
})

r_login = client.post("/institutions/login", json={
    "official_email": inst_email,
    "password": "Password@123"
})
assert r_login.status_code == 200
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 4. Test 1: Issue Certificate for PASSED student (460 / 500 = 92.00%)
r_pass = client.post("/certificates/issue", json={
    "student_name": "Rohan Deshmukh",
    "student_roll_no": f"CS-{uuid.uuid4().hex[:6].upper()}",
    "course_name": "Bachelor of Technology in Computer Science",
    "issue_date": "2026-08-16",
    "marks_obtained": 460,
    "total_marks": 500,
    "cgpa": 9.20
}, headers=headers)
assert r_pass.status_code in [200, 201], f"Issue passed cert failed: {r_pass.text}"
pass_data = r_pass.json()
print(f"[PASSED TEST 1] Passed Student Issued: #{pass_data['certificate_number']} | Marks: {pass_data['marks']}/{pass_data['total_marks']} ({pass_data['percentage']}%) | Result: {pass_data['result_status']}")
assert "PASS" in pass_data["result_status"]

# 5. Test 2: Issue Certificate for FAILED student (150 / 500 = 30.00%)
r_fail = client.post("/certificates/issue", json={
    "student_name": "Siddharth Verma",
    "student_roll_no": f"EE-{uuid.uuid4().hex[:6].upper()}",
    "course_name": "Bachelor of Technology in Electrical Engineering",
    "issue_date": "2026-08-16",
    "marks_obtained": 150,
    "total_marks": 500,
    "cgpa": 3.10
}, headers=headers)
assert r_fail.status_code in [200, 201], f"Issue failed cert failed: {r_fail.text}"
fail_data = r_fail.json()
print(f"[PASSED TEST 2] Failed Student Issued: #{fail_data['certificate_number']} | Marks: {fail_data['marks']}/{fail_data['total_marks']} ({fail_data['percentage']}%) | Result: {fail_data['result_status']}")
assert "FAIL" in fail_data["result_status"]

# 6. Test 3: Public Verification of Passed Student
r_ver_pass = client.post("/certificates/verify", json={"certificate_identifier": pass_data["certificate_number"]})
assert r_ver_pass.status_code == 200
ver_pass_body = r_ver_pass.json()
print(f"[PASSED TEST 3] Public Verifier on Passed Student -> Status: {ver_pass_body['certificate']['status']} | Result: {ver_pass_body['certificate']['result_status']}")
assert ver_pass_body["certificate"]["result_status"] == pass_data["result_status"]

# 7. Test 4: Public Verification of Failed Student
r_ver_fail = client.post("/certificates/verify", json={"certificate_identifier": fail_data["certificate_number"]})
assert r_ver_fail.status_code == 200
ver_fail_body = r_ver_fail.json()
print(f"[PASSED TEST 4] Public Verifier on Failed Student -> Status: {ver_fail_body['certificate']['status']} | Result: {ver_fail_body['certificate']['result_status']}")
assert ver_fail_body["certificate"]["result_status"] == fail_data["result_status"]

# 8. Test 5: Verify PDF Generation and PDF Download endpoint
r_pdf = client.get(f"/certificates/download/{pass_data['certificate_number']}")
assert r_pdf.status_code == 200
assert r_pdf.headers["content-type"] == "application/pdf"
print(f"[PASSED TEST 5] Generated Vector PDF Downloaded successfully ({len(r_pdf.content)} bytes)!")

print("\n[SUCCESS] ALL MARKS OBTAINED/TOTAL & PASS/FAIL EVALUATION TESTS PASSED WITH 100% SUCCESS!")
