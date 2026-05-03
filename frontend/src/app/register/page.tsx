"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { apiRequest } from "@/src/shared/api/client";
import {
  getSafeNextPath,
  isAuthenticated,
  saveTokens,
  type TokenPair,
} from "@/src/shared/lib/auth";

function RegisterContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const nextPath = useMemo(
    () => getSafeNextPath(searchParams?.get("next")),
    [searchParams],
  );

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"USER" | "ORGANIZER">("USER");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace(nextPath);
    }
  }, [nextPath, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const data = await apiRequest<TokenPair>("/auth/register", {
        method: "POST",
        body: { username, email, password, role },
      });

      saveTokens(data);
      router.push(nextPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="auth-layout">
      <div className="auth-card">
        <div className="auth-logo">CH</div>

        <h1 className="auth-title">Register</h1>
        <p className="auth-subtitle">
          Join CyberHub to play matches, track stats and compete in tournaments.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              placeholder="Choose a username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Create a password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="new-password"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="role">Account type</label>
            <select
              id="role"
              value={role}
              onChange={(event) =>
                setRole(event.target.value as "USER" | "ORGANIZER")
              }
            >
              <option value="USER">Player</option>
              <option value="ORGANIZER">Organizer</option>
            </select>
          </div>

          {error ? <p className="error-text">{error}</p> : null}

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Registering..." : "Register"}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account?{" "}
          <Link
            href={`/login${
              nextPath !== "/" ? `?next=${encodeURIComponent(nextPath)}` : ""
            }`}
          >
            Login
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="auth-layout">
          <div className="auth-card">
            <h1 className="auth-title">Register</h1>
          </div>
        </div>
      }
    >
      <RegisterContent />
    </Suspense>
  );
}
