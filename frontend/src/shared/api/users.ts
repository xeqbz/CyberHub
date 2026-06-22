import { apiRequest } from "@/src/shared/api/client";

export type CurrentUser = {
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

export type UpdateCurrentUserPayload = {
  username?: string;
  email?: string;
};

export async function getCurrentUser(token: string): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/users/me", {
    token,
  });
}

export async function updateCurrentUser(
  payload: UpdateCurrentUserPayload,
  token: string,
): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/users/me", {
    method: "PATCH",
    body: payload,
    token,
  });
}
