"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent } from "react";

import {
  deleteMatch,
  getMatch,
  updateMatch,
  updateMatchScore,
  type MatchRead,
} from "@/src/shared/api/matches";
import { getAccessToken } from "@/src/shared/lib/auth";
import { useCurrentUser } from "@/src/hooks/use-current-user";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

const MATCH_STATUS_OPTIONS = [
  "SCHEDULED",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
] as const;

function formatDate(value: string | null): string {
  if (!value) return "Not specified";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function formatDateTimeLocal(value: string | null): string {
  if (!value) return "";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function getNumericValue(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export default function MatchDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const matchId = useMemo(() => Number(params?.id), [params]);

  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [match, setMatch] = useState<MatchRead | null>(null);
  const [loadError, setLoadError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const [homeScore, setHomeScore] = useState("0");
  const [awayScore, setAwayScore] = useState("0");

  const [statusValue, setStatusValue] = useState("");
  const [scheduledAtValue, setScheduledAtValue] = useState("");

  const [scoreError, setScoreError] = useState("");
  const [scoreSuccess, setScoreSuccess] = useState("");
  const [isUpdatingScore, setIsUpdatingScore] = useState(false);

  const [updateError, setUpdateError] = useState("");
  const [updateSuccess, setUpdateSuccess] = useState("");
  const [isUpdatingMatch, setIsUpdatingMatch] = useState(false);

  const [quickActionError, setQuickActionError] = useState("");
  const [quickActionSuccess, setQuickActionSuccess] = useState("");
  const [isRunningQuickAction, setIsRunningQuickAction] = useState(false);

  const [deleteError, setDeleteError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    async function loadMatch() {
      if (!Number.isFinite(matchId)) {
        setLoadError("Invalid match id");
        setIsLoading(false);
        return;
      }

      try {
        setLoadError("");
        setIsLoading(true);

        const data = await getMatch(matchId);
        setMatch(data);
        setHomeScore(String(data.home_score ?? 0));
        setAwayScore(String(data.away_score ?? 0));
        setStatusValue(data.status);
        setScheduledAtValue(formatDateTimeLocal(data.scheduled_at));
      } catch (error) {
        setLoadError(
          error instanceof Error ? error.message : "Failed to load match",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadMatch();
  }, [matchId]);

  const isOwner = Boolean(
    currentUser && match && currentUser.id === match.tournament.owner_id,
  );

  const numericHomeScore = useMemo(() => getNumericValue(homeScore), [homeScore]);
  const numericAwayScore = useMemo(() => getNumericValue(awayScore), [awayScore]);

  const derivedWinner = useMemo(() => {
    if (!match) return null;
    if (numericHomeScore > numericAwayScore) return match.home_team;
    if (numericAwayScore > numericHomeScore) return match.away_team;
    return null;
  }, [match, numericHomeScore, numericAwayScore]);

  const hasScoreDifference = numericHomeScore !== numericAwayScore;
  const canCompleteMatch = hasScoreDifference && numericHomeScore >= 0 && numericAwayScore >= 0;

  async function refreshMatch(): Promise<void> {
    const data = await getMatch(matchId);
    setMatch(data);
    setHomeScore(String(data.home_score ?? 0));
    setAwayScore(String(data.away_score ?? 0));
    setStatusValue(data.status);
    setScheduledAtValue(formatDateTimeLocal(data.scheduled_at));
  }

  async function handleScoreSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setScoreError("You need to login before updating score");
      return;
    }

    if (!match) {
      setScoreError("Match is not loaded yet");
      return;
    }

    if (numericHomeScore < 0 || numericAwayScore < 0) {
      setScoreError("Score values cannot be negative");
      return;
    }

    setScoreError("");
    setScoreSuccess("");
    setIsUpdatingScore(true);

    try {
      const updated = await updateMatchScore(
        matchId,
        {
          home_score: numericHomeScore,
          away_score: numericAwayScore,
          winner_team_id: derivedWinner ? derivedWinner.id : null,
        },
        token,
      );

      setMatch(updated);
      setScoreSuccess("Score updated successfully");
    } catch (error) {
      setScoreError(
        error instanceof Error ? error.message : "Failed to update score",
      );
    } finally {
      setIsUpdatingScore(false);
    }
  }

  async function handleMatchUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setUpdateError("You need to login before updating a match");
      return;
    }

    setUpdateError("");
    setUpdateSuccess("");
    setIsUpdatingMatch(true);

    try {
      const updated = await updateMatch(
        matchId,
        {
          status: statusValue || undefined,
          scheduled_at: scheduledAtValue
            ? new Date(scheduledAtValue).toISOString()
            : null,
        },
        token,
      );

      setMatch(updated);
      setUpdateSuccess("Match updated successfully");
    } catch (error) {
      setUpdateError(
        error instanceof Error ? error.message : "Failed to update match",
      );
    } finally {
      setIsUpdatingMatch(false);
    }
  }

  async function handleQuickStatusChange(nextStatus: string) {
    const token = getAccessToken();
    if (!token) {
      setQuickActionError("You need to login before changing match status");
      return;
    }

    setQuickActionError("");
    setQuickActionSuccess("");
    setIsRunningQuickAction(true);

    try {
      const updated = await updateMatch(
        matchId,
        {
          status: nextStatus,
          scheduled_at: scheduledAtValue
            ? new Date(scheduledAtValue).toISOString()
            : null,
        },
        token,
      );

      setMatch(updated);
      setStatusValue(updated.status);
      setQuickActionSuccess(`Match status changed to ${updated.status}`);
    } catch (error) {
      setQuickActionError(
        error instanceof Error ? error.message : "Failed to change match status",
      );
    } finally {
      setIsRunningQuickAction(false);
    }
  }

  async function handleCompleteMatch() {
    const token = getAccessToken();
    if (!token) {
      setQuickActionError("You need to login before completing a match");
      return;
    }

    if (!match) {
      setQuickActionError("Match is not loaded yet");
      return;
    }

    if (numericHomeScore < 0 || numericAwayScore < 0) {
      setQuickActionError("Score values cannot be negative");
      return;
    }

    if (!derivedWinner) {
      setQuickActionError("Completed match must have a winner. Set different scores.");
      return;
    }

    setQuickActionError("");
    setQuickActionSuccess("");
    setIsRunningQuickAction(true);

    try {
      await updateMatchScore(
        matchId,
        {
          home_score: numericHomeScore,
          away_score: numericAwayScore,
          winner_team_id: derivedWinner.id,
        },
        token,
      );

      const updated = await updateMatch(
        matchId,
        {
          status: "COMPLETED",
          scheduled_at: scheduledAtValue
            ? new Date(scheduledAtValue).toISOString()
            : null,
        },
        token,
      );

      setMatch(updated);
      setStatusValue(updated.status);
      setQuickActionSuccess("Match completed successfully");
      await refreshMatch();
    } catch (error) {
      setQuickActionError(
        error instanceof Error ? error.message : "Failed to complete match",
      );
    } finally {
      setIsRunningQuickAction(false);
    }
  }

  async function handleDeleteMatch() {
    const token = getAccessToken();
    if (!token) {
      setDeleteError("You need to login before deleting a match");
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to delete this match?",
    );

    if (!confirmed) return;

    setDeleteError("");
    setIsDeleting(true);

    try {
      await deleteMatch(matchId, token);
      router.push("/matches");
    } catch (error) {
      setDeleteError(
        error instanceof Error ? error.message : "Failed to delete match",
      );
      setIsDeleting(false);
    }
  }

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Match details</p>
        <h1>
          {match ? `${match.home_team.name} vs ${match.away_team.name}` : "Match"}
        </h1>
        <p>
          Inspect the match, control its lifecycle and confirm the final result
          from one place.
        </p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/matches" className="btn btn-secondary">
            Back to matches
          </Link>
          {match ? (
            <Link
              href={`/tournaments/${match.tournament.id}`}
              className="btn btn-secondary"
            >
              Open tournament
            </Link>
          ) : null}
        </div>
      </section>

      {isLoading ? (
        <section className="card">
          <h2>Loading match...</h2>
          <p>Please wait while we fetch match details.</p>
        </section>
      ) : null}

      {!isLoading && loadError ? (
        <Alert variant="error" title="Failed to load match">
          {loadError}
        </Alert>
      ) : null}

      {!isLoading && match ? (
        <>
          {!isLoadingCurrentUser && !isOwner ? (
            <Alert variant="info" title="Read-only mode">
              You are not the owner of the tournament for this match, so edit
              actions are hidden.
            </Alert>
          ) : null}

          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">Status</p>
              <StatusBadge value={match.status} />
            </div>

            <div className="card">
              <p className="muted">Score</p>
              <strong>
                {match.home_score ?? "-"} : {match.away_score ?? "-"}
              </strong>
            </div>

            <div className="card">
              <p className="muted">Winner</p>
              <strong>{match.winner_team?.name ?? "Not decided"}</strong>
            </div>

            <div className="card">
              <p className="muted">Scheduled at</p>
              <strong>{formatDate(match.scheduled_at)}</strong>
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>General info</h2>

              <div className="grid" style={{ gap: "14px", marginTop: "16px" }}>
                <div>
                  <p className="muted">Tournament</p>
                  <strong>{match.tournament.name}</strong>
                </div>

                <div>
                  <p className="muted">Home team</p>
                  <strong>{match.home_team.name}</strong>
                </div>

                <div>
                  <p className="muted">Away team</p>
                  <strong>{match.away_team.name}</strong>
                </div>

                <div>
                  <p className="muted">Derived winner from form</p>
                  <strong>{derivedWinner?.name ?? "No winner yet"}</strong>
                </div>
              </div>
            </div>

            <div className="card">
              <h2>Quick actions</h2>
              <p style={{ marginBottom: "16px" }}>
                Use fast actions to move the match through its lifecycle.
              </p>

              {!isOwner ? (
                <EmptyState
                  title="Owner access required"
                  description="Only the tournament owner can manage this match."
                />
              ) : (
                <>
                  {quickActionError ? (
                    <Alert variant="error" title="Quick action failed">
                      {quickActionError}
                    </Alert>
                  ) : null}

                  {quickActionSuccess ? (
                    <Alert variant="success" title="Quick action completed">
                      {quickActionSuccess}
                    </Alert>
                  ) : null}

                  <div className="row" style={{ flexWrap: "wrap", gap: "10px" }}>
                    <button
                      type="button"
                      onClick={() => void handleQuickStatusChange("IN_PROGRESS")}
                      disabled={isRunningQuickAction}
                    >
                      Start match
                    </button>

                    <button
                      type="button"
                      onClick={() => void handleCompleteMatch()}
                      disabled={isRunningQuickAction || !canCompleteMatch}
                    >
                      Complete match
                    </button>

                    <button
                      type="button"
                      onClick={() => void handleQuickStatusChange("CANCELLED")}
                      disabled={isRunningQuickAction}
                    >
                      Cancel match
                    </button>
                  </div>

                  <p className="muted" style={{ marginTop: "14px" }}>
                    To complete a match, set different scores so the winner can
                    be determined automatically.
                  </p>
                </>
              )}
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Update score</h2>

              {isOwner ? (
                <form onSubmit={handleScoreSubmit}>
                  <div className="grid grid-2">
                    <div className="form-group">
                      <label htmlFor="home-score">{match.home_team.name}</label>
                      <input
                        id="home-score"
                        type="number"
                        min="0"
                        step="1"
                        value={homeScore}
                        onChange={(event) => setHomeScore(event.target.value)}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="away-score">{match.away_team.name}</label>
                      <input
                        id="away-score"
                        type="number"
                        min="0"
                        step="1"
                        value={awayScore}
                        onChange={(event) => setAwayScore(event.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <div className="card" style={{ padding: "16px", marginTop: "12px" }}>
                    <p className="muted">Result preview</p>
                    <strong>
                      {numericHomeScore} : {numericAwayScore}
                    </strong>
                    <p style={{ marginTop: "8px" }}>
                      Winner: {derivedWinner?.name ?? "No winner yet"}
                    </p>
                  </div>

                  {scoreError ? (
                    <Alert variant="error" title="Score update failed">
                      {scoreError}
                    </Alert>
                  ) : null}

                  {scoreSuccess ? (
                    <Alert variant="success" title="Score updated">
                      {scoreSuccess}
                    </Alert>
                  ) : null}

                  <div className="row" style={{ marginTop: "16px" }}>
                    <button type="submit" disabled={isUpdatingScore}>
                      {isUpdatingScore ? "Updating..." : "Save score"}
                    </button>
                  </div>
                </form>
              ) : (
                <EmptyState
                  title="Owner access required"
                  description="Only the tournament owner can update the score."
                />
              )}
            </div>

            <div className="card">
              <h2>Update match</h2>

              {isOwner ? (
                <form onSubmit={handleMatchUpdate}>
                  <div className="form-group">
                    <label htmlFor="match-status">Status</label>
                    <select
                      id="match-status"
                      value={statusValue}
                      onChange={(event) => setStatusValue(event.target.value)}
                    >
                      {MATCH_STATUS_OPTIONS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="match-scheduled-at">Scheduled at</label>
                    <input
                      id="match-scheduled-at"
                      type="datetime-local"
                      value={scheduledAtValue}
                      onChange={(event) => setScheduledAtValue(event.target.value)}
                    />
                  </div>

                  {updateError ? (
                    <Alert variant="error" title="Match update failed">
                      {updateError}
                    </Alert>
                  ) : null}

                  {updateSuccess ? (
                    <Alert variant="success" title="Match updated">
                      {updateSuccess}
                    </Alert>
                  ) : null}

                  <div className="row" style={{ marginTop: "16px" }}>
                    <button type="submit" disabled={isUpdatingMatch}>
                      {isUpdatingMatch ? "Saving..." : "Save changes"}
                    </button>
                  </div>
                </form>
              ) : (
                <EmptyState
                  title="Owner access required"
                  description="Only the tournament owner can update status and schedule."
                />
              )}
            </div>
          </section>

          <section className="card">
            <h2>Danger zone</h2>
            <p>Deleting a match removes it permanently.</p>

            {isOwner ? (
              <>
                {deleteError ? (
                  <Alert variant="error" title="Delete failed">
                    {deleteError}
                  </Alert>
                ) : null}

                <div className="row" style={{ marginTop: "16px" }}>
                  <button type="button" onClick={handleDeleteMatch} disabled={isDeleting}>
                    {isDeleting ? "Deleting..." : "Delete match"}
                  </button>
                </div>
              </>
            ) : (
              <EmptyState
                title="Owner access required"
                description="Only the tournament owner can delete this match."
              />
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}