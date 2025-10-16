from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/users/", response_model=models.User)
def create_user(user: models.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)
