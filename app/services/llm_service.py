import os
import json
from groq import Groq
from app.models.schemas import SearchParams, ChargerResponse
from typing import List, Optional

class LlmService:
    def __init__(self):
        msg = "GROQ_API_KEY environment variable is not set."
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print(f"Warning: {msg}")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile" # Using the large model for better reasoning

    def extract_search_params(self, query: str, user_lat: Optional[float] = None, user_lon: Optional[float] = None, user_profile: Optional[dict] = None) -> SearchParams:
        """
        Uses LLM to extract location coordinates and filters from natural language.
        If user_lat/lon are provided, prioritize them as the search center unless specific city mentioned.
        Injects user preferences if available.
        """
        context_str = ""
        if user_lat and user_lon:
            context_str += f"User's Current Location: Latitude {user_lat}, Longitude {user_lon}. Use this as the center if the query implies 'near me' or doesn't specify a city.\n"
        
        if user_profile:
            name = user_profile.get("name", "User")
            prefs = user_profile.get("preferences", {})
            context_str += f"User Profile: Name: {name}. Preferences: {prefs}.\n"

        system_prompt = f"""
        You are an EV assistant. Extract search parameters from the user's query.
        {context_str}
        
        If the user's preferences imply specific filters (e.g. "I only drive Tesla"), apply them automatically unless the query overrides them.
        
        Return a valid JSON object with:
        - latitude (float): inferred from the location mentioned OR the User's Current Location.
        - longitude (float): inferred from the location mentioned OR the User's Current Location.
        - distance (int): search radius in miles (default 20)
        - connection_type_id (int, optional): 
            - 2 for CHAdeMO
            - 32 or 33 for CCS
            - 1 for J1772
            - 27 for Tesla Supercharger
            - 30 for Tesla Destination
        - min_power_kw (float, optional): e.g., 50 for DC Fast, 150 for Ultrafast.
        - max_results (int): default 10
        
        IMPORTANT: 
        1. If the user says "near me" and you have User's Current Location, use it.
        2. If the user mentions a specific city (e.g., "Chicago"), prioritize that city over current location.
        3. If NO location is found, return 0.0 for lat/lon (the app will handle this).
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            data = json.loads(content)
            
            # Simple fallback if LLM returns 0.0 but we have user location
            if (data.get("latitude") == 0 or data.get("latitude") is None) and user_lat:
                data["latitude"] = user_lat
                data["longitude"] = user_lon
                
            return SearchParams(**data)
        except Exception as e:
            print(f"Error extracting params: {e}")
            # Fallback to user location if available, else raise/empty
            if user_lat and user_lon:
                return SearchParams(latitude=user_lat, longitude=user_lon)
            # Last resort fallback (better than crashing, but maybe we should tell user)
            return SearchParams(latitude=42.3314, longitude=-83.0458) # Default to Detroit/Dearborn area since user is there? Or just neutral.

    def generate_response(self, query: str, stations: List[ChargerResponse], user_profile: Optional[dict] = None) -> (str, Optional[dict]):
        """
        Summarizes the finding for the user and updates user profile if new info is learned.
        Returns: (response_text, new_profile_data)
        """
        profile_context = ""
        if user_profile:
            profile_context = f"User: {user_profile.get('name', 'Unknown')}. Preferences: {user_profile.get('preferences', {})}"

        system_prompt = f"""
        You are a smart EV assistant. 
        1. Analyze the charger data and answer the user's question.
        2. EXPLAIN WHY you chose these stations (e.g., "This matches your preference for Fast Charging").
        3. Check if the user mentioned their name or a new preference (e.g., "I drive a Bolt"). 
        
        {profile_context}

        Return a JSON object:
        {{
            "response_text": "The actual helpful response...",
            "new_profile_data": {{ "name": "...", "preferences": {{ "key": "value" }} }} (or null if nothing new)
        }}
        """
        
        stations_str = "\n".join([str(s.model_dump()) for s in stations])
        user_content = f"User Query: {query}\n\nSearch Results:\n{stations_str}"

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            content = completion.choices[0].message.content
            data = json.loads(content)
            return data.get("response_text", "Here are the stations found."), data.get("new_profile_data")
        except Exception as e:
            return f"I found {len(stations)} stations, but couldn't generate a summary due to an error: {e}", None
