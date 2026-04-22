"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { listMyTeams, type TeamRead } from "@/src/shared/api/teams";
import { createMatch, listTournamentMatches, type MatchRead } from "@/src/shared/api/matches";
import {
  getTournament,
  registerTeamForTournament,
  removeTeamFromTournament,
  updateTournament,
  type TournamentRead,
  type TournamentStatus,
} from "@/src/shared/api/tournaments";
import { getAccessToken } from "@/src/shared/lib/auth";
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
  const [tournamentMatches, setTournamentMatches] = useState<MatchRead[]>([]);
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

  const [matchesError, setMatchesError] = useState("");
  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [createMatchError, setCreateMatchError] = useState("");
  const [createMatchSuccess, setCreateMatchSuccess] = useState("");
  const [isCreatingMatch, setIsCreatingMatch] = useState(false);

  useEffect(() => {
    async function loadTournamentData() {
      if (!Number.isFinite(tournamentId)) {
        setError("Invalid tournament id");
        setIsLoading(false);
        return;
      }

      try {
        setError("");
        setMatchesError("");
        setIsLoading(true);

        const [tournamentData, matchesData] = await Promise.all([
          getTournament(tournamentId),
          listTournamentMatches(tournamentId),
        ]);

        setTournament(tournamentData);
        setTournamentMatches(matchesData);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load tournament",
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadTournamentData();
  }, [tournamentId]);

  useEffect(() => {
    async function loadMyTeams() {
      const token = getAccessToken();
      if (!token) return;

      try {
        const data = await listMyTeams(token);
        setMyTeams(data);
      } catch {
        // page can still work without this block
      }
    }

    loadMyTeams();
  }, []);

  async function refreshTournamentData() {
    if (!Number.isFinite(tournamentId)) return;

    const [tournamentData, matchesData] = await Promise.all([
      getTournament(tournamentId),
      listTournamentMatches(tournamentId),
    ]);

    setTournament(tournamentData);
    setTournamentMatches(matchesData);
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
      await refreshTournamentData();
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
      await refreshTournamentData();
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

  async function handleCreateMatch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();

    if (!token) {
      setCreateMatchError("You need to login before creating a match");
      return;
    }

    if (!homeTeamId || !awayTeamId) {
      setCreateMatchError("Select both teams");
      return;
    }

    if (homeTeamId === awayTeamId) {
      setCreateMatchError("Teams must be different");
      return;
    }

    setCreateMatchError("");
    setCreateMatchSuccess("");
    setIsCreatingMatch(true);

    try {
      const createdMatch = await createMatch(
        {
          tournament_id: tournamentId,
          home_team_id: Number(homeTeamId),
          away_team_id: Number(awayTeamId),
          scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        },
        token,
      );

      setCreateMatchSuccess(`Match #${createdMatch.id} created successfully`);
      setHomeTeamId("");
      setAwayTeamId("");
      setScheduledAt("");

      await refreshTournamentData();
    } catch (err) {
      setCreateMatchError(
        err instanceof Error ? err.message : "Failed to create match",
      );
    } finally {
      setIsCreatingMatch(false);
    }
  }

  const participantTeams = useMemo(() => {
    if (!tournament) return [];
    return tournament.participants.map((participant) => participant.team);
  }, [tournament]);

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Tournament details</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            {tournament?.name ?? "Tournament"}
          </h1>
          <p className="page-subtitle">
            Inspect tournament metadata, participants, registration flow and
            matches.
          </p>
        </div>

        <div className="row">
          <Link href="/tournaments" className="btn btn-secondary">
            Back to tournaments
          </Link>
          <Link href="/matches" className="btn btn-secondary">
            All matches
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
        <Alert variant="error" title="Failed to load tournament">
          {error}
        </Alert>
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
              <div className="stat-value">
                <StatusBadge value={tournament.status} />
              </div>
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

              {statusError ? (
                <Alert variant="error" title="Status update failed">
                  {statusError}
                </Alert>
              ) : null}
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
                <EmptyState
                  title="No teams available"
                  description="You have no teams available. Create one first on the Teams page."
                />
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
                    <Alert variant="error" title="Registration failed">
                      {registerError}
                    </Alert>
                  ) : null}

                  {registerSuccess ? (
                    <Alert variant="success" title="Team registered">
                      {registerSuccess}
                    </Alert>
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

              {removeError ? (
                <Alert variant="error" title="Remove failed">
                  {removeError}
                </Alert>
              ) : null}

              {tournament.participants.length === 0 ? (
                <EmptyState
                  title="No participants yet"
                  description="No participants are registered in this tournament yet."
                />
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

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
              <h2>Create match for this tournament</h2>
              <p style={{ marginBottom: "20px" }}>
                Create a match using the teams that are already registered in this
                tournament.
              </p>

              {participantTeams.length < 2 ? (
                <EmptyState
                  title="Not enough teams"
                  description="At least two registered teams are required before creating a match."
                />
              ) : (
                <form onSubmit={handleCreateMatch}>
                  <div className="grid grid-2">
                    <div className="form-group">
                      <label htmlFor="home-team-id">Home team</label>
                      <select
                        id="home-team-id"
                        value={homeTeamId}
                        onChange={(event) => setHomeTeamId(event.target.value)}
                      >
                        <option value="">Choose team</option>
                        {participantTeams.map((team) => (
                          <option key={team.id} value={team.id}>
                            {team.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label htmlFor="away-team-id">Away team</label>
                      <select
                        id="away-team-id"
                        value={awayTeamId}
                        onChange={(event) => setAwayTeamId(event.target.value)}
                      >
                        <option value="">Choose team</option>
                        {participantTeams.map((team) => (
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

                  {createMatchError ? (
                    <Alert variant="error" title="Match creation failed">
                      {createMatchError}
                    </Alert>
                  ) : null}

                  {createMatchSuccess ? (
                    <Alert variant="success" title="Match created">
                      {createMatchSuccess}
                    </Alert>
                  ) : null}

                  <button type="submit" disabled={isCreatingMatch}>
                    {isCreatingMatch ? "Creating..." : "Create match"}
                  </button>
                </form>
              )}
            </section>

            <section>
              <h2>Tournament matches</h2>
              <p style={{ marginBottom: "20px" }}>
                Matches linked to this tournament.
              </p>

              {matchesError ? (
                <Alert variant="error" title="Failed to load matches">
                  {matchesError}
                </Alert>
              ) : null}

              {tournamentMatches.length === 0 ? (
                <EmptyState
                  title="No matches yet"
                  description="No matches have been created for this tournament yet."
                />
              ) : (
                <div className="grid">
                  {tournamentMatches.map((match) => (
                    <div key={match.id} className="card">
                      <div className="row" style={{ justifyContent: "space-between" }}>
                        <div>
                          <h3>
                            {match.home_team.name} vs {match.away_team.name}
                          </h3>
                          <p>Scheduled: {formatDate(match.scheduled_at)}</p>
                        </div>

                        <StatusBadge value={match.status} />
                      </div>

                      <div
                        className="grid grid-2"
                        style={{ marginTop: "16px", gap: "12px" }}
                      >
                        <div>
                          <p className="muted">Score</p>
                          <strong>
                            {match.home_score ?? "-"} : {match.away_score ?? "-"}
                          </strong>
                        </div>

                        <div>
                          <p className="muted">Winner</p>
                          <strong>{match.winner_team?.name ?? "Not decided"}</strong>
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