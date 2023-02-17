import os

import pytest
from sqlalchemy import create_engine, text
import uvicorn
MIGRATIONS_DIR = os.path.join(os.getcwd(), 'migrations')
DB_NAME = os.environ.get('DB_NAME')


def _create_engine():
  db_user = os.environ.get('DB_USER')
  db_password = os.environ.get('DB_PASS')
  url = f'mysql://{db_user}:{db_password}@mysql:3306'
  return create_engine(url, connect_args={'auth_plugin': 'mysql_native_password'})

db_engine = _create_engine()

def get_migrations():
  for filepath in sorted(os.listdir(MIGRATIONS_DIR)):
    with open(os.path.join(MIGRATIONS_DIR, filepath), 'r') as migration:
      yield migration.read()


@pytest.fixture(scope='session')
def db():
  with db_engine.connect() as conn:
    conn.execute(text(f'USE {DB_NAME}'))
    yield conn


def pytest_sessionstart(session):
  with db_engine.connect() as conn:
    conn.execute(text(f'DROP DATABASE IF EXISTS {DB_NAME}'))
    conn.execute(text(f'CREATE DATABASE {DB_NAME}'))
    conn.execute(text(f'USE {DB_NAME}'))
    for migration_query in get_migrations():
      conn.execute(text(migration_query))
    conn.commit()

