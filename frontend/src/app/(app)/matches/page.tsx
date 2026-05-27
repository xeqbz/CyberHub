"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { listTeams, type TeamListItem } from "@/src/shared/api/teams";
import { createMatch, listMatches, type MatchListItem } from "@/src/shared/api/matches";
import { listTournaments, type TournamentListItem } from "@/src/shared/api/tournaments";
import { getAccessToken, isAuthenticated } from "@/src/shared/lib/auth";
import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

function formatDate(value: string | null): string {
  if (!value) return "Not scheduled";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function buildTeamMap(teams: TeamListItem[]): Map<number, TeamListItem> {
  return new Map(teams.map((team) => [team.id, team]));
}

function buildTournamentMap(
  tournaments: TournamentListItem[],
): Map<number, TournamentListItem> {
  return new Map(tournaments.map((item) => [item.id, item]));
}

export default function MatchesPage() {
  const authenticated = useMemo(() => isAuthenticated(), []);

  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [teams, setTeams] = useState<TeamListItem[]>([]);
  const [tournaments, setTournaments] = useState<TournamentListItem[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [tournamentId, setTournamentId] = useState("");
  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");

  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoadError("");
        setIsLoading(true);

        const [matchesData, teamsData, tournamentsData] = await Promise.all([
          listMatches(),
          listTeams(),
          listTournaments(),
        ]);

        setMatches(matchesData);
        setTeams(teamsData);
        setTournaments(tournamentsData);
      } catch (err) {
        setLoadError(
          err instanceof Error ? err.message : "Failed to load matches data",
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  async function handleCreateMatch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();

    if (!token) {
      setCreateError("You need to login before creating a match");
      return;
    }

    if (!tournamentId || !homeTeamId || !awayTeamId) {
      setCreateError("Tournament and both teams are required");
      return;
    }

    if (homeTeamId === awayTeamId) {
      setCreateError("Home team and away team must be different");
      return;
    }

    setCreateError("");
    setCreateSuccess("");
    setIsCreating(true);

    try {
      const createdMatch = await createMatch(
        {
          tournament_id: Number(tournamentId),
          home_team_id: Number(homeTeamId),
          away_team_id: Number(awayTeamId),
          scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        },
        token,
      );

      setCreateSuccess(`Match #${createdMatch.id} created successfully`);
      setTournamentId("");
      setHomeTeamId("");
      setAwayTeamId("");
      setScheduledAt("");

      setMatches((prev) => [
        {
          id: createdMatch.id,
          tournament_id: createdMatch.tournament_id,
          home_team_id: createdMatch.home_team_id,
          away_team_id: createdMatch.away_team_id,
          status: createdMatch.status,
          scheduled_at: createdMatch.scheduled_at,
          completed_at: createdMatch.completed_at,
          stage: createdMatch.stage,
          round_number: createdMatch.round_number,
          bracket_position: createdMatch.bracket_position,
          home_score: createdMatch.home_score,
          away_score: createdMatch.away_score,
          winner_team_id: createdMatch.winner_team_id,
          result_confirmed_by_id: createdMatch.result_confirmed_by_id,
          proposed_home_score: createdMatch.proposed_home_score,
          proposed_away_score: createdMatch.proposed_away_score,
          proposed_winner_team_id: createdMatch.proposed_winner_team_id,
          result_submitted_by_id: createdMatch.result_submitted_by_id,
          result_submitted_at: createdMatch.result_submitted_at,
          created_at: createdMatch.created_at,
          updated_at: createdMatch.updated_at,
        },
        ...prev,
      ]);
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create match",
      );
    } finally {
      setIsCreating(false);
    }
  }

  const teamMap = useMemo(() => buildTeamMap(teams), [teams]);
  const tournamentMap = useMemo(
    () => buildTournamentMap(tournaments),
    [tournaments],
  );

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Matches</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Create and manage matches
          </h1>
          <p className="page-subtitle">
            Browse scheduled matches, inspect match details and create new
            matches for tournaments.
          </p>
        </div>

        <div className="row">
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
          <Link href="/teams" className="btn btn-secondary">
            Teams
          </Link>
          <Link href="/tournaments" className="btn btn-secondary">
            Tournaments
          </Link>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: "24px" }}>
        <section>
          <h2>Create match</h2>
          <p style={{ marginBottom: "20px" }}>
            Only the tournament owner can create matches for a tournament.
          </p>

          {!authenticated ? (
            <EmptyState
              title="Login required"
              description="You need to sign in before creating a match."
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
            <form onSubmit={handleCreateMatch}>
              <div className="form-group">
                <label htmlFor="match-tournament">Tournament</label>
                <select
                  id="match-tournament"
                  value={tournamentId}
                  onChange={(event) => setTournamentId(event.target.value)}
                  required
                >
                  <option value="">Choose tournament</option>
                  {tournaments.map((tournament) => (
                    <option key={tournament.id} value={tournament.id}>
                      {tournament.name} ({tournament.status})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-2">
                <div className="form-group">
                  <label htmlFor="home-team">Home team</label>
                  <select
                    id="home-team"
                    value={homeTeamId}
                    onChange={(event) => setHomeTeamId(event.target.value)}
                    required
                  >
                    <option value="">Choose team</option>
                    {teams.map((team) => (
                      <option key={team.id} value={team.id}>
                        {team.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="away-team">Away team</label>
                  <select
                    id="away-team"
                    value={awayTeamId}
                    onChange={(event) => setAwayTeamId(event.target.value)}
                    required
                  >
                    <option value="">Choose team</option>
                    {teams.map((team) => (
                      <option key={team.id} value={team.id}>
                        {team.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="scheduled-at">Scheduled at</label>
                <input
                  id="scheduled-at"
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={(event) => setScheduledAt(event.target.value)}
                />
              </div>

              {createError ? (
                <Alert variant="error" title="Match creation failed">
                  {createError}
                </Alert>
              ) : null}

              {createSuccess ? (
                <Alert variant="success" title="Match created">
                  {createSuccess}
                </Alert>
              ) : null}

              <button type="submit" disabled={isCreating}>
                {isCreating ? "Creating..." : "Create match"}
              </button>
            </form>
          )}
        </section>

        <section>
          <h2>Notes</h2>
          <div className="grid" style={{ marginTop: "18px" }}>
            <div className="card">
              <h3>Ownership</h3>
              <p>Backend allows match creation only for the tournament owner.</p>
            </div>

            <div className="card">
              <h3>Teams</h3>
              <p>
                Home and away teams must be different and must belong to the
                tournament.
              </p>
            </div>

            <div className="card">
              <h3>Next step</h3>
              <p>Open the match details page to update score, winner and status.</p>
            </div>
          </div>
        </section>
      </div>

      <section>
        <h2>All matches</h2>
        <p style={{ marginBottom: "20px" }}>
          Current list of matches available on the platform.
        </p>

        {isLoading ? <p>Loading matches...</p> : null}

        {loadError ? (
          <Alert variant="error" title="Failed to load matches">
            {loadError}
          </Alert>
        ) : null}

        {!isLoading && !loadError && matches.length === 0 ? (
          <EmptyState
            title="No matches yet"
            description="No matches have been created yet."
          />
        ) : null}

        {!isLoading && !loadError && matches.length > 0 ? (
          <div className="grid">
            {matches.map((match) => {
              const tournament = tournamentMap.get(match.tournament_id);
              const homeTeam = teamMap.get(match.home_team_id);
              const awayTeam = teamMap.get(match.away_team_id);

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

                  <div
                    className="grid grid-2"
                    style={{ marginTop: "16px", gap: "12px" }}
                  >
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
      </section>
    </main>
  );
}
