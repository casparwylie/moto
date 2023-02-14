from sqlalchemy import (
  Table,
  MetaData,
  Column,
  ForeignKey,
  Index,
  Integer,
  DateTime,
  String,
  select,
  insert,
)

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


race_history_table = Table(
  'race_history',
  metadata,
  Column('id', Integer, primary_key=True),
  Column('created_at', DateTime),
)


race_racers_table = Table(
  'race_racers',
  metadata,
  Column('race_id', Integer, ForeignKey(race_history_table.c.id)),
  Column('model_id', Integer, ForeignKey(racer_models_table.c.id)),
)


### QUERIES ###

def build_search_racer_query(make: int, model: str):
  return select(
    racer_models_table.columns
  ).where(
    racer_models_table.c.name.contains(model),
    racer_models_table.c.make == make
  )


def build_get_race_query(race_id: int):
  return select(
    racer_models_table,
    racer_makes_table.c.name.label('make_name'),
  ).where(race_racers_table.c.race_id == race_id
  ).join(
    race_racers_table, race_racers_table.c.model_id == racer_models_table.c.id).join(
    racer_makes_table, racer_makes_table.c.id == racer_models_table.c.make,
  )


def build_get_racer_by_make_model_query(make: int, model: str):
  return select(
    racer_models_table.columns
  ).where(racer_models_table.c.name == model, racer_models_table.c.make == make)


def build_get_make_by_name_query(make_name: str):
  return select(racer_makes_table.columns).where(
    racer_makes_table.c.name.contains(make_name)
  )


def build_insert_race_query():
  return insert(race_history_table)


def build_insert_race_racers_query(race_id: int, model_ids: list[int]):
  return insert(race_racers_table).values([
    dict(race_id=race_id, model_id=model_id)
    for model_id in model_ids
  ])
