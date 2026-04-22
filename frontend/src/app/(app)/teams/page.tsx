"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { createTeam, listMyTeams, listTeams, type TeamListItem, type TeamRead } from "@/src/shared/api/teams";
import { getAccessToken, isAuthenticated } from "@/src/shared/lib/auth";
import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString();
}

export default function TeamsPage() {
  const authenticated = useMemo(() => isAuthenticated(), []);

  const [teams, setTeams] = useState<TeamListItem[]>([]);
  const [myTeams, setMyTeams] = useState<TeamRead[]>([]);
  const [isLoadingTeams, setIsLoadingTeams] = useState(true);
  const [isLoadingMyTeams, setIsLoadingMyTeams] = useState(true);
  const [teamsError, setTeamsError] = useState("");
  const [myTeamsError, setMyTeamsError] = useState("");

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    async function loadTeams() {
      try {
        setTeamsError("");
        setIsLoadingTeams(true);

        const data = await listTeams();
        setTeams(data);
      } catch (err) {
        setTeamsError(err instanceof Error ? err.message : "Failed to load teams");
      } finally {
        setIsLoadingTeams(false);
      }
    }

    loadTeams();
  }, []);

  useEffect(() => {
    async function loadMyTeams() {
      const token = getAccessToken();

      if (!token) {
        setIsLoadingMyTeams(false);
        return;
      }

      try {
        setMyTeamsError("");
        setIsLoadingMyTeams(true);

        const data = await listMyTeams(token);
        setMyTeams(data);
      } catch (err) {
        setMyTeamsError(err instanceof Error ? err.message : "Failed to load my teams");
      } finally {
        setIsLoadingMyTeams(false);
      }
    }

    loadMyTeams();
  }, []);

  async function handleCreateTeam(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();

    if (!token) {
      setCreateError("You need to login before creating a team");
      return;
    }

    setCreateError("");
    setCreateSuccess("");
    setIsCreating(true);

    try {
      const createdTeam = await createTeam(
        {
          name,
          description: description.trim() || undefined,
        },
        token,
      );

      setCreateSuccess(`Team "${createdTeam.name}" created successfully`);
      setName("");
      setDescription("");

      setMyTeams((prev) => [createdTeam, ...prev]);

      setTeams((prev) => [
        {
          id: createdTeam.id,
          name: createdTeam.name,
          description: createdTeam.description,
          owner_id: createdTeam.owner_id,
          created_at: createdTeam.created_at,
          updated_at: createdTeam.updated_at,
        },
        ...prev,
      ]);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create team");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Teams</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Manage and explore teams
          </h1>
          <p className="page-subtitle">
            Browse all teams on the platform, create your own roster and open
            detailed team pages.
          </p>
        </div>

        <div className="row">
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
          <Link href="/profile" className="btn btn-secondary">
            Profile
          </Link>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: "24px" }}>
        <section>
          <h2>Create team</h2>
          <p style={{ marginBottom: "20px" }}>
            Create a new team and become its owner.
          </p>

          {!authenticated ? (
            <EmptyState
              title="Login required"
              description="You need to sign in before creating a team."
              action={
                <div className="row">
                  <Link href="/login" className="btn btn-secondary">
                    Login
                  </Link>
                  <Link href="/register" className="btn btn-secondary">
                    Register
                  </Link>
                </div>
              }
            />
          ) : (
            <form onSubmit={handleCreateTeam}>
              <div className="form-group">
                <label htmlFor="team-name">Team name</label>
                <input
                  id="team-name"
                  type="text"
                  placeholder="Enter team name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="team-description">Description</label>
                <textarea
                  id="team-description"
                  placeholder="Short team description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                />
              </div>

              {createError ? (
                <Alert variant="error" title="Team creation failed">
                  {createError}
                </Alert>
              ) : null}

              {createSuccess ? (
                <Alert variant="success" title="Team created">
                  {createSuccess}
                </Alert>
              ) : null}

              <button type="submit" disabled={isCreating}>
                {isCreating ? "Creating..." : "Create team"}
              </button>
            </form>
          )}
        </section>

        <section>
          <h2>My teams</h2>
          <p style={{ marginBottom: "20px" }}>
            Teams where the current authenticated user is a member.
          </p>

          {!authenticated ? (
            <EmptyState
              title="You are not logged in"
              description="Sign in to see the teams you belong to."
            />
          ) : isLoadingMyTeams ? (
            <p>Loading your teams...</p>
          ) : myTeamsError ? (
            <Alert variant="error" title="Failed to load your teams">
              {myTeamsError}
            </Alert>
          ) : myTeams.length === 0 ? (
            <EmptyState
              title="No personal teams yet"
              description="You are not a member of any team yet."
            />
          ) : (
            <div className="grid">
              {myTeams.map((team) => (
                <div key={team.id} className="card">
                  <div className="row" style={{ justifyContent: "space-between" }}>
                    <div>
                      <h3>{team.name}</h3>
                      <p>
                        {team.description || "No description provided for this team yet."}
                      </p>
                    </div>

                    <span className="badge">
                      {team.members.length} member{team.members.length === 1 ? "" : "s"}
                    </span>
                  </div>

                  <div style={{ marginTop: "14px" }}>
                    <p className="muted">Owner</p>
                    <strong>{team.owner.username}</strong>
                  </div>

                  <div className="row" style={{ marginTop: "16px" }}>
                    <Link href={`/teams/${team.id}`} className="btn btn-secondary">
                      Open details
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section>
        <h2>All teams</h2>
        <p style={{ marginBottom: "20px" }}>
          Public list of all teams currently available in the platform.
        </p>

        {isLoadingTeams ? <p>Loading teams...</p> : null}

        {teamsError ? (
          <Alert variant="error" title="Failed to load teams">
            {teamsError}
          </Alert>
        ) : null}

        {!isLoadingTeams && !teamsError && teams.length === 0 ? (
          <EmptyState
            title="No teams yet"
            description="No teams have been created yet."
          />
        ) : null}

        {!isLoadingTeams && !teamsError && teams.length > 0 ? (
          <div className="grid">
            {teams.map((team) => (
              <div key={team.id} className="card">
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <div>
                    <h3>{team.name}</h3>
                    <p>{team.description || "No description provided."}</p>
                  </div>
                  <span className="badge">ID: {team.id}</span>
                </div>

                <div style={{ marginTop: "14px" }}>
                  <p className="muted">Created</p>
                  <strong>{formatDate(team.created_at)}</strong>
                </div>

                <div className="row" style={{ marginTop: "16px" }}>
                  <Link href={`/teams/${team.id}`} className="btn btn-secondary">
                    View team
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}