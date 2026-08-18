import os
import sys

# Ensure repository root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = r"C:\Users\kesar\Antigravity\screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def capture_all():
    print("Starting automated screenshot capture of all 10 pages...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 1920x1080 high-res viewport
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = context.new_page()

        # Helper to take screenshot
        def snap(filename, wait_ms=400):
            time.sleep(wait_ms / 1000.0)
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            page.screenshot(path=filepath, full_page=False)
            print(f"  [SAVED] {filename}")

        # 1. Page 1: Landing
        page.goto("http://127.0.0.1:8000")
        page.evaluate("navigateTo('page-1-landing')")
        snap("01_page_1_landing.png")

        # 2. Page 2: Institution Login
        page.evaluate("navigateTo('page-2-login')")
        snap("02_page_2_institution_login.png")

        # 3. Page 3: Institution Registration
        page.evaluate("navigateTo('page-3-register')")
        snap("03_page_3_institution_registration.png")

        # 4. Page 4: OTP Verification
        page.evaluate("navigateTo('page-4-otp')")
        snap("04_page_4_otp_verification.png")

        # 5. Page 5: Set Password
        page.evaluate("navigateTo('page-5-password')")
        snap("05_page_5_set_password.png")

        # 6. Page 6: Dashboard (post-login)
        # First log in via JS to populate dashboard state
        page.evaluate("""
            state.token = 'demo_jwt_token_2026';
            state.institution = { name: 'Global Institute of Technology', id: 'inst-123', email: 'issuer@git.edu' };
            localStorage.setItem('avfa_jwt', state.token);
            localStorage.setItem('avfa_institution', JSON.stringify(state.institution));
            updateNavState();
            navigateTo('page-6-dashboard');
        """)
        snap("06_page_6_dashboard.png", wait_ms=600)

        # 7. Page 7: Issue New Certificate
        page.evaluate("navigateTo('page-7-issue')")
        snap("07_page_7_issue_new_certificate.png")

        # 8. Page 8: Certificate Issued Confirmation
        page.evaluate("""
            document.getElementById('issued-cert-num').textContent = 'CERT-2026-88F4A19C';
            document.getElementById('issued-cert-hash').textContent = '0x8f3c7a9b12e405d6718a234f90bc5e81d723fa90841cd67ef21a09847123bc45';
            document.getElementById('issued-cert-sig').textContent = 'MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7rF1q3N4V8...';
            document.getElementById('issued-cert-status').innerHTML = '<span class="status-pill valid">ISSUED</span>';
            navigateTo('page-8-issued');
        """)
        snap("08_page_8_certificate_issued_confirmation.png")

        # 9. Page 9 Tab A: Verify by Certificate Number
        page.evaluate("""
            navigateTo('page-9-verify');
            switchVerifyTab('A');
        """)
        snap("09_page_9_verify_tab_a_number.png")

        # 10. Page 9 Tab B: Verify by Document Upload
        page.evaluate("switchVerifyTab('B')")
        snap("10_page_9_verify_tab_b_document.png")

        # 11. Page 10: Verification Result Tab A (Authentic)
        page.evaluate("""
            renderVerificationResultTabA({
                found: true,
                hash_signature_valid: true,
                tamper_detected: false,
                status: 'ISSUED',
                certificate: {
                    certificate_number: 'AVFA-GIT-2024-001',
                    student_name: 'Elena R. Vance',
                    student_roll_no: 'CS-2024-001',
                    course_name: 'Master of Science in Computer Science',
                    issue_date: '2024-10-24',
                    marks: '485',
                    cgpa: '9.82',
                    sha256_hash: '0x7a34f89b2c8e19a4d0f872b1cd12c9e4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0',
                    status: 'ISSUED'
                }
            }, 'AVFA-GIT-2024-001');
            navigateTo('page-10-result');
        """)
        snap("11_page_10_result_tab_a_authentic.png")

        # 12. Page 10: Verification Result Tab B (Document Mismatch Breakdown)
        page.evaluate("""
            renderVerificationResultTabB({
                found: true,
                document_matches_record: false,
                status: 'TAMPERED',
                certificate_number: 'CERT-2024-0091',
                mismatches: [
                    { field: 'Total Marks', document_value: '495', record_value: '485' },
                    { field: 'CGPA', document_value: '9.90', record_value: '7.80' }
                ],
                record: {
                    certificate_number: 'CERT-2024-0091',
                    student_name: 'Jane Doe',
                    student_roll_no: 'CS-2024-091',
                    course_name: 'Bachelor of Technology in CS',
                    issue_date: '2024-05-15'
                }
            });
            navigateTo('page-10-result');
        """)
        snap("12_page_10_result_tab_b_mismatch_breakdown.png")

        browser.close()
    print(f"\n[SUCCESS] All screenshots saved to: {SCREENSHOTS_DIR}")

if __name__ == "__main__":
    capture_all()
