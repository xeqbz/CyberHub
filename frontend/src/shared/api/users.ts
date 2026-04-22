import { apiRequest } from "@/src/shared/api/client";

export type CurrentUser = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  created_at: string;
  updated_at: string;
};

export async function getCurrentUser(token: string): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/users/me", {
    token,
  });
}