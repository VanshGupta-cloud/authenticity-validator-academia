from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from src.schemas import RegisterRequest, UserResponse, LoginRequest, LoginResponse
from src.security import hash_password, verify_password, create_access_token
from src.database import get_db
from src.models import User, Institution

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    inst_id = payload.institution_id
    if not inst_id and payload.role in ["ISSUER", "ADMIN"]:
        # Assign to default institution if available
        inst = db.query(Institution).first()
        if inst:
            inst_id = inst.id

    new_user = User(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        full_name=payload.full_name.strip(),
        email=payload.email.lower().strip(),
        role=payload.role.upper(),
        password_hash=hash_password(payload.password),
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Registration error: {str(e)}")

    return new_user


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "sub": str(user.id),
        "institution_id": str(user.institution_id) if user.institution_id else "",
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }