"""
Intégration Sentry pour monitoring d'erreurs et performance
"""
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

# Intégrations optionnelles
try:
    from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


def init_sentry(app):
    """Initialise Sentry pour monitoring d'erreurs et performance"""
    
    # Configuration Sentry
    sentry_dsn = os.environ.get('SENTRY_DSN')
    environment = os.environ.get('FLASK_ENV', 'development')
    release = os.environ.get('SENTRY_RELEASE', 'unknown')
    
    if not sentry_dsn:
        app.logger.warning("SENTRY_DSN non configuré - monitoring Sentry désactivé")
        return
    
    # Intégration logging
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture les logs INFO et plus
        event_level=logging.ERROR  # Envoie les erreurs comme events à Sentry
    )
    
    # Intégrations automatiques
    integrations = [
        FlaskIntegration(
            transaction_style='endpoint'  # Track les endpoints Flask
        ),
        sentry_logging,           # Intégration logs
    ]
    
    # Ajouter les intégrations optionnelles si disponibles
    if SQLALCHEMY_AVAILABLE:
        integrations.append(SqlAlchemyIntegration())
    
    # Initialisation Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        release=release,
        
        # Intégrations
        integrations=integrations,
        
        # Performance monitoring
        traces_sample_rate=1.0 if environment == 'development' else 0.1,  # 10% en prod
        
        # Sampling des erreurs (100% par défaut)
        sample_rate=1.0,
        
        # Configuration avancée
        attach_stacktrace=True,    # Stack trace sur tous les messages
        send_default_pii=False,    # Ne pas envoyer d'infos personnelles
        
        # Filtrage des erreurs
        before_send=filter_sentry_events,
    )
    
    app.logger.info(f"Sentry initialisé - Environment: {environment}, Release: {release}")


def filter_sentry_events(event, hint):
    """Filtre les events Sentry avant envoi"""
    
    # Ignorer certaines erreurs communes
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # Ignorer les erreurs 404 (pas vraiment des erreurs)
        if 'Not Found' in str(exc_value):
            return None
        
        # Ignorer les erreurs de connexion réseau temporaires
        if 'Connection refused' in str(exc_value):
            return None
    
    # Anonymiser les données sensibles
    if 'request' in event:
        request = event['request']
        
        # Supprimer les mots de passe des données POST
        if 'data' in request and isinstance(request['data'], dict):
            if 'password' in request['data']:
                request['data']['password'] = '[Filtered]'
            if 'confirmation' in request['data']:
                request['data']['confirmation'] = '[Filtered]'
    
    return event


def capture_user_context(user_id=None, username=None, email=None):
    """Ajoute le contexte utilisateur à Sentry"""
    sentry_sdk.set_user({
        "id": user_id,
        "username": username,
        "email": email
    })


def capture_custom_event(message, level='info', extra=None):
    """Capture un événement custom dans Sentry"""
    with sentry_sdk.configure_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        
        sentry_sdk.capture_message(message, level=level)


def performance_transaction(name, op='function'):
    """Décorateur pour tracer les performances d'une fonction"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(name=name, op=op):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Métriques custom pour Sentry
class SentryMetrics:
    """Collecteur de métriques custom pour Sentry"""
    
    @staticmethod
    def increment(metric_name, value=1, tags=None):
        """Incrémenter une métrique"""
        sentry_sdk.set_extra(f"metric_{metric_name}", value)
        if tags:
            for key, val in tags.items():
                sentry_sdk.set_tag(key, val)
    
    @staticmethod
    def timing(metric_name, duration, tags=None):
        """Enregistrer une durée"""
        sentry_sdk.set_extra(f"timing_{metric_name}", f"{duration:.3f}s")
        if tags:
            for key, val in tags.items():
                sentry_sdk.set_tag(key, val)
    
    @staticmethod
    def gauge(metric_name, value, tags=None):
        """Enregistrer une valeur de gauge"""
        sentry_sdk.set_extra(f"gauge_{metric_name}", value)
        if tags:
            for key, val in tags.items():
                sentry_sdk.set_tag(key, val)
