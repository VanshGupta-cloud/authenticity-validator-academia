from sqlalchemy.orm import Session
from src.models import VerificationLog


# Allowed values for verification_status, matching the DB CHECK constraint:
# CHECK (verification_status IN ('VALID', 'TAMPERED', 'REVOKED', 'NOT_FOUND'))
VALID_STATUSES = {"VALID", "TAMPERED", "REVOKED", "NOT_FOUND"}


def log_verification(
    db: Session,
    queried_hash: str,
    verification_status: str,
    certificate_id=None,
    request=None,
) -> VerificationLog:
    """
    Insert a row into verification_logs.

    Args:
        db: active SQLAlchemy session
        queried_hash: the sha256_hash that was submitted for verification
        verification_status: one of VALID, TAMPERED, REVOKED, NOT_FOUND
        certificate_id: UUID of the matched certificate, or None if not found
        request: FastAPI Request object (optional) - used to capture IP + user agent

    Returns:
        The created VerificationLog row.
    """
    if verification_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid verification_status '{verification_status}'. "
            f"Must be one of {sorted(VALID_STATUSES)}"
        )

    log_entry = VerificationLog(
        certificate_id=certificate_id,
        queried_hash=queried_hash,
        verification_status=verification_status,
        verified_by_ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry