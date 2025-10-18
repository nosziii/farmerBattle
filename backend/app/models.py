from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Literal, Dict
import datetime

class UserBase(BaseModel):
    username: str
    model_config = ConfigDict(from_attributes=True)

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
    town_hall_level: int
    warehouse_level: int
    farm_level: int
    barracks_level: int
    smithy_level: int
    training_ground_level: int
    stable_level: int
    workshop_level: int
    forge_level: int
    market_level: int
    embassy_level: int
    library_level: int
    academy_level: int
    noble_house_level: int
    wall_level: int
    watchtower_level: int
    hospital_level: int
    sanctuary_level: int
    gold: float
    gold_production: float
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
    gold: float

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


class BuildingRequirementStatus(BaseModel):
    building: str
    display_name: str
    required_level: int
    current_level: int
    met: bool


class BuildingStatus(BaseModel):
    name: str
    internal_name: str
    category: str
    description: str
    icon: str
    level: int
    max_level: int
    is_upgrading: bool
    production: float
    storage: Optional[float]
    resource_field: Optional[str]
    next_cost: Optional[BuildingCost]
    upgrade_duration: Optional[int]
    upgrade_end_time: Optional[datetime.datetime]
    requirements: List[BuildingRequirementStatus]
    effects: List[str]
    unlocks: List[str]
    available: bool
    order: int
    model_config = ConfigDict(from_attributes=True)

class BuildingUpgradeResponse(BaseModel):
    message: str
    resources: ResourceBalances
    queue: List[BuildingUpgrade]

Village.model_rebuild()
BuildingUpgrade.model_rebuild()


class BarbarianVillage(BaseModel):
    id: int
    name: str
    level: int
    warriors: int
    last_growth_at: datetime.datetime
    last_level_up_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MapTile(BaseModel):
    x: int
    y: int
    type: Literal["empty", "player", "barbarian"]
    village: Optional[VillageResponse] = None
    barbarian: Optional[BarbarianVillage] = None


class MapOverview(BaseModel):
    width: int
    height: int
    tiles: List[MapTile]


class AdminUser(BaseModel):
    id: int
    username: str
    is_active: bool
    village_ids: List[int]


class AdminUserCreate(BaseModel):
    username: str
    password: str


class MapPosition(BaseModel):
    x: int
    y: int


class AdminVillageSummary(BaseModel):
    id: int
    name: str
    user_id: int
    user_name: str
    resources: ResourceBalances
    productions: ResourceBalances
    tile: Optional[MapPosition]


class AdminVillageDetail(AdminVillageSummary):
    building_levels: Dict[str, int]


class AdminVillageUpdate(BaseModel):
    name: Optional[str] = None
    wood: Optional[float] = None
    clay: Optional[float] = None
    iron: Optional[float] = None
    gold: Optional[float] = None
    wood_mill_level: Optional[int] = None
    clay_pit_level: Optional[int] = None
    iron_mine_level: Optional[int] = None
    town_hall_level: Optional[int] = None
    warehouse_level: Optional[int] = None


class AdminVillageCreate(BaseModel):
    user_id: int
    name: str


class AdminAssignVillageTile(BaseModel):
    village_id: int
    x: int
    y: int
    force: bool = False
