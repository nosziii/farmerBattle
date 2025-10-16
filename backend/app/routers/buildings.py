from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/villages/{village_id}/upgrade/{building}", response_model=models.Village)
def upgrade_building(village_id: int, building: str, db: Session = Depends(get_db)):
    db_village = crud.upgrade_building(db, village_id=village_id, building=building)
    if db_village is None:
        raise HTTPException(status_code=404, detail="Village not found")
    return db_village
