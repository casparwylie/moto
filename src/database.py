import os
from sqlalchemy import (
    create_engine,
    Table,
    MetaData,
    Column,
    ForeignKey,
    DateTime,
    Integer,
    String,
)

from sqlalchemy.engine.base import Engine


### CONNECTION ###

DB_URL = "mysql://{user}:{password}@{host}:{port}/{database}"


def _create_engine() -> Engine:
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASS")
    host = "mysql"
    port = "3306"
    database = os.environ.get("DB_NAME")

    url = DB_URL.format(
        user=db_user, password=db_password, host=host, port=port, database=database
    )
    return create_engine(
        url,
        connect_args={"auth_plugin": "mysql_native_password"},
        pool_pre_ping=True,
    )


engine = _create_engine()


##############
### TABLES ###
##############

metadata = MetaData()

racer_makes_table = Table(
    "racer_makes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50), index=True),
)


racer_models_table = Table(
    "racer_models",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(500), index=True),
    Column("style", String(100)),
    Column("make", Integer, ForeignKey(racer_makes_table.c.id), index=True),
    Column("year", Integer),
    Column("power", Integer),
    Column("torque", Integer),
    Column("weight", Integer),
    Column("weight_type", String(10)),
)


race_history_table = Table(
    "race_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("created_at", DateTime),
)


race_racers_table = Table(
    "race_racers",
    metadata,
    Column("race_id", Integer, ForeignKey(race_history_table.c.id)),
    Column("model_id", Integer, ForeignKey(racer_models_table.c.id)),
)


users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(100)),
    Column("email", String(500)),
    Column("password", String(500)),
)

user_sessions_table = Table(
    "user_sessions",
    metadata,
    Column("token", String(32)),
    Column("user_id", Integer, ForeignKey(users_table.c.id)),
    Column("expire", Integer),
)

user_garage_table = Table(
    "user_garage",
    metadata,
    Column("user_id", Integer, ForeignKey(users_table.c.id)),
    Column("model_id", Integer, ForeignKey(racer_models_table.c.id)),
    Column("relation", String(50)),
)
