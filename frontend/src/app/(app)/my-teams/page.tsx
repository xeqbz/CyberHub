"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listMyTeams, type TeamRead } from "@/src/shared/api/teams";
import { getAccessToken } from "@/src/shared/lib/auth";
import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";

export default function MyTeamsPage() {
  const [teams, setTeams] = useState<TeamRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadMyTeams() {
      const token = getAccessToken();

      if (!token) {
        setError("You need to login to view your teams.");
        setIsLoading(false);
        return;
      }

      try {
        setError("");
        setIsLoading(true);

        const data = await listMyTeams(token);
        setTeams(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load your teams");
      } finally {
        setIsLoading(false);
      }
    }

    void loadMyTeams();
  }, []);

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">My teams</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Teams you belong to
          </h1>
          <p className="page-subtitle">
            Quick access to your roster, ownership and team details.
          </p>
        </div>

        <div className="row">
          <Link href="/teams" className="btn btn-secondary">
            All teams
          </Link>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
        </div>
      </div>

      {isLoading ? <p>Loading your teams...</p> : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Failed to load teams">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !error && teams.length === 0 ? (
        <EmptyState
          title="No personal teams yet"
          description="You are not a member of any team yet. Create one or join an existing roster."
          action={
            <Link href="/teams" className="btn btn-secondary">
              Open teams
            </Link>
          }
        />
      ) : null}

      {!isLoading && !error && teams.length > 0 ? (
        <div className="grid">
          {teams.map((team) => (
            <div key={team.id} className="card">
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div>
                  <h3>{team.name}</h3>
                  <p>{team.description || "No description provided."}</p>
                </div>

                <span className="badge">
                  {team.members.length} member{team.members.length === 1 ? "" : "s"}
                </span>
              </div>

              <div className="grid grid-2" style={{ marginTop: "16px", gap: "12px" }}>
                <div>
                  <p className="muted">Owner</p>
                  <strong>{team.owner.username}</strong>
                </div>

                <div>
                  <p className="muted">Owner email</p>
                  <strong>{team.owner.email}</strong>
                </div>
              </div>

              <div className="row" style={{ marginTop: "16px" }}>
                <Link href={`/teams/${team.id}`} className="btn btn-secondary">
                  Open details
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </main>
  );
}