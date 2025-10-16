from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from . import models, schemas
import datetime
import random
from typing import List
from .websocket import manager

# Upgrade costs
BASE_COST = {
    "wood_mill": {"wood": 60, "clay": 40, "iron": 20},
    "clay_pit": {"wood": 40, "clay": 60, "iron": 20},
    "iron_mine": {"wood": 80, "clay": 80, "iron": 40},
}
COST_FACTOR = 1.5

def get_village(db: Session, village_id: int):
    db_village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if db_village:
        time_diff = (datetime.datetime.utcnow() - db_village.last_updated).total_seconds() / 3600  # Time difference in hours
        db_village.wood += db_village.wood_production * time_diff
        db_village.clay += db_village.clay_production * time_diff
        db_village.iron += db_village.iron_production * time_diff
        db_village.last_updated = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_village)
    return db_village

def get_villages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(schemas.Village).offset(skip).limit(limit).all()

def get_villages_by_user_id(db: Session, user_id: int):
    return db.query(schemas.Village).filter(schemas.Village.user_id == user_id).all()

def create_village(db: Session, village: models.VillageCreate):
    db_village = schemas.Village(
        name=village.name,
        wood=500,
        clay=500,
        iron=500,
        wood_production=10,
        clay_production=10,
        iron_production=10,
        last_updated=datetime.datetime.utcnow(),
        wood_mill_level=1,
        clay_pit_level=1,
        iron_mine_level=1,
        score=100,
        user_id=1 # I will need to fix this later
    )
    db.add(db_village)
    db.commit()
    db.refresh(db_village)
    return db_village

def upgrade_building(db: Session, village_id: int, building: str):
    db_village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if not db_village:
        raise HTTPException(status_code=404, detail="Village not found")

    level = 0
    if building == "wood_mill":
        level = db_village.wood_mill_level
    elif building == "clay_pit":
        level = db_village.clay_pit_level
    elif building == "iron_mine":
        level = db_village.iron_mine_level
    else:
        raise HTTPException(status_code=400, detail="Invalid building type")

    cost_wood = BASE_COST[building]["wood"] * (COST_FACTOR ** level)
    cost_clay = BASE_COST[building]["clay"] * (COST_FACTOR ** level)
    cost_iron = BASE_COST[building]["iron"] * (COST_FACTOR ** level)

    if db_village.wood < cost_wood or db_village.clay < cost_clay or db_village.iron < cost_iron:
        raise HTTPException(status_code=400, detail="Not enough resources")

    db_village.wood -= cost_wood
    db_village.clay -= cost_clay
    db_village.iron -= cost_iron

    if building == "wood_mill":
        db_village.wood_mill_level += 1
        db_village.wood_production *= 1.2
    elif building == "clay_pit":
        db_village.clay_pit_level += 1
        db_village.clay_production *= 1.2
    elif building == "iron_mine":
        db_village.iron_mine_level += 1
        db_village.iron_production *= 1.2
        
    db.commit()
    db.refresh(db_village)
    return db_village

def get_leaderboard(db: Session, skip: int = 0, limit: int = 10):
    return db.query(schemas.Village).order_by(schemas.Village.score.desc()).offset(skip).limit(limit).all()

def get_opponents(db: Session, village_id: int):
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    opponents = db.query(schemas.Village).filter(
        schemas.Village.user_id != village.user_id,
        schemas.Village.score >= village.score * 0.8,
        schemas.Village.score <= village.score * 1.2
    ).all()
    return opponents

