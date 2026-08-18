from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=True)
    official_email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)
    public_key = Column(Text, nullable=True)
    private_key = Column(Text, nullable=True)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_email_verified = Column(Boolean, nullable=False, server_default=text("false"))
    is_verified = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, server_default=text("'ISSUER'"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    certificate_number = Column(String, unique=True, nullable=False)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False)
    issuer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    batch_id = Column(UUID(as_uuid=True), nullable=True)

    student_name = Column(String, nullable=False)
    student_roll_no = Column(String, nullable=False)
    course_name = Column(String, nullable=False)
    issue_date = Column(String, nullable=False)

    marks = Column(Numeric(10, 2), nullable=True)
    cgpa = Column(Numeric(4, 2), nullable=True)

    sha256_hash = Column(String(64), unique=True, nullable=False)
    digital_signature = Column(Text, nullable=False)
    qr_code_url = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, server_default=text("'ISSUED'"))
    revocation_reason = Column(Text, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id", ondelete="SET NULL"), nullable=True)
    queried_hash = Column(String(64), nullable=False)
    verification_status = Column(String(20), nullable=False)
    verified_by_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))