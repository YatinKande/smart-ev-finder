from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from app.services.llm_service import LlmService
from app.services.ev_api_service import EvApiService
from app.models.schemas import BotResponse
from dotenv import load_dotenv
import os

# Load env variables
load_dotenv()

app = FastAPI(title="EV Charging Bot")

# Initialize Services
llm_service = LlmService()
ev_service = EvApiService()

class ChatRequest(BaseModel):
    message: str
    user_latitude: Optional[float] = None
    user_longitude: Optional[float] = None
    user_profile: Optional[dict] = None # Passing dict to avoid circular deps or complex imports for now

@app.post("/api/chat", response_model=BotResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Understand Intent
        search_params = llm_service.extract_search_params(
            query=request.message, 
            user_lat=request.user_latitude, 
            user_lon=request.user_longitude,
            user_profile=request.user_profile
        )
        
        # 2. Fetch Data
        stations = await ev_service.get_charging_stations(
            latitude=search_params.latitude,
            longitude=search_params.longitude,
            distance=search_params.distance,
            connection_type_id=search_params.connection_type_id,
            min_power_kw=search_params.min_power_kw,
            max_results=search_params.max_results
        )
        
        # 3. Generate Insight
        insight, new_profile = llm_service.generate_response(request.message, stations, request.user_profile)
        
        return BotResponse(
            llm_response=insight,
            stations=stations,
            original_query=request.message,
            new_user_profile_data=new_profile
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (Frontend)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("app/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
