import { apiRequest } from "@/src/shared/api/client";
import type { TeamListItem, UserSummary } from "@/src/shared/api/teams";

export type TournamentStatus =
  | "DRAFT"
  | "REGISTRATION_OPEN"
  | "REGISTRATION_CLOSED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED";

export type TournamentListItem = {
  id: number;
  name: string;
  description: string | null;
  format: string;
  discipline: string;
  rules: string;
  bracket_settings: Record<string, unknown> | null;
  status: TournamentStatus;
  owner_id: number;
  max_teams: number;
  starts_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TournamentParticipant = {
  id: number;
  tournament_id: number;
  team_id: number;
  status: "PENDING" | "APPROVED" | "REJECTED";
  decided_by_id: number | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
  team: TeamListItem;
};

export type TournamentRead = {
  id: number;
  name: string;
  description: string | null;
  format: string;
  discipline: string;
  rules: string;
  bracket_settings: Record<string, unknown> | null;
  status: TournamentStatus;
  owner_id: number;
  max_teams: number;
  starts_at: string | null;
  created_at: string;
  updated_at: string;
  owner: UserSummary;
  participants: TournamentParticipant[];
};

export type CreateTournamentPayload = {
  name: string;
  description?: string;
  format?: string;
  discipline?: string;
  rules?: string;
  bracket_settings?: Record<string, unknown> | null;
  status?: TournamentStatus;
  max_teams?: number;
  starts_at?: string | null;
};

export type UpdateTournamentPayload = Partial<CreateTournamentPayload>;

export async function listTournaments(): Promise<TournamentListItem[]> {
  return apiRequest<TournamentListItem[]>("/tournaments");
}

export async function getTournament(tournamentId: number): Promise<TournamentRead> {
  return apiRequest<TournamentRead>(`/tournaments/${tournamentId}`);
}

export async function createTournament(
  payload: CreateTournamentPayload,
  token: string,
): Promise<TournamentRead> {
  return apiRequest<TournamentRead>("/tournaments", {
    method: "POST",
    body: payload,
    token,
  });
}

export async function updateTournament(
  tournamentId: number,
  payload: UpdateTournamentPayload,
  token: string,
): Promise<TournamentRead> {
  return apiRequest<TournamentRead>(`/tournaments/${tournamentId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function registerTeamForTournament(
  tournamentId: number,
  teamId: number,
  token: string,
): Promise<TournamentParticipant> {
  return apiRequest<TournamentParticipant>(`/tournaments/${tournamentId}/participants`, {
    method: "POST",
    body: { team_id: teamId },
    token,
  });
}

export async function removeTeamFromTournament(
  tournamentId: number,
  teamId: number,
  token: string,
): Promise<void> {
  await apiRequest<void>(`/tournaments/${tournamentId}/participants/${teamId}`, {
    method: "DELETE",
    token,
  });
}

export async function reviewTournamentParticipant(
  tournamentId: number,
  teamId: number,
  participantStatus: "APPROVED" | "REJECTED",
  token: string,
): Promise<TournamentParticipant> {
  return apiRequest<TournamentParticipant>(
    `/tournaments/${tournamentId}/participants/${teamId}`,
    {
      method: "PATCH",
      body: { status: participantStatus },
      token,
    },
  );
}
