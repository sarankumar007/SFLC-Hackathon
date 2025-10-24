import random
from geopy.geocoders import Nominatim
import time

def get_district(lat, lon):
    geolocator = Nominatim(user_agent="geo_district_finder")
    location = geolocator.reverse((lat, lon), language='en')
    
    if location is None:
        return None

    address = location.raw.get('address', {})
    country = address.get('country')
    
    if country != 'India':
        return None

    # Prefer district, then county, then state
    district = address.get('district') or address.get('county') or address.get('state')
    return district

def random_coordinates_india():
    """
    Generate random coordinates within approximate bounding box of India
    """
    lat = random.uniform(6.0, 36.0)    # approx lat range of India
    lon = random.uniform(68.0, 97.0)   # approx lon range of India
    return lat, lon

def main():
    geolocator = Nominatim(user_agent="geo_district_finder")
    
    count = 0
    while count < 5:
        lat, lon = random_coordinates_india()
        district = get_district(lat, lon)
        if district:
            print(f"Coordinates: ({lat:.4f}, {lon:.4f}) -> District: {district}")
            count += 1
        else:
            # Skip coordinates that are invalid
            continue
        time.sleep(1)  # Respect Nominatim rate limit

if __name__ == "__main__":
    main()
