"""
Configuration pytest pour l'application
"""
import pytest
import sys
import os

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Configuration globale de pytest"""
    # Markers personnalisés
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests related to authentication"
    )
    config.addinivalue_line(
        "markers", "cache: marks tests related to caching"
    )
    config.addinivalue_line(
        "markers", "db: marks tests that require database"
    )


def pytest_collection_modifyitems(config, items):
    """Modifier la collection des tests"""
    for item in items:
        # Marquer automatiquement les tests selon leur nom/emplacement
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "test_auth" in item.nodeid:
            item.add_marker(pytest.mark.auth)
        if "test_cache" in item.name.lower():
            item.add_marker(pytest.mark.cache)
        if "slow" in item.name.lower() or "performance" in item.name.lower():
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuration de l'environnement de test"""
    # Variables d'environnement pour les tests
    os.environ['TESTING'] = 'True'
    os.environ['WTF_CSRF_ENABLED'] = 'False'  # Désactiver CSRF pour les tests
    
    yield
    
    # Nettoyage après tous les tests
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
    if 'WTF_CSRF_ENABLED' in os.environ:
        del os.environ['WTF_CSRF_ENABLED']


@pytest.fixture(scope="function")
def cleanup_files():
    """Nettoyer les fichiers créés pendant les tests"""
    yield
    
    # Nettoyer les fichiers de session de test
    test_session_dir = "flask_session_test"
    if os.path.exists(test_session_dir):
        import shutil
        shutil.rmtree(test_session_dir)


# Configuration des options de ligne de commande
def pytest_addoption(parser):
    """Ajouter des options de ligne de commande"""
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-integration", action="store_true", default=False,
        help="run integration tests"
    )


def pytest_runtest_setup(item):
    """Configuration avant chaque test"""
    # Skip les tests lents si l'option n'est pas activée
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")
    
    # Skip les tests d'intégration si l'option n'est pas activée
    if "integration" in item.keywords and not item.config.getoption("--run-integration"):
        pytest.skip("need --run-integration option to run")
