from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, text, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base
from sqlalchemy import Numeric


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
        server_default=text("gen_random_uuid()")
    )
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id")
    )
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(TIMESTAMP)

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    certificate_number = Column(String, unique=True, nullable=False)
    student_name = Column(String, nullable=False)
    student_roll_no = Column(String, nullable=False)
    course_name = Column(String, nullable=False)
    issue_date = Column(String, nullable=False)
    marks = Column(String, nullable=True)
    cgpa = Column(String, nullable=True)
    sha256_hash = Column(String, nullable=False)
    digital_signature = Column(Text, nullable=False)
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=False
    )
    issuer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    qr_code_url = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    status = Column(String, server_default="ISSUED")
    revocation_reason = Column(String, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))