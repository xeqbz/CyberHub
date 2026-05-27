"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/src/hooks/use-current-user";
import {
  getProfileHistory,
  type ProfileHistory,
} from "@/src/shared/api/platform";
import { updateCurrentUser } from "@/src/shared/api/users";
import { clearTokens, getAccessToken } from "@/src/shared/lib/auth";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatOptionalDate(value: string | null): string {
  return value ? formatDate(value) : "Not specified";
}

export default function ProfilePage() {
  const router = useRouter();
  const {
    user,
    isLoading,
    error: loadError,
    refreshUser,
    clearUser,
  } = useCurrentUser();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");

  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [history, setHistory] = useState<ProfileHistory | null>(null);
  const [historyError, setHistoryError] = useState("");

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;

    setUsername(user.username);
    setEmail(user.email);
  }, [user]);

  useEffect(() => {
    async function loadHistory() {
      const token = getAccessToken();
      if (!token || !user) return;

      try {
        setHistoryError("");
        setHistory(await getProfileHistory(token));
      } catch (error) {
        setHistoryError(
          error instanceof Error ? error.message : "Failed to load profile history",
        );
      }
    }

    void loadHistory();
  }, [user]);

  const initials = useMemo(() => {
    if (!user?.username) return "CH";
    return user.username.slice(0, 2).toUpperCase();
  }, [user]);

  const hasChanges = useMemo(() => {
    if (!user) return false;

    return (
      username.trim() !== user.username ||
      email.trim().toLowerCase() !== user.email.toLowerCase()
    );
  }, [user, username, email]);

  function handleResetForm() {
    if (!user) return;

    setUsername(user.username);
    setEmail(user.email);
    setFormError("");
    setFormSuccess("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setFormError("You need to login before updating your profile.");
      return;
    }

    const nextUsername = username.trim();
    const nextEmail = email.trim();

    if (!nextUsername) {
      setFormError("Username cannot be empty.");
      return;
    }

    if (!nextEmail) {
      setFormError("Email cannot be empty.");
      return;
    }

    if (!nextEmail.includes("@")) {
      setFormError("Enter a valid email address.");
      return;
    }

    if (!hasChanges) {
      setFormSuccess("No changes to save.");
      setFormError("");
      return;
    }

    setFormError("");
    setFormSuccess("");
    setIsSaving(true);

    try {
      await updateCurrentUser(
        {
          username: nextUsername,
          email: nextEmail,
        },
        token,
      );

      await refreshUser();
      setFormSuccess("Profile updated successfully.");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to update profile",
      );
    } finally {
      setIsSaving(false);
    }
  }

  function handleLogout() {
    clearTokens();
    clearUser();
    router.push("/login");
  }

  return (
    <main className="page">
      <section className="page-hero">
        <div
          className="row"
          style={{ justifyContent: "space-between", alignItems: "flex-start" }}
        >
          <div>
            <p className="eyebrow">Profile</p>
            <h1>{user?.username ?? "Profile"}</h1>
            <p>
              Manage your CyberHub account, basic identity data and quick access
              to personal sections.
            </p>
          </div>

          <div
            className="card"
            style={{
              width: "84px",
              height: "84px",
              display: "grid",
              placeItems: "center",
              fontSize: "1.5rem",
              fontWeight: 700,
            }}
          >
            {initials}
          </div>
        </div>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/" className="btn btn-secondary">
            Back to home
          </Link>
          <Link href="/my-teams" className="btn btn-secondary">
            My teams
          </Link>
          <Link href="/my-tournaments" className="btn btn-secondary">
            My tournaments
          </Link>
          <Link href="/my-matches" className="btn btn-secondary">
            My matches
          </Link>
          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </section>

      {isLoading ? (
        <section className="card">
          <h2>Loading profile...</h2>
          <p>Please wait while we fetch your account data.</p>
        </section>
      ) : null}

      {!isLoading && loadError ? (
        <Alert variant="error" title="Failed to load profile">
          {loadError}
        </Alert>
      ) : null}

      {!isLoading && !loadError && !user ? (
        <EmptyState
          title="Profile is unavailable"
          description="You need to login again to access your account."
          action={
            <Link href="/login" className="btn btn-secondary">
              Go to login
            </Link>
          }
        />
      ) : null}

      {!isLoading && !loadError && user ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">Username</p>
              <strong>{user.username}</strong>
            </div>

            <div className="card">
              <p className="muted">Email</p>
              <strong>{user.email}</strong>
            </div>

            <div className="card">
              <p className="muted">Role</p>
              <StatusBadge value={user.role} />
            </div>

            <div className="card">
              <p className="muted">Account status</p>
              <strong>{user.is_active ? "Active" : "Inactive"}</strong>
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Edit profile</h2>
              <p style={{ marginBottom: "16px" }}>
                Update the basic account data currently supported by the API.
              </p>

              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="profile-username">Username</label>
                  <input
                    id="profile-username"
                    type="text"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder="Enter username"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="profile-email">Email</label>
                  <input
                    id="profile-email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="Enter email"
                    required
                  />
                </div>

                {formError ? (
                  <Alert variant="error" title="Update failed">
                    {formError}
                  </Alert>
                ) : null}

                {formSuccess ? (
                  <Alert variant="success" title="Profile saved">
                    {formSuccess}
                  </Alert>
                ) : null}

                <div className="row" style={{ marginTop: "16px" }}>
                  <button type="submit" disabled={isSaving}>
                    {isSaving ? "Saving..." : "Save changes"}
                  </button>

                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleResetForm}
                    disabled={isSaving}
                  >
                    Reset
                  </button>
                </div>
              </form>
            </div>

            <div className="card">
              <h2>Account details</h2>

              <div className="grid" style={{ gap: "14px", marginTop: "16px" }}>
                <div>
                  <p className="muted">Account ID</p>
                  <strong>{user.id}</strong>
                </div>

                <div>
                  <p className="muted">Created at</p>
                  <strong>{formatDate(user.created_at)}</strong>
                </div>

                <div>
                  <p className="muted">Updated at</p>
                  <strong>{formatDate(user.updated_at)}</strong>
                </div>

                <div>
                  <p className="muted">Active flag</p>
                  <strong>{String(user.is_active)}</strong>
                </div>
              </div>
            </div>
          </section>

          <section className="card">
            <h2>Quick navigation</h2>
            <p style={{ marginBottom: "16px" }}>
              Fast access to the main personal areas of the platform.
            </p>

            <div className="grid grid-2">
              <Link href="/my-teams" className="card">
                <p className="muted">Teams</p>
                <strong>Open my teams</strong>
              </Link>

              <Link href="/my-tournaments" className="card">
                <p className="muted">Tournaments</p>
                <strong>Open my tournaments</strong>
              </Link>

              <Link href="/my-matches" className="card">
                <p className="muted">Matches</p>
                <strong>Open my matches</strong>
              </Link>

              <Link href="/" className="card">
                <p className="muted">Dashboard</p>
                <strong>Back to home</strong>
              </Link>
            </div>
          </section>

          <section style={{ marginTop: "24px" }}>
            <h2>Participation history</h2>

            {historyError ? (
              <Alert variant="error" title="History unavailable">
                {historyError}
              </Alert>
            ) : null}

            {!history && !historyError ? <p>Loading history...</p> : null}

            {history ? (
              <div className="grid grid-2" style={{ marginTop: "16px" }}>
                <div>
                  <h3>Teams</h3>
                  {history.teams.length === 0 ? (
                    <p className="muted">No team memberships yet.</p>
                  ) : (
                    <div className="grid" style={{ marginTop: "12px" }}>
                      {history.teams.map((team) => (
                        <Link key={team.id} href={`/teams/${team.id}`} className="card">
                          <strong>{team.name}</strong>
                          <p className="muted">
                            {team.role} · joined {formatDate(team.created_at)}
                          </p>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3>Tournaments</h3>
                  {history.tournaments.length === 0 ? (
                    <p className="muted">No tournament applications yet.</p>
                  ) : (
                    <div className="grid" style={{ marginTop: "12px" }}>
                      {history.tournaments.map((tournament) => (
                        <Link
                          key={`${tournament.id}-${tournament.team_name}`}
                          href={`/tournaments/${tournament.id}`}
                          className="card"
                        >
                          <div
                            className="row"
                            style={{ justifyContent: "space-between" }}
                          >
                            <strong>{tournament.name}</strong>
                            <StatusBadge value={tournament.participant_status} />
                          </div>
                          <p className="muted">
                            {tournament.team_name} · {tournament.status} ·{" "}
                            {formatOptionalDate(tournament.starts_at)}
                          </p>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3>Tournament matches</h3>
                  {history.tournament_matches.length === 0 ? (
                    <p className="muted">No tournament matches yet.</p>
                  ) : (
                    <div className="grid" style={{ marginTop: "12px" }}>
                      {history.tournament_matches.map((match) => (
                        <Link
                          key={match.id}
                          href={`/matches/${match.id}`}
                          className="card"
                        >
                          <div
                            className="row"
                            style={{ justifyContent: "space-between" }}
                          >
                            <strong>
                              {match.home_team_name} vs {match.away_team_name}
                            </strong>
                            <StatusBadge value={match.status} />
                          </div>
                          <p className="muted">
                            {match.tournament_name} ·{" "}
                            {formatOptionalDate(
                              match.completed_at ?? match.scheduled_at,
                            )}
                          </p>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3>Ranked matches</h3>
                  {history.ranked_matches.length === 0 ? (
                    <p className="muted">No ranked matches yet.</p>
                  ) : (
                    <div className="grid" style={{ marginTop: "12px" }}>
                      {history.ranked_matches.map((match) => (
                        <div key={match.id} className="card">
                          <div
                            className="row"
                            style={{ justifyContent: "space-between" }}
                          >
                            <strong>
                              {match.player_one.username} vs{" "}
                              {match.player_two.username}
                            </strong>
                            <StatusBadge value={match.status} />
                          </div>
                          <p className="muted">
                            {match.discipline} · {match.mode} ·{" "}
                            {formatOptionalDate(match.completed_at)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </main>
  );
}
