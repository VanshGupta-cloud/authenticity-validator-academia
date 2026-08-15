from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db
from src.routers import auth, institutions, certificate_issue, certificates

app = FastAPI(title="Authenticity Validator for Academia")

# Register all routers so FastAPI exposes their endpoints
app.include_router(auth.router)
app.include_router(institutions.router)
app.include_router(certificate_issue.router)
app.include_router(certificates.router)

@app.get("/")
def root():
    return {"status": "AVFA API is running"}

@app.get("/health/db")
def check_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"database": "Supabase PostgreSQL connected successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")