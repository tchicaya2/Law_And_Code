"""
Tests pour les routes d'authentification
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import session


def assert_redirect(response, expected_location=None):
    """Vérifier qu'une réponse est une redirection"""
    assert response.status_code in [301, 302, 303, 307, 308]


class TestAuthRoutes:
    """Tests des routes d'authentification"""
    
    def test_login_page_get(self, client):
        """Test affichage page de connexion"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_register_page_get(self, client):
        """Test affichage page d'inscription"""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower() or b'inscription' in response.data.lower()
    
    @patch('helpers.core.db_request')
    def test_register_success(self, mock_db_request, client):
        """Test inscription réussie"""
        # Mock des requêtes DB
        mock_db_request.side_effect = [
            [],  # Vérification username n'existe pas
            None,  # Insertion utilisateur
            [(1,)],  # Récupération ID utilisateur
            None  # Insertion login_attempts
        ]
        
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'password': 'TestPass123!',
            'confirmation': 'TestPass123!',
            'email': 'new@example.com'
        })
        
        assert_redirect(response)
        assert mock_db_request.call_count >= 3
    
    def test_register_password_mismatch(self, client):
        """Test inscription avec mots de passe différents"""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'password': 'TestPass123!',
            'confirmation': 'DifferentPass123!',
            'email': 'new@example.com'
        })
        
        assert response.status_code == 400
        assert b'correspondent pas' in response.data
    
    def test_register_weak_password(self, client):
        """Test inscription avec mot de passe faible"""
        weak_passwords = [
            'weak',           # Trop court
            'password',       # Pas de majuscule/chiffre/spécial
            'Password',       # Pas de chiffre/spécial
            'Password123',    # Pas de caractère spécial
        ]
        
        for weak_password in weak_passwords:
            response = client.post('/auth/register', data={
                'username': 'newuser',
                'password': weak_password,
                'confirmation': weak_password,
                'email': 'new@example.com'
            })
            
            assert response.status_code == 400
            assert '8 caractères'.encode() in response.data
    
    def test_register_invalid_email(self, client):
        """Test inscription avec email invalide"""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'password': 'TestPass123!',
            'confirmation': 'TestPass123!',
            'email': 'invalid-email'
        })
        
        assert response.status_code == 400
        assert b'email valide' in response.data
    
    @patch('helpers.core.db_request')
    def test_register_username_already_exists(self, mock_db_request, client):
        """Test inscription avec nom d'utilisateur existant"""
        # Mock : username existe déjà
        mock_db_request.return_value = [('existing_user',)]
        
        response = client.post('/auth/register', data={
            'username': 'existing_user',
            'password': 'TestPass123!',
            'confirmation': 'TestPass123!',
            'email': 'new@example.com'
        })
        
        assert response.status_code == 400
        assert 'déjà pris'.encode() in response.data
    
    @patch('helpers.core.db_request')
    @patch('werkzeug.security.check_password_hash')
    def test_login_success(self, mock_check_password, mock_db_request, client):
        """Test connexion réussie"""
        # Mock des données utilisateur
        mock_db_request.side_effect = [
            [(1, 'testuser', 'hashed_password', 'test@example.com')],  # User exists
            (None, 5, 0),  # Login attempts data
            None  # Reset login attempts
        ]
        mock_check_password.return_value = True
        
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        
        assert_redirect(response)
        # Vérifier que l'utilisateur est en session
        with client.session_transaction() as sess:
            assert 'user_id' in sess
            assert sess['username'] == 'testuser'
    
    @patch('helpers.core.db_request')
    def test_login_invalid_credentials(self, mock_db_request, client):
        """Test connexion avec identifiants incorrects"""
        # Mock : utilisateur n'existe pas
        mock_db_request.return_value = []
        
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'WrongPass123!'
        })
        
        assert response.status_code == 403
        assert b'incorrect' in response.data
    
    @patch('helpers.core.db_request')
    @patch('werkzeug.security.check_password_hash')
    def test_login_wrong_password(self, mock_check_password, mock_db_request, client):
        """Test connexion avec mot de passe incorrect"""
        mock_db_request.side_effect = [
            [(1, 'testuser', 'hashed_password', 'test@example.com')],  # User exists
            (None, 4, 0),  # Login attempts data
            [(4,)]  # Update attempts remaining
        ]
        mock_check_password.return_value = False
        
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'WrongPass123!'
        })
        
        assert response.status_code == 403
        assert b'incorrect' in response.data
    
    def test_login_missing_fields(self, client):
        """Test connexion avec champs manquants"""
        # Pas de nom d'utilisateur
        response = client.post('/auth/login', data={'password': 'TestPass123!'})
        assert response.status_code == 403
        
        # Pas de mot de passe
        response = client.post('/auth/login', data={'username': 'testuser'})
        assert response.status_code == 403
    
    def test_logout(self, client):
        """Test déconnexion"""
        # Se connecter d'abord
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        response = client.get('/auth/logout')
        assert response.status_code == 200
        assert 'déconnecté'.encode() in response.data
        
        # Vérifier que la session est vidée
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'username' not in sess
    
    def test_forgot_password_page(self, client):
        """Test page mot de passe oublié"""
        response = client.get('/auth/forgot_password')
        assert response.status_code == 200
        assert b'email' in response.data.lower()
    
    @patch('helpers.core.db_request')
    @patch('helpers.core.send_reset_email')
    def test_forgot_password_valid_email(self, mock_send_email, mock_db_request, client):
        """Test demande réinitialisation avec email valide"""
        # Mock : utilisateur existe avec cet email
        mock_db_request.side_effect = [
            [(1, 'testuser', 'test@example.com')],  # User exists
            None,  # Delete existing tokens
            None   # Insert new token
        ]
        mock_send_email.return_value = True
        
        response = client.post('/auth/forgot_password', data={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 200
        assert b'email avec les instructions' in response.data
        mock_send_email.assert_called_once()
    
    @patch('helpers.core.db_request')
    def test_forgot_password_invalid_email(self, mock_db_request, client):
        """Test demande réinitialisation avec email invalide"""
        # Mock : aucun utilisateur avec cet email
        mock_db_request.return_value = []
        
        response = client.post('/auth/forgot_password', data={
            'email': 'nonexistent@example.com'
        })
        
        # Même message pour ne pas révéler si l'email existe
        assert response.status_code == 200
        assert b'email avec les instructions' in response.data


class TestEmailManagement:
    """Tests de gestion des emails"""
    
    def test_add_email_requires_auth(self, client):
        """Test ajout email nécessite authentification"""
        response = client.post('/auth/add_email', data={'email': 'new@example.com'})
        assert_redirect(response, '/auth/login')
    
    @patch('helpers.core.db_request')
    def test_add_email_success(self, mock_db_request, client):
        """Test ajout email réussi"""
        # Se connecter
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock DB responses
        mock_db_request.side_effect = [
            [('test_token',)],  # Get auth token
            [(1,)]  # Successful update
        ]
        
        response = client.post('/auth/add_email', data={
            'email': 'new@example.com',
            'authentication_token': 'test_token'
        })
        
        assert_redirect(response)
    
    def test_add_email_invalid_format(self, client):
        """Test ajout email avec format invalide"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        response = client.post('/auth/add_email', data={
            'email': 'invalid-email',
            'authentication_token': 'test_token'
        })
        
        assert_redirect(response)  # Redirection avec message d'erreur


class TestAuthSecurityFeatures:
    """Tests des fonctionnalités de sécurité"""
    
    @patch('helpers.core.db_request')
    def test_login_attempts_limiting(self, mock_db_request, client):
        """Test limitation des tentatives de connexion"""
        # Mock : utilisateur avec 0 tentatives restantes et ban récent
        from datetime import datetime, timezone
        mock_db_request.side_effect = [
            [(1, 'testuser', 'hashed_password')],  # User exists
            (datetime.now(timezone.utc), 0, 1),  # Login attempts: recent fail, 0 left, 1 ban
        ]
        
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        
        assert response.status_code == 403
        assert 'épuisé'.encode() in response.data
    
    def test_csrf_token_validation(self, client):
        """Test validation token CSRF (si implémenté)"""
        # Cette fonctionnalité nécessiterait Flask-WTF
        # Test basique pour s'assurer que les tokens sont requis
        
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Test sans token d'authentification
        response = client.post('/auth/add_email', data={
            'email': 'new@example.com'
            # Pas de authentication_token
        })
        
        # Doit rediriger avec erreur
        assert_redirect(response)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
