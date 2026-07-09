"""
Weather Routes - Real-time weather from OpenWeatherMap API
FastAPI version.
"""

from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
import requests as http_requests
import os
from utils.jwt_utils import get_current_user

weather_router = APIRouter(prefix='/api/weather', tags=['Weather'])

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'e45520198f11734beae8ebfe007cf071')

@weather_router.get('')
async def get_weather(
    lat: str = Query(None),
    lon: str = Query(None),
    city: str = Query('Hyderabad'),
    location: str = Query(None),
    user_id: str = Depends(get_current_user)
):
    """Get weather for a city or coordinates"""
    try:
        search_city = location or city or 'Hyderabad'
        if lat and lon:
            url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric'
        else:
            url = f'https://api.openweathermap.org/data/2.5/weather?q={search_city}&appid={WEATHER_API_KEY}&units=metric'
        resp = http_requests.get(url, timeout=10)
        data = resp.json()
        
        if resp.status_code != 200:
            return JSONResponse(
                status_code=resp.status_code,
                content={'error': data.get('message', 'Weather unavailable')}
            )
        
        weather = {
            'city': data.get('name', city),
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'humidity': data['main']['humidity'],
            'wind_speed': round(data['wind']['speed'] * 3.6, 1),  # m/s to km/h
            'description': data['weather'][0]['description'].title(),
            'icon': data['weather'][0]['icon'],
            'main': data['weather'][0]['main'],
            'temp_min': round(data['main']['temp_min']),
            'temp_max': round(data['main']['temp_max']),
        }
        
        return {'success': True, 'weather': weather}
    except Exception as e:
        print(f'Weather error: {e}')
        return JSONResponse(status_code=500, content={'error': str(e)})
