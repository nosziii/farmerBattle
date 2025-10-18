import os
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import SessionLocal

router = APIRouter()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "changeme")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(x_admin_token: str = Header(..., alias="X-Admin-Token")) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Admin token is not configured")
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


@router.get("/users", response_model=List[models.AdminUser], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return crud.admin_list_users(db)


@router.post("/users", response_model=models.AdminUser, dependencies=[Depends(require_admin)])
def create_user(payload: models.AdminUserCreate, db: Session = Depends(get_db)):
    return crud.admin_create_user(db, payload)


@router.get("/villages", response_model=List[models.AdminVillageSummary], dependencies=[Depends(require_admin)])
def list_villages(db: Session = Depends(get_db)):
    return crud.admin_list_villages(db)


@router.post("/villages", response_model=models.AdminVillageDetail, dependencies=[Depends(require_admin)])
def create_village(payload: models.AdminVillageCreate, db: Session = Depends(get_db)):
    return crud.admin_create_village(db, payload)


@router.get("/villages/{village_id}", response_model=models.AdminVillageDetail, dependencies=[Depends(require_admin)])
def get_village(village_id: int, db: Session = Depends(get_db)):
    return crud.admin_get_village(db, village_id)


@router.put("/villages/{village_id}", response_model=models.AdminVillageDetail, dependencies=[Depends(require_admin)])
def update_village(village_id: int, payload: models.AdminVillageUpdate, db: Session = Depends(get_db)):
    return crud.admin_update_village(db, village_id, payload)


@router.post("/map/assign", response_model=models.MapPosition, dependencies=[Depends(require_admin)])
def assign_village_tile(payload: models.AdminAssignVillageTile, db: Session = Depends(get_db)):
    return crud.admin_assign_village_to_tile(db, payload.village_id, payload.x, payload.y, payload.force)


@router.get("/map", response_model=models.MapOverview, dependencies=[Depends(require_admin)])
def map_overview(db: Session = Depends(get_db)):
    return crud.get_world_map(db)
