import requests
import json
import os
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== STARTING FULL 10-PAGE WORKFLOW AUTOMATED VALIDATION ===")
    
    # 1. Page 1: Landing Page
    print("\n1. Page 1 — Landing (Static Serving)...")
    res = requests.get(f"{BASE_URL}/")
    assert res.status_code == 200, f"Failed: {res.status_code}"
    assert "AVFA ACADEMIA" in res.text, "AVFA ACADEMIA brand title not in HTML"
    assert "page-1-landing" in res.text, "page-1-landing view section not found"
    print("   [PASSED] Landing Page (Page 1) served successfully!")

    # 2. Page 3: Register Institution
    print("\n2. Page 3 — Institution Registration (`POST /institutions/register`)...")
    reg_payload = {
        "name": "Indian Institute of Science",
        "official_email": "registrar@iisc.ac.in",
        "address": "Bangalore, Karnataka"
    }
    res = requests.post(f"{BASE_URL}/institutions/register", json=reg_payload)
    assert res.status_code == 200, f"Register failed: {res.status_code} {res.text}"
    data = res.json()
    assert "otp_hint" in data, "otp_hint missing in response"
    print(f"   [PASSED] Registered institution! OTP hint: {data['otp_hint']}")

    # 3. Page 4: Verify OTP
    print("\n3. Page 4 — OTP Verification (`POST /institutions/verify-otp`)...")
    otp_payload = {
        "official_email": "registrar@iisc.ac.in",
        "otp_code": "123456"
    }
    res = requests.post(f"{BASE_URL}/institutions/verify-otp", json=otp_payload)
    assert res.status_code == 200, f"OTP verification failed: {res.status_code} {res.text}"
    print("   [PASSED] OTP verified successfully!")

    # 4. Page 5: Set Password
    print("\n4. Page 5 — Set Password (`POST /institutions/set-password`)...")
    pass_payload = {
        "official_email": "registrar@iisc.ac.in",
        "password": "iiscPass@2026",
        "confirm_password": "iiscPass@2026"
    }
    res = requests.post(f"{BASE_URL}/institutions/set-password", json=pass_payload)
    assert res.status_code == 200, f"Set password failed: {res.status_code} {res.text}"
    print("   [PASSED] Password set successfully!")

    # 5. Page 2: Institution Login
    print("\n5. Page 2 — Institution Login (`POST /institutions/login`)...")
    login_payload = {
        "official_email": "registrar@iisc.ac.in",
        "password": "iiscPass@2026"
    }
    res = requests.post(f"{BASE_URL}/institutions/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.status_code} {res.text}"
    login_data = res.json()
    jwt_token = login_data["access_token"]
    assert jwt_token, "No access token in response"
    print(f"   [PASSED] Login successful! JWT: {jwt_token[:30]}...")

    # 6. Page 6: Dashboard Stats & Recent Certificates
    print("\n6. Page 6 — Dashboard (`GET /certificates/stats` & `GET /certificates`)...")
    res_stats = requests.get(f"{BASE_URL}/certificates/stats")
    assert res_stats.status_code == 200, f"Stats failed: {res_stats.status_code}"
    res_certs = requests.get(f"{BASE_URL}/certificates")
    assert res_certs.status_code == 200, f"Certificates list failed: {res_certs.status_code}"
    print(f"   [PASSED] Dashboard data: {res_stats.json()}")

    # 7. Page 7 & 8: Issue Certificate with Bearer Token
    print("\n7. Page 7 & 8 — Issue Certificate (`POST /certificates/issue`)...")
    issue_payload = {
        "student_name": "Rohan Deshmukh",
        "student_roll_no": "IISc-2026-881",
        "course_name": "Ph.D in Quantum Computing",
        "issue_date": "2026-08-16",
        "marks": "495",
        "cgpa": "9.94"
    }
    headers = {"Authorization": f"Bearer {jwt_token}"}
    res = requests.post(f"{BASE_URL}/certificates/issue", json=issue_payload, headers=headers)
    assert res.status_code == 201, f"Issue failed: {res.status_code} {res.text}"
    cert_issued = res.json()
    cert_num = cert_issued["certificate_number"]
    assert cert_issued["sha256_hash"], "SHA-256 hash missing"
    assert cert_issued["digital_signature"], "Digital signature missing"
    print(f"   [PASSED] Issued Certificate: {cert_num} | Hash: {cert_issued['sha256_hash'][:20]}...")

    # 8. Page 9 & 10 (Tab A): Verify by Certificate Number
    print("\n8. Page 9 & 10 (Tab A) — Verify by ID (`POST /certificates/verify`)...")
    verify_payload = {"certificate_number": cert_num}
    res = requests.post(f"{BASE_URL}/certificates/verify", json=verify_payload)
    assert res.status_code == 200, f"Verify failed: {res.status_code}"
    v_data = res.json()
    assert v_data["found"] is True, "Certificate should be found"
    assert v_data["hash_signature_valid"] is True, "Signature should be valid"
    assert v_data["tamper_detected"] is False, "Should have zero tampering"
    print(f"   [PASSED] Verified Authentic! Student: {v_data['certificate']['student_name']}")

    # 9. Page 9 & 10 (Tab B): Verify by Document Upload
    print("\n9. Page 9 & 10 (Tab B) — Verify Document Upload (`POST /certificates/verify-document`)...")
    # Generate dummy test PDF
    dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Academic Degree) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    files = {'file': ('academic_certificate.pdf', dummy_pdf_content, 'application/pdf')}
    res = requests.post(f"{BASE_URL}/certificates/verify-document", files=files)
    assert res.status_code == 200, f"Verify document failed: {res.status_code}"
    doc_data = res.json()
    assert doc_data["found"] is True, "Document search should succeed"
    print(f"   [PASSED] Document verification returned: found={doc_data['found']}, status={doc_data['status']}")

    print("\n[SUCCESS] ALL 10 PAGES AND WORKFLOWS TESTED & VALIDATED WITH 100% SUCCESS!")

if __name__ == "__main__":
    run_tests()
