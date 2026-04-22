"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

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

export default function DashboardPage() {
  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [myTeams, setMyTeams] = useState<TeamRead[]>([]);
  const [allTournaments, setAllTournaments] = useState<TournamentListItem[]>([]);
  const [allMatches, setAllMatches] = useState<MatchListItem[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboardData() {
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
    }

    void loadDashboardData();
  }, []);

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

  const recentTeams = useMemo(() => {
    return sortByCreatedDesc(myTeams).slice(0, 3);
  }, [myTeams]);

  const recentTournaments = useMemo(() => {
    return sortByCreatedDesc(myTournaments).slice(0, 3);
  }, [myTournaments]);

  const recentMatches = useMemo(() => {
    return sortByCreatedDesc(myMatches).slice(0, 3);
  }, [myMatches]);

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">CyberHub Dashboard</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Welcome back{currentUser ? `, ${currentUser.username}` : ""}
          </h1>
          <p className="page-subtitle">
            Your personal control center for profile, teams, tournaments and
            matches.
          </p>
        </div>

        <div className="row">
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
        </div>
      </div>

      {isLoading || isLoadingCurrentUser ? <p>Loading dashboard...</p> : null}

      {!isLoading && !isLoadingCurrentUser && error ? (
        <Alert variant="error" title="Failed to load dashboard">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !isLoadingCurrentUser && !error ? (
        <>
          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <div className="card">
              <h3>Account snapshot</h3>
              <div className="grid" style={{ marginTop: "16px" }}>
                <div>
                  <p className="muted">Username</p>
                  <strong>{currentUser?.username ?? "-"}</strong>
                </div>

                <div>
                  <p className="muted">Email</p>
                  <strong>{currentUser?.email ?? "-"}</strong>
                </div>

                <div>
                  <p className="muted">Role</p>
                  <strong>{currentUser?.role ?? "-"}</strong>
                </div>
              </div>
            </div>

            <div className="card">
              <h3>Quick actions</h3>
              <div className="row" style={{ marginTop: "16px" }}>
                <Link href="/teams" className="btn btn-secondary">
                  Create team
                </Link>
                <Link href="/tournaments" className="btn btn-secondary">
                  Create tournament
                </Link>
                <Link href="/matches" className="btn btn-secondary">
                  Create match
                </Link>
              </div>
            </div>
          </div>

          <div className="stat-grid" style={{ marginBottom: "24px" }}>
            <div className="card stat-card">
              <div className="stat-label">My teams</div>
              <div className="stat-value">{myTeams.length}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">My tournaments</div>
              <div className="stat-value">{myTournaments.length}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">My matches</div>
              <div className="stat-value">{myMatches.length}</div>
            </div>
          </div>

          <div className="grid grid-3" style={{ marginBottom: "24px" }}>
            <section>
              <h2>Recent teams</h2>
              <p style={{ marginBottom: "20px" }}>
                Latest teams where you are a member.
              </p>

              {recentTeams.length === 0 ? (
                <EmptyState
                  title="No teams yet"
                  description="Create or join a team to see it here."
                  action={
                    <Link href="/teams" className="btn btn-secondary">
                      Open teams
                    </Link>
                  }
                />
              ) : (
                <div className="grid">
                  {recentTeams.map((team) => (
                    <div key={team.id} className="card">
                      <h3>{team.name}</h3>
                      <p>{team.description || "No description provided."}</p>

                      <div className="row" style={{ marginTop: "16px" }}>
                        <Link
                          href={`/teams/${team.id}`}
                          className="btn btn-secondary"
                        >
                          Open team
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2>Recent tournaments</h2>
              <p style={{ marginBottom: "20px" }}>
                Latest tournaments owned by you.
              </p>

              {recentTournaments.length === 0 ? (
                <EmptyState
                  title="No tournaments yet"
                  description="Create your first tournament to see it here."
                  action={
                    <Link href="/tournaments" className="btn btn-secondary">
                      Open tournaments
                    </Link>
                  }
                />
              ) : (
                <div className="grid">
                  {recentTournaments.map((tournament) => (
                    <div key={tournament.id} className="card">
                      <div
                        className="row"
                        style={{ justifyContent: "space-between" }}
                      >
                        <h3>{tournament.name}</h3>
                        <StatusBadge value={tournament.status} />
                      </div>

                      <p>{tournament.description || "No description provided."}</p>

                      <div className="grid" style={{ marginTop: "16px" }}>
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
                          Open tournament
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2>Recent matches</h2>
              <p style={{ marginBottom: "20px" }}>
                Latest matches involving your teams.
              </p>

              {recentMatches.length === 0 ? (
                <EmptyState
                  title="No matches yet"
                  description="Once your teams are linked to matches, they will appear here."
                  action={
                    <Link href="/matches" className="btn btn-secondary">
                      Open matches
                    </Link>
                  }
                />
              ) : (
                <div className="grid">
                  {recentMatches.map((match) => (
                    <div key={match.id} className="card">
                      <div
                        className="row"
                        style={{ justifyContent: "space-between" }}
                      >
                        <h3>
                          Team #{match.home_team_id} vs Team #{match.away_team_id}
                        </h3>
                        <StatusBadge value={match.status} />
                      </div>

                      <div className="grid" style={{ marginTop: "16px" }}>
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
                        <Link
                          href={`/matches/${match.id}`}
                          className="btn btn-secondary"
                        >
                          Open match
                        </Link>
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