import os
import sys

# Ensure repository root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import urllib.request
import json

payloads = [
    {"certificate_number": "http://localhost:8000/verify?cert_id=CERT-2026-B97DA3E5"},
    {"certificate_number": "CERT-2026-B97DA3E5"},
    {"certificate_number": "http://127.0.0.1:8000/?verify=CERT-2026-B97DA3E5"},
    {"certificate_number": "https://avfa.gov.in/verify?certificate_number=CERT-2026-B97DA3E5"}
]

for p in payloads:
    req = urllib.request.Request(
        "http://127.0.0.1:8000/certificates/verify",
        data=json.dumps(p).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        cert_no = data.get("certificate_number") or (data.get("certificate") or {}).get("certificate_number")
        print(f"Query: {p['certificate_number']}\n  -> Found: {data.get('found')} | Status: {data.get('status')} | Cert: {cert_no}\n")
