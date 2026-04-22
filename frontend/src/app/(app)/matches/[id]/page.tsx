"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  deleteMatch,
  getMatch,
  updateMatch,
  updateMatchScore,
  type MatchRead,
} from "@/src/shared/api/matches";
import { getAccessToken } from "@/src/shared/lib/auth";
import Alert from "@/src/components/ui/alert";
import StatusBadge from "@/src/components/ui/status-badge";
import EmptyState from "@/src/components/ui/empty-state";
import { useCurrentUser } from "@/src/hooks/use-current-user";

function formatDate(value: string | null): string {
  if (!value) return "Not specified";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

const MATCH_STATUS_OPTIONS = [
  "SCHEDULED",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
];

export default function MatchDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const matchId = useMemo(() => Number(params?.id), [params]);
  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [match, setMatch] = useState<MatchRead | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const [homeScore, setHomeScore] = useState("0");
  const [awayScore, setAwayScore] = useState("0");
  const [winnerTeamId, setWinnerTeamId] = useState("");

  const [scoreError, setScoreError] = useState("");
  const [scoreSuccess, setScoreSuccess] = useState("");
  const [isUpdatingScore, setIsUpdatingScore] = useState(false);

  const [statusValue, setStatusValue] = useState("");
  const [scheduledAtValue, setScheduledAtValue] = useState("");

  const [updateError, setUpdateError] = useState("");
  const [updateSuccess, setUpdateSuccess] = useState("");
  const [isUpdatingMatch, setIsUpdatingMatch] = useState(false);

  const [deleteError, setDeleteError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    async function loadMatch() {
      if (!Number.isFinite(matchId)) {
        setError("Invalid match id");
        setIsLoading(false);
        return;
      }

      try {
        setError("");
        setIsLoading(true);

        const data = await getMatch(matchId);
        setMatch(data);
        setHomeScore(String(data.home_score ?? 0));
        setAwayScore(String(data.away_score ?? 0));
        setWinnerTeamId(data.winner_team_id ? String(data.winner_team_id) : "");
        setStatusValue(data.status);
        setScheduledAtValue(
          data.scheduled_at
            ? new Date(data.scheduled_at).toISOString().slice(0, 16)
            : "",
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load match");
      } finally {
        setIsLoading(false);
      }
    }

    void loadMatch();
  }, [matchId]);

  async function handleScoreSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setScoreError("You need to login before updating score");
      return;
    }

    setScoreError("");
    setScoreSuccess("");
    setIsUpdatingScore(true);

    try {
      const updated = await updateMatchScore(
        matchId,
        {
          home_score: Number(homeScore),
          away_score: Number(awayScore),
          winner_team_id: winnerTeamId ? Number(winnerTeamId) : null,
        },
        token,
      );

      setMatch(updated);
      setScoreSuccess("Score updated successfully");
    } catch (err) {
      setScoreError(
        err instanceof Error ? err.message : "Failed to update score",
      );
    } finally {
      setIsUpdatingScore(false);
    }
  }

  async function handleMatchUpdate(event: React.FormEvent<HTMLFormElement>) {
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
    } catch (err) {
      setUpdateError(
        err instanceof Error ? err.message : "Failed to update match",
      );
    } finally {
      setIsUpdatingMatch(false);
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

    if (!confirmed) {
      return;
    }

    setDeleteError("");
    setIsDeleting(true);

    try {
      await deleteMatch(matchId, token);
      router.push("/matches");
    } catch (err) {
      setDeleteError(
        err instanceof Error ? err.message : "Failed to delete match",
      );
      setIsDeleting(false);
    }
  }

  const isOwner = Boolean(
    currentUser && match && currentUser.id === match.tournament.owner_id,
  );

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Match details</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            {match ? `${match.home_team.name} vs ${match.away_team.name}` : "Match"}
          </h1>
          <p className="page-subtitle">
            Inspect metadata, update score and manage match lifecycle.
          </p>
        </div>

        <div className="row">
          <Link href="/matches" className="btn btn-secondary">
            Back to matches
          </Link>
          {match ? (
            <Link
              href={`/tournaments/${match.tournament_id}`}
              className="btn btn-secondary"
            >
              Open tournament
            </Link>
          ) : null}
        </div>
      </div>

      {isLoading ? (
        <section>
          <h2>Loading match...</h2>
          <p>Please wait while we fetch match details.</p>
        </section>
      ) : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Failed to load match">
          {error}
        </Alert>
      ) : null}

      {!isLoading && match ? (
        <>
          {!isLoadingCurrentUser && !isOwner ? (
            <Alert variant="info" title="Read-only mode">
              You are not the owner of the tournament for this match, so edit actions are hidden.
            </Alert>
          ) : null}

          <div className="grid grid-3" style={{ marginBottom: "24px" }}>
            <div className="card stat-card">
              <div className="stat-label">Status</div>
              <div className="stat-value">
                <StatusBadge value={match.status} />
              </div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Score</div>
              <div className="stat-value">
                {match.home_score ?? "-"} : {match.away_score ?? "-"}
              </div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Winner</div>
              <div className="stat-value">
                {match.winner_team?.name ?? "Not set"}
              </div>
            </div>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
              <h2>General info</h2>

              <div className="grid" style={{ marginTop: "18px" }}>
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
                  <p className="muted">Scheduled at</p>
                  <strong>{formatDate(match.scheduled_at)}</strong>
                </div>
              </div>
            </section>

            <section>
              <h2>Update score</h2>

              {isOwner ? (
                <form onSubmit={handleScoreSubmit}>
                  <div className="grid grid-2">
                    <div className="form-group">
                      <label htmlFor="home-score">Home score</label>
                      <input
                        id="home-score"
                        type="number"
                        min={0}
                        value={homeScore}
                        onChange={(event) => setHomeScore(event.target.value)}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="away-score">Away score</label>
                      <input
                        id="away-score"
                        type="number"
                        min={0}
                        value={awayScore}
                        onChange={(event) => setAwayScore(event.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="winner-team">Winner team</label>
                    <select
                      id="winner-team"
                      value={winnerTeamId}
                      onChange={(event) => setWinnerTeamId(event.target.value)}
                    >
                      <option value="">No winner</option>
                      <option value={match.home_team.id}>{match.home_team.name}</option>
                      <option value={match.away_team.id}>{match.away_team.name}</option>
                    </select>
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

                  <button type="submit" disabled={isUpdatingScore}>
                    {isUpdatingScore ? "Updating..." : "Update score"}
                  </button>
                </form>
              ) : (
                <EmptyState
                  title="Owner action only"
                  description="Only the tournament owner can update match score."
                />
              )}
            </section>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
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

                  <button type="submit" disabled={isUpdatingMatch}>
                    {isUpdatingMatch ? "Saving..." : "Save changes"}
                  </button>
                </form>
              ) : (
                <EmptyState
                  title="Owner action only"
                  description="Only the tournament owner can edit this match."
                />
              )}
            </section>

            <section>
              <h2>Danger zone</h2>
              <p style={{ marginBottom: "18px" }}>
                Deleting a match removes it permanently.
              </p>

              {isOwner ? (
                <>
                  {deleteError ? (
                    <Alert variant="error" title="Delete failed">
                      {deleteError}
                    </Alert>
                  ) : null}

                  <button
                    type="button"
                    onClick={handleDeleteMatch}
                    disabled={isDeleting}
                  >
                    {isDeleting ? "Deleting..." : "Delete match"}
                  </button>
                </>
              ) : (
                <EmptyState
                  title="Owner action only"
                  description="Only the tournament owner can delete this match."
                />
              )}
            </section>
          </div>
        </>
      ) : null}
    </main>
  );
}