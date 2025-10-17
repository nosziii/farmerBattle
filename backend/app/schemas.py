from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
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
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    wood_mill_level = Column(Integer, default=1)
    clay_pit_level = Column(Integer, default=1)
    iron_mine_level = Column(Integer, default=1)

    owner = relationship("User", back_populates="villages")
    offense_battles = relationship("Battle", foreign_keys="[Battle.attacker_id]", back_populates="attacker")
    defense_battles = relationship("Battle", foreign_keys="[Battle.defender_id]", back_populates="defender")
    troops = relationship("VillageTroop", back_populates="village")
    building_upgrades = relationship("BuildingUpgradeQueue", back_populates="village")

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


class BuildingUpgradeQueue(Base):
    __tablename__ = "building_upgrade_queue"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"), index=True)
    building = Column(String, index=True)
    target_level = Column(Integer)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)

    village = relationship("Village", back_populates="building_upgrades")
