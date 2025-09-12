"""
Tests pour les routes d'authentification - basés sur le code réel
"""
import pytest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta


class TestAuthLogin:
    """Tests pour la route de connexion"""
    
    def test_login_get_returns_template(self, client):
        """Test que GET /auth/login retourne le template de connexion"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_login_get_with_next_url(self, client):
        """Test que GET /auth/login conserve l'URL next"""
        response = client.get('/auth/login?next=/quiz/choix')
        assert response.status_code == 200
        assert b'/quiz/choix' in response.data or b'next' in response.data
    
    @patch('auth.routes.db_request')
    def test_login_missing_username(self, mock_db, client):
        """Test connexion sans nom d'utilisateur"""
        response = client.post('/auth/login', data={
            'password': 'testpass'
        })
        assert response.status_code == 403
        assert 'nom d\'utilisateur' in response.data.decode().lower()
    
    @patch('auth.routes.db_request')
    def test_login_missing_password(self, mock_db, client):
        """Test connexion sans mot de passe"""
        response = client.post('/auth/login', data={
            'username': 'testuser'
        })
        assert response.status_code == 403
        assert 'mot de passe' in response.data.decode().lower()
    
    @patch('auth.routes.db_request')
    def test_login_user_not_found(self, mock_db, client):
        """Test connexion avec utilisateur inexistant"""
        mock_db.return_value = []  # Utilisateur non trouvé
        
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        assert response.status_code == 403
        assert 'incorrect' in response.data.decode().lower()
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.check_password_hash')
    def test_login_wrong_password(self, mock_check_hash, mock_db, client):
        """Test connexion avec mauvais mot de passe"""
        # Simuler utilisateur existant avec tentatives de connexion
        mock_db.side_effect = [
            [(1, 'testuser', 'hashed_password', 'test@example.com')],  # User exists
            [(None, 5, 0)],  # Login attempts data
            [(4,)]  # Update attempts result
        ]
        mock_check_hash.return_value = False
        
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpass'
        })
        assert response.status_code == 403
        assert 'incorrect' in response.data.decode().lower()
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.check_password_hash')
    @patch('auth.routes.log_user_action')
    @patch('auth.routes.capture_user_context')
    def test_login_success(self, mock_capture, mock_log, mock_check_hash, mock_db, client):
        """Test connexion réussie"""
        # Simuler utilisateur valide et mot de passe correct
        mock_db.side_effect = [
            [(1, 'testuser', 'hashed_password', 'test@example.com')],  # User exists
            [(None, 5, 0)],  # Login attempts data
        ]
        mock_check_hash.return_value = True
        
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'correctpass'
        })
        
        # Vérifier la redirection vers l'index
        assert response.status_code == 302
        assert 'Bienvenu' in response.location or '/' in response.location
        
        # Vérifier que la session contient l'utilisateur
        with client.session_transaction() as sess:
            assert sess.get('user_id') == 1
            assert sess.get('username') == 'testuser'


