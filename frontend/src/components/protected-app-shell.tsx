"use client";

import { useEffect, useSyncExternalStore } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useCurrentUser } from "@/src/hooks/use-current-user";
import { getAccessToken } from "@/src/shared/lib/auth";

type ProtectedAppShellProps = {
  children: React.ReactNode;
};

function subscribeToHydrationStore() {
  return () => {};
}

function getHydratedSnapshot() {
  return true;
}

function getServerHydrationSnapshot() {
  return false;
}

export default function ProtectedAppShell({
  children,
}: ProtectedAppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { isLoading: isLoadingCurrentUser } = useCurrentUser();
  const hasHydrated = useSyncExternalStore(
    subscribeToHydrationStore,
    getHydratedSnapshot,
    getServerHydrationSnapshot,
  );

  const token = hasHydrated ? getAccessToken() : null;

  useEffect(() => {
    if (!hasHydrated || token) return;

    const search = searchParams?.toString();
    const fullPath = `${pathname}${search ? `?${search}` : ""}`;
    const next =
      fullPath && fullPath !== "/"
        ? `?next=${encodeURIComponent(fullPath)}`
        : "";

    router.replace(`/login${next}`);
  }, [hasHydrated, pathname, router, searchParams, token]);

  if (!hasHydrated || !token || isLoadingCurrentUser) {
    return (
      <main
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          padding: "24px",
          background:
            "linear-gradient(180deg, rgba(15,23,42,0.04) 0%, rgba(15,23,42,0) 100%)",
        }}
      >
        <section
          className="card"
          style={{
            width: "100%",
            maxWidth: "520px",
            textAlign: "center",
            padding: "32px 24px",
          }}
        >
          <div
            style={{
              width: "56px",
              height: "56px",
              margin: "0 auto 16px",
              borderRadius: "18px",
              display: "grid",
              placeItems: "center",
              fontWeight: 800,
              background: "rgba(15,23,42,0.08)",
              border: "1px solid rgba(15,23,42,0.10)",
            }}
          >
            CH
          </div>

          <h2 style={{ marginBottom: "8px" }}>Checking authorization...</h2>
          <p className="muted">
            Please wait while we verify your session and restore access to the
            internal workspace.
          </p>
        </section>
      </main>
    );
  }

  return <>{children}</>;
}
