import { apiRequest } from "@/src/shared/api/client";

export type UserSummary = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  rating: number;
  wins: number;
  losses: number;
  draws: number;
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

export type UpdateTeamPayload = {
  name?: string;
  description?: string | null;
};

export type AddTeamMemberPayload = {
  user_id: number;
  role?: TeamMemberRole;
};

export type UpdateTeamMemberRolePayload = {
  role: TeamMemberRole;
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

export async function updateTeam(
  teamId: number,
  payload: UpdateTeamPayload,
  token: string,
): Promise<TeamRead> {
  return apiRequest<TeamRead>(`/teams/${teamId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function deleteTeam(teamId: number, token: string): Promise<void> {
  await apiRequest<void>(`/teams/${teamId}`, {
    method: "DELETE",
    token,
  });
}

export async function addTeamMember(
  teamId: number,
  payload: AddTeamMemberPayload,
  token: string,
): Promise<TeamMember> {
  return apiRequest<TeamMember>(`/teams/${teamId}/members`, {
    method: "POST",
    body: payload,
    token,
  });
}

export async function updateTeamMemberRole(
  teamId: number,
  userId: number,
  payload: UpdateTeamMemberRolePayload,
  token: string,
): Promise<TeamMember> {
  return apiRequest<TeamMember>(`/teams/${teamId}/members/${userId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export async function removeTeamMember(
  teamId: number,
  userId: number,
  token: string,
): Promise<void> {
  await apiRequest<void>(`/teams/${teamId}/members/${userId}`, {
    method: "DELETE",
    token,
  });
}
