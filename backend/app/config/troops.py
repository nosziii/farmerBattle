from __future__ import annotations

from typing import Dict, List, TypedDict


class TroopDefinition(TypedDict):
    name: str
    attack: int
    defense: int
    speed: int
    carry_capacity: int
    wood_cost: int
    clay_cost: int
    iron_cost: int
    training_time: int
    requirements: Dict[str, int]


TROOP_DEFINITIONS: List[TroopDefinition] = [
    {
        "name": "Militia",
        "attack": 8,
        "defense": 5,
        "speed": 12,
        "carry_capacity": 40,
        "wood_cost": 50,
        "clay_cost": 40,
        "iron_cost": 30,
        "training_time": 5,
        "requirements": {
            "barracks": 1,
        },
    },
    {
        "name": "Spearman",
        "attack": 12,
        "defense": 10,
        "speed": 11,
        "carry_capacity": 45,
        "wood_cost": 60,
        "clay_cost": 50,
        "iron_cost": 35,
        "training_time": 6,
        "requirements": {
            "barracks": 2,
            "smithy": 1,
        },
    },
    {
        "name": "Swordsman",
        "attack": 18,
        "defense": 18,
        "speed": 10,
        "carry_capacity": 35,
        "wood_cost": 80,
        "clay_cost": 70,
        "iron_cost": 50,
        "training_time": 8,
        "requirements": {
            "barracks": 3,
            "smithy": 2,
        },
    },
    {
        "name": "Archer",
        "attack": 20,
        "defense": 12,
        "speed": 13,
        "carry_capacity": 30,
        "wood_cost": 90,
        "clay_cost": 60,
        "iron_cost": 45,
        "training_time": 7,
        "requirements": {
            "barracks": 4,
            "training_ground": 1,
        },
    },
    {
        "name": "Cavalry",
        "attack": 45,
        "defense": 20,
        "speed": 18,
        "carry_capacity": 80,
        "wood_cost": 200,
        "clay_cost": 160,
        "iron_cost": 140,
        "training_time": 12,
        "requirements": {
            "stable": 2,
            "smithy": 3,
        },
    },
]
