"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import Alert from "@/src/components/ui/alert";
import EmptyState from "@/src/components/ui/empty-state";
import {
  listNotifications,
  markNotificationRead,
  type NotificationRead,
  type PlatformRealtimeEvent,
} from "@/src/shared/api/platform";
import { getWebSocketUrl } from "@/src/shared/config/api";
import { getAccessToken } from "@/src/shared/lib/auth";

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationRead[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [liveStatus, setLiveStatus] = useState<"connecting" | "live" | "offline">(
    "connecting",
  );

  const loadNotifications = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setError("You need to login to view notifications.");
      setIsLoading(false);
      return;
    }

    try {
      setError("");
      setIsLoading(true);
      setNotifications(await listNotifications(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notifications");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setLiveStatus("offline");
      return;
    }

    let isClosed = false;
    const socket = new WebSocket(getWebSocketUrl("/ws/notifications", token));

    socket.onopen = () => {
      setLiveStatus("live");
      socket.send("ping");
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as PlatformRealtimeEvent;
        if (message.type === "notifications.snapshot") {
          setNotifications(message.payload.notifications);
          setIsLoading(false);
        }
      } catch {
        // Ignore malformed realtime messages and keep the current HTTP snapshot.
      }
    };

    socket.onerror = () => {
      setLiveStatus("offline");
    };

    socket.onclose = () => {
      if (!isClosed) {
        setLiveStatus("offline");
      }
    };

    return () => {
      isClosed = true;
      socket.close();
    };
  }, []);

  const unreadCount = useMemo(
    () => notifications.filter((item) => !item.is_read).length,
    [notifications],
  );

  async function handleMarkRead(notificationId: number) {
    const token = getAccessToken();
    if (!token) return;

    try {
      setBusyId(notificationId);
      await markNotificationRead(notificationId, token);
      await loadNotifications();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update notification");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main className="page">
      <section className="page-hero">
        <p className="eyebrow">Notifications</p>
        <h1>System notifications</h1>
        <p>Application updates, match scheduling, dispute results and ranked events.</p>

        <div className="row" style={{ marginTop: "16px", flexWrap: "wrap" }}>
          <Link href="/" className="btn btn-secondary">
            Dashboard
          </Link>
          <button type="button" onClick={() => void loadNotifications()}>
            Refresh
          </button>
          <span className="badge">
            {liveStatus === "live"
              ? "Live"
              : liveStatus === "connecting"
                ? "Connecting"
                : "Offline"}
          </span>
        </div>
      </section>

      <section
        className="grid grid-2"
        style={{ alignItems: "stretch", marginBottom: "24px" }}
      >
        <div className="card">
          <p className="muted">All notifications</p>
          <strong>{notifications.length}</strong>
        </div>
        <div className="card">
          <p className="muted">Unread</p>
          <strong>{unreadCount}</strong>
        </div>
      </section>

      {error ? (
        <Alert variant="error" title="Notifications unavailable">
          {error}
        </Alert>
      ) : null}

      {isLoading ? (
        <section className="card">
          <h2>Loading notifications...</h2>
        </section>
      ) : null}

      {!isLoading && notifications.length === 0 ? (
        <EmptyState
          title="No notifications"
          description="Notifications will appear after platform activity."
        />
      ) : null}

      {!isLoading && notifications.length > 0 ? (
        <section className="card">
          <div className="grid" style={{ gap: "12px" }}>
            {notifications.map((notification) => (
              <div key={notification.id} className="card">
                <div
                  className="row"
                  style={{ justifyContent: "space-between", alignItems: "center" }}
                >
                  <div>
                    <h3>{notification.title}</h3>
                    <p>{notification.message}</p>
                    <p className="muted" style={{ marginTop: "8px" }}>
                      {formatDate(notification.created_at)}
                    </p>
                  </div>
                  <span className="badge">
                    {notification.is_read ? "Read" : "Unread"}
                  </span>
                </div>

                {!notification.is_read ? (
                  <div className="row" style={{ marginTop: "14px" }}>
                    <button
                      type="button"
                      onClick={() => void handleMarkRead(notification.id)}
                      disabled={busyId === notification.id}
                    >
                      {busyId === notification.id ? "Saving..." : "Mark as read"}
                    </button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
