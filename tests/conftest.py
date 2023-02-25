import os
from typing import Generator

import pytest
import uvicorn
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine.base import Engine

from tests.dummy_data import TEST_DATA_MAKES, TEST_DATA_MODELS

MIGRATIONS_DIR = os.path.join(os.getcwd(), "migrations")
DB_NAME = os.environ.get("DB_NAME")

insert_racer_query = """
INSERT INTO racer_models
(name, make, style, year, power, torque, weight, weight_type)
VALUES
 (
  '{name}',
  {make},
  '{style}',
  {year},
  {power},
  {torque},
  {weight},
  '{weight_type}'
)
"""

insert_make_query = """
INSERT INTO racer_makes (name) VALUES ('{name}')
"""


def _create_engine() -> Engine:
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASS")
    url = f"mysql://{db_user}:{db_password}@mysql:3306"
    return create_engine(url, connect_args={"auth_plugin": "mysql_native_password"})


db_engine = _create_engine()


def get_migrations() -> Generator:
    for filepath in sorted(os.listdir(MIGRATIONS_DIR)):
        with open(os.path.join(MIGRATIONS_DIR, filepath), "r") as migration:
            yield migration.read()


@pytest.fixture(scope="session")
def db() -> Generator:
    with db_engine.connect() as conn:
        conn.execute(text(f"USE {DB_NAME}"))
        yield conn


def pytest_sessionstart(session: pytest.Session) -> None:
    with db_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME}"))
        conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
        conn.execute(text(f"USE {DB_NAME}"))
        for migration_query in get_migrations():
            conn.execute(text(migration_query))
        conn.commit()


@pytest.fixture(scope="session", autouse=True)
def store_racing_makes_models(db: Connection) -> Generator:
    for make in TEST_DATA_MAKES.values():
        db.execute(text(insert_make_query.format(name=make)))
    for model in TEST_DATA_MODELS.values():
        db.execute(text(insert_racer_query.format(**model)))
    db.commit()
    yield
    db.execute(text("DELETE FROM racer_models"))
    db.execute(text("DELETE FROM racer_makes"))
    db.commit()
