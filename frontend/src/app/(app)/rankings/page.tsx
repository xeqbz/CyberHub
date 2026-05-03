"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import { useCurrentUser } from "@/src/hooks/use-current-user";
import { listRankings, type RankingUser } from "@/src/shared/api/platform";

export default function RankingsPage() {
  const { user } = useCurrentUser();
  const [rankings, setRankings] = useState<RankingUser[]>([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRankings = useCallback(async (nextSearch = "") => {
    try {
      setError("");
      setIsLoading(true);
      setRankings(await listRankings(nextSearch.trim() || undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load rankings");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRankings("");
  }, [loadRankings]);

  const currentUserRank = useMemo(() => {
    if (!user) return null;
    const index = rankings.findIndex((item) => item.id === user.id);
    return index >= 0 ? index + 1 : null;
  }, [rankings, user]);

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Rankings</p>
        <h1>Player rating table</h1>
        <p>Current ELO ratings, wins, losses and draw records.</p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/ranked" className="btn btn-secondary">
            Ranked matches
          </Link>
          <Link href="/statistics" className="btn btn-secondary">
            Statistics
          </Link>
          <button type="button" onClick={() => void loadRankings(search)}>
            Refresh
          </button>
        </div>
      </section>

      <section className="card" style={{ marginBottom: "24px" }}>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void loadRankings(search);
          }}
        >
          <div className="form-group">
            <label htmlFor="ranking-search">Search player</label>
            <input
              id="ranking-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Username"
            />
          </div>
          <div className="row">
            <button type="submit">Search</button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setSearch("");
                void loadRankings("");
              }}
            >
              Reset
            </button>
          </div>
        </form>
      </section>

      {currentUserRank ? (
        <Alert variant="info" title="Your ranking">
          You are currently #{currentUserRank} with {user?.rating} rating points.
        </Alert>
      ) : null}

      {isLoading ? (
        <section className="card">
          <h2>Loading rankings...</h2>
        </section>
      ) : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Rankings unavailable">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !error && rankings.length === 0 ? (
        <EmptyState
          title="No players found"
          description="Players will appear here after registration."
        />
      ) : null}

      {!isLoading && !error && rankings.length > 0 ? (
        <section className="card">
          <div className="grid" style={{ gap: "12px" }}>
            {rankings.map((player, index) => (
              <div key={player.id} className="card">
                <div
                  className="row"
                  style={{ justifyContent: "space-between", alignItems: "center" }}
                >
                  <div>
                    <p className="muted">#{index + 1}</p>
                    <h3>{player.username}</h3>
                  </div>
                  <strong>{player.rating}</strong>
                </div>

                <div className="grid grid-3" style={{ marginTop: "14px" }}>
                  <div>
                    <p className="muted">Wins</p>
                    <strong>{player.wins}</strong>
                  </div>
                  <div>
                    <p className="muted">Losses</p>
                    <strong>{player.losses}</strong>
                  </div>
                  <div>
                    <p className="muted">Draws</p>
                    <strong>{player.draws}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
