import importlib
from contextlib import asynccontextmanager

import anyio
import fastapi.concurrency
import fastapi.dependencies.utils
import fastapi.routing
import httpx
import pytest
import starlette.concurrency
import starlette.routing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.modules.matches.model
import app.modules.platform.model
import app.modules.teams.model
import app.modules.tournaments.model
import app.modules.users.model
from app.db.base import Base
from app.db.session import get_db


async def run_inline(func, *args, **kwargs):
    return func(*args, **kwargs)


@asynccontextmanager
async def contextmanager_inline(cm):
    value = cm.__enter__()
    try:
        yield value
    except Exception as exc:
        if not cm.__exit__(type(exc), exc, exc.__traceback__):
            raise
    else:
        cm.__exit__(None, None, None)


fastapi.concurrency.run_in_threadpool = run_inline
fastapi.concurrency.contextmanager_in_threadpool = contextmanager_inline
fastapi.routing.run_in_threadpool = run_inline
fastapi.dependencies.utils.run_in_threadpool = run_inline
fastapi.dependencies.utils.contextmanager_in_threadpool = contextmanager_inline
starlette.concurrency.run_in_threadpool = run_inline
starlette.routing.run_in_threadpool = run_inline

app = importlib.import_module("app.main").app


class ASGISyncClient:
    def __init__(self) -> None:
        self.transport = httpx.ASGITransport(app=app)
        self.base_url = "http://testserver"

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(
            transport=self.transport,
            base_url=self.base_url,
        ) as client:
            return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async def runner() -> httpx.Response:
            return await self._request(method, url, **kwargs)

        return anyio.run(runner)

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)


@pytest.fixture()
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def test_session_factory(test_engine):
    return sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture()
def client(test_session_factory):
    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield ASGISyncClient()

    app.dependency_overrides.clear()
