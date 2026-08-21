import os
from collections.abc import Generator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://app:local-development-only@postgres:5432/performance_marketing_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["AUTH_MODE"] = "dev"

from app.db.session import engine  # noqa: E402

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def create_test_database() -> None:
    database_url = make_url(TEST_DATABASE_URL)
    database_name = database_url.database or ""
    if not database_name.endswith("_test"):
        raise RuntimeError("Integration tests require a database ending in '_test'")

    admin_url = database_url.set(drivername="postgresql", database="postgres")
    admin_dsn = admin_url.render_as_string(hide_password=False)
    with psycopg.connect(admin_dsn, autocommit=True) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (database_name,)
        ).fetchone()
        if exists is None:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Generator[None, None, None]:
    create_test_database()
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")

    alembic_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_config, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tenant_tables(migrated_database: None) -> Generator[None, None, None]:
    del migrated_database
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE competitors, brands, memberships, organizations, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield
