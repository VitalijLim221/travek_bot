# bot/location_utils.py
from geopy.distance import geodesic
from bot.config import LOCATION_ACCURACY

def calculate_distance(lat1, lon1, lat2, lon2):
    "Calculate distance between two points in meters"
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    distance_km = geodesic(point1, point2).kilometers
    return distance_km * 1000  # Convert to meters

def is_location_match(user_lat, user_lon, target_lat, target_lon, accuracy=LOCATION_ACCURACY):
    """Check if user location matches target location within accuracy"""
    distance = calculate_distance(user_lat, user_lon, target_lat, target_lon)
    return distance <= accuracy