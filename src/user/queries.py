from sqlalchemy import (
    Column,
    Delete,
    ForeignKey,
    Insert,
    Integer,
    MetaData,
    Select,
    String,
    Table,
    Update,
    delete,
    insert,
    literal_column,
    or_,
    select,
    text,
    update,
)

from src.database import (
    racer_makes_table,
    racer_models_table,
    user_garage_table,
    user_sessions_table,
    users_table,
)
from src.racing.queries import racer_makes_table, racer_models_table


def build_check_user_exists_query(username: str, email: str) -> Select:
    return select(users_table).where(
        or_(
            users_table.c.email == email,
            users_table.c.username == username,
        )
    )


def build_signup_query(username: str, password: str, email: str) -> Insert:
    return insert(users_table).values(
        username=username,
        password=password,
        email=email,
    )


def build_user_auth_query(username: str, password: str) -> Select:
    return select(users_table).where(
        users_table.c.password == password,
        users_table.c.username == username,
    )


def build_get_user_session_query(user_id: int) -> Select:
    return select(user_sessions_table).where(user_sessions_table.c.user_id == user_id)


def build_make_user_session_query(token: str, user_id: int, expire: int) -> Insert:
    return insert(user_sessions_table).values(
        token=token,
        user_id=user_id,
        expire=expire,
    )


def build_get_user_by_token_query(token: str) -> Select:
    return (
        select(users_table.c.id, users_table.c.username, users_table.c.email)
        .where(user_sessions_table.c.token == token)
        .join(users_table, user_sessions_table.c.user_id == users_table.c.id)
    )


def build_delete_session_query(token: str) -> Delete:
    return delete(user_sessions_table).where(user_sessions_table.c.token == token)


def build_add_user_garage_item_query(
    user_id: int, model_id: int, relation: str
) -> Insert:
    return insert(user_garage_table).values(
        user_id=user_id, model_id=model_id, relation=relation
    )


def build_get_model_id_query(make: str, model: str, year: int | None) -> Select:
    filters = [
        racer_models_table.c.name == model,
        literal_column("make_name") == make,
    ]
    if year:
        filters.append(racer_models_table.c.year == year)
    return (
        select(
            racer_models_table.columns,
            racer_makes_table.c.name.label("make_name"),
        )
        .having(*filters)
        .join(racer_makes_table, racer_makes_table.c.id == racer_models_table.c.make)
    )


def build_get_user_garage_query(user_id: int) -> Select:
    return (
        select(
            user_garage_table.c.relation,
            racer_models_table.c.name,
            racer_models_table.c.year,
            racer_models_table.c.id,
            racer_makes_table.c.name.label("make_name"),
        )
        .where(user_garage_table.c.user_id == user_id)
        .join(
            racer_models_table, user_garage_table.c.model_id == racer_models_table.c.id
        )
        .join(racer_makes_table, racer_models_table.c.make == racer_makes_table.c.id)
    )


def build_delete_user_garage_item_query(user_id: int, model_id: int) -> Delete:
    return delete(user_garage_table).where(
        user_garage_table.c.user_id == user_id,
        user_garage_table.c.model_id == model_id,
    )


def build_change_password_query(user_id: int, password: str) -> Update:
    return (
        update(users_table).where(users_table.c.id == user_id).values(password=password)
    )


def build_update_user_field_query(user_id: int, field: str, value: str) -> Update:
    return (
        update(users_table).where(users_table.c.id == user_id).values(**{field: value})
    )
