"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { listMyTeams, type TeamRead } from "@/src/shared/api/teams";
import {
  getTournament,
  registerTeamForTournament,
  removeTeamFromTournament,
  updateTournament,
  type TournamentRead,
  type TournamentStatus,
} from "@/src/shared/api/tournaments";
import { getAccessToken } from "@/src/shared/lib/auth";

const STATUS_OPTIONS: TournamentStatus[] = [
  "DRAFT",
  "REGISTRATION_OPEN",
  "REGISTRATION_CLOSED",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
];

function formatDate(value: string | null): string {
  if (!value) return "Not specified";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

export default function TournamentDetailsPage() {
  const params = useParams();
  const tournamentId = useMemo(() => Number(params?.id), [params]);

  const [tournament, setTournament] = useState<TournamentRead | null>(null);
  const [myTeams, setMyTeams] = useState<TeamRead[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState("");

  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const [registerError, setRegisterError] = useState("");
  const [registerSuccess, setRegisterSuccess] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);

  const [removeError, setRemoveError] = useState("");
  const [isRemovingTeamId, setIsRemovingTeamId] = useState<number | null>(null);

  const [statusError, setStatusError] = useState("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  useEffect(() => {
    async function loadTournament() {
      if (!Number.isFinite(tournamentId)) {
        setError("Invalid tournament id");
        setIsLoading(false);
        return;
      }

      try {
        setError("");
        setIsLoading(true);

        const data = await getTournament(tournamentId);
        setTournament(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load tournament",
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadTournament();
  }, [tournamentId]);

  useEffect(() => {
    async function loadMyTeams() {
      const token = getAccessToken();
      if (!token) return;

      try {
        const data = await listMyTeams(token);
        setMyTeams(data);
      } catch {
        // keep silent here, tournament page can still work without this block
      }
    }

    loadMyTeams();
  }, []);

  async function refreshTournament() {
    if (!Number.isFinite(tournamentId)) return;

    const data = await getTournament(tournamentId);
    setTournament(data);
  }

  async function handleRegisterTeam(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setRegisterError("You need to login before registering a team");
      return;
    }

    if (!selectedTeamId) {
      setRegisterError("Select a team first");
      return;
    }

    setRegisterError("");
    setRegisterSuccess("");
    setIsRegistering(true);

    try {
      await registerTeamForTournament(tournamentId, Number(selectedTeamId), token);
      setRegisterSuccess("Team registered successfully");
      setSelectedTeamId("");
      await refreshTournament();
    } catch (err) {
      setRegisterError(
        err instanceof Error ? err.message : "Failed to register team",
      );
    } finally {
      setIsRegistering(false);
    }
  }

  async function handleRemoveTeam(teamId: number) {
    const token = getAccessToken();
    if (!token) {
      setRemoveError("You need to login before removing a participant");
      return;
    }

    setRemoveError("");
    setIsRemovingTeamId(teamId);

    try {
      await removeTeamFromTournament(tournamentId, teamId, token);
      await refreshTournament();
    } catch (err) {
      setRemoveError(
        err instanceof Error ? err.message : "Failed to remove team",
      );
    } finally {
      setIsRemovingTeamId(null);
    }
  }

  async function handleStatusChange(nextStatus: TournamentStatus) {
    const token = getAccessToken();
    if (!token) {
      setStatusError("You need to login before updating tournament status");
      return;
    }

    setStatusError("");
    setIsUpdatingStatus(true);

    try {
      const updated = await updateTournament(
        tournamentId,
        { status: nextStatus },
        token,
      );
      setTournament(updated);
    } catch (err) {
      setStatusError(
        err instanceof Error ? err.message : "Failed to update status",
      );
    } finally {
      setIsUpdatingStatus(false);
    }
  }

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Tournament details</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            {tournament?.name ?? "Tournament"}
          </h1>
          <p className="page-subtitle">
            Inspect tournament metadata, participants and registration flow.
          </p>
        </div>

        <div className="row">
          <Link href="/tournaments" className="btn btn-secondary">
            Back to tournaments
          </Link>
          <Link href="/teams" className="btn btn-secondary">
            Teams
          </Link>
        </div>
      </div>

      {isLoading ? (
        <section>
          <h2>Loading tournament...</h2>
          <p>Please wait while we fetch tournament details.</p>
        </section>
      ) : null}

      {!isLoading && error ? (
        <section>
          <h2>Failed to load tournament</h2>
          <p className="error-text" style={{ marginTop: "10px" }}>
            {error}
          </p>
        </section>
      ) : null}

      {!isLoading && tournament ? (
        <>
          <div className="grid grid-3" style={{ marginBottom: "24px" }}>
            <div className="card stat-card">
              <div className="stat-label">Tournament ID</div>
              <div className="stat-value">{tournament.id}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Status</div>
              <div className="stat-value">{tournament.status}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Participants</div>
              <div className="stat-value">
                {tournament.participants.length}/{tournament.max_teams}
              </div>
            </div>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
              <h2>General info</h2>

              <div className="grid" style={{ marginTop: "18px" }}>
                <div>
                  <p className="muted">Name</p>
                  <strong>{tournament.name}</strong>
                </div>

                <div>
                  <p className="muted">Description</p>
                  <strong>
                    {tournament.description || "No description provided"}
                  </strong>
                </div>

                <div>
                  <p className="muted">Starts at</p>
                  <strong>{formatDate(tournament.starts_at)}</strong>
                </div>

                <div>
                  <p className="muted">Owner</p>
                  <strong>{tournament.owner.username}</strong>
                </div>
              </div>
            </section>

            <section>
              <h2>Status management</h2>
              <p style={{ marginBottom: "18px" }}>
                Tournament owner can switch status directly from this page.
              </p>

              <div className="form-group">
                <label htmlFor="tournament-status-select">Status</label>
                <select
                  id="tournament-status-select"
                  value={tournament.status}
                  onChange={(event) =>
                    handleStatusChange(
                      event.target.value as TournamentStatus,
                    )
                  }
                  disabled={isUpdatingStatus}
                >
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              {statusError ? <p className="error-text">{statusError}</p> : null}
            </section>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
              <h2>Register team</h2>
              <p style={{ marginBottom: "20px" }}>
                You can register a team here when tournament status is
                REGISTRATION_OPEN.
              </p>

              {myTeams.length === 0 ? (
                <p>
                  You have no teams available. Create one first on the Teams page.
                </p>
              ) : (
                <form onSubmit={handleRegisterTeam}>
                  <div className="form-group">
                    <label htmlFor="team-select">Select team</label>
                    <select
                      id="team-select"
                      value={selectedTeamId}
                      onChange={(event) => setSelectedTeamId(event.target.value)}
                    >
                      <option value="">Choose team</option>
                      {myTeams.map((team) => (
                        <option key={team.id} value={team.id}>
                          {team.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {registerError ? (
                    <p className="error-text">{registerError}</p>
                  ) : null}
                  {registerSuccess ? (
                    <p className="success-text">{registerSuccess}</p>
                  ) : null}

                  <button type="submit" disabled={isRegistering}>
                    {isRegistering ? "Registering..." : "Register team"}
                  </button>
                </form>
              )}
            </section>

            <section>
              <h2>Participants</h2>
              <p style={{ marginBottom: "20px" }}>
                Current registered teams in this tournament.
              </p>

              {removeError ? <p className="error-text">{removeError}</p> : null}

              {tournament.participants.length === 0 ? (
                <p>No participants registered yet.</p>
              ) : (
                <div className="grid">
                  {tournament.participants.map((participant) => (
                    <div key={participant.id} className="card">
                      <div className="row" style={{ justifyContent: "space-between" }}>
                        <div>
                          <h3>{participant.team.name}</h3>
                          <p>
                            {participant.team.description ||
                              "No team description provided."}
                          </p>
                        </div>

                        <span className="badge">Team ID: {participant.team_id}</span>
                      </div>

                      <div className="row" style={{ marginTop: "16px" }}>
                        <Link
                          href={`/teams/${participant.team_id}`}
                          className="btn btn-secondary"
                        >
                          Open team
                        </Link>

                        <button
                          type="button"
                          onClick={() => handleRemoveTeam(participant.team_id)}
                          disabled={isRemovingTeamId === participant.team_id}
                        >
                          {isRemovingTeamId === participant.team_id
                            ? "Removing..."
                            : "Remove"}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        </>
      ) : null}
    </main>
  );
}