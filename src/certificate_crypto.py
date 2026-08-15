import hashlib
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def build_canonical_payload(student_name, student_roll_no, degree_name, issue_date, institution_id, marks=None, cgpa=None):
    def normalize_number(val):
        if val is None:
            return None
        return f"{float(val):.2f}"

    payload = {
        "student_name": student_name,
        "student_roll_no": student_roll_no,
        "degree_name": degree_name,
        "issue_date": str(issue_date),
        "institution_id": str(institution_id),
        "marks": normalize_number(marks),
        "cgpa": normalize_number(cgpa),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def hash_certificate(payload_str: str) -> str:
    return hashlib.sha256(payload_str.encode()).hexdigest()


def sign_hash(hash_hex: str, private_key_path: str) -> str:
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    signature = private_key.sign(
        hash_hex.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode()


def verify_signature(
    hash_hex: str,
    signature_b64: str,
    public_key_pem: str
) -> bool:
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode()
    )

    signature = base64.b64decode(signature_b64)

    try:
        public_key.verify(
            signature,
            hash_hex.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return True

    except Exception:
        return False


def sign_hash_from_pem(hash_hex: str, private_key_pem: str) -> str:
    private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    signature = private_key.sign(
        hash_hex.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()