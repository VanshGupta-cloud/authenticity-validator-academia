import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db, engine, Base
from src.routers import auth, institutions, certificate_issue, certificates, certificate_verify
from src.init_demo_data import init_db

# Create tables
Base.metadata.create_all(bind=engine)

# Auto seed demo data if empty
try:
    init_db()
except Exception as e:
    print(f"Notice during init_db: {e}")

app = FastAPI(
    title="Authenticity Validator for Academia (AVFA)",
    description="SIH25029 - Tamper-Proof Academic Document Verification System",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(institutions.router, prefix="/api/v1")
app.include_router(certificate_issue.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")

# Also include un-prefixed routers for direct compatibility with contract
app.include_router(auth.router)
app.include_router(institutions.router)
app.include_router(certificate_issue.router)
app.include_router(certificates.router)

# Directory paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
static_dir = os.path.join(root_dir, "static")
frontend_dir = os.path.join(root_dir, "frontend")
certs_dir = os.path.join(root_dir, "generated_certificates")
os.makedirs(certs_dir, exist_ok=True)

css_dir = os.path.join(frontend_dir, "css") if os.path.exists(os.path.join(frontend_dir, "css")) else os.path.join(static_dir, "css")
js_dir = os.path.join(frontend_dir, "js") if os.path.exists(os.path.join(frontend_dir, "js")) else os.path.join(static_dir, "js")

# Mount static endpoints
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")
app.mount("/generated_certificates", StaticFiles(directory=certs_dir), name="generated_certificates")

if os.path.exists(css_dir):
    app.mount("/css", StaticFiles(directory=css_dir), name="css")
if os.path.exists(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="js")

@app.get("/")
def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(index_path):
        index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"status": "AVFA API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "AVFA API is running", "platform": "SIH25029"}

@app.get("/health/db")
def check_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"database": "Database connected successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")