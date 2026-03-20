# Backend
pyproject.toml
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pip install -e ".[dev]"

docker compose --profile app up --build

docker compose up -d postgres redis
docker compose ps
docker compose down

http://localhost:8000/health
http://localhost:8000/health/db
http://localhost:8000/docs

docker stop cyberhub_backend
docker rm cyberhub_backend
docker compose down --remove-orphans