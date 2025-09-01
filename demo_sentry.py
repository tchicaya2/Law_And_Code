#!/usr/bin/env python3
"""
Exemple d'utilisation de Sentry avec l'application LawAndCode
Ce script simule différents scénarios pour démontrer les capacités de Sentry
"""
import os
import sys
sys.path.append('.')

from helpers.sentry_simple import init_sentry, capture_user_context, capture_custom_event, SentryMetrics
from flask import Flask
import time
import random

def demo_sentry():
    """Démonstration des fonctionnalités Sentry"""
    
    # Configuration
    os.environ['SENTRY_DSN'] = 'https://demo@sentry.io/demo'  # Fake DSN pour demo
    os.environ['FLASK_ENV'] = 'development'
    
    app = Flask(__name__)
    
    print("🚀 Démonstration Sentry - LawAndCode")
    print("=" * 50)
    
    # 1. Initialisation Sentry
    print("\n1️⃣ Initialisation Sentry...")
    init_sentry(app)
    
    # 2. Définir le contexte utilisateur
    print("\n2️⃣ Définition du contexte utilisateur...")
    capture_user_context(
        user_id=1247,
        username="demo_user",
        email="demo@lawandcode.com"
    )
    print("✅ Contexte utilisateur défini pour Sentry")
    
    # 3. Événements custom métier
    print("\n3️⃣ Capture d'événements métier...")
    
    # Simulation d'un quiz complété
    capture_custom_event(
        "Quiz complété avec succès", 
        level='info',
        extra={
            'quiz_id': 89,
            'quiz_title': 'Droit Civil - Niveau 2',
            'score': '15/20',
            'duration_seconds': 240
        }
    )
    print("✅ Événement 'Quiz complété' capturé")
    
    # Simulation d'une tentative de connexion suspecte
    capture_custom_event(
        "Tentative de connexion avec mot de passe incorrect",
        level='warning',
        extra={
            'attempted_username': 'admin',
            'ip_address': '192.168.1.100',
            'attempts_count': 3
        }
    )
    print("⚠️ Événement de sécurité capturé")
    
    # 4. Métriques custom
    print("\n4️⃣ Envoi de métriques custom...")
    
    SentryMetrics.increment('quiz_completed', tags={'subject': 'droit_civil'})
    SentryMetrics.timing('quiz_loading_time', 0.234, tags={'quiz_type': 'advanced'})
    SentryMetrics.increment('user_registration')
    
    print("📊 Métriques envoyées à Sentry")
    
    # 5. Simulation d'erreurs pour démonstration
    print("\n5️⃣ Simulation d'erreurs (pour démonstration)...")
    
    try:
        # Erreur intentionnelle pour démonstration
        result = 10 / 0
    except ZeroDivisionError as e:
        # Cette erreur sera automatiquement capturée par Sentry
        print(f"❌ Erreur capturée automatiquement par Sentry: {e}")
    
    # Erreur custom avec contexte
    try:
        raise ValueError("Quiz non trouvé - ID invalide")
    except ValueError as e:
        capture_custom_event(
            f"Erreur métier: {str(e)}",
            level='error',
            extra={
                'error_type': 'business_logic',
                'quiz_id': 99999,
                'user_action': 'load_quiz'
            }
        )
        print(f"❌ Erreur métier capturée avec contexte: {e}")
    
    # 6. Simulation de données de performance
    print("\n6️⃣ Simulation de données de performance...")
    
    # Simulation de requêtes avec temps de réponse variables
    for i in range(5):
        endpoint = random.choice(['/quiz/list', '/profile', '/auth/login'])
        duration = random.uniform(0.1, 2.0)
        
        SentryMetrics.timing(f'endpoint_response_time', duration, tags={
            'endpoint': endpoint,
            'status': '200'
        })
        
        print(f"📈 {endpoint}: {duration:.3f}s")
        time.sleep(0.1)
    
    print("\n" + "=" * 50)
    print("🎯 RÉSUMÉ - Ce que Sentry aurait capturé :")
    print("   • Contexte utilisateur (ID, email, username)")
    print("   • 2 événements métier custom")
    print("   • 1 événement de sécurité")
    print("   • 4 métriques custom")
    print("   • 2 erreurs avec stack traces complètes")
    print("   • 5 métriques de performance")
    print("   • Toutes les requêtes HTTP automatiquement")
    print("\n🔍 En production, vous verriez tout cela dans le dashboard Sentry !")
    print("📧 + notifications instantanées sur erreurs critiques")
    print("📊 + graphiques de tendances automatiques")
    print("🚨 + alertes intelligentes sur seuils")


if __name__ == "__main__":
    demo_sentry()
