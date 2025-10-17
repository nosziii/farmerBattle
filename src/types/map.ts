export type TileType = 'empty' | 'player' | 'barbarian';

export interface UserSummary {
  username: string;
}

export interface VillageSummary {
  id: number;
  name: string;
  score: number;
  wood_mill_level: number;
  clay_pit_level: number;
  iron_mine_level: number;
  owner: UserSummary;
}

export interface BarbarianSummary {
  id: number;
  name: string;
  level: number;
  warriors: number;
}

export interface MapTile {
  x: number;
  y: number;
  type: TileType;
  village?: VillageSummary;
  barbarian?: BarbarianSummary;
}

export interface MapOverview {
  width: number;
  height: number;
  tiles: MapTile[];
}

