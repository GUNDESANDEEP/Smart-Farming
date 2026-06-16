"""
Buyer Reviews & Ratings Routes
Handles: Submit reviews, Get reviews, Edit/Delete reviews
Path: /api/reviews
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

import sys
sys.path.append('..')
from models.models import BuyerReview, Order

buyer_reviews_bp = Blueprint('buyer_reviews', __name__, url_prefix='/api/reviews')

# ====================================================================
# 1. SUBMIT REVIEW - Post review after order delivery
# ====================================================================
@buyer_reviews_bp.route('/<int:order_id>', methods=['POST'])
@jwt_required()
def submit_review(order_id):
    """
    Submit product and farmer review for completed order
    
    Request:
    {
        "product_rating": 5,
        "product_review": "Great quality tomatoes!",
        "farmer_rating": 4,
        "farmer_review": "Good farmer, delivered on time"
    }
    
    Response:
    {
        "success": true,
        "review_id": 1,
        "message": "Review submitted successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        product_rating = data.get('product_rating')
        product_review = data.get('product_review', '')
        farmer_rating = data.get('farmer_rating')
        farmer_review = data.get('farmer_review', '')
        
        # Validate ratings
        if not all([1 <= product_rating <= 5, 1 <= farmer_rating <= 5]):
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
        
        # Verify order
        order_obj = Order()
        order = order_obj.get_order_by_id(order_id)
        
        if not order or order['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Check if order is delivered
        if order['status'] != 'delivered':
            return jsonify({'success': False, 'error': 'Can only review delivered orders'}), 400
        
        # Check if already reviewed
        review_obj = BuyerReview()
        existing_review = review_obj.get_review_by_order(order_id)
        
        if existing_review:
            return jsonify({'success': False, 'error': 'Order already reviewed'}), 409
        
        # Create review
        review_id = review_obj.create_review(
            order_id=order_id,
            buyer_id=buyer_id,
            product_id=order['product_id'],
            farmer_id=order['farmer_id'],
            product_rating=product_rating,
            product_review=product_review,
            farmer_rating=farmer_rating,
            farmer_review=farmer_review
        )
        
        if not review_id:
            return jsonify({'success': False, 'error': 'Failed to submit review'}), 500
        
        # Update product and farmer ratings (aggregate)
        # TODO: Recalculate average ratings
        
        return jsonify({
            'success': True,
            'review_id': review_id,
            'message': 'Review submitted successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in submit_review: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to submit review'}), 500


# ====================================================================
# 2. GET PRODUCT REVIEWS - Get all reviews for a product
# ====================================================================
@buyer_reviews_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    """
    Get all reviews for a product
    
    Query Parameters:
    - sort: Sort order (recent, helpful, highest, lowest)
    - page: Page number
    - limit: Items per page
    
    Response:
    {
        "success": true,
        "product_id": 1,
        "average_rating": 4.5,
        "total_reviews": 120,
        "rating_breakdown": {
            "5": 60,
            "4": 40,
            "3": 15,
            "2": 4,
            "1": 1
        },
        "reviews": [
            {
                "review_id": 1,
                "buyer_name": "Rajesh",
                "rating": 5,
                "review": "Great quality!",
                "helpful_count": 25,
                "created_at": "2026-06-01"
            }
        ]
    }
    """
    try:
        sort = request.args.get('sort', 'recent')
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=10)
        
        review_obj = BuyerReview()
        reviews = review_obj.get_product_reviews(product_id, sort, page, limit)
        
        if not reviews:
            return jsonify({
                'success': True,
                'product_id': product_id,
                'reviews': [],
                'average_rating': 0,
                'total_reviews': 0
            }), 200
        
        # Calculate statistics
        total_reviews = review_obj.count_product_reviews(product_id)
        avg_rating = review_obj.get_product_average_rating(product_id)
        rating_breakdown = review_obj.get_rating_breakdown(product_id)
        
        formatted_reviews = []
        for review in reviews:
            formatted_reviews.append({
                'review_id': review['review_id'],
                'buyer_name': review.get('buyer_name', 'Anonymous'),
                'rating': review['product_rating'],
                'review': review['product_review'],
                'helpful_count': review.get('helpful_count', 0),
                'created_at': review['created_at'].strftime('%Y-%m-%d') if review['created_at'] else None
            })
        
        pages = (total_reviews + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'product_id': product_id,
            'average_rating': float(avg_rating) if avg_rating else 0,
            'total_reviews': total_reviews,
            'rating_breakdown': rating_breakdown,
            'reviews': formatted_reviews,
            'page': page,
            'pages': pages
        }), 200
        
    except Exception as e:
        print(f"Error in get_product_reviews: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch reviews'}), 500


# ====================================================================
# 3. GET FARMER REVIEWS - Get all reviews for a farmer
# ====================================================================
@buyer_reviews_bp.route('/farmer/<int:farmer_id>', methods=['GET'])
def get_farmer_reviews(farmer_id):
    """
    Get all reviews for a farmer
    
    Query Parameters:
    - sort: Sort order
    - page: Page number
    - limit: Items per page
    
    Response:
    {
        "success": true,
        "farmer_id": 1,
        "farmer_name": "Ravi Kumar",
        "average_rating": 4.6,
        "total_reviews": 250,
        "reviews": [...]
    }
    """
    try:
        sort = request.args.get('sort', 'recent')
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=10)
        
        review_obj = BuyerReview()
        reviews = review_obj.get_farmer_reviews(farmer_id, sort, page, limit)
        
        if not reviews:
            return jsonify({
                'success': True,
                'farmer_id': farmer_id,
                'reviews': [],
                'average_rating': 0,
                'total_reviews': 0
            }), 200
        
        # Calculate statistics
        total_reviews = review_obj.count_farmer_reviews(farmer_id)
        avg_rating = review_obj.get_farmer_average_rating(farmer_id)
        
        formatted_reviews = []
        for review in reviews:
            formatted_reviews.append({
                'review_id': review['review_id'],
                'buyer_name': review.get('buyer_name', 'Anonymous'),
                'rating': review['farmer_rating'],
                'review': review['farmer_review'],
                'product_name': review.get('product_name', 'Product'),
                'created_at': review['created_at'].strftime('%Y-%m-%d') if review['created_at'] else None
            })
        
        pages = (total_reviews + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'farmer_id': farmer_id,
            'farmer_name': reviews[0].get('farmer_name', '') if reviews else '',
            'average_rating': float(avg_rating) if avg_rating else 0,
            'total_reviews': total_reviews,
            'reviews': formatted_reviews,
            'page': page,
            'pages': pages
        }), 200
        
    except Exception as e:
        print(f"Error in get_farmer_reviews: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch reviews'}), 500


# ====================================================================
# 4. UPDATE REVIEW - Edit review
# ====================================================================
@buyer_reviews_bp.route('/<int:review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    """
    Update existing review (within 7 days of posting)
    
    Request:
    {
        "product_rating": 4,
        "product_review": "Updated review"
    }
    
    Response:
    {
        "success": true,
        "message": "Review updated successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        data = request.get_json()
        
        review_obj = BuyerReview()
        review = review_obj.get_review_by_id(review_id)
        
        if not review or review['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Review not found'}), 404
        
        # Check if review is editable (within 7 days)
        days_old = (datetime.now() - review['created_at']).days
        if days_old > 7:
            return jsonify({'success': False, 'error': 'Review can only be edited within 7 days'}), 400
        
        # Update review
        success = review_obj.update_review(
            review_id=review_id,
            product_rating=data.get('product_rating', review['product_rating']),
            product_review=data.get('product_review', review['product_review']),
            farmer_rating=data.get('farmer_rating', review['farmer_rating']),
            farmer_review=data.get('farmer_review', review['farmer_review'])
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update review'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Review updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in update_review: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update review'}), 500


# ====================================================================
# 5. DELETE REVIEW
# ====================================================================
@buyer_reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """
    Delete own review
    
    Response:
    {
        "success": true,
        "message": "Review deleted successfully"
    }
    """
    try:
        buyer_id = get_jwt_identity()
        
        review_obj = BuyerReview()
        review = review_obj.get_review_by_id(review_id)
        
        if not review or review['buyer_id'] != buyer_id:
            return jsonify({'success': False, 'error': 'Review not found'}), 404
        
        # Delete review
        success = review_obj.delete_review(review_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete review'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Review deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_review: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete review'}), 500


# ====================================================================
# 6. GET BUYER'S REVIEWS - All reviews posted by buyer
# ====================================================================
@buyer_reviews_bp.route('/my-reviews', methods=['GET'])
@jwt_required()
def get_my_reviews():
    """
    Get all reviews posted by the buyer
    
    Response:
    {
        "success": true,
        "reviews": [
            {
                "review_id": 1,
                "order_id": 101,
                "product_name": "Organic Tomatoes",
                "farmer_name": "Ravi Kumar",
                "product_rating": 5,
                "farmer_rating": 4,
                "created_at": "2026-06-01"
            }
        ]
    }
    """
    try:
        buyer_id = get_jwt_identity()
        page = request.args.get('page', type=int, default=1)
        limit = request.args.get('limit', type=int, default=10)
        
        review_obj = BuyerReview()
        reviews = review_obj.get_buyer_reviews(buyer_id, page, limit)
        
        formatted_reviews = []
        for review in reviews:
            formatted_reviews.append({
                'review_id': review['review_id'],
                'order_id': review['order_id'],
                'product_id': review['product_id'],
                'product_name': review.get('product_name', ''),
                'farmer_id': review['farmer_id'],
                'farmer_name': review.get('farmer_name', ''),
                'product_rating': review['product_rating'],
                'product_review': review['product_review'],
                'farmer_rating': review['farmer_rating'],
                'farmer_review': review['farmer_review'],
                'created_at': review['created_at'].strftime('%Y-%m-%d') if review['created_at'] else None
            })
        
        total = review_obj.count_buyer_reviews(buyer_id)
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'reviews': formatted_reviews,
            'total': total,
            'page': page,
            'pages': pages
        }), 200
        
    except Exception as e:
        print(f"Error in get_my_reviews: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch reviews'}), 500


# ====================================================================
# 7. MARK REVIEW HELPFUL
# ====================================================================
@buyer_reviews_bp.route('/<int:review_id>/helpful', methods=['POST'])
def mark_helpful(review_id):
    """
    Mark review as helpful (upvote)
    
    Response:
    {
        "success": true,
        "helpful_count": 26
    }
    """
    try:
        review_obj = BuyerReview()
        review = review_obj.get_review_by_id(review_id)
        
        if not review:
            return jsonify({'success': False, 'error': 'Review not found'}), 404
        
        # Increment helpful count
        helpful_count = review_obj.mark_helpful(review_id)
        
        return jsonify({
            'success': True,
            'helpful_count': helpful_count
        }), 200
        
    except Exception as e:
        print(f"Error in mark_helpful: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to mark review helpful'}), 500


# ====================================================================
# 8. REPORT REVIEW - Report inappropriate review
# ====================================================================
@buyer_reviews_bp.route('/<int:review_id>/report', methods=['POST'])
@jwt_required()
def report_review(review_id):
    """
    Report inappropriate review
    
    Request:
    {
        "reason": "Offensive language"
    }
    
    Response:
    {
        "success": true,
        "message": "Review reported successfully"
    }
    """
    try:
        data = request.get_json()
        reason = data.get('reason', '')
        
        review_obj = BuyerReview()
        review = review_obj.get_review_by_id(review_id)
        
        if not review:
            return jsonify({'success': False, 'error': 'Review not found'}), 404
        
        # Create report (would go to moderation queue)
        success = review_obj.report_review(review_id, reason)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to report review'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Review reported successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in report_review: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to report review'}), 500