def attack(db: Session, attacker_id: int, defender_id: int):
    attacker = get_village(db, attacker_id)
    defender = get_village(db, defender_id)

    if not attacker or not defender:
        raise HTTPException(status_code=404, detail="Village not found")

    if attacker.user_id == defender.user_id:
        raise HTTPException(status_code=400, detail="Cannot attack your own village")

    # Simple battle logic: higher score wins
    if attacker.score > defender.score:
        winner = attacker
        loser = defender
    else:
        winner = defender
        loser = attacker

    # Winner steals resources
    stolen_wood = loser.wood * 0.1
    stolen_clay = loser.clay * 0.1
    stolen_iron = loser.iron * 0.1

    winner.wood += stolen_wood
    winner.clay += stolen_clay
    winner.iron += stolen_iron

    loser.wood -= stolen_wood
    loser.clay -= stolen_clay
    loser.iron -= stolen_iron

    # Update scores
    winner.score += 10
    loser.score -= 5

    battle = schemas.Battle(
        attacker_id=attacker_id,
        defender_id=defender_id,
        winner_id=winner.id
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)

    log = f"{winner.name} defeated {loser.name} and stole {stolen_wood:.0f} wood, {stolen_clay:.0f} clay, and {stolen_iron:.0f} iron."
    battle_log = schemas.BattleLog(
        battle_id=battle.id,
        turn=1,
        log=log
    )
    db.add(battle_log)
    db.commit()
    db.refresh(battle_log)

    return battle_log

def get_battle_log(db: Session, battle_id: int):
    return db.query(schemas.BattleLog).filter(schemas.BattleLog.battle_id == battle_id).all()

def create_user(db: Session, user: models.UserCreate):
    hashed_password = user.password + "notreallyhashed"
    db_user = schemas.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_troops(db: Session):
    return db.query(schemas.Troop).all()

def create_initial_troops(db: Session):
    if db.query(schemas.Troop).count() == 0:
        troops = [
            schemas.Troop(name="Warrior", attack=10, defense=5, speed=10, carry_capacity=50, wood_cost=50, clay_cost=30, iron_cost=10, training_time=60),
            schemas.Troop(name="Swordsman", attack=20, defense=10, speed=8, carry_capacity=30, wood_cost=80, clay_cost=50, iron_cost=20, training_time=120),
            schemas.Troop(name="Archer", attack=15, defense=5, speed=12, carry_capacity=40, wood_cost=60, clay_cost=40, iron_cost=15, training_time=90),
        ]
        db.add_all(troops)
        db.commit()

def train_troops(db: Session, village_id: int, troops: List[models.VillageTroopCreate]):
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    for troop_order in troops:
        troop = db.query(schemas.Troop).filter(schemas.Troop.id == troop_order.troop_id).first()
        if not troop:
            raise HTTPException(status_code=404, detail=f"Troop with id {troop_order.troop_id} not found")

        total_wood_cost = troop.wood_cost * troop_order.quantity
        total_clay_cost = troop.clay_cost * troop_order.quantity
        total_iron_cost = troop.iron_cost * troop_order.quantity

        if village.wood < total_wood_cost or village.clay < total_clay_cost or village.iron < total_iron_cost:
            raise HTTPException(status_code=400, detail="Not enough resources")

        village.wood -= total_wood_cost
        village.clay -= total_clay_cost
        village.iron -= total_iron_cost

        training_time = troop.training_time * troop_order.quantity
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=training_time)

        training_queue_item = schemas.TrainingQueue(
            village_id=village_id,
            troop_id=troop_order.troop_id,
            quantity=troop_order.quantity,
            end_time=end_time
        )
        db.add(training_queue_item)

    db.commit()
    manager.broadcast(f"village:{village_id}:training_started")
    return {"message": "Troops are being trained"}

from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import HTTPException
from . import models, schemas
import datetime
import random
from typing import List
from .websocket import manager
import asyncio

# Upgrade costs
BASE_COST = {
    "wood_mill": {"wood": 60, "clay": 40, "iron": 20},
    "clay_pit": {"wood": 40, "clay": 60, "iron": 20},
    "iron_mine": {"wood": 80, "clay": 80, "iron": 40},
}
COST_FACTOR = 1.5

def get_village(db: Session, village_id: int):
    db_village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if db_village:
        time_diff = (datetime.datetime.utcnow() - db_village.last_updated).total_seconds() / 3600  # Time difference in hours
        db_village.wood += db_village.wood_production * time_diff
        db_village.clay += db_village.clay_production * time_diff
        db_village.iron += db_village.iron_production * time_diff
        db_village.last_updated = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_village)
    return db_village

def get_villages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(schemas.Village).offset(skip).limit(limit).all()

def get_villages_by_user_id(db: Session, user_id: int):
    return db.query(schemas.Village).filter(schemas.Village.user_id == user_id).all()

def create_village(db: Session, village: models.VillageCreate):
    db_village = schemas.Village(
        name=village.name,
        wood=500,
        clay=500,
        iron=500,
        wood_production=10,
        clay_production=10,
        iron_production=10,
        last_updated=datetime.datetime.utcnow(),
        wood_mill_level=1,
        clay_pit_level=1,
        iron_mine_level=1,
        score=100,
        user_id=1 # I will need to fix this later
    )
    db.add(db_village)
    db.commit()
    db.refresh(db_village)
    return db_village

def upgrade_building(db: Session, village_id: int, building: str):
    db_village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if not db_village:
        raise HTTPException(status_code=404, detail="Village not found")

    level = 0
    if building == "wood_mill":
        level = db_village.wood_mill_level
    elif building == "clay_pit":
        level = db_village.clay_pit_level
    elif building == "iron_mine":
        level = db_village.iron_mine_level
    else:
        raise HTTPException(status_code=400, detail="Invalid building type")

    cost_wood = BASE_COST[building]["wood"] * (COST_FACTOR ** level)
    cost_clay = BASE_COST[building]["clay"] * (COST_FACTOR ** level)
    cost_iron = BASE_COST[building]["iron"] * (COST_FACTOR ** level)

    if db_village.wood < cost_wood or db_village.clay < cost_clay or db_village.iron < cost_iron:
        raise HTTPException(status_code=400, detail="Not enough resources")

    db_village.wood -= cost_wood
    db_village.clay -= cost_clay
    db_village.iron -= cost_iron

    if building == "wood_mill":
        db_village.wood_mill_level += 1
        db_village.wood_production *= 1.2
    elif building == "clay_pit":
        db_village.clay_pit_level += 1
        db_village.clay_production *= 1.2
    elif building == "iron_mine":
        db_village.iron_mine_level += 1
        db_village.iron_production *= 1.2
        
    db.commit()
    db.refresh(db_village)
    return db_village

def get_leaderboard(db: Session, skip: int = 0, limit: int = 10):
    return db.query(schemas.Village).order_by(schemas.Village.score.desc()).offset(skip).limit(limit).all()

def get_opponents(db: Session, village_id: int):
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    opponents = db.query(schemas.Village).filter(
        schemas.Village.user_id != village.user_id,
        schemas.Village.score >= village.score * 0.8,
        schemas.Village.score <= village.score * 1.2
    ).all()
    return opponents

def attack(db: Session, attacker_id: int, defender_id: int):
    attacker = get_village(db, attacker_id)
    defender = get_village(db, defender_id)

    if not attacker or not defender:
        raise HTTPException(status_code=404, detail="Village not found")

    if attacker.user_id == defender.user_id:
        raise HTTPException(status_code=400, detail="Cannot attack your own village")

    # Simple battle logic: higher score wins
    if attacker.score > defender.score:
        winner = attacker
        loser = defender
    else:
        winner = defender
        loser = attacker

    # Winner steals resources
    stolen_wood = loser.wood * 0.1
    stolen_clay = loser.clay * 0.1
    stolen_iron = loser.iron * 0.1

    winner.wood += stolen_wood
    winner.clay += stolen_clay
    winner.iron += stolen_iron

    loser.wood -= stolen_wood
    loser.clay -= stolen_clay
    loser.iron -= stolen_iron

    # Update scores
    winner.score += 10
    loser.score -= 5

    battle = schemas.Battle(
        attacker_id=attacker_id,
        defender_id=defender_id,
        winner_id=winner.id
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)

    log = f"{winner.name} defeated {loser.name} and stole {stolen_wood:.0f} wood, {stolen_clay:.0f} clay, and {stolen_iron:.0f} iron."
    battle_log = schemas.BattleLog(
        battle_id=battle.id,
        turn=1,
        log=log
    )
    db.add(battle_log)
    db.commit()
    db.refresh(battle_log)

    return battle_log

def get_battle_log(db: Session, battle_id: int):
    return db.query(schemas.BattleLog).filter(schemas.BattleLog.battle_id == battle_id).all()

def create_user(db: Session, user: models.UserCreate):
    hashed_password = user.password + "notreallyhashed"
    db_user = schemas.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_troops(db: Session):
    return db.query(schemas.Troop).all()

def create_initial_troops(db: Session):
    if db.query(schemas.Troop).count() == 0:
        troops = [
            schemas.Troop(name="Warrior", attack=10, defense=5, speed=10, carry_capacity=50, wood_cost=50, clay_cost=30, iron_cost=10, training_time=60),
            schemas.Troop(name="Swordsman", attack=20, defense=10, speed=8, carry_capacity=30, wood_cost=80, clay_cost=50, iron_cost=20, training_time=120),
            schemas.Troop(name="Archer", attack=15, defense=5, speed=12, carry_capacity=40, wood_cost=60, clay_cost=40, iron_cost=15, training_time=90),
        ]
        db.add_all(troops)
        db.commit()

from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import HTTPException
from . import models, schemas
import datetime
import random
from typing import List
from .websocket import manager
import asyncio

# Upgrade costs
BASE_COST = {
    "wood_mill": {"wood": 60, "clay": 40, "iron": 20},
    "clay_pit": {"wood": 40, "clay": 60, "iron": 20},
    "iron_mine": {"wood": 80, "clay": 80, "iron": 40},
}
COST_FACTOR = 1.5

def get_village(db: Session, village_id: int):
    db_village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if db_village:
        time_diff = (datetime.datetime.utcnow() - db_village.last_updated).total_seconds() / 3600  # Time difference in hours
        db_village.wood += db_village.wood_production * time_diff
        db_village.clay += db_village.clay_production * time_diff
        db_village.iron += db_village.iron_production * time_diff
        db_village.last_updated = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_village)
    return db_village

def get_villages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(schemas.Village).offset(skip).limit(limit).all()

def get_villages_by_user_id(db: Session, user_id: int):
    return db.query(schemas.Village).filter(schemas.Village.user_id == user_id).all()

def create_village(db: Session, village: models.VillageCreate):
    db_village = schemas.Village(
        name=village.name,
        wood=500,
        clay=500,
        iron=500,
        wood_production=10,
        clay_production=10,
        iron_production=10,
        last_updated=datetime.datetime.utcnow(),
        wood_mill_level=1,
        clay_pit_level=1,
        iron_mine_level=1,
        score=100,
        user_id=1 # I will need to fix this later
    )
    db.add(db_village)
    db.commit()
    db.refresh(db_village)
    return db_village

def upgrade_building(db: Session, village_id: int, building: str):
    db_village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if not db_village:
        raise HTTPException(status_code=404, detail="Village not found")

    level = 0
    if building == "wood_mill":
        level = db_village.wood_mill_level
    elif building == "clay_pit":
        level = db_village.clay_pit_level
    elif building == "iron_mine":
        level = db_village.iron_mine_level
    else:
        raise HTTPException(status_code=400, detail="Invalid building type")

    cost_wood = BASE_COST[building]["wood"] * (COST_FACTOR ** level)
    cost_clay = BASE_COST[building]["clay"] * (COST_FACTOR ** level)
    cost_iron = BASE_COST[building]["iron"] * (COST_FACTOR ** level)

    if db_village.wood < cost_wood or db_village.clay < cost_clay or db_village.iron < cost_iron:
        raise HTTPException(status_code=400, detail="Not enough resources")

    db_village.wood -= cost_wood
    db_village.clay -= cost_clay
    db_village.iron -= cost_iron

    if building == "wood_mill":
        db_village.wood_mill_level += 1
        db_village.wood_production *= 1.2
    elif building == "clay_pit":
        db_village.clay_pit_level += 1
        db_village.clay_production *= 1.2
    elif building == "iron_mine":
        db_village.iron_mine_level += 1
        db_village.iron_production *= 1.2
        
    db.commit()
    db.refresh(db_village)
    return db_village

def get_leaderboard(db: Session, skip: int = 0, limit: int = 10):
    return db.query(schemas.Village).order_by(schemas.Village.score.desc()).offset(skip).limit(limit).all()

def get_opponents(db: Session, village_id: int):
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    opponents = db.query(schemas.Village).filter(
        schemas.Village.user_id != village.user_id,
        schemas.Village.score >= village.score * 0.8,
        schemas.Village.score <= village.score * 1.2
    ).all()
    return opponents

def attack(db: Session, attacker_id: int, defender_id: int):
    attacker = get_village(db, attacker_id)
    defender = get_village(db, defender_id)

    if not attacker or not defender:
        raise HTTPException(status_code=404, detail="Village not found")

    if attacker.user_id == defender.user_id:
        raise HTTPException(status_code=400, detail="Cannot attack your own village")

    # Simple battle logic: higher score wins
    if attacker.score > defender.score:
        winner = attacker
        loser = defender
    else:
        winner = defender
        loser = attacker

    # Winner steals resources
    stolen_wood = loser.wood * 0.1
    stolen_clay = loser.clay * 0.1
    stolen_iron = loser.iron * 0.1

    winner.wood += stolen_wood
    winner.clay += stolen_clay
    winner.iron += stolen_iron

    loser.wood -= stolen_wood
    loser.clay -= stolen_clay
    loser.iron -= stolen_iron

    # Update scores
    winner.score += 10
    loser.score -= 5

    battle = schemas.Battle(
        attacker_id=attacker_id,
        defender_id=defender_id,
        winner_id=winner.id
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)

    log = f"{winner.name} defeated {loser.name} and stole {stolen_wood:.0f} wood, {stolen_clay:.0f} clay, and {stolen_iron:.0f} iron."
    battle_log = schemas.BattleLog(
        battle_id=battle.id,
        turn=1,
        log=log
    )
    db.add(battle_log)
    db.commit()
    db.refresh(battle_log)

    return battle_log

def get_battle_log(db: Session, battle_id: int):
    return db.query(schemas.BattleLog).filter(schemas.BattleLog.battle_id == battle_id).all()

def create_user(db: Session, user: models.UserCreate):
    hashed_password = user.password + "notreallyhashed"
    db_user = schemas.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_troops(db: Session):
    return db.query(schemas.Troop).all()

def create_initial_troops(db: Session):
    if db.query(schemas.Troop).count() == 0:
        troops = [
            schemas.Troop(name="Warrior", attack=10, defense=5, speed=10, carry_capacity=50, wood_cost=50, clay_cost=30, iron_cost=10, training_time=60),
            schemas.Troop(name="Swordsman", attack=20, defense=10, speed=8, carry_capacity=30, wood_cost=80, clay_cost=50, iron_cost=20, training_time=120),
            schemas.Troop(name="Archer", attack=15, defense=5, speed=12, carry_capacity=40, wood_cost=60, clay_cost=40, iron_cost=15, training_time=90),
        ]
        db.add_all(troops)
        db.commit()

async def train_troops(db: Session, village_id: int, troops: List[models.VillageTroopCreate]):
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    for troop_order in troops:
        troop = db.query(schemas.Troop).filter(schemas.Troop.id == troop_order.troop_id).first()
        if not troop:
            raise HTTPException(status_code=404, detail=f"Troop with id {troop_order.troop_id} not found")

        total_wood_cost = troop.wood_cost * troop_order.quantity
        total_clay_cost = troop.clay_cost * troop_order.quantity
        total_iron_cost = troop.iron_cost * troop_order.quantity

        if village.wood < total_wood_cost or village.clay < total_clay_cost or village.iron < total_iron_cost:
            raise HTTPException(status_code=400, detail="Not enough resources")

        village.wood -= total_wood_cost
        village.clay -= total_clay_cost
        village.iron -= total_iron_cost

        training_time = troop.training_time * troop_order.quantity
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=training_time)

        training_queue_item = schemas.TrainingQueue(
            village_id=village_id,
            troop_id=troop_order.troop_id,
            quantity=troop_order.quantity,
            end_time=end_time
        )
        db.add(training_queue_item)

    db.commit()
    await manager.broadcast(f"village:{village_id}:training_started")
    return {"message": "Troops are being trained"}

def get_training_queue(db: Session, village_id: int):
    return db.query(schemas.TrainingQueue).options(selectinload(schemas.TrainingQueue.troop)).filter(schemas.TrainingQueue.village_id == village_id).all()

def process_training_queue(db: Session):
    training_queue = db.query(schemas.TrainingQueue).filter(schemas.TrainingQueue.end_time <= datetime.datetime.utcnow()).all()
    for item in training_queue:
        village_troop = db.query(schemas.VillageTroop).filter(
            schemas.VillageTroop.village_id == item.village_id,
            schemas.VillageTroop.troop_id == item.troop_id
        ).first()
        if village_troop:
            village_troop.quantity += item.quantity
        else:
            village_troop = schemas.VillageTroop(
                village_id=item.village_id,
                troop_id=item.troop_id,
                quantity=item.quantity
            )
            db.add(village_troop)
        db.delete(item)
    db.commit()


def get_training_queue(db: Session, village_id: int):
    return db.query(schemas.TrainingQueue).options(selectinload(schemas.TrainingQueue.troop)).filter(schemas.TrainingQueue.village_id == village_id).all()

def process_training_queue(db: Session):
    training_queue = db.query(schemas.TrainingQueue).filter(schemas.TrainingQueue.end_time <= datetime.datetime.utcnow()).all()
    for item in training_queue:
        village_troop = db.query(schemas.VillageTroop).filter(
            schemas.VillageTroop.village_id == item.village_id,
            schemas.VillageTroop.troop_id == item.troop_id
        ).first()
        if village_troop:
            village_troop.quantity += item.quantity
        else:
            village_troop = schemas.VillageTroop(
                village_id=item.village_id,
                troop_id=item.troop_id,
                quantity=item.quantity
            )
            db.add(village_troop)
        db.delete(item)
    db.commit()

def process_training_queue(db: Session):
    training_queue = db.query(schemas.TrainingQueue).filter(schemas.TrainingQueue.end_time <= datetime.datetime.utcnow()).all()
    for item in training_queue:
        village_troop = db.query(schemas.VillageTroop).filter(
            schemas.VillageTroop.village_id == item.village_id,
            schemas.VillageTroop.troop_id == item.troop_id
        ).first()
        if village_troop:
            village_troop.quantity += item.quantity
        else:
            village_troop = schemas.VillageTroop(
                village_id=item.village_id,
                troop_id=item.troop_id,
                quantity=item.quantity
            )
            db.add(village_troop)
        db.delete(item)
    db.commit()


def get_troops(db: Session):
    return db.query(schemas.Troop).all()

def create_initial_troops(db: Session):
    if db.query(schemas.Troop).count() == 0:
        troops = [
            schemas.Troop(name="Warrior", attack=10, defense=5, speed=10, carry_capacity=50, wood_cost=50, clay_cost=30, iron_cost=10, training_time=60),
            schemas.Troop(name="Swordsman", attack=20, defense=10, speed=8, carry_capacity=30, wood_cost=80, clay_cost=50, iron_cost=20, training_time=120),
            schemas.Troop(name="Archer", attack=15, defense=5, speed=12, carry_capacity=40, wood_cost=60, clay_cost=40, iron_cost=15, training_time=90),
        ]
        db.add_all(troops)
        db.commit()

def train_troops(db: Session, village_id: int, troops: List[models.VillageTroopCreate]):
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    for troop_order in troops:
        troop = db.query(schemas.Troop).filter(schemas.Troop.id == troop_order.troop_id).first()
        if not troop:
            raise HTTPException(status_code=404, detail=f"Troop with id {troop_order.troop_id} not found")

        total_wood_cost = troop.wood_cost * troop_order.quantity
        total_clay_cost = troop.clay_cost * troop_order.quantity
        total_iron_cost = troop.iron_cost * troop_order.quantity

        if village.wood < total_wood_cost or village.clay < total_clay_cost or village.iron < total_iron_cost:
            raise HTTPException(status_code=400, detail="Not enough resources")

        village.wood -= total_wood_cost
        village.clay -= total_clay_cost
        village.iron -= total_iron_cost

        training_time = troop.training_time * troop_order.quantity
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=training_time)

        training_queue_item = schemas.TrainingQueue(
            village_id=village_id,
            troop_id=troop_order.troop_id,
            quantity=troop_order.quantity,
            end_time=end_time
        )
        db.add(training_queue_item)

    db.commit()
    manager.broadcast(f"village:{village_id}:training_started")
    return {"message": "Troops are being trained"}

def get_training_queue(db: Session, village_id: int):
    return db.query(schemas.TrainingQueue).filter(schemas.TrainingQueue.village_id == village_id).all()
