from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from fastapi import HTTPException
from . import models, schemas
import datetime
import random
from typing import Dict, List, Optional
from .websocket import manager
from .config.buildings import (
    BUILDING_CONFIG,
    get_building_definition,
    get_level_definition,
    get_next_level_definition,
)
from .config.world import WORLD_CONFIG

RESOURCE_TICK_SECONDS = 5
BARBARIAN_GROWTH_TICK_SECONDS = 60


def _weighted_random_level() -> int:
    """Pick a barbarian village level using the configured weight distribution."""
    levels = list(WORLD_CONFIG.barbarian.level_weights.keys())
    weights = list(WORLD_CONFIG.barbarian.level_weights.values())
    # normalise weights to guard against misconfiguration that does not sum to 1
    weight_sum = sum(weights)
    if weight_sum == 0:
        return 1
    normalised = [weight / weight_sum for weight in weights]
    return random.choices(levels, weights=normalised, k=1)[0]


def _initial_warrior_count(level: int) -> int:
    """Return an initial warrior count for a barbarian village at `level`."""
    warrior_range = WORLD_CONFIG.barbarian.warrior_ranges.get(level)
    if warrior_range is None:
        # fall back to the closest defined level to keep numbers sensible
        defined_levels = sorted(WORLD_CONFIG.barbarian.warrior_ranges.keys())
        fallback_level = max((lvl for lvl in defined_levels if lvl <= level), default=defined_levels[0])
        warrior_range = WORLD_CONFIG.barbarian.warrior_ranges[fallback_level]
    low, high = warrior_range
    return random.randint(low, high)


def ensure_world_map(db: Session) -> None:
    """Create the world map grid and initial barbarian villages if none exist yet."""
    existing_tiles = db.query(func.count(schemas.WorldTile.id)).scalar()
    if existing_tiles and existing_tiles > 0:
        return

    width = WORLD_CONFIG.width
    height = WORLD_CONFIG.height
    now = datetime.datetime.utcnow()

    tiles: List[schemas.WorldTile] = []
    for y in range(height):
        for x in range(width):
            tile = schemas.WorldTile(x=x, y=y)
            db.add(tile)
            tiles.append(tile)

    db.flush()

    # Assign existing player villages to random tiles first so they always occupy the map.
    available_tiles = tiles.copy()
    random.shuffle(available_tiles)
    player_villages = db.query(schemas.Village).all()
    for village in player_villages:
        if not available_tiles:
            break
        tile = available_tiles.pop()
        tile.player_village_id = village.id

    # Recompute available tiles once player villages have been placed.
    available_tiles = [tile for tile in tiles if tile.player_village_id is None]
    random.shuffle(available_tiles)

    targeted_barbarian_count = int(width * height * WORLD_CONFIG.barbarian.density)
    targeted_barbarian_count = max(1, min(targeted_barbarian_count, len(available_tiles)))

    for _ in range(targeted_barbarian_count):
        if not available_tiles:
            break
        tile = available_tiles.pop()
        level = _weighted_random_level()
        barbarian = schemas.BarbarianVillage(
            name=f"Barbarian {tile.x}|{tile.y}",
            level=level,
            warriors=_initial_warrior_count(level),
            last_growth_at=now,
            last_level_up_at=now,
        )
        tile.barbarian_village = barbarian
        db.add(barbarian)

    db.commit()


def assign_player_village_to_tile(db: Session, village: schemas.Village) -> None:
    """Place a newly created village on an empty world tile."""
    ensure_world_map(db)

    tile = (
        db.query(schemas.WorldTile)
        .filter(
            schemas.WorldTile.player_village_id.is_(None),
            schemas.WorldTile.barbarian_village_id.is_(None),
        )
        .order_by(func.random())
        .first()
    )

    if tile is None:
        raise HTTPException(status_code=409, detail="World map is full. Cannot place new village.")

    tile.player_village_id = village.id


def get_world_map(db: Session) -> models.MapOverview:
    """Return an overview of the current world map."""
    ensure_world_map(db)

    tiles = (
        db.query(schemas.WorldTile)
        .options(
            selectinload(schemas.WorldTile.player_village).selectinload(schemas.Village.owner),
            selectinload(schemas.WorldTile.barbarian_village),
        )
        .order_by(schemas.WorldTile.y.asc(), schemas.WorldTile.x.asc())
        .all()
    )

    map_tiles: List[models.MapTile] = []
    for tile in tiles:
        if tile.player_village:
            village_model = models.VillageResponse.from_orm(tile.player_village)
            map_tiles.append(
                models.MapTile(
                    x=tile.x,
                    y=tile.y,
                    type="player",
                    village=village_model,
                )
            )
        elif tile.barbarian_village:
            map_tiles.append(
                models.MapTile(
                    x=tile.x,
                    y=tile.y,
                    type="barbarian",
                    barbarian=models.BarbarianVillage.from_orm(tile.barbarian_village),
                )
            )
        else:
            map_tiles.append(models.MapTile(x=tile.x, y=tile.y, type="empty"))

    return models.MapOverview(width=WORLD_CONFIG.width, height=WORLD_CONFIG.height, tiles=map_tiles)


def process_barbarian_growth(db: Session) -> List[Dict[str, int]]:
    """Advance barbarian villages over time based on the configured growth rules."""
    ensure_world_map(db)

    growth_config = WORLD_CONFIG.barbarian.growth
    now = datetime.datetime.utcnow()
    updates: List[Dict[str, int]] = []

    villages = db.query(schemas.BarbarianVillage).all()
    if not villages:
        return updates

    for village in villages:
        updated = False

        # Warrior growth tick
        minutes_since_growth = (now - village.last_growth_at).total_seconds() / 60
        if minutes_since_growth >= growth_config.growth_interval_minutes:
            ticks = int(minutes_since_growth // growth_config.growth_interval_minutes)
            if ticks > 0:
                warriors_to_add = ticks * (
                    growth_config.warriors_per_growth_base
                    + growth_config.warriors_per_growth_per_level * village.level
                )
                village.warriors += warriors_to_add
                village.last_growth_at = now
                updated = True

        # Level-up tick
        minutes_since_level_up = (now - village.last_level_up_at).total_seconds() / 60
        if minutes_since_level_up >= growth_config.level_up_interval_minutes and village.level < growth_config.max_level:
            level_ticks = int(minutes_since_level_up // growth_config.level_up_interval_minutes)
            level_ticks = min(level_ticks, growth_config.max_level - village.level)
            if level_ticks > 0:
                village.level += level_ticks
                village.warriors += growth_config.warriors_per_level_up * level_ticks
                village.last_level_up_at = now
                updated = True

        if updated:
            updates.append(
                {
                    "barbarian_village_id": village.id,
                    "level": village.level,
                    "warriors": village.warriors,
                }
            )

    if updates:
        db.commit()

    return updates

def calculate_resource_capacities(village: schemas.Village) -> Dict[str, float]:
    capacities: Dict[str, float] = {}
    max_cap = 999_999_999.0

    for building_key, config in BUILDING_CONFIG.items():
        resource_field = config.get("resource_field")
        if not resource_field:
            continue
        level_field = _building_level_field(building_key)
        level = getattr(village, level_field)
        level_definition = get_level_definition(building_key, level)
        storage = level_definition.get("storage")
        if storage is not None:
            capacities[resource_field] = float(storage)
        else:
            capacities.setdefault(resource_field, max_cap)

    for resource in ("wood", "clay", "iron", "gold"):
        capacities.setdefault(resource, max_cap)

    warehouse_bonus = 0.0
    if hasattr(village, "warehouse_level"):
        warehouse_level = getattr(village, "warehouse_level")
        try:
            warehouse_definition = get_level_definition("warehouse", warehouse_level)
        except KeyError:
            warehouse_definition = None
        if warehouse_definition:
            warehouse_storage = warehouse_definition.get("storage")
            if warehouse_storage is not None:
                warehouse_bonus = float(warehouse_storage)

    if warehouse_bonus:
        for resource in ("wood", "clay", "iron"):
            capacities[resource] = min(
                max_cap,
                capacities.get(resource, max_cap) + warehouse_bonus,
            )

    return capacities

def apply_resource_production(village: schemas.Village, now: Optional[datetime.datetime] = None) -> bool:
    if now is None:
        now = datetime.datetime.utcnow()

    time_diff_hours = (now - village.last_updated).total_seconds() / 3600
    if time_diff_hours <= 0:
        return False

    capacities = calculate_resource_capacities(village)

    village.wood = min(village.wood + village.wood_production * time_diff_hours, capacities["wood"])
    village.clay = min(village.clay + village.clay_production * time_diff_hours, capacities["clay"])
    village.iron = min(village.iron + village.iron_production * time_diff_hours, capacities["iron"])
    village.gold = min(village.gold + village.gold_production * time_diff_hours, capacities["gold"])
    village.last_updated = now
    return True

def get_village(db: Session, village_id: int):
    db_village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if db_village:
        if apply_resource_production(db_village):
            db.commit()
            db.refresh(db_village)
    return db_village

def get_villages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(schemas.Village).offset(skip).limit(limit).all()

def get_villages_by_user_id(db: Session, user_id: int):
    return db.query(schemas.Village).filter(schemas.Village.user_id == user_id).all()

def process_resource_generation(db: Session) -> List[Dict[str, Dict[str, float]]]:
    now = datetime.datetime.utcnow()
    villages = db.query(schemas.Village).all()
    updates: List[Dict[str, Dict[str, float]]] = []

    for village in villages:
        if apply_resource_production(village, now):
            capacities = calculate_resource_capacities(village)
            updates.append(
                {
                    "village_id": village.id,
                    "resources": {
                        "wood": village.wood,
                        "clay": village.clay,
                        "iron": village.iron,
                        "gold": village.gold,
                    },
                    "capacities": capacities,
                }
            )

    if updates:
        db.commit()

    return updates

def create_village(db: Session, village: models.VillageCreate):
    wood_level = get_level_definition("wood_mill", 1)
    clay_level = get_level_definition("clay_pit", 1)
    iron_level = get_level_definition("iron_mine", 1)
    town_hall_level_def = get_level_definition("town_hall", 1)

    db_village = schemas.Village(
        name=village.name,
        wood=500,
        clay=500,
        iron=500,
        gold=0,
        wood_production=wood_level["production"],
        clay_production=clay_level["production"],
        iron_production=iron_level["production"],
        gold_production=town_hall_level_def["production"],
        last_updated=datetime.datetime.utcnow(),
        wood_mill_level=1,
        clay_pit_level=1,
        iron_mine_level=1,
        town_hall_level=1,
        warehouse_level=1,
        farm_level=1,
        barracks_level=1,
        smithy_level=1,
        training_ground_level=1,
        stable_level=1,
        workshop_level=1,
        forge_level=1,
        market_level=1,
        embassy_level=1,
        library_level=1,
        academy_level=1,
        noble_house_level=1,
        wall_level=1,
        watchtower_level=1,
        hospital_level=1,
        sanctuary_level=1,
        score=100,
        user_id=1 # I will need to fix this later
    )
    db.add(db_village)
    db.commit()
    db.refresh(db_village)
    assign_player_village_to_tile(db, db_village)
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

DEFAULT_TROOPS = [
    {
        "name": "Warrior",
        "attack": 10,
        "defense": 5,
        "speed": 10,
        "carry_capacity": 50,
        "wood_cost": 50,
        "clay_cost": 30,
        "iron_cost": 10,
        "training_time": 5,
    },
    {
        "name": "Swordsman",
        "attack": 20,
        "defense": 10,
        "speed": 8,
        "carry_capacity": 30,
        "wood_cost": 80,
        "clay_cost": 50,
        "iron_cost": 20,
        "training_time": 7,
    },
    {
        "name": "Archer",
        "attack": 15,
        "defense": 5,
        "speed": 12,
        "carry_capacity": 40,
        "wood_cost": 60,
        "clay_cost": 40,
        "iron_cost": 15,
        "training_time": 5,
    },
]

def create_initial_troops(db: Session):
    # Ensure defaults exist and keep their key stats in sync
    existing = {
        troop.name: troop
        for troop in db.query(schemas.Troop).filter(schemas.Troop.name.in_([t["name"] for t in DEFAULT_TROOPS])).all()
    }

    for data in DEFAULT_TROOPS:
        troop = existing.get(data["name"])
        if troop:
            updated = False
            for field, value in data.items():
                if getattr(troop, field) != value:
                    setattr(troop, field, value)
                    updated = True
            if updated:
                db.add(troop)
        else:
            db.add(schemas.Troop(**data))

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

        start_time = datetime.datetime.utcnow()
        training_time = troop.training_time * troop_order.quantity
        end_time = start_time + datetime.timedelta(seconds=training_time)

        training_queue_item = schemas.TrainingQueue(
            village_id=village_id,
            troop_id=troop_order.troop_id,
            quantity=troop_order.quantity,
            start_time=start_time,
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
    wood_level = get_level_definition("wood_mill", 1)
    clay_level = get_level_definition("clay_pit", 1)
    iron_level = get_level_definition("iron_mine", 1)

    db_village = schemas.Village(
        name=village.name,
        wood=500,
        clay=500,
        iron=500,
        wood_production=wood_level["production"],
        clay_production=clay_level["production"],
        iron_production=iron_level["production"],
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
    assign_player_village_to_tile(db, db_village)
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
    existing = {
        troop.name: troop
        for troop in db.query(schemas.Troop).filter(schemas.Troop.name.in_([t["name"] for t in DEFAULT_TROOPS])).all()
    }

    for data in DEFAULT_TROOPS:
        troop = existing.get(data["name"])
        if troop:
            updated = False
            for field, value in data.items():
                if getattr(troop, field) != value:
                    setattr(troop, field, value)
                    updated = True
            if updated:
                db.add(troop)
        else:
            db.add(schemas.Troop(**data))

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
    wood_level = get_level_definition("wood_mill", 1)
    clay_level = get_level_definition("clay_pit", 1)
    iron_level = get_level_definition("iron_mine", 1)

    db_village = schemas.Village(
        name=village.name,
        wood=500,
        clay=500,
        iron=500,
        wood_production=wood_level["production"],
        clay_production=clay_level["production"],
        iron_production=iron_level["production"],
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
    assign_player_village_to_tile(db, db_village)
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

DEFAULT_TROOPS = [
    {
        "name": "Warrior",
        "attack": 10,
        "defense": 5,
        "speed": 10,
        "carry_capacity": 50,
        "wood_cost": 50,
        "clay_cost": 30,
        "iron_cost": 10,
        "training_time": 5,
    },
    {
        "name": "Swordsman",
        "attack": 20,
        "defense": 10,
        "speed": 8,
        "carry_capacity": 30,
        "wood_cost": 80,
        "clay_cost": 50,
        "iron_cost": 20,
        "training_time": 7,
    },
    {
        "name": "Archer",
        "attack": 15,
        "defense": 5,
        "speed": 12,
        "carry_capacity": 40,
        "wood_cost": 60,
        "clay_cost": 40,
        "iron_cost": 15,
        "training_time": 5,
    },
]

def create_initial_troops(db: Session):
    existing = {
        troop.name: troop
        for troop in db.query(schemas.Troop).filter(schemas.Troop.name.in_([t["name"] for t in DEFAULT_TROOPS])).all()
    }

    for data in DEFAULT_TROOPS:
        troop = existing.get(data["name"])
        if troop:
            updated = False
            for field, value in data.items():
                if getattr(troop, field) != value:
                    setattr(troop, field, value)
                    updated = True
            if updated:
                db.add(troop)
        else:
            db.add(schemas.Troop(**data))

    db.commit()

async def train_troops(db: Session, village_id: int, troops: List[models.VillageTroopCreate]):
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    if not troops:
        raise HTTPException(status_code=400, detail={"error": "empty_order", "message": "No troops selected for training."})

    created_queue_items = []

    for troop_order in troops:
        if troop_order.quantity <= 0:
            raise HTTPException(status_code=400, detail={"error": "invalid_quantity", "message": "Training quantity must be greater than zero."})

        troop = db.query(schemas.Troop).filter(schemas.Troop.id == troop_order.troop_id).first()
        if not troop:
            raise HTTPException(status_code=404, detail={"error": "troop_not_found", "message": f"Troop with id {troop_order.troop_id} not found."})

        total_wood_cost = troop.wood_cost * troop_order.quantity
        total_clay_cost = troop.clay_cost * troop_order.quantity
        total_iron_cost = troop.iron_cost * troop_order.quantity

        shortages = {
            "wood": max(0, total_wood_cost - village.wood),
            "clay": max(0, total_clay_cost - village.clay),
            "iron": max(0, total_iron_cost - village.iron),
        }
        if any(amount > 0 for amount in shortages.values()):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "not_enough_resources",
                    "message": f"Not enough resources to train {troop.name}.",
                    "shortage": shortages,
                    "required": {"wood": total_wood_cost, "clay": total_clay_cost, "iron": total_iron_cost},
                    "available": {"wood": village.wood, "clay": village.clay, "iron": village.iron},
                    "troop": {"id": troop.id, "name": troop.name},
                },
            )

        village.wood -= total_wood_cost
        village.clay -= total_clay_cost
        village.iron -= total_iron_cost

        start_time = datetime.datetime.utcnow()
        training_time = troop.training_time * troop_order.quantity
        end_time = start_time + datetime.timedelta(seconds=training_time)

        training_queue_item = schemas.TrainingQueue(
            village_id=village_id,
            troop_id=troop_order.troop_id,
            quantity=troop_order.quantity,
            start_time=start_time,
            end_time=end_time
        )
        db.add(training_queue_item)
        created_queue_items.append(training_queue_item)

    db.commit()

    for item in created_queue_items:
        db.refresh(item)

    capacities = calculate_resource_capacities(village)

    await manager.broadcast(f"village:{village_id}:training_started")
    return {
        "message": "Troops are being trained.",
        "queue": get_training_queue(db, village_id),
        "resources": {"wood": village.wood, "clay": village.clay, "iron": village.iron, "gold": village.gold},
        "capacities": capacities,
    }

def get_training_queue(db: Session, village_id: int):
    return (
        db.query(schemas.TrainingQueue)
        .options(selectinload(schemas.TrainingQueue.troop))
        .filter(schemas.TrainingQueue.village_id == village_id)
        .order_by(schemas.TrainingQueue.end_time.asc())
        .all()
    )

def process_training_queue(db: Session):
    now = datetime.datetime.utcnow()
    ready_items = (
        db.query(schemas.TrainingQueue)
        .options(selectinload(schemas.TrainingQueue.troop))
        .filter(schemas.TrainingQueue.end_time <= now)
        .all()
    )

    completed_villages = set()

    for item in ready_items:
        village_troop = (
            db.query(schemas.VillageTroop)
            .filter(
                schemas.VillageTroop.village_id == item.village_id,
                schemas.VillageTroop.troop_id == item.troop_id,
            )
            .first()
        )
        if village_troop:
            village_troop.quantity += item.quantity
        else:
            village_troop = schemas.VillageTroop(
                village_id=item.village_id,
                troop_id=item.troop_id,
                quantity=item.quantity,
            )
            db.add(village_troop)

        completed_villages.add(item.village_id)
        db.delete(item)

    if ready_items:
        db.commit()

    return list(completed_villages)

def get_village_troops(db: Session, village_id: int):
    return (
        db.query(schemas.VillageTroop)
        .options(selectinload(schemas.VillageTroop.troop))
        .filter(schemas.VillageTroop.village_id == village_id)
        .order_by(schemas.VillageTroop.troop_id.asc())
        .all()
    )

def get_building_queue(db: Session, village_id: int):
    return (
        db.query(schemas.BuildingUpgradeQueue)
        .filter(schemas.BuildingUpgradeQueue.village_id == village_id)
        .order_by(schemas.BuildingUpgradeQueue.end_time.asc())
        .all()
    )

def _normalise_building(building: str) -> str:
    key = building.lower()
    if key not in BUILDING_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid building type '{building}'.")
    return key

def _building_level_field(building: str) -> str:
    return f"{building}_level"

def _build_requirement_statuses(village: schemas.Village, building_key: str) -> List[models.BuildingRequirementStatus]:
    config = get_building_definition(building_key)
    requirement_entries = config.get("requirements", [])
    statuses: List[models.BuildingRequirementStatus] = []

    for requirement in requirement_entries:
        required_key = requirement["building"]
        required_level = requirement["level"]
        required_definition = get_building_definition(required_key)
        current_level = getattr(village, _building_level_field(required_key))
        statuses.append(
            models.BuildingRequirementStatus(
                building=required_key,
                display_name=required_definition["display_name"],
                required_level=required_level,
                current_level=current_level,
                met=current_level >= required_level,
            )
        )

    return statuses

def upgrade_building(db: Session, village_id: int, building: str) -> models.BuildingUpgradeResponse:
    building_key = _normalise_building(building)
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    definition = get_building_definition(building_key)
    level_field = _building_level_field(building_key)
    current_level = getattr(village, level_field)

    requirement_statuses = _build_requirement_statuses(village, building_key)
    unmet_requirements = [req for req in requirement_statuses if not req.met]
    if unmet_requirements:
        requirement_summary = ", ".join(
            f"{req.display_name} Lv.{req.required_level}" for req in unmet_requirements
        )
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upgrade {definition['display_name']}. Missing requirements: {requirement_summary}.",
        )

    next_level = get_next_level_definition(building_key, current_level)
    if not next_level:
        raise HTTPException(status_code=400, detail=f"{definition['display_name']} already at the maximum level.")

    existing_upgrade = (
        db.query(schemas.BuildingUpgradeQueue)
        .filter(
            schemas.BuildingUpgradeQueue.village_id == village_id,
            schemas.BuildingUpgradeQueue.building == building_key,
        )
        .first()
    )
    if existing_upgrade:
        raise HTTPException(status_code=400, detail=f"{definition['display_name']} upgrade already in progress.")

    cost = next_level["cost"]
    if (
        village.wood < cost["wood"]
        or village.clay < cost["clay"]
        or village.iron < cost["iron"]
    ):
        raise HTTPException(status_code=400, detail="Not enough resources for the upgrade.")

    village.wood -= cost["wood"]
    village.clay -= cost["clay"]
    village.iron -= cost["iron"]

    start_time = datetime.datetime.utcnow()
    end_time = start_time + datetime.timedelta(seconds=int(next_level["duration"]))

    queue_item = schemas.BuildingUpgradeQueue(
        village_id=village_id,
        building=building_key,
        target_level=current_level + 1,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(queue_item)
    db.commit()
    db.refresh(queue_item)

    queue = get_building_queue(db, village_id)

    return models.BuildingUpgradeResponse(
        message=f"{definition['display_name']} upgrade to level {current_level + 1} started.",
        resources=models.ResourceBalances(
            wood=village.wood,
            clay=village.clay,
            iron=village.iron,
            gold=village.gold,
        ),
        queue=[models.BuildingUpgrade.from_orm(item) for item in queue],
    )

def get_building_statuses(db: Session, village_id: int) -> List[models.BuildingStatus]:
    village = get_village(db, village_id)
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    queue_items = get_building_queue(db, village_id)
    queue_lookup = {item.building: item for item in queue_items}

    statuses: List[models.BuildingStatus] = []

    ordered_config = sorted(
        BUILDING_CONFIG.items(), key=lambda entry: entry[1].get("order", 0)
    )

    for building_key, config in ordered_config:
        level_field = _building_level_field(building_key)
        current_level = getattr(village, level_field)
        current_def = get_level_definition(building_key, current_level)
        next_def = get_next_level_definition(building_key, current_level)
        active_upgrade = queue_lookup.get(building_key)
        requirement_statuses = _build_requirement_statuses(village, building_key)
        requirements_met = all(requirement.met for requirement in requirement_statuses)

        next_cost = (
            models.BuildingCost(**next_def["cost"])
            if next_def is not None
            else None
        )
        next_duration = int(next_def["duration"]) if next_def is not None else None
        upgrade_end_time = active_upgrade.end_time if active_upgrade else None

        statuses.append(
            models.BuildingStatus(
                name=config["display_name"],
                internal_name=building_key,
                category=config.get("category", ""),
                description=config.get("description", ""),
                icon=config.get("icon", ""),
                level=current_level,
                max_level=config["max_level"],
                is_upgrading=active_upgrade is not None,
                production=current_def["production"],
                storage=current_def["storage"],
                resource_field=config.get("resource_field"),
                next_cost=next_cost,
                upgrade_duration=next_duration,
                upgrade_end_time=upgrade_end_time,
                requirements=requirement_statuses,
                effects=list(config.get("effects", [])),
                unlocks=list(config.get("unlocks", [])),
                available=requirements_met and next_def is not None and not active_upgrade,
                order=int(config.get("order", 0)),
            )
        )

    return statuses

def process_building_queue(db: Session) -> List[Dict[str, object]]:
    now = datetime.datetime.utcnow()
    ready_items = (
        db.query(schemas.BuildingUpgradeQueue)
        .filter(schemas.BuildingUpgradeQueue.end_time <= now)
        .all()
    )

    updates: List[Dict[str, object]] = []

    for item in ready_items:
        village = db.query(schemas.Village).filter(schemas.Village.id == item.village_id).first()
        if not village:
            db.delete(item)
            continue

        level_field = _building_level_field(item.building)
        setattr(village, level_field, item.target_level)

        level_def = get_level_definition(item.building, item.target_level)
        resource_field = BUILDING_CONFIG[item.building]["resource_field"]

        if resource_field == "wood":
            village.wood_production = level_def["production"]
        elif resource_field == "clay":
            village.clay_production = level_def["production"]
        elif resource_field == "iron":
            village.iron_production = level_def["production"]
        elif resource_field == "gold":
            village.gold_production = level_def["production"]

        capacities = calculate_resource_capacities(village)
        village.wood = min(village.wood, capacities["wood"])
        village.clay = min(village.clay, capacities["clay"])
        village.iron = min(village.iron, capacities["iron"])
        village.gold = min(village.gold, capacities["gold"])

        db.delete(item)
        updates.append(
            {
                "village_id": village.id,
                "building": item.building,
                "level": item.target_level,
            }
        )

    if ready_items:
        db.commit()

    return updates

# --------------------------------------------------------------------------- #
# Admin helpers
# --------------------------------------------------------------------------- #

ADMIN_BUILDING_KEYS = [
    "wood_mill",
    "clay_pit",
    "iron_mine",
    "town_hall",
    "warehouse",
    "farm",
    "barracks",
    "smithy",
    "training_ground",
    "stable",
    "workshop",
    "forge",
    "market",
    "embassy",
    "library",
    "academy",
    "noble_house",
    "wall",
    "watchtower",
    "hospital",
    "sanctuary",
]


def _build_admin_village_summary(village: schemas.Village) -> models.AdminVillageSummary:
    owner_name = village.owner.username if village.owner else ""
    tile = None
    if village.world_tile:
        tile = models.MapPosition(x=village.world_tile.x, y=village.world_tile.y)
    return models.AdminVillageSummary(
        id=village.id,
        name=village.name,
        user_id=village.user_id,
        user_name=owner_name,
        resources=models.ResourceBalances(
            wood=village.wood,
            clay=village.clay,
            iron=village.iron,
            gold=village.gold,
        ),
        productions=models.ResourceBalances(
            wood=village.wood_production,
            clay=village.clay_production,
            iron=village.iron_production,
            gold=village.gold_production,
        ),
        tile=tile,
    )


def _build_admin_village_detail(village: schemas.Village) -> models.AdminVillageDetail:
    summary = _build_admin_village_summary(village)
    building_levels = {
        key: getattr(village, f"{key}_level")
        for key in ADMIN_BUILDING_KEYS
        if hasattr(village, f"{key}_level")
    }
    return models.AdminVillageDetail(
        **summary.model_dump(),
        building_levels=building_levels,
    )


def admin_list_users(db: Session) -> List[models.AdminUser]:
    users = (
        db.query(schemas.User)
        .options(selectinload(schemas.User.villages))
        .order_by(schemas.User.id.asc())
        .all()
    )
    return [
        models.AdminUser(
            id=user.id,
            username=user.username,
            is_active=user.is_active,
            village_ids=[village.id for village in user.villages],
        )
        for user in users
    ]


def admin_create_user(db: Session, payload: models.AdminUserCreate) -> models.AdminUser:
    user = create_user(db, models.UserCreate(username=payload.username, password=payload.password))
    return models.AdminUser(id=user.id, username=user.username, is_active=user.is_active, village_ids=[])


def admin_list_villages(db: Session) -> List[models.AdminVillageSummary]:
    villages = (
        db.query(schemas.Village)
        .options(selectinload(schemas.Village.owner), selectinload(schemas.Village.world_tile))
        .order_by(schemas.Village.id.asc())
        .all()
    )
    return [_build_admin_village_summary(village) for village in villages]


def admin_get_village(db: Session, village_id: int) -> models.AdminVillageDetail:
    village = (
        db.query(schemas.Village)
        .options(selectinload(schemas.Village.owner), selectinload(schemas.Village.world_tile))
        .filter(schemas.Village.id == village_id)
        .first()
    )
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
    return _build_admin_village_detail(village)


def admin_update_village(db: Session, village_id: int, payload: models.AdminVillageUpdate) -> models.AdminVillageDetail:
    village = (
        db.query(schemas.Village)
        .options(selectinload(schemas.Village.owner), selectinload(schemas.Village.world_tile))
        .filter(schemas.Village.id == village_id)
        .first()
    )
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    updated = False

    if payload.name is not None:
        village.name = payload.name
        updated = True

    for resource in ("wood", "clay", "iron", "gold"):
        value = getattr(payload, resource)
        if value is not None:
            setattr(village, resource, float(max(0.0, value)))
            updated = True

    level_updates = {
        "wood_mill": payload.wood_mill_level,
        "clay_pit": payload.clay_pit_level,
        "iron_mine": payload.iron_mine_level,
        "town_hall": payload.town_hall_level,
        "warehouse": payload.warehouse_level,
    }
    for key, value in level_updates.items():
        if value is not None:
            level_attr = f"{key}_level"
            setattr(village, level_attr, max(1, int(value)))
            updated = True

    if payload.wood_mill_level is not None:
        wood_def = get_level_definition("wood_mill", village.wood_mill_level)
        village.wood_production = wood_def["production"]
    if payload.clay_pit_level is not None:
        clay_def = get_level_definition("clay_pit", village.clay_pit_level)
        village.clay_production = clay_def["production"]
    if payload.iron_mine_level is not None:
        iron_def = get_level_definition("iron_mine", village.iron_mine_level)
        village.iron_production = iron_def["production"]
    if payload.town_hall_level is not None:
        town_def = get_level_definition("town_hall", village.town_hall_level)
        village.gold_production = town_def["production"]

    if updated:
        db.commit()
        db.refresh(village)

    return _build_admin_village_detail(village)


def admin_create_village(db: Session, payload: models.AdminVillageCreate) -> models.AdminVillageDetail:
    user = db.query(schemas.User).filter(schemas.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wood_level = get_level_definition("wood_mill", 1)
    clay_level = get_level_definition("clay_pit", 1)
    iron_level = get_level_definition("iron_mine", 1)
    town_level = get_level_definition("town_hall", 1)

    village = schemas.Village(
        name=payload.name,
        wood=500,
        clay=500,
        iron=500,
        gold=0,
        wood_production=wood_level["production"],
        clay_production=clay_level["production"],
        iron_production=iron_level["production"],
        gold_production=town_level["production"],
        last_updated=datetime.datetime.utcnow(),
        wood_mill_level=1,
        clay_pit_level=1,
        iron_mine_level=1,
        town_hall_level=1,
        warehouse_level=1,
        farm_level=1,
        barracks_level=1,
        smithy_level=1,
        training_ground_level=1,
        stable_level=1,
        workshop_level=1,
        forge_level=1,
        market_level=1,
        embassy_level=1,
        library_level=1,
        academy_level=1,
        noble_house_level=1,
        wall_level=1,
        watchtower_level=1,
        hospital_level=1,
        sanctuary_level=1,
        score=100,
        user_id=payload.user_id,
    )
    db.add(village)
    db.commit()
    db.refresh(village)
    assign_player_village_to_tile(db, village)
    db.commit()
    db.refresh(village)
    return admin_get_village(db, village.id)


def admin_assign_village_to_tile(db: Session, village_id: int, x: int, y: int, force: bool = False) -> models.MapPosition:
    ensure_world_map(db)

    village = db.query(schemas.Village).filter(schemas.Village.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")

    tile = (
        db.query(schemas.WorldTile)
        .filter(schemas.WorldTile.x == x, schemas.WorldTile.y == y)
        .first()
    )
    if not tile:
        raise HTTPException(status_code=404, detail="Tile not found")

    if tile.player_village_id and tile.player_village_id != village_id:
        if not force:
            raise HTTPException(status_code=409, detail="Tile already occupied by another village")
        tile.player_village_id = None

    if tile.barbarian_village_id and tile.barbarian_village_id != village_id:
        if not force:
            raise HTTPException(status_code=409, detail="Tile occupied by a barbarian village")
        tile.barbarian_village_id = None

    current_tile = (
        db.query(schemas.WorldTile)
        .filter(schemas.WorldTile.player_village_id == village_id)
        .first()
    )
    if current_tile:
        current_tile.player_village_id = None

    tile.player_village_id = village_id
    db.commit()
    return models.MapPosition(x=tile.x, y=tile.y)
