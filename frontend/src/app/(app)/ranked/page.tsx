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

type RankedMatchFormState = {
  one: string;
  two: string;
  oneKills: string;
  oneDeaths: string;
  oneAssists: string;
  twoKills: string;
  twoDeaths: string;
  twoAssists: string;
};

function getDefaultFormState(): RankedMatchFormState {
  return {
    one: "0",
    two: "0",
    oneKills: "0",
    oneDeaths: "0",
    oneAssists: "0",
    twoKills: "0",
    twoDeaths: "0",
    twoAssists: "0",
  };
}

export default function RankedPage() {
  const [matches, setMatches] = useState<RankedMatch[]>([]);
  const [scores, setScores] = useState<Record<number, RankedMatchFormState>>({});
  const [discipline, setDiscipline] = useState("CS2");
  const [mode, setMode] = useState("1v1");
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
      const response = await findRankedOpponent(
        {
          discipline: discipline.trim() || "CS2",
          mode: mode.trim() || "1v1",
        },
        token,
      );
      const rangeText =
        response.rating_range !== null
          ? ` Rating range: ±${response.rating_range}.`
          : "";
      setMessage(
        `${response.message} (${response.discipline ?? discipline} ${
          response.mode ?? mode
        }).${rangeText}`,
      );
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

    const score = scores[match.id] ?? getDefaultFormState();
    const numericValues = {
      playerOneScore: Number(score.one),
      playerTwoScore: Number(score.two),
      playerOneKills: Number(score.oneKills),
      playerOneDeaths: Number(score.oneDeaths),
      playerOneAssists: Number(score.oneAssists),
      playerTwoKills: Number(score.twoKills),
      playerTwoDeaths: Number(score.twoDeaths),
      playerTwoAssists: Number(score.twoAssists),
    };

    if (Object.values(numericValues).some((value) => !Number.isFinite(value))) {
      setError("Scores and player statistics must be numeric.");
      return;
    }

    try {
      setError("");
      await submitRankedMatchResult(
        match.id,
        {
          player_one_score: numericValues.playerOneScore,
          player_two_score: numericValues.playerTwoScore,
          player_one_kills: numericValues.playerOneKills,
          player_one_deaths: numericValues.playerOneDeaths,
          player_one_assists: numericValues.playerOneAssists,
          player_two_kills: numericValues.playerTwoKills,
          player_two_deaths: numericValues.playerTwoDeaths,
          player_two_assists: numericValues.playerTwoAssists,
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

        <div className="grid grid-2" style={{ marginTop: "16px", maxWidth: "560px" }}>
          <div className="form-group">
            <label htmlFor="ranked-discipline">Discipline</label>
            <input
              id="ranked-discipline"
              type="text"
              value={discipline}
              onChange={(event) => setDiscipline(event.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="ranked-mode">Mode</label>
            <select
              id="ranked-mode"
              value={mode}
              onChange={(event) => setMode(event.target.value)}
            >
              <option value="1v1">1v1</option>
              <option value="2v2">2v2</option>
              <option value="5v5">5v5</option>
            </select>
          </div>
        </div>

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
              const score = scores[match.id] ?? getDefaultFormState();

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
                      <p className="muted">
                        {match.discipline} · {match.mode}
                      </p>
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

                  {match.status === "COMPLETED" ? (
                    <div className="grid grid-2" style={{ marginTop: "16px" }}>
                      <div className="card">
                        <h3>{match.player_one.username}</h3>
                        <p className="muted">
                          K/D/A: {match.player_one_kills}/
                          {match.player_one_deaths}/{match.player_one_assists}
                        </p>
                        <strong>KDA {match.player_one_kda.toFixed(2)}</strong>
                      </div>

                      <div className="card">
                        <h3>{match.player_two.username}</h3>
                        <p className="muted">
                          K/D/A: {match.player_two_kills}/
                          {match.player_two_deaths}/{match.player_two_assists}
                        </p>
                        <strong>KDA {match.player_two_kda.toFixed(2)}</strong>
                      </div>
                    </div>
                  ) : null}

                  {match.status === "SCHEDULED" ? (
                    <div className="grid" style={{ marginTop: "16px" }}>
                      <div className="grid grid-2">
                        <div className="form-group">
                          <label htmlFor={`player-one-score-${match.id}`}>
                            {match.player_one.username} score
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
                            {match.player_two.username} score
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
                      </div>

                      <div className="form-group">
                        <label>{match.player_one.username} K/D/A</label>
                        <div className="grid grid-3">
                          <input
                            aria-label={`${match.player_one.username} kills`}
                            type="number"
                            min={0}
                            value={score.oneKills}
                            onChange={(event) =>
                              setScores((prev) => ({
                                ...prev,
                                [match.id]: {
                                  ...score,
                                  oneKills: event.target.value,
                                },
                              }))
                            }
                          />
                          <input
                            aria-label={`${match.player_one.username} deaths`}
                            type="number"
                            min={0}
                            value={score.oneDeaths}
                            onChange={(event) =>
                              setScores((prev) => ({
                                ...prev,
                                [match.id]: {
                                  ...score,
                                  oneDeaths: event.target.value,
                                },
                              }))
                            }
                          />
                          <input
                            aria-label={`${match.player_one.username} assists`}
                            type="number"
                            min={0}
                            value={score.oneAssists}
                            onChange={(event) =>
                              setScores((prev) => ({
                                ...prev,
                                [match.id]: {
                                  ...score,
                                  oneAssists: event.target.value,
                                },
                              }))
                            }
                          />
                        </div>
                      </div>

                      <div className="form-group">
                        <label>{match.player_two.username} K/D/A</label>
                        <div className="grid grid-3">
                          <input
                            aria-label={`${match.player_two.username} kills`}
                            type="number"
                            min={0}
                            value={score.twoKills}
                            onChange={(event) =>
                              setScores((prev) => ({
                                ...prev,
                                [match.id]: {
                                  ...score,
                                  twoKills: event.target.value,
                                },
                              }))
                            }
                          />
                          <input
                            aria-label={`${match.player_two.username} deaths`}
                            type="number"
                            min={0}
                            value={score.twoDeaths}
                            onChange={(event) =>
                              setScores((prev) => ({
                                ...prev,
                                [match.id]: {
                                  ...score,
                                  twoDeaths: event.target.value,
                                },
                              }))
                            }
                          />
                          <input
                            aria-label={`${match.player_two.username} assists`}
                            type="number"
                            min={0}
                            value={score.twoAssists}
                            onChange={(event) =>
                              setScores((prev) => ({
                                ...prev,
                                [match.id]: {
                                  ...score,
                                  twoAssists: event.target.value,
                                },
                              }))
                            }
                          />
                        </div>
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
