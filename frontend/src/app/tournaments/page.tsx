"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  createTournament,
  listTournaments,
  type TournamentListItem,
  type TournamentStatus,
} from "@/src/shared/api/tournaments";
import { getAccessToken, isAuthenticated } from "@/src/shared/lib/auth";

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

export default function TournamentsPage() {
  const authenticated = useMemo(() => isAuthenticated(), []);

  const [tournaments, setTournaments] = useState<TournamentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [maxTeams, setMaxTeams] = useState("8");
  const [status, setStatus] = useState<TournamentStatus>("DRAFT");
  const [startsAt, setStartsAt] = useState("");

  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    async function loadTournaments() {
      try {
        setLoadError("");
        setIsLoading(true);

        const data = await listTournaments();
        setTournaments(data);
      } catch (err) {
        setLoadError(
          err instanceof Error ? err.message : "Failed to load tournaments",
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadTournaments();
  }, []);

  async function handleCreateTournament(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const token = getAccessToken();

    if (!token) {
      setCreateError("You need to login before creating a tournament");
      return;
    }

    setCreateError("");
    setCreateSuccess("");
    setIsCreating(true);

    try {
      const createdTournament = await createTournament(
        {
          name,
          description: description.trim() || undefined,
          status,
          max_teams: Number(maxTeams),
          starts_at: startsAt ? new Date(startsAt).toISOString() : null,
        },
        token,
      );

      setCreateSuccess(`Tournament "${createdTournament.name}" created successfully`);
      setName("");
      setDescription("");
      setMaxTeams("8");
      setStatus("DRAFT");
      setStartsAt("");

      setTournaments((prev) => [
        {
          id: createdTournament.id,
          name: createdTournament.name,
          description: createdTournament.description,
          status: createdTournament.status,
          owner_id: createdTournament.owner_id,
          max_teams: createdTournament.max_teams,
          starts_at: createdTournament.starts_at,
          created_at: createdTournament.created_at,
          updated_at: createdTournament.updated_at,
        },
        ...prev,
      ]);
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create tournament",
      );
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Tournaments</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Create and explore tournaments
          </h1>
          <p className="page-subtitle">
            Browse tournaments, inspect details and register teams when
            registration is open.
          </p>
        </div>

        <div className="row">
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
          <Link href="/teams" className="btn btn-secondary">
            Teams
          </Link>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: "24px" }}>
        <section>
          <h2>Create tournament</h2>
          <p style={{ marginBottom: "20px" }}>
            Tournament owner can set basic metadata, capacity and initial status.
          </p>

          {!authenticated ? (
            <div className="card">
              <p style={{ marginBottom: "16px" }}>
                Login is required to create a tournament.
              </p>
              <div className="row">
                <Link href="/login" className="btn btn-secondary">
                  Login
                </Link>
                <Link href="/register" className="btn btn-secondary">
                  Register
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleCreateTournament}>
              <div className="form-group">
                <label htmlFor="tournament-name">Tournament name</label>
                <input
                  id="tournament-name"
                  type="text"
                  placeholder="Enter tournament name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="tournament-description">Description</label>
                <textarea
                  id="tournament-description"
                  placeholder="Short tournament description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                />
              </div>

              <div className="grid grid-2">
                <div className="form-group">
                  <label htmlFor="tournament-max-teams">Max teams</label>
                  <input
                    id="tournament-max-teams"
                    type="number"
                    min={2}
                    max={1024}
                    value={maxTeams}
                    onChange={(event) => setMaxTeams(event.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="tournament-status">Status</label>
                  <select
                    id="tournament-status"
                    value={status}
                    onChange={(event) =>
                      setStatus(event.target.value as TournamentStatus)
                    }
                  >
                    {STATUS_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="tournament-starts-at">Starts at</label>
                <input
                  id="tournament-starts-at"
                  type="datetime-local"
                  value={startsAt}
                  onChange={(event) => setStartsAt(event.target.value)}
                />
              </div>

              {createError ? <p className="error-text">{createError}</p> : null}
              {createSuccess ? (
                <p className="success-text">{createSuccess}</p>
              ) : null}

              <button type="submit" disabled={isCreating}>
                {isCreating ? "Creating..." : "Create tournament"}
              </button>
            </form>
          )}
        </section>

        <section>
          <h2>Tips</h2>
          <div className="grid" style={{ marginTop: "18px" }}>
            <div className="card">
              <h3>Registration flow</h3>
              <p>
                Keep tournament status as <strong>REGISTRATION_OPEN</strong> when
                you want team owners to join.
              </p>
            </div>

            <div className="card">
              <h3>Capacity</h3>
              <p>
                Backend enforces participant limit through <strong>max_teams</strong>.
              </p>
            </div>

            <div className="card">
              <h3>Team requirement</h3>
              <p>
                A team must already exist before it can be registered in a
                tournament.
              </p>
            </div>
          </div>
        </section>
      </div>

      <section>
        <h2>All tournaments</h2>
        <p style={{ marginBottom: "20px" }}>
          Current list of tournaments available on the platform.
        </p>

        {isLoading ? <p>Loading tournaments...</p> : null}
        {loadError ? <p className="error-text">{loadError}</p> : null}

        {!isLoading && !loadError && tournaments.length === 0 ? (
          <p>No tournaments have been created yet.</p>
        ) : null}

        {!isLoading && !loadError && tournaments.length > 0 ? (
          <div className="grid">
            {tournaments.map((tournament) => (
              <div key={tournament.id} className="card">
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <div>
                    <h3>{tournament.name}</h3>
                    <p>{tournament.description || "No description provided."}</p>
                  </div>

                  <span className="badge">{tournament.status}</span>
                </div>

                <div
                  className="grid grid-2"
                  style={{ marginTop: "16px", gap: "12px" }}
                >
                  <div>
                    <p className="muted">Max teams</p>
                    <strong>{tournament.max_teams}</strong>
                  </div>

                  <div>
                    <p className="muted">Starts at</p>
                    <strong>{formatDate(tournament.starts_at)}</strong>
                  </div>
                </div>

                <div className="row" style={{ marginTop: "16px" }}>
                  <Link
                    href={`/tournaments/${tournament.id}`}
                    className="btn btn-secondary"
                  >
                    View tournament
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}