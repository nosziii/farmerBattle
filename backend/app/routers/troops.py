from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import auth, crud, models, schemas
from ..database import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_village_ownership(db: Session, village_id: int, current_user: schemas.User) -> None:
    village = crud.get_village(db, village_id=village_id)
    if village is None or (village.user_id != current_user.id and not getattr(current_user, "is_admin", False)):
        raise HTTPException(status_code=404, detail="Village not found")


@router.get("/troops/", response_model=List[models.Troop])
def read_troops(db: Session = Depends(get_db)):
    troops = crud.get_troops(db)
    return troops


@router.get(
    "/villages/{village_id}/available-troops",
    response_model=List[models.TroopAvailability],
)
def read_available_troops(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    return crud.get_troop_availability(db, village_id)


@router.post("/villages/{village_id}/train")
async def train_troops(
    village_id: int,
    troops: List[models.VillageTroopCreate],
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    return await crud.train_troops(db=db, village_id=village_id, troops=troops)

@router.get("/villages/{village_id}/training-queue", response_model=List[models.TrainingQueue])
def read_training_queue(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    queue = crud.get_training_queue(db, village_id=village_id)
    return queue

@router.get("/villages/{village_id}/troops", response_model=List[models.VillageTroop])
def read_village_troops(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    return crud.get_village_troops(db, village_id=village_id)
