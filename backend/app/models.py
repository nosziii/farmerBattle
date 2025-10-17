from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

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
    building_upgrades: List["BuildingUpgrade"] = []
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

class ResourceBalances(BaseModel):
    wood: float
    clay: float
    iron: float

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
    model_config = ConfigDict(from_attributes=True)

class VillageTroopBase(BaseModel):
    troop_id: int
    quantity: int

class VillageTroopCreate(VillageTroopBase):
    pass

class VillageTroop(VillageTroopBase):
    id: int
    village_id: int
    troop: Troop
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

class BuildingUpgradeBase(BaseModel):
    village_id: int
    building: str
    target_level: int
    start_time: datetime.datetime
    end_time: datetime.datetime

class BuildingUpgrade(BuildingUpgradeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class BuildingCost(BaseModel):
    wood: int
    clay: int
    iron: int

class BuildingStatus(BaseModel):
    name: str
    internal_name: str
    level: int
    max_level: int
    is_upgrading: bool
    production: float
    storage: Optional[float]
    next_cost: Optional[BuildingCost]
    upgrade_duration: Optional[int]
    upgrade_end_time: Optional[datetime.datetime]

class BuildingUpgradeResponse(BaseModel):
    message: str
    resources: ResourceBalances
    queue: List[BuildingUpgrade]

Village.model_rebuild()
BuildingUpgrade.model_rebuild()
