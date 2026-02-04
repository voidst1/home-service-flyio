import re
import httpx
from haversine import haversine, Unit


def validate_postal_code(value):
    if not re.match(r'^\d{6}$', value):
        raise ValidationError('Enter a valid SG postal code (6 digits)')


def get_postal_code_info(postal_code):
    # TODO: validate postal code

    api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMDg0NCwiZm9yZXZlciI6ZmFsc2UsImlzcyI6Ik9uZU1hcCIsImlhdCI6MTc3MDIxOTg2NSwibmJmIjoxNzcwMjE5ODY1LCJleHAiOjE3NzA0NzkwNjUsImp0aSI6ImY3NzJiYzE2LWJlNzgtNDcyNS1hYjE3LTM5NDM0M2MyZTY0MCJ9.Gy5kk-mnLicri9pRdphpdgX4-zlZDr5B2jWJac5bRtCdsL6F_YdrKf_Y6LlBjWYoN-03HXmd0ArQ66bW5yPzVMC99zb2lbravdxomDQsbTm3h_Od6fb5_mnlWRev4NxXzPp4K9nyJEwgcGZpa9fSedunQoFLN5PokRk7XuOBhifhKkR_mryAULTWnD6afZ-bOuKy3XAxjUT126RWX5AyIV-5MLz8Yv7zKBr0-NgLJao_kty83zYEGpML2rhZtLYXvrB3mQ9AGHMvHhp6i8b4vIpnqdeQztWM9NhIC18YopffNiL3kkpdk6V_TaF6JE1qB7rOp6VOXtcwjxv4kfPAng"

    # api_key = '1'
    headers = {"Authorization": api_key}
    url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=Y"

    r = httpx.get(url, headers=headers)

    # if r.status_code != 200:
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
