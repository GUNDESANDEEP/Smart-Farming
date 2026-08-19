"""
AI Features Routes - Crop Recommendations, Price Predictions, Disease Detection
Uses Scikit-learn Models
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Farmer
import json

def get_matrix_recommendations(season, soil_type):
    s = (season or "monsoon").lower()
    st = (soil_type or "loam").lower()
    
    matrix = {
        ("monsoon", "black"): [
            {"rank": 1, "crop": "Cotton", "confidence": 0.96, "profitability": "high", "growing_period_days": 160, "water_requirement": "medium", "tips": ["Apply NPK 120:60:60", "Monitor for pink bollworm pest", "Maintain 90x60 cm row spacing"]},
            {"rank": 2, "crop": "Soybean", "confidence": 0.91, "profitability": "high", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Inoculate seeds with Rhizobium culture", "45 cm row spacing", "Watch for yellow mosaic virus"]},
            {"rank": 3, "crop": "Groundnut (Peanut)", "confidence": 0.85, "profitability": "medium", "growing_period_days": 105, "water_requirement": "low-medium", "tips": ["Apply Gypsum at pegging stage", "Avoid standing water in fields"]}
        ],
        ("monsoon", "sandy"): [
            {"rank": 1, "crop": "Pearl Millet (Bajra)", "confidence": 0.94, "profitability": "medium", "growing_period_days": 85, "water_requirement": "low", "tips": ["Highly drought-resistant crop", "Apply NPK 80:40:0", "Maintain 45x15 cm spacing"]},
            {"rank": 2, "crop": "Cluster Bean (Guar)", "confidence": 0.89, "profitability": "high", "growing_period_days": 90, "water_requirement": "low", "tips": ["Natural nitrogen-fixing crop", "High industrial gum market demand", "Requires minimal synthetic fertilizer"]},
            {"rank": 3, "crop": "Sesame (Til)", "confidence": 0.84, "profitability": "high", "growing_period_days": 80, "water_requirement": "very low", "tips": ["Avoid waterlogging in sandy soil", "Thin seedlings at 15 days", "Harvest when bottom capsules turn yellow"]}
        ],
        ("monsoon", "clay"): [
            {"rank": 1, "crop": "Paddy (Rice)", "confidence": 0.97, "profitability": "high", "growing_period_days": 120, "water_requirement": "high", "tips": ["Clay soil retains water exceptionally well", "Maintain 5-8 cm standing water", "Apply NPK 120:60:40 in 3 split doses"]},
            {"rank": 2, "crop": "Sugarcane", "confidence": 0.90, "profitability": "high", "growing_period_days": 330, "water_requirement": "high", "tips": ["Deep trench planting method", "Trash mulching for soil moisture retention"]},
            {"rank": 3, "crop": "Jute / Hemp", "confidence": 0.83, "profitability": "medium", "growing_period_days": 120, "water_requirement": "high", "tips": ["Thrives in warm, humid clay soils", "Retting water availability is crucial"]}
        ],
        ("monsoon", "red"): [
            {"rank": 1, "crop": "Groundnut (Peanut)", "confidence": 0.93, "profitability": "high", "growing_period_days": 105, "water_requirement": "medium", "tips": ["Well-drained red soil promotes pod formation", "Apply Gypsum @ 400 kg/ha at 45 days"]},
            {"rank": 2, "crop": "Finger Millet (Ragi)", "confidence": 0.90, "profitability": "high", "growing_period_days": 100, "water_requirement": "low-medium", "tips": ["Rich in calcium and iron", "Tolerates semi-arid red soil stress"]},
            {"rank": 3, "crop": "Maize (Corn)", "confidence": 0.85, "profitability": "medium", "growing_period_days": 105, "water_requirement": "medium", "tips": ["Add organic compost to boost red soil organic carbon"]}
        ],
        ("winter", "loam"): [
            {"rank": 1, "crop": "Wheat", "confidence": 0.96, "profitability": "high", "growing_period_days": 135, "water_requirement": "medium", "tips": ["Irrigate at Crown Root Initiation stage (21 days)", "Apply NPK 120:60:40"]},
            {"rank": 2, "crop": "Mustard / Rapeseed", "confidence": 0.92, "profitability": "high", "growing_period_days": 110, "water_requirement": "low-medium", "tips": ["Sulfur application boosts seed oil content by 15%", "Thin plants to 10-15 cm spacing"]},
            {"rank": 3, "crop": "Chickpea (Gram / Chana)", "confidence": 0.88, "profitability": "high", "growing_period_days": 110, "water_requirement": "low", "tips": ["Nipping top buds at 35 days increases branching and pods"]}
        ],
        ("winter", "black"): [
            {"rank": 1, "crop": "Chickpea (Gram / Chana)", "confidence": 0.95, "profitability": "high", "growing_period_days": 115, "water_requirement": "low", "tips": ["Thrives on deep residual moisture of black soil", "Avoid over-irrigation"]},
            {"rank": 2, "crop": "Wheat (Durum / Sharbati)", "confidence": 0.90, "profitability": "high", "growing_period_days": 130, "water_requirement": "medium", "tips": ["Apply Zinc Sulfate @ 25 kg/ha at sowing"]},
            {"rank": 3, "crop": "Safflower (Kusum)", "confidence": 0.86, "profitability": "medium", "growing_period_days": 120, "water_requirement": "low", "tips": ["Deep root system extracts moisture from subsoil", "Drought tolerant oilseed crop"]}
        ],
        ("winter", "sandy"): [
            {"rank": 1, "crop": "Barley", "confidence": 0.93, "profitability": "medium", "growing_period_days": 100, "water_requirement": "low", "tips": ["Tolerates sandy soil and salinity", "Lower water needs than wheat"]},
            {"rank": 2, "crop": "Mustard", "confidence": 0.89, "profitability": "high", "growing_period_days": 105, "water_requirement": "low", "tips": ["Drip irrigation with fertigation gives optimal yields"]},
            {"rank": 3, "crop": "Cumin (Jeera) / Coriander", "confidence": 0.84, "profitability": "high", "growing_period_days": 110, "water_requirement": "low", "tips": ["Requires cool dry climate, avoid excessive dampness"]}
        ],
        ("winter", "red"): [
            {"rank": 1, "crop": "Potato", "confidence": 0.94, "profitability": "high", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Friable red soil permits free tuber expansion", "Earthing up at 30 days"]},
            {"rank": 2, "crop": "Mustard", "confidence": 0.89, "profitability": "high", "growing_period_days": 110, "water_requirement": "low-medium", "tips": ["Apply Boron @ 10 kg/ha for better pod development"]},
            {"rank": 3, "crop": "Sunflower", "confidence": 0.84, "profitability": "medium", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Ensure honeybee activity or manual pollination during flowering"]}
        ],
        ("summer", "sandy"): [
            {"rank": 1, "crop": "Watermelon / Muskmelon", "confidence": 0.96, "profitability": "high", "growing_period_days": 85, "water_requirement": "medium", "tips": ["Sandy soil warms quickly, accelerating vine growth", "Use plastic mulching & drip irrigation"]},
            {"rank": 2, "crop": "Cucumber / Gourd", "confidence": 0.91, "profitability": "high", "growing_period_days": 65, "water_requirement": "medium", "tips": ["Trellis staking keeps fruits clean and prevents soil rot"]},
            {"rank": 3, "crop": "Cowpea / Green Gram (Moong)", "confidence": 0.87, "profitability": "medium", "growing_period_days": 65, "water_requirement": "low", "tips": ["Short duration summer pulse crop", "Improves soil fertility for Kharif"]}
        ],
        ("summer", "black"): [
            {"rank": 1, "crop": "Green Gram (Moong Dal)", "confidence": 0.94, "profitability": "high", "growing_period_days": 65, "water_requirement": "low", "tips": ["Ideal catch crop between Rabi and Kharif", "Requires minimal irrigation"]},
            {"rank": 2, "crop": "Sesame (Til)", "confidence": 0.89, "profitability": "high", "growing_period_days": 75, "water_requirement": "low", "tips": ["Highly heat tolerant", "Strong summer market prices"]},
            {"rank": 3, "crop": "Sunflower", "confidence": 0.85, "profitability": "medium", "growing_period_days": 85, "water_requirement": "medium", "tips": ["High solar radiation boosts seed oil content"]}
        ]
    }
    
    key = (s, st)
    if key in matrix:
        return matrix[key]
    
    if s == "winter":
        return [
            {"rank": 1, "crop": "Wheat", "confidence": 0.95, "profitability": "high", "growing_period_days": 135, "water_requirement": "medium", "tips": ["Crown Root Initiation irrigation at 21 days", "Apply NPK 120:60:40"]},
            {"rank": 2, "crop": "Mustard", "confidence": 0.90, "profitability": "high", "growing_period_days": 110, "water_requirement": "low-medium", "tips": ["Apply sulfur for higher oil yield", "Thin seedlings to 10-15 cm"]},
            {"rank": 3, "crop": "Chickpea (Chana)", "confidence": 0.86, "profitability": "high", "growing_period_days": 110, "water_requirement": "low", "tips": ["Nipping terminal shoots increases branching"]}
        ]
    elif s == "summer":
        return [
            {"rank": 1, "crop": "Watermelon / Muskmelon", "confidence": 0.95, "profitability": "high", "growing_period_days": 85, "water_requirement": "medium", "tips": ["Use drip irrigation", "High summer market demand"]},
            {"rank": 2, "crop": "Green Gram (Moong)", "confidence": 0.90, "profitability": "medium", "growing_period_days": 65, "water_requirement": "low", "tips": ["Short duration 60-day crop", "Fixes soil nitrogen"]},
            {"rank": 3, "crop": "Okra (Bhindi)", "confidence": 0.85, "profitability": "high", "growing_period_days": 75, "water_requirement": "medium", "tips": ["Harvest every 2 days for continuous yield"]}
        ]
    else:
        return [
            {"rank": 1, "crop": "Paddy (Rice)", "confidence": 0.94, "profitability": "high", "growing_period_days": 120, "water_requirement": "high", "tips": ["Use quality certified seeds", "Maintain water level of 5-8 cm", "Apply NPK 60:40:40 in 3 splits"]},
            {"rank": 2, "crop": "Maize (Corn)", "confidence": 0.88, "profitability": "medium", "growing_period_days": 110, "water_requirement": "medium", "tips": ["Space 60cm between rows", "Apply NPK 120:60:40", "Monitor for fall armyworm"]},
            {"rank": 3, "crop": "Soybean", "confidence": 0.82, "profitability": "high", "growing_period_days": 95, "water_requirement": "medium", "tips": ["Apply Rhizobium culture", "Spacing: 45cm rows", "Watch for yellow mosaic virus"]}
        ]

# ==================== CROP RECOMMENDATION ====================
@ai_bp.route('/crop-recommendation', methods=['GET'])
@jwt_required()
def get_crop_recommendation():
    """
    Get AI-based crop recommendations
    
    Query: ?season=monsoon&soil_type=loam
    
    Response: {
        "success": true,
        "recommendations": [
            {
                "rank": 1,
                "crop": "Rice",
                "confidence": 0.94,
                "avg_price": 4500,
                "expected_yield": 50,
                "growing_period": 120,
                "water_requirement": "high",
                "soil_type": "loam",
                "season": "monsoon",
                "planting_date": "2026-06-15",
                "harvest_date": "2026-10-15",
                "tips": [
                    "Use quality seeds",
                    "Maintain water level",
                    "Monitor for pests"
                ]
            }
        ]
    }
    """
    try:
        farmer_id = get_jwt_identity()
        farmer = Farmer.get_farmer_by_id(farmer_id)
        
        season = request.args.get('season', 'monsoon')
        soil_type = request.args.get('soil_type', 'loam')
        
        recommendations = get_matrix_recommendations(season, soil_type)
        
        return {
            'success': True,
            'location': farmer['location'] if farmer else 'Unknown',
            'season': season,
            'soil_type': soil_type,
            'model_version': '1.0',
            'recommendations': recommendations
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== PRICE PREDICTION ====================
@ai_bp.route('/price-prediction/<int:product_id>', methods=['GET'])
@jwt_required()
def get_price_prediction(product_id):
    """
    Predict future price for a product
    
    Response: {
        "success": true,
        "product": "Tomato",
        "current_price": 45,
        "prediction": {
            "next_week_min": 40,
            "next_week_max": 48,
            "next_week_avg": 44,
            "next_month_min": 35,
            "next_month_max": 55,
            "next_month_avg": 45,
            "confidence": 0.78,
            "factors": [
                "supply_decrease: 80%",
                "festival_demand: 90%",
                "weather_impact: 60%"
            ],
            "recommendation": "Price may increase in next week. Consider holding inventory."
        }
    }
    """
    try:
        farmer_id = get_jwt_identity()
        
        # TODO: Implement price prediction model
        # 1. Get historical price data for product
        # 2. Get seasonal factors, supply/demand
        # 3. Use Linear Regression or Time Series models
        # 4. Return future price ranges and confidence
        
        prediction = {
            'product': 'Tomato',
            'current_price': 45,
            'unit': 'per kg',
            'market': 'Hyderabad APMC',
            'predictions': {
                'next_7_days': {
                    'min': 40,
                    'max': 48,
                    'average': 44,
                    'confidence': 0.78
                },
                'next_30_days': {
                    'min': 35,
                    'max': 55,
                    'average': 45,
                    'confidence': 0.72
                },
                'next_90_days': {
                    'min': 32,
                    'max': 58,
                    'average': 46,
                    'confidence': 0.65
                }
            },
            'factors': [
                {'factor': 'Supply Level', 'impact': -10, 'description': 'Lower supply expected'},
                {'factor': 'Festival Demand', 'impact': 15, 'description': 'Upcoming festival demand'},
                {'factor': 'Weather', 'impact': 5, 'description': 'Moderate impact from monsoon'},
                {'factor': 'Market Trend', 'impact': -3, 'description': 'Slight downward trend'}
            ],
            'recommendation': 'Price expected to rise next week due to lower supply. Consider timing your sale strategically.',
            'best_selling_period': 'Next 2 weeks',
            'model_version': '1.0'
        }
        
        return {
            'success': True,
            'prediction': prediction
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== FERTILIZER SUGGESTION ====================
@ai_bp.route('/fertilizer-suggestion', methods=['GET'])
@jwt_required()
def get_fertilizer_suggestion():
    """
    Get fertilizer recommendations based on crop and soil
    
    Query: ?crop=tomato&soil_npk=10:5:5&land_area=2.5
    
    Response: {
        "success": true,
        "suggestions": [
            {
                "stage": "pre_planting",
                "fertilizer": "FYM/Compost",
                "quantity": 25,
                "unit": "tons",
                "timing": "2 weeks before planting",
                "application_method": "Mix in soil"
            }
        ]
    }
    """
    try:
        farmer_id = get_jwt_identity()
        crop = request.args.get('crop', 'tomato')
        land_area = float(request.args.get('land_area', 1.0))
        
        # TODO: Implement fertilizer recommendation model
        # 1. Get crop nutrient requirements
        # 2. Test soil NPK levels (if available)
        # 3. Recommend balanced fertilizer
        # 4. Calculate quantity based on land area
        
        suggestions = [
            {
                'stage': 'pre_planting',
                'name': 'Farmyard Manure / Compost',
                'quantity': 25 * land_area,
                'unit': 'tons',
                'timing': '2 weeks before planting',
                'application_method': 'Mix thoroughly in soil',
                'cost_estimate': 5000 * land_area
            },
            {
                'stage': 'planting',
                'name': 'NPK 19:19:19',
                'quantity': 500 * land_area,
                'unit': 'kg',
                'timing': 'At the time of planting',
                'application_method': 'As basal dressing',
                'cost_estimate': 8000 * land_area
            },
            {
                'stage': 'growth',
                'name': 'Urea (for N)',
                'quantity': 250 * land_area,
                'unit': 'kg',
                'timing': '6 weeks after planting',
                'application_method': 'Side dressing / Through irrigation',
                'cost_estimate': 4000 * land_area
            },
            {
                'stage': 'flowering',
                'name': 'Potash / MOP (for K)',
                'quantity': 150 * land_area,
                'unit': 'kg',
                'timing': '10-12 weeks after planting',
                'application_method': 'Side dressing',
                'cost_estimate': 3000 * land_area
            }
        ]
        
        return {
            'success': True,
            'crop': crop.title(),
            'land_area': land_area,
            'total_estimated_cost': sum([s['cost_estimate'] for s in suggestions]),
            'suggestions': suggestions
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== DISEASE DETECTION ====================
@ai_bp.route('/disease-detection', methods=['POST'])
@jwt_required()
def detect_disease():
    """
    Detect plant disease from image (using CNN - TensorFlow/Keras)
    [Future Feature - Phase 2]
    
    Request: FormData with image
    
    Response: {
        "success": true,
        "disease": "Early Blight",
        "confidence": 0.92,
        "description": "...",
        "treatment": [...]
    }
    """
    try:
        farmer_id = get_jwt_identity()
        
        # TODO: Implement disease detection using CNN
        # 1. Receive image from farmer
        # 2. Preprocess image
        # 3. Use trained TensorFlow model
        # 4. Return disease name, confidence, and treatment
        
        return {
            'success': True,
            'message': 'Disease detection coming soon in Phase 2'
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

# ==================== GET ALL AI PREDICTIONS ====================
@ai_bp.route('/predictions', methods=['GET'])
@jwt_required()
def get_all_predictions():
    """
    Get all AI predictions history for farmer
    
    Query: ?type=crop_recommendation&limit=10
    """
    try:
        farmer_id = get_jwt_identity()
        pred_type = request.args.get('type')
        limit = request.args.get('limit', 10, type=int)
        
        # TODO: Fetch from AI_predictions table
        
        return {
            'success': True,
            'predictions': []
        }, 200
    
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
