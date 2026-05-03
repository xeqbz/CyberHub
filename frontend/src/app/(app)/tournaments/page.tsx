"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import { useCurrentUser } from "@/src/hooks/use-current-user";
import {
  createTournament,
  listTournaments,
  type TournamentListItem,
  type TournamentStatus,
} from "@/src/shared/api/tournaments";
import { getAccessToken, isAuthenticated } from "@/src/shared/lib/auth";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

const STATUS_OPTIONS: TournamentStatus[] = [
  "DRAFT",
  "REGISTRATION_OPEN",
  "REGISTRATION_CLOSED",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
];

type ScopeFilter = "ALL" | "MY_TOURNAMENTS" | "OPEN" | "ACTIVE" | "COMPLETED";

function formatDate(value: string | null): string {
  if (!value) return "Not specified";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function sortTournaments(items: TournamentListItem[]): TournamentListItem[] {
  return [...items].sort((a, b) => {
    if (a.starts_at && b.starts_at) {
      return new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime();
    }

    if (a.starts_at && !b.starts_at) return -1;
    if (!a.starts_at && b.starts_at) return 1;

    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

function matchesScope(
  tournament: TournamentListItem,
  scope: ScopeFilter,
  currentUserId?: number,
): boolean {
  switch (scope) {
    case "MY_TOURNAMENTS":
      return currentUserId ? tournament.owner_id === currentUserId : false;

    case "OPEN":
      return tournament.status === "REGISTRATION_OPEN";

    case "ACTIVE":
      return (
        tournament.status === "REGISTRATION_OPEN" ||
        tournament.status === "REGISTRATION_CLOSED" ||
        tournament.status === "IN_PROGRESS"
      );

    case "COMPLETED":
      return tournament.status === "COMPLETED";

    case "ALL":
    default:
      return true;
  }
}

export default function TournamentsPage() {
  const authenticated = useMemo(() => isAuthenticated(), []);
  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [tournaments, setTournaments] = useState<TournamentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [format, setFormat] = useState("single_elimination");
  const [discipline, setDiscipline] = useState("CS2");
  const [rules, setRules] = useState("Standard competitive rules");
  const [maxTeams, setMaxTeams] = useState("8");
  const [status, setStatus] = useState<TournamentStatus>("DRAFT");
  const [startsAt, setStartsAt] = useState("");

  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const [search, setSearch] = useState("");
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const loadTournaments = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    void loadTournaments();
  }, [loadTournaments]);

  async function handleCreateTournament(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setCreateError("You need to login before creating a tournament");
      return;
    }

    const nextName = name.trim();
    const nextDescription = description.trim();
    const nextMaxTeams = Number(maxTeams);

    if (!nextName) {
      setCreateError("Tournament name cannot be empty");
      return;
    }

    if (!Number.isFinite(nextMaxTeams) || nextMaxTeams < 2) {
      setCreateError("Max teams must be at least 2");
      return;
    }

    setCreateError("");
    setCreateSuccess("");
    setIsCreating(true);

    try {
      const createdTournament = await createTournament(
        {
          name: nextName,
          description: nextDescription || undefined,
          format,
          discipline,
          rules,
          status,
          max_teams: nextMaxTeams,
          starts_at: startsAt ? new Date(startsAt).toISOString() : null,
        },
        token,
      );

      setCreateSuccess(`Tournament "${createdTournament.name}" created successfully`);
      setName("");
      setDescription("");
      setFormat("single_elimination");
      setDiscipline("CS2");
      setRules("Standard competitive rules");
      setMaxTeams("8");
      setStatus("DRAFT");
      setStartsAt("");

      setTournaments((prev) =>
        sortTournaments([
          {
            id: createdTournament.id,
            name: createdTournament.name,
            description: createdTournament.description,
            format: createdTournament.format,
            discipline: createdTournament.discipline,
            rules: createdTournament.rules,
            bracket_settings: createdTournament.bracket_settings,
            status: createdTournament.status,
            owner_id: createdTournament.owner_id,
            max_teams: createdTournament.max_teams,
            starts_at: createdTournament.starts_at,
            created_at: createdTournament.created_at,
            updated_at: createdTournament.updated_at,
          },
          ...prev,
        ]),
      );
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create tournament",
      );
    } finally {
      setIsCreating(false);
    }
  }

  const myTournaments = useMemo(() => {
    if (!currentUser) return [];
    return tournaments.filter((item) => item.owner_id === currentUser.id);
  }, [tournaments, currentUser]);

  const filteredTournaments = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return sortTournaments(
      tournaments.filter((tournament) => {
        const matchesText =
          !normalizedSearch ||
          tournament.name.toLowerCase().includes(normalizedSearch) ||
          tournament.description?.toLowerCase().includes(normalizedSearch) ||
          tournament.discipline.toLowerCase().includes(normalizedSearch) ||
          tournament.format.toLowerCase().includes(normalizedSearch) ||
          String(tournament.id).includes(normalizedSearch);

        const matchesScopeFilter = matchesScope(
          tournament,
          scopeFilter,
          currentUser?.id,
        );

        const matchesStatusFilter =
          statusFilter === "ALL" || tournament.status === statusFilter;

        return matchesText && matchesScopeFilter && matchesStatusFilter;
      }),
    );
  }, [tournaments, search, scopeFilter, statusFilter, currentUser]);

  const openRegistrationCount = useMemo(
    () => tournaments.filter((item) => item.status === "REGISTRATION_OPEN").length,
    [tournaments],
  );

  const activeCount = useMemo(
    () =>
      tournaments.filter(
        (item) =>
          item.status === "REGISTRATION_OPEN" ||
          item.status === "REGISTRATION_CLOSED" ||
          item.status === "IN_PROGRESS",
      ).length,
    [tournaments],
  );

  const completedCount = useMemo(
    () => tournaments.filter((item) => item.status === "COMPLETED").length,
    [tournaments],
  );

  const recentMyTournaments = useMemo(() => {
    return [...myTournaments]
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      .slice(0, 3);
  }, [myTournaments]);

  const isInitialLoading = isLoading || isLoadingCurrentUser;

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Tournaments</p>
        <h1>Create and explore tournaments</h1>
        <p>
          Browse tournaments, create new competitions and jump into detailed
          tournament management.
        </p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
          <Link href="/my-tournaments" className="btn btn-secondary">
            My tournaments
          </Link>
          <Link href="/teams" className="btn btn-secondary">
            Teams
          </Link>
          <button type="button" onClick={() => void loadTournaments()}>
            Refresh
          </button>
        </div>
      </section>

      {isInitialLoading ? (
        <section className="card">
          <h2>Loading tournaments...</h2>
          <p>Please wait while platform tournaments are being loaded.</p>
        </section>
      ) : null}

      {!isInitialLoading && loadError ? (
        <Alert variant="error" title="Failed to load tournaments">
          {loadError}
        </Alert>
      ) : null}

      {!isInitialLoading && !loadError ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">All tournaments</p>
              <strong>{tournaments.length}</strong>
            </div>

            <div className="card">
              <p className="muted">My tournaments</p>
              <strong>{myTournaments.length}</strong>
            </div>

            <div className="card">
              <p className="muted">Open registration</p>
              <strong>{openRegistrationCount}</strong>
            </div>

            <div className="card">
              <p className="muted">Active tournaments</p>
              <strong>{activeCount}</strong>
            </div>

            <div className="card">
              <p className="muted">Completed</p>
              <strong>{completedCount}</strong>
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Create tournament</h2>
              <p style={{ marginBottom: "16px" }}>
                Set basic metadata, capacity and initial state for a new tournament.
              </p>

              {!authenticated ? (
                <EmptyState
                  title="Authentication required"
                  description="Login or register before creating a tournament."
                  action={
                    <div className="row">
                      <Link href="/login" className="btn btn-secondary">
                        Login
                      </Link>
                      <Link href="/register" className="btn btn-secondary">
                        Register
                      </Link>
                    </div>
                  }
                />
              ) : (
                <form onSubmit={handleCreateTournament}>
                  <div className="form-group">
                    <label htmlFor="tournament-name">Tournament name</label>
                    <input
                      id="tournament-name"
                      type="text"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Enter tournament name"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="tournament-description">Description</label>
                    <textarea
                      id="tournament-description"
                      value={description}
                      onChange={(event) => setDescription(event.target.value)}
                      placeholder="Optional tournament description"
                      rows={4}
                    />
                  </div>

                  <div className="grid grid-2">
                    <div className="form-group">
                      <label htmlFor="tournament-discipline">Discipline</label>
                      <input
                        id="tournament-discipline"
                        type="text"
                        value={discipline}
                        onChange={(event) => setDiscipline(event.target.value)}
                        placeholder="CS2, Dota 2, Valorant"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="tournament-format">Format</label>
                      <select
                        id="tournament-format"
                        value={format}
                        onChange={(event) => setFormat(event.target.value)}
                      >
                        <option value="single_elimination">Single elimination</option>
                        <option value="double_elimination">Double elimination</option>
                        <option value="round_robin">Round robin</option>
                        <option value="swiss">Swiss</option>
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="tournament-rules">Rules</label>
                    <textarea
                      id="tournament-rules"
                      value={rules}
                      onChange={(event) => setRules(event.target.value)}
                      placeholder="Core tournament rules"
                      rows={4}
                      required
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
                      <label htmlFor="tournament-status">Initial status</label>
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

                  {createError ? (
                    <Alert variant="error" title="Tournament creation failed">
                      {createError}
                    </Alert>
                  ) : null}

                  {createSuccess ? (
                    <Alert variant="success" title="Tournament created">
                      {createSuccess}
                    </Alert>
                  ) : null}

                  <div className="row" style={{ marginTop: "16px" }}>
                    <button type="submit" disabled={isCreating}>
                      {isCreating ? "Creating..." : "Create tournament"}
                    </button>
                  </div>
                </form>
              )}
            </div>

            <div className="card">
              <h2>Catalog filters</h2>

              <div className="grid" style={{ gap: "14px", marginTop: "16px" }}>
                <div className="form-group">
                  <label htmlFor="tournament-search">Search</label>
                  <input
                    id="tournament-search"
                    type="text"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search by name, description or id"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="tournament-scope">Scope</label>
                  <select
                    id="tournament-scope"
                    value={scopeFilter}
                    onChange={(event) =>
                      setScopeFilter(event.target.value as ScopeFilter)
                    }
                  >
                    <option value="ALL">All tournaments</option>
                    <option value="MY_TOURNAMENTS">My tournaments</option>
                    <option value="OPEN">Open registration</option>
                    <option value="ACTIVE">Active</option>
                    <option value="COMPLETED">Completed</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="tournament-status-filter">Exact status</label>
                  <select
                    id="tournament-status-filter"
                    value={statusFilter}
                    onChange={(event) => setStatusFilter(event.target.value)}
                  >
                    <option value="ALL">All</option>
                    <option value="DRAFT">DRAFT</option>
                    <option value="REGISTRATION_OPEN">REGISTRATION_OPEN</option>
                    <option value="REGISTRATION_CLOSED">REGISTRATION_CLOSED</option>
                    <option value="IN_PROGRESS">IN_PROGRESS</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </select>
                </div>

                <div className="row">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setSearch("");
                      setScopeFilter("ALL");
                      setStatusFilter("ALL");
                    }}
                  >
                    Reset filters
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="card" style={{ marginBottom: "24px" }}>
            <div
              className="row"
              style={{ justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <h2>My recent tournaments</h2>
                <p className="muted">
                  Quick access to the latest tournaments you created.
                </p>
              </div>

              <Link href="/my-tournaments" className="btn btn-secondary">
                View personal page
              </Link>
            </div>

            {!currentUser ? (
              <EmptyState
                title="Login required"
                description="Authenticate to see tournaments you own."
              />
            ) : recentMyTournaments.length === 0 ? (
              <EmptyState
                title="No tournaments created yet"
                description="Create your first tournament to see it here."
              />
            ) : (
              <div className="grid" style={{ marginTop: "18px" }}>
                {recentMyTournaments.map((tournament) => (
                  <Link
                    key={tournament.id}
                    href={`/tournaments/${tournament.id}`}
                    className="card"
                  >
                    <div
                      className="row"
                      style={{
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: "12px",
                      }}
                    >
                      <div>
                        <p className="muted">Tournament #{tournament.id}</p>
                        <strong>{tournament.name}</strong>
                      </div>

                      <StatusBadge value={tournament.status} />
                    </div>

                    <p style={{ marginTop: "8px" }}>
                      {tournament.description || "No description provided."}
                    </p>

                    <div
                      className="grid grid-2"
                      style={{ marginTop: "16px", gap: "12px" }}
                    >
                      <div>
                        <p className="muted">Discipline</p>
                        <strong>{tournament.discipline}</strong>
                      </div>

                      <div>
                        <p className="muted">Format</p>
                        <strong>{tournament.format}</strong>
                      </div>

                      <div>
                        <p className="muted">Starts at</p>
                        <strong>{formatDate(tournament.starts_at)}</strong>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>

          <section className="card">
            <div
              className="row"
              style={{ justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <h2>All tournaments</h2>
                <p className="muted">
                  Full tournament catalog with search and filter support.
                </p>
              </div>

              <strong>{filteredTournaments.length}</strong>
            </div>

            {tournaments.length === 0 ? (
              <EmptyState
                title="No tournaments yet"
                description="No tournaments have been created yet."
              />
            ) : filteredTournaments.length === 0 ? (
              <EmptyState
                title="No tournaments for current filters"
                description="Try changing the search text or filter configuration."
              />
            ) : (
              <div className="grid" style={{ marginTop: "18px" }}>
                {filteredTournaments.map((tournament) => {
                  const isMine =
                    currentUser && tournament.owner_id === currentUser.id;

                  return (
                    <Link
                      key={tournament.id}
                      href={`/tournaments/${tournament.id}`}
                      className="card"
                    >
                      <div
                        className="row"
                        style={{
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          gap: "12px",
                        }}
                      >
                        <div>
                          <p className="muted">Tournament #{tournament.id}</p>
                          <strong>{tournament.name}</strong>
                        </div>

                        <div className="row" style={{ gap: "8px" }}>
                          {isMine ? <span className="badge">My tournament</span> : null}
                          <StatusBadge value={tournament.status} />
                        </div>
                      </div>

                      <p style={{ marginTop: "8px" }}>
                        {tournament.description || "No description provided."}
                      </p>

                      <div
                        className="grid grid-2"
                        style={{ marginTop: "16px", gap: "12px" }}
                      >
                        <div>
                          <p className="muted">Discipline</p>
                          <strong>{tournament.discipline}</strong>
                        </div>

                        <div>
                          <p className="muted">Format</p>
                          <strong>{tournament.format}</strong>
                        </div>

                        <div>
                          <p className="muted">Starts at</p>
                          <strong>{formatDate(tournament.starts_at)}</strong>
                        </div>
                      </div>

                      <div className="row" style={{ marginTop: "16px" }}>
                        <span className="btn btn-secondary">Open tournament</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
