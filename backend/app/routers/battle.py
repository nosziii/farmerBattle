from fastapi import APIRouter, Depends
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


@router.get("/battle/opponents/{village_id}", response_model=list[models.VillageResponse])
def get_opponents(village_id: int, db: Session = Depends(get_db)):
    opponents = crud.get_opponents(db, village_id=village_id)
    return opponents


@router.post("/battle/attack/{attacker_id}/{defender_id}")
def attack(attacker_id: int, defender_id: int, db: Session = Depends(get_db)):
    battle_log = crud.attack(db, attacker_id=attacker_id, defender_id=defender_id)
    return battle_log


@router.get("/battle/log/{battle_id}", response_model=list[models.BattleLog])
def get_battle_log(battle_id: int, db: Session = Depends(get_db)):
    battle_log = crud.get_battle_log(db, battle_id=battle_id)
    return battle_log
