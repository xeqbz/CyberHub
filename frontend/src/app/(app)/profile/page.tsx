"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { updateCurrentUser } from "@/src/shared/api/users";
import { clearTokens, getAccessToken } from "@/src/shared/lib/auth";
import Alert from "@/src/components/ui/alert";
import { useCurrentUser } from "@/src/hooks/use-current-user";

export default function ProfilePage() {
  const router = useRouter();
  const {
    user,
    isLoading,
    error,
    refreshUser,
  } = useCurrentUser();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");

  const [updateError, setUpdateError] = useState("");
  const [updateSuccess, setUpdateSuccess] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setEmail(user.email);
    }
  }, [user]);

  const initials = useMemo(() => {
    if (!user?.username) return "CH";
    return user.username.slice(0, 2).toUpperCase();
  }, [user]);

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString();
  }

  async function handleProfileUpdate(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const token = getAccessToken();
    if (!token) {
      setUpdateError("You need to login before updating profile");
      return;
    }

    setUpdateError("");
    setUpdateSuccess("");
    setIsUpdating(true);

    try {
      await updateCurrentUser(
        {
          username,
          email,
        },
        token,
      );

      await refreshUser();
      setUpdateSuccess("Profile updated successfully");
    } catch (err) {
      setUpdateError(
        err instanceof Error ? err.message : "Failed to update profile",
      );
    } finally {
      setIsUpdating(false);
    }
  }

  return (
    <div className="profile-layout">
      <div className="profile-hero card">
        <div className="profile-avatar">{initials}</div>

        <div>
          <h1 className="page-title">{user?.username ?? "Profile"}</h1>
          <p className="page-subtitle">
            Your CyberHub account overview, role and account activity.
          </p>

          <div className="profile-meta">
            {user?.role ? <span className="badge">Role: {user.role}</span> : null}
            {typeof user?.is_active === "boolean" ? (
              <span className="badge">
                Status: {user.is_active ? "Active" : "Inactive"}
              </span>
            ) : null}
            {user?.email ? <span className="badge">{user.email}</span> : null}
          </div>

          <div className="row" style={{ marginTop: "18px" }}>
            <Link href="/" className="btn btn-secondary">
              Back to home
            </Link>
            <button type="button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <section>
          <h2>Loading profile...</h2>
          <p>Please wait while we fetch your account data.</p>
        </section>
      ) : null}

      {!isLoading && error ? (
        <Alert variant="error" title="Failed to load profile">
          {error}
        </Alert>
      ) : null}

      {!isLoading && user ? (
        <>
          <div className="stat-grid" style={{ marginBottom: "24px" }}>
            <div className="card stat-card">
              <div className="stat-label">Account ID</div>
              <div className="stat-value">{user.id}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Role</div>
              <div className="stat-value">{user.role}</div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Status</div>
              <div className="stat-value">
                {user.is_active ? "Active" : "Inactive"}
              </div>
            </div>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "24px" }}>
            <section>
              <h2>Edit profile</h2>
              <p style={{ marginBottom: "20px" }}>
                Update your username and email for the current account.
              </p>

              <form onSubmit={handleProfileUpdate}>
                <div className="form-group">
                  <label htmlFor="profile-username">Username</label>
                  <input
                    id="profile-username"
                    type="text"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
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
                    required
                  />
                </div>

                {updateError ? (
                  <Alert variant="error" title="Profile update failed">
                    {updateError}
                  </Alert>
                ) : null}

                {updateSuccess ? (
                  <Alert variant="success" title="Profile updated">
                    {updateSuccess}
                  </Alert>
                ) : null}

                <button type="submit" disabled={isUpdating}>
                  {isUpdating ? "Saving..." : "Save changes"}
                </button>
              </form>
            </section>

            <section>
              <h2>Account details</h2>
              <p style={{ marginBottom: "20px" }}>
                Basic information returned by the backend for the current user.
              </p>

              <div className="grid">
                <div>
                  <p className="muted">Username</p>
                  <strong>{user.username}</strong>
                </div>

                <div>
                  <p className="muted">Email</p>
                  <strong>{user.email}</strong>
                </div>

                <div>
                  <p className="muted">Role</p>
                  <strong>{user.role}</strong>
                </div>

                <div>
                  <p className="muted">Created at</p>
                  <strong>{formatDate(user.created_at)}</strong>
                </div>

                <div>
                  <p className="muted">Updated at</p>
                  <strong>{formatDate(user.updated_at)}</strong>
                </div>
              </div>
            </section>
          </div>
        </>
      ) : null}
    </div>
  );
}