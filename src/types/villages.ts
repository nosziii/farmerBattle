export interface PlayerVillageOwner {
  id: number;
  username: string;
}

export interface PlayerVillage {
  id: number;
  name: string;
  score: number;
  user_id: number;
  owner: PlayerVillageOwner;
  [key: string]: unknown;
}
