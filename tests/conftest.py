import asyncio
import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from testcontainers.postgres import PostgresContainer

from app.main import app
from app.database import get_db

@pytest.fixture(scope="session")
def event_loop():
    """Создает один экземпляр цикла событий на всю сессию тестов."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# 1. Запускаем базу один раз на все тесты
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

# @pytest.fixture(scope="session")
# async def db_engine():
#     # 1. Запускаем временный Docker-контейнер с Postgres
#     with PostgresContainer("postgres:17-alpine") as postgres:
#         # Формируем асинхронный URL (testcontainers выдает psycopg2 по умолчанию)
#         db_url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        
#         # 2. Создаем асинхронный движок для тестов
#         engine = create_async_engine(db_url, echo=False)

#         # 3. Накатываем миграции Alembic на этот контейнер
#         # Мы создаем конфиг программно, указывая путь к твоему alembic.ini
#         alembic_cfg = Config("alembic.ini")
#         # Подменяем sqlalchemy.url в конфиге на URL нашего контейнера
#         alembic_cfg.set_main_option("sqlalchemy.url", db_url + "?async_fallback=True")
        
#         # Запускаем миграции
#         command.upgrade(alembic_cfg, "head")
        
#         yield engine
#         await engine.dispose()
@pytest.fixture(scope="session")
async def db_engine():
    with PostgresContainer("postgres:16-alpine") as postgres:
        db_url = postgres.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        engine = create_async_engine(db_url, echo=False)

        # Эта функция — "мостик" для Alembic
        def run_alembic_migrations(connection):
            alembic_cfg = Config("alembic.ini")
            # Передаем наше живое соединение в атрибуты конфига
            alembic_cfg.attributes["connection"] = connection
            command.upgrade(alembic_cfg, "head")

        # Запускаем миграции внутри асинхронного соединения
        async with engine.begin() as conn:
            await conn.run_sync(run_alembic_migrations)
        
        yield engine
        await engine.dispose()


# 2. Создаем сессию для каждого теста
@pytest.fixture
async def db_session(db_engine):
    async with db_engine.connect() as connection:
        transaction = await connection.begin()
        
        async_session_factory = async_sessionmaker(
            bind=connection, 
            expire_on_commit=False, 
            class_=AsyncSession
        )
        session = async_session_factory()

        yield session

        await session.close()
        await transaction.rollback() # Чистим данные после теста


# 3. Наш "клиент-робот"
@pytest.fixture
async def client(db_session):
    # Dependency Override: подменяем реальную БД на тестовую сессию
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()