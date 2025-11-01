
import random
import time
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Initialize geolocator once (reuse across calls)
geolocator = Nominatim(user_agent="geo_district_finder")


def get_district(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocode latitude and longitude to get the district name in India.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
    
    Returns:
        str | None: District name if found and within India, else None.
    """
    try:
        location = geolocator.reverse((lat, lon), language='en')
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        print(f"⚠️ Geocoding error for ({lat}, {lon}): {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for ({lat}, {lon}): {e}")
        return None

    if not location:
        return None

    address = location.raw.get('address', {})
    if address.get('country') != 'India':
        return None

    # Extract district-level info (some states use different naming)
    district = (
        address.get('district')
        or address.get('county')
        or address.get('state_district')
        or address.get('state')
    )
    return district


def random_coordinates_india() -> tuple[float, float]:
    """
    Generate random coordinates within approximate bounding box of India.
    """
    lat = random.uniform(6.0, 36.0)
    lon = random.uniform(68.0, 97.0)
    return lat, lon


def main():
    """
    Test the district fetching logic by generating 5 random Indian coordinates.
    """
    print("=== 🗺️ Fetching random Indian districts ===\n")

    count = 0
    while count < 5:
        lat, lon = random_coordinates_india()
        district = get_district(lat, lon)
        if district:
            print(f"Coordinates: ({lat:.4f}, {lon:.4f}) -> District: {district}")
            count += 1
        time.sleep(1)  # Respect Nominatim rate limits

    print("\n✅ Done — 5 valid districts fetched.")


if __name__ == "__main__":
    main()
