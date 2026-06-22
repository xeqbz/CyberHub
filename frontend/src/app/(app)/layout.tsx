import AppHeader from "@/src/components/app-header";
import CurrentUserProvider from "@/src/components/current-user-provider";
import ProtectedAppShell from "@/src/components/protected-app-shell";
import { Suspense } from "react";

export default function InternalAppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <CurrentUserProvider>
      <Suspense
        fallback={
          <main>
            <section className="card">
              <h2>Loading workspace...</h2>
            </section>
          </main>
        }
      >
        <ProtectedAppShell>
          <div
            style={{
              minHeight: "100vh",
              background:
                "linear-gradient(180deg, rgba(15,23,42,0.03) 0%, rgba(15,23,42,0) 220px)",
            }}
          >
            <AppHeader />

            <div
              style={{
                maxWidth: "1280px",
                margin: "0 auto",
                padding: "24px 20px 48px",
              }}
            >
              {children}
            </div>
          </div>
        </ProtectedAppShell>
      </Suspense>
    </CurrentUserProvider>
  );
}
