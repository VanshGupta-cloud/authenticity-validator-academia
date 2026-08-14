from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from src.database import get_db
from src import models, schemas

router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"]
)

# 1. CREATE Certificate
@router.post("/", response_model=schemas.CertificateResponse, status_code=status.HTTP_201_CREATED)
def create_certificate(
    cert_data: schemas.CertificateCreate, 
    db: Session = Depends(get_db)
):
    existing_cert = db.query(models.Certificate).filter(
        models.Certificate.certificate_number == cert_data.certificate_number
    ).first()
    
    if existing_cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate with this certificate_number already exists."
        )

    db_cert = models.Certificate(**cert_data.model_dump())
    db.add(db_cert)
    db.commit()
    db.refresh(db_cert)
    return db_cert


# 2. READ All Certificates (with pagination)
@router.get("/", response_model=List[schemas.CertificateResponse])
def get_all_certificates(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    certificates = db.query(models.Certificate).offset(skip).limit(limit).all()
    return certificates


# 3. READ Single Certificate by ID
@router.get("/{cert_id}", response_model=schemas.CertificateResponse)
def get_certificate_by_id(cert_id: UUID, db: Session = Depends(get_db)):
    cert = db.query(models.Certificate).filter(models.Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Certificate with ID {cert_id} not found."
        )
    return cert


# 4. UPDATE Certificate (e.g., Revoke/Change Status)
@router.patch("/{cert_id}", response_model=schemas.CertificateResponse)
def update_certificate(
    cert_id: UUID, 
    cert_update: schemas.CertificateUpdate, 
    db: Session = Depends(get_db)
):
    cert = db.query(models.Certificate).filter(models.Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Certificate with ID {cert_id} not found."
        )

    update_data = cert_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cert, key, value)

    db.commit()
    db.refresh(cert)
    return cert


# 5. DELETE Certificate
@router.delete("/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(cert_id: UUID, db: Session = Depends(get_db)):
    cert = db.query(models.Certificate).filter(models.Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Certificate with ID {cert_id} not found."
        )

    db.delete(cert)
    db.commit()
    return None