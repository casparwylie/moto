import os
import sys
import requests
from sqlalchemy import text, create_engine
import enum

_MAKES_TRUTH = (
  'Honda',
  'Indian',
  'Yamaha',
  'Suzuki',
  'Royal Enfield',
  'Triumph',
  'Kawasaki',
  'KTM',
  'Aprilia',
  'BMW',
  'Ducati',
  'Harley-Davidson',
  'Enfield',
  'Benelli',
  'MV Agusta',
  'Moto Guzzi',
  'Norton',
  'Victory',
  'Keeway',
)

DB_URL = 'mysql://{user}:{password}@{host}:{port}/{database}'

M_API_KEY = 'QvIUv0aywoBXbuXNHAreHQ==t2wcm1EX72ciNWjV'
M_API_URL = 'https://api.api-ninjas.com/v1/motorcycles?&make={make}&offset={offset}'
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

def _create_engine():

  db_user = '2wheeluser'
  db_password = '2wheelpass'
  host = '108.61.173.62'
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


def get_scanned_makes_from_db(conn):
  return list(conn.execute(text(select_scanned_makes_query)))

class RacerStyles(str, enum.Enum):
  STREET = 'street'
  CROSS = 'cross'
  CLASSIC = 'classic'
  TOUR = 'tour',
  CRUISER = 'cruiser'
  SPORT = 'sport'
  ADVENTURE = 'adventure'
  RETRO = 'retro'

unknown_styles = set()

STYLE_MAP = {
  ('naked',): RacerStyles.STREET,
  ('cross', 'moto', 'motard', 'trial'): RacerStyles.CROSS,
  ('classic',): RacerStyles.CLASSIC,
  ('tour',): RacerStyles.TOUR,
  ('cruiser', 'chopper'): RacerStyles.CRUISER,
  ('sport',): RacerStyles.SPORT,
  ('enduro', 'offroad'): RacerStyles.ADVENTURE,
  ('custom', 'allround', 'unspecified'): RacerStyles.RETRO,
}

def get_style_from_api_type(given_type):
  global unknown_styles
  for terms, style in STYLE_MAP.items():
    for term in terms:
      if term.lower() in given_type.lower():
        return style.value
  unknown_styles.add(given_type)
  return RacerStyles.RETRO.value


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
    style=get_style_from_api_type(data.get('type').strip()),
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
      print('Total valid/saving: ', len(valid_models))
      sync_models(valid_models, conn)
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
      response = requests.get(
        M_API_URL.format(make=make_name, offset=offset),
        headers={'X-Api-Key': M_API_KEY},
      )
      if data := response.json():
        all_data += data
      result_length = len(data)
      offset += M_API_PAGE_LENGTH
      print(f'Scanned {offset}')
    return all_data


def clear_all(conn):
  conn.execute(text(delete_racers_query))


def add_make(name, conn):
  conn.execute(text(add_make_query.format(name=name)))


def factory_run():
  """Deletes all models and rescans them"""
  with _create_engine().connect() as conn:
    clear_all(conn)
    makes = get_makes_from_db(conn)
    run_sync(makes, conn)
    conn.commit()
    print('Unknown styles: ', unknown_styles)
    print('Done!')


def update_run():
  """Scans newly added makes"""
  with _create_engine().connect() as conn:
    makes = get_makes_from_db(conn)
    scanned = [make.make for make in get_scanned_makes_from_db(conn)]
    to_sync = [make for make in makes if make.id not in scanned]
    if to_sync:
      print('Scanning: ' + ', '.join(make.name for make in to_sync))
      run_sync(to_sync, conn)
      print('Unknown styles: ', unknown_styles)
      print('Done!')
      conn.commit()
    else:
      print('Nothing to sync.')


def sync_makes_run():
  with _create_engine().connect() as conn:
    make_names = [make.name for make in get_makes_from_db(conn)]
    to_add = [make for make in _MAKES_TRUTH if make not in make_names]
    if to_add:
      for name in to_add:
        print('Adding ' + name)
        add_make(name, conn)
      print('Done!')
      conn.commit()
    else:
      print('Nothing to add.')


def main():
  option = sys.argv[-1]
  match sys.argv[-1]:
    case 'factory':
      factory_run()
    case 'update':
      update_run()
    case 'sync-makes':
      sync_makes_run()
    case _:
      print('Unknown command.')

if __name__ == '__main__':
  main()
