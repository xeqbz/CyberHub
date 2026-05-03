"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import {
  getOverviewStats,
  listTeamStats,
  listTournamentStats,
  type OverviewStats,
  type TeamStats,
  type TournamentStats,
} from "@/src/shared/api/platform";

export default function StatisticsPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [teams, setTeams] = useState<TeamStats[]>([]);
  const [tournaments, setTournaments] = useState<TournamentStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadStatistics() {
    try {
      setError("");
      setIsLoading(true);
      const [overviewData, teamData, tournamentData] = await Promise.all([
        getOverviewStats(),
        listTeamStats(),
        listTournamentStats(),
      ]);
      setOverview(overviewData);
      setTeams(teamData);
      setTournaments(tournamentData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load statistics");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadStatistics();
  }, []);

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Statistics</p>
        <h1>Platform analytics</h1>
        <p>Aggregated players, teams, tournaments, matches and disputes.</p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/rankings" className="btn btn-secondary">
            Rankings
          </Link>
          <Link href="/tournaments" className="btn btn-secondary">
            Tournaments
          </Link>
          <button type="button" onClick={() => void loadStatistics()}>
            Refresh
          </button>
        </div>
      </section>

      {isLoading ? (
        <section className="card">
          <h2>Loading statistics...</h2>
        </section>
      ) : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Statistics unavailable">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !error && overview ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            {Object.entries(overview).map(([key, value]) => (
              <div key={key} className="card">
                <p className="muted">{key.replaceAll("_", " ")}</p>
                <strong>{value}</strong>
              </div>
            ))}
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Team performance</h2>
              {teams.length === 0 ? (
                <EmptyState
                  title="No team data"
                  description="Team statistics will appear after completed matches."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
                  {teams.map((team) => (
                    <div key={team.team_id} className="card">
                      <h3>{team.name}</h3>
                      <div className="grid grid-3" style={{ marginTop: "14px" }}>
                        <div>
                          <p className="muted">Matches</p>
                          <strong>{team.matches}</strong>
                        </div>
                        <div>
                          <p className="muted">Wins</p>
                          <strong>{team.wins}</strong>
                        </div>
                        <div>
                          <p className="muted">Losses</p>
                          <strong>{team.losses}</strong>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h2>Tournament progress</h2>
              {tournaments.length === 0 ? (
                <EmptyState
                  title="No tournaments"
                  description="Tournament analytics will appear after creation."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
                  {tournaments.map((tournament) => (
                    <Link
                      key={tournament.tournament_id}
                      href={`/tournaments/${tournament.tournament_id}`}
                      className="card"
                    >
                      <h3>{tournament.name}</h3>
                      <p className="muted">
                        {tournament.discipline} · {tournament.format}
                      </p>
                      <div className="grid grid-3" style={{ marginTop: "14px" }}>
                        <div>
                          <p className="muted">Teams</p>
                          <strong>{tournament.participants}</strong>
                        </div>
                        <div>
                          <p className="muted">Matches</p>
                          <strong>{tournament.matches}</strong>
                        </div>
                        <div>
                          <p className="muted">Done</p>
                          <strong>{tournament.completed_matches}</strong>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
