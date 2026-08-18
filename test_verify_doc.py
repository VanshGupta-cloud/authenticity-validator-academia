import urllib.request
import json
import uuid
import tempfile
from reportlab.pdfgen import canvas

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

print("--- Test 1: Real Valid Certificate ---")
res1 = upload_pdf("generated_certificates/CERT-2026-BFB6E7E4.pdf")
print("Found:", res1["found"], "| Matches Record:", res1["document_matches_record"], "| Status:", res1["status"])

print("\n--- Test 2: Unregistered / Fake PDF Document ---")
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    c = canvas.Canvas(tmp.name)
    c.drawString(100, 750, "Random Unregistered PDF Document")
    c.drawString(100, 700, "Certificate Number: CERT-9999-FAKE9999")
    c.save()
    fake_path = tmp.name

res2 = upload_pdf(fake_path)
print("Found:", res2["found"], "| Matches Record:", res2["document_matches_record"], "| Status:", res2["status"], "| Message:", res2.get("message"))

print("\n--- Test 3: Tampered Certificate (Name Altered in PDF) ---")
with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    c = canvas.Canvas(tmp.name)
    c.drawString(100, 750, "Certificate Number: CERT-2026-BFB6E7E4")
    c.drawString(100, 700, "This is to certify that")
    c.drawString(100, 680, "FAKE TAMPERED STUDENT")
    c.drawString(100, 650, "Roll Number: CS-2026-099")
    c.drawString(100, 600, "Marks\n500")
    c.drawString(100, 550, "CGPA\n10.0")
    c.save()
    tampered_path = tmp.name

res3 = upload_pdf(tampered_path)
print("Found:", res3["found"], "| Matches Record:", res3["document_matches_record"], "| Status:", res3["status"])
print("Mismatches detected:", res3["mismatches"])
