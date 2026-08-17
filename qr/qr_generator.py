"""
QR Code Generator & File Hash Utility for AVFA
"""

import hashlib
from pathlib import Path
import qrcode


def generate_qr_code(
    certificate_number: str,
    verification_base_url: str,
    output_path: str
) -> str:
    """
    Generate a QR code image for a certificate pointing to the verification endpoint.

    Parameters:
    - certificate_number: The unique certificate number (e.g. CERT-2026-BD6AD0A8)
    - verification_base_url: Base URL (e.g. http://localhost:8000/verify)
    - output_path: File path to save the generated PNG image

    Returns:
    - Path to the saved QR image
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build verification target URL
    if "?" in verification_base_url:
        qr_data = f"{verification_base_url}&cert_id={certificate_number}"
    elif verification_base_url.endswith("/"):
        qr_data = f"{verification_base_url}?cert_id={certificate_number}"
    else:
        qr_data = f"{verification_base_url}?cert_id={certificate_number}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(str(path))

    return str(path)


def calculate_hash(file_path: str) -> str:
    """Calculate and return the SHA-256 hash of a file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    sha256 = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()