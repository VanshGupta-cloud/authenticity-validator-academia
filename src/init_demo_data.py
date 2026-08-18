"""
Database schema initialization module.
Creates required tables without seeding hardcoded demo accounts.
"""
from src.database import Base, engine


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
