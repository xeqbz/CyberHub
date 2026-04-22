"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { listTournaments, type TournamentListItem } from "@/src/shared/api/tournaments";
import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";
import { useCurrentUser } from "@/src/hooks/use-current-user";

function formatDate(value: string | null): string {
  if (!value) return "Not specified";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

export default function MyTournamentsPage() {
  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [tournaments, setTournaments] = useState<TournamentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadTournaments() {
      try {
        setError("");
        setIsLoading(true);

        const data = await listTournaments();
        setTournaments(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load tournaments",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadTournaments();
  }, []);

  const myTournaments = useMemo(() => {
    if (!currentUser) return [];
    return tournaments.filter((item) => item.owner_id === currentUser.id);
  }, [currentUser, tournaments]);

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">My tournaments</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Tournaments you own
          </h1>
          <p className="page-subtitle">
            Quick access to tournaments you created and manage.
          </p>
        </div>

        <div className="row">
          <Link href="/tournaments" className="btn btn-secondary">
            All tournaments
          </Link>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
        </div>
      </div>

      {isLoading || isLoadingCurrentUser ? <p>Loading your tournaments...</p> : null}

      {!isLoading && !isLoadingCurrentUser && error ? (
        <Alert variant="error" title="Failed to load tournaments">
          {error}
        </Alert>
      ) : null}

      {!isLoading && !isLoadingCurrentUser && !error && myTournaments.length === 0 ? (
        <EmptyState
          title="No owned tournaments yet"
          description="You have not created any tournaments yet."
          action={
            <Link href="/tournaments" className="btn btn-secondary">
              Open tournaments
            </Link>
          }
        />
      ) : null}

      {!isLoading && !isLoadingCurrentUser && !error && myTournaments.length > 0 ? (
        <div className="grid">
          {myTournaments.map((tournament) => (
            <div key={tournament.id} className="card">
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div>
                  <h3>{tournament.name}</h3>
                  <p>{tournament.description || "No description provided."}</p>
                </div>

                <StatusBadge value={tournament.status} />
              </div>

              <div className="grid grid-2" style={{ marginTop: "16px", gap: "12px" }}>
                <div>
                  <p className="muted">Max teams</p>
                  <strong>{tournament.max_teams}</strong>
                </div>

                <div>
                  <p className="muted">Starts at</p>
                  <strong>{formatDate(tournament.starts_at)}</strong>
                </div>
              </div>

              <div className="row" style={{ marginTop: "16px" }}>
                <Link
                  href={`/tournaments/${tournament.id}`}
                  className="btn btn-secondary"
                >
                  Open tournament
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </main>
  );
}