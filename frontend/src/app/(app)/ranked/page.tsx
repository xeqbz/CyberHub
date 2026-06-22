"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";
import { useCurrentUser } from "@/src/hooks/use-current-user";
import {
  cancelRankedMatchmaking,
  findRankedOpponent,
  listRankedMatches,
  submitRankedMatchResult,
  type RankedMatch,
} from "@/src/shared/api/platform";
import { getCurrentUser } from "@/src/shared/api/users";
import { getAccessToken } from "@/src/shared/lib/auth";

function formatDate(value: string | null): string {
  if (!value) return "Not completed";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

const DEMO_RANKED_OPPONENT_USERNAME = "su1sside";
const DEMO_RANKED_SERVER_ADDRESS = "127.0.0.1:27015";
const DEMO_RESULT = {
  playerScore: 16,
  opponentScore: 12,
  playerKills: 16,
  playerDeaths: 12,
  playerAssists: 0,
  opponentKills: 12,
  opponentDeaths: 16,
  opponentAssists: 0,
};

function getMatchPerspective(match: RankedMatch, currentUserId: number | null) {
  const userIsPlayerTwo = currentUserId === match.player_two_id;
  const you = userIsPlayerTwo ? match.player_two : match.player_one;
  const opponent = userIsPlayerTwo ? match.player_one : match.player_two;
  const yourScore = userIsPlayerTwo
    ? match.player_two_score
    : match.player_one_score;
  const opponentScore = userIsPlayerTwo
    ? match.player_one_score
    : match.player_two_score;
  const yourKills = userIsPlayerTwo
    ? match.player_two_kills
    : match.player_one_kills;
  const yourDeaths = userIsPlayerTwo
    ? match.player_two_deaths
    : match.player_one_deaths;
  const yourAssists = userIsPlayerTwo
    ? match.player_two_assists
    : match.player_one_assists;
  const yourKda = userIsPlayerTwo ? match.player_two_kda : match.player_one_kda;
  const opponentKills = userIsPlayerTwo
    ? match.player_one_kills
    : match.player_two_kills;
  const opponentDeaths = userIsPlayerTwo
    ? match.player_one_deaths
    : match.player_two_deaths;
  const opponentAssists = userIsPlayerTwo
    ? match.player_one_assists
    : match.player_two_assists;
  const opponentKda = userIsPlayerTwo
    ? match.player_one_kda
    : match.player_two_kda;

  return {
    you,
    opponent,
    userIsPlayerTwo,
    yourScore,
    opponentScore,
    yourKills,
    yourDeaths,
    yourAssists,
    yourKda,
    opponentKills,
    opponentDeaths,
    opponentAssists,
    opponentKda,
    didWin: match.winner_id === you.id,
  };
}

export default function RankedPage() {
  const { user, refreshUser } = useCurrentUser();
  const [matches, setMatches] = useState<RankedMatch[]>([]);
  const [discipline, setDiscipline] = useState("CS2");
  const [mode, setMode] = useState("1v1");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [submittingMatchId, setSubmittingMatchId] = useState<number | null>(null);
  const [ratingUpdate, setRatingUpdate] = useState<{
    before: number;
    after: number;
  } | null>(null);

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
          demo_opponent_username: DEMO_RANKED_OPPONENT_USERNAME,
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

  async function handleCopyServerAddress() {
    try {
      setError("");
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(DEMO_RANKED_SERVER_ADDRESS);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = DEMO_RANKED_SERVER_ADDRESS;
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.append(textarea);
        textarea.focus();
        textarea.select();
        const didCopy = document.execCommand("copy");
        textarea.remove();

        if (!didCopy) {
          throw new Error("Copy command failed");
        }
      }

      setMessage("Server address copied.");
    } catch {
      setError("Failed to copy server address.");
    }
  }

  async function handleSubmitDemoResult(match: RankedMatch) {
    const token = getAccessToken();
    if (!token) {
      setError("You need to login before submitting a result.");
      return;
    }

    if (!user) {
      setError("Current user profile is still loading.");
      return;
    }

    const currentUserIsPlayerTwo = user.id === match.player_two_id;
    const payload = currentUserIsPlayerTwo
      ? {
          player_one_score: DEMO_RESULT.opponentScore,
          player_two_score: DEMO_RESULT.playerScore,
          player_one_kills: DEMO_RESULT.opponentKills,
          player_one_deaths: DEMO_RESULT.opponentDeaths,
          player_one_assists: DEMO_RESULT.opponentAssists,
          player_two_kills: DEMO_RESULT.playerKills,
          player_two_deaths: DEMO_RESULT.playerDeaths,
          player_two_assists: DEMO_RESULT.playerAssists,
        }
      : {
          player_one_score: DEMO_RESULT.playerScore,
          player_two_score: DEMO_RESULT.opponentScore,
          player_one_kills: DEMO_RESULT.playerKills,
          player_one_deaths: DEMO_RESULT.playerDeaths,
          player_one_assists: DEMO_RESULT.playerAssists,
          player_two_kills: DEMO_RESULT.opponentKills,
          player_two_deaths: DEMO_RESULT.opponentDeaths,
          player_two_assists: DEMO_RESULT.opponentAssists,
        };

    try {
      setError("");
      setSubmittingMatchId(match.id);
      const ratingBefore = user.rating;

      await submitRankedMatchResult(match.id, payload, token);
      const updatedUser = await getCurrentUser(token);

      setRatingUpdate({
        before: ratingBefore,
        after: updatedUser.rating,
      });
      setMessage(`Demo result saved. Rating ${ratingBefore} -> ${updatedUser.rating}.`);
      await refreshUser();
      await loadMatches();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit result");
    } finally {
      setSubmittingMatchId(null);
    }
  }

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Ranked</p>
        <h1>Ranked matchmaking</h1>
        <p>Find an opponent, submit the result and update ELO automatically.</p>

        {user ? (
          <div className="grid grid-3" style={{ marginTop: "18px", maxWidth: "720px" }}>
            <div
              style={{
                padding: "14px",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                background: "rgba(255, 255, 255, 0.04)",
              }}
            >
              <p className="muted">Rating</p>
              <strong>{user.rating}</strong>
              {ratingUpdate ? (
                <span
                  style={{
                    marginLeft: "8px",
                    color:
                      ratingUpdate.after >= ratingUpdate.before
                        ? "#86efac"
                        : "#fda4af",
                    fontWeight: 900,
                  }}
                >
                  {ratingUpdate.after >= ratingUpdate.before ? "+" : ""}
                  {ratingUpdate.after - ratingUpdate.before}
                </span>
              ) : null}
            </div>
            <div
              style={{
                padding: "14px",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                background: "rgba(255, 255, 255, 0.04)",
              }}
            >
              <p className="muted">Wins</p>
              <strong>{user.wins}</strong>
            </div>
            <div
              style={{
                padding: "14px",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                background: "rgba(255, 255, 255, 0.04)",
              }}
            >
              <p className="muted">Losses</p>
              <strong>{user.losses}</strong>
            </div>
          </div>
        ) : null}

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
              const perspective = getMatchPerspective(match, user?.id ?? null);
              const ratingDelta = ratingUpdate
                ? ratingUpdate.after - ratingUpdate.before
                : null;
              const isSubmittingResult = submittingMatchId === match.id;

              return (
                <div
                  key={match.id}
                  className="card"
                  style={{
                    overflow: "hidden",
                    padding: 0,
                    borderColor:
                      match.status === "COMPLETED"
                        ? "rgba(34, 197, 94, 0.32)"
                        : "var(--border)",
                  }}
                >
                  <div
                    className="row"
                    style={{
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "22px",
                      background:
                        match.status === "COMPLETED"
                          ? "linear-gradient(135deg, rgba(34, 197, 94, 0.14), rgba(239, 68, 68, 0.06))"
                          : "rgba(255, 255, 255, 0.025)",
                    }}
                  >
                    <div>
                      <p className="muted">
                        Match #{match.id} · {match.discipline} · {match.mode}
                      </p>
                      <h3 style={{ marginBottom: 0, overflowWrap: "anywhere" }}>
                        {perspective.opponent.username} vs {perspective.you.username}
                      </h3>
                    </div>
                    <StatusBadge value={match.status} />
                  </div>

                  {match.status === "COMPLETED" ? (
                    <div style={{ display: "grid", gap: "18px", padding: "22px" }}>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "minmax(0, 1fr) auto minmax(0, 1fr)",
                          gap: "16px",
                          alignItems: "center",
                        }}
                      >
                        <div style={{ minWidth: 0 }}>
                          <p className="muted">Opponent</p>
                          <strong style={{ overflowWrap: "anywhere" }}>
                            {perspective.opponent.username}
                          </strong>
                          <div
                            style={{
                              marginTop: "8px",
                              fontSize: "3rem",
                              fontWeight: 900,
                              lineHeight: 1,
                              color: "var(--text-soft)",
                            }}
                          >
                            {perspective.opponentScore ?? "-"}
                          </div>
                        </div>

                        <div style={{ textAlign: "center" }}>
                          <div
                            style={{
                              padding: "7px 12px",
                              border: "1px solid rgba(34, 197, 94, 0.32)",
                              borderRadius: "999px",
                              background: "rgba(34, 197, 94, 0.14)",
                              color: "#86efac",
                              fontSize: "0.78rem",
                              fontWeight: 900,
                            }}
                          >
                            {perspective.didWin ? "VICTORY" : "COMPLETED"}
                          </div>
                          <p className="muted" style={{ marginTop: "8px", fontSize: "0.85rem" }}>
                            {formatDate(match.completed_at)}
                          </p>
                        </div>

                        <div style={{ minWidth: 0, textAlign: "right" }}>
                          <p className="muted">You</p>
                          <strong style={{ overflowWrap: "anywhere" }}>
                            {perspective.you.username}
                          </strong>
                          <div
                            style={{
                              marginTop: "8px",
                              fontSize: "3rem",
                              fontWeight: 900,
                              lineHeight: 1,
                              color: "#fff",
                            }}
                          >
                            {perspective.yourScore ?? "-"}
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-3">
                        <div
                          style={{
                            padding: "16px",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            borderRadius: "12px",
                            background: "rgba(255, 255, 255, 0.04)",
                          }}
                        >
                          <p className="muted">Rating</p>
                          <strong style={{ fontSize: "1.5rem" }}>
                            {user?.rating ?? "Loading"}
                          </strong>
                          {ratingDelta !== null ? (
                            <span
                              style={{
                                marginLeft: "8px",
                                color: ratingDelta >= 0 ? "#86efac" : "#fda4af",
                                fontWeight: 900,
                              }}
                            >
                              {ratingDelta >= 0 ? "+" : ""}
                              {ratingDelta}
                            </span>
                          ) : null}
                        </div>

                        <div
                          style={{
                            padding: "16px",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            borderRadius: "12px",
                            background: "rgba(255, 255, 255, 0.04)",
                          }}
                        >
                          <p className="muted">Your K/D/A</p>
                          <strong style={{ fontSize: "1.5rem" }}>
                            {perspective.yourKills}/{perspective.yourDeaths}/
                            {perspective.yourAssists}
                          </strong>
                        </div>

                        <div
                          style={{
                            padding: "16px",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            borderRadius: "12px",
                            background: "rgba(255, 255, 255, 0.04)",
                          }}
                        >
                          <p className="muted">Your KDA</p>
                          <strong style={{ fontSize: "1.5rem" }}>
                            {perspective.yourKda.toFixed(2)}
                          </strong>
                        </div>
                      </div>

                      <div className="grid grid-2">
                        <div
                          style={{
                            padding: "18px",
                            border: "1px solid rgba(34, 197, 94, 0.24)",
                            borderRadius: "14px",
                            background: "rgba(34, 197, 94, 0.08)",
                          }}
                        >
                          <p className="muted">Your performance</p>
                          <h3 style={{ marginTop: "4px" }}>
                            {perspective.you.username}
                          </h3>
                          <div className="grid grid-3">
                            <strong>{perspective.yourKills} K</strong>
                            <strong>{perspective.yourDeaths} D</strong>
                            <strong>{perspective.yourAssists} A</strong>
                          </div>
                        </div>

                        <div
                          style={{
                            padding: "18px",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            borderRadius: "14px",
                            background: "rgba(255, 255, 255, 0.035)",
                          }}
                        >
                          <p className="muted">Opponent performance</p>
                          <h3 style={{ marginTop: "4px" }}>
                            {perspective.opponent.username}
                          </h3>
                          <div className="grid grid-3">
                            <strong>{perspective.opponentKills} K</strong>
                            <strong>{perspective.opponentDeaths} D</strong>
                            <strong>{perspective.opponentAssists} A</strong>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: "grid", gap: "18px", padding: "22px" }}>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "minmax(0, 1fr) auto minmax(0, 1fr)",
                          gap: "16px",
                          alignItems: "center",
                        }}
                      >
                        <div style={{ minWidth: 0 }}>
                          <p className="muted">Opponent</p>
                          <h3 style={{ overflowWrap: "anywhere" }}>
                            {perspective.opponent.username}
                          </h3>
                        </div>
                        <strong style={{ color: "var(--text-soft)" }}>VS</strong>
                        <div style={{ minWidth: 0, textAlign: "right" }}>
                          <p className="muted">You</p>
                          <h3 style={{ overflowWrap: "anywhere" }}>
                            {perspective.you.username}
                          </h3>
                        </div>
                      </div>

                      <div className="grid grid-2">
                        <div style={{ minWidth: 0 }}>
                          <p
                            style={{
                              marginBottom: "6px",
                              color: "#fff",
                              fontSize: "0.82rem",
                              fontWeight: 800,
                            }}
                          >
                            Connect with in game console
                          </p>
                          <div
                            style={{
                              display: "grid",
                              gridTemplateColumns: "minmax(0, 1fr) auto",
                              alignItems: "center",
                              minHeight: "32px",
                              overflow: "hidden",
                              border: "1px solid rgba(255, 255, 255, 0.12)",
                              borderRadius: "4px",
                              background: "rgba(255, 255, 255, 0.08)",
                            }}
                          >
                            <span
                              style={{
                                minWidth: 0,
                                padding: "0 10px",
                                color: "var(--text-soft)",
                              }}
                            >
                              Hidden
                            </span>
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => void handleCopyServerAddress()}
                              style={{
                                minHeight: "26px",
                                marginRight: "4px",
                                padding: "0 9px",
                                borderRadius: "3px",
                                fontSize: "0.72rem",
                                fontWeight: 900,
                              }}
                            >
                              COPY
                            </button>
                          </div>
                        </div>

                        <div
                          style={{
                            display: "grid",
                            alignContent: "center",
                            gap: "10px",
                            padding: "18px",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            borderRadius: "14px",
                            background: "rgba(255, 255, 255, 0.035)",
                          }}
                        >
                          <p className="muted">Demo result</p>
                          <strong>
                            {DEMO_RESULT.opponentScore} : {DEMO_RESULT.playerScore}
                          </strong>
                          <p className="muted">
                            Your K/D/A: {DEMO_RESULT.playerKills}/
                            {DEMO_RESULT.playerDeaths}/{DEMO_RESULT.playerAssists}
                          </p>
                          <button
                            type="button"
                            onClick={() => void handleSubmitDemoResult(match)}
                            disabled={isSubmittingResult}
                          >
                            {isSubmittingResult
                              ? "Saving result..."
                              : "Finish demo match"}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      ) : null}
    </main>
  );
}
