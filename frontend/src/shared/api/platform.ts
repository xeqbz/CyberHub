import { apiRequest } from "@/src/shared/api/client";
import { API_URL } from "@/src/shared/config/api";
import type { MatchRead } from "@/src/shared/api/matches";
import type { CurrentUser } from "@/src/shared/api/users";

export type RankingUser = {
  id: number;
  username: string;
  rating: number;
  wins: number;
  losses: number;
  draws: number;
};

export type OverviewStats = {
  users: number;
  teams: number;
  tournaments: number;
  tournament_matches: number;
  ranked_matches: number;
  open_disputes: number;
  completed_matches: number;
};

export type TeamStats = {
  team_id: number;
  name: string;
  matches: number;
  wins: number;
  losses: number;
  draws: number;
};

export type PlayerStats = {
  user_id: number;
  username: string;
  rating: number;
  ranked_matches: number;
  wins: number;
  losses: number;
  draws: number;
  kills: number;
  deaths: number;
  assists: number;
  kda: number;
};

export type TournamentStats = {
  tournament_id: number;
  name: string;
  discipline: string;
  format: string;
  participants: number;
  matches: number;
  completed_matches: number;
};

export type NotificationRead = {
  id: number;
  user_id: number;
  title: string;
  message: string;
  is_read: boolean;
  related_entity_type: string | null;
  related_entity_id: number | null;
  created_at: string;
  updated_at: string;
};

export type NotificationSnapshot = {
  total_count: number;
  unread_count: number;
  latest_notification_id: number | null;
  notifications: NotificationRead[];
};

export type PlatformSnapshot = OverviewStats & {
  latest_match_id: number | null;
  latest_tournament_id: number | null;
  latest_ranked_match_id: number | null;
};

export type PlatformRealtimeEvent =
  | {
      type: "notifications.snapshot";
      payload: NotificationSnapshot;
      created_at: string;
    }
  | {
      type: "platform.snapshot";
      payload: PlatformSnapshot;
      created_at: string;
    }
  | {
      type: "pong";
      payload: Record<string, never>;
      created_at: string;
    };

export type RankedMatch = {
  id: number;
  discipline: string;
  mode: string;
  player_one_id: number;
  player_two_id: number;
  status: "SCHEDULED" | "COMPLETED" | "CANCELLED";
  player_one_score: number | null;
  player_two_score: number | null;
  player_one_kills: number;
  player_one_deaths: number;
  player_one_assists: number;
  player_one_kda: number;
  player_two_kills: number;
  player_two_deaths: number;
  player_two_assists: number;
  player_two_kda: number;
  winner_id: number | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  player_one: CurrentUser;
  player_two: CurrentUser;
  winner: CurrentUser | null;
};

export type MatchmakingResponse = {
  status: "SEARCHING" | "MATCHED" | "CANCELLED";
  message: string;
  discipline: string | null;
  mode: string | null;
  rating_range: number | null;
  request: {
    id: number;
    user_id: number;
    status: "SEARCHING" | "MATCHED" | "CANCELLED";
    discipline: string;
    mode: string;
    rating_snapshot: number;
    matched_ranked_match_id: number | null;
    created_at: string;
    updated_at: string;
  } | null;
  match: RankedMatch | null;
};

export type DisputeStatus = "OPEN" | "RESOLVED" | "REJECTED";

export type MatchDispute = {
  id: number;
  match_id: number;
  opened_by_id: number;
  reason: string;
  status: DisputeStatus;
  resolution: string | null;
  resolved_by_id: number | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
  opened_by: CurrentUser;
  resolved_by: CurrentUser | null;
  match: MatchRead;
};

export type ActionLog = {
  id: number;
  actor_id: number | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  actor: CurrentUser | null;
};

export type ProfileHistory = {
  teams: Array<{
    id: number;
    name: string;
    role: string;
    created_at: string;
  }>;
  tournaments: Array<{
    id: number;
    name: string;
    status: string;
    participant_status: string;
    team_name: string;
    starts_at: string | null;
  }>;
  tournament_matches: Array<{
    id: number;
    tournament_id: number;
    tournament_name: string;
    home_team_name: string;
    away_team_name: string;
    status: string;
    scheduled_at: string | null;
    completed_at: string | null;
  }>;
  ranked_matches: RankedMatch[];
};

export type AdminUserUpdatePayload = {
  username?: string;
  email?: string;
  is_active?: boolean;
  role?: "USER" | "ORGANIZER" | "ADMIN";
};

export type RankingSort = "rating" | "wins" | "matches";

export type RankingFilters = {
  search?: string;
  sortBy?: RankingSort;
  minMatches?: number;
};

