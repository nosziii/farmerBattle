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


@router.post("/villages/", response_model=models.VillageResponse)
def create_village(
    village: models.VillageCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    payload = models.VillageCreate(name=village.name, user_id=current_user.id)
    return crud.create_village(db=db, village=payload)


@router.get("/villages/{village_id}", response_model=models.VillageResponse)
def read_village(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    db_village = crud.get_village(db, village_id=village_id)
    if db_village is None:
        raise HTTPException(status_code=404, detail="Village not found")
    if db_village.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=404, detail="Village not found")
    return db_village

@router.get("/villages/", response_model=List[models.VillageResponse])
def read_villages(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    return crud.get_villages_by_user_id(db, user_id=current_user.id)
