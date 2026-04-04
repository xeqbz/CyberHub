"use client";

import { useEffect, useState } from "react";

import { apiRequest } from "@/src/shared/api/client";

type User = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  created_at: string;
  updated_at: string;
};

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadProfile() {
      try {
        const token = localStorage.getItem("access_token");

        if (!token) {
          throw new Error("Access token not found");
        }

        const data = await apiRequest<User>("/users/me", {
          token,
        });

        setUser(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile");
      } finally {
        setIsLoading(false);
      }
    }

    loadProfile();
  }, []);

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Profile</h1>

      {isLoading ? <p>Loading...</p> : null}
      {error ? <p className="text-red-600">{error}</p> : null}

      {user ? (
        <div className="space-y-2 rounded border p-4">
          <p><strong>ID:</strong> {user.id}</p>
          <p><strong>Username:</strong> {user.username}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Role:</strong> {user.role}</p>
          <p><strong>Active:</strong> {String(user.is_active)}</p>
        </div>
      ) : null}
    </main>
  );
}