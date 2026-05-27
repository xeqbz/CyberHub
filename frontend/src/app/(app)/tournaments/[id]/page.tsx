"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent } from "react";

import { useCurrentUser } from "@/src/hooks/use-current-user";
import {
  createMatch,
  listTournamentMatches,
  type MatchRead,
} from "@/src/shared/api/matches";
import {
  listMyTeams,
  type TeamRead,
} from "@/src/shared/api/teams";
import {
  generateTournamentBracket,
  getTournament,
  registerTeamForTournament,
  removeTeamFromTournament,
  reviewTournamentParticipant,
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

const STAGE_ORDER = [
  "Upper bracket",
  "Lower bracket",
  "Grand final",
  "Main bracket",
  "Swiss",
  "Round robin",
];

type BracketRoundGroup = {
  roundNumber: number;
  matches: MatchRead[];
};

type BracketStageGroup = {
  stage: string;
  rounds: BracketRoundGroup[];
  matchesCount: number;
  completedCount: number;
};

function getStageRank(stage: string): number {
  const index = STAGE_ORDER.indexOf(stage);
  return index === -1 ? STAGE_ORDER.length : index;
}

function formatRoundTitle(stage: string, roundNumber: number): string {
  if (stage === "Grand final") return "Final match";
  if (stage === "Swiss") return `Swiss round ${roundNumber}`;
  return `Round ${roundNumber}`;
}

function formatScore(value: number | null): string {
  return value === null ? "-" : String(value);
}

export default function TournamentDetailsPage() {
  const params = useParams();
  const tournamentId = useMemo(() => Number(params?.id), [params]);

  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [tournament, setTournament] = useState<TournamentRead | null>(null);
  const [tournamentMatches, setTournamentMatches] = useState<MatchRead[]>([]);
  const [myTeams, setMyTeams] = useState<TeamRead[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [registerError, setRegisterError] = useState("");
  const [registerSuccess, setRegisterSuccess] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);

  const [removeError, setRemoveError] = useState("");
  const [isRemovingTeamId, setIsRemovingTeamId] = useState<number | null>(null);
  const [reviewError, setReviewError] = useState("");
  const [busyReviewTeamId, setBusyReviewTeamId] = useState<number | null>(null);

  const [statusError, setStatusError] = useState("");
  const [statusSuccess, setStatusSuccess] = useState("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [createMatchError, setCreateMatchError] = useState("");
  const [createMatchSuccess, setCreateMatchSuccess] = useState("");
  const [isCreatingMatch, setIsCreatingMatch] = useState(false);
  const [bracketError, setBracketError] = useState("");
  const [bracketSuccess, setBracketSuccess] = useState("");
  const [isGeneratingBracket, setIsGeneratingBracket] = useState(false);

  useEffect(() => {
    async function loadTournamentData() {
      if (!Number.isFinite(tournamentId)) {
        setPageError("Invalid tournament id");
        setIsLoading(false);
        return;
      }

      try {
        setPageError("");
        setIsLoading(true);

        const [tournamentData, matchesData] = await Promise.all([
          getTournament(tournamentId),
          listTournamentMatches(tournamentId),
        ]);

        setTournament(tournamentData);
        setTournamentMatches(matchesData);
      } catch (error) {
        setPageError(
          error instanceof Error ? error.message : "Failed to load tournament",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadTournamentData();
  }, [tournamentId]);

  useEffect(() => {
    async function loadMyTeams() {
      const token = getAccessToken();
      if (!token) return;

      try {
        const data = await listMyTeams(token);
        setMyTeams(data);
      } catch {
        // page stays usable even if this block fails
      }
    }

    void loadMyTeams();
  }, []);

  async function refreshTournamentData(): Promise<void> {
    if (!Number.isFinite(tournamentId)) return;

    const [tournamentData, matchesData] = await Promise.all([
      getTournament(tournamentId),
      listTournamentMatches(tournamentId),
    ]);

    setTournament(tournamentData);
    setTournamentMatches(matchesData);
  }

  async function handleRegisterTeam(event: FormEvent<HTMLFormElement>) {
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
    } catch (error) {
      setRegisterError(
        error instanceof Error ? error.message : "Failed to register team",
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
    } catch (error) {
      setRemoveError(
        error instanceof Error ? error.message : "Failed to remove team",
      );
    } finally {
      setIsRemovingTeamId(null);
    }
  }

  async function handleReviewParticipant(
    teamId: number,
    nextStatus: "APPROVED" | "REJECTED",
  ) {
    const token = getAccessToken();
    if (!token) {
      setReviewError("You need to login before reviewing applications");
      return;
    }

    setReviewError("");
    setBusyReviewTeamId(teamId);

    try {
      await reviewTournamentParticipant(tournamentId, teamId, nextStatus, token);
      await refreshTournamentData();
    } catch (error) {
      setReviewError(
        error instanceof Error ? error.message : "Failed to review application",
      );
    } finally {
      setBusyReviewTeamId(null);
    }
  }

  async function handleStatusChange(nextStatus: TournamentStatus) {
    const token = getAccessToken();
    if (!token) {
      setStatusError("You need to login before updating tournament status");
      return;
    }

    setStatusError("");
    setStatusSuccess("");
    setIsUpdatingStatus(true);

    try {
      const updated = await updateTournament(
        tournamentId,
        { status: nextStatus },
        token,
      );

      setTournament(updated);
      setStatusSuccess(`Tournament status updated to ${updated.status}`);
    } catch (error) {
      setStatusError(
        error instanceof Error ? error.message : "Failed to update status",
      );
    } finally {
      setIsUpdatingStatus(false);
    }
  }

  async function handleCreateMatch(event: FormEvent<HTMLFormElement>) {
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
          scheduled_at: scheduledAt
            ? new Date(scheduledAt).toISOString()
            : null,
        },
        token,
      );

      setCreateMatchSuccess(`Match #${createdMatch.id} created successfully`);
      setHomeTeamId("");
      setAwayTeamId("");
      setScheduledAt("");

      await refreshTournamentData();
    } catch (error) {
      setCreateMatchError(
        error instanceof Error ? error.message : "Failed to create match",
      );
    } finally {
      setIsCreatingMatch(false);
    }
  }

  async function handleGenerateBracket() {
    const token = getAccessToken();
    if (!token) {
      setBracketError("You need to login before generating the bracket");
      return;
    }

    setBracketError("");
    setBracketSuccess("");
    setIsGeneratingBracket(true);

    try {
      const matches = await generateTournamentBracket(tournamentId, token);
      setTournamentMatches(matches);
      setBracketSuccess(`Bracket generated: ${matches.length} matches created.`);
      await refreshTournamentData();
    } catch (error) {
      setBracketError(
        error instanceof Error ? error.message : "Failed to generate bracket",
      );
    } finally {
      setIsGeneratingBracket(false);
    }
  }

  const participantTeams = useMemo(() => {
    if (!tournament) return [];
    return tournament.participants
      .filter((participant) => participant.status === "APPROVED")
      .map((participant) => participant.team);
  }, [tournament]);

  const allParticipantTeamIds = useMemo(() => {
    if (!tournament) return new Set<number>();
    return new Set(tournament.participants.map((participant) => participant.team_id));
  }, [tournament]);

  const availableMyTeams = useMemo(() => {
    return myTeams.filter((team) => !allParticipantTeamIds.has(team.id));
  }, [myTeams, allParticipantTeamIds]);

  const bracketStages = useMemo<BracketStageGroup[]>(() => {
    const stageGroups = new Map<string, Map<number, MatchRead[]>>();

    tournamentMatches.forEach((match) => {
      const roundGroups = stageGroups.get(match.stage) ?? new Map();
      const roundMatches = roundGroups.get(match.round_number) ?? [];

      roundMatches.push(match);
      roundGroups.set(match.round_number, roundMatches);
      stageGroups.set(match.stage, roundGroups);
    });

    return Array.from(stageGroups.entries())
      .map(([stage, roundGroups]) => {
        const rounds = Array.from(roundGroups.entries())
          .map(([roundNumber, matches]) => ({
            roundNumber,
            matches: [...matches].sort(
              (a, b) => a.bracket_position - b.bracket_position,
            ),
          }))
          .sort((a, b) => a.roundNumber - b.roundNumber);
        const matches = rounds.flatMap((round) => round.matches);

        return {
          stage,
          rounds,
          matchesCount: matches.length,
          completedCount: matches.filter(
            (match) => match.status === "COMPLETED",
          ).length,
        };
      })
      .sort((a, b) => {
        const stageRankDiff = getStageRank(a.stage) - getStageRank(b.stage);
        if (stageRankDiff !== 0) return stageRankDiff;
        return a.stage.localeCompare(b.stage);
      });
  }, [tournamentMatches]);

  const completedMatchesCount = useMemo(() => {
    return tournamentMatches.filter((match) => match.status === "COMPLETED").length;
  }, [tournamentMatches]);

  const scheduledMatchesCount = useMemo(() => {
    return tournamentMatches.filter((match) => match.status !== "COMPLETED").length;
  }, [tournamentMatches]);

  const isOwner = Boolean(
    currentUser && tournament && currentUser.id === tournament.owner_id,
  );

  const isRegistrationOpen = tournament?.status === "REGISTRATION_OPEN";
  const isTournamentLocked =
    tournament?.status === "COMPLETED" || tournament?.status === "CANCELLED";

  const canCreateMatch =
    isOwner &&
    !isTournamentLocked &&
    participantTeams.length >= 2;
  const canGenerateBracket =
    isOwner &&
    tournamentMatches.length === 0 &&
    participantTeams.length >= 2 &&
    (tournament?.status === "REGISTRATION_CLOSED" ||
      tournament?.status === "IN_PROGRESS");

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Tournament details</p>
        <h1>{tournament?.name ?? "Tournament"}</h1>
        <p>
          Manage participants, schedule matches and keep the tournament state in
          one place.
        </p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
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
      </section>

      {isLoading ? (
        <section className="card">
          <h2>Loading tournament...</h2>
          <p>Please wait while we fetch tournament details.</p>
        </section>
      ) : null}

      {!isLoading && pageError ? (
        <Alert variant="error" title="Failed to load tournament">
          {pageError}
        </Alert>
      ) : null}

      {!isLoading && tournament ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">Tournament ID</p>
              <strong>{tournament.id}</strong>
            </div>

            <div className="card">
              <p className="muted">Status</p>
              <StatusBadge value={tournament.status} />
            </div>

            <div className="card">
              <p className="muted">Participants</p>
              <strong>
                {tournament.participants.length}/{tournament.max_teams}
              </strong>
            </div>

            <div className="card">
              <p className="muted">Starts at</p>
              <strong>{formatDate(tournament.starts_at)}</strong>
            </div>

            <div className="card">
              <p className="muted">Owner</p>
              <strong>{tournament.owner.username}</strong>
            </div>

            <div className="card">
              <p className="muted">Matches</p>
              <strong>{tournamentMatches.length}</strong>
            </div>
          </section>

          {!isLoadingCurrentUser && !isOwner ? (
            <Alert variant="info" title="Read-only mode">
              You are not the owner of this tournament, so management actions are
              limited. You can still inspect participants and matches.
            </Alert>
          ) : null}

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>General info</h2>

              <div className="grid" style={{ gap: "14px", marginTop: "16px" }}>
                <div>
                  <p className="muted">Name</p>
                  <strong>{tournament.name}</strong>
                </div>

                <div>
                  <p className="muted">Description</p>
                  <p>{tournament.description || "No description provided."}</p>
                </div>

                <div>
                  <p className="muted">Discipline</p>
                  <strong>{tournament.discipline}</strong>
                </div>

                <div>
                  <p className="muted">Format</p>
                  <strong>{tournament.format}</strong>
                </div>

                <div>
                  <p className="muted">Rules</p>
                  <p>{tournament.rules}</p>
                </div>

                <div>
                  <p className="muted">Starts at</p>
                  <p>{formatDate(tournament.starts_at)}</p>
                </div>

                <div>
                  <p className="muted">Registration state</p>
                  <p>
                    {isRegistrationOpen
                      ? "Teams can join right now."
                      : "Registration is currently closed."}
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <h2>Match overview</h2>

              <div
                className="grid grid-2"
                style={{ marginTop: "16px", gap: "12px" }}
              >
                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Total matches</p>
                  <strong>{tournamentMatches.length}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Completed</p>
                  <strong>{completedMatchesCount}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Pending</p>
                  <strong>{scheduledMatchesCount}</strong>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <p className="muted">Available slots</p>
                  <strong>
                    {Math.max(tournament.max_teams - participantTeams.length, 0)}
                  </strong>
                </div>
              </div>
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Register team</h2>
              <p style={{ marginBottom: "16px" }}>
                Use this block to register one of your teams when tournament
                registration is open.
              </p>

              {!getAccessToken() ? (
                <EmptyState
                  title="Login required"
                  description="You need to login before registering a team."
                  action={
                    <div className="row">
                      <Link href="/login" className="btn btn-secondary">
                        Login
                      </Link>
                    </div>
                  }
                />
              ) : !isRegistrationOpen ? (
                <EmptyState
                  title="Registration is closed"
                  description="Change tournament status to REGISTRATION_OPEN to allow team registration."
                />
              ) : availableMyTeams.length === 0 ? (
                <EmptyState
                  title="No eligible teams"
                  description={
                    myTeams.length === 0
                      ? "You do not have any teams yet."
                      : "All of your teams are already registered in this tournament."
                  }
                  action={
                    myTeams.length === 0 ? (
                      <Link href="/teams" className="btn btn-secondary">
                        Go to teams
                      </Link>
                    ) : undefined
                  }
                />
              ) : (
                <form onSubmit={handleRegisterTeam}>
                  <div className="form-group">
                    <label htmlFor="register-team-select">Select team</label>
                    <select
                      id="register-team-select"
                      value={selectedTeamId}
                      onChange={(event) => setSelectedTeamId(event.target.value)}
                    >
                      <option value="">Choose team</option>
                      {availableMyTeams.map((team) => (
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

                  <div className="row" style={{ marginTop: "16px" }}>
                    <button type="submit" disabled={isRegistering}>
                      {isRegistering ? "Registering..." : "Register team"}
                    </button>
                  </div>
                </form>
              )}
            </div>

            <div className="card">
              <h2>Status management</h2>
              <p style={{ marginBottom: "16px" }}>
                Tournament owner can switch the state directly from this page.
              </p>

              {!isOwner ? (
                <EmptyState
                  title="Owner access required"
                  description="Only the tournament owner can change its status."
                />
              ) : (
                <>
                  <div className="form-group">
                    <label htmlFor="tournament-status-select">Status</label>
                    <select
                      id="tournament-status-select"
                      value={tournament.status}
                      onChange={(event) =>
                        void handleStatusChange(
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

                  {statusSuccess ? (
                    <Alert variant="success" title="Status updated">
                      {statusSuccess}
                    </Alert>
                  ) : null}

                  <p className="muted" style={{ marginTop: "14px" }}>
                    Recommended flow: DRAFT → REGISTRATION_OPEN →
                    REGISTRATION_CLOSED → IN_PROGRESS → COMPLETED.
                  </p>
                </>
              )}
            </div>
          </section>

          <section className="card" style={{ marginBottom: "24px" }}>
            <div
              className="row"
              style={{ justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <h2>Participants</h2>
                <p className="muted">
                  Current applications and approved teams in this tournament.
                </p>
              </div>
              <strong>
                {participantTeams.length}/{tournament.max_teams} approved
              </strong>
            </div>

            {removeError ? (
              <Alert variant="error" title="Participant removal failed">
                {removeError}
              </Alert>
            ) : null}

            {reviewError ? (
              <Alert variant="error" title="Application review failed">
                {reviewError}
              </Alert>
            ) : null}

            {tournament.participants.length === 0 ? (
              <EmptyState
                title="No participants yet"
                description="Teams will appear here after registration."
              />
            ) : (
              <div className="grid" style={{ marginTop: "18px" }}>
                {tournament.participants.map((participant) => (
                  <div key={participant.id} className="card">
                    <div
                      className="row"
                      style={{
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: "12px",
                      }}
                    >
                      <div>
                        <h3>{participant.team.name}</h3>
                        <p>
                          {participant.team.description || "No team description provided."}
                        </p>
                        <p className="muted">Team ID: {participant.team_id}</p>
                      </div>

                      <StatusBadge value={participant.status} />
                    </div>

                    <div className="row" style={{ marginTop: "12px" }}>
                      {isOwner && participant.status === "PENDING" ? (
                        <>
                          <button
                            type="button"
                            onClick={() =>
                              void handleReviewParticipant(
                                participant.team_id,
                                "APPROVED",
                              )
                            }
                            disabled={busyReviewTeamId === participant.team_id}
                          >
                            {busyReviewTeamId === participant.team_id
                              ? "Saving..."
                              : "Approve"}
                          </button>

                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() =>
                              void handleReviewParticipant(
                                participant.team_id,
                                "REJECTED",
                              )
                            }
                            disabled={busyReviewTeamId === participant.team_id}
                          >
                            Reject
                          </button>
                        </>
                      ) : null}

                      <Link
                        href={`/teams/${participant.team.id}`}
                        className="btn btn-secondary"
                      >
                        Open team
                      </Link>

                      {isOwner ? (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={() => void handleRemoveTeam(participant.team_id)}
                          disabled={isRemovingTeamId === participant.team_id}
                        >
                          {isRemovingTeamId === participant.team_id
                            ? "Removing..."
                            : "Remove"}
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Create match</h2>
              <p style={{ marginBottom: "16px" }}>
                Create a match using teams already registered in this tournament.
              </p>

              {!isOwner ? (
                <EmptyState
                  title="Owner access required"
                  description="Only the tournament owner can create tournament matches."
                />
              ) : participantTeams.length < 2 ? (
                <EmptyState
                  title="Not enough participants"
                  description="Register at least two teams before creating a match."
                />
              ) : isTournamentLocked ? (
                <EmptyState
                  title="Tournament is locked"
                  description="You cannot create new matches after tournament completion or cancellation."
                />
              ) : (
                <form onSubmit={handleCreateMatch}>
                  <div className="grid grid-2">
                    <div className="form-group">
                      <label htmlFor="match-home-team">Home team</label>
                      <select
                        id="match-home-team"
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
                      <label htmlFor="match-away-team">Away team</label>
                      <select
                        id="match-away-team"
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
                    <label htmlFor="match-scheduled-at">Scheduled at</label>
                    <input
                      id="match-scheduled-at"
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

                  <div className="row" style={{ marginTop: "16px" }}>
                    <button type="submit" disabled={!canCreateMatch || isCreatingMatch}>
                      {isCreatingMatch ? "Creating..." : "Create match"}
                    </button>
                  </div>
                </form>
              )}
            </div>

            <div className="card">
              <h2>Bracket generation</h2>

              <div className="grid" style={{ gap: "12px", marginTop: "16px" }}>
                <div className="card" style={{ padding: "16px" }}>
                  <strong>1. Close registration</strong>
                  <p className="muted" style={{ marginTop: "8px" }}>
                    Generate the initial bracket after applications are reviewed
                    and registration is closed.
                  </p>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <strong>2. Create first matches</strong>
                  <p className="muted" style={{ marginTop: "8px" }}>
                    Single and double elimination create opening bracket matches.
                    Round robin creates all pairings, while Swiss starts from the
                    first round.
                  </p>
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <strong>3. Run the tournament</strong>
                  <p className="muted" style={{ marginTop: "8px" }}>
                    Use IN_PROGRESS when matches begin. Completed playoff matches
                    advance teams automatically, and Swiss creates the next round
                    after current results.
                  </p>
                </div>
              </div>

              {bracketError ? (
                <Alert variant="error" title="Bracket generation failed">
                  {bracketError}
                </Alert>
              ) : null}

              {bracketSuccess ? (
                <Alert variant="success" title="Bracket generated">
                  {bracketSuccess}
                </Alert>
              ) : null}

              <div className="row" style={{ marginTop: "16px" }}>
                <button
                  type="button"
                  onClick={() => void handleGenerateBracket()}
                  disabled={!canGenerateBracket || isGeneratingBracket}
                >
                  {isGeneratingBracket ? "Generating..." : "Generate bracket"}
                </button>
              </div>

              {!canGenerateBracket ? (
                <p className="muted" style={{ marginTop: "12px" }}>
                  Bracket generation is available to the owner after registration
                  is closed and before matches exist.
                </p>
              ) : null}
            </div>
          </section>

          <section className="card">
            <div
              className="row"
              style={{ justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <h2>Tournament matches</h2>
                <p className="muted">
                  Matches linked to this tournament, grouped by bracket stage and
                  round.
                </p>
              </div>

              <Link href="/matches" className="btn btn-secondary">
                Open all matches
              </Link>
            </div>

            {tournamentMatches.length === 0 ? (
              <EmptyState
                title="No matches yet"
                description="Generate a bracket or create the first match to start tournament play."
              />
            ) : (
              <div className="bracket-stage-list">
                {bracketStages.map((stage) => (
                  <div key={stage.stage} className="bracket-stage">
                    <div className="bracket-stage__header">
                      <div>
                        <h3>{stage.stage}</h3>
                        <p className="muted">
                          {stage.completedCount} of {stage.matchesCount} matches
                          completed
                        </p>
                      </div>

                      <span className="badge">
                        {stage.rounds.length}{" "}
                        {stage.rounds.length === 1 ? "round" : "rounds"}
                      </span>
                    </div>

                    <div className="bracket-round-grid">
                      {stage.rounds.map((round) => (
                        <div
                          key={`${stage.stage}-${round.roundNumber}`}
                          className="bracket-round"
                        >
                          <div className="bracket-round__header">
                            <strong>
                              {formatRoundTitle(stage.stage, round.roundNumber)}
                            </strong>
                            <span className="muted">
                              {round.matches.length}{" "}
                              {round.matches.length === 1 ? "match" : "matches"}
                            </span>
                          </div>

                          <div className="bracket-round__matches">
                            {round.matches.map((match) => {
                              const homeWon =
                                match.winner_team_id === match.home_team_id;
                              const awayWon =
                                match.winner_team_id === match.away_team_id;

                              return (
                                <div key={match.id} className="bracket-match">
                                  <div className="bracket-match__header">
                                    <div>
                                      <strong>Match #{match.id}</strong>
                                      <p className="muted">
                                        Position {match.bracket_position}
                                      </p>
                                    </div>

                                    <StatusBadge value={match.status} />
                                  </div>

                                  <div className="bracket-match__teams">
                                    <div
                                      className={`bracket-team-row${
                                        homeWon ? " is-winner" : ""
                                      }`}
                                    >
                                      <span>{match.home_team.name}</span>
                                      <strong>{formatScore(match.home_score)}</strong>
                                    </div>

                                    <div
                                      className={`bracket-team-row${
                                        awayWon ? " is-winner" : ""
                                      }`}
                                    >
                                      <span>{match.away_team.name}</span>
                                      <strong>{formatScore(match.away_score)}</strong>
                                    </div>
                                  </div>

                                  <div className="bracket-match__meta">
                                    <p>
                                      Winner:{" "}
                                      <strong>
                                        {match.winner_team?.name ?? "Not decided"}
                                      </strong>
                                    </p>
                                    <p>Scheduled: {formatDate(match.scheduled_at)}</p>
                                  </div>

                                  <Link
                                    href={`/matches/${match.id}`}
                                    className="btn btn-secondary bracket-match__link"
                                  >
                                    Open match
                                  </Link>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