class TestAuthRegister:
    """Tests pour la route d'inscription"""
    
    def test_register_get_returns_template(self, client):
        """Test que GET /auth/register retourne le template d'inscription"""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower() or b'inscription' in response.data.lower()
    
    @patch('auth.routes.arg_is_present')
    def test_register_missing_fields(self, mock_args, client):
        """Test inscription avec champs manquants"""
        mock_args.return_value = False
        
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'password': '',
            'confirmation': ''
        })
        assert response.status_code == 400
        # La fonction apology devrait renvoyer une erreur
    
    def test_register_password_mismatch(self, client):
        """Test inscription avec mots de passe différents"""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'password': 'Test123!',
            'confirmation': 'Different123!',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        assert 'correspondent pas' in response.data.decode()
    
    def test_register_weak_password(self, client):
        """Test inscription avec mot de passe faible"""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'password': 'weak',
            'confirmation': 'weak',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        assert '8 caractères' in response.data.decode()
    
    @patch('auth.routes.db_request')
    def test_register_username_exists(self, mock_db, client):
        """Test inscription avec nom d'utilisateur existant"""
        mock_db.return_value = [('existing_user',)]  # Username already exists
        
        response = client.post('/auth/register', data={
            'username': 'existinguser',
            'password': 'Test123!',
            'confirmation': 'Test123!',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        assert 'déjà pris' in response.data.decode()
    
    def test_register_username_too_long(self, client):
        """Test inscription avec nom d'utilisateur trop long"""
        long_username = 'a' * 60  # Plus de 50 caractères
        
        response = client.post('/auth/register', data={
            'username': long_username,
            'password': 'Test123!',
            'confirmation': 'Test123!',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        assert 'trop long' in response.data.decode()
    
    def test_register_username_too_short(self, client):
        """Test inscription avec nom d'utilisateur trop court"""
        response = client.post('/auth/register', data={
            'username': 'ab',  # Moins de 3 caractères
            'password': 'Test123!',
            'confirmation': 'Test123!',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
        assert 'au moins 3' in response.data.decode()
    
    @patch('auth.routes.is_valid_email')
    def test_register_invalid_email(self, mock_email_valid, client):
        """Test inscription avec email invalide"""
        mock_email_valid.return_value = False
        
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'password': 'Test123!',
            'confirmation': 'Test123!',
            'email': 'invalid-email'
        })
        assert response.status_code == 400
        assert 'email valide' in response.data.decode()
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.is_valid_email')
    def test_register_email_exists(self, mock_email_valid, mock_db, client):
        """Test inscription avec email déjà utilisé"""
        mock_email_valid.return_value = True
        mock_db.side_effect = [
            [],  # Username doesn't exist
            [('existing@example.com',)]  # Email exists
        ]
        
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'password': 'Test123!',
            'confirmation': 'Test123!',
            'email': 'existing@example.com'
        })
        assert response.status_code == 400
        assert 'déjà associée' in response.data.decode()
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.is_valid_email')
    @patch('auth.routes.generate_password_hash')
    @patch('auth.routes.generate_reset_token')
    @patch('auth.routes.log_user_action')
    def test_register_success(self, mock_log, mock_token, mock_hash, mock_email_valid, mock_db, client):
        """Test inscription réussie"""
        mock_email_valid.return_value = True
        mock_hash.return_value = 'hashed_password'
        mock_token.return_value = 'reset_token'
        mock_db.side_effect = [
            [],  # Username doesn't exist
            [],  # Email doesn't exist
            None,  # Insert user
            [(1,)],  # Get user ID
            None,  # Insert login attempts
        ]
        
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'password': 'Test123!',
            'confirmation': 'Test123!',
            'email': 'new@example.com'
        })
        
        # Vérifier la redirection vers l'index
        assert response.status_code == 302
        assert 'Inscription réussie' in response.location or '/' in response.location
        
        # Vérifier que la session contient l'utilisateur
        with client.session_transaction() as sess:
            assert sess.get('user_id') == 1
            assert sess.get('username') == 'newuser'


class TestAuthLogout:
    """Tests pour la route de déconnexion"""
    
    def test_logout_clears_session(self, client, authenticated_user):
        """Test que la déconnexion vide la session"""
        response = client.get('/auth/logout')
        assert response.status_code == 200
        assert 'déconnecté' in response.data.decode()
        
        # Vérifier que la session est vide
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'username' not in sess


class TestAuthEmailManagement:
    """Tests pour la gestion des emails"""
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.is_valid_email')
    def test_add_email_success(self, mock_email_valid, mock_db, client, authenticated_user):
        """Test ajout d'email réussi"""
        mock_email_valid.return_value = True
        mock_db.side_effect = [
            [('auth_token',)],  # Get auth token
            [(1,)]  # Update email result
        ]
        
        response = client.post('/auth/add_email', data={
            'email': 'new@example.com',
            'authentication_token': 'auth_token'
        })
        
        assert response.status_code == 302
        assert 'profile' in response.location
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.is_valid_email')
    def test_update_email_success(self, mock_email_valid, mock_db, client, authenticated_user):
        """Test modification d'email réussie"""
        mock_email_valid.return_value = True
        mock_db.side_effect = [
            [('auth_token',)],  # Get auth token
            [],  # Email not used by other user
            [('old@example.com',)],  # Current email
            None,  # Update email
            None  # Delete reset tokens
        ]
        
        response = client.post('/auth/update_email', data={
            'email': 'updated@example.com',
            'authentication_token': 'auth_token'
        })
        
        assert response.status_code == 302
        assert 'profile' in response.location
    
    @patch('auth.routes.db_request')
    def test_remove_email_success(self, mock_db, client, authenticated_user):
        """Test suppression d'email réussie"""
        mock_db.side_effect = [
            [('auth_token',)],  # Get auth token
            [('current@example.com',)],  # Current email
            None,  # Update email to NULL
            None  # Delete reset tokens
        ]
        
        response = client.post('/auth/remove_email', data={
            'confirm_remove': 'true',
            'authentication_token': 'auth_token'
        })
        
        assert response.status_code == 302
        assert 'profile' in response.location


