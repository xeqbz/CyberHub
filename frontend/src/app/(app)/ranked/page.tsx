"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";
import {
  cancelRankedMatchmaking,
  findRankedOpponent,
  listRankedMatches,
  submitRankedMatchResult,
  type RankedMatch,
} from "@/src/shared/api/platform";
import { getAccessToken } from "@/src/shared/lib/auth";

function formatDate(value: string | null): string {
  if (!value) return "Not completed";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function RankedPage() {
  const [matches, setMatches] = useState<RankedMatch[]>([]);
  const [scores, setScores] = useState<Record<number, { one: string; two: string }>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);

  const loadMatches = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setError("You need to login to use ranked matches.");
      setIsLoading(false);
      return;
    }

    try {
      setError("");
      setIsLoading(true);
      setMatches(await listRankedMatches(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load ranked matches");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMatches();
  }, [loadMatches]);

  async function handleFindOpponent() {
    const token = getAccessToken();
    if (!token) {
      setError("You need to login before searching for an opponent.");
      return;
    }

    try {
      setError("");
      setMessage("");
      setIsSearching(true);
      const response = await findRankedOpponent(token);
      setMessage(response.message);
      await loadMatches();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start matchmaking");
    } finally {
      setIsSearching(false);
    }
  }

  async function handleCancelSearch() {
    const token = getAccessToken();
    if (!token) return;
    await cancelRankedMatchmaking(token);
    setMessage("Matchmaking cancelled.");
  }

  async function handleSubmitResult(match: RankedMatch) {
    const token = getAccessToken();
    if (!token) {
      setError("You need to login before submitting a result.");
      return;
    }

    const score = scores[match.id] ?? { one: "0", two: "0" };
    const playerOneScore = Number(score.one);
    const playerTwoScore = Number(score.two);

    if (!Number.isFinite(playerOneScore) || !Number.isFinite(playerTwoScore)) {
      setError("Scores must be numeric.");
      return;
    }

    try {
      setError("");
      await submitRankedMatchResult(
        match.id,
        {
          player_one_score: playerOneScore,
          player_two_score: playerTwoScore,
        },
        token,
      );
      setMessage(`Result for ranked match #${match.id} saved.`);
      await loadMatches();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit result");
    }
  }

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Ranked</p>
        <h1>Ranked matchmaking</h1>
        <p>Find an opponent, submit the result and update ELO automatically.</p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <button type="button" onClick={handleFindOpponent} disabled={isSearching}>
            {isSearching ? "Searching..." : "Find opponent"}
          </button>
          <button type="button" className="btn btn-secondary" onClick={handleCancelSearch}>
            Cancel search
          </button>
          <Link href="/rankings" className="btn btn-secondary">
            Rankings
          </Link>
        </div>
      </section>

      {message ? (
        <Alert variant="success" title="Ranked update">
          {message}
        </Alert>
      ) : null}

      {error ? (
        <Alert variant="error" title="Ranked action failed">
          {error}
        </Alert>
      ) : null}

      {isLoading ? (
        <section className="card">
          <h2>Loading ranked matches...</h2>
        </section>
      ) : null}

      {!isLoading && !error && matches.length === 0 ? (
        <EmptyState
          title="No ranked matches"
          description="Start matchmaking to create your first ranked match."
        />
      ) : null}

      {!isLoading && matches.length > 0 ? (
        <section className="card">
          <h2>My ranked matches</h2>
          <div className="grid" style={{ marginTop: "18px" }}>
            {matches.map((match) => {
              const score = scores[match.id] ?? { one: "0", two: "0" };

              return (
                <div key={match.id} className="card">
                  <div
                    className="row"
                    style={{ justifyContent: "space-between", alignItems: "center" }}
                  >
                    <div>
                      <p className="muted">Match #{match.id}</p>
                      <h3>
                        {match.player_one.username} vs {match.player_two.username}
                      </h3>
                    </div>
                    <StatusBadge value={match.status} />
                  </div>

                  <div className="grid grid-3" style={{ marginTop: "16px" }}>
                    <div>
                      <p className="muted">Score</p>
                      <strong>
                        {match.player_one_score ?? "-"} : {match.player_two_score ?? "-"}
                      </strong>
                    </div>
                    <div>
                      <p className="muted">Winner</p>
                      <strong>{match.winner?.username ?? "Not decided"}</strong>
                    </div>
                    <div>
                      <p className="muted">Completed</p>
                      <strong>{formatDate(match.completed_at)}</strong>
                    </div>
                  </div>

                  {match.status === "SCHEDULED" ? (
                    <div className="grid grid-2" style={{ marginTop: "16px" }}>
                      <div className="form-group">
                        <label htmlFor={`player-one-score-${match.id}`}>
                          {match.player_one.username}
                        </label>
                        <input
                          id={`player-one-score-${match.id}`}
                          type="number"
                          min={0}
                          value={score.one}
                          onChange={(event) =>
                            setScores((prev) => ({
                              ...prev,
                              [match.id]: { ...score, one: event.target.value },
                            }))
                          }
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor={`player-two-score-${match.id}`}>
                          {match.player_two.username}
                        </label>
                        <input
                          id={`player-two-score-${match.id}`}
                          type="number"
                          min={0}
                          value={score.two}
                          onChange={(event) =>
                            setScores((prev) => ({
                              ...prev,
                              [match.id]: { ...score, two: event.target.value },
                            }))
                          }
                        />
                      </div>

                      <div className="row">
                        <button
                          type="button"
                          onClick={() => void handleSubmitResult(match)}
                        >
                          Submit result
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </section>
      ) : null}
    </main>
  );
}
