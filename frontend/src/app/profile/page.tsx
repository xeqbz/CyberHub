"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiRequest } from "@/src/shared/api/client";

type User = {
  id: number | string;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  created_at: string;
  updated_at: string;
};

export default function ProfilePage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadProfile() {
      try {
        const token = localStorage.getItem("access_token");

        if (!token) {
          router.replace("/login");
          return;
        }

        const data = await apiRequest<User>("/users/me", {
          token,
        });

        setUser(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile");
      } finally {
        setIsLoading(false);
      }
    }

    loadProfile();
  }, [router]);

  const initials = useMemo(() => {
    if (!user?.username) return "CH";
    return user.username.slice(0, 2).toUpperCase();
  }, [user]);

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  }

  function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString();
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
        <section>
          <h2>Failed to load profile</h2>
          <p className="error-text" style={{ marginTop: "10px" }}>
            {error}
          </p>

          <div className="row" style={{ marginTop: "18px" }}>
            <button type="button" onClick={() => window.location.reload()}>
              Retry
            </button>
            <Link href="/login" className="btn btn-secondary">
              Go to login
            </Link>
          </div>
        </section>
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

          <section>
            <h2>Account details</h2>
            <p style={{ marginBottom: "20px" }}>
              Basic information returned by the backend for the current user.
            </p>

            <div className="grid grid-2">
              <div className="card">
                <h3>Identity</h3>
                <div style={{ marginTop: "14px" }} className="grid">
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
                </div>
              </div>

              <div className="card">
                <h3>Metadata</h3>
                <div style={{ marginTop: "14px" }} className="grid">
                  <div>
                    <p className="muted">Created at</p>
                    <strong>{formatDate(user.created_at)}</strong>
                  </div>

                  <div>
                    <p className="muted">Updated at</p>
                    <strong>{formatDate(user.updated_at)}</strong>
                  </div>

                  <div>
                    <p className="muted">Active</p>
                    <strong>{String(user.is_active)}</strong>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}