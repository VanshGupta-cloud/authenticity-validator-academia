from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, text, Boolean
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