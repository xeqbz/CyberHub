import { apiRequest } from "@/src/shared/api/client";
import type { TeamListItem } from "@/src/shared/api/teams";
import type { TournamentListItem } from "@/src/shared/api/tournaments";

export type MatchStatus = string;

export type MatchListItem = {
  id: number;
  tournament_id: number;
  home_team_id: number;
  away_team_id: number;
  status: MatchStatus;
  scheduled_at: string | null;
  completed_at: string | null;
  stage: string;
  round_number: number;
  bracket_position: number;
  home_score: number | null;
  away_score: number | null;
  winner_team_id: number | null;
  result_confirmed_by_id: number | null;
  created_at: string;
  updated_at: string;
};

export type MatchRead = {
  id: number;
  tournament_id: number;
  home_team_id: number;
  away_team_id: number;
  status: MatchStatus;
  scheduled_at: string | null;
  completed_at: string | null;
  stage: string;
  round_number: number;
  bracket_position: number;
  home_score: number | null;
  away_score: number | null;
  winner_team_id: number | null;
  result_confirmed_by_id: number | null;
  created_at: string;
  updated_at: string;
  tournament: TournamentListItem;
  home_team: TeamListItem;
  away_team: TeamListItem;
  winner_team: TeamListItem | null;
};

export type CreateMatchPayload = {
  tournament_id: number;
  home_team_id: number;
  away_team_id: number;
  scheduled_at?: string | null;
  stage?: string;
  round_number?: number;
  bracket_position?: number;
};

export type UpdateMatchPayload = {
  status?: string;
  scheduled_at?: string | null;
  stage?: string;
  round_number?: number;
  bracket_position?: number;
  home_score?: number | null;
  away_score?: number | null;
  winner_team_id?: number | null;
};

export type UpdateMatchScorePayload = {
  home_score: number;
  away_score: number;
  winner_team_id?: number | null;
};

export async function listMatches(): Promise<MatchListItem[]> {
  return apiRequest<MatchListItem[]>("/matches");
}

export async function getMatch(matchId: number): Promise<MatchRead> {
  return apiRequest<MatchRead>(`/matches/${matchId}`);
}

export async function listTournamentMatches(
  tournamentId: number,
): Promise<MatchRead[]> {
  return apiRequest<MatchRead[]>(`/matches/tournament/${tournamentId}`);
}

export async function createMatch(
  payload: CreateMatchPayload,
  token: string,
): Promise<MatchRead> {
  return apiRequest<MatchRead>("/matches", {
    method: "POST",
    body: payload,
    token,
  });
}

export async function updateMatch(
  matchId: number,
  payload: UpdateMatchPayload,
  token: string,
): Promise<MatchRead> {
  return apiRequest<MatchRead>(`/matches/${matchId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function updateMatchScore(
  matchId: number,
  payload: UpdateMatchScorePayload,
  token: string,
): Promise<MatchRead> {
  return apiRequest<MatchRead>(`/matches/${matchId}/score`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function deleteMatch(
  matchId: number,
  token: string,
): Promise<void> {
  await apiRequest<void>(`/matches/${matchId}`, {
    method: "DELETE",
    token,
  });
}
