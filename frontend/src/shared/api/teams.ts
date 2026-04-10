import { apiRequest } from "@/src/shared/api/client";

export type UserSummary = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  created_at: string;
  updated_at: string;
};

export type TeamMemberRole = "OWNER" | "MEMBER";

export type TeamMember = {
  id: number;
  team_id: number;
  user_id: number;
  role: TeamMemberRole;
  created_at: string;
  updated_at: string;
  user: UserSummary;
};

export type TeamListItem = {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
};

export type TeamRead = {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
  owner: UserSummary;
  members: TeamMember[];
};

export type CreateTeamPayload = {
  name: string;
  description?: string;
};

export async function listTeams(): Promise<TeamListItem[]> {
  return apiRequest<TeamListItem[]>("/teams");
}

export async function listMyTeams(token: string): Promise<TeamRead[]> {
  return apiRequest<TeamRead[]>("/teams/my", {
    token,
  });
}

export async function getTeam(teamId: number): Promise<TeamRead> {
  return apiRequest<TeamRead>(`/teams/${teamId}`);
}

export async function createTeam(
  payload: CreateTeamPayload,
  token: string,
): Promise<TeamRead> {
  return apiRequest<TeamRead>("/teams", {
    method: "POST",
    body: payload,
    token,
  });
}