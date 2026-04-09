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
          <h1 className="page-title" style={{ marginTop: "14px" }}>
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

      <div className="grid grid-3" style={{ marginBottom: "24px" }}>
        <div className="card">
          <h3>Tournaments</h3>
          <p>
            Create, browse and manage tournaments with transparent brackets and
            match progression.
          </p>
        </div>

        <div className="card">
          <h3>Ranked matches</h3>
          <p>
            Build competitive flows around matchmaking, ratings and player
            performance.
          </p>
        </div>

        <div className="card">
          <h3>Player profiles</h3>
          <p>
            Keep identity, activity and future match statistics in a single
            account space.
          </p>
        </div>
      </div>

      <section>
        <h2>Quick navigation</h2>
        <p style={{ marginBottom: "20px" }}>
          This is the first frontend shell. Next we can connect real business
          pages for teams and tournaments.
        </p>

        <div className="grid grid-2">
          <div className="card">
            <h3>Account</h3>
            <div className="row" style={{ marginTop: "16px" }}>
              <Link href="/profile">
                <button type="button">Profile</button>
              </Link>
              <Link href="/login" className="btn btn-secondary">
                Login
              </Link>
              <Link href="/register" className="btn btn-secondary">
                Register
              </Link>
            </div>
          </div>

          <div className="card">
            <h3>Coming next</h3>
            <p style={{ marginBottom: "16px" }}>
              Teams, tournaments, protected routes and shared navigation.
            </p>
            <div className="badge">Frontend foundation ready</div>
          </div>
        </div>
      </section>
    </main>
  );
}