import Link from "next/link";

export default function DashboardPage() {
  return (
    <main>
      <div className="page-header">
        <div>
          <span className="badge">CyberHub Dashboard</span>
          <h1 className="page-title" style={{ marginTop: "14px" }}>
            Welcome back to CyberHub
          </h1>
          <p className="page-subtitle">
            Continue managing your profile, teams, tournaments and matches from one place.
          </p>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: "24px" }}>
        <div className="card">
          <h3>Core sections</h3>
          <div className="row" style={{ marginTop: "16px" }}>
            <Link href="/profile" className="btn btn-secondary">
              Profile
            </Link>
            <Link href="/teams" className="btn btn-secondary">
              Teams
            </Link>
            <Link href="/tournaments" className="btn btn-secondary">
              Tournaments
            </Link>
            <Link href="/matches" className="btn btn-secondary">
              Matches
            </Link>
          </div>
        </div>

        <div className="card">
          <h3>My workspace</h3>
          <div className="row" style={{ marginTop: "16px" }}>
            <Link href="/my-teams" className="btn btn-secondary">
              My teams
            </Link>
            <Link href="/my-tournaments" className="btn btn-secondary">
              My tournaments
            </Link>
            <Link href="/my-matches" className="btn btn-secondary">
              My matches
            </Link>
          </div>
        </div>
      </div>

      <section>
        <h2>Next milestone</h2>
        <p style={{ marginBottom: "20px" }}>
          After personal pages, the strongest next step is profile editing or
          team member management.
        </p>

        <div className="grid grid-2">
          <div className="card">
            <h3>Good next UX step</h3>
            <p>Edit profile and improve account management flow.</p>
          </div>

          <div className="card">
            <h3>Good next product step</h3>
            <p>Manage team members, invitations and ownership actions.</p>
          </div>
        </div>
      </section>
    </main>
  );
}