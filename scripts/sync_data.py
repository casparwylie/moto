import os
import requests
from sqlalchemy import text, create_engine


DB_URL = 'mysql://{user}:{password}@{host}:{port}/{database}'

M_API_KEY = 'QvIUv0aywoBXbuXNHAreHQ==t2wcm1EX72ciNWjV'
M_API_URL = 'https://api.api-ninjas.com/v1/motorcycles?&make={make}&offset={offset}'
M_API_PAGE_LENGTH = 30

insert_racer_query = """
INSERT INTO racer_models (name, make, year, power, torque, weight, weight_type)
VALUES ('{name}', {make}, {year}, {power}, {torque}, {weight}, '{weight_type}')
"""

select_makes_query = """
SELECT * FROM racer_makes
"""

delete_racers_query = """
TRUNCATE TABLE racer_models
"""

def _create_engine():

  db_user = 'user'
  db_password = 'password'
  host = '0.0.0.0'
  port = '3306'
  database = 'moto'

  url = DB_URL.format(
    user=db_user, password=db_password, host=host, port=port, database=database
  )
  return create_engine(url)


def find_number_by_metric(value: str, metric: str) -> int:
  if value:
    return int(float(value[0:value.lower().find(metric.lower())].strip()))

def get_makes_from_db(conn):
  return list(conn.execute(text(select_makes_query)))

def prepare_model(data, make_id):
  weight = None
  weight_type = None
  if weight := data.get('total_weight'):
    weight_type = 'total'
  elif weight := data.get('wet_weight'):
    weight_type = 'wet'
  elif weight := data.get('dry_weight'):
    weight_type = 'dry'
  weight = find_number_by_metric(weight, 'kg')
  make = data.get('make').strip()
  model = data.get('model').strip()
  return dict(
    name=model,
    make=make_id,
    year=data.get('year').strip(),
    power=find_number_by_metric(data.get('power'), 'hp'),
    torque=find_number_by_metric(data.get('torque'), 'nm'),
    weight=weight,
    weight_type=weight_type,
  )

def run_sync(makes, conn):
  for make in makes:
    print(f'\n\nFetching models for {make.name}...')
    models_data = get_models_by_make_api(make.name)
    if models_data:
      models = [prepare_model(model, make.id) for model in models_data]
      print('Total scanned: ', len(models_data))
      valid_models = [model for model in models if all(model.values())]
      print('Total valid/saving: ', len(models_data))
      sync_models(models, conn)
    else:
      print('Failed to find model! Skipping...')

def sync_models(models, conn):
  for model in models:
    query = insert_racer_query.format(**model)
    conn.execute(text(query))

def get_models_by_make_api(make_name):
    all_data = []
    result_length = M_API_PAGE_LENGTH
    offset = 0
    while result_length:
      print(f'Scanned {offset}')
      response = requests.get(
        M_API_URL.format(make=make_name, offset=offset),
        headers={'X-Api-Key': M_API_KEY},
      )
      if data := response.json():
        all_data += data
      result_length = len(data)
      offset += M_API_PAGE_LENGTH
    return all_data

def clear_all(conn):
  conn.execute(text(delete_racers_query))

def main():
  with _create_engine().connect() as conn:
    clear_all(conn)
    makes = get_makes_from_db(conn)
    makes_names = ', '.join(make.name for make in makes)
    print('Curent makes: ' + makes_names)
    run_sync(makes, conn)
    print('Done!')
    conn.commit()

if __name__ == '__main__':
  main()
