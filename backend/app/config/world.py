"""
World and map configuration for Farmer Battle.

The configuration lives here so that gameplay designers can tweak map layout,
barbarian density, and their growth behaviour without touching the core logic.
All time-based values are expressed in minutes to stay close to the in-game
terminology (one map tile equals one minute of travel by design).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class BarbarianGrowthConfig:
    """Controls how barbarian villages develop over time."""

    growth_interval_minutes: int = 120  # add warriors every 2 hours
    level_up_interval_minutes: int = 720  # level up roughly every 12 hours
    warriors_per_growth_base: int = 5  # flat addition per growth tick
    warriors_per_growth_per_level: int = 3  # extra warriors scaled by level
    warriors_per_level_up: int = 25  # bonus warriors granted on level-up
    max_level: int = 20


@dataclass(frozen=True)
class BarbarianConfig:
    """Bundled barbarian village tuning knobs."""

    density: float = 0.04  # 4% of map tiles host a barbarian village
    level_weights: Dict[int, float] = field(
        default_factory=lambda: {
            1: 0.55,
            2: 0.25,
            3: 0.12,
            4: 0.08,
        }
    )
    warrior_ranges: Dict[int, Tuple[int, int]] = field(
        default_factory=lambda: {
            1: (10, 25),
            2: (26, 45),
            3: (46, 70),
            4: (71, 100),
        }
    )
    growth: BarbarianGrowthConfig = field(default_factory=BarbarianGrowthConfig)


@dataclass(frozen=True)
class WorldConfig:
    """Top-level world settings."""

    width: int = 50
    height: int = 50
    barbarian: BarbarianConfig = field(default_factory=BarbarianConfig)


WORLD_CONFIG = WorldConfig()
"""Expose a single configuration instance for the rest of the backend."""

