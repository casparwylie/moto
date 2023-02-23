from sqlalchemy import (
  Table,
  MetaData,
  Column,
  ForeignKey,
  Integer,
  String,
  select,
  insert,
  text,
  or_,
  delete,
)

metadata = MetaData()


### TABLES ###

users_table = Table(
  'users',
  metadata,
  Column('id', Integer, primary_key=True),
  Column('username', String(100)),
  Column('email', String(500)),
  Column('password', String(500)),
)

user_sessions_table = Table(
  'user_sessions',
  metadata,
  Column('token', String(32)),
  Column('user_id', Integer, ForeignKey(users_table.c.id)),
  Column('expire', Integer),
)

### QUERIES ###

def build_check_user_exists_query(username: str, email: str):
  return select(users_table).where(
    or_(
      users_table.c.email == email,
      users_table.c.username == username,
    )
  )


def build_signup_query(username: str, password: str, email: str):
  return insert(users_table).values(
    username=username,
    password=password,
    email=email,
  )


def build_user_auth_query(username: str, password: str):
  return select(users_table).where(
    users_table.c.password == password,
    users_table.c.username == username,
  )


def build_get_user_session_query(user_id: int):
  return select(user_sessions_table).where(
    user_sessions_table.c.user_id == user_id
  )


def build_make_user_session_query(
  token: str, user_id: int, expire: int
):
  return insert(user_sessions_table).values(
    token=token,
    user_id=user_id,
    expire=expire,
  )

def build_get_user_by_token_query(token: str):
  return select(
    users_table.c.username,
    users_table.c.email
  ).where(
    user_sessions_table.c.token == token
  ).join(
    users_table, user_sessions_table.c.user_id == users_table.c.id
  )

def build_delete_session_query(token: str):
  return delete(user_sessions_table).where(
    user_sessions_table.c.token == token
  )
