import os
from sqlalchemy import (
  Table,
  MetaData,
  Column,
  ForeignKey,
  Index,
  Integer,
  String,
  create_engine,
  select,
)

### CONNECTION ###

DB_URL = 'mysql://{user}:{password}@{host}:{port}/{database}'

def _create_engine():
  db_user = os.environ.get('DB_USER')
  db_password = os.environ.get('DB_PASS')
  host = 'mysql'
  port = '3306'
  database = os.environ.get('DB_NAME')

  url = DB_URL.format(
    user=db_user, password=db_password, host=host, port=port, database=database
  )
  return create_engine(url, connect_args={'auth_plugin': 'mysql_native_password'})

engine = _create_engine()

### TABLES ###

metadata = MetaData()

racer_makes_table = Table(
    'racer_makes',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50), index=True),
)

racer_models_table = Table(
    'racer_models',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(500), index=True),
    Column('style', String(100)),
    Column('make', Integer, ForeignKey(racer_makes_table.c.id), index=True),
    Column('year', Integer),
    Column('power', Integer),
    Column('torque', Integer),
    Column('weight', Integer),
    Column('weight_type', String(10)),
)

### QUERIES ###

def build_search_racer_query(make: int, model: str):
  return select(
    racer_models_table.columns
  ).where(
    racer_models_table.c.name.contains(model),
    racer_models_table.c.make == make
  )


def build_get_racer_by_make_model_query(make: int, model: str):
  return select(
    racer_models_table.columns
  ).where(racer_models_table.c.name == model, racer_models_table.c.make == make)


def build_get_make_by_name_query(make_name: str):
  return select(racer_makes_table.columns).where(
    racer_makes_table.c.name.contains(make_name)
  )

