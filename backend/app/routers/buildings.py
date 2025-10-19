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


@router.post(
    "/villages/{village_id}/upgrade/{building}",
    response_model=models.BuildingUpgradeResponse,
)
def upgrade_building(
    village_id: int,
    building: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    return crud.upgrade_building(db, village_id=village_id, building=building)


@router.get(
    "/villages/{village_id}/buildings",
    response_model=List[models.BuildingStatus],
)
def list_buildings(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    return crud.get_building_statuses(db, village_id=village_id)


@router.get(
    "/villages/{village_id}/building-queue",
    response_model=List[models.BuildingUpgrade],
)
def list_building_queue(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    queue = crud.get_building_queue(db, village_id=village_id)
    return [models.BuildingUpgrade.from_orm(item) for item in queue]
