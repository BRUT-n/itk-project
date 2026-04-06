import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

import app.main as main_module
from app.database import engine as app_engine
from app.database import get_db, new_session
from app.main import app
from app.models import Wallet


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    with PostgresContainer("postgres:17-alpine") as postgres:
        db_url = postgres.get_connection_url().replace(
            "postgresql+psycopg2", "postgresql+asyncpg"
        )
        engine = create_async_engine(db_url, echo=False)

        def run_alembic_migrations(connection):
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.attributes["connection"] = connection
            command.upgrade(alembic_cfg, "head")

        async with engine.begin() as conn:
            await conn.run_sync(run_alembic_migrations)

        import app.database as database_module

        database_module.engine = engine
        database_module.new_session = async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        main_module.engine = engine

        yield engine

        await engine.dispose()
        database_module.engine = app_engine
        database_module.new_session = new_session
        main_module.engine = app_engine


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with factory() as session:
        yield session
    async with factory() as session:
        await session.execute(delete(Wallet))
        await session.commit()


@pytest_asyncio.fixture
async def client(db_engine):
    factory = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, class_=AsyncSession
    )

    async def _override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
