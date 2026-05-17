# CyberHub Backend

Backend service for the CyberHub diploma project.

## Stack

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

## Project structure

    backend/
    ├── alembic/
    ├── app/
    ├── tests/
    ├── .env.example
    ├── alembic.ini
    ├── Dockerfile
    ├── pyproject.toml
    └── README.md

## Local setup

From the `backend` directory:

    python -m venv .venv
    source .venv/bin/activate
    pip install -U pip
    pip install -e .
    pip install -e ".[dev]"

## Run with Docker Compose

From the repository root:

    docker compose --profile app up --build

## Run only infrastructure

If you want to run PostgreSQL and Redis separately:

    docker compose up -d postgres redis

## Migrations

Apply migrations inside the backend container:

    docker compose --profile app exec backend alembic upgrade head

Create a new migration:

    docker compose --profile app exec backend alembic revision --autogenerate -m "your message"

## Tests

Run all tests locally from the `backend` directory:

    pytest -v

Run a specific test module:

    pytest tests/api/test_auth.py -v

## Demo data

After applying migrations and starting the database, seed demo data from the
`backend` directory:

    DEBUG=false ./.venv/bin/python -m app.scripts.seed_demo

If you are not using the local virtual environment:

    DEBUG=false python -m app.scripts.seed_demo

The command is idempotent and creates a complete UI walkthrough: demo users,
teams, tournament participants, matches, ranked matches, notifications, a resolved
dispute and action-log records.

Demo password for all demo accounts:

    demo12345

Useful logins:

    admin@cyberhub-demo.com
    organizer@cyberhub-demo.com
    player@cyberhub-demo.com
    rival@cyberhub-demo.com

## Formatting and linting

Run from the `backend` directory:

    ruff check app tests --fix
    black app tests
    ruff check app tests

## API documentation

Available after startup:

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Database health check: `http://localhost:8000/health/db`

Business routes are mounted under:

    /api/v1/...

Examples:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/users/me`
- `GET /api/v1/teams`
- `GET /api/v1/tournaments`
- `GET /api/v1/matches`

## Implemented modules

### Auth
- register
- login
- refresh token

### Users
- current user endpoint
- rating, wins, losses and draws

### Teams
- CRUD for teams
- list my teams
- manage team members

### Tournaments
- CRUD for tournaments
- tournament participants management
- participant application review
- discipline, format, rules and bracket settings

### Matches
- CRUD for matches
- score update
- list by tournament

### Platform
- rankings and statistics
- ranked matchmaking and ELO recalculation
- notifications
- match disputes
- admin user management
- action log
- CSV report export

## Notes

- Health endpoints are available without API prefix.
- Business endpoints use `/api/v1`.
- Environment variables should be configured via `.env` based on `.env.example`.
