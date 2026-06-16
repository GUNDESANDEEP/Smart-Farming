"""
Admin AI Monitoring Routes
Handles: AI prediction logs, model performance, accuracy metrics
Path: /api/admin/ai-monitoring
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

import sys
sys.path.append('..')
from models.models import Admin, AILog

admin_monitoring_bp = Blueprint('admin_monitoring', __name__, url_prefix='/api/admin/ai-monitoring')

# ====================================================================
# 1. GET CROP PREDICTION LOGS
# ====================================================================
@admin_monitoring_bp.route('/crop-predictions', methods=['GET'])
@jwt_required()
def get_crop_predictions():
    """
    Get all crop prediction logs with accuracy metrics
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - farmer_id: Filter by farmer
    - status: success/error/warning
    
    Response:
    {
        "success": true,
        "predictions": [
            {
                "log_id": 1,
                "farmer_id": 12,
                "farmer_name": "Ravi Kumar",
                "crop_name": "Wheat",
                "confidence_score": 0.92,
                "status": "success",
                "execution_time": 234,
                "created_date": "2026-06-01T10:00:00"
            }
        ],
        "statistics": {
            "total_predictions": 1234,
            "accuracy_rate": 92.5,
            "avg_execution_time": 245
        }
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        farmer_id = request.args.get('farmer_id', type=int)
        status = request.args.get('status')
        
        ai_log = AILog()
        logs, total = ai_log.get_logs_paginated(
            log_type='crop_prediction',
            page=page,
            limit=limit,
            farmer_id=farmer_id,
            status=status
        )
        
        formatted_logs = []
        success_count = 0
        total_confidence = 0
        total_exec_time = 0
        
        for log in logs:
            formatted_logs.append({
                'log_id': log['log_id'],
                'farmer_id': log.get('farmer_id'),
                'farmer_name': log.get('farmer_name', ''),
                'crop_name': log.get('crop_name', 'Unknown'),
                'confidence_score': float(log.get('confidence_score', 0)),
                'status': log['status'],
                'execution_time': log.get('execution_time_ms', 0),
                'created_date': log['created_at'].isoformat() if log['created_at'] else None
            })
            
            if log['status'] == 'success':
                success_count += 1
                total_confidence += float(log.get('confidence_score', 0))
            total_exec_time += log.get('execution_time_ms', 0)
        
        accuracy_rate = (success_count / total * 100) if total > 0 else 0
        avg_confidence = (total_confidence / success_count) if success_count > 0 else 0
        avg_exec_time = (total_exec_time / len(logs)) if logs else 0
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'predictions': formatted_logs,
            'statistics': {
                'total_predictions': total,
                'success_rate': round(accuracy_rate, 2),
                'avg_confidence': round(avg_confidence, 3),
                'avg_execution_time': int(avg_exec_time)
            },
            'pagination': {
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_crop_predictions: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch crop predictions'}), 500


# ====================================================================
# 2. GET PRICE PREDICTION LOGS
# ====================================================================
@admin_monitoring_bp.route('/price-predictions', methods=['GET'])
@jwt_required()
def get_price_predictions():
    """
    Get all price prediction logs
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - product_id: Filter by product
    
    Response:
    {
        "success": true,
        "predictions": [
            {
                "log_id": 1,
                "product_id": 45,
                "product_name": "Organic Tomatoes",
                "predicted_price": 42.50,
                "actual_price": 45.00,
                "accuracy_percent": 94.4,
                "confidence_score": 0.89,
                "created_date": "2026-06-01T10:00:00"
            }
        ]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        product_id = request.args.get('product_id', type=int)
        
        ai_log = AILog()
        logs, total = ai_log.get_logs_paginated(
            log_type='price_prediction',
            page=page,
            limit=limit
        )
        
        formatted_logs = []
        accuracy_scores = []
        
        for log in logs:
            # Parse output data
            output_data = log.get('output_data', {})
            if isinstance(output_data, str):
                import json
                try:
                    output_data = json.loads(output_data)
                except:
                    output_data = {}
            
            predicted = output_data.get('predicted_price', 0)
            actual = output_data.get('actual_price', 0)
            accuracy = ((min(predicted, actual) / max(predicted, actual)) * 100) if max(predicted, actual) > 0 else 0
            
            formatted_logs.append({
                'log_id': log['log_id'],
                'product_id': log.get('product_id'),
                'product_name': log.get('product_name', 'Unknown'),
                'predicted_price': float(predicted),
                'actual_price': float(actual),
                'accuracy_percent': round(accuracy, 2),
                'confidence_score': float(log.get('confidence_score', 0)),
                'status': log['status'],
                'created_date': log['created_at'].isoformat() if log['created_at'] else None
            })
            
            accuracy_scores.append(accuracy)
        
        avg_accuracy = (sum(accuracy_scores) / len(accuracy_scores)) if accuracy_scores else 0
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'predictions': formatted_logs,
            'statistics': {
                'total_predictions': total,
                'average_accuracy': round(avg_accuracy, 2)
            },
            'pagination': {
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_price_predictions: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch price predictions'}), 500


# ====================================================================
# 3. GET DISEASE DETECTION LOGS
# ====================================================================
@admin_monitoring_bp.route('/disease-detection', methods=['GET'])
@jwt_required()
def get_disease_detection():
    """
    Get disease detection logs
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    - farmer_id: Filter by farmer
    
    Response:
    {
        "success": true,
        "detections": [
            {
                "log_id": 1,
                "farmer_id": 12,
                "crop": "Wheat",
                "disease_detected": "Powdery Mildew",
                "confidence": 0.87,
                "status": "success",
                "created_date": "2026-06-01T10:00:00"
            }
        ]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        farmer_id = request.args.get('farmer_id', type=int)
        
        ai_log = AILog()
        logs, total = ai_log.get_logs_paginated(
            log_type='disease_detection',
            page=page,
            limit=limit,
            farmer_id=farmer_id
        )
        
        formatted_logs = []
        for log in logs:
            output_data = log.get('output_data', {})
            if isinstance(output_data, str):
                import json
                try:
                    output_data = json.loads(output_data)
                except:
                    output_data = {}
            
            formatted_logs.append({
                'log_id': log['log_id'],
                'farmer_id': log.get('farmer_id'),
                'farmer_name': log.get('farmer_name', ''),
                'crop': log.get('crop_name', 'Unknown'),
                'disease_detected': output_data.get('disease', 'Unknown'),
                'confidence': float(log.get('confidence_score', 0)),
                'status': log['status'],
                'created_date': log['created_at'].isoformat() if log['created_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'detections': formatted_logs,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_disease_detection: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch disease detection logs'}), 500


# ====================================================================
# 4. GET FERTILIZER SUGGESTION LOGS
# ====================================================================
@admin_monitoring_bp.route('/fertilizer-suggestions', methods=['GET'])
@jwt_required()
def get_fertilizer_suggestions():
    """
    Get fertilizer suggestion logs
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Records per page (default: 20)
    
    Response:
    {
        "success": true,
        "suggestions": [
            {
                "log_id": 1,
                "farmer_id": 12,
                "crop": "Rice",
                "suggested_fertilizer": "NPK 16:16:16",
                "quantity": "50 kg/acre",
                "status": "success",
                "created_date": "2026-06-01T10:00:00"
            }
        ]
    }
    """
    try:
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=20)
        
        ai_log = AILog()
        logs, total = ai_log.get_logs_paginated(
            log_type='fertilizer_suggestion',
            page=page,
            limit=limit
        )
        
        formatted_logs = []
        for log in logs:
            output_data = log.get('output_data', {})
            if isinstance(output_data, str):
                import json
                try:
                    output_data = json.loads(output_data)
                except:
                    output_data = {}
            
            formatted_logs.append({
                'log_id': log['log_id'],
                'farmer_id': log.get('farmer_id'),
                'farmer_name': log.get('farmer_name', ''),
                'crop': log.get('crop_name', 'Unknown'),
                'suggested_fertilizer': output_data.get('fertilizer', 'Unknown'),
                'quantity': output_data.get('quantity', ''),
                'status': log['status'],
                'created_date': log['created_at'].isoformat() if log['created_at'] else None
            })
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'suggestions': formatted_logs,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': pages
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_fertilizer_suggestions: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch fertilizer suggestions'}), 500


# ====================================================================
# 5. GET AI SYSTEM STATISTICS
# ====================================================================
@admin_monitoring_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_ai_stats():
    """
    Get overall AI system statistics
    
    Response:
    {
        "success": true,
        "stats": {
            "total_predictions": 5678,
            "success_rate": 95.3,
            "error_rate": 1.2,
            "avg_execution_time": 245,
            "by_type": {
                "crop_predictions": 1234,
                "price_predictions": 2456,
                "disease_detections": 1500,
                "fertilizer_suggestions": 488
            },
            "performance": {
                "crop_prediction_accuracy": 92.5,
                "price_prediction_accuracy": 88.3,
                "disease_detection_accuracy": 94.7
            }
        }
    }
    """
    try:
        ai_log = AILog()
        
        # Get all predictions
        crop_preds = ai_log.count_logs_by_type('crop_prediction')
        price_preds = ai_log.count_logs_by_type('price_prediction')
        disease_detect = ai_log.count_logs_by_type('disease_detection')
        fertilizer_sugg = ai_log.count_logs_by_type('fertilizer_suggestion')
        
        total_preds = crop_preds + price_preds + disease_detect + fertilizer_sugg
        
        # Get success/error counts
        success_count = ai_log.count_logs_by_status('success')
        error_count = ai_log.count_logs_by_status('error')
        warning_count = ai_log.count_logs_by_status('warning')
        
        # Calculate rates
        success_rate = (success_count / total_preds * 100) if total_preds > 0 else 0
        error_rate = (error_count / total_preds * 100) if total_preds > 0 else 0
        warning_rate = (warning_count / total_preds * 100) if total_preds > 0 else 0
        
        # Get average execution time
        avg_exec_time = ai_log.get_avg_execution_time()
        
        # Get accuracy metrics
        crop_accuracy = ai_log.get_accuracy_metric('crop_prediction')
        price_accuracy = ai_log.get_accuracy_metric('price_prediction')
        disease_accuracy = ai_log.get_accuracy_metric('disease_detection')
        
        return jsonify({
            'success': True,
            'stats': {
                'total_predictions': total_preds,
                'success_rate': round(success_rate, 2),
                'error_rate': round(error_rate, 2),
                'warning_rate': round(warning_rate, 2),
                'avg_execution_time': int(avg_exec_time or 0),
                'by_type': {
                    'crop_predictions': crop_preds,
                    'price_predictions': price_preds,
                    'disease_detections': disease_detect,
                    'fertilizer_suggestions': fertilizer_sugg
                },
                'performance': {
                    'crop_prediction_accuracy': round(crop_accuracy or 0, 2),
                    'price_prediction_accuracy': round(price_accuracy or 0, 2),
                    'disease_detection_accuracy': round(disease_accuracy or 0, 2)
                }
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_ai_stats: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch AI statistics'}), 500


# ====================================================================
# 6. GET MODEL PERFORMANCE DETAILS
# ====================================================================
@admin_monitoring_bp.route('/models/performance', methods=['GET'])
@jwt_required()
def get_model_performance():
    """
    Get detailed model performance metrics
    
    Response:
    {
        "success": true,
        "models": [
            {
                "model_name": "Crop Prediction v2.1",
                "type": "crop_prediction",
                "version": "2.1",
                "total_predictions": 1234,
                "accuracy": 92.5,
                "avg_confidence": 0.87,
                "errors": 95,
                "warnings": 45,
                "last_updated": "2026-05-15T10:00:00"
            }
        ]
    }
    """
    try:
        ai_log = AILog()
        models = ai_log.get_model_performance_stats()
        
        formatted_models = []
        for model in models:
            formatted_models.append({
                'model_name': model.get('model_name', 'Unknown'),
                'type': model.get('type', ''),
                'version': model.get('version', '1.0'),
                'total_predictions': model.get('total_count', 0),
                'accuracy': round(model.get('accuracy', 0), 2),
                'avg_confidence': round(model.get('avg_confidence', 0), 3),
                'errors': model.get('error_count', 0),
                'warnings': model.get('warning_count', 0),
                'last_updated': model.get('last_updated', '')
            })
        
        return jsonify({
            'success': True,
            'models': formatted_models
        }), 200
        
    except Exception as e:
        print(f"Error in get_model_performance: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch model performance'}), 500


# ====================================================================
# 7. GET ERROR ANALYSIS
# ====================================================================
@admin_monitoring_bp.route('/errors', methods=['GET'])
@jwt_required()
def get_error_analysis():
    """
    Analyze AI system errors
    
    Response:
    {
        "success": true,
        "error_analysis": {
            "total_errors": 95,
            "by_type": {
                "crop_prediction": 23,
                "price_prediction": 45,
                "disease_detection": 17,
                "fertilizer_suggestions": 10
            },
            "common_errors": [
                {
                    "error_message": "Invalid input format",
                    "count": 34,
                    "percentage": 35.8
                }
            ]
        }
    }
    """
    try:
        ai_log = AILog()
        
        # Get errors by type
        errors_by_type = ai_log.get_errors_by_type()
        
        # Get common error messages
        common_errors = ai_log.get_common_error_messages(limit=10)
        
        total_errors = sum([e['count'] for e in common_errors])
        
        formatted_errors = []
        for error in common_errors:
            percentage = (error['count'] / total_errors * 100) if total_errors > 0 else 0
            formatted_errors.append({
                'error_message': error.get('error_message', 'Unknown'),
                'count': error['count'],
                'percentage': round(percentage, 2)
            })
        
        return jsonify({
            'success': True,
            'error_analysis': {
                'total_errors': total_errors,
                'by_type': errors_by_type,
                'common_errors': formatted_errors
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_error_analysis: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch error analysis'}), 500
