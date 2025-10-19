import type { BuildingRequirement } from './buildings';

export interface TroopRequirement {
  building: string;
  level: number;
}

export interface TroopDefinition {
  id: number;
  name: string;
  attack: number;
  defense: number;
  speed: number;
  carry_capacity: number;
  wood_cost: number;
  clay_cost: number;
  iron_cost: number;
  training_time: number;
  requirements: TroopRequirement[];
}

export interface AvailableTroop extends TroopDefinition {
  available: boolean;
  missing_requirements: BuildingRequirement[];
}
