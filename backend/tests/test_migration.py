from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app.db.session import engine


def test_clean_database_is_at_alembic_head() -> None:
    expected_tables = {
        "api_usage",
        "brands",
        "competitors",
        "collection_sources",
        "credit_ledger",
        "creative_analyses",
        "creative_assets",
        "creatives",
        "jobs",
        "memberships",
        "organizations",
        "subscriptions",
        "users",
    }
    assert expected_tables.issubset(set(inspect(engine).get_table_names()))

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    with engine.connect() as connection:
        current_revision = MigrationContext.configure(connection).get_current_revision()

    assert current_revision == script.get_current_head() == "20260826_0008"
