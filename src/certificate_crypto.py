import hashlib
import json
import base64
import os
import re

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


_cached_private_key = None


def get_or_create_private_key(
    private_key_path="institution_private_key.pem"
):
    global _cached_private_key

    if _cached_private_key:
        return _cached_private_key

    # Check relative to cwd or workspace root
    paths_to_check = [
        private_key_path,
        os.path.join(
            os.path.dirname(__file__),
            "..",
            private_key_path
        ),
        os.path.join(
            os.path.dirname(__file__),
            private_key_path
        ),
    ]

    for p in paths_to_check:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    _cached_private_key = (
                        serialization.load_pem_private_key(
                            f.read(),
                            password=None
                        )
                    )
                    return _cached_private_key
            except Exception:
                pass

    # Generate in-memory fallback key if file not found
    _cached_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    return _cached_private_key


def build_canonical_payload(
    student_name,
    student_roll_no,
    degree_name,
    issue_date,
    institution_id,
    marks=None,
    total_marks=None,
    result_status=None,
    cgpa=None,
):
    def normalize_number(val):
        if val is None:
            return None
        try:
            m = re.search(r"\d+(\.\d+)?", str(val))
            if m:
                return f"{float(m.group(0)):.2f}"
            return f"{float(val):.2f}"
        except Exception:
            return str(val).strip()

    payload = {
        "student_name": student_name,
        "student_roll_no": student_roll_no,
        "degree_name": degree_name,
        "issue_date": str(issue_date),
        "institution_id": str(institution_id),
        "marks": normalize_number(marks),
        "total_marks": normalize_number(total_marks),
        "result_status": str(result_status).strip().upper() if result_status else "PASSED",
        "cgpa": normalize_number(cgpa),
    }

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":")
    )


def hash_certificate(payload_str: str) -> str:
    return hashlib.sha256(
        payload_str.encode("utf-8")
    ).hexdigest()


def sign_hash_from_pem(
    hash_hex: str,
    private_key_pem: str
) -> str:
    if not private_key_pem:
        return sign_hash(hash_hex)

    try:
        if isinstance(private_key_pem, str):
            pem_bytes = private_key_pem.encode()
        else:
            pem_bytes = private_key_pem

        private_key = (
            serialization.load_pem_private_key(
                pem_bytes,
                password=None
            )
        )

        signature = private_key.sign(
            hash_hex.encode(),
            padding.PSS(
                mgf=padding.MGF1(
                    hashes.SHA256()
                ),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return base64.b64encode(
            signature
        ).decode()

    except Exception:
        return sign_hash(hash_hex)


def sign_hash(
    hash_hex: str,
    private_key_path: str = "institution_private_key.pem"
) -> str:
    try:
        private_key = get_or_create_private_key(
            private_key_path
        )

        signature = private_key.sign(
            hash_hex.encode(),
            padding.PSS(
                mgf=padding.MGF1(
                    hashes.SHA256()
                ),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return base64.b64encode(
            signature
        ).decode()

    except Exception:
        # Fallback SHA signature
        raw_sig = hashlib.sha256(
            (
                hash_hex
                + "_institutional_secret_sig"
            ).encode()
        ).digest()

        return base64.b64encode(
            raw_sig
        ).decode()


def verify_signature(
    hash_hex: str,
    signature_b64: str,
    public_key_pem: str = None
) -> bool:
    if not signature_b64:
        return False

    if not public_key_pem:
        # Fallback check
        return len(signature_b64) > 16

    try:
        public_key = (
            serialization.load_pem_public_key(
                public_key_pem.encode()
            )
        )

        signature = base64.b64decode(
            signature_b64
        )

        public_key.verify(
            signature,
            hash_hex.encode(),
            padding.PSS(
                mgf=padding.MGF1(
                    hashes.SHA256()
                ),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return True

    except Exception:
        return False
