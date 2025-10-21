export interface AdminResourceBalances {
  wood: number;
  clay: number;
  iron: number;
  gold: number;
}

export interface AdminUser {
  id: number;
  username: string;
  is_active: boolean;
  village_ids: number[];
}

export interface AdminUserCreate {
  username: string;
  password: string;
}

export interface AdminMapPosition {
  x: number;
  y: number;
}

export interface AdminVillageSummary {
  id: number;
  name: string;
  user_id: number;
  user_name: string;
  resources: AdminResourceBalances;
  productions: AdminResourceBalances;
  tile: AdminMapPosition | null;
}

export interface AdminVillageDetail extends AdminVillageSummary {
  building_levels: Record<string, number>;
}

export interface AdminVillageUpdate {
  name?: string;
  wood?: number;
  clay?: number;
  iron?: number;
  gold?: number;
  wood_mill_level?: number;
  clay_pit_level?: number;
  iron_mine_level?: number;
  town_hall_level?: number;
  warehouse_level?: number;
}

export interface AdminVillageCreate {
  user_id: number;
  name: string;
}

export interface AdminAssignTileRequest {
  village_id: number;
  x: number;
  y: number;
  force?: boolean;
}

export interface AdminVillageTroop {
  id: number;
  village_id: number;
  troop_id: number;
  quantity: number;
  troop: AdminTroop;
}

export interface AdminVillageTroopUpdate {
  troop_id: number;
  quantity: number;
}

export interface AdminVillageTroopUpdatePayload {
  troops: AdminVillageTroopUpdate[];
}

export interface AdminTroopRequirement {
  building: string;
  level: number;
}

export interface AdminTroop {
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
  requirements: AdminTroopRequirement[];
}

export interface AdminTroopCreate {
  name: string;
  attack: number;
  defense: number;
  speed: number;
  carry_capacity: number;
  wood_cost: number;
  clay_cost: number;
  iron_cost: number;
  training_time: number;
  requirements: Record<string, number>;
}

export interface AdminTroopUpdate {
  name?: string;
  attack?: number;
  defense?: number;
  speed?: number;
  carry_capacity?: number;
  wood_cost?: number;
  clay_cost?: number;
  iron_cost?: number;
  training_time?: number;
  requirements?: Record<string, number>;
}
