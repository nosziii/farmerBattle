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


@router.post(
    "/villages/{village_id}/upgrade/{building}",
    response_model=models.BuildingUpgradeResponse,
)
def upgrade_building(village_id: int, building: str, db: Session = Depends(get_db)):
    return crud.upgrade_building(db, village_id=village_id, building=building)


@router.get(
    "/villages/{village_id}/buildings",
    response_model=List[models.BuildingStatus],
)
def list_buildings(village_id: int, db: Session = Depends(get_db)):
    return crud.get_building_statuses(db, village_id=village_id)


@router.get(
    "/villages/{village_id}/building-queue",
    response_model=List[models.BuildingUpgrade],
)
def list_building_queue(village_id: int, db: Session = Depends(get_db)):
    queue = crud.get_building_queue(db, village_id=village_id)
    return [models.BuildingUpgrade.from_orm(item) for item in queue]
