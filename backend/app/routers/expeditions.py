from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
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


def _ensure_village_access(
    db: Session,
    village_id: int,
    current_user: schemas.User,
) -> schemas.Village:
    village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
    if village.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorised to manage this village")
    return village


@router.get(
    "/villages/{village_id}/expeditions",
    response_model=models.ExpeditionListResponse,
)
def list_expeditions(
    village_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_access(db, village_id, current_user)
    return crud.list_expeditions(db, village_id, status_filter=status)


@router.post(
    "/villages/{village_id}/expeditions",
    response_model=models.ExpeditionSummary,
    status_code=201,
)
def create_expedition(
    village_id: int,
    payload: models.ExpeditionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_access(db, village_id, current_user)
    return crud.create_expedition(db, village_id, payload, current_user)


@router.get("/expeditions/{expedition_id}", response_model=models.ExpeditionSummary)
def get_expedition(
    expedition_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    return crud.get_expedition(db, expedition_id, current_user)
