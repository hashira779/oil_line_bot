import asyncio
import requests
import logging

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, station_data_url):
        self.stations = []
        self.station_data_url = station_data_url

    async def fetch_station_data(self):
        """Fetch station data from the configured URL."""
        try:
            response = await asyncio.to_thread(requests.get, self.station_data_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.stations = data.get("STATION", [])
            for station in self.stations:
                station["id"] = str(station.get("id", ""))
                station["latitude"] = str(station.get("latitude", ""))
                station["longitude"] = str(station.get("longitude", ""))
                station["service"] = station.get("service", []) or []
                station["other_product"] = station.get("other_product", []) or []
                station["description"] = station.get("description", []) or []
            logger.info(f"Successfully loaded {len(self.stations)} stations.")
            return self.stations
        except Exception as e:
            logger.error(f"Error fetching station data: {e}")
            return []