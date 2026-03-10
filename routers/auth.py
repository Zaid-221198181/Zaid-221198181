import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import RegisterRequest, LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if request.role not in ("buyer", "seller"):
        raise HTTPException(status_code=400, detail="Role must be 'buyer' or 'seller'")

    existing = db.query(User).filter(User.name == request.name, User.role == request.role).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        name=request.name,
        password_hash=hash_password(request.password),
        role=request.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == request.name).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.password_hash != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Wrong password")

    return user
