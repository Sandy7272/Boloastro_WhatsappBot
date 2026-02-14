"""
Analytics API
Endpoints for admin dashboard and revenue analytics
"""

from flask import Blueprint, jsonify, request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create blueprint
analytics_api = Blueprint('analytics_api', __name__, url_prefix='/api/v1/analytics')


def require_auth(f):
    """Simple authentication decorator (extend for production)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement proper authentication
        # For now, just check for API key in header
        api_key = request.headers.get('X-API-Key')
        
        # Skip auth in development
        from backend.config import Config
        if Config.ENVIRONMENT == 'development':
            return f(*args, **kwargs)
        
        if not api_key:
            return jsonify({"error": "Authentication required"}), 401
        
        # TODO: Validate API key
        return f(*args, **kwargs)
    
    return decorated_function


@analytics_api.route('/dashboard', methods=['GET'])
@require_auth
def get_dashboard():
    """
    Get complete dashboard statistics
    
    Returns:
        JSON: All analytics data
    """
    try:
        from backend.services.analytics.analytics_service import get_analytics_service
        
        analytics = get_analytics_service()
        stats = analytics.get_dashboard_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api.route('/revenue', methods=['GET'])
@require_auth
def get_revenue():
    """
    Get revenue summary
    
    Query params:
        days: Number of days (default: 30)
    
    Returns:
        JSON: Revenue data
    """
    try:
        from backend.services.analytics.analytics_service import get_analytics_service
        
        days = int(request.args.get('days', 30))
        
        analytics = get_analytics_service()
        revenue = analytics.get_revenue_summary(days=days)
        
        return jsonify({
            "success": True,
            "data": revenue
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Revenue API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api.route('/mrr', methods=['GET'])
@require_auth
def get_mrr():
    """
    Get Monthly Recurring Revenue
    
    Returns:
        JSON: MRR value
    """
    try:
        from backend.services.analytics.analytics_service import get_analytics_service
        
        analytics = get_analytics_service()
        mrr = analytics.get_mrr()
        
        return jsonify({
            "success": True,
            "data": {
                "mrr": mrr,
                "currency": "INR"
            }
        }), 200
    
    except Exception as e:
        logger.error(f"❌ MRR API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api.route('/funnel', methods=['GET'])
@require_auth
def get_funnel():
    """
    Get conversion funnel metrics
    
    Returns:
        JSON: Funnel data
    """
    try:
        from backend.services.analytics.analytics_service import get_analytics_service
        
        analytics = get_analytics_service()
        funnel = analytics.get_conversion_funnel()
        
        return jsonify({
            "success": True,
            "data": funnel
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Funnel API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api.route('/success-rate', methods=['GET'])
@require_auth
def get_success_rate():
    """
    Get payment success rate
    
    Query params:
        days: Number of days (default: 7)
    
    Returns:
        JSON: Success rate metrics
    """
    try:
        from backend.services.analytics.analytics_service import get_analytics_service
        
        days = int(request.args.get('days', 7))
        
        analytics = get_analytics_service()
        success_rate = analytics.get_payment_success_rate(days=days)
        
        return jsonify({
            "success": True,
            "data": success_rate
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Success rate API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api.route('/customers/top', methods=['GET'])
@require_auth
def get_top_customers():
    """
    Get top customers by revenue
    
    Query params:
        limit: Number of customers (default: 10)
    
    Returns:
        JSON: Top customers
    """
    try:
        from backend.services.analytics.analytics_service import get_analytics_service
        
        limit = int(request.args.get('limit', 10))
        
        analytics = get_analytics_service()
        customers = analytics.get_top_customers(limit=limit)
        
        return jsonify({
            "success": True,
            "data": customers
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Top customers API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api.route('/ltv', methods=['GET'])
@require_auth
def get_ltv():
    """
    Get user lifetime value
    
    Query params:
        phone: Specific user phone (optional)
    
    Returns:
        JSON: LTV data
    """
    try:
        from backend.services.analytics.analytics_service import get_analytics_service
        
        phone = request.args.get('phone')
        
        analytics = get_analytics_service()
        ltv = analytics.get_user_ltv(phone=phone)
        
        return jsonify({
            "success": True,
            "data": ltv
        }), 200
    
    except Exception as e:
        logger.error(f"❌ LTV API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Health check
@analytics_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "analytics_api"
    }), 200