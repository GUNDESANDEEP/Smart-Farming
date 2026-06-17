"""
Redis Cloud Caching Utility for Smart Farming Marketplace
Provides caching decorators and helpers for aggressive caching.
"""

import json
import functools
from flask import request, current_app
from datetime import datetime

# Cache TTL Constants (seconds)
CACHE_TTL = {
    'products_list': 300,      # 5 minutes
    'product_detail': 600,     # 10 minutes
    'farmer_profile': 900,     # 15 minutes
    'dashboard_stats': 300,    # 5 minutes
    'weather': 1800,           # 30 minutes
    'market_prices': 600,      # 10 minutes
    'search_results': 180,     # 3 minutes
    'default': 300,            # 5 minutes
}


def get_redis():
    """Get Redis client from app config"""
    try:
        return current_app.config.get('REDIS_CLIENT')
    except RuntimeError:
        return None


def cache_get(key):
    """Get value from cache"""
    redis_client = get_redis()
    if not redis_client:
        return None
    try:
        value = redis_client.get(f"sf:{key}")
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"[CACHE] Get error for {key}: {e}")
        return None


def cache_set(key, value, ttl=None):
    """Set value in cache"""
    redis_client = get_redis()
    if not redis_client:
        return False
    try:
        ttl = ttl or CACHE_TTL['default']
        serialized = json.dumps(value, default=str)
        redis_client.setex(f"sf:{key}", ttl, serialized)
        return True
    except Exception as e:
        print(f"[CACHE] Set error for {key}: {e}")
        return False


def cache_delete(key):
    """Delete a specific cache key"""
    redis_client = get_redis()
    if not redis_client:
        return False
    try:
        redis_client.delete(f"sf:{key}")
        return True
    except Exception as e:
        print(f"[CACHE] Delete error for {key}: {e}")
        return False


def cache_invalidate_pattern(pattern):
    """Invalidate all cache keys matching a pattern"""
    redis_client = get_redis()
    if not redis_client:
        return False
    try:
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=f"sf:{pattern}", count=100)
            if keys:
                redis_client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        if deleted > 0:
            print(f"[CACHE] Invalidated {deleted} keys matching '{pattern}'")
        return True
    except Exception as e:
        print(f"[CACHE] Invalidate error for pattern {pattern}: {e}")
        return False


def cached(ttl=None, key_prefix=None, include_query_params=True):
    """
    Decorator for caching route responses.
    
    Usage:
        @cached(ttl=300, key_prefix='products')
        def get_products():
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            redis_client = get_redis()
            if not redis_client:
                return f(*args, **kwargs)
            
            # Build cache key
            prefix = key_prefix or f.__name__
            if include_query_params:
                params = '&'.join(sorted(f"{k}={v}" for k, v in request.args.items()))
                cache_key = f"{prefix}:{request.path}:{params}" if params else f"{prefix}:{request.path}"
            else:
                cache_key = f"{prefix}:{request.path}"
            
            # Try cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache the result (only for successful responses)
            if result:
                cache_ttl = ttl or CACHE_TTL['default']
                try:
                    # Handle Flask response tuples
                    if isinstance(result, tuple):
                        response_data, status_code = result[0], result[1] if len(result) > 1 else 200
                        if status_code == 200:
                            cache_set(cache_key, response_data, cache_ttl)
                    else:
                        cache_set(cache_key, result, cache_ttl)
                except Exception:
                    pass
            
            return result
        return decorated_function
    return decorator


# ============================================================================
# CACHE INVALIDATION HELPERS
# ============================================================================

def invalidate_product_caches(product_id=None, farmer_id=None):
    """Invalidate all product-related caches"""
    cache_invalidate_pattern("products:*")
    cache_invalidate_pattern("search:*")
    if product_id:
        cache_delete(f"product:{product_id}")
    if farmer_id:
        cache_invalidate_pattern(f"farmer:{farmer_id}:*")
        cache_invalidate_pattern(f"dashboard:farmer:{farmer_id}:*")


def invalidate_order_caches(farmer_id=None, buyer_id=None):
    """Invalidate order-related caches"""
    cache_invalidate_pattern("orders:*")
    if farmer_id:
        cache_invalidate_pattern(f"dashboard:farmer:{farmer_id}:*")
    if buyer_id:
        cache_invalidate_pattern(f"dashboard:buyer:{buyer_id}:*")
    cache_invalidate_pattern("dashboard:admin:*")


def invalidate_user_caches(user_id=None, role=None):
    """Invalidate user-related caches"""
    if user_id:
        cache_delete(f"user:{user_id}")
    if role:
        cache_invalidate_pattern(f"{role}:*")
    cache_invalidate_pattern("dashboard:admin:*")


def invalidate_dashboard_caches():
    """Invalidate all dashboard caches"""
    cache_invalidate_pattern("dashboard:*")
