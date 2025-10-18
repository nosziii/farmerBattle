export interface BuildingCost {
  wood: number;
  clay: number;
  iron: number;
}

export interface BuildingRequirement {
  building: string;
  display_name: string;
  required_level: number;
  current_level: number;
  met: boolean;
}

export interface BuildingStatus {
  name: string;
  internal_name: string;
  category: string;
  description: string;
  icon: string;
  level: number;
  max_level: number;
  is_upgrading: boolean;
  production: number;
  storage: number | null;
  resource_field?: string | null;
  next_cost: BuildingCost | null;
  upgrade_duration: number | null;
  upgrade_end_time: string | null;
  requirements: BuildingRequirement[];
  effects: string[];
  unlocks: string[];
  available: boolean;
  order: number;
}

export interface BuildingQueueItem {
  id: number;
  village_id: number;
  building: string;
  target_level: number;
  start_time: string;
  end_time: string;
}
