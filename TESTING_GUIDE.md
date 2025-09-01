# Guide des Tests

## Structure des Tests

```
tests/
├── conftest.py              # Configuration et fixtures globales
├── test_helpers.py          # Tests des fonctions utilitaires
├── test_auth.py            # Tests d'authentification et sécurité
├── test_quiz.py            # Tests des fonctionnalités quiz
├── test_main.py            # Tests des routes principales
└── test_integration.py     # Tests d'intégration bout en bout
```

## Types de Tests

### 1. Tests Unitaires
- **Fichiers** : `test_helpers.py`, `test_auth.py`
- **Focus** : Fonctions individuelles, logique métier
- **Exécution** : `pytest -m unit`

### 2. Tests d'Intégration
- **Fichiers** : `test_integration.py`, `test_quiz.py`, `test_main.py`
- **Focus** : Interaction entre composants, workflows complets
- **Exécution** : `pytest -m integration --run-integration`

### 3. Tests de Performance
- **Marqueur** : `@pytest.mark.slow`
- **Focus** : Performance, charge, concurrence
- **Exécution** : `pytest -m slow --run-slow`

## Commandes d'Exécution

### Tests Basiques
```bash
# Tous les tests rapides
pytest

# Tests spécifiques
pytest tests/test_auth.py
pytest tests/test_helpers.py::TestCacheSystem

# Avec couverture
pytest --cov=helpers --cov=app --cov-report=html
```

### Tests Avancés
```bash
# Tests d'intégration
pytest --run-integration

# Tests de performance
pytest --run-slow

# Tests parallèles
pytest -n auto

# Mode verbose avec détails
pytest -v --tb=long
```

### Tests par Catégorie
```bash
# Authentification
pytest -m auth

# Cache
pytest -m cache

# Base de données
pytest -m db

# Exclure les tests lents
pytest -m "not slow"
```

## Fixtures Disponibles

### Configuration
- `test_app` : Application Flask configurée pour les tests
- `client` : Client de test Flask
- `mock_db` : Base de données mockée

### Authentification
- `authenticated_user` : Utilisateur connecté pour les tests
- `admin_user` : Utilisateur admin pour les tests

### Helpers
- `DatabaseTestHelper` : Utilitaires pour les tests de base de données
- `cleanup_files` : Nettoyage automatique des fichiers de test

## Mocking et Stubs

### Base de Données
```python
@patch('helpers.core.db_request')
def test_function(self, mock_db_request, client):
    mock_db_request.return_value = [('test_data',)]
    # Test logic here
```

### Cache
```python
@patch('helpers.cache.CacheManager.get')
def test_cache(self, mock_cache_get, client):
    mock_cache_get.return_value = None  # Cache miss
    # Test logic here
```

### Authentication
```python
def test_with_auth(self, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'testuser'
    # Test logic here
```

## Patterns de Test

### Test d'API
```python
def test_api_endpoint(self, client):
    response = client.get('/api/endpoint')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'expected_field' in data
```

### Test de Redirection
```python
def test_redirect(self, client):
    response = client.get('/protected-route')
    assert response.status_code in [301, 302, 303, 307, 308]
```

### Test de Formulaire
```python
def test_form_submission(self, client):
    response = client.post('/form-endpoint', data={
        'field1': 'value1',
        'field2': 'value2'
    })
    assert response.status_code == 200
```

## Gestion des Erreurs

### Encodage
```python
# Pour les textes avec accents
assert 'texte français'.encode() in response.data
```

### Exceptions
```python
@patch('helpers.core.db_request')
def test_database_error(self, mock_db_request, client):
    mock_db_request.side_effect = Exception("DB Error")
    response = client.get('/')
    # Test error handling
```

## Configuration de l'Environnement

### Variables d'Environnement
- `TESTING=True` : Mode test activé
- `WTF_CSRF_ENABLED=False` : CSRF désactivé pour les tests

### Base de Données de Test
```python
# Dans conftest.py
@pytest.fixture
def test_database():
    # Setup test database
    yield
    # Cleanup
```

## Couverture de Code

### Installation
```bash
pip install pytest-cov
```

### Exécution
```bash
# Rapport console
pytest --cov=helpers --cov=app

# Rapport HTML
pytest --cov=helpers --cov=app --cov-report=html

# Rapport détaillé
pytest --cov=helpers --cov=app --cov-report=term-missing
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run tests
  run: |
    pytest --cov=helpers --cov=app
    pytest --run-integration
```

### Hooks Pre-commit
```bash
# .pre-commit-hooks.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      files: \.py$
```

## Debugging

### Mode Debug
```bash
# Arrêt au premier échec
pytest -x

# Mode interactif
pytest --pdb

# Logging détaillé
pytest --log-cli-level=DEBUG
```

### Profiling
```bash
# Temps d'exécution
pytest --durations=10

# Profile complet
pytest --profile
```

## Best Practices

1. **Isolation** : Chaque test doit être indépendant
2. **Noms explicites** : `test_user_login_with_valid_credentials`
3. **Arrange-Act-Assert** : Structure claire des tests
4. **Mocking** : Mock les dépendances externes
5. **Fixtures** : Réutiliser la configuration commune
6. **Markers** : Organiser les tests par catégorie
7. **Documentation** : Docstrings pour les tests complexes

## Troubleshooting

### Problèmes Courants

1. **Import Error** : Vérifier `PYTHONPATH` et `sys.path`
2. **Database Lock** : Utiliser des transactions de test
3. **Session Conflicts** : Nettoyer les sessions entre tests
4. **Encoding Issues** : Utiliser `.encode()` pour les comparaisons

### Solutions
```python
# Import fix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Session cleanup
@pytest.fixture(autouse=True)
def cleanup_session():
    yield
    # Clear session data
```
