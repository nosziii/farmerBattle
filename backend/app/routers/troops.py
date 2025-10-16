from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

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


@router.get("/troops/", response_model=List[models.Troop])
def read_troops(db: Session = Depends(get_db)):
    troops = crud.get_troops(db)
    return troops


@router.post("/villages/{village_id}/train")
def train_troops(village_id: int, troops: List[models.VillageTroopCreate], db: Session = Depends(get_db)):
    return crud.train_troops(db=db, village_id=village_id, troops=troops)

@router.get("/villages/{village_id}/training-queue", response_model=List[models.TrainingQueue])
def read_training_queue(village_id: int, db: Session = Depends(get_db)):
    queue = crud.get_training_queue(db, village_id=village_id)
    return queue
