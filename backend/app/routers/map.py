from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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


@router.get("/map/", response_model=models.MapOverview)
def read_map(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    return crud.get_world_map(db)


@router.get("/barbarian-villages/{barbarian_id}", response_model=models.BarbarianVillageDetail)
def read_barbarian_village(
    barbarian_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    return crud.get_barbarian_village_detail(db, barbarian_id)
