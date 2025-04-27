from functools import wraps
from flask import current_app, request
import hashlib
import json
from datetime import datetime

class Cache:
    """Cache utility class"""
    
    @staticmethod
    def generate_key(prefix, *args, **kwargs):
        """Generate a cache key from arguments"""
        key_parts = [prefix]
        
        # Add args to key
        for arg in args:
            if isinstance(arg, (list, dict)):
                key_parts.append(hashlib.md5(
                    json.dumps(arg, sort_keys=True).encode('utf-8')
                ).hexdigest())
            else:
                key_parts.append(str(arg))
        
        # Add kwargs to key
        if kwargs:
            key_parts.append(hashlib.md5(
                json.dumps(sorted(kwargs.items())).encode('utf-8')
            ).hexdigest())
        
        return ':'.join(key_parts)
    
    @staticmethod
    def cached(prefix, timeout=300):
        """Decorator for caching function results"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Generate cache key
                cache_key = Cache.generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_result = current_app.redis.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
                
                # If not in cache, execute function
                result = f(*args, **kwargs)
                
                # Cache the result
                current_app.redis.setex(
                    cache_key,
                    timeout,
                    json.dumps(result)
                )
                
                return result
            return wrapped
        return decorator
    
    @staticmethod
    def memoize(prefix, timeout=300):
        """Decorator for memoizing function results with request context"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Include request path and query string in cache key
                cache_key = Cache.generate_key(
                    prefix,
                    request.path,
                    request.query_string.decode('utf-8'),
                    *args,
                    **kwargs
                )
                
                # Try to get from cache
                cached_result = current_app.redis.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
                
                # If not in cache, execute function
                result = f(*args, **kwargs)
                
                # Cache the result
                current_app.redis.setex(
                    cache_key,
                    timeout,
                    json.dumps(result)
                )
                
                return result
            return wrapped
        return decorator
    
    @staticmethod
    def invalidate(prefix, *args, **kwargs):
        """Invalidate cache for given prefix and arguments"""
        pattern = Cache.generate_key(prefix, *args, **kwargs)
        keys = current_app.redis.keys(f'{pattern}*')
        if keys:
            current_app.redis.delete(*keys)
    
    @staticmethod
    def bulk_invalidate(patterns):
        """Invalidate cache for multiple patterns"""
        for pattern in patterns:
            keys = current_app.redis.keys(f'{pattern}*')
            if keys:
                current_app.redis.delete(*keys)
    
    @staticmethod
    def cache_stampede_prevention(prefix, timeout=300, beta=1):
        """Decorator for preventing cache stampede using probabilistic early expiration"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                cache_key = Cache.generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_data = current_app.redis.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    stored_time = datetime.fromisoformat(data['stored_time'])
                    
                    # Calculate actual age of the cache
                    age = (datetime.utcnow() - stored_time).total_seconds()
                    
                    # Probabilistic early expiration
                    if age < timeout * beta:
                        return data['result']
                
                # If not in cache or expired, execute function
                result = f(*args, **kwargs)
                
                # Cache the result with timestamp
                cache_data = {
                    'result': result,
                    'stored_time': datetime.utcnow().isoformat()
                }
                current_app.redis.setex(
                    cache_key,
                    timeout,
                    json.dumps(cache_data)
                )
                
                return result
            return wrapped
        return decorator
