"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { listMyTeams, type TeamRead } from "@/src/shared/api/teams";
import { listMatches, type MatchListItem } from "@/src/shared/api/matches";
import { listTournaments, type TournamentListItem } from "@/src/shared/api/tournaments";
import { getAccessToken } from "@/src/shared/lib/auth";
import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

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

export default function MyMatchesPage() {
  const [myTeams, setMyTeams] = useState<TeamRead[]>([]);
  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [tournaments, setTournaments] = useState<TournamentListItem[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
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
    }

    void loadData();
  }, []);

  const teamIds = useMemo(() => new Set(myTeams.map((team) => team.id)), [myTeams]);

  const myMatches = useMemo(() => {
    return matches.filter(
      (match) => teamIds.has(match.home_team_id) || teamIds.has(match.away_team_id),
    );
  }, [matches, teamIds]);

  const teamMap = useMemo(() => buildTeamMap(myTeams), [myTeams]);
  const tournamentMap = useMemo(
    () => buildTournamentMap(tournaments),
    [tournaments],
  );

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">My matches</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Matches involving your teams
          </h1>
          <p className="page-subtitle">
            Quick access to matches where one of your teams participates.
          </p>
        </div>

        <div className="row">
          <Link href="/matches" className="btn btn-secondary">
            All matches
          </Link>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
        </div>
      </div>

      {isLoading ? <p>Loading your matches...</p> : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Failed to load matches">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !error && myMatches.length === 0 ? (
        <EmptyState
          title="No personal matches yet"
          description="None of your teams are linked to any matches yet."
          action={
            <Link href="/teams" className="btn btn-secondary">
              Open teams
            </Link>
          }
        />
      ) : null}

      {!isLoading && !error && myMatches.length > 0 ? (
        <div className="grid">
          {myMatches.map((match) => {
            const homeTeam = teamMap.get(match.home_team_id);
            const awayTeam = teamMap.get(match.away_team_id);
            const tournament = tournamentMap.get(match.tournament_id);

            return (
              <div key={match.id} className="card">
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <div>
                    <h3>
                      {homeTeam?.name ?? `Team #${match.home_team_id}`} vs{" "}
                      {awayTeam?.name ?? `Team #${match.away_team_id}`}
                    </h3>
                    <p>{tournament?.name ?? `Tournament #${match.tournament_id}`}</p>
                  </div>

                  <StatusBadge value={match.status} />
                </div>

                <div className="grid grid-2" style={{ marginTop: "16px", gap: "12px" }}>
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
                  <Link href={`/matches/${match.id}`} className="btn btn-secondary">
                    Open match
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
    </main>
  );
}