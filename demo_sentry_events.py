#!/usr/bin/env python3
"""
Script pour générer des événements Sentry de démonstration
"""
import os
import sys
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
sys.path.append('.')

def demo_user_actions():
    """Simuler des actions utilisateur avec monitoring"""
    print("🧑 Simulation d'actions utilisateur...")
    
    from helpers.sentry_simple import capture_user_context, capture_custom_event
    import sentry_sdk
    
    # Simuler différents utilisateurs
    users = [
        {"id": 1, "username": "admin", "email": "admin@example.com"},
        {"id": 2, "username": "john_doe", "email": "john@example.com"},
        {"id": 3, "username": "jane_smith", "email": "jane@example.com"}
    ]
    
    actions = [
        "user_login",
        "quiz_created", 
        "quiz_completed",
        "account_updated",
        "password_changed"
    ]
    
    for user in users:
        # Définir le contexte utilisateur
        capture_user_context(
            user_id=user["id"],
            username=user["username"],
            email=user["email"]
        )
        
        for action in actions[:2]:  # Limiter le nombre d'actions
            capture_custom_event(
                message=f"Action utilisateur: {action}",
                level='info',
                extra={
                    'action': action,
                    'user_id': user["id"],
                    'timestamp': time.time()
                }
            )
            time.sleep(0.1)  # Petite pause
    
    print("✅ Actions utilisateur simulées")

def demo_errors():
    """Simuler différents types d'erreurs"""
    print("🚨 Simulation d'erreurs pour monitoring...")
    
    import sentry_sdk
    from helpers.sentry_simple import capture_user_context
    
    # Erreur 1: Erreur de base de données
    try:
        capture_user_context(user_id=5, username="test_user")
        raise ConnectionError("Impossible de se connecter à la base de données PostgreSQL")
    except Exception as e:
        sentry_sdk.capture_exception(e, extra={
            'error_type': 'database_connection',
            'component': 'db_pool',
            'severity': 'high'
        })
    
    time.sleep(0.5)
    
    # Erreur 2: Erreur de validation
    try:
        capture_user_context(user_id=10, username="invalid_user")
        raise ValueError("Format d'email invalide: 'email_invalide'")
    except Exception as e:
        sentry_sdk.capture_exception(e, extra={
            'error_type': 'validation_error',
            'component': 'auth',
            'user_input': 'email_invalide',
            'severity': 'medium'
        })
    
    time.sleep(0.5)
    
    # Erreur 3: Erreur de permission
    try:
        capture_user_context(user_id=15, username="restricted_user")
        raise PermissionError("Utilisateur non autorisé à accéder à cette ressource")
    except Exception as e:
        sentry_sdk.capture_exception(e, extra={
            'error_type': 'permission_denied',
            'component': 'auth',
            'requested_resource': '/admin/users',
            'severity': 'medium'
        })
    
    print("✅ Erreurs simulées pour démonstration")

def demo_performance_issues():
    """Simuler des problèmes de performance"""
    print("⏱️ Simulation de problèmes de performance...")
    
    import sentry_sdk
    
    # Transaction lente
    with sentry_sdk.start_transaction(op="http", name="slow_database_query") as transaction:
        transaction.set_tag("endpoint", "/quiz/results")
        transaction.set_tag("user_id", "123")
        
        # Simuler une requête lente
        with sentry_sdk.start_span(op="db", description="SELECT * FROM quiz_results WHERE user_id = %s"):
            time.sleep(2)  # Simuler 2 secondes de latence
        
        # Simuler un calcul complexe
        with sentry_sdk.start_span(op="task", description="calculate_user_statistics"):
            time.sleep(1)  # Simuler 1 seconde de calcul
    
    # Alerte pour requête très lente
    with sentry_sdk.configure_scope() as scope:
        scope.set_extra('query_time', '3.2s')
        scope.set_extra('threshold', '1.0s')
        scope.set_extra('endpoint', '/quiz/results')
        scope.set_extra('optimization_needed', True)
        
        sentry_sdk.capture_message(
            "Requête base de données très lente détectée",
            level='warning'
        )
    
    print("✅ Métriques de performance envoyées")

def demo_security_events():
    """Simuler des événements de sécurité"""
    print("🛡️ Simulation d'événements de sécurité...")
    
    import sentry_sdk
    from helpers.sentry_simple import capture_user_context
    
    # Tentative de connexion suspecte
    with sentry_sdk.configure_scope() as scope:
        scope.set_extra('security_event', 'failed_login_attempts')
        scope.set_extra('ip_address', '192.168.1.100')
        scope.set_extra('attempts', 5)
        scope.set_extra('time_window', '5 minutes')
        scope.set_extra('username_attempted', 'admin')
        
        sentry_sdk.capture_message(
            "Tentatives de connexion multiples échouées",
            level='warning'
        )
    
    time.sleep(0.5)
    
    # Accès non autorisé
    capture_user_context(user_id=999, username="suspicious_user")
    with sentry_sdk.configure_scope() as scope:
        scope.set_extra('security_event', 'unauthorized_access')
        scope.set_extra('endpoint', '/admin/users')
        scope.set_extra('user_role', 'student')
        scope.set_extra('required_role', 'admin')
        scope.set_extra('action_blocked', True)
        
        sentry_sdk.capture_message(
            "Tentative d'accès non autorisé détectée",
            level='error'
        )
    
    time.sleep(0.5)
    
    # Activité de bot détectée
    with sentry_sdk.configure_scope() as scope:
        scope.set_extra('security_event', 'bot_detected')
        scope.set_extra('detection_method', 'honeypot')
        scope.set_extra('ip_address', '203.0.113.1')
        scope.set_extra('user_agent', 'Mozilla/5.0 (compatible; bot/1.0)')
        scope.set_extra('blocked', True)
        
        sentry_sdk.capture_message(
            "Activité de bot détectée sur formulaire de contact",
            level='info'
        )
    
    print("✅ Événements de sécurité enregistrés")

def main():
    """Fonction principale pour la démo"""
    print("🎭 DÉMONSTRATION SENTRY - ÉVÉNEMENTS RÉELS")
    print("=" * 60)
    print("Cette démo va générer différents types d'événements")
    print("que vous pourrez voir dans votre dashboard Sentry.")
    print("=" * 60)
    
    try:
        demo_user_actions()
        print()
        
        demo_errors()
        print()
        
        demo_performance_issues()
        print()
        
        demo_security_events()
        print()
        
        print("🎉 DÉMONSTRATION TERMINÉE !")
        print("=" * 60)
        print("📊 Consultez maintenant votre dashboard Sentry :")
        print("   https://sentry.io")
        print("")
        print("🔍 Vous devriez voir :")
        print("   • Messages d'information (actions utilisateur)")
        print("   • Erreurs simulées (database, validation, permissions)")
        print("   • Métriques de performance (transactions lentes)")
        print("   • Alertes de sécurité (tentatives d'intrusion)")
        print("")
        print("💡 Conseil : Configurez des alertes email/Slack")
        print("   dans Sentry pour être notifié des erreurs importantes !")
        
    except Exception as e:
        print(f"❌ Erreur pendant la démo : {e}")
        import sentry_sdk
        sentry_sdk.capture_exception(e)

if __name__ == "__main__":
    main()
