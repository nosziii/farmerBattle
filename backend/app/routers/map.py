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


@router.get("/map/", response_model=list[models.VillageResponse])
def read_map(db: Session = Depends(get_db)):
    map_data = crud.get_villages(db)
    return map_data