export async function listRankings(
  searchOrFilters?: string | RankingFilters,
): Promise<RankingUser[]> {
  const filters =
    typeof searchOrFilters === "string"
      ? { search: searchOrFilters }
      : searchOrFilters;
  const params = new URLSearchParams();

  if (filters?.search) {
    params.set("search", filters.search);
  }

  if (filters?.sortBy) {
    params.set("sort_by", filters.sortBy);
  }

  if (filters?.minMatches && filters.minMatches > 0) {
    params.set("min_matches", String(filters.minMatches));
  }

  const query = params.toString();
  return apiRequest<RankingUser[]>(`/rankings${query ? `?${query}` : ""}`);
}

export async function getOverviewStats(): Promise<OverviewStats> {
  return apiRequest<OverviewStats>("/statistics/overview");
}

export async function listTeamStats(): Promise<TeamStats[]> {
  return apiRequest<TeamStats[]>("/statistics/teams");
}

export async function listPlayerStats(): Promise<PlayerStats[]> {
  return apiRequest<PlayerStats[]>("/statistics/players");
}

export async function listTournamentStats(): Promise<TournamentStats[]> {
  return apiRequest<TournamentStats[]>("/statistics/tournaments");
}

export async function listNotifications(
  token: string,
): Promise<NotificationRead[]> {
  return apiRequest<NotificationRead[]>("/notifications", { token });
}

export async function markNotificationRead(
  notificationId: number,
  token: string,
): Promise<NotificationRead> {
  return apiRequest<NotificationRead>(
    `/notifications/${notificationId}/read`,
    {
      method: "PATCH",
      token,
    },
  );
}

export async function findRankedOpponent(
  payload: { discipline: string; mode: string },
  token: string,
): Promise<MatchmakingResponse> {
  return apiRequest<MatchmakingResponse>("/ranked/matchmaking", {
    method: "POST",
    body: payload,
    token,
  });
}

export async function cancelRankedMatchmaking(token: string): Promise<void> {
  await apiRequest<void>("/ranked/matchmaking", {
    method: "DELETE",
    token,
  });
}

export async function listRankedMatches(token: string): Promise<RankedMatch[]> {
  return apiRequest<RankedMatch[]>("/ranked/matches", { token });
}

export async function getProfileHistory(token: string): Promise<ProfileHistory> {
  return apiRequest<ProfileHistory>("/profile/history", { token });
}

export async function submitRankedMatchResult(
  matchId: number,
  payload: {
    player_one_score: number;
    player_two_score: number;
    player_one_kills?: number;
    player_one_deaths?: number;
    player_one_assists?: number;
    player_two_kills?: number;
    player_two_deaths?: number;
    player_two_assists?: number;
  },
  token: string,
): Promise<RankedMatch> {
  return apiRequest<RankedMatch>(`/ranked/matches/${matchId}/result`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function createDispute(
  payload: { match_id: number; reason: string },
  token: string,
): Promise<MatchDispute> {
  return apiRequest<MatchDispute>("/disputes", {
    method: "POST",
    body: payload,
    token,
  });
}

export async function listMyDisputes(token: string): Promise<MatchDispute[]> {
  return apiRequest<MatchDispute[]>("/disputes", { token });
}

export async function adminListUsers(token: string): Promise<CurrentUser[]> {
  return apiRequest<CurrentUser[]>("/admin/users", { token });
}

export async function bootstrapFirstAdmin(token: string): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/admin/bootstrap", {
    method: "POST",
    token,
  });
}

export async function adminUpdateUser(
  userId: number,
  payload: AdminUserUpdatePayload,
  token: string,
): Promise<CurrentUser> {
  return apiRequest<CurrentUser>(`/admin/users/${userId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function adminListDisputes(
  token: string,
  status?: DisputeStatus,
): Promise<MatchDispute[]> {
  const query = status ? `?status=${status}` : "";
  return apiRequest<MatchDispute[]>(`/admin/disputes${query}`, { token });
}

export async function adminResolveDispute(
  disputeId: number,
  payload: { status: "RESOLVED" | "REJECTED"; resolution: string },
  token: string,
): Promise<MatchDispute> {
  return apiRequest<MatchDispute>(`/admin/disputes/${disputeId}/resolve`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function adminListActionLogs(token: string): Promise<ActionLog[]> {
  return apiRequest<ActionLog[]>("/admin/action-logs", { token });
}

export type ReportExportType =
  | "users"
  | "tournaments"
  | "matches"
  | "player_statistics"
  | "action_logs";

export function buildReportExportUrl(reportType: ReportExportType): string {
  return `${API_URL}/admin/reports/export?report_type=${reportType}`;
}
