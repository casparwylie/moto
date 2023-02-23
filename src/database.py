import os
from sqlalchemy import create_engine

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
  return create_engine(
    url,
    connect_args={'auth_plugin': 'mysql_native_password'},
    pool_pre_ping=True,
  )

engine = _create_engine()

