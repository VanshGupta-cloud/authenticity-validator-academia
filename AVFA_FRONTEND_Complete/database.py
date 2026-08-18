"""
Root database compatibility module.
Delegates to src.database for unified connection management & SQLite fallback.
"""
from src.database import engine, SessionLocal, Base, get_db

__all__ = ["engine", "SessionLocal", "Base", "get_db"]
