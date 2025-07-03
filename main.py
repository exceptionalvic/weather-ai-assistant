from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import uuid

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WeatherResponse(BaseModel):
    temp: float
    description: str
    humidity: float
    wind: float
    city: str

class AIPrompt(BaseModel):
    prompt: str
    session_id: str = None

# Store session tokens (in production, use Redis or database)
sessions = {}

@app.get("/api/weather", response_model=WeatherResponse)
async def get_weather(city: str = Query(..., min_length=2)):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    # Clean the city name
    clean_city = ''.join(c for c in city if c.isalpha() or c.isspace()).strip()
    if not clean_city:
        raise HTTPException(status_code=400, detail="Invalid city name")
    
    try:
        async with httpx.AsyncClient() as client:
            # First try direct match
            response = await client.get(
                f"https://api.openweathermap.org/data/2.5/weather?q={clean_city}&appid={api_key}&units=metric"
            )
            
            # If not found, try with the first word only
            if response.status_code == 404:
                first_word = clean_city.split()[0]
                response = await client.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q={first_word}&appid={api_key}&units=metric"
                )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "temp": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind": data["wind"]["speed"],
                "city": data["name"]
            }
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=422,
            detail="Could not fetch weather data for that location. Please try a different city."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching weather data")

@app.post("/api/ai/chat")
async def chat_with_ai(prompt_data: AIPrompt):
    """
    Proxy for Puter.js AI with session management
    """
    try:
        # In a real app, you would use the session_id to maintain auth state
        # For demo, we'll just pass through to Puter.js
        
        # This would be replaced with actual Puter.js auth token
        # if we had backend access to their API
        prompt = prompt_data.prompt
        
        # Simulate Puter.js response
        return JSONResponse({
            "response": f"Mock AI response to: {prompt}",
            "session_id": prompt_data.session_id or str(uuid.uuid4())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)