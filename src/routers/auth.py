from fastapi import APIRouter, HTTPException
from uuid import uuid4
from src.schemas import RegisterRequest, UserResponse, LoginRequest, LoginResponse
from src.security import hash_password, verify_password, create_access_token
from src.database import fake_users_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest):
    if payload.email in fake_users_db:
        raise HTTPException(status_code=409, detail="Email already exists")

    user_id = uuid4()
    fake_users_db[payload.email] = {
        "id": user_id,
        "full_name": payload.full_name,
        "email": payload.email,
        "role": payload.role,
        "institution_id": payload.institution_id,
        "password_hash": hash_password(payload.password),
    }
    return fake_users_db[payload.email]

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = fake_users_db.get(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }