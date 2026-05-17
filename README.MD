# CyberHub

CyberHub is a diploma project focused on building a web platform for esports tournaments and competitive matches.

The platform gives players, team owners, organizers and administrators a single environment for:
- authentication and user management,
- team and roster management,
- tournament creation and participation,
- match creation and result handling,
- ranked matches and ELO rating,
- statistics, disputes, notifications, moderation and reports.

At this stage, the project already contains a working backend foundation **and** a connected frontend with core user flows.

---

## Project goals

CyberHub is being developed as a web platform that reduces manual tournament administration and gives users a more удобный way to work with tournaments, teams and matches.

The diploma scope describes CyberHub as a unified environment for:
- user registration and authorization,
- tournament creation and management,
- match handling and result tracking,
- statistics visibility,
- ranked scenarios, moderation and broader competitive tooling.

---

## Current implementation status

### Backend
Implemented and working:
- authentication:
  - register
  - login
  - refresh token
- users:
  - current user endpoint
  - player rating fields and ranked results
- teams:
  - create, update, delete
  - list all teams
  - list my teams
  - team member management
- tournaments:
  - create, update, delete
  - list tournaments
  - register/remove tournament participants
  - participant application review
  - format, discipline, rules and bracket settings
  - update tournament status
- matches:
  - create, update, delete
  - list all matches
  - list matches by tournament
  - update match score and winner
- ranked:
  - matchmaking requests
  - ranked match creation
  - ranked result submission
  - ELO recalculation
- platform:
  - rankings
  - team and tournament statistics
  - notifications
  - match result disputes
  - admin user management
  - audit/action log
  - CSV report export
- infrastructure:
  - PostgreSQL
  - Redis
  - Alembic migrations
  - Docker Compose
- testing:
  - API tests for auth, users, teams, team members, tournaments and matches

### Frontend
Implemented and already connected to backend API:
- login page
- registration page
- protected application shell for authorized routes
- current user loading through shared context/provider
- profile page
- teams page:
  - create team
  - view all teams
  - view my teams
- team details page:
  - edit team
  - add/remove members
  - change member role
  - delete team
- tournaments page:
  - create tournament
  - view all tournaments
- tournament details page:
  - view participants
  - register a team
  - approve/reject applications
  - remove a team
  - change tournament status
  - create match inside tournament
- matches page:
  - create match
  - view all matches
- match details page:
  - update score
  - set winner
  - update status/schedule
  - delete match
- additional personal pages:
  - my teams
  - my tournaments
  - my matches
- ranked, rankings and statistics pages
- disputes and notifications pages
- admin page:
  - manage users
  - resolve disputes
  - inspect action logs
  - export CSV reports
- shared UI and navigation:
  - top navigation/header
  - alert components
  - empty states
  - status badges
  - shared API client

### Remaining growth scope
The implemented branch now covers the diploma's core platform flows. The next
natural growth area is deeper real-time delivery through WebSocket channels and
more advanced tournament bracket generation for double-elimination and Swiss
formats.

---

## Technology stack

### Backend
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- Redis
- Celery
- WebSocket
- Pytest
- Ruff
- Black
- Docker / Docker Compose

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- ESLint

### Environment
- Python 3.11+
- Node.js
- Docker
- Docker Compose

---

## Repository structure

```text
CyberHub/
├── backend/          # FastAPI backend, database layer, tests, migrations
├── frontend/         # Next.js frontend
├── docker-compose.yml
└── README.MD
```

---

## Running the project

### 1. Start backend infrastructure and API

From the repository root:

```bash
docker compose --profile app up --build
```

This starts:
- PostgreSQL on `localhost:5433`
- Redis on `localhost:6379`
- Backend API on `localhost:8000`

### 2. Start frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at:

```text
http://localhost:3000
```

By default, the frontend uses:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

If needed, override it through an environment variable.

### 3. Add demo data

After migrations are applied and the backend database is running, seed a full demo
flow from the `backend` directory:

```bash
DEBUG=false ./.venv/bin/python -m app.scripts.seed_demo
```

If you run outside the local virtual environment:

```bash
DEBUG=false python -m app.scripts.seed_demo
```

The seeder is idempotent, so it can be run more than once. It creates demo users,
teams, tournament participants, tournament matches, ranked matches, notifications,
one resolved dispute and action-log records.

Demo password for all demo accounts:

```text
demo12345
```

Useful logins:

```text
admin@cyberhub-demo.com
organizer@cyberhub-demo.com
player@cyberhub-demo.com
rival@cyberhub-demo.com
```

---

## Backend API

After startup, backend documentation and health endpoints are available at:

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Database health check: `http://localhost:8000/health/db`

Business endpoints are mounted under:

```text
/api/v1/...
```

Examples:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/users/me`
- `GET /api/v1/teams`
- `GET /api/v1/tournaments`
- `GET /api/v1/matches`

---

## Tests

Run backend tests from the `backend` directory:

```bash
pytest -v
```

Run a specific test module:

```bash
pytest tests/api/test_auth.py -v
pytest tests/api/test_teams.py -v
pytest tests/api/test_tournaments.py -v
pytest tests/api/test_matches.py -v
```

---

## Migrations

Apply migrations inside the backend container:

```bash
docker compose --profile app exec backend alembic upgrade head
```

Create a new migration:

```bash
docker compose --profile app exec backend alembic revision --autogenerate -m "your message"
```

---

## What this README reflects

This README intentionally describes the **actual state of the dev branch**:
- backend foundation is implemented and tested,
- frontend is no longer just "planned",
- the application already has working pages and flows for auth, profile, teams, tournaments and matches,
- broader esports features from the diploma text are treated as roadmap items unless they are already present in code.

---

## Author

Diploma project for BSUIR.
