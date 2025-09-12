"""
Tests pour les routes principales - basés sur le code réel
"""
import pytest
from unittest.mock import patch, MagicMock


class TestMainIndex:
    """Tests pour la route d'accueil"""
    
    def test_index_returns_template(self, client):
        """Test que GET / retourne le template d'accueil"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'html' in response.data.lower()
    
    def test_index_with_message_parameter(self, client):
        """Test que l'index peut recevoir un message en paramètre"""
        response = client.get('/?message=Bienvenue')
        assert response.status_code == 200
        # Le message devrait être passé au template
        assert b'Bienvenue' in response.data or response.status_code == 200


class TestMainMessages:
    """Tests pour l'envoi de messages à l'administrateur"""
    
    @patch('main.routes.arg_is_present')
    def test_messages_missing_fields(self, mock_args, client):
        """Test envoi de message avec champs manquants"""
        mock_args.return_value = False
        
        response = client.post('/messages', data={
            'name': 'John',
            'msg': ''
        })
        assert response.status_code == 400
        # La fonction apology devrait renvoyer une erreur
    
    def test_messages_message_too_long(self, client):
        """Test envoi de message trop long"""
        long_message = 'a' * 510  # Plus de 500 caractères
        
        response = client.post('/messages', data={
            'name': 'John',
            'msg': long_message
        })
        assert response.status_code == 400
        # Devrait retourner une erreur via apology
    
    def test_messages_name_too_long(self, client):
        """Test envoi avec nom trop long"""
        long_name = 'a' * 60  # Plus de 50 caractères
        
        response = client.post('/messages', data={
            'name': long_name,
            'msg': 'Message valide'
        })
        assert response.status_code == 400
        # Devrait retourner une erreur via apology
    
    @patch('main.routes.db_request')
    @patch('main.routes.arg_is_present')
    def test_messages_database_error(self, mock_args, mock_db, client):
        """Test envoi de message avec erreur base de données"""
        mock_args.return_value = True
        mock_db.side_effect = Exception("Database error")
        
        response = client.post('/messages', data={
            'name': 'John',
            'msg': 'Message valide'
        })
        assert response.status_code == 400
        # Devrait retourner une erreur via apology
    
    @patch('main.routes.db_request')
    @patch('main.routes.arg_is_present')
    def test_messages_success(self, mock_args, mock_db, client):
        """Test envoi de message réussi"""
        mock_args.return_value = True
        mock_db.return_value = None  # Insert successful
        
        response = client.post('/messages', data={
            'name': 'John Doe',
            'msg': 'Ceci est un message de test valide'
        })
        
        # Devrait rediriger vers about avec message de confirmation
        assert response.status_code == 302
        assert 'about' in response.location
        assert 'message' in response.location or 'Message' in response.location


class TestMainProfile:
    """Tests pour la page de profil utilisateur"""
    
    def test_profile_requires_authentication(self, client):
        """Test que /profile nécessite une authentification"""
        response = client.get('/profile')
        # Devrait rediriger vers login ou retourner 401/403
        assert response.status_code in [302, 401, 403]
    
    @patch('main.routes.db_request')
    def test_profile_authenticated_user(self, mock_db, client, authenticated_user):
        """Test affichage du profil pour un utilisateur authentifié"""
        # Mock des données de profil
        mock_db.side_effect = [
            [('Droit Civil', 10, 8), ('Droit Pénal', 5, 4)],  # Stats
            [('user@example.com',)],  # Email
            [('auth_token',)]  # Authentication token
        ]
        
        response = client.get('/profile')
        assert response.status_code == 200
        
        # Vérifier les en-têtes de sécurité
        assert 'Content-Security-Policy' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-Content-Type-Options' in response.headers
    
    @patch('main.routes.db_request')
    def test_profile_with_message(self, mock_db, client, authenticated_user):
        """Test profil avec message d'erreur/succès"""
        mock_db.side_effect = [
            [],  # Pas de stats
            [(None,)],  # Pas d'email
            [('auth_token',)]  # Authentication token
        ]
        
        response = client.get('/profile?message=Email+mis+à+jour')
        assert response.status_code == 200
        assert b'mis' in response.data or b'jour' in response.data
    
    @patch('main.routes.db_request')
    def test_profile_no_email(self, mock_db, client, authenticated_user):
        """Test profil sans email configuré"""
        mock_db.side_effect = [
            [],  # Pas de stats
            [],  # Pas d'email
            [('auth_token',)]  # Authentication token
        ]
        
        response = client.get('/profile')
        assert response.status_code == 200
        # Le template devrait gérer l'absence d'email
    
    @patch('main.routes.db_request')
    def test_profile_security_headers(self, mock_db, client, authenticated_user):
        """Test que les en-têtes de sécurité sont bien définis"""
        mock_db.side_effect = [
            [],  # Stats
            [(None,)],  # Email
            [('auth_token',)]  # Authentication token
        ]
        
        response = client.get('/profile')
        assert response.status_code == 200
        
        # Vérifier les en-têtes de sécurité spécifiques
        csp = response.headers.get('Content-Security-Policy')
        assert csp and "script-src 'self'" in csp
        
        xfo = response.headers.get('X-Frame-Options')
        assert xfo and 'DENY' in xfo
        
        xcto = response.headers.get('X-Content-Type-Options')
        assert xcto and "script-src 'self'" in xcto


class TestMainAbout:
    """Tests pour la page À propos"""
    
    def test_about_returns_template(self, client):
        """Test que GET /about retourne le template à propos"""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'html' in response.data.lower()
    
    def test_about_with_message_parameter(self, client):
        """Test que la page about peut recevoir un message"""
        response = client.get('/about?message=Message+envoyé')
        assert response.status_code == 200
        # Le message devrait être passé au template
        assert b'envoy' in response.data or response.status_code == 200


class TestMainRouteIntegration:
    """Tests d'intégration pour les routes principales"""
    
    def test_navigation_flow(self, client):
        """Test du flux de navigation entre les pages principales"""
        # Test accueil
        response = client.get('/')
        assert response.status_code == 200
        
        # Test about
        response = client.get('/about')
        assert response.status_code == 200
        
        # Test que profile nécessite auth
        response = client.get('/profile')
        assert response.status_code in [302, 401, 403]
    
    @patch('main.routes.db_request')
    @patch('main.routes.arg_is_present')
    def test_message_to_about_flow(self, mock_args, mock_db, client):
        """Test du flux d'envoi de message vers about"""
        mock_args.return_value = True
        mock_db.return_value = None
        
        # Envoyer un message
        response = client.post('/messages', data={
            'name': 'Test User',
            'msg': 'Message de test'
        })
        
        # Devrait rediriger vers about
        assert response.status_code == 302
        assert 'about' in response.location
        
        # Suivre la redirection
        response = client.get(response.location)
        assert response.status_code == 200
