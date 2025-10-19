from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas
from ..database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(current_user: schemas.User = Depends(auth.get_current_user)) -> schemas.User:
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


@router.get("/users", response_model=List[models.AdminUser])
def list_users(
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_list_users(db)


@router.post("/users", response_model=models.AdminUser)
def create_user(
    payload: models.AdminUserCreate,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_create_user(db, payload)


@router.put("/users/{user_id}", response_model=models.AdminUser)
def update_user(
    user_id: int,
    payload: models.AdminUserUpdate,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_update_user(db, user_id, payload)


@router.get("/troops", response_model=List[models.AdminTroop])
def list_troops(
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_list_troops(db)


@router.post("/troops", response_model=models.AdminTroop, status_code=status.HTTP_201_CREATED)
def create_troop(
    payload: models.AdminTroopCreate,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_create_troop(db, payload)


@router.put("/troops/{troop_id}", response_model=models.AdminTroop)
def update_troop(
    troop_id: int,
    payload: models.AdminTroopUpdate,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_update_troop(db, troop_id, payload)


@router.get("/villages", response_model=List[models.AdminVillageSummary])
def list_villages(
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_list_villages(db)


@router.post("/villages", response_model=models.AdminVillageDetail)
def create_village(
    payload: models.AdminVillageCreate,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_create_village(db, payload)


@router.get("/villages/{village_id}", response_model=models.AdminVillageDetail)
def get_village(
    village_id: int,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_get_village(db, village_id)


@router.put("/villages/{village_id}", response_model=models.AdminVillageDetail)
def update_village(
    village_id: int,
    payload: models.AdminVillageUpdate,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_update_village(db, village_id, payload)


@router.post("/map/assign", response_model=models.MapPosition)
def assign_village_tile(
    payload: models.AdminAssignVillageTile,
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.admin_assign_village_to_tile(db, payload.village_id, payload.x, payload.y, payload.force)


@router.get("/map", response_model=models.MapOverview)
def map_overview(
    db: Session = Depends(get_db),
    _: schemas.User = Depends(require_admin),
):
    return crud.get_world_map(db)
