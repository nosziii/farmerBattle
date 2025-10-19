from fastapi import APIRouter, Depends, HTTPException
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


def _ensure_village_ownership(db: Session, village_id: int, current_user: schemas.User) -> None:
    village = crud.get_village(db, village_id=village_id)
    if village is None or (village.user_id != current_user.id and not getattr(current_user, "is_admin", False)):
        raise HTTPException(status_code=404, detail="Village not found")


@router.get("/battle/opponents/{village_id}", response_model=list[models.VillageResponse])
def get_opponents(
    village_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, village_id, current_user)
    opponents = crud.get_opponents(db, village_id=village_id)
    return opponents


@router.post("/battle/attack/{attacker_id}/{defender_id}")
def attack(
    attacker_id: int,
    defender_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    _ensure_village_ownership(db, attacker_id, current_user)
    battle_log = crud.attack(db, attacker_id=attacker_id, defender_id=defender_id)
    return battle_log


@router.get("/battle/log/{battle_id}", response_model=list[models.BattleLog])
def get_battle_log(
    battle_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user),
):
    battle = (
        db.query(schemas.Battle)
        .filter(schemas.Battle.id == battle_id)
        .first()
    )
    if battle is None:
        raise HTTPException(status_code=404, detail="Battle not found")
    involved_villages = {battle.attacker_id, battle.defender_id}
    owned_village_ids = {village.id for village in crud.get_villages_by_user_id(db, current_user.id)}
    if not involved_villages.intersection(owned_village_ids) and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=404, detail="Battle not found")

    battle_log = crud.get_battle_log(db, battle_id=battle_id)
    return battle_log
