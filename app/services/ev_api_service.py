import httpx
import os
import datetime
from typing import List, Dict, Any, Optional
from app.models.schemas import ChargerResponse

STATUS_MAP = {
    0: "Unknown",
    10: "Available",
    20: "In Use",
    30: "Temp Unavailable",
    50: "Operational", 
    75: "Partly Operational",
    100: "Not Operational",
    150: "Planned",
    200: "Removed"
}

OPEN_CHARGE_MAP_API_URL = "https://api.openchargemap.io/v3/poi/"

class EvApiService:
    def __init__(self):
        self.api_key = os.getenv("OPEN_CHARGE_MAP_API_KEY")
        self.headers = {"User-Agent": "EV-Bot/1.0"}
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

    async def get_charging_stations(
        self, 
        latitude: float, 
        longitude: float, 
        distance: int = 20, 
        distance_unit: str = "Miles",
        max_results: int = 10,
        connection_type_id: Optional[int] = None,
        min_power_kw: Optional[float] = None
    ) -> List[ChargerResponse]:
        
        params = {
            "output": "json",
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance,
            "distanceunit": distance_unit,
            "maxresults": max_results,
            "compact": True,
            "verbose": False
        }

        if connection_type_id:
            params["connectiontypeid"] = connection_type_id
        
        if min_power_kw:
            params["minpowerkw"] = min_power_kw

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    OPEN_CHARGE_MAP_API_URL, 
                    params=params, 
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_stations(data)
            except Exception as e:
                print(f"Error fetching EV data: {e}")
                return []

    def _parse_stations(self, data: List[Dict[str, Any]]) -> List[ChargerResponse]:
        stations = []
        for item in data:
            try:
                address_info = item.get("AddressInfo", {})
                connections = item.get("Connections", [])
                
                # Find the most relevant connection data (e.g., max power)
                max_power = 0.0
                conn_type = "Unknown"
                
                if connections:
                    # simplistic: take the first one or the one with highest power
                    for conn in connections:
                        power = conn.get("PowerKW", 0) or 0
                        if power >= max_power:
                            max_power = power
                            if conn.get("ConnectionType"):
                                conn_type = conn["ConnectionType"].get("Title", "Unknown")

                status_type = item.get("StatusType")
                status_id = item.get("StatusTypeID")
                
                if status_type and "Title" in status_type:
                    status = status_type["Title"]
                elif status_id in STATUS_MAP:
                    status = STATUS_MAP[status_id]
                else:
                    status = "Unknown"
                
                usage_type = item.get("UsageType", {})
                cost = usage_type.get("Title", "Unknown") if usage_type else "Unknown"

                # Trust Signals
                date_last_status = item.get("DateLastStatusUpdate")
                data_provider_info = item.get("DataProvider", {})
                data_provider = data_provider_info.get("Title", "Unknown Provider")
                
                confidence_score = 0.5 # Default
                last_verified = "Unknown"
                
                if date_last_status:
                    try:
                        # Parse ISO format (e.g. 2023-01-01T12:00:00Z)
                        last_verified = date_last_status.split("T")[0] # Simple date extraction
                        
                        # Calculate confidence based on age
                        status_date = datetime.datetime.fromisoformat(date_last_status.replace("Z", "+00:00"))
                        now = datetime.datetime.now(datetime.timezone.utc)
                        days_old = (now - status_date).days
                        
                        if days_old < 30:
                            confidence_score = 1.0
                        elif days_old < 90:
                            confidence_score = 0.8
                        elif days_old < 180:
                            confidence_score = 0.5
                        else:
                            confidence_score = 0.2
                    except Exception:
                        pass

                lat = address_info.get("Latitude")
                lon = address_info.get("Longitude")
                
                # Construct Google Maps Link
                maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "#"

                stations.append(ChargerResponse(
                    station_name=address_info.get("Title", "Unknown Station"),
                    distance_miles=address_info.get("Distance"),
                    address=address_info.get("AddressLine1"),
                    usage_cost=cost,
                    status=status,
                    power_kw=max_power,
                    connection_type=conn_type,
                    latitude=lat,
                    longitude=lon,
                    maps_link=maps_link,
                    last_verified=last_verified,
                    data_provider=data_provider,
                    confidence_score=confidence_score
                ))
            except Exception as e:
                print(f"Error parsing station item: {e}")
                continue
                
        return stations
