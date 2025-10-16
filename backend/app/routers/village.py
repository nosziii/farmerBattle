from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Union

from .. import crud, models, schemas
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
def create_village(village: models.VillageCreate, db: Session = Depends(get_db)):
    return crud.create_village(db=db, village=village)


@router.get("/villages/{village_id}", response_model=models.VillageResponse)
def read_village(village_id: int, db: Session = Depends(get_db)):
    db_village = crud.get_village(db, village_id=village_id)
    if db_village is None:
        raise HTTPException(status_code=404, detail="Village not found")
    return db_village

@router.get("/villages/", response_model=List[models.VillageResponse])
def read_villages(user_id: Union[int, None] = None, db: Session = Depends(get_db)):
    if user_id:
        villages = crud.get_villages_by_user_id(db, user_id=user_id)
    else:
        villages = crud.get_villages(db)
    return villages
