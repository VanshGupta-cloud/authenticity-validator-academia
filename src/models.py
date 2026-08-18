import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text
from src.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, default="GIT")
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)
    public_key = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="STUDENT")  # ADMIN, ISSUER, VERIFIER, STUDENT
    created_at = Column(DateTime, default=datetime.utcnow)


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    certificate_number = Column(String(100), unique=True, nullable=False)
    student_name = Column(String(255), nullable=False)
    student_roll_no = Column(String(100), nullable=False)
    course_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    marks = Column(String(50), nullable=True)
    cgpa = Column(String(50), nullable=True)
    sha256_hash = Column(String(64), nullable=False, index=True)
    digital_signature = Column(Text, nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=True)
    issuer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    batch_id = Column(String(36), nullable=True)
    qr_code_url = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)
    status = Column(String(20), default="ISSUED")  # ISSUED, REVOKED
    revocation_reason = Column(String(255), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    certificate_id = Column(String(36), ForeignKey("certificates.id", ondelete="SET NULL"), nullable=True)
    queried_hash = Column(String(64), nullable=False)
    verification_status = Column(String(20), nullable=False)  # VALID, TAMPERED, REVOKED, NOT_FOUND
    verified_by_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OtpVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(10), nullable=False)
    institution_name = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)