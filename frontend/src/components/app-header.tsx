"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useCurrentUser } from "@/src/hooks/use-current-user";
import { clearTokens } from "@/src/shared/lib/auth";

type NavItem = {
  href: string;
  label: string;
};

const PRIMARY_NAV: NavItem[] = [
  { href: "/", label: "Dashboard" },
  { href: "/profile", label: "Profile" },
  { href: "/teams", label: "Teams" },
  { href: "/tournaments", label: "Tournaments" },
  { href: "/matches", label: "Matches" },
  { href: "/rankings", label: "Rankings" },
  { href: "/statistics", label: "Statistics" },
];

const SECONDARY_NAV: NavItem[] = [
  { href: "/my-teams", label: "My teams" },
  { href: "/my-tournaments", label: "My tournaments" },
  { href: "/my-matches", label: "My matches" },
  { href: "/ranked", label: "Ranked" },
  { href: "/disputes", label: "Disputes" },
  { href: "/notifications", label: "Notifications" },
];

function isActivePath(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  return pathname === href || (href !== "/" && pathname.startsWith(href));
}

function linkClassName(active: boolean): string {
  return `app-header__link${active ? " is-active" : ""}`;
}

export default function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearUser } = useCurrentUser();
  const secondaryNavItems = [
    ...SECONDARY_NAV,
    ...(user?.role === "ADMIN" ? [{ href: "/admin", label: "Admin" }] : []),
  ];

  function handleLogout() {
    clearTokens();
    clearUser();
    router.push("/login");
  }

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <Link href="/" className="app-header__brand">
          <div className="app-header__brand-mark">CH</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: "1rem" }}>CyberHub</div>
            <div className="muted" style={{ fontSize: "0.9rem" }}>
              Esports workspace
            </div>
          </div>
        </Link>

        <div className="row" style={{ gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {user ? (
            <div className="card" style={{ padding: "10px 14px", minWidth: "220px" }}>
              <div className="muted" style={{ fontSize: "0.85rem" }}>
                Signed in as
              </div>
              <strong>{user.username}</strong>
              <div className="muted" style={{ fontSize: "0.85rem" }}>
                {user.email}
              </div>
            </div>
          ) : null}

          <button type="button" className="app-header__logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      <div className="card" style={{ padding: "12px", display: "grid", gap: "10px" }}>
        <div className="app-header__nav">
          {PRIMARY_NAV.map((item) => (
            <Link key={item.href} href={item.href} className={linkClassName(isActivePath(pathname, item.href))}>
              {item.label}
            </Link>
          ))}
        </div>

        <div style={{ height: "1px", background: "rgba(15,23,42,0.08)" }} />

        <div className="row" style={{ justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          <div className="row" style={{ gap: "8px", flexWrap: "wrap" }}>
            {secondaryNavItems.map((item) => (
              <Link key={item.href} href={item.href} className={linkClassName(isActivePath(pathname, item.href))}>
                {item.label}
              </Link>
            ))}
          </div>

          <div className="muted" style={{ fontSize: "0.9rem" }}>
            {user ? `Role: ${user.role}` : "Session active"}
          </div>
        </div>
      </div>
    </header>
  );
}
