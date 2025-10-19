import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas
from ..database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _attach_admin_flag(user: schemas.User) -> None:
    admin_username = os.getenv("ADMIN_USER", crud.DEFAULT_USER_USERNAME)
    setattr(user, "is_admin", user.username == admin_username)


@router.post("/auth/register", response_model=models.AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: models.RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if not username or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password are required")

    existing = crud.get_user_by_username(db, username)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user = crud.create_user(db, models.UserCreate(username=username, password=payload.password))

    # Give every new player a starter village.
    village_name = f"{username}'s Village"
    crud.create_village(db, models.VillageCreate(name=village_name, user_id=user.id))

    token = auth.create_access_token(user.id)
    _attach_admin_flag(user)

    return models.AuthResponse(access_token=token, user=user)


@router.post("/auth/login", response_model=models.AuthResponse)
def login(payload: models.LoginRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if not username or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password are required")

    user = crud.authenticate_user(db, username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = auth.create_access_token(user.id)
    _attach_admin_flag(user)
    return models.AuthResponse(access_token=token, user=user)


@router.get("/auth/me", response_model=models.User)
def read_me(current_user: schemas.User = Depends(auth.get_current_user)):
    _attach_admin_flag(current_user)
    return current_user
