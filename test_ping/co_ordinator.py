import random
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.extra.rate_limiter import RateLimiter

# Initialize geolocator once
geolocator = Nominatim(user_agent="geo_district_finder")

# Wrap reverse with rate limiting and retries
geocode = RateLimiter(
    geolocator.reverse,
    min_delay_seconds=1,
    max_retries=3,
    error_wait_seconds=2.0
)

def get_district(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocode latitude and longitude globally, with rate limiting and error handling.
    """
    try:
        location = geocode((lat, lon), language='en')
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        print(f"⚠️ Geocoding error for ({lat}, {lon}): {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for ({lat}, {lon}): {e}")
        return None
    
    if not location:
        return None

    address = location.raw.get('address', {})
    # Extract typical location info (district/county/city/state)
    district = (address.get('district') or
                address.get('county') or
                address.get('city') or
                address.get('state_district') or
                address.get('state'))
    return district

def random_coordinates() -> tuple[float, float]:
    """Generate random global coordinates."""
    lat = random.uniform(-90, 90)
    lon = random.uniform(-180, 180)
    return lat, lon

def main():
    """Demonstrate reverse geocoding for various worldwide coords."""
    lat, lon = 35.674107, 139.653733
    print(f"Coordinates: ({lat}, {lon})")
    print("Location:", get_district(lat, lon))
    
    # Random global coordinate if needed
    lat, lon = random_coordinates()
    print(f"\nCoordinates: ({lat}, {lon})")
    print("Location:", get_district(lat, lon))

if __name__ == "__main__":
    main()

# lat, lon =  35.674107, 139.653733
