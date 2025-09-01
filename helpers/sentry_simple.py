"""
Configuration Sentry simple et robuste pour l'application LawAndCode
"""
import os
import logging

def init_sentry(app):
    """Initialise Sentry pour monitoring d'erreurs et performance"""
    
    # Configuration Sentry
    sentry_dsn = os.environ.get('SENTRY_DSN')
    environment = os.environ.get('FLASK_ENV', 'development')
    
    if not sentry_dsn:
        app.logger.warning("SENTRY_DSN non configuré - monitoring Sentry désactivé")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Intégration logging
        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # Capture les logs INFO et plus
            event_level=logging.ERROR  # Envoie les erreurs comme events à Sentry
        )
        
        # Initialisation Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            integrations=[
                FlaskIntegration(transaction_style='endpoint'),
                sentry_logging,
            ],
            traces_sample_rate=1.0 if environment == 'development' else 0.1,
            sample_rate=1.0,
            attach_stacktrace=True,
            send_default_pii=False,
            before_send=filter_sentry_events,
        )
        
        app.logger.info(f"✅ Sentry initialisé - Environment: {environment}")
        
    except ImportError:
        app.logger.warning("❌ Sentry SDK non installé - monitoring désactivé")
    except Exception as e:
        app.logger.error(f"❌ Erreur initialisation Sentry: {e}")


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
    try:
        import sentry_sdk
        sentry_sdk.set_user({
            "id": user_id,
            "username": username,
            "email": email
        })
    except ImportError:
        pass


def capture_custom_event(message, level='info', extra=None):
    """Capture un événement custom dans Sentry"""
    try:
        import sentry_sdk
        with sentry_sdk.configure_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            
            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        pass


class SentryMetrics:
    """Collecteur de métriques custom pour Sentry"""
    
    @staticmethod
    def increment(metric_name, value=1, tags=None):
        """Incrémenter une métrique"""
        try:
            import sentry_sdk
            sentry_sdk.set_extra(f"metric_{metric_name}", value)
            if tags:
                for key, val in tags.items():
                    sentry_sdk.set_tag(key, val)
        except ImportError:
            pass
    
    @staticmethod
    def timing(metric_name, duration, tags=None):
        """Enregistrer une durée"""
        try:
            import sentry_sdk
            sentry_sdk.set_extra(f"timing_{metric_name}", f"{duration:.3f}s")
            if tags:
                for key, val in tags.items():
                    sentry_sdk.set_tag(key, val)
        except ImportError:
            pass
