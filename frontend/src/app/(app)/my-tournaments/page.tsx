"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  listTournaments,
  type TournamentListItem,
} from "@/src/shared/api/tournaments";
import { useCurrentUser } from "@/src/hooks/use-current-user";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

type ScopeFilter =
  | "ALL"
  | "ACTIVE"
  | "REGISTRATION_OPEN"
  | "COMPLETED"
  | "UPCOMING";

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

function getScopeMatch(
  scope: ScopeFilter,
  tournament: TournamentListItem,
): boolean {
  const now = Date.now();
  const startsAt = tournament.starts_at
    ? new Date(tournament.starts_at).getTime()
    : null;

  switch (scope) {
    case "ACTIVE":
      return (
        tournament.status === "REGISTRATION_OPEN" ||
        tournament.status === "REGISTRATION_CLOSED" ||
        tournament.status === "IN_PROGRESS"
      );

    case "REGISTRATION_OPEN":
      return tournament.status === "REGISTRATION_OPEN";

    case "COMPLETED":
      return tournament.status === "COMPLETED";

    case "UPCOMING":
      return (
        startsAt !== null &&
        startsAt >= now &&
        tournament.status !== "COMPLETED" &&
        tournament.status !== "CANCELLED"
      );

    case "ALL":
    default:
      return true;
  }
}

export default function MyTournamentsPage() {
  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [tournaments, setTournaments] = useState<TournamentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const loadTournaments = useCallback(async () => {
    try {
      setError("");
      setIsLoading(true);

      const data = await listTournaments();
      setTournaments(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load tournaments",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTournaments();
  }, [loadTournaments]);

  const myTournaments = useMemo(() => {
    if (!currentUser) return [];

    return tournaments.filter((item) => item.owner_id === currentUser.id);
  }, [currentUser, tournaments]);

  const filteredTournaments = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return sortTournaments(
      myTournaments.filter((tournament) => {
        const matchesSearch =
          !normalizedSearch ||
          tournament.name.toLowerCase().includes(normalizedSearch) ||
          tournament.description?.toLowerCase().includes(normalizedSearch) ||
          String(tournament.id).includes(normalizedSearch);

        const matchesScope = getScopeMatch(scopeFilter, tournament);

        const matchesStatus =
          statusFilter === "ALL" || tournament.status === statusFilter;

        return matchesSearch && matchesScope && matchesStatus;
      }),
    );
  }, [myTournaments, search, scopeFilter, statusFilter]);

  const activeCount = useMemo(
    () => myTournaments.filter((item) => getScopeMatch("ACTIVE", item)).length,
    [myTournaments],
  );

  const openRegistrationCount = useMemo(
    () =>
      myTournaments.filter((item) => item.status === "REGISTRATION_OPEN").length,
    [myTournaments],
  );

  const upcomingCount = useMemo(
    () => myTournaments.filter((item) => getScopeMatch("UPCOMING", item)).length,
    [myTournaments],
  );

  const completedCount = useMemo(
    () => myTournaments.filter((item) => item.status === "COMPLETED").length,
    [myTournaments],
  );

  const recentTournaments = useMemo(() => {
    return [...myTournaments]
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      .slice(0, 3);
  }, [myTournaments]);

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">My tournaments</p>
        <h1>Tournaments you own</h1>
        <p>
          Track tournaments you created, monitor their status and jump straight
          into management.
        </p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/tournaments" className="btn btn-secondary">
            All tournaments
          </Link>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
          <button type="button" onClick={() => void loadTournaments()}>
            Refresh
          </button>
        </div>
      </section>

      {isLoading || isLoadingCurrentUser ? (
        <section className="card">
          <h2>Loading your tournaments...</h2>
          <p>Please wait while we load your organizer workspace.</p>
        </section>
      ) : null}

      {!isLoading && !isLoadingCurrentUser && error ? (
        <Alert variant="error" title="Failed to load tournaments">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !isLoadingCurrentUser && !error && myTournaments.length > 0 ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">All my tournaments</p>
              <strong>{myTournaments.length}</strong>
            </div>

            <div className="card">
              <p className="muted">Active</p>
              <strong>{activeCount}</strong>
            </div>

            <div className="card">
              <p className="muted">Open registration</p>
              <strong>{openRegistrationCount}</strong>
            </div>

            <div className="card">
              <p className="muted">Upcoming</p>
              <strong>{upcomingCount}</strong>
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
              <h2>Filters</h2>

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
                  <label htmlFor="scope-filter">Scope</label>
                  <select
                    id="scope-filter"
                    value={scopeFilter}
                    onChange={(event) =>
                      setScopeFilter(event.target.value as ScopeFilter)
                    }
                  >
                    <option value="ALL">All</option>
                    <option value="ACTIVE">Active</option>
                    <option value="REGISTRATION_OPEN">Open registration</option>
                    <option value="UPCOMING">Upcoming</option>
                    <option value="COMPLETED">Completed</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="status-filter">Exact status</label>
                  <select
                    id="status-filter"
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

            <div className="card">
              <h2>Recent tournaments</h2>

              {recentTournaments.length === 0 ? (
                <EmptyState
                  title="No tournaments yet"
                  description="Your latest tournaments will appear here."
                />
              ) : (
                <div className="grid" style={{ gap: "12px", marginTop: "16px" }}>
                  {recentTournaments.map((tournament) => (
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
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </section>

          {filteredTournaments.length === 0 ? (
            <EmptyState
              title="No tournaments for current filters"
              description="Try changing the search text or filter settings."
            />
          ) : (
            <section className="card">
              <div
                className="row"
                style={{ justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <h2>Filtered tournaments</h2>
                  <p className="muted">
                    Tournaments currently matching your search and filters.
                  </p>
                </div>

                <strong>{filteredTournaments.length}</strong>
              </div>

              <div className="grid" style={{ marginTop: "18px" }}>
                {filteredTournaments.map((tournament) => (
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
                        <p className="muted">Max teams</p>
                        <strong>{tournament.max_teams}</strong>
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
                ))}
              </div>
            </section>
          )}
        </>
      ) : null}

      {!isLoading && !isLoadingCurrentUser && !error && myTournaments.length === 0 ? (
        <EmptyState
          title="You do not own tournaments yet"
          description="Create your first tournament to start managing competition flow."
          action={
            <Link href="/tournaments" className="btn btn-secondary">
              Open tournaments
            </Link>
          }
        />
      ) : null}
    </main>
  );
}