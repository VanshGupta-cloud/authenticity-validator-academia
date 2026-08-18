"""
Compatibility alias module for certificate verification router.
Consolidates endpoints with src.routers.certificates for single source of truth.
"""
from src.routers.certificates import router, verify_certificate, verify_document, extract_pdf_fields

__all__ = ["router", "verify_certificate", "verify_document", "extract_pdf_fields"]
