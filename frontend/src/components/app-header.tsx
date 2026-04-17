"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { clearTokens } from "@/src/shared/lib/auth";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/profile", label: "Profile" },
  { href: "/teams", label: "Teams" },
  { href: "/tournaments", label: "Tournaments" },
  { href: "/matches", label: "Matches" },
];

export default function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <Link href="/" className="app-header__brand">
          <span className="app-header__brand-mark">CH</span>
          <span>CyberHub</span>
        </Link>

        <nav className="app-header__nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname?.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`app-header__link ${isActive ? "is-active" : ""}`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <button
          type="button"
          onClick={handleLogout}
          className="app-header__logout"
        >
          Logout
        </button>
      </div>
    </header>
  );
}