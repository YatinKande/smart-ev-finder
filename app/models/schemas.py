from pydantic import BaseModel
from typing import Optional, List, Any, Dict

class SearchParams(BaseModel):
    latitude: float
    longitude: float
    distance: int = 20  # miles
    # Common connection types: 
    # 2: CHAdeMO, 32: CCS1, 33: CCS2, 1: J1772, 27: Tesla Supercharger, 30: Tesla Destination
    connection_type_id: Optional[int] = None 
    min_power_kw: Optional[float] = None
    max_results: int = 10

class UserProfile(BaseModel):
    name: Optional[str] = None
    preferences: Dict[str, Any] = {} # e.g., {"preferred_operator": "Tesla", "min_speed": 50}

class ChargerResponse(BaseModel):
    station_name: str
    distance_miles: Optional[float]
    address: Optional[str]
    usage_cost: Optional[str]
    status: Optional[str]
    power_kw: Optional[float]
    connection_type: Optional[str]
    latitude: float
    longitude: float
    maps_link: Optional[str] = None
    last_verified: Optional[str] = None # ISO date string or "Unknown"
    data_provider: Optional[str] = None
    confidence_score: Optional[float] = None # 0.0 to 1.0 based on data freshness

class BotResponse(BaseModel):
    llm_response: str
    stations: List[ChargerResponse]
    original_query: str
    new_user_profile_data: Optional[Dict[str, Any]] = None # Updates to user profile inferred by LLM
