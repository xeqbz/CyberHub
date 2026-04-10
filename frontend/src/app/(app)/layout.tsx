import AppHeader from "@/src/components/app-header";
import ProtectedAppShell from "@/src/components/protected-app-shell";

export default function InternalAppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <ProtectedAppShell>
      <AppHeader />
      <div className="app-content">{children}</div>
    </ProtectedAppShell>
  );
}