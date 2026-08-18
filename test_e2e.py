import urllib.request
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def request_json(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if resp.headers.get_content_type() == "application/json" else content
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, content

def run_tests():
    print("=== STARTING COMPREHENSIVE END-TO-END VERIFICATION TESTS ===")

    # 1. Health and Index HTML
    print("\n1. Testing Frontend Static Serving (`GET /`)...")
    status, content = request_json("/")
    assert status == 200, f"Expected 200, got {status}"
    assert "Authenticity Validator" in content, "Frontend title not found in HTML"
    print("   [PASSED] Frontend HTML served successfully!")

    # 2. Issuer Login
    print("\n2. Testing Issuer Login (`POST /auth/login`)...")
    status, login_res = request_json("/auth/login", method="POST", data={
        "email": "issuer@git.edu",
        "password": "issuer123"
    })
    assert status == 200, f"Expected 200, got {status}: {login_res}"
    token = login_res["access_token"]
    print(f"   [PASSED] Issuer logged in! Token: {token[:20]}...")

    # 3. Student Login
    print("\n3. Testing Student Login (`POST /auth/login`)...")
    status, student_res = request_json("/auth/login", method="POST", data={
        "email": "student@git.edu",
        "password": "student123"
    })
    assert status == 200, f"Expected 200, got {status}: {student_res}"
    print(f"   [PASSED] Student logged in! Name: {student_res['user']['full_name']}")

    # 4. Certificate Stats
    print("\n4. Testing Certificate Stats (`GET /certificates/stats`)...")
    status, stats = request_json("/certificates/stats")
    assert status == 200, f"Expected 200, got {status}: {stats}"
    print(f"   [PASSED] Stats: {stats}")

    # 5. List Certificates
    print("\n5. Testing List Certificates (`GET /certificates`)...")
    status, certs = request_json("/certificates")
    assert status == 200, f"Expected 200, got {status}: {certs}"
    assert len(certs) > 0, "Expected seeded certificates"
    print(f"   [PASSED] Retrieved {len(certs)} certificates.")

    # 6. Public Verification - Valid Cert
    print("\n6. Testing Verification on Valid Cert (`POST /certificates/verify`)...")
    valid_cert = next(c for c in certs if c["status"] == "ISSUED")
    status, verify_res = request_json("/certificates/verify", method="POST", data={
        "queried_hash": valid_cert["sha256_hash"]
    })
    assert status == 200, f"Expected 200, got {status}: {verify_res}"
    assert verify_res["verification_status"] == "VALID", f"Expected VALID, got {verify_res['verification_status']}"
    assert verify_res["checks"]["signature_valid"] is True
    print(f"   [PASSED] Status: {verify_res['verification_status']} | Message: {verify_res['message']}")

    # 7. Public Verification - Revoked Cert (CERT-2024-0034)
    print("\n7. Testing Verification on Revoked Cert (`POST /certificates/verify`)...")
    status, rev_verify = request_json("/certificates/verify", method="POST", data={
        "certificate_number": "CERT-2024-0034"
    })
    assert status == 200, f"Expected 200, got {status}: {rev_verify}"
    assert rev_verify["verification_status"] == "REVOKED", f"Expected REVOKED, got {rev_verify['verification_status']}"
    print(f"   [PASSED] Status: {rev_verify['verification_status']} | Reason: {rev_verify['certificate']['revocation_reason']}")

    # 8. Public Verification - Tampered/Forged Hash
    print("\n8. Testing Verification on Forged Hash (`POST /certificates/verify`)...")
    status, forged_res = request_json("/certificates/verify", method="POST", data={
        "queried_hash": "forged_nonexistent_hash_00000000000000000000000000"
    })
    assert status == 200, f"Expected 200, got {status}: {forged_res}"
    assert forged_res["verification_status"] == "NOT_FOUND", f"Expected NOT_FOUND, got {forged_res['verification_status']}"
    print(f"   [PASSED] Tampered/Not Found check: {forged_res['verification_status']}")

    # 9. OCR RapidFuzz Field Extraction Comparison
    print("\n9. Testing OCR Field Extractor & RapidFuzz (`POST /certificates/ocr-compare`)...")
    status, ocr_res = request_json("/certificates/ocr-compare", method="POST", data={
        "certificate_number": "AVFA-GIT-2024-001",
        "extracted_fields": {
            "student_name": "Elena R. Vance",
            "student_roll_no": "CS-2024-001",
            "degree_name": "Master of Science in Computer Science",
            "issue_date": "2024-10-24",
            "institution": "Global Institute of Technology"
        }
    })
    assert status == 200, f"Expected 200, got {status}: {ocr_res}"
    assert ocr_res["overall_similarity"] >= 85.0
    assert ocr_res["status"] == "VERIFIED"
    print(f"   [PASSED] OCR RapidFuzz similarity: {ocr_res['overall_similarity']}% | Status: {ocr_res['status']}")

    # 10. Batch / Bulk CSV Certificate Issuance
    print("\n10. Testing Batch CSV Certificate Issuance (`POST /certificates/batch-issue`)...")
    status, batch_res = request_json("/certificates/batch-issue", method="POST", data=[
        {"student_name": "Liam O'Connor", "student_roll_no": "CS-2026-101", "course_name": "B.Tech in AI", "issue_date": "2026-08-16"},
        {"student_name": "Aria Montgomery", "student_roll_no": "CS-2026-102", "course_name": "B.Tech in CS", "issue_date": "2026-08-16"}
    ], token=token)
    assert status == 200, f"Expected 200, got {status}: {batch_res}"
    assert batch_res["total_records"] == 2
    print(f"   [PASSED] Batch issued {batch_res['total_records']} certificates!")

    # 11. Blockchain Ledger Explorer
    print("\n11. Testing Blockchain Ledger Explorer (`GET /certificates/blockchain-ledger`)...")
    status, ledger_res = request_json("/certificates/blockchain-ledger")
    assert status == 200, f"Expected 200, got {status}: {ledger_res}"
    assert len(ledger_res["blocks"]) > 0
    print(f"   [PASSED] Blockchain Ledger retrieved: {len(ledger_res['blocks'])} blocks, consensus {ledger_res['network_status']}")

    # 12. Issue Single Certificate & Revoke
    print("\n12. Testing Issue Single & Instant Revoke...")
    import uuid
    s_uid = uuid.uuid4().hex[:6].upper()
    status, new_cert = request_json("/certificates/issue", method="POST", data={
        "student_name": f"Alexander Hayes {s_uid}",
        "student_roll_no": f"CS-2026-{s_uid}",
        "course_name": "Master of Science in Cybersecurity",
        "issue_date": "2026-08-16",
        "cgpa": "9.95 / 10.0"
    }, token=token)
    assert status == 201
    
    status, revoke_res = request_json(f"/certificates/{new_cert['id']}/revoke", method="PATCH", data={
        "revocation_reason": "Clerical audit request"
    }, token=token)
    assert status == 200
    assert revoke_res["status"] == "REVOKED"
    print(f"   [PASSED] Single issue & revoke verified!")

    print("\n[SUCCESS] ALL 12 REPOSITORY CAPABILITY TESTS PASSED WITH 100% SUCCESS!\n")

if __name__ == "__main__":
    run_tests()
