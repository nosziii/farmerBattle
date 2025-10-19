from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    villages = relationship("Village", back_populates="owner")

class Village(Base):
    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    score = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    wood = Column(Float, default=500)
    clay = Column(Float, default=500)
    iron = Column(Float, default=500)
    wood_production = Column(Float, default=10)
    clay_production = Column(Float, default=10)
    iron_production = Column(Float, default=10)
    gold = Column(Float, default=0)
    gold_production = Column(Float, default=0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    wood_mill_level = Column(Integer, default=1)
    clay_pit_level = Column(Integer, default=1)
    iron_mine_level = Column(Integer, default=1)
    town_hall_level = Column(Integer, default=1)
    warehouse_level = Column(Integer, default=1)
    farm_level = Column(Integer, default=1)
    barracks_level = Column(Integer, default=1)
    smithy_level = Column(Integer, default=1)
    training_ground_level = Column(Integer, default=1)
    stable_level = Column(Integer, default=1)
    workshop_level = Column(Integer, default=1)
    forge_level = Column(Integer, default=1)
    market_level = Column(Integer, default=1)
    embassy_level = Column(Integer, default=1)
    library_level = Column(Integer, default=1)
    academy_level = Column(Integer, default=1)
    noble_house_level = Column(Integer, default=1)
    wall_level = Column(Integer, default=1)
    watchtower_level = Column(Integer, default=1)
    hospital_level = Column(Integer, default=1)
    sanctuary_level = Column(Integer, default=1)

    owner = relationship("User", back_populates="villages")
    offense_battles = relationship("Battle", foreign_keys="[Battle.attacker_id]", back_populates="attacker")
    defense_battles = relationship("Battle", foreign_keys="[Battle.defender_id]", back_populates="defender")
    troops = relationship("VillageTroop", back_populates="village")
    building_upgrades = relationship("BuildingUpgradeQueue", back_populates="village")
    world_tile = relationship(
        "WorldTile",
        back_populates="player_village",
        uselist=False,
        foreign_keys="WorldTile.player_village_id",
    )
    expeditions = relationship("Expedition", back_populates="village")

class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True, index=True)
    attacker_id = Column(Integer, ForeignKey("villages.id"))
    defender_id = Column(Integer, ForeignKey("villages.id"))
    winner_id = Column(Integer, ForeignKey("villages.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    attacker = relationship("Village", foreign_keys=[attacker_id], back_populates="offense_battles")
    defender = relationship("Village", foreign_keys=[defender_id], back_populates="defense_battles")
    winner = relationship("Village", foreign_keys=[winner_id])
    logs = relationship("BattleLog", back_populates="battle")

class BattleLog(Base):
    __tablename__ = "battle_logs"

    id = Column(Integer, primary_key=True, index=True)
    battle_id = Column(Integer, ForeignKey("battles.id"))
    turn = Column(Integer)
    log = Column(String)

    battle = relationship("Battle", back_populates="logs")

class Troop(Base):
    __tablename__ = "troops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    attack = Column(Integer)
    defense = Column(Integer)
    speed = Column(Integer)
    carry_capacity = Column(Integer)
    wood_cost = Column(Integer)
    clay_cost = Column(Integer)
    iron_cost = Column(Integer)
    training_time = Column(Integer)
    requirements = relationship("TroopRequirement", back_populates="troop", cascade="all, delete-orphan")

class VillageTroop(Base):
    __tablename__ = "village_troops"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"))
    troop_id = Column(Integer, ForeignKey("troops.id"))
    quantity = Column(Integer)

    village = relationship("Village", back_populates="troops")
    troop = relationship("Troop")

class TrainingQueue(Base):
    __tablename__ = "training_queue"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"))
    troop_id = Column(Integer, ForeignKey("troops.id"))
    quantity = Column(Integer)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)

    village = relationship("Village")
    troop = relationship("Troop")


class TroopRequirement(Base):
    __tablename__ = "troop_requirements"

    id = Column(Integer, primary_key=True, index=True)
    troop_id = Column(Integer, ForeignKey("troops.id"), index=True, nullable=False)
    building = Column(String, index=True)
    level = Column(Integer, default=1)

    troop = relationship("Troop", back_populates="requirements")


class BuildingUpgradeQueue(Base):
    __tablename__ = "building_upgrade_queue"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"), index=True)
    building = Column(String, index=True)
    target_level = Column(Integer)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)

    village = relationship("Village", back_populates="building_upgrades")


class BarbarianVillage(Base):
    __tablename__ = "barbarian_villages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    level = Column(Integer, default=1)
    warriors = Column(Integer, default=0)
    last_growth_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_level_up_at = Column(DateTime, default=datetime.datetime.utcnow)

    tile = relationship("WorldTile", back_populates="barbarian_village", uselist=False)
    expeditions = relationship("Expedition", back_populates="barbarian_village")


class WorldTile(Base):
    __tablename__ = "world_tiles"

    id = Column(Integer, primary_key=True, index=True)
    x = Column(Integer, index=True)
    y = Column(Integer, index=True)
    player_village_id = Column(Integer, ForeignKey("villages.id"), nullable=True)
    barbarian_village_id = Column(Integer, ForeignKey("barbarian_villages.id"), nullable=True)

    player_village = relationship("Village", back_populates="world_tile", foreign_keys=[player_village_id])
    barbarian_village = relationship("BarbarianVillage", back_populates="tile", uselist=False, foreign_keys=[barbarian_village_id])

    __table_args__ = (UniqueConstraint("x", "y", name="uq_world_tiles_coordinates"),)


class Expedition(Base):
    __tablename__ = "expeditions"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"), nullable=False, index=True)
    barbarian_village_id = Column(Integer, ForeignKey("barbarian_villages.id"), nullable=False, index=True)
    status = Column(String, default="outbound", index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    departed_at = Column(DateTime, default=datetime.datetime.utcnow)
    arrive_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    return_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    travel_seconds = Column(Integer, default=0)
    distance = Column(Integer, default=0)
    success = Column(Boolean, default=False)
    battle_report = Column(String, nullable=True)
    loot = Column(JSON, default=dict)
    troops_sent = Column(JSON, default=dict)
    troops_returning = Column(JSON, default=dict)
    casualties = Column(JSON, default=dict)

    village = relationship("Village", back_populates="expeditions")
    barbarian_village = relationship("BarbarianVillage", back_populates="expeditions")
