import enum
import os
import sys
from typing import cast

import requests
from sqlalchemy import Connection, Row, create_engine, text
from sqlalchemy.engine.base import Engine

_MAKES_TRUTH = (
    "Honda",
    "Indian",
    "Yamaha",
    "Suzuki",
    "Triumph",
    "Kawasaki",
    "KTM",
    "Aprilia",
    "BMW",
    "Ducati",
    "Harley-Davidson",
    "Enfield",
    "Benelli",
    "MV Agusta",
    "Moto Guzzi",
    "Norton",
    "Victory",
    "Keeway",
    "CCM",
)

DB_URL = "mysql://{user}:{password}@{host}:{port}/{database}"
M_API_KEY = os.environ.get("MOTO_API_KEY")
M_API_URL = "https://api.api-ninjas.com/v1/motorcycles?&make={make}&offset={offset}"
M_API_PAGE_LENGTH = 30

insert_racer_query = """
INSERT INTO racer_models (name, make, style, year, power, torque, weight, weight_type)
VALUES ('{name}', {make}, '{style}', {year}, {power}, {torque}, {weight}, '{weight_type}')
"""

select_makes_query = """
SELECT * FROM racer_makes
"""

select_scanned_makes_query = """
SELECT DISTINCT make FROM racer_models;
"""

delete_racers_query = """
TRUNCATE TABLE racer_models;
"""

add_make_query = """
INSERT INTO racer_makes (name) VALUES ('{name}')
"""


class Env:
    db_user: str
    db_password: str
    host: str
    port: str
    database: str


class LocalDb(Env):
    db_user = "user"
    db_password = "password"
    host = "127.0.0.1"
    port = "3307"
    database = "moto"


class ProdDb(Env):
    db_user = os.environ.get("MOTO_DB_USER_PROD", "")
    db_password = os.environ.get("MOTO_DB_PASS_PROD", "")
    host = "108.61.173.62"
    port = "3307"
    database = "moto"


def _create_engine(env: Env) -> Engine:
    url = DB_URL.format(
        user=env.db_user,
        password=env.db_password,
        host=env.host,
        port=env.port,
        database=env.database,
    )
    return create_engine(url)


def get_env() -> Env:
    match sys.argv[-2]:
        case "production":
            return cast(Env, ProdDb)
        case _:
            return cast(Env, LocalDb)


engine = _create_engine(get_env())


def find_number_by_metric(value: str, metric: str) -> int | None:
    if value:
        return int(float(value[0 : value.lower().find(metric.lower())].strip()))


def get_makes_from_db(conn: Connection) -> list[Row]:
    return list(conn.execute(text(select_makes_query)))


def get_scanned_makes_from_db(conn: Connection) -> list[Row]:
    return list(conn.execute(text(select_scanned_makes_query)))


class RacerStyles(str, enum.Enum):
    STREET = "street"
    CROSS = "cross"
    CLASSIC = "classic"
    TOUR = ("tour",)
    CRUISER = "cruiser"
    SPORT = "sport"
    ADVENTURE = "adventure"
    RETRO = "retro"


unknown_styles = set()

STYLE_MAP = {
    ("naked",): RacerStyles.STREET,
    ("cross", "moto", "motard", "trial"): RacerStyles.CROSS,
    ("classic",): RacerStyles.CLASSIC,
    ("tour",): RacerStyles.TOUR,
    ("cruiser", "chopper"): RacerStyles.CRUISER,
    ("sport",): RacerStyles.SPORT,
    ("enduro", "offroad"): RacerStyles.ADVENTURE,
    ("custom", "allround", "unspecified"): RacerStyles.RETRO,
}


def get_style_from_api_type(given_type: str) -> str:
    global unknown_styles
    for terms, style in STYLE_MAP.items():
        for term in terms:
            if term.lower() in given_type.lower():
                return cast(str, style.value)
    unknown_styles.add(given_type)
    return RacerStyles.RETRO.value


def prepare_model(data: dict, make_id: int) -> dict:
    weight = None
    weight_type = None
    if weight := data.get("total_weight"):
        weight_type = "total"
    elif weight := data.get("wet_weight"):
        weight_type = "wet"
    elif weight := data.get("dry_weight"):
        weight_type = "dry"
    weight = find_number_by_metric(weight, "kg")
    model = data.get("model", "").strip()
    return dict(
        name=model,
        make=make_id,
        style=get_style_from_api_type(data.get("type", "").strip()),
        year=data.get("year", "").strip(),
        power=find_number_by_metric(data.get("power", ""), "hp"),
        torque=find_number_by_metric(data.get("torque", ""), "nm"),
        weight=weight,
        weight_type=weight_type,
    )


def run_sync(makes: list[Row], conn: Connection) -> None:
    for make in makes:
        print(f"\n\nFetching models for {make.name}...")
        models_data = get_models_by_make_api(make.name)
        if models_data:
            models = [prepare_model(model, make.id) for model in models_data]
            print("Total scanned: ", len(models_data))
            valid_models = [model for model in models if all(model.values())]
            print("Total valid/saving: ", len(valid_models))
            sync_models(valid_models, conn)
        else:
            print("Failed to find model! Skipping...")


def sync_models(models: list[Row], conn: Connection) -> None:
    for model in models:
        query = insert_racer_query.format(**model)
        conn.execute(text(query))


def get_models_by_make_api(make_name: str) -> list[dict]:
    all_data = []
    result_length = M_API_PAGE_LENGTH
    offset = 0
    while result_length:
        response = requests.get(
            M_API_URL.format(make=make_name, offset=offset),
            headers={"X-Api-Key": M_API_KEY},
        )
        if data := response.json():
            all_data += data
        result_length = len(data)
        offset += M_API_PAGE_LENGTH
        print(f"Scanned {offset}")
    return all_data


def clear_all(conn: Connection) -> None:
    conn.execute(text(delete_racers_query))


def add_make(name: str, conn: Connection) -> None:
    conn.execute(text(add_make_query.format(name=name)))


def factory_run() -> None:
    """Deletes all models and rescans them"""
    with engine.connect() as conn:
        clear_all(conn)
        makes = get_makes_from_db(conn)
        run_sync(makes, conn)
        conn.commit()
        print("Unknown styles: ", unknown_styles)
        print("Done!")


def update_run() -> None:
    """Scans newly added makes"""
    with engine.connect() as conn:
        makes = get_makes_from_db(conn)
        scanned = [make.make for make in get_scanned_makes_from_db(conn)]
        to_sync = [make for make in makes if make.id not in scanned]
        if to_sync:
            print("Scanning: " + ", ".join(make.name for make in to_sync))
            run_sync(to_sync, conn)
            print("Unknown styles: ", unknown_styles)
            print("Done!")
            conn.commit()
        else:
            print("Nothing to sync.")


def sync_makes_run() -> None:
    with engine.connect() as conn:
        make_names = [make.name for make in get_makes_from_db(conn)]
        to_add = [make for make in _MAKES_TRUTH if make not in make_names]
        if to_add:
            for name in to_add:
                print("Adding " + name)
                add_make(name, conn)
            print("Done!")
            conn.commit()
        else:
            print("Nothing to add.")


def main() -> None:
    sys.argv[-1]
    match sys.argv[-1]:
        case "factory":
            factory_run()
        case "update":
            update_run()
        case "sync-makes":
            sync_makes_run()
        case _:
            print("Unknown command.")


if __name__ == "__main__":
    main()
