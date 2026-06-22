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
import { useCurrentUser } from "@/src/hooks/use-current-user";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

function formatDate(value: string | null): string {
  if (!value) return "Not scheduled";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function sortByCreatedDesc<T extends { created_at: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const left = new Date(a.created_at).getTime();
    const right = new Date(b.created_at).getTime();
    return right - left;
  });
}

function sortMatchesForDashboard(matches: MatchListItem[]): MatchListItem[] {
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

export default function DashboardPage() {
  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [myTeams, setMyTeams] = useState<TeamRead[]>([]);
  const [allTournaments, setAllTournaments] = useState<TournamentListItem[]>([]);
  const [allMatches, setAllMatches] = useState<MatchListItem[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboardData = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      setError("You need to login to view your dashboard.");
      setIsLoading(false);
      return;
    }

    try {
      setError("");
      setIsLoading(true);

      const [teamsData, tournamentsData, matchesData] = await Promise.all([
        listMyTeams(token),
        listTournaments(),
        listMatches(),
      ]);

      setMyTeams(teamsData);
      setAllTournaments(tournamentsData);
      setAllMatches(matchesData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load dashboard data",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboardData();
  }, [loadDashboardData]);

  const myTeamIds = useMemo(() => {
    return new Set(myTeams.map((team) => team.id));
  }, [myTeams]);

  const myTournaments = useMemo(() => {
    if (!currentUser) return [];

    return allTournaments.filter(
      (tournament) => tournament.owner_id === currentUser.id,
    );
  }, [allTournaments, currentUser]);

  const myMatches = useMemo(() => {
    return allMatches.filter(
      (match) =>
        myTeamIds.has(match.home_team_id) || myTeamIds.has(match.away_team_id),
    );
  }, [allMatches, myTeamIds]);

  const upcomingMatches = useMemo(() => {
    const now = Date.now();

    return sortMatchesForDashboard(
      myMatches.filter((match) => {
        if (!match.scheduled_at) return false;
        if (match.status === "COMPLETED" || match.status === "CANCELLED") {
          return false;
        }

        return new Date(match.scheduled_at).getTime() >= now;
      }),
    ).slice(0, 4);
  }, [myMatches]);

  const recentTeams = useMemo(() => {
    return sortByCreatedDesc(myTeams).slice(0, 4);
  }, [myTeams]);

  const recentTournaments = useMemo(() => {
    return sortByCreatedDesc(myTournaments).slice(0, 4);
  }, [myTournaments]);

  const recentMatches = useMemo(() => {
    return sortMatchesForDashboard(myMatches).slice(0, 4);
  }, [myMatches]);

  const openPlatformTournaments = useMemo(() => {
    return allTournaments.filter(
      (tournament) => tournament.status === "REGISTRATION_OPEN",
    ).length;
  }, [allTournaments]);

  const activeOwnedTournaments = useMemo(() => {
    return myTournaments.filter(
      (tournament) =>
        tournament.status === "REGISTRATION_OPEN" ||
        tournament.status === "REGISTRATION_CLOSED" ||
        tournament.status === "IN_PROGRESS",
    ).length;
  }, [myTournaments]);

  const completedMyMatches = useMemo(() => {
    return myMatches.filter((match) => match.status === "COMPLETED").length;
  }, [myMatches]);

  const scheduledMyMatches = useMemo(() => {
    return myMatches.filter(
      (match) =>
        match.status !== "COMPLETED" && match.status !== "CANCELLED",
    ).length;
  }, [myMatches]);

  const dashboardReady =
    !isLoading && !isLoadingCurrentUser && !error && Boolean(currentUser);

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">CyberHub Dashboard</p>
        <h1>
          Welcome back{currentUser ? `, ${currentUser.username}` : ""}
        </h1>
        <p>
          Your control center for profile, teams, tournaments and matches.
        </p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/profile" className="btn btn-secondary">
            Profile
          </Link>
          <Link href="/my-teams" className="btn btn-secondary">
            My teams
          </Link>
          <Link href="/my-tournaments" className="btn btn-secondary">
            My tournaments
          </Link>
          <Link href="/my-matches" className="btn btn-secondary">
            My matches
          </Link>
          <button type="button" onClick={() => void loadDashboardData()}>
            Refresh dashboard
          </button>
        </div>
      </section>

      {isLoading || isLoadingCurrentUser ? (
        <section className="card">
          <h2>Loading dashboard...</h2>
          <p>Please wait while we load your workspace.</p>
        </section>
      ) : null}

      {!isLoading && !isLoadingCurrentUser && error ? (
        <Alert variant="error" title="Dashboard unavailable">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !isLoadingCurrentUser && !error && !currentUser ? (
        <EmptyState
          title="Login required"
          description="You need to login to access the dashboard."
          action={
            <Link href="/login" className="btn btn-secondary">
              Go to login
            </Link>
          }
        />
      ) : null}

      {dashboardReady && currentUser ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">Username</p>
              <strong>{currentUser.username}</strong>
            </div>

            <div className="card">
              <p className="muted">Email</p>
              <strong>{currentUser.email}</strong>
            </div>

            <div className="card">
              <p className="muted">Role</p>
              <StatusBadge value={currentUser.role} />
            </div>

            <div className="card">
              <p className="muted">Account status</p>
              <strong>{currentUser.is_active ? "Active" : "Inactive"}</strong>
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Quick actions</h2>
              <p style={{ marginBottom: "16px" }}>
                Jump straight into the main workflow areas.
              </p>

              <div className="grid grid-2">
                <Link href="/teams" className="card">
                  <p className="muted">Teams</p>
                  <strong>Create or manage teams</strong>
                </Link>

                <Link href="/tournaments" className="card">
                  <p className="muted">Tournaments</p>
                  <strong>Create or manage tournaments</strong>
                </Link>

                <Link href="/matches" className="card">
                  <p className="muted">Matches</p>
                  <strong>Create or manage matches</strong>
                </Link>

                <Link href="/profile" className="card">
                  <p className="muted">Profile</p>
                  <strong>Open account settings</strong>
                </Link>
              </div>
            </div>

            <div className="card">
              <h2>Workspace summary</h2>

              <div
                className="grid grid-2"
                style={{ marginTop: "16px", gap: "12px" }}
              >
                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">My teams</p>
                  <strong>{myTeams.length}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">My tournaments</p>
                  <strong>{myTournaments.length}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">My matches</p>
                  <strong>{myMatches.length}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Open tournaments</p>
                  <strong>{openPlatformTournaments}</strong>
                </div>
              </div>
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Activity snapshot</h2>

              <div className="grid" style={{ gap: "12px", marginTop: "16px" }}>
                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Active tournaments you own</p>
                  <strong>{activeOwnedTournaments}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Scheduled or active matches</p>
                  <strong>{scheduledMyMatches}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Completed matches</p>
                  <strong>{completedMyMatches}</strong>
                </div>
              </div>
            </div>

            <div className="card">
              <h2>Next steps</h2>

              {myTeams.length === 0 ? (
                <EmptyState
                  title="Create your first team"
                  description="You need at least one team before you can participate in team tournaments and matches."
                  action={
                    <Link href="/teams" className="btn btn-secondary">
                      Go to teams
                    </Link>
                  }
                />
              ) : openPlatformTournaments === 0 ? (
                <EmptyState
                  title="No open tournaments right now"
                  description="You already have teams, but there are no tournaments with open registration at the moment."
                  action={
                    <Link href="/tournaments" className="btn btn-secondary">
                      Browse tournaments
                    </Link>
                  }
                />
              ) : (
                <div className="grid" style={{ gap: "12px", marginTop: "16px" }}>
                  <div className="card" style={{ padding: "16px" }}>
                    <strong>You are ready to join tournaments</strong>
                    <p className="muted" style={{ marginTop: "8px" }}>
                      Your teams are available, and there are tournaments with open registration.
                    </p>
                  </div>

                  <div className="row">
                    <Link href="/tournaments" className="btn btn-secondary">
                      Open tournaments
                    </Link>
                    <Link href="/my-teams" className="btn btn-secondary">
                      Review my teams
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <div
                className="row"
                style={{ justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <h2>Recent teams</h2>
                  <p className="muted">Latest teams linked to your account.</p>
                </div>

                <Link href="/my-teams" className="btn btn-secondary">
                  View all
                </Link>
              </div>

              {recentTeams.length === 0 ? (
                <EmptyState
                  title="No teams yet"
                  description="Create your first team to start participating."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
                  {recentTeams.map((team) => (
                    <Link key={team.id} href={`/teams/${team.id}`} className="card">
                      <p className="muted">Team</p>
                      <strong>{team.name}</strong>
                      <p style={{ marginTop: "8px" }}>
                        {team.description || "No description provided."}
                      </p>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <div
                className="row"
                style={{ justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <h2>Recent tournaments</h2>
                  <p className="muted">Tournaments you created.</p>
                </div>

                <Link href="/my-tournaments" className="btn btn-secondary">
                  View all
                </Link>
              </div>

              {recentTournaments.length === 0 ? (
                <EmptyState
                  title="No tournaments yet"
                  description="Create your first tournament to start organizing matches."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
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
                          <p className="muted">Tournament</p>
                          <strong>{tournament.name}</strong>
                        </div>

                        <StatusBadge value={tournament.status} />
                      </div>

                      <p style={{ marginTop: "8px" }}>
                        {tournament.description || "No description provided."}
                      </p>

                      <p className="muted" style={{ marginTop: "8px" }}>
                        Starts: {formatDate(tournament.starts_at)}
                      </p>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <div
                className="row"
                style={{ justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <h2>Upcoming matches</h2>
                  <p className="muted">
                    Scheduled matches linked to your teams.
                  </p>
                </div>

                <Link href="/my-matches" className="btn btn-secondary">
                  View all
                </Link>
              </div>

              {upcomingMatches.length === 0 ? (
                <EmptyState
                  title="No upcoming matches"
                  description="Scheduled matches for your teams will appear here."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
                  {upcomingMatches.map((match) => (
                    <Link
                      key={match.id}
                      href={`/matches/${match.id}`}
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
                          <p className="muted">Match #{match.id}</p>
                          <strong>
                            Team #{match.home_team_id} vs Team #{match.away_team_id}
                          </strong>
                        </div>

                        <StatusBadge value={match.status} />
                      </div>

                      <p className="muted" style={{ marginTop: "8px" }}>
                        Scheduled: {formatDate(match.scheduled_at)}
                      </p>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <div
                className="row"
                style={{ justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <h2>Recent match activity</h2>
                  <p className="muted">Latest matches related to your teams.</p>
                </div>

                <Link href="/my-matches" className="btn btn-secondary">
                  View all
                </Link>
              </div>

              {recentMatches.length === 0 ? (
                <EmptyState
                  title="No matches yet"
                  description="Your team-related matches will appear here."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
                  {recentMatches.map((match) => (
                    <Link
                      key={match.id}
                      href={`/matches/${match.id}`}
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
                          <p className="muted">Match #{match.id}</p>
                          <strong>
                            Team #{match.home_team_id} vs Team #{match.away_team_id}
                          </strong>
                        </div>

                        <StatusBadge value={match.status} />
                      </div>

                      <p style={{ marginTop: "8px" }}>
                        Score: {match.home_score ?? "-"} : {match.away_score ?? "-"}
                      </p>

                      <p className="muted" style={{ marginTop: "8px" }}>
                        Scheduled: {formatDate(match.scheduled_at)}
                      </p>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="card">
            <div
              className="row"
              style={{ justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <h2>Platform snapshot</h2>
                <p className="muted">
                  High-level view of current platform activity.
                </p>
              </div>

              <Link href="/tournaments" className="btn btn-secondary">
                Browse tournaments
              </Link>
            </div>

            <div
              className="grid grid-2"
              style={{ marginTop: "18px", gap: "12px" }}
            >
              <div className="card" style={{ padding: "16px" }}>
                <p className="muted">All tournaments</p>
                <strong>{allTournaments.length}</strong>
              </div>

              <div className="card" style={{ padding: "16px" }}>
                <p className="muted">All matches</p>
                <strong>{allMatches.length}</strong>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
