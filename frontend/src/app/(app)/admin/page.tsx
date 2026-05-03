"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import StatusBadge from "@/src/components/ui/status-badge";
import { useCurrentUser } from "@/src/hooks/use-current-user";
import {
  adminListActionLogs,
  adminListDisputes,
  adminListUsers,
  adminResolveDispute,
  adminUpdateUser,
  bootstrapFirstAdmin,
  buildReportExportUrl,
  type ActionLog,
  type DisputeStatus,
  type MatchDispute,
} from "@/src/shared/api/platform";
import type { CurrentUser } from "@/src/shared/api/users";
import { getAccessToken } from "@/src/shared/lib/auth";

const ROLES = ["USER", "ORGANIZER", "ADMIN"] as const;

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function AdminPage() {
  const { user, refreshUser } = useCurrentUser();
  const [users, setUsers] = useState<CurrentUser[]>([]);
  const [disputes, setDisputes] = useState<MatchDispute[]>([]);
  const [logs, setLogs] = useState<ActionLog[]>([]);
  const [resolutionText, setResolutionText] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const loadAdminData = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setError("You need to login to access admin tools.");
      setIsLoading(false);
      return;
    }

    try {
      setError("");
      setIsLoading(true);
      const [userData, disputeData, logData] = await Promise.all([
        adminListUsers(token),
        adminListDisputes(token),
        adminListActionLogs(token),
      ]);
      setUsers(userData);
      setDisputes(disputeData);
      setLogs(logData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load admin data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAdminData();
  }, [loadAdminData]);

  async function handleRoleChange(
    targetUser: CurrentUser,
    role: (typeof ROLES)[number],
  ) {
    const token = getAccessToken();
    if (!token) return;

    try {
      setError("");
      const updated = await adminUpdateUser(targetUser.id, { role }, token);
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setSuccess(`Role for ${updated.username} updated.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user role");
    }
  }

  async function handleActiveChange(targetUser: CurrentUser, isActive: boolean) {
    const token = getAccessToken();
    if (!token) return;

    try {
      setError("");
      const updated = await adminUpdateUser(
        targetUser.id,
        { is_active: isActive },
        token,
      );
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setSuccess(`Status for ${updated.username} updated.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user status");
    }
  }

  async function handleResolveDispute(
    dispute: MatchDispute,
    nextStatus: Extract<DisputeStatus, "RESOLVED" | "REJECTED">,
  ) {
    const token = getAccessToken();
    if (!token) return;

    const resolution = resolutionText[dispute.id]?.trim();
    if (!resolution) {
      setError("Resolution text is required.");
      return;
    }

    try {
      setError("");
      await adminResolveDispute(dispute.id, { status: nextStatus, resolution }, token);
      setResolutionText((prev) => ({ ...prev, [dispute.id]: "" }));
      setSuccess(`Dispute #${dispute.id} updated.`);
      await loadAdminData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve dispute");
    }
  }

  async function handleExport(reportType: "users" | "tournaments" | "matches") {
    const token = getAccessToken();
    if (!token) return;

    try {
      const response = await fetch(buildReportExportUrl(reportType), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to export report");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `cyberhub-${reportType}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export report");
    }
  }

  async function handleBootstrapAdmin() {
    const token = getAccessToken();
    if (!token) return;

    try {
      setError("");
      await bootstrapFirstAdmin(token);
      await refreshUser();
      setSuccess("Current account promoted to administrator.");
      await loadAdminData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to bootstrap admin");
    }
  }

  if (user && user.role !== "ADMIN") {
    return (
      <main className="page">
        <section className="page-hero">
          <p className="eyebrow">Admin</p>
          <h1>Restricted area</h1>
          <p>Only administrators can access moderation and audit tools.</p>
        </section>
        {error ? (
          <Alert variant="error" title="Bootstrap failed">
            {error}
          </Alert>
        ) : null}
        {success ? (
          <Alert variant="success" title="Bootstrap complete">
            {success}
          </Alert>
        ) : null}
        <EmptyState
          title="Admin role required"
          description="Ask an existing administrator to update your role if needed."
          action={
            <button type="button" onClick={() => void handleBootstrapAdmin()}>
              Bootstrap first admin
            </button>
          }
        />
      </main>
    );
  }

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Admin</p>
        <h1>Moderation and audit</h1>
        <p>Manage users, review disputes, inspect action logs and export reports.</p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/disputes" className="btn btn-secondary">
            Disputes
          </Link>
          <button type="button" onClick={() => void loadAdminData()}>
            Refresh
          </button>
          <button type="button" onClick={() => void handleExport("users")}>
            Export users
          </button>
          <button type="button" onClick={() => void handleExport("tournaments")}>
            Export tournaments
          </button>
          <button type="button" onClick={() => void handleExport("matches")}>
            Export matches
          </button>
        </div>
      </section>

      {error ? (
        <Alert variant="error" title="Admin action failed">
          {error}
        </Alert>
      ) : null}

      {success ? (
        <Alert variant="success" title="Admin action saved">
          {success}
        </Alert>
      ) : null}

      {isLoading ? (
        <section className="card">
          <h2>Loading admin data...</h2>
        </section>
      ) : null}

      {!isLoading ? (
        <>
          <section className="card" style={{ marginBottom: "24px" }}>
            <h2>Users</h2>
            <div className="grid" style={{ marginTop: "18px" }}>
              {users.map((targetUser) => (
                <div key={targetUser.id} className="card">
                  <div
                    className="row"
                    style={{ justifyContent: "space-between", alignItems: "center" }}
                  >
                    <div>
                      <h3>{targetUser.username}</h3>
                      <p>{targetUser.email}</p>
                    </div>
                    <StatusBadge value={targetUser.role} />
                  </div>

                  <div className="grid grid-3" style={{ marginTop: "16px" }}>
                    <div className="form-group">
                      <label htmlFor={`role-${targetUser.id}`}>Role</label>
                      <select
                        id={`role-${targetUser.id}`}
                        value={targetUser.role}
                        onChange={(event) =>
                          void handleRoleChange(
                            targetUser,
                            event.target.value as (typeof ROLES)[number],
                          )
                        }
                      >
                        {ROLES.map((role) => (
                          <option key={role} value={role}>
                            {role}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label htmlFor={`active-${targetUser.id}`}>Active</label>
                      <select
                        id={`active-${targetUser.id}`}
                        value={String(targetUser.is_active)}
                        onChange={(event) =>
                          void handleActiveChange(
                            targetUser,
                            event.target.value === "true",
                          )
                        }
                      >
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                      </select>
                    </div>

                    <div>
                      <p className="muted">Rating</p>
                      <strong>{targetUser.rating}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section
            className="grid grid-2"
            style={{ alignItems: "start", marginBottom: "24px" }}
          >
            <div className="card">
              <h2>Disputes</h2>
              {disputes.length === 0 ? (
                <EmptyState
                  title="No disputes"
                  description="Open disputes will appear here."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
                  {disputes.map((dispute) => (
                    <div key={dispute.id} className="card">
                      <div
                        className="row"
                        style={{
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <strong>Dispute #{dispute.id}</strong>
                        <StatusBadge value={dispute.status} />
                      </div>
                      <p style={{ marginTop: "10px" }}>{dispute.reason}</p>
                      <p className="muted" style={{ marginTop: "8px" }}>
                        Opened by {dispute.opened_by.username}
                      </p>

                      {dispute.status === "OPEN" ? (
                        <div className="grid" style={{ marginTop: "14px" }}>
                          <div className="form-group">
                            <label htmlFor={`resolution-${dispute.id}`}>
                              Resolution
                            </label>
                            <textarea
                              id={`resolution-${dispute.id}`}
                              value={resolutionText[dispute.id] ?? ""}
                              onChange={(event) =>
                                setResolutionText((prev) => ({
                                  ...prev,
                                  [dispute.id]: event.target.value,
                                }))
                              }
                              rows={3}
                            />
                          </div>
                          <div className="row">
                            <button
                              type="button"
                              onClick={() =>
                                void handleResolveDispute(dispute, "RESOLVED")
                              }
                            >
                              Resolve
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() =>
                                void handleResolveDispute(dispute, "REJECTED")
                              }
                            >
                              Reject
                            </button>
                          </div>
                        </div>
                      ) : dispute.resolution ? (
                        <p className="muted" style={{ marginTop: "10px" }}>
                          Resolution: {dispute.resolution}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h2>Action log</h2>
              {logs.length === 0 ? (
                <EmptyState
                  title="No log entries"
                  description="Administrative and system actions will appear here."
                />
              ) : (
                <div className="grid" style={{ marginTop: "18px" }}>
                  {logs.map((log) => (
                    <div key={log.id} className="card">
                      <strong>{log.action}</strong>
                      <p className="muted" style={{ marginTop: "8px" }}>
                        {log.entity_type} #{log.entity_id ?? "-"} ·{" "}
                        {formatDate(log.created_at)}
                      </p>
                      <p className="muted" style={{ marginTop: "8px" }}>
                        Actor: {log.actor?.username ?? "System"}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
