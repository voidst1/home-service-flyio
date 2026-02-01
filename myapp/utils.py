import re
from django.core.exceptions import ValidationError
import httpx

from haversine import haversine, Unit

def does_profile_exist(user):
    return hasattr(user, 'customer_profile')

def validate_postal_code(value):
    if not re.match(r'^\d{6}$', value):
        raise ValidationError('Enter a valid SG postal code (6 digits)')

def get_postal_code_info(postal_code):
    # TODO: validate postal code

    api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMDg0NCwiZm9yZXZlciI6ZmFsc2UsImlzcyI6Ik9uZU1hcCIsImlhdCI6MTc2OTkzODg0OCwibmJmIjoxNzY5OTM4ODQ4LCJleHAiOjE3NzAxOTgwNDgsImp0aSI6IjJmMzU4MWM0LWIwMDktNDBiOS1iZjBmLTJkNWQ5YjU5YTZiOSJ9.wfLg5IEVFsMbTvHBKKtetNIJGNIXuXJuCXsgS4aQoI3sLklvxv5A0-fNHbJxzZdDd-s7Fn2ZisvXGVBLYHVf9N_p8TkFr2HNkiDh4dPmFEWkvqAfpKCKffsF0YU1T9-NN_tfVuhig6jzgeLtzk1RnojlvnQpBFX6UDOlGS1UBTJ0sr43Psjgy0maWb8Aqqq8tqHPwOBeWfPI46CZRF2ed0SHdU9Oga2hc2Sff2OF_oUc4TdYAbHB7kVF18nHG9YmiDBKuEV1Eu3dT9mbLgSIr6J2GA8dfDOxBQ6ct-WmFFHM2qBjiqOaevtBRKOCElYkDsmUIOAHdD11VRoK0EtEdA"

    #api_key = '1'
    headers = {"Authorization": api_key }
    url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=Y"

    r = httpx.get(url, headers=headers)

    #if r.status_code != 200:
    #  print(r.status_code)
    #  return None

    o = r.json()
    if 'error' in o:
      print(o['error'])
      return o['error']

    return o

# in float
def get_distance_km(lat1, long1, lat2, long2):
    return haversine((lat1, long1), (lat2, long2), unit=Unit.KILOMETERS)
