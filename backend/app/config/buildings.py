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
from typing import Dict, List, Optional, Sequence
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


def _build_config(
    *,
    display_name: str,
    icon: str,
    category: str,
    description: str,
    order: int,
    resource_field: Optional[str],
    max_level: int,
    levels: List[BuildingLevel],
    requirements: Optional[Sequence[Dict[str, int]]] = None,
    effects: Optional[Sequence[str]] = None,
    unlocks: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    """Helper to create the declarative building configuration blocks."""

    return {
        "display_name": display_name,
        "icon": icon,
        "category": category,
        "description": description,
        "order": order,
        "resource_field": resource_field,
        "max_level": max_level,
        "requirements": list(requirements or []),
        "effects": list(effects or []),
        "unlocks": list(unlocks or []),
        "levels": _as_dict(levels),
    }


BUILDING_CONFIG: Dict[str, Dict[str, object]] = {
    "wood_mill": _build_config(
        display_name="Wood Mill",
        icon="🪓",
        category="Resources",
        description="Harvests timber from the nearby forests. Each upgrade improves hourly wood production and storage.",
        order=10,
        resource_field="wood",
        max_level=45,
        effects=[
            "Increases hourly wood production.",
            "Adds a small amount of storage for wood.",
        ],
        levels=_generate_levels(
            max_level=45,
            base_cost={"wood": 60, "clay": 40, "iron": 20},
            cost_growth=1.35,
            base_time_s=20,
            time_growth=1.22,
            base_production=10.0,
            production_growth=1.18,
            base_storage=5000.0,
            storage_growth=1.28,
        ),
    ),
    "clay_pit": _build_config(
        display_name="Clay Pit",
        icon="🧱",
        category="Resources",
        description="Expands the mud quarries. Clay is vital for most upgrades and fortifications.",
        order=12,
        resource_field="clay",
        max_level=45,
        effects=[
            "Raises hourly clay production.",
            "Adds a modest amount of clay storage.",
        ],
        levels=_generate_levels(
            max_level=45,
            base_cost={"wood": 40, "clay": 60, "iron": 20},
            cost_growth=1.32,
            base_time_s=25,
            time_growth=1.20,
            base_production=10.0,
            production_growth=1.17,
            base_storage=5000.0,
            storage_growth=1.26,
        ),
    ),
    "iron_mine": _build_config(
        display_name="Iron Mine",
        icon="⛏️",
        category="Resources",
        description="Deepens the iron veins under the village. Essential for forging weapons and armor.",
        order=14,
        resource_field="iron",
        max_level=45,
        effects=[
            "Boosts hourly iron production.",
            "Adds a touch of iron storage.",
        ],
        levels=_generate_levels(
            max_level=45,
            base_cost={"wood": 80, "clay": 80, "iron": 40},
            cost_growth=1.33,
            base_time_s=30,
            time_growth=1.23,
            base_production=10.0,
            production_growth=1.19,
            base_storage=5000.0,
            storage_growth=1.30,
        ),
    ),
    "town_hall": _build_config(
        display_name="Town Hall",
        icon="🏛️",
        category="Infrastructure",
        description="Administrative heart of the village. Coordinates every construction effort.",
        order=1,
        resource_field="gold",
        max_level=30,
        effects=[
            "Generates gold used for premium actions.",
            "Reduces build coordination overhead and unlocks advanced infrastructure buildings.",
        ],
        unlocks=[
            "Unlocks Barracks, Market, Warehouse and Farm upgrades.",
        ],
        levels=_generate_levels(
            max_level=30,
            base_cost={"wood": 90, "clay": 60, "iron": 30},
            cost_growth=1.42,
            base_time_s=35,
            time_growth=1.28,
            base_production=1.0,
            production_growth=1.22,
            base_storage=50.0,
            storage_growth=1.35,
        ),
    ),
    "warehouse": _build_config(
        display_name="Warehouse",
        icon="📦",
        category="Infrastructure",
        description="Stores resources safely behind thick walls and sturdy locks.",
        order=3,
        resource_field=None,
        max_level=30,
        requirements=[{"building": "town_hall", "level": 2}],
        effects=[
            "Adds storage capacity for all resources.",
        ],
        unlocks=[
            "Supports Market and Barracks expansion.",
        ],
        levels=_generate_levels(
            max_level=30,
            base_cost={"wood": 80, "clay": 90, "iron": 40},
            cost_growth=1.36,
            base_time_s=30,
            time_growth=1.24,
            base_production=0.0,
            production_growth=1.0,
            base_storage=2500.0,
            storage_growth=1.35,
        ),
    ),
    "farm": _build_config(
        display_name="Farm",
        icon="🌾",
        category="Infrastructure",
        description="Feeds your population and keeps troops supplied.",
        order=4,
        resource_field=None,
        max_level=30,
        requirements=[{"building": "town_hall", "level": 2}],
        effects=[
            "Raises population capacity (future feature).",
            "Keeps troops provisioned.",
        ],
        unlocks=[
            "Supports Barracks and Stable development.",
        ],
        levels=_generate_levels(
            max_level=30,
            base_cost={"wood": 70, "clay": 40, "iron": 30},
            cost_growth=1.32,
            base_time_s=25,
            time_growth=1.20,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "barracks": _build_config(
        display_name="Barracks",
        icon="🛡️",
        category="Military",
        description="Trains infantry forces to defend and expand your domain.",
        order=20,
        resource_field=None,
        max_level=25,
        requirements=[
            {"building": "town_hall", "level": 3},
            {"building": "warehouse", "level": 3},
            {"building": "farm", "level": 2},
        ],
        effects=[
            "Allows recruitment of basic infantry units.",
            "Shortens infantry training time with each level (future feature).",
        ],
        unlocks=[
            "Required for Smithy, Training Ground, and Stable.",
        ],
        levels=_generate_levels(
            max_level=25,
            base_cost={"wood": 200, "clay": 170, "iron": 90},
            cost_growth=1.35,
            base_time_s=40,
            time_growth=1.26,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "smithy": _build_config(
        display_name="Smithy",
        icon="⚒️",
        category="Military",
        description="Forges improved weaponry and armour for your forces.",
        order=22,
        resource_field=None,
        max_level=20,
        requirements=[
            {"building": "town_hall", "level": 5},
            {"building": "barracks", "level": 3},
        ],
        effects=[
            "Enables research of advanced infantry and siege equipment.",
        ],
        unlocks=[
            "Stable, Workshop, Forge upgrades require the smithy.",
        ],
        levels=_generate_levels(
            max_level=20,
            base_cost={"wood": 220, "clay": 200, "iron": 160},
            cost_growth=1.38,
            base_time_s=45,
            time_growth=1.30,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "training_ground": _build_config(
        display_name="Training Ground",
        icon="🥁",
        category="Military",
        description="Specialised fields where infantry drills hone combat readiness.",
        order=23,
        resource_field=None,
        max_level=15,
        requirements=[
            {"building": "barracks", "level": 5},
            {"building": "farm", "level": 5},
        ],
        effects=[
            "Further reduces infantry training time (future feature).",
            "Adds morale bonuses to defending troops.",
        ],
        unlocks=[
            "Prerequisite for elite infantry research.",
        ],
        levels=_generate_levels(
            max_level=15,
            base_cost={"wood": 260, "clay": 210, "iron": 140},
            cost_growth=1.33,
            base_time_s=50,
            time_growth=1.28,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "stable": _build_config(
        display_name="Stable",
        icon="🐎",
        category="Military",
        description="Houses and trains cavalry. Faster troops mean greater reach.",
        order=24,
        resource_field=None,
        max_level=20,
        requirements=[
            {"building": "barracks", "level": 10},
            {"building": "smithy", "level": 5},
            {"building": "farm", "level": 5},
        ],
        effects=[
            "Enables recruitment of cavalry units.",
        ],
        unlocks=[
            "Prerequisite for cavalry technologies.",
        ],
        levels=_generate_levels(
            max_level=20,
            base_cost={"wood": 260, "clay": 200, "iron": 270},
            cost_growth=1.34,
            base_time_s=55,
            time_growth=1.30,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "workshop": _build_config(
        display_name="Workshop",
        icon="🏗️",
        category="Military",
        description="Builds siege engines capable of toppling rival walls.",
        order=25,
        resource_field=None,
        max_level=15,
        requirements=[
            {"building": "barracks", "level": 7},
            {"building": "smithy", "level": 7},
            {"building": "market", "level": 5},
        ],
        effects=[
            "Allows recruitment of rams and catapults.",
        ],
        unlocks=[
            "Works with Forge for advanced siege gear.",
        ],
        levels=_generate_levels(
            max_level=15,
            base_cost={"wood": 300, "clay": 280, "iron": 320},
            cost_growth=1.36,
            base_time_s=60,
            time_growth=1.32,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "forge": _build_config(
        display_name="Forge",
        icon="🔥",
        category="Military",
        description="Experimental foundry for master smiths to craft elite weaponry.",
        order=26,
        resource_field=None,
        max_level=15,
        requirements=[
            {"building": "smithy", "level": 8},
            {"building": "barracks", "level": 8},
        ],
        effects=[
            "Unlocks upgrades for elite troops (future feature).",
        ],
        unlocks=[
            "Required for Academy weapon research.",
        ],
        levels=_generate_levels(
            max_level=15,
            base_cost={"wood": 320, "clay": 300, "iron": 360},
            cost_growth=1.34,
            base_time_s=65,
            time_growth=1.32,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "market": _build_config(
        display_name="Market",
        icon="⚖️",
        category="Economy",
        description="Traders gather here to exchange goods with allies and distant villages.",
        order=30,
        resource_field=None,
        max_level=25,
        requirements=[
            {"building": "town_hall", "level": 3},
            {"building": "warehouse", "level": 4},
        ],
        effects=[
            "Increases merchant capacity and trade routes (future feature).",
        ],
        unlocks=[
            "Supports Workshop logistics.",
            "Enables diplomacy options via the Embassy.",
        ],
        levels=_generate_levels(
            max_level=25,
            base_cost={"wood": 200, "clay": 180, "iron": 120},
            cost_growth=1.31,
            base_time_s=35,
            time_growth=1.25,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "embassy": _build_config(
        display_name="Embassy",
        icon="🤝",
        category="Diplomacy",
        description="Manages treaties and alliances with neighbouring tribes.",
        order=35,
        resource_field=None,
        max_level=15,
        requirements=[
            {"building": "town_hall", "level": 4},
            {"building": "market", "level": 4},
        ],
        effects=[
            "Unlocks tribe features and diplomacy tools (future feature).",
        ],
        unlocks=[
            "Enables shared technology projects.",
        ],
        levels=_generate_levels(
            max_level=15,
            base_cost={"wood": 250, "clay": 200, "iron": 200},
            cost_growth=1.33,
            base_time_s=40,
            time_growth=1.28,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "library": _build_config(
        display_name="Library",
        icon="📚",
        category="Research",
        description="Scholars document and share battle-tested strategies.",
        order=40,
        resource_field=None,
        max_level=20,
        requirements=[
            {"building": "town_hall", "level": 7},
            {"building": "smithy", "level": 5},
        ],
        effects=[
            "Unlocks technology research (future feature).",
        ],
        unlocks=[
            "Required for the Academy and Sanctuary.",
        ],
        levels=_generate_levels(
            max_level=20,
            base_cost={"wood": 180, "clay": 180, "iron": 220},
            cost_growth=1.32,
            base_time_s=45,
            time_growth=1.29,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "academy": _build_config(
        display_name="Academy",
        icon="🎓",
        category="Research",
        description="Strategists gather here to plan large-scale conquests.",
        order=45,
        resource_field=None,
        max_level=10,
        requirements=[
            {"building": "town_hall", "level": 12},
            {"building": "library", "level": 7},
            {"building": "smithy", "level": 10},
        ],
        effects=[
            "Allows recruitment of nobles for conquering villages.",
        ],
        unlocks=[
            "Unlocks the Noble Estate.",
        ],
        levels=_generate_levels(
            max_level=10,
            base_cost={"wood": 400, "clay": 400, "iron": 500},
            cost_growth=1.38,
            base_time_s=80,
            time_growth=1.35,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "noble_house": _build_config(
        display_name="Noble Estate",
        icon="👑",
        category="Conquest",
        description="Houses nobles who can claim rival villages for your tribe.",
        order=46,
        resource_field=None,
        max_level=5,
        requirements=[
            {"building": "academy", "level": 1},
            {"building": "market", "level": 10},
        ],
        effects=[
            "Produces nobles used to conquer enemy villages (future feature).",
        ],
        unlocks=[
            "Required for late-game expansion.",
        ],
        levels=_generate_levels(
            max_level=5,
            base_cost={"wood": 600, "clay": 600, "iron": 700},
            cost_growth=1.40,
            base_time_s=120,
            time_growth=1.40,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "wall": _build_config(
        display_name="Wall",
        icon="🧱",
        category="Defence",
        description="Encircles the village with stone ramparts to slow attackers.",
        order=50,
        resource_field=None,
        max_level=25,
        requirements=[
            {"building": "town_hall", "level": 2},
            {"building": "warehouse", "level": 3},
        ],
        effects=[
            "Improves village defence rating (future feature).",
        ],
        unlocks=[
            "Prerequisite for Watchtower construction.",
        ],
        levels=_generate_levels(
            max_level=25,
            base_cost={"wood": 100, "clay": 200, "iron": 100},
            cost_growth=1.34,
            base_time_s=35,
            time_growth=1.26,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "watchtower": _build_config(
        display_name="Watchtower",
        icon="🔭",
        category="Defence",
        description="Scouts keep watch for hostile armies, granting valuable warning.",
        order=52,
        resource_field=None,
        max_level=25,
        requirements=[
            {"building": "wall", "level": 5},
            {"building": "town_hall", "level": 6},
        ],
        effects=[
            "Increases detection range and incoming attack info (future feature).",
        ],
        unlocks=[
            "Works with Hospital to reduce losses.",
        ],
        levels=_generate_levels(
            max_level=25,
            base_cost={"wood": 150, "clay": 220, "iron": 160},
            cost_growth=1.33,
            base_time_s=40,
            time_growth=1.27,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "hospital": _build_config(
        display_name="Hospital",
        icon="⚕️",
        category="Support",
        description="Treats wounded warriors so they can return to battle.",
        order=55,
        resource_field=None,
        max_level=20,
        requirements=[
            {"building": "town_hall", "level": 8},
            {"building": "farm", "level": 6},
            {"building": "warehouse", "level": 6},
        ],
        effects=[
            "Heals a portion of lost troops after battles (future feature).",
        ],
        unlocks=[
            "Synergises with Watchtower intelligence.",
        ],
        levels=_generate_levels(
            max_level=20,
            base_cost={"wood": 200, "clay": 220, "iron": 250},
            cost_growth=1.32,
            base_time_s=45,
            time_growth=1.30,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
    "sanctuary": _build_config(
        display_name="Sanctuary",
        icon="🕍",
        category="Faith",
        description="A sacred ground inspiring loyalty and protecting nobles.",
        order=60,
        resource_field=None,
        max_level=10,
        requirements=[
            {"building": "town_hall", "level": 10},
            {"building": "library", "level": 8},
        ],
        effects=[
            "Boosts noble loyalty and defensive morale (future feature).",
        ],
        unlocks=[
            "Enhances Noble Estate effectiveness.",
        ],
        levels=_generate_levels(
            max_level=10,
            base_cost={"wood": 300, "clay": 320, "iron": 350},
            cost_growth=1.35,
            base_time_s=60,
            time_growth=1.35,
            base_production=0.0,
            production_growth=1.0,
            base_storage=None,
            storage_growth=None,
        ),
    ),
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
