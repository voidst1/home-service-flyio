import re
import httpx
from haversine import haversine, Unit


def validate_postal_code(value):
    if not re.match(r'^\d{6}$', value):
        raise ValidationError('Enter a valid SG postal code (6 digits)')


def get_postal_code_info(postal_code):
    # TODO: validate postal code

    api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMDg0NCwiZm9yZXZlciI6ZmFsc2UsImlzcyI6Ik9uZU1hcCIsImlhdCI6MTc3MDg4MTQzMiwibmJmIjoxNzcwODgxNDMyLCJleHAiOjE3NzExNDA2MzIsImp0aSI6IjRlYTBjYWNjLTk3MWEtNDYzYy1iZDI4LWNhOWQxNDAxMDY0MSJ9.3-w6UQqs7SW6Mlsot50p9wqVwITWtwf-9XwJLO9LtKa2GH8kCKoShEH8ysk9nutsdCax46y4qjJPCb7RgoZy05ZsAW4K5uvgO8SG-fL4bKWP3xbcfkYKoptiUERCVguPDLWi_0l6z75gTZ79f3C1sLzBV_smNu0I9GG4NlgeJzYmGNrlLlLpMSIIXT46kq3fB6gIiuaHzFyfZeIqsFYB3xI2CSN0NlaNOsRjLHFVJW6JRhGp4lgHx0A4PzxYKFKYkwCzZDrSfeG4TA6m9PKcE3CjSb940nOq8U115gXOX8PllWzJuOGDV0ut1u1TcmhAYsGeJQaXVPtGrK6HMqZP0A"

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
