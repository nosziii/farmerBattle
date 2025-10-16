from pydantic import BaseModel
from typing import List, Optional
import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class VillageBase(BaseModel):
    name: str

class VillageCreate(VillageBase):
    pass

class Village(VillageBase):
    id: int
    score: int
    user_id: int
    wood: float
    clay: float
    iron: float
    wood_production: float
    clay_production: float
    iron_production: float
    wood_mill_level: int
    clay_pit_level: int
    iron_mine_level: int
    owner: User

    class Config:
        orm_mode = True

class VillageResponse(Village):
    owner: UserBase

class BattleLogBase(BaseModel):
    turn: int
    log: str

class BattleLogCreate(BattleLogBase):
    pass

class BattleLog(BattleLogBase):
    id: int
    battle_id: int

    class Config:
        orm_mode = True

class BattleBase(BaseModel):
    attacker_id: int
    defender_id: int
    winner_id: int

class BattleCreate(BattleBase):
    pass

class Battle(BattleBase):
    id: int
    timestamp: datetime.datetime
    logs: List[BattleLog] = []

    class Config:
        orm_mode = True

class TroopBase(BaseModel):
    name: str
    attack: int
    defense: int
    speed: int
    carry_capacity: int
    wood_cost: int
    clay_cost: int
    iron_cost: int
    training_time: int

class TroopCreate(TroopBase):
    pass

class Troop(TroopBase):
    id: int

    class Config:
        orm_mode = True

class VillageTroopBase(BaseModel):
    troop_id: int
    quantity: int

class VillageTroopCreate(VillageTroopBase):
    pass

class VillageTroop(VillageTroopBase):
    id: int
    village_id: int
    troop: Troop

    class Config:
        orm_mode = True

class TrainingQueueBase(BaseModel):
    village_id: int
    troop_id: int
    quantity: int
    start_time: datetime.datetime
    end_time: datetime.datetime

class TrainingQueueCreate(TrainingQueueBase):
    pass

class TrainingQueue(TrainingQueueBase):
    id: int
    troop: Troop

    class Config:
        orm_mode = True

User.update_forward_refs()
