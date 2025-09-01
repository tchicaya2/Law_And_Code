"""
Système de monitoring et logging pour l'application Flask
"""
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from functools import wraps
from flask import request, session, current_app, g
import json


class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour les logs en développement"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Vert
        'WARNING': '\033[33m',  # Jaune
        'ERROR': '\033[31m',    # Rouge
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Formatter JSON pour les logs en production"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Ajouter des infos de requête si disponibles
        if request:
            log_data.update({
                'request_id': getattr(g, 'request_id', None),
                'user_id': session.get('user_id'),
                'ip': request.remote_addr,
                'method': request.method,
                'url': request.url,
                'user_agent': request.headers.get('User-Agent')
            })
        
        # Ajouter les données d'exception si présentes
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


def setup_logging(app):
    """Configure le système de logging selon l'environnement"""
    
    # Niveau de log selon l'environnement
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    # Dossier de logs
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Supprimer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    if app.debug:
        # Mode développement : logs colorés dans la console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        ))
        logger.addHandler(console_handler)
    else:
        # Mode production : logs JSON dans des fichiers
        
        # Handler pour les logs généraux
        file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
        
        # Handler séparé pour les erreurs
        error_handler = logging.FileHandler(os.path.join(log_dir, 'errors.log'))
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        logger.addHandler(error_handler)
    
    # Logger spécifique pour l'application
    app_logger = logging.getLogger('law_quiz_app')
    app_logger.setLevel(log_level)
    
    return app_logger


def log_performance(func):
    """Décorateur pour mesurer les performances des fonctions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger('law_quiz_app.performance')
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"Performance: {func.__name__} executed in {execution_time:.3f}s", extra={
                'function': func.__name__,
                'execution_time': execution_time,
                'status': 'success'
            })
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Performance: {func.__name__} failed after {execution_time:.3f}s", extra={
                'function': func.__name__,
                'execution_time': execution_time,
                'status': 'error',
                'error': str(e)
            })
            raise
    
    return wrapper


def log_user_action(action, details=None):
    """Log les actions utilisateur importantes"""
    logger = logging.getLogger('law_quiz_app.user_actions')
    
    log_data = {
        'action': action,
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'ip': request.remote_addr if request else None,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"User action: {action}", extra=log_data)


def log_security_event(event_type, details=None):
    """Log les événements de sécurité"""
    logger = logging.getLogger('law_quiz_app.security')
    
    log_data = {
        'event_type': event_type,
        'user_id': session.get('user_id'),
        'ip': request.remote_addr if request else None,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    logger.warning(f"Security event: {event_type}", extra=log_data)


class MetricsCollector:
    """Collecteur de métriques pour le monitoring"""
    
    def __init__(self):
        self.metrics = {}
    
    def increment(self, metric_name, tags=None):
        """Incrémenter une métrique"""
        key = f"{metric_name}:{tags or ''}"
        self.metrics[key] = self.metrics.get(key, 0) + 1
    
    def gauge(self, metric_name, value, tags=None):
        """Définir une valeur de métrique"""
        key = f"{metric_name}:{tags or ''}"
        self.metrics[key] = value
    
    def timer(self, metric_name, duration, tags=None):
        """Enregistrer une durée"""
        key = f"{metric_name}_duration:{tags or ''}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(duration)
    
    def get_metrics(self):
        """Récupérer toutes les métriques"""
        return self.metrics.copy()
    
    def reset(self):
        """Reset toutes les métriques"""
        self.metrics.clear()


# Instance globale du collecteur de métriques
metrics = MetricsCollector()


def setup_error_handling(app):
    """Configure la gestion d'erreurs globale"""
    logger = logging.getLogger('law_quiz_app.errors')
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 Error: {request.url}", extra={
            'error_type': '404',
            'url': request.url,
            'user_id': session.get('user_id'),
            'ip': request.remote_addr
        })
        metrics.increment('http_errors', tags='404')
        return "Page non trouvée", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Error: {error}", extra={
            'error_type': '500',
            'url': request.url,
            'user_id': session.get('user_id'),
            'ip': request.remote_addr
        }, exc_info=True)
        metrics.increment('http_errors', tags='500')
        return "Erreur interne du serveur", 500
    
    @app.errorhandler(403)
    def forbidden(error):
        logger.warning(f"403 Error: {request.url}", extra={
            'error_type': '403',
            'url': request.url,
            'user_id': session.get('user_id'),
            'ip': request.remote_addr
        })
        metrics.increment('http_errors', tags='403')
        log_security_event('forbidden_access', {'url': request.url})
        return "Accès interdit", 403


def setup_request_monitoring(app):
    """Configure le monitoring des requêtes"""
    logger = logging.getLogger('law_quiz_app.requests')
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = f"{time.time()}_{os.getpid()}"
        
        # Log de la requête entrante
        logger.debug(f"Request: {request.method} {request.url}", extra={
            'request_id': g.request_id,
            'method': request.method,
            'url': request.url,
            'user_id': session.get('user_id'),
            'ip': request.remote_addr
        })
    
    @app.after_request
    def after_request(response):
        duration = time.time() - g.start_time
        
        # Log de la réponse
        logger.info(f"Response: {response.status_code} in {duration:.3f}s", extra={
            'request_id': g.request_id,
            'status_code': response.status_code,
            'duration': duration,
            'user_id': session.get('user_id')
        })
        
        # Métriques
        metrics.increment('http_requests', tags=f"status_{response.status_code}")
        metrics.timer('request_duration', duration)
        
        return response


def health_check():
    """Endpoint de health check pour le monitoring"""
    from helpers import get_connection
    
    status = {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
    
    try:
        # Test de connexion à la base de données
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        status['database'] = 'healthy'
    except Exception as e:
        status['database'] = 'unhealthy'
        status['database_error'] = str(e)
        status['status'] = 'degraded'
    
    try:
        # Test du cache Redis
        from app import redis_client
        if redis_client:
            redis_client.ping()
            status['cache'] = 'healthy'
        else:
            status['cache'] = 'memory_fallback'
    except Exception as e:
        status['cache'] = 'unhealthy'
        status['cache_error'] = str(e)
    
    # Ajouter les métriques
    status['metrics'] = metrics.get_metrics()
    
    return status
