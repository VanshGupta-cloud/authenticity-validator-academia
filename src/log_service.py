from sqlalchemy.orm import Session
from src.models import VerificationLog

# Allowed values for verification_status:
VALID_STATUSES = {"VALID", "TAMPERED", "REVOKED", "NOT_FOUND"}

def log_verification(
    db: Session,
    queried_hash: str,
    verification_status: str,
    certificate_id=None,
    request=None,
) -> VerificationLog:
    if verification_status not in VALID_STATUSES:
        verification_status = "TAMPERED"

    log_entry = VerificationLog(
        certificate_id=certificate_id,
        queried_hash=queried_hash or "UNKNOWN",
        verification_status=verification_status,
        verified_by_ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
