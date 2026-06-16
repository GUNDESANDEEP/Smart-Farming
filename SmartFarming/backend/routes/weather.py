"""
Weather Routes - Real-time weather from OpenWeatherMap API
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import requests as http_requests
import os

weather_bp = Blueprint('weather', __name__, url_prefix='/api/weather')

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'e45520198f11734beae8ebfe007cf071')

@weather_bp.route('', methods=['GET'])
@jwt_required()
def get_weather():
    """Get weather for a city or coordinates"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        city = request.args.get('city', 'Hyderabad')
        
        if lat and lon:
            url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric'
        else:
            url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric'
        resp = http_requests.get(url, timeout=10)
        data = resp.json()
        
        if resp.status_code != 200:
            return jsonify({'error': data.get('message', 'Weather unavailable')}), resp.status_code
        
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
        
        return jsonify({'success': True, 'weather': weather}), 200
    except Exception as e:
        print(f'Weather error: {e}')
        return jsonify({'error': str(e)}), 500
