"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { listMatches, type MatchListItem } from "@/src/shared/api/matches";
import { listMyTeams, type TeamRead } from "@/src/shared/api/teams";
import {
  listTournaments,
  type TournamentListItem,
} from "@/src/shared/api/tournaments";
import { getAccessToken } from "@/src/shared/lib/auth";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

type ScopeFilter = "ALL" | "UPCOMING" | "ACTIVE" | "COMPLETED" | "CANCELLED";

function formatDate(value: string | null): string {
  if (!value) return "Not scheduled";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function buildTeamMap(teams: TeamRead[]): Map<number, TeamRead> {
  return new Map(teams.map((team) => [team.id, team]));
}

function buildTournamentMap(
  tournaments: TournamentListItem[],
): Map<number, TournamentListItem> {
  return new Map(tournaments.map((item) => [item.id, item]));
}

function sortMatches(matches: MatchListItem[]): MatchListItem[] {
  return [...matches].sort((a, b) => {
    if (a.scheduled_at && b.scheduled_at) {
      return (
        new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
      );
    }

    if (a.scheduled_at && !b.scheduled_at) return -1;
    if (!a.scheduled_at && b.scheduled_at) return 1;

    return b.id - a.id;
  });
}

function getScopeMatch(scope: ScopeFilter, match: MatchListItem): boolean {
  const now = Date.now();
  const scheduledAt = match.scheduled_at
    ? new Date(match.scheduled_at).getTime()
    : null;

  switch (scope) {
    case "UPCOMING":
      return (
        match.status !== "COMPLETED" &&
        match.status !== "CANCELLED" &&
        scheduledAt !== null &&
        scheduledAt >= now
      );

    case "ACTIVE":
      return match.status === "IN_PROGRESS" || match.status === "SCHEDULED";

    case "COMPLETED":
      return match.status === "COMPLETED";

    case "CANCELLED":
      return match.status === "CANCELLED";

    case "ALL":
    default:
      return true;
  }
}

function getRelatedTeams(match: MatchListItem, myTeamIds: Set<number>): string {
  const related: string[] = [];

  if (myTeamIds.has(match.home_team_id)) related.push("home");
  if (myTeamIds.has(match.away_team_id)) related.push("away");

  if (related.length === 2) return "Both sides";
  if (related.length === 1) return related[0] === "home" ? "Home side" : "Away side";
  return "Indirect";
}

export default function MyMatchesPage() {
  const [myTeams, setMyTeams] = useState<TeamRead[]>([]);
  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [tournaments, setTournaments] = useState<TournamentListItem[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [teamFilter, setTeamFilter] = useState("ALL");

  const loadData = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      setError("You need to login to view your matches.");
      setIsLoading(false);
      return;
    }

    try {
      setError("");
      setIsLoading(true);

      const [myTeamsData, matchesData, tournamentsData] = await Promise.all([
        listMyTeams(token),
        listMatches(),
        listTournaments(),
      ]);

      setMyTeams(myTeamsData);
      setMatches(matchesData);
      setTournaments(tournamentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load your matches");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const teamIds = useMemo(() => new Set(myTeams.map((team) => team.id)), [myTeams]);
  const teamMap = useMemo(() => buildTeamMap(myTeams), [myTeams]);
  const tournamentMap = useMemo(
    () => buildTournamentMap(tournaments),
    [tournaments],
  );

  const myMatches = useMemo(() => {
    return matches.filter(
      (match) =>
        teamIds.has(match.home_team_id) || teamIds.has(match.away_team_id),
    );
  }, [matches, teamIds]);

  const filteredMatches = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return sortMatches(
      myMatches.filter((match) => {
        const homeTeam = teamMap.get(match.home_team_id);
        const awayTeam = teamMap.get(match.away_team_id);
        const tournament = tournamentMap.get(match.tournament_id);

        const matchesSearch =
          !normalizedSearch ||
          homeTeam?.name.toLowerCase().includes(normalizedSearch) ||
          awayTeam?.name.toLowerCase().includes(normalizedSearch) ||
          tournament?.name.toLowerCase().includes(normalizedSearch) ||
          String(match.id).includes(normalizedSearch);

        const matchesScope = getScopeMatch(scopeFilter, match);

        const matchesStatus =
          statusFilter === "ALL" || match.status === statusFilter;

        const matchesTeam =
          teamFilter === "ALL" ||
          String(match.home_team_id) === teamFilter ||
          String(match.away_team_id) === teamFilter;

        return matchesSearch && matchesScope && matchesStatus && matchesTeam;
      }),
    );
  }, [myMatches, teamMap, tournamentMap, search, scopeFilter, statusFilter, teamFilter]);

  const upcomingCount = useMemo(
    () =>
      myMatches.filter((match) => getScopeMatch("UPCOMING", match)).length,
    [myMatches],
  );

  const activeCount = useMemo(
    () => myMatches.filter((match) => getScopeMatch("ACTIVE", match)).length,
    [myMatches],
  );

  const completedCount = useMemo(
    () => myMatches.filter((match) => match.status === "COMPLETED").length,
    [myMatches],
  );

  const recentCompleted = useMemo(() => {
    return sortMatches(
      myMatches.filter((match) => match.status === "COMPLETED"),
    ).slice(0, 3);
  }, [myMatches]);

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">My matches</p>
        <h1>Matches involving your teams</h1>
        <p>
          Track upcoming, active and completed matches linked to the teams you manage.
        </p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/matches" className="btn btn-secondary">
            All matches
          </Link>
          <Link href="/my-teams" className="btn btn-secondary">
            My teams
          </Link>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
          <button type="button" onClick={() => void loadData()}>
            Refresh
          </button>
        </div>
      </section>

      {isLoading ? (
        <section className="card">
          <h2>Loading your matches...</h2>
          <p>Please wait while we gather your match activity.</p>
        </section>
      ) : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Failed to load matches">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !error ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">All my matches</p>
              <strong>{myMatches.length}</strong>
            </div>

            <div className="card">
              <p className="muted">Upcoming</p>
              <strong>{upcomingCount}</strong>
            </div>

            <div className="card">
              <p className="muted">Scheduled or active</p>
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
              <h2>Filters</h2>

              <div className="grid" style={{ gap: "14px", marginTop: "16px" }}>
                <div className="form-group">
                  <label htmlFor="match-search">Search</label>
                  <input
                    id="match-search"
                    type="text"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search by team, tournament or match id"
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
                    <option value="UPCOMING">Upcoming</option>
                    <option value="ACTIVE">Scheduled or active</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="CANCELLED">Cancelled</option>
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
                    <option value="SCHEDULED">SCHEDULED</option>
                    <option value="IN_PROGRESS">IN_PROGRESS</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="team-filter">Team</label>
                  <select
                    id="team-filter"
                    value={teamFilter}
                    onChange={(event) => setTeamFilter(event.target.value)}
                  >
                    <option value="ALL">All my teams</option>
                    {myTeams.map((team) => (
                      <option key={team.id} value={String(team.id)}>
                        {team.name}
                      </option>
                    ))}
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
                      setTeamFilter("ALL");
                    }}
                  >
                    Reset filters
                  </button>
                </div>
              </div>
            </div>

            <div className="card">
              <h2>Recent completed matches</h2>

              {recentCompleted.length === 0 ? (
                <EmptyState
                  title="No completed matches"
                  description="Completed matches for your teams will appear here."
                />
              ) : (
                <div className="grid" style={{ gap: "12px", marginTop: "16px" }}>
                  {recentCompleted.map((match) => {
                    const homeTeam = teamMap.get(match.home_team_id);
                    const awayTeam = teamMap.get(match.away_team_id);
                    const tournament = tournamentMap.get(match.tournament_id);

                    return (
                      <Link key={match.id} href={`/matches/${match.id}`} className="card">
                        <div
                          className="row"
                          style={{
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            gap: "12px",
                          }}
                        >
                          <div>
                            <p className="muted">Match #{match.id}</p>
                            <strong>
                              {homeTeam?.name ?? `Team #${match.home_team_id}`} vs{" "}
                              {awayTeam?.name ?? `Team #${match.away_team_id}`}
                            </strong>
                          </div>

                          <StatusBadge value={match.status} />
                        </div>

                        <p style={{ marginTop: "8px" }}>
                          Score: {match.home_score ?? "-"} : {match.away_score ?? "-"}
                        </p>

                        <p className="muted" style={{ marginTop: "8px" }}>
                          {tournament?.name ?? `Tournament #${match.tournament_id}`}
                        </p>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </section>

          {myMatches.length === 0 ? (
            <EmptyState
              title="No matches yet"
              description="Your matches will appear here once one of your teams participates in a tournament match."
              action={
                <Link href="/my-teams" className="btn btn-secondary">
                  Open teams
                </Link>
              }
            />
          ) : filteredMatches.length === 0 ? (
            <EmptyState
              title="No matches for current filters"
              description="Try changing the search text or filter values."
            />
          ) : (
            <section className="card">
              <div
                className="row"
                style={{ justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <h2>Filtered matches</h2>
                  <p className="muted">
                    Matches currently matching your search and filter settings.
                  </p>
                </div>

                <strong>{filteredMatches.length}</strong>
              </div>

              <div className="grid" style={{ marginTop: "18px" }}>
                {filteredMatches.map((match) => {
                  const homeTeam = teamMap.get(match.home_team_id);
                  const awayTeam = teamMap.get(match.away_team_id);
                  const tournament = tournamentMap.get(match.tournament_id);

                  return (
                    <Link key={match.id} href={`/matches/${match.id}`} className="card">
                      <div
                        className="row"
                        style={{
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          gap: "12px",
                        }}
                      >
                        <div>
                          <p className="muted">Match #{match.id}</p>
                          <strong>
                            {homeTeam?.name ?? `Team #${match.home_team_id}`} vs{" "}
                            {awayTeam?.name ?? `Team #${match.away_team_id}`}
                          </strong>
                        </div>

                        <StatusBadge value={match.status} />
                      </div>

                      <div
                        className="grid grid-2"
                        style={{ marginTop: "16px", gap: "12px" }}
                      >
                        <div>
                          <p className="muted">Tournament</p>
                          <strong>
                            {tournament?.name ?? `Tournament #${match.tournament_id}`}
                          </strong>
                        </div>

                        <div>
                          <p className="muted">Your relation</p>
                          <strong>{getRelatedTeams(match, teamIds)}</strong>
                        </div>

                        <div>
                          <p className="muted">Scheduled at</p>
                          <strong>{formatDate(match.scheduled_at)}</strong>
                        </div>

                        <div>
                          <p className="muted">Score</p>
                          <strong>
                            {match.home_score ?? "-"} : {match.away_score ?? "-"}
                          </strong>
                        </div>
                      </div>

                      <div className="row" style={{ marginTop: "16px" }}>
                        <span className="btn btn-secondary">Open match</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}
        </>
      ) : null}
    </main>
  );
}