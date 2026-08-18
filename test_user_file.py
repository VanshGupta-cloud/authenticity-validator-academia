import urllib.request
import json
import uuid
import os

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

path = r"C:\Users\kesar\Downloads\CERT-2026-B97DA3E5_edited.pdf.pdf"
if os.path.exists(path):
    print("Testing User's Exact Uploaded Edited File:")
    res = upload_pdf(path)
    print("Found:", res.get("found"))
    print("Status:", res.get("status"))
    print("Document Matches Record:", res.get("document_matches_record"))
    print("Mismatches:", res.get("mismatches") or res.get("field_mismatches"))
    print("\nFull JSON Response:")
    print(json.dumps(res, indent=2))
else:
    print("File not found at:", path)
