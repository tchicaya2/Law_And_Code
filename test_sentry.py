#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement de Sentry
"""
import os
import sys
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire du projet au path
sys.path.append('.')

def test_sentry_basic():
    """Test basique de Sentry"""
    print("🔧 Test 1: Initialisation Sentry...")
    
    try:
        from helpers.sentry_simple import init_sentry
        
        # Créer une app Flask simple pour le test
        from flask import Flask
        test_app = Flask(__name__)
        
        # Initialiser Sentry
        init_sentry(test_app)
        
        print("✅ Sentry initialisé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

def test_sentry_events():
    """Test des événements Sentry"""
    print("\n🔧 Test 2: Envoi d'événements à Sentry...")
    
    try:
        import sentry_sdk
        from helpers.sentry_simple import capture_custom_event, capture_user_context
        
        # Test 1: Message simple
        print("  📤 Envoi d'un message de test...")
        sentry_sdk.capture_message("Test Sentry - Application démarrée", level='info')
        time.sleep(1)
        
        # Test 2: Exception simulée
        print("  📤 Envoi d'une exception de test...")
        try:
            raise ValueError("Exception de test pour Sentry")
        except Exception as e:
            sentry_sdk.capture_exception(e, extra={
                'test': True,
                'message': 'Test de capture d\'exception',
                'timestamp': time.time()
            })
        time.sleep(1)
        
        # Test 3: Contexte utilisateur
        print("  📤 Test du contexte utilisateur...")
        capture_user_context(
            user_id=999,
            username="test_user", 
            email="test@example.com"
        )
        
        sentry_sdk.capture_message("Message avec contexte utilisateur", level='info')
        time.sleep(1)
        
        # Test 4: Event custom
        print("  📤 Test d'événement personnalisé...")
        capture_custom_event(
            message="Événement personnalisé de test", 
            level='warning',
            extra={
                'feature': 'sentry_test',
                'version': '1.0.0'
            }
        )
        time.sleep(1)
        
        print("✅ Tous les événements envoyés avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi d'événements: {e}")
        return False

def test_sentry_performance():
    """Test du monitoring de performance"""
    print("\n🔧 Test 3: Monitoring de performance...")
    
    try:
        import sentry_sdk
        
        # Test de transaction
        print("  ⏱️  Test de transaction de performance...")
        with sentry_sdk.start_transaction(op="test", name="test_performance_transaction") as transaction:
            # Simuler du travail
            time.sleep(0.5)
            
            # Ajouter des spans
            with sentry_sdk.start_span(op="db", description="fake database query"):
                time.sleep(0.2)
            
            with sentry_sdk.start_span(op="http", description="fake API call"):
                time.sleep(0.1)
        
        print("✅ Transaction de performance terminée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de performance: {e}")
        return False

def test_sentry_config():
    """Vérifier la configuration Sentry"""
    print("\n🔧 Test 4: Vérification de la configuration...")
    
    sentry_dsn = os.getenv('SENTRY_DSN')
    flask_env = os.getenv('FLASK_ENV')
    
    print(f"  📋 SENTRY_DSN: {'✅ Configuré' if sentry_dsn else '❌ Manquant'}")
    print(f"  📋 FLASK_ENV: {flask_env}")
    print(f"  📋 APP_VERSION: {os.getenv('APP_VERSION', 'Non défini')}")
    
    if sentry_dsn:
        # Masquer la clé pour des raisons de sécurité
        masked_dsn = sentry_dsn[:30] + "***" + sentry_dsn[-10:]
        print(f"  📋 DSN: {masked_dsn}")
        return True
    else:
        print("  ❌ Configuration Sentry incomplète")
        return False

def test_full_app():
    """Test avec l'application complète"""
    print("\n🔧 Test 5: Test avec l'application Flask complète...")
    
    try:
        from app import app
        
        with app.app_context():
            print("  🔧 Application Flask chargée")
            
            # Tester une route
            with app.test_client() as client:
                print("  🌐 Test de la route /health...")
                response = client.get('/health')
                print(f"  📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("  ✅ Application fonctionne correctement")
                    
                    # Envoyer un événement de test depuis l'app
                    import sentry_sdk
                    sentry_sdk.capture_message("Test depuis l'application Flask", level='info')
                    
                    return True
                else:
                    print("  ❌ Problème avec l'application")
                    return False
                    
    except Exception as e:
        print(f"  ❌ Erreur lors du test de l'application: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DES TESTS SENTRY")
    print("=" * 50)
    
    tests = [
        test_sentry_config,
        test_sentry_basic,
        test_sentry_events,
        test_sentry_performance,
        test_full_app
    ]
    
    results = []
    
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_func.__name__}: {e}")
            results.append(False)
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"✅ Tests réussis: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 TOUS LES TESTS SENTRY SONT PASSÉS !")
        print("\n📝 Prochaines étapes:")
        print("   1. Vérifiez vos événements sur https://sentry.io")
        print("   2. Configurez des alertes dans Sentry si besoin")
        print("   3. Le monitoring est maintenant actif sur votre application !")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    print("\n🔗 Pour voir vos événements: https://sentry.io/organizations/votre-org/projects/")
    print(f"🌍 Environment: {os.getenv('FLASK_ENV', 'development')}")

if __name__ == "__main__":
    main()
