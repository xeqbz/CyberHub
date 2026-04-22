import AppHeader from "@/src/components/app-header";
import CurrentUserProvider from "@/src/components/current-user-provider";
import ProtectedAppShell from "@/src/components/protected-app-shell";

export default function InternalAppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <ProtectedAppShell>
      <CurrentUserProvider>
        <AppHeader />
        <div className="app-content">{children}</div>
      </CurrentUserProvider>
    </ProtectedAppShell>
  );
}