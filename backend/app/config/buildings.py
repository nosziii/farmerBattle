"""
Building configuration for Farmer Battle.

The values defined here are intentionally declarative so that game designers can
balance costs, durations, and growth curves without touching the main backend
logic.  Keep the following in mind when tweaking the numbers:

* max_level      – the highest level a building may reach (inclusive).
* base_cost      – the starting resource cost for level 2 (level 1 exists at game
                   start so its cost is always considered zero).
* cost_growth    – multiplicative growth applied per level. Raising this number
                   makes higher levels exponentially more expensive.
* base_time_s    – training time (in seconds) for the level 2 upgrade. Set this
                   low in development environments so upgrades complete quickly.
* time_growth    – multiplicative growth for upgrade durations.
* base_production – hourly production (or other effect) at level 1.
* production_growth – multiplicative growth applied per level.
* base_storage   – maximum storable amount at level 1 (set to None if the
                   building does not influence storage).
* storage_growth – multiplicative growth applied per level storage.

If you need fine‑tuned control per level, feel free to replace the call to
``generate_levels`` with a manually curated list – the rest of the backend only
expects the ``levels`` list to contain dictionaries shaped like:

    {
        "level": 7,
        "cost": {"wood": 123, "clay": 234, "iron": 345},
        "duration": 120,  # seconds
        "production": 42.0,
        "storage": 15000.0,
    }
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import math


RESOURCE_FIELDS = ("wood", "clay", "iron")


@dataclass(frozen=True)
class BuildingLevel:
    """Single building level entry derived from the config."""

    level: int
    cost: Dict[str, int]
    duration: int  # seconds
    production: float
    storage: Optional[float]


def _round_cost(value: float) -> int:
    """Consistent rounding strategy for resource costs."""
    return max(0, int(round(value)))


def _generate_levels(
    *,
    max_level: int,
    base_cost: Dict[str, float],
    cost_growth: float,
    base_time_s: float,
    time_growth: float,
    base_production: float,
    production_growth: float,
    base_storage: Optional[float],
    storage_growth: Optional[float],
) -> List[BuildingLevel]:
    """Generate per-level definitions using easily tweakable growth curves."""

    levels: List[BuildingLevel] = []

    for level in range(1, max_level + 1):
        if level == 1:
            # Level 1 represents the initial state of the village.
            cost = {resource: 0 for resource in RESOURCE_FIELDS}
            duration = 0
            production = base_production
            storage = base_storage
        else:
            exponent = level - 1
            cost = {
                resource: _round_cost(base_cost[resource] * (cost_growth ** (exponent - 1)))
                for resource in RESOURCE_FIELDS
            }
            duration = max(1, int(round(base_time_s * (time_growth ** (exponent - 1)))))
            production = base_production * (production_growth ** exponent)
            storage = (
                base_storage * (storage_growth ** exponent)
                if base_storage is not None and storage_growth is not None
                else base_storage
            )

        levels.append(
            BuildingLevel(
                level=level,
                cost=cost,
                duration=duration,
                production=production,
                storage=storage,
            )
        )

    return levels


def _as_dict(levels: List[BuildingLevel]) -> List[Dict[str, object]]:
    """Convert dataclass instances to plain dictionaries for JSON serialisation."""
    return [
        {
            "level": level.level,
            "cost": level.cost,
            "duration": level.duration,
            "production": level.production,
            "storage": level.storage,
        }
        for level in levels
    ]


# --------------------------------------------------------------------------- #
# Building configuration
# --------------------------------------------------------------------------- #

BUILDING_CONFIG: Dict[str, Dict[str, object]] = {
    "wood_mill": {
        "display_name": "Wood Mill",
        "resource_field": "wood",
        "max_level": 45,
        "levels": _as_dict(
            _generate_levels(
                max_level=45,
                base_cost={"wood": 60, "clay": 40, "iron": 20},
                cost_growth=1.35,
                base_time_s=20,  # tweak this while developing to speed up upgrades
                time_growth=1.22,
                base_production=10.0,
                production_growth=1.18,
                base_storage=5000.0,
                storage_growth=1.28,
            )
        ),
    },
    "clay_pit": {
        "display_name": "Clay Pit",
        "resource_field": "clay",
        "max_level": 45,
        "levels": _as_dict(
            _generate_levels(
                max_level=45,
                base_cost={"wood": 40, "clay": 60, "iron": 20},
                cost_growth=1.32,
                base_time_s=25,
                time_growth=1.20,
                base_production=10.0,
                production_growth=1.17,
                base_storage=5000.0,
                storage_growth=1.26,
            )
        ),
    },
    "iron_mine": {
        "display_name": "Iron Mine",
        "resource_field": "iron",
        "max_level": 45,
        "levels": _as_dict(
            _generate_levels(
                max_level=45,
                base_cost={"wood": 80, "clay": 80, "iron": 40},
                cost_growth=1.33,
                base_time_s=30,
                time_growth=1.23,
                base_production=10.0,
                production_growth=1.19,
                base_storage=5000.0,
                storage_growth=1.30,
            )
        ),
    },
}


def get_building_definition(building: str) -> Dict[str, object]:
    """Return the immutable configuration block for the requested building."""
    if building not in BUILDING_CONFIG:
        raise KeyError(f"Unknown building '{building}'")
    return BUILDING_CONFIG[building]


def get_level_definition(building: str, level: int) -> Dict[str, object]:
    """Fetch the configuration for a specific building level."""
    definition = get_building_definition(building)
    levels = definition["levels"]  # type: ignore[index]
    max_level = definition["max_level"]  # type: ignore[assignment]

    if level < 1 or level > max_level:
        raise ValueError(f"Level {level} outside the allowed range for {building} (1–{max_level})")

    # levels list is 0-indexed while the levels themselves start at 1
    return levels[level - 1]


def get_next_level_definition(building: str, current_level: int) -> Optional[Dict[str, object]]:
    """Return the next level configuration if the building can still be upgraded."""
    definition = get_building_definition(building)
    max_level = definition["max_level"]  # type: ignore[assignment]
    next_level = current_level + 1
    if next_level > max_level:
        return None
    return get_level_definition(building, next_level)