class TestAuthPasswordReset:
    """Tests pour la réinitialisation de mot de passe"""
    
    def test_forgot_password_get(self, client):
        """Test que GET /auth/forgot_password retourne le template"""
        response = client.get('/auth/forgot_password')
        assert response.status_code == 200
        assert b'email' in response.data.lower()
    
    @patch('auth.routes.is_valid_email')
    def test_forgot_password_invalid_email(self, mock_email_valid, client):
        """Test demande avec email invalide"""
        mock_email_valid.return_value = False
        
        response = client.post('/auth/forgot_password', data={
            'email': 'invalid-email'
        })
        assert response.status_code == 400
        assert 'email valide' in response.data.decode()
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.is_valid_email')
    def test_forgot_password_user_not_found(self, mock_email_valid, mock_db, client):
        """Test demande avec email non trouvé"""
        mock_email_valid.return_value = True
        mock_db.return_value = []  # User not found
        
        response = client.post('/auth/forgot_password', data={
            'email': 'notfound@example.com'
        })
        assert response.status_code == 200
        assert 'instructions' in response.data.decode()
    
    @patch('auth.routes.db_request')
    @patch('auth.routes.is_valid_email')
    @patch('auth.routes.generate_reset_token')
    @patch('auth.routes.send_reset_email')
    def test_forgot_password_success(self, mock_send_email, mock_token, mock_email_valid, mock_db, client):
        """Test demande de réinitialisation réussie"""
        mock_email_valid.return_value = True
        mock_token.return_value = 'reset_token'
        mock_send_email.return_value = True
        mock_db.side_effect = [
            [(1, 'testuser', 'test@example.com')],  # User found
            None,  # Delete old tokens
            None   # Insert new token
        ]
        
        response = client.post('/auth/forgot_password', data={
            'email': 'test@example.com'
        })
        assert response.status_code == 200
        assert 'instructions' in response.data.decode()
    
    @patch('auth.routes.db_request')
    def test_reset_password_invalid_token(self, mock_db, client):
        """Test réinitialisation avec token invalide"""
        mock_db.return_value = []  # Token not found
        
        response = client.get('/auth/reset_password/invalid_token')
        assert response.status_code == 400
        assert 'invalide' in response.data.decode()
    
    @patch('auth.routes.db_request')
    def test_reset_password_expired_token(self, mock_db, client):
        """Test réinitialisation avec token expiré"""
        # Token expiré
        expired_time = datetime.now() - timedelta(hours=2)
        mock_db.return_value = [(1, 1, 'testuser', expired_time, False)]
        
        response = client.get('/auth/reset_password/expired_token')
        assert response.status_code == 400
        assert 'expiré' in response.data.decode()
    
    @patch('auth.routes.db_request')
    def test_reset_password_success(self, mock_db, client):
        """Test réinitialisation réussie"""
        # Token valide
        future_time = datetime.now() + timedelta(hours=1)
        mock_db.side_effect = [
            [(1, 1, 'testuser', future_time, False)],  # Valid token
            None,  # Update password
            [(1,)],  # Mark token as used
            None   # Delete used tokens
        ]
        
        response = client.post('/auth/reset_password/valid_token', data={
            'password': 'NewPass123!',
            'confirmation': 'NewPass123!'
        })
        
        assert response.status_code == 200
        assert 'réinitialisé avec succès' in response.data.decode()


class TestAuthDeleteAccount:
    """Tests pour la suppression de compte"""
    
    @patch('auth.routes.db_request')
    def test_delete_account_success(self, mock_db, client, authenticated_user):
        """Test suppression de compte réussie"""
        mock_db.return_value = None  # Delete user
        
        response = client.get('/auth/delete_account')
        assert response.status_code == 302
        assert '/' in response.location
        
        # Vérifier que la session est vidée
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'username' not in sess
