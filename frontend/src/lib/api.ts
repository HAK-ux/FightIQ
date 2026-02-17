import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface Fighter {
  id: number;
  name: string;
  nickname: string | null;
  weight_class: string;
  wins: number;
  losses: number;
  draws: number;
  height_cm: number | null;
  reach_cm: number | null;
  stance: string | null;
  stats: FighterStats | null;
}

export interface FighterStats {
  sig_strikes_landed_per_min: number;
  sig_strikes_absorbed_per_min: number;
  striking_accuracy: number;
  striking_defense: number;
  takedown_avg_per_fight: number;
  takedown_accuracy: number;
  takedown_defense: number;
  submission_avg_per_fight?: number;
}

export interface MatchupPrediction {
  fighter_a_win_probability: number;
  fighter_b_win_probability: number;
  confidence: string;
  method: string;
  deltas: any;
  fighter_a: Fighter;
  fighter_b: Fighter;
  breakdown?: string;
  fighter_a_win_condition?: string;
  fighter_b_win_condition?: string;
  from_cache?: boolean;
}

// API Functions
export const fightersApi = {
  getAll: (params?: { weight_class?: string; skip?: number; limit?: number }) =>
    api.get<Fighter[]>('/fighters', { params }),
  
  getById: (id: number) =>
    api.get<Fighter>(`/fighters/${id}`),
  
  search: (query: string) =>
    api.get<Fighter[]>('/fighters/search', { params: { q: query } }),
  
  getWeightClasses: () =>
    api.get<string[]>('/weight-classes'),
};

export const matchupApi = {
  predict: (fighterAId: number, fighterBId: number) =>
    api.get<MatchupPrediction>(`/matchup/${fighterAId}/vs/${fighterBId}`),
  
  getBreakdown: (fighterAId: number, fighterBId: number) =>
    api.get<MatchupPrediction>(`/matchup/${fighterAId}/vs/${fighterBId}/breakdown`),
};