from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
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

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    public_key = Column(String, nullable=True)
    is_verified = Column(Boolean, nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
    )
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(TIMESTAMP)


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ISSUED', 'REVOKED')",
            name="ck_certificates_status",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    certificate_number = Column(String, unique=True, nullable=False)

    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=False,
    )
    issuer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    batch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch_logs.id"),
        nullable=True,
    )

    student_name = Column(String, nullable=False)
    student_roll_no = Column(String, nullable=False)
    course_name = Column(String, nullable=False)
    issue_date = Column(Date, nullable=False)

    marks = Column(Numeric(10, 2), nullable=True)
    cgpa = Column(Numeric(4, 2), nullable=True)

    sha256_hash = Column(String(64), unique=True, nullable=False)
    digital_signature = Column(Text, nullable=False)
    qr_code_url = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        server_default=text("'ISSUED'"),
    )
    revocation_reason = Column(Text, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    certificate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("certificates.id", ondelete="SET NULL"),
        nullable=True,
    )
    queried_hash = Column(String(64), nullable=False)
    verification_status = Column(String(20), nullable=False)
    verified_by_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
