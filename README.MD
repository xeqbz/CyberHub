# CyberHub

CyberHub is a diploma project focused on building a tournament platform for competitive teams and players.

## About

The project is designed as a web platform for managing:
- user authentication and authorization
- teams and team members
- tournaments and tournament participants
- matches and match results

At the current stage, the backend MVP is already implemented and covered with API tests.

## Technology stack

### Backend
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- Redis
- Celery
- WebSocket
- Docker Compose

### Frontend
- Next.js / React / TypeScript
- Planned / in progress

### Infrastructure
- Docker
- Docker Compose

## Repository structure

    CyberHub/
    ├── backend/
    ├── frontend/
    ├── docker-compose.yml
    └── README.md

## Implemented backend modules

The backend currently includes:
- authentication:
  - register
  - login
  - refresh token
- users:
  - current user endpoint
- teams:
  - create, update, delete
  - list teams
  - list my teams
  - team members management
- tournaments:
  - create, update, delete
  - tournament participants management
- matches:
  - create, update, delete
  - list matches
  - list matches by tournament
  - update match score

## Running the project

From the repository root:

    docker compose --profile app up --build

## Backend API

After startup, the backend is available at:

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Database health check: `http://localhost:8000/health/db`

Business API endpoints are available under:

    /api/v1/...

For example:
- `/api/v1/auth/register`
- `/api/v1/auth/login`
- `/api/v1/users/me`
- `/api/v1/teams`
- `/api/v1/tournaments`
- `/api/v1/matches`

## Current status

The backend foundation is stabilized:
- Docker environment is configured
- database migrations work correctly
- API tests are implemented for key modules

The next major step is frontend development and integration with the existing backend API.