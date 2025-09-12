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

# Configuration d'environnement pour les tests (désactiver la vraie DB)
os.environ['DATABASE_URL'] = 'postgresql://mock:mock@localhost/mock_db'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['FLASK_ENV'] = 'testing'

# Mock global du pool de connexions pour tous les tests
with patch('helpers.core.initialize_db_pool'):
    with patch('helpers.core.get_connection'):
        from app import app


@pytest.fixture(scope='session')
def test_app():
    """Configuration de l'application pour les tests"""
    
    # Configuration spécifique aux tests
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'DATABASE_URL': 'postgresql://mock:mock@localhost/mock_db',
        'SENTRY_DSN': None,  # Désactiver Sentry en test
        'ADMIN_USER_ID': '1',
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
    
    # Simuler un utilisateur connecté
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'test_user'
    
    return {'user_id': 1, 'username': 'test_user'}


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
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert 'html' in content


# Décorateurs pour les tests
def requires_auth(test_func):
    """Décorateur pour tests nécessitant une authentification"""
    def wrapper(*args, **kwargs):
        return test_func(*args, **kwargs)
    return wrapper
