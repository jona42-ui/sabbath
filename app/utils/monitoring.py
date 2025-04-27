from functools import wraps
import time
from flask import request, current_app
import psutil
import os
from datadog import initialize, statsd
from prometheus_client import Counter, Histogram, Info

# Prometheus metrics
REQUEST_COUNT = Counter(
    'request_count', 'App Request Count',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'request_latency_seconds', 'Request latency',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'error_count', 'App Error Count',
    ['method', 'endpoint', 'error_type']
)

APP_INFO = Info('sabbath_app_info', 'Application information')

def init_monitoring(app):
    """Initialize monitoring systems"""
    
    # Initialize DataDog if configured
    if app.config.get('DATADOG_API_KEY'):
        initialize(
            api_key=app.config.get('DATADOG_API_KEY'),
            app_key=app.config.get('DATADOG_APP_KEY')
        )
    
    # Set basic app info
    APP_INFO.info({
        'version': app.config.get('VERSION', 'unknown'),
        'environment': app.config.get('ENV', 'production')
    })
    
    # Register monitoring middleware
    @app.before_request
    def before_request():
        request._start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Skip monitoring for health check endpoints
        if request.path == '/health':
            return response
        
        # Calculate request duration
        duration = time.time() - request._start_time
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint
        ).observe(duration)
        
        # Send metrics to DataDog if configured
        if app.config.get('DATADOG_API_KEY'):
            tags = [
                f'method:{request.method}',
                f'endpoint:{request.endpoint}',
                f'status:{response.status_code}'
            ]
            
            statsd.increment('sabbath.request.count', tags=tags)
            statsd.histogram('sabbath.request.duration', duration, tags=tags)
        
        return response
    
    # Register error monitoring
    @app.errorhandler(Exception)
    def handle_error(error):
        ERROR_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint,
            error_type=error.__class__.__name__
        ).inc()
        
        if app.config.get('DATADOG_API_KEY'):
            tags = [
                f'method:{request.method}',
                f'endpoint:{request.endpoint}',
                f'error:{error.__class__.__name__}'
            ]
            statsd.increment('sabbath.error.count', tags=tags)
        
        raise error

def get_system_metrics():
    """Collect system metrics"""
    metrics = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage_percent': psutil.disk_usage('/').percent,
        'open_files': len(psutil.Process(os.getpid()).open_files()),
        'connections': len(psutil.Process(os.getpid()).connections()),
        'threads': psutil.Process(os.getpid()).num_threads()
    }
    
    return metrics

def monitor_performance(name):
    """Decorator to monitor function performance"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                status = 'success'
            except Exception as e:
                status = 'error'
                raise e
            finally:
                duration = time.time() - start_time
                
                # Record metrics
                if current_app.config.get('DATADOG_API_KEY'):
                    tags = [f'function:{name}', f'status:{status}']
                    statsd.timing(f'sabbath.function.duration', duration * 1000, tags=tags)
                    statsd.increment(f'sabbath.function.calls', tags=tags)
            
            return result
        return wrapped
    return decorator

def track_resource_usage(name):
    """Decorator to track function resource usage"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            process = psutil.Process(os.getpid())
            start_cpu_time = process.cpu_times()
            start_memory = process.memory_info()
            
            result = f(*args, **kwargs)
            
            end_cpu_time = process.cpu_times()
            end_memory = process.memory_info()
            
            cpu_user = end_cpu_time.user - start_cpu_time.user
            cpu_system = end_cpu_time.system - start_cpu_time.system
            memory_diff = end_memory.rss - start_memory.rss
            
            if current_app.config.get('DATADOG_API_KEY'):
                tags = [f'function:{name}']
                statsd.gauge(f'sabbath.function.cpu.user', cpu_user, tags=tags)
                statsd.gauge(f'sabbath.function.cpu.system', cpu_system, tags=tags)
                statsd.gauge(f'sabbath.function.memory', memory_diff, tags=tags)
            
            return result
        return wrapped
    return decorator
