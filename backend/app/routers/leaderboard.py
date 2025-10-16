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


@router.get("/leaderboard/", response_model=list[models.VillageResponse])
def read_leaderboard(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    leaderboard = crud.get_leaderboard(db, skip=skip, limit=limit)
    return leaderboard
