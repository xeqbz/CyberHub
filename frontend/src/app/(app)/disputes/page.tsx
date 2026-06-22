"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";
import { listMatches, type MatchListItem } from "@/src/shared/api/matches";
import {
  createDispute,
  listMyDisputes,
  type MatchDispute,
} from "@/src/shared/api/platform";
import { listTeams, type TeamListItem } from "@/src/shared/api/teams";
import { getAccessToken } from "@/src/shared/lib/auth";

function buildTeamMap(teams: TeamListItem[]): Map<number, TeamListItem> {
  return new Map(teams.map((team) => [team.id, team]));
}

export default function DisputesPage() {
  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [teams, setTeams] = useState<TeamListItem[]>([]);
  const [disputes, setDisputes] = useState<MatchDispute[]>([]);
  const [matchId, setMatchId] = useState("");
  const [reason, setReason] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadData = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setError("You need to login to view disputes.");
      setIsLoading(false);
      return;
    }

    try {
      setError("");
      setIsLoading(true);
      const [matchData, teamData, disputeData] = await Promise.all([
        listMatches(),
        listTeams(),
        listMyDisputes(token),
      ]);
      setMatches(matchData);
      setTeams(teamData);
      setDisputes(disputeData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load disputes");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const teamMap = useMemo(() => buildTeamMap(teams), [teams]);

  async function handleCreateDispute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) {
      setError("You need to login before opening a dispute.");
      return;
    }
    if (!matchId || !reason.trim()) {
      setError("Match and reason are required.");
      return;
    }

    try {
      setError("");
      setSuccess("");
      setIsCreating(true);
      await createDispute(
        {
          match_id: Number(matchId),
          reason: reason.trim(),
        },
        token,
      );
      setSuccess("Dispute opened successfully.");
      setMatchId("");
      setReason("");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open dispute");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Disputes</p>
        <h1>Match result disputes</h1>
        <p>Open a dispute and track moderation decisions.</p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/matches" className="btn btn-secondary">
            Matches
          </Link>
          <Link href="/admin" className="btn btn-secondary">
            Admin
          </Link>
          <button type="button" onClick={() => void loadData()}>
            Refresh
          </button>
        </div>
      </section>

      {error ? (
        <Alert variant="error" title="Dispute action failed">
          {error}
        </Alert>
      ) : null}

      {success ? (
        <Alert variant="success" title="Dispute saved">
          {success}
        </Alert>
      ) : null}

      <section
        className="grid grid-2"
        style={{ alignItems: "start", marginBottom: "24px" }}
      >
        <div className="card">
          <h2>Open dispute</h2>
          <form onSubmit={handleCreateDispute}>
            <div className="form-group">
              <label htmlFor="dispute-match">Match</label>
              <select
                id="dispute-match"
                value={matchId}
                onChange={(event) => setMatchId(event.target.value)}
              >
                <option value="">Choose match</option>
                {matches.map((match) => {
                  const homeTeam = teamMap.get(match.home_team_id);
                  const awayTeam = teamMap.get(match.away_team_id);
                  return (
                    <option key={match.id} value={match.id}>
                      #{match.id} {homeTeam?.name ?? match.home_team_id} vs{" "}
                      {awayTeam?.name ?? match.away_team_id}
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="dispute-reason">Reason</label>
              <textarea
                id="dispute-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={5}
                placeholder="Describe what should be reviewed"
              />
            </div>

            <button type="submit" disabled={isCreating}>
              {isCreating ? "Opening..." : "Open dispute"}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>My disputes</h2>
          {isLoading ? <p>Loading disputes...</p> : null}
          {!isLoading && disputes.length === 0 ? (
            <EmptyState
              title="No disputes"
              description="Your disputes will appear here."
            />
          ) : (
            <div className="grid" style={{ marginTop: "18px" }}>
              {disputes.map((dispute) => (
                <div key={dispute.id} className="card">
                  <div
                    className="row"
                    style={{ justifyContent: "space-between", alignItems: "center" }}
                  >
                    <strong>Dispute #{dispute.id}</strong>
                    <StatusBadge value={dispute.status} />
                  </div>
                  <p style={{ marginTop: "10px" }}>{dispute.reason}</p>
                  {dispute.resolution ? (
                    <p className="muted" style={{ marginTop: "10px" }}>
                      Resolution: {dispute.resolution}
                    </p>
                  ) : null}
                  <div className="row" style={{ marginTop: "14px" }}>
                    <Link
                      href={`/matches/${dispute.match_id}`}
                      className="btn btn-secondary"
                    >
                      Open match
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
