FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \ 
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

#Here lies backend
WORKDIR /app 

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

#For dependencies
COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --upgrade pip && pip install -e .

EXPOSE 8000