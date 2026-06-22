"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import {
  createTeam,
  listMyTeams,
  listTeams,
  type TeamListItem,
  type TeamRead,
} from "@/src/shared/api/teams";
import { getAccessToken, isAuthenticated } from "@/src/shared/lib/auth";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";

type TeamScopeFilter = "ALL" | "MY_TEAMS" | "OTHERS";

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString();
}

function sortTeams<T extends { created_at: string }>(items: T[]): T[] {
  return [...items].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
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

  const [search, setSearch] = useState("");
  const [scopeFilter, setScopeFilter] = useState<TeamScopeFilter>("ALL");

  const loadTeams = useCallback(async () => {
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
  }, []);

  const loadMyTeams = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      setMyTeams([]);
      setIsLoadingMyTeams(false);
      return;
    }

    try {
      setMyTeamsError("");
      setIsLoadingMyTeams(true);

      const data = await listMyTeams(token);
      setMyTeams(data);
    } catch (err) {
      setMyTeamsError(
        err instanceof Error ? err.message : "Failed to load my teams",
      );
    } finally {
      setIsLoadingMyTeams(false);
    }
  }, []);

  useEffect(() => {
    void loadTeams();
  }, [loadTeams]);

  useEffect(() => {
    void loadMyTeams();
  }, [loadMyTeams]);

  const myTeamIds = useMemo(() => {
    return new Set(myTeams.map((team) => team.id));
  }, [myTeams]);

  const ownedTeamsCount = useMemo(() => {
    return myTeams.filter((team) => team.owner_id === team.owner.id).length;
  }, [myTeams]);

  const totalMembersAcrossMyTeams = useMemo(() => {
    return myTeams.reduce((acc, team) => acc + team.members.length, 0);
  }, [myTeams]);

  const filteredCatalogTeams = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return sortTeams(
      teams.filter((team) => {
        const isMine = myTeamIds.has(team.id);

        const matchesSearch =
          !normalizedSearch ||
          team.name.toLowerCase().includes(normalizedSearch) ||
          team.description?.toLowerCase().includes(normalizedSearch) ||
          String(team.id).includes(normalizedSearch);

        const matchesScope =
          scopeFilter === "ALL" ||
          (scopeFilter === "MY_TEAMS" && isMine) ||
          (scopeFilter === "OTHERS" && !isMine);

        return matchesSearch && matchesScope;
      }),
    );
  }, [teams, myTeamIds, search, scopeFilter]);

  async function handleCreateTeam(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();

    if (!token) {
      setCreateError("You need to login before creating a team");
      return;
    }

    const nextName = name.trim();
    const nextDescription = description.trim();

    if (!nextName) {
      setCreateError("Team name cannot be empty");
      return;
    }

    setCreateError("");
    setCreateSuccess("");
    setIsCreating(true);

    try {
      const createdTeam = await createTeam(
        {
          name: nextName,
          description: nextDescription || undefined,
        },
        token,
      );

      setCreateSuccess(`Team "${createdTeam.name}" created successfully`);
      setName("");
      setDescription("");

      setMyTeams((prev) => [createdTeam, ...prev]);
      setTeams((prev) =>
        sortTeams([
          {
            id: createdTeam.id,
            name: createdTeam.name,
            description: createdTeam.description,
            owner_id: createdTeam.owner_id,
            created_at: createdTeam.created_at,
            updated_at: createdTeam.updated_at,
          },
          ...prev,
        ]),
      );
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create team",
      );
    } finally {
      setIsCreating(false);
    }
  }

  const isInitialLoading =
    isLoadingTeams || (authenticated && isLoadingMyTeams);

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Teams</p>
        <h1>Manage and explore teams</h1>
        <p>
          Create your own roster, inspect your personal teams and browse the full
          team catalog on the platform.
        </p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/" className="btn btn-secondary">
            Home
          </Link>
          <Link href="/profile" className="btn btn-secondary">
            Profile
          </Link>
          <Link href="/my-teams" className="btn btn-secondary">
            My teams
          </Link>
          <button
            type="button"
            onClick={() => {
              void loadTeams();
              void loadMyTeams();
            }}
          >
            Refresh
          </button>
        </div>
      </section>

      {isInitialLoading ? (
        <section className="card">
          <h2>Loading teams...</h2>
          <p>Please wait while the platform team data is being loaded.</p>
        </section>
      ) : null}

      {!isInitialLoading ? (
        <>
          <section
            className="grid grid-2"
            style={{ alignItems: "stretch", marginBottom: "24px" }}
          >
            <div className="card">
              <p className="muted">All teams on platform</p>
              <strong>{teams.length}</strong>
            </div>

            <div className="card">
              <p className="muted">My teams</p>
              <strong>{myTeams.length}</strong>
            </div>

            <div className="card">
              <p className="muted">Owned teams</p>
              <strong>{ownedTeamsCount}</strong>
            </div>

            <div className="card">
              <p className="muted">Members across my teams</p>
              <strong>{totalMembersAcrossMyTeams}</strong>
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Create team</h2>
              <p style={{ marginBottom: "16px" }}>
                Create a new team and become its owner.
              </p>

              {!authenticated ? (
                <EmptyState
                  title="Authentication required"
                  description="Login or register before creating your own team."
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
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Enter team name"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="team-description">Description</label>
                    <textarea
                      id="team-description"
                      value={description}
                      onChange={(event) => setDescription(event.target.value)}
                      placeholder="Optional short description"
                      rows={4}
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

                  <div className="row" style={{ marginTop: "16px" }}>
                    <button type="submit" disabled={isCreating}>
                      {isCreating ? "Creating..." : "Create team"}
                    </button>
                  </div>
                </form>
              )}
            </div>

            <div className="card">
              <h2>Catalog filters</h2>

              <div className="grid" style={{ gap: "14px", marginTop: "16px" }}>
                <div className="form-group">
                  <label htmlFor="teams-search">Search</label>
                  <input
                    id="teams-search"
                    type="text"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search by name, description or id"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="teams-scope">Scope</label>
                  <select
                    id="teams-scope"
                    value={scopeFilter}
                    onChange={(event) =>
                      setScopeFilter(event.target.value as TeamScopeFilter)
                    }
                  >
                    <option value="ALL">All teams</option>
                    <option value="MY_TEAMS">My teams in catalog</option>
                    <option value="OTHERS">Other teams only</option>
                  </select>
                </div>

                <div className="row">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setSearch("");
                      setScopeFilter("ALL");
                    }}
                  >
                    Reset filters
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="card" style={{ marginBottom: "24px" }}>
            <div
              className="row"
              style={{ justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <h2>My teams</h2>
                <p className="muted">
                  Teams where the current authenticated user is a member.
                </p>
              </div>

              <Link href="/my-teams" className="btn btn-secondary">
                View personal page
              </Link>
            </div>

            {!authenticated ? (
              <EmptyState
                title="You are not logged in"
                description="Sign in to see the teams you belong to."
              />
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
              <div className="grid" style={{ marginTop: "18px" }}>
                {sortTeams(myTeams).map((team) => (
                  <div key={team.id} className="card">
                    <div
                      className="row"
                      style={{
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: "12px",
                      }}
                    >
                      <div>
                        <h3>{team.name}</h3>
                        <p>
                          {team.description ||
                            "No description provided for this team yet."}
                        </p>
                      </div>

                      <span className="badge">
                        {team.members.length} member
                        {team.members.length === 1 ? "" : "s"}
                      </span>
                    </div>

                    <div
                      className="grid grid-2"
                      style={{ marginTop: "16px", gap: "12px" }}
                    >
                      <div>
                        <p className="muted">Owner</p>
                        <strong>{team.owner.username}</strong>
                      </div>

                      <div>
                        <p className="muted">Created</p>
                        <strong>{formatDate(team.created_at)}</strong>
                      </div>
                    </div>

                    <div className="row" style={{ marginTop: "16px" }}>
                      <Link
                        href={`/teams/${team.id}`}
                        className="btn btn-secondary"
                      >
                        Open details
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="card">
            <div
              className="row"
              style={{ justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                <h2>All teams</h2>
                <p className="muted">
                  Public list of teams currently available on the platform.
                </p>
              </div>

              <strong>{filteredCatalogTeams.length}</strong>
            </div>

            {teamsError ? (
              <Alert variant="error" title="Failed to load teams">
                {teamsError}
              </Alert>
            ) : null}

            {!teamsError && teams.length === 0 ? (
              <EmptyState
                title="No teams yet"
                description="No teams have been created yet."
              />
            ) : null}

            {!teamsError && teams.length > 0 && filteredCatalogTeams.length === 0 ? (
              <EmptyState
                title="No teams for current filters"
                description="Try changing your search text or scope filter."
              />
            ) : null}

            {!teamsError && filteredCatalogTeams.length > 0 ? (
              <div className="grid" style={{ marginTop: "18px" }}>
                {filteredCatalogTeams.map((team) => {
                  const isMine = myTeamIds.has(team.id);

                  return (
                    <div key={team.id} className="card">
                      <div
                        className="row"
                        style={{
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          gap: "12px",
                        }}
                      >
                        <div>
                          <h3>{team.name}</h3>
                          <p>{team.description || "No description provided."}</p>
                        </div>

                        <div className="row" style={{ gap: "8px" }}>
                          {isMine ? <span className="badge">My team</span> : null}
                          <span className="badge">ID: {team.id}</span>
                        </div>
                      </div>

                      <div
                        className="grid grid-2"
                        style={{ marginTop: "16px", gap: "12px" }}
                      >
                        <div>
                          <p className="muted">Created</p>
                          <strong>{formatDate(team.created_at)}</strong>
                        </div>

                        <div>
                          <p className="muted">Ownership</p>
                          <strong>{isMine ? "Related to me" : "Catalog team"}</strong>
                        </div>
                      </div>

                      <div className="row" style={{ marginTop: "16px" }}>
                        <Link
                          href={`/teams/${team.id}`}
                          className="btn btn-secondary"
                        >
                          View team
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </main>
  );
}