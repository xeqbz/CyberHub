"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { getTeam, type TeamRead } from "@/src/shared/api/teams";

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export default function TeamDetailsPage() {
  const params = useParams();
  const teamId = useMemo(() => Number(params?.id), [params]);

  const [team, setTeam] = useState<TeamRead | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadTeam() {
      if (!Number.isFinite(teamId)) {
        setError("Invalid team id");
        setIsLoading(false);
        return;
      }

      try {
        setError("");
        setIsLoading(true);

        const data = await getTeam(teamId);
        setTeam(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load team");
      } finally {
        setIsLoading(false);
      }
    }

    loadTeam();
  }, [teamId]);

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Team details</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            {team?.name ?? "Team"}
          </h1>
          <p className="page-subtitle">
            Team overview, owner information and current roster.
          </p>
        </div>

        <div className="row">
          <Link href="/teams" className="btn btn-secondary">
            Back to teams
          </Link>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
        </div>
      </div>

      {isLoading ? (
        <section>
          <h2>Loading team...</h2>
          <p>Please wait while we fetch team details.</p>
        </section>
      ) : null}

      {!isLoading && error ? (
        <section>
          <h2>Failed to load team</h2>
          <p className="error-text" style={{ marginTop: "10px" }}>
            {error}
          </p>
        </section>
      ) : null}

      {!isLoading && team ? (
        <>
          <div className="grid grid-3" style={{ marginBottom: "24px" }}>
            <div className="card stat-card">
              <div className="stat-label">Team ID</div>
              <div className="stat-value">{team.id}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Owner ID</div>
              <div className="stat-value">{team.owner_id}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Members</div>
              <div className="stat-value">{team.members.length}</div>
            </div>
          </div>

          <div className="grid grid-2">
            <section>
              <h2>General info</h2>
              <div className="grid" style={{ marginTop: "18px" }}>
                <div>
                  <p className="muted">Name</p>
                  <strong>{team.name}</strong>
                </div>

                <div>
                  <p className="muted">Description</p>
                  <strong>{team.description || "No description provided"}</strong>
                </div>

                <div>
                  <p className="muted">Created at</p>
                  <strong>{formatDate(team.created_at)}</strong>
                </div>

                <div>
                  <p className="muted">Updated at</p>
                  <strong>{formatDate(team.updated_at)}</strong>
                </div>
              </div>
            </section>

            <section>
              <h2>Owner</h2>
              <div className="grid" style={{ marginTop: "18px" }}>
                <div>
                  <p className="muted">Username</p>
                  <strong>{team.owner.username}</strong>
                </div>

                <div>
                  <p className="muted">Email</p>
                  <strong>{team.owner.email}</strong>
                </div>

                <div>
                  <p className="muted">Role</p>
                  <strong>{team.owner.role}</strong>
                </div>

                <div>
                  <p className="muted">Status</p>
                  <strong>{team.owner.is_active ? "Active" : "Inactive"}</strong>
                </div>
              </div>
            </section>
          </div>

          <section style={{ marginTop: "24px" }}>
            <h2>Roster</h2>
            <p style={{ marginBottom: "20px" }}>
              Current team members returned by the backend.
            </p>

            {team.members.length === 0 ? (
              <p>No members found.</p>
            ) : (
              <div className="grid">
                {team.members.map((member) => (
                  <div key={member.id} className="card">
                    <div className="row" style={{ justifyContent: "space-between" }}>
                      <div>
                        <h3>{member.user.username}</h3>
                        <p>{member.user.email}</p>
                      </div>

                      <span className="badge">{member.role}</span>
                    </div>

                    <div className="grid grid-2" style={{ marginTop: "16px" }}>
                      <div>
                        <p className="muted">User ID</p>
                        <strong>{member.user_id}</strong>
                      </div>

                      <div>
                        <p className="muted">Joined record created</p>
                        <strong>{formatDate(member.created_at)}</strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}