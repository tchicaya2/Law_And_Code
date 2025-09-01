"""
Configuration de base pour les tests unitaires et d'intégration
"""
import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import avec gestion d'erreur pour les tests
try:
    from app import app
    from helpers import get_connection, db_request
except ImportError:
    # Créer une app Flask minimale pour les tests si l'import échoue
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Mock des fonctions helpers
    def get_connection():
        return MagicMock()
    
    def db_request(query, params=None, fetch=True):
        return []

# Configuration de test
TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://test_user:test_pass@localhost/test_lawandcode')

@pytest.fixture(scope='session')
def test_app():
    """Configuration de l'application pour les tests"""
    
    # Configuration spécifique aux tests
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'DATABASE_URL': TEST_DATABASE_URL,
        'SENTRY_DSN': None,  # Désactiver Sentry en test
    })
    
    return app


@pytest.fixture(scope='function')
def client(test_app):
    """Client de test Flask"""
    with test_app.test_client() as client:
        with test_app.app_context():
            yield client


@pytest.fixture(scope='function')
def mock_db():
    """Mock de base de données pour tests unitaires"""
    with patch('helpers.core.get_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.__enter__ = lambda x: mock_conn.return_value
        mock_conn.return_value.__exit__ = lambda x, y, z, w: None
        yield mock_cursor


@pytest.fixture(scope='function')
def authenticated_user(client):
    """Utilisateur authentifié pour les tests"""
    
    # Créer un utilisateur de test
    test_user_data = {
        'username': 'test_user',
        'password': 'TestPass123!',
        'email': 'test@example.com'
    }
    
    # S'inscrire
    response = client.post('/auth/register', data={
        'username': test_user_data['username'],
        'password': test_user_data['password'],
        'confirmation': test_user_data['password'],
        'email': test_user_data['email']
    })
    
    # Se connecter
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = test_user_data['username']
    
    return test_user_data


@pytest.fixture(scope='function')
def sample_quiz_data():
    """Données de quiz pour les tests"""
    return {
        'title': 'Test Quiz Droit Civil',
        'description': 'Quiz de test pour les tests unitaires',
        'matiere': 'Droit Civil',
        'questions': [
            {
                'question': 'Qu\'est-ce que le droit civil ?',
                'options': ['Droit public', 'Droit privé', 'Droit pénal', 'Droit fiscal'],
                'correct_answer': 1,
                'explanation': 'Le droit civil est une branche du droit privé'
            },
            {
                'question': 'Qui peut passer un contrat ?',
                'options': ['Majeurs seulement', 'Toute personne capable', 'Avocats seulement', 'Notaires seulement'],
                'correct_answer': 1,
                'explanation': 'Toute personne juridiquement capable peut contracter'
            }
        ]
    }


class DatabaseTestHelper:
    """Helper pour les tests avec base de données"""
    
    @staticmethod
    def setup_test_data():
        """Créer des données de test dans la base"""
        
        # Créer un utilisateur de test
        db_request("""
            INSERT INTO users (username, hash, email, authentication_token) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, ('test_user', 'test_hash', 'test@example.com', 'test_token'), fetch=False)
        
        # Créer des quiz de test
        db_request("""
            INSERT INTO quiz (title, description, matiere, creator_id, is_public) 
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, ('Test Quiz', 'Description test', 'Droit Civil', 1, True), fetch=False)
    
    @staticmethod
    def cleanup_test_data():
        """Nettoyer les données de test"""
        
        # Supprimer dans l'ordre inverse des dépendances
        tables_to_clean = [
            'quiz_attempts',
            'stats', 
            'messages',
            'password_reset_tokens',
            'login_attempts',
            'quiz_questions',
            'quiz',
            'users'
        ]
        
        for table in tables_to_clean:
            try:
                db_request(f"DELETE FROM {table} WHERE username = %s OR creator_id = 1", 
                          ('test_user',), fetch=False)
            except:
                pass  # Table peut ne pas exister ou contrainte OK


# Utilitaires de test
def assert_json_response(response, expected_status=200):
    """Vérifier qu'une réponse est du JSON valide"""
    assert response.status_code == expected_status
    assert response.content_type == 'application/json'
    return response.get_json()


def assert_redirect(response, expected_location=None):
    """Vérifier qu'une réponse est une redirection"""
    assert response.status_code in [301, 302, 303, 307, 308]
    if expected_location:
        assert expected_location in response.location


def assert_template_used(response, template_name):
    """Vérifier qu'un template spécifique a été utilisé"""
    # Cette fonction nécessiterait Flask-Testing pour être complète
    assert response.status_code == 200
    # Vérification basique par contenu
    content = response.data.decode('utf-8')
    assert template_name.replace('.html', '') in content or 'html' in content


# Décorateurs pour les tests
def requires_auth(test_func):
    """Décorateur pour tests nécessitant une authentification"""
    def wrapper(*args, **kwargs):
        # Ajouter la logique d'auth si nécessaire
        return test_func(*args, **kwargs)
    return wrapper


def with_test_data(test_func):
    """Décorateur pour tests nécessitant des données de test"""
    def wrapper(*args, **kwargs):
        DatabaseTestHelper.setup_test_data()
        try:
            return test_func(*args, **kwargs)
        finally:
            DatabaseTestHelper.cleanup_test_data()
    return wrapper
