"use client";

import Link from "next/link";
import { useMemo } from "react";

import { isAuthenticated } from "@/src/shared/lib/auth";

export default function HomePage() {
  const authenticated = useMemo(() => isAuthenticated(), []);

  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">CyberHub Platform</span>
          <h1 className="page-title" style={{ marginTop: 14 }}>
            Competitive esports management in one place
          </h1>
          <p className="page-subtitle">
            Manage your profile, join tournaments, play ranked matches and track
            your progress inside a single platform.
          </p>
        </div>

        <div className="row">
          {authenticated ? (
            <Link href="/profile">
              <button type="button">Open profile</button>
            </Link>
          ) : (
            <>
              <Link href="/login" className="btn btn-secondary">
                Login
              </Link>
              <Link href="/register">
                <button type="button">Get started</button>
              </Link>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: "24px" }}>
        <div className="card">
          <h3>Profile</h3>
          <p>Review your account information and session state.</p>
          <div className="row" style={{ marginTop: "16px" }}>
            <Link href="/profile" className="btn btn-secondary">
              Open profile
            </Link>
          </div>
        </div>

        <div className="card">
          <h3>Teams</h3>
          <p>Create a team, inspect rosters and manage participation.</p>
          <div className="row" style={{ marginTop: "16px" }}>
            <Link href="/teams" className="btn btn-secondary">
              Open teams
            </Link>
          </div>
        </div>

        <div className="card">
          <h3>Tournaments</h3>
          <p>Create tournaments and register teams into active brackets.</p>
          <div className="row" style={{ marginTop: "16px" }}>
            <Link href="/tournaments" className="btn btn-secondary">
              Open tournaments
            </Link>
          </div>
        </div>

        <div className="card">
          <h3>Matches</h3>
          <p>Create matches, inspect score and control tournament game flow.</p>
          <div className="row" style={{ marginTop: "16px" }}>
            <Link href="/matches" className="btn btn-secondary">
              Open matches
            </Link>
          </div>
        </div>
      </div>

      <section>
        <h2>Quick navigation</h2>
        <p style={{ marginBottom: 20 }}>
          Frontend foundation is ready. Next we can connect real business pages
          for teams and tournaments.
        </p>

        <div className="grid grid-2">
          <div className="card">
            <h3>Account</h3>
            <div className="row" style={{ marginTop: 16 }}>
              <Link href="/profile">
                <button type="button">Profile</button>
              </Link>
              <Link href="/login" className="btn btn-secondary">
                Login
              </Link>
              <Link href="/register" className="btn btn-secondary">
                Register
              </Link>
              <Link href="/teams" className="btn btn-secondary">
                Teams
              </Link>
              <Link href="/tournaments" className="btn btn-secondary">
                Tournaments
              </Link>
            </div>
          </div>

          <div className="card">
            <h3>Coming next</h3>
            <p style={{ marginBottom: 16 }}>
              Teams, tournaments, protected routes and shared navigation.
            </p>
            <div className="badge">Frontend foundation ready</div>
          </div>
        </div>
      </section>
    </main>
  );
}