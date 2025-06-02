import haversine as hs
import logging

logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula."""
    try:
        coord1 = (float(lat1), float(lon1))
        coord2 = (float(lat2), float(lon2))
        return hs.haversine(coord1, coord2, unit=hs.Unit.KILOMETERS)
    except (ValueError, Exception) as e:
        logger.error(f"Error calculating distance: {e}")
        return float('inf')