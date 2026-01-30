import re
from django.core.exceptions import ValidationError
import httpx

def does_profile_exist(user):
    return hasattr(user, 'customer_profile')

def validate_postal_code(value):
    if not re.match(r'^\d{6}$', value):
        raise ValidationError('Enter a valid SG postal code (6 digits)')

def get_postal_code_info(postal_code):
    # TODO: validate postal code

    api_key = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMDg0NCwiZm9yZXZlciI6ZmFsc2UsImlzcyI6Ik9uZU1hcCIsImlhdCI6MTc2OTYyMjE5NSwibmJmIjoxNzY5NjIyMTk1LCJleHAiOjE3Njk4ODEzOTUsImp0aSI6ImYyODExODE3LWJlZTQtNDgxMC1iMzNjLTFlNGUzMGYwMzc2OSJ9.ILQflmdMdNBd_Aeug_Y2GY1jVqL1u7gjngRmdpKmpFOm7TivuufVwkNUeFNY8G2gNLSc_auicu_V5EZamjNW878YHZ2DUGstR6-hJYR2zCQ6cmXRCqkqxGX4L5g4GaW7eZK7jtBOlu5bWeUxKMEDCXkS9CaVpBKGFXoiN-RqLMhW7V-5w0reUvNuNTsZ_s1Ag_t04VdTwf-fO1uJ8dEjQ4MALzsHQbSWnj8dFsxgUhBuOsejGCxZ5CLtSuVVp_uwotEuUZVrtKBjxDhhald-b5-RabZoG3Bss7DAoUKKsC0UWdrPpDBphdHWi5fI1Dt-DzxciCoNPY0qUntKKBdifA'
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

