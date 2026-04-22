"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  addTeamMember,
  deleteTeam,
  getTeam,
  removeTeamMember,
  updateTeam,
  updateTeamMemberRole,
  type TeamMember,
  type TeamMemberRole,
  type TeamRead,
} from "@/src/shared/api/teams";
import { getAccessToken } from "@/src/shared/lib/auth";
import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";
import { useCurrentUser } from "@/src/hooks/use-current-user";

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export default function TeamDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const teamId = useMemo(() => Number(params?.id), [params]);
  const { user: currentUser, isLoading: isLoadingCurrentUser } = useCurrentUser();

  const [team, setTeam] = useState<TeamRead | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [updateError, setUpdateError] = useState("");
  const [updateSuccess, setUpdateSuccess] = useState("");
  const [isUpdatingTeam, setIsUpdatingTeam] = useState(false);

  const [newMemberUserId, setNewMemberUserId] = useState("");
  const [newMemberRole, setNewMemberRole] = useState<TeamMemberRole>("MEMBER");
  const [addMemberError, setAddMemberError] = useState("");
  const [addMemberSuccess, setAddMemberSuccess] = useState("");
  const [isAddingMember, setIsAddingMember] = useState(false);

  const [memberActionError, setMemberActionError] = useState("");
  const [memberActionSuccess, setMemberActionSuccess] = useState("");
  const [busyMemberUserId, setBusyMemberUserId] = useState<number | null>(null);

  const [deleteError, setDeleteError] = useState("");
  const [isDeletingTeam, setIsDeletingTeam] = useState(false);

  useEffect(() => {
    async function loadTeam() {
      if (!Number.isFinite(teamId)) {
        setError("Invalid team id");
        setIsLoading(false);
        return;
      }

      try {
        setError("");
        setIsLoading(true);

        const data = await getTeam(teamId);
        setTeam(data);
        setEditName(data.name);
        setEditDescription(data.description ?? "");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load team");
      } finally {
        setIsLoading(false);
      }
    }

    void loadTeam();
  }, [teamId]);

  const isOwner = Boolean(
    currentUser && team && currentUser.id === team.owner_id,
  );

  async function refreshTeam() {
    if (!Number.isFinite(teamId)) return;

    const data = await getTeam(teamId);
    setTeam(data);
    setEditName(data.name);
    setEditDescription(data.description ?? "");
  }

  async function handleTeamUpdate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setUpdateError("You need to login before updating a team");
      return;
    }

    setUpdateError("");
    setUpdateSuccess("");
    setIsUpdatingTeam(true);

    try {
      const updated = await updateTeam(
        teamId,
        {
          name: editName,
          description: editDescription.trim() || null,
        },
        token,
      );

      setTeam(updated);
      setUpdateSuccess("Team updated successfully");
    } catch (err) {
      setUpdateError(
        err instanceof Error ? err.message : "Failed to update team",
      );
    } finally {
      setIsUpdatingTeam(false);
    }
  }

  async function handleAddMember(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setAddMemberError("You need to login before adding members");
      return;
    }

    if (!newMemberUserId) {
      setAddMemberError("User ID is required");
      return;
    }

    setAddMemberError("");
    setAddMemberSuccess("");
    setIsAddingMember(true);

    try {
      await addTeamMember(
        teamId,
        {
          user_id: Number(newMemberUserId),
          role: newMemberRole,
        },
        token,
      );

      setAddMemberSuccess("Member added successfully");
      setNewMemberUserId("");
      setNewMemberRole("MEMBER");
      await refreshTeam();
    } catch (err) {
      setAddMemberError(
        err instanceof Error ? err.message : "Failed to add member",
      );
    } finally {
      setIsAddingMember(false);
    }
  }

  async function handleRoleChange(member: TeamMember, role: TeamMemberRole) {
    const token = getAccessToken();
    if (!token) {
      setMemberActionError("You need to login before changing member roles");
      return;
    }

    setMemberActionError("");
    setMemberActionSuccess("");
    setBusyMemberUserId(member.user_id);

    try {
      await updateTeamMemberRole(teamId, member.user_id, { role }, token);
      setMemberActionSuccess("Member role updated successfully");
      await refreshTeam();
    } catch (err) {
      setMemberActionError(
        err instanceof Error ? err.message : "Failed to update member role",
      );
    } finally {
      setBusyMemberUserId(null);
    }
  }

  async function handleRemoveMember(member: TeamMember) {
    const token = getAccessToken();
    if (!token) {
      setMemberActionError("You need to login before removing members");
      return;
    }

    const confirmed = window.confirm(
      `Remove ${member.user.username} from this team?`,
    );

    if (!confirmed) {
      return;
    }

    setMemberActionError("");
    setMemberActionSuccess("");
    setBusyMemberUserId(member.user_id);

    try {
      await removeTeamMember(teamId, member.user_id, token);
      setMemberActionSuccess("Member removed successfully");
      await refreshTeam();
    } catch (err) {
      setMemberActionError(
        err instanceof Error ? err.message : "Failed to remove member",
      );
    } finally {
      setBusyMemberUserId(null);
    }
  }

  async function handleDeleteTeam() {
    const token = getAccessToken();
    if (!token) {
      setDeleteError("You need to login before deleting a team");
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to delete this team?",
    );

    if (!confirmed) {
      return;
    }

    setDeleteError("");
    setIsDeletingTeam(true);

    try {
      await deleteTeam(teamId, token);
      router.push("/teams");
    } catch (err) {
      setDeleteError(
        err instanceof Error ? err.message : "Failed to delete team",
      );
      setIsDeletingTeam(false);
    }
  }

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">Team details</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            {team?.name ?? "Team"}
          </h1>
          <p className="page-subtitle">
            Team overview, owner information, roster and member management.
          </p>
        </div>

        <div className="row">
          <Link href="/teams" className="btn btn-secondary">
            Back to teams
          </Link>
          <Link href="/my-teams" className="btn btn-secondary">
            My teams
          </Link>
        </div>
      </div>

      {isLoading ? (
        <section>
          <h2>Loading team...</h2>
          <p>Please wait while we fetch team details.</p>
        </section>
      ) : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Failed to load team">
          {error}
        </Alert>
      ) : null}

      {!isLoading && team ? (
        <>
          {!isLoadingCurrentUser && !isOwner ? (
            <Alert variant="info" title="Read-only mode">
              You are not the owner of this team, so management actions are hidden.
            </Alert>
          ) : null}

          <div className="grid grid-3" style={{ marginBottom: "24px" }}>
            <div className="card stat-card">
              <div className="stat-label">Team ID</div>
              <div className="stat-value">{team.id}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Owner</div>
              <div className="stat-value">{team.owner.username}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Members</div>
              <div className="stat-value">{team.members.length}</div>
            </div>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
              <h2>General info</h2>
              <div className="grid" style={{ marginTop: "18px" }}>
                <div>
                  <p className="muted">Name</p>
                  <strong>{team.name}</strong>
                </div>

                <div>
                  <p className="muted">Description</p>
                  <strong>{team.description || "No description provided"}</strong>
                </div>

                <div>
                  <p className="muted">Created at</p>
                  <strong>{formatDate(team.created_at)}</strong>
                </div>

                <div>
                  <p className="muted">Updated at</p>
                  <strong>{formatDate(team.updated_at)}</strong>
                </div>
              </div>
            </section>

            <section>
              <h2>Owner</h2>
              <div className="grid" style={{ marginTop: "18px" }}>
                <div>
                  <p className="muted">Username</p>
                  <strong>{team.owner.username}</strong>
                </div>

                <div>
                  <p className="muted">Email</p>
                  <strong>{team.owner.email}</strong>
                </div>

                <div>
                  <p className="muted">Role</p>
                  <strong>{team.owner.role}</strong>
                </div>

                <div>
                  <p className="muted">Status</p>
                  <strong>{team.owner.is_active ? "Active" : "Inactive"}</strong>
                </div>
              </div>
            </section>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
              <h2>Edit team</h2>

              {isOwner ? (
                <form onSubmit={handleTeamUpdate}>
                  <div className="form-group">
                    <label htmlFor="team-name">Name</label>
                    <input
                      id="team-name"
                      type="text"
                      value={editName}
                      onChange={(event) => setEditName(event.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="team-description">Description</label>
                    <textarea
                      id="team-description"
                      value={editDescription}
                      onChange={(event) => setEditDescription(event.target.value)}
                    />
                  </div>

                  {updateError ? (
                    <Alert variant="error" title="Team update failed">
                      {updateError}
                    </Alert>
                  ) : null}

                  {updateSuccess ? (
                    <Alert variant="success" title="Team updated">
                      {updateSuccess}
                    </Alert>
                  ) : null}

                  <button type="submit" disabled={isUpdatingTeam}>
                    {isUpdatingTeam ? "Saving..." : "Save changes"}
                  </button>
                </form>
              ) : (
                <EmptyState
                  title="Owner action only"
                  description="Only the team owner can edit team information."
                />
              )}
            </section>

            <section>
              <h2>Add member</h2>

              {isOwner ? (
                <form onSubmit={handleAddMember}>
                  <div className="form-group">
                    <label htmlFor="new-member-id">User ID</label>
                    <input
                      id="new-member-id"
                      type="number"
                      min={1}
                      value={newMemberUserId}
                      onChange={(event) => setNewMemberUserId(event.target.value)}
                      placeholder="Enter user ID"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="new-member-role">Role</label>
                    <select
                      id="new-member-role"
                      value={newMemberRole}
                      onChange={(event) =>
                        setNewMemberRole(event.target.value as TeamMemberRole)
                      }
                    >
                      <option value="MEMBER">MEMBER</option>
                      <option value="OWNER">OWNER</option>
                    </select>
                  </div>

                  {addMemberError ? (
                    <Alert variant="error" title="Add member failed">
                      {addMemberError}
                    </Alert>
                  ) : null}

                  {addMemberSuccess ? (
                    <Alert variant="success" title="Member added">
                      {addMemberSuccess}
                    </Alert>
                  ) : null}

                  <button type="submit" disabled={isAddingMember}>
                    {isAddingMember ? "Adding..." : "Add member"}
                  </button>
                </form>
              ) : (
                <EmptyState
                  title="Owner action only"
                  description="Only the team owner can add members."
                />
              )}
            </section>
          </div>

          <section>
            <h2>Roster</h2>
            <p style={{ marginBottom: "20px" }}>
              Current team members returned by the backend.
            </p>

            {memberActionError ? (
              <Alert variant="error" title="Member action failed">
                {memberActionError}
              </Alert>
            ) : null}

            {memberActionSuccess ? (
              <Alert variant="success" title="Member action complete">
                {memberActionSuccess}
              </Alert>
            ) : null}

            {team.members.length === 0 ? (
              <EmptyState
                title="No members"
                description="This team currently has no members."
              />
            ) : (
              <div className="grid">
                {team.members.map((member) => (
                  <div key={member.id} className="card">
                    <div className="row" style={{ justifyContent: "space-between" }}>
                      <div>
                        <h3>{member.user.username}</h3>
                        <p>{member.user.email}</p>
                      </div>

                      <StatusBadge value={member.role} />
                    </div>

                    <div className="grid grid-2" style={{ marginTop: "16px" }}>
                      <div>
                        <p className="muted">User ID</p>
                        <strong>{member.user_id}</strong>
                      </div>

                      <div>
                        <p className="muted">Joined record created</p>
                        <strong>{formatDate(member.created_at)}</strong>
                      </div>
                    </div>

                    {isOwner ? (
                      <div className="row" style={{ marginTop: "16px" }}>
                        {member.role !== "OWNER" ? (
                          <button
                            type="button"
                            onClick={() => handleRoleChange(member, "OWNER")}
                            disabled={busyMemberUserId === member.user_id}
                          >
                            {busyMemberUserId === member.user_id
                              ? "Updating..."
                              : "Make owner"}
                          </button>
                        ) : null}

                        {member.role !== "MEMBER" ? (
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => handleRoleChange(member, "MEMBER")}
                            disabled={busyMemberUserId === member.user_id}
                          >
                            {busyMemberUserId === member.user_id
                              ? "Updating..."
                              : "Make member"}
                          </button>
                        ) : null}

                        {member.role !== "OWNER" ? (
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => handleRemoveMember(member)}
                            disabled={busyMemberUserId === member.user_id}
                          >
                            {busyMemberUserId === member.user_id
                              ? "Removing..."
                              : "Remove"}
                          </button>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </section>

          <section style={{ marginTop: "24px" }}>
            <h2>Danger zone</h2>
            <p style={{ marginBottom: "18px" }}>
              Deleting a team removes it permanently.
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
                  onClick={handleDeleteTeam}
                  disabled={isDeletingTeam}
                >
                  {isDeletingTeam ? "Deleting..." : "Delete team"}
                </button>
              </>
            ) : (
              <EmptyState
                title="Owner action only"
                description="Only the team owner can delete this team."
              />
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}