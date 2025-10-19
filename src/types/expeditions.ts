export type ExpeditionStatus = 'outbound' | 'returning' | 'completed';

export interface ExpeditionTroopSummary {
  troop_id: number;
  name: string;
  sent: number;
  returning: number;
  casualties: number;
}

export interface ExpeditionSummary {
  id: number;
  village_id: number;
  barbarian_village_id: number;
  barbarian_name: string;
  barbarian_level: number;
  status: ExpeditionStatus;
  success: boolean;
  distance: number;
  travel_seconds: number;
  created_at: string;
  departed_at: string;
  arrive_at: string;
  resolved_at: string | null;
  return_at: string | null;
  completed_at: string | null;
  loot: Record<string, number>;
  troops: ExpeditionTroopSummary[];
  battle_report: string | null;
}

export interface ExpeditionListResponse {
  active: ExpeditionSummary[];
  completed: ExpeditionSummary[];
}

export interface ExpeditionTroopOrder {
  troop_id: number;
  quantity: number;
}

export interface ExpeditionCreateRequest {
  barbarian_village_id: number;
  troops: ExpeditionTroopOrder[];
}
