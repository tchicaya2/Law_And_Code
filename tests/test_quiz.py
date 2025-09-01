"""
Tests pour les routes principales et quiz
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import session
import json


def assert_redirect(response, expected_location=None):
    """Vérifier qu'une réponse est une redirection"""
    assert response.status_code in [301, 302, 303, 307, 308]


class TestMainRoutes:
    """Tests des routes principales"""
    
    def test_homepage(self, client):
        """Test page d'accueil"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Law' in response.data or b'law' in response.data
    
    def test_about_page(self, client):
        """Test page à propos"""
        response = client.get('/about')
        assert response.status_code == 200
        # Vérifier contenu basique
        content = response.data.decode('utf-8')
        assert 'propos' in content.lower() or 'about' in content.lower()
    
    @patch('helpers.core.db_request')
    def test_contact_message_success(self, mock_db_request, client):
        """Test envoi message de contact réussi"""
        mock_db_request.return_value = None  # Insertion réussie
        
        response = client.post('/messages', data={
            'name': 'Test User',
            'msg': 'Ceci est un message de test'
        })
        
        assert_redirect(response)
        mock_db_request.assert_called_once()
    
    def test_contact_message_missing_fields(self, client):
        """Test envoi message avec champs manquants"""
        response = client.post('/messages', data={
            'name': '',
            'msg': 'Message sans nom'
        })
        
        assert response.status_code == 400
    
    def test_contact_message_too_long(self, client):
        """Test envoi message trop long"""
        long_message = 'x' * 501  # Plus de 500 caractères
        
        response = client.post('/messages', data={
            'name': 'Test User',
            'msg': long_message
        })
        
        assert response.status_code == 400
        assert 'trop long'.encode() in response.data
    
    def test_profile_requires_auth(self, client):
        """Test que la page profil nécessite une authentification"""
        response = client.get('/profile')
        assert_redirect(response, '/auth/login')
    
    @patch('helpers.core.db_request')
    def test_profile_authenticated_user(self, mock_db_request, client):
        """Test page profil pour utilisateur authentifié"""
        # Se connecter
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock des données utilisateur
        mock_db_request.side_effect = [
            [('Droit Civil', 50, 40), ('Droit Pénal', 30, 25)],  # Stats
            [('test@example.com',)],  # Email
            [('auth_token',)]  # Token
        ]
        
        response = client.get('/profile')
        assert response.status_code == 200
        
        # Vérifier que les stats sont affichées
        content = response.data.decode('utf-8')
        assert 'Droit Civil' in content
        assert 'test@example.com' in content


class TestQuizRoutes:
    """Tests des routes de quiz"""
    
    def test_quiz_list_public(self, client):
        """Test liste publique des quiz"""
        response = client.get('/quiz/')
        assert response.status_code == 200
    
    @patch('helpers.core.db_request')
    def test_quiz_list_with_data(self, mock_db_request, client):
        """Test liste des quiz avec données"""
        # Mock des quiz
        mock_db_request.side_effect = [
            50,  # Nombre total de quiz
            [  # Quiz avec pagination
                (1, 'Quiz Droit Civil', 'Description', 'Droit Civil', 'testuser', True),
                (2, 'Quiz Droit Pénal', 'Description 2', 'Droit Pénal', 'testuser2', True)
            ]
        ]
        
        response = client.get('/quiz/')
        assert response.status_code == 200
        
        content = response.data.decode('utf-8')
        assert 'Quiz Droit Civil' in content
        assert 'Quiz Droit Pénal' in content
    
    def test_quiz_list_pagination(self, client):
        """Test pagination de la liste des quiz"""
        response = client.get('/quiz/?page=2')
        assert response.status_code == 200
    
    def test_quiz_list_filtering(self, client):
        """Test filtrage par matière"""
        response = client.post('/quiz/', data={
            'matiere': 'Droit Civil',
            'quiz_type': 'public'
        })
        assert response.status_code == 200
    
    @patch('helpers.core.db_request')
    def test_quiz_detail_public(self, mock_db_request, client):
        """Test détail d'un quiz public"""
        # Mock des données du quiz
        mock_db_request.side_effect = [
            [(1, 'Test Quiz', 'Description', 'Droit Civil', 1, True)],  # Quiz info
            [  # Questions
                (1, 'Question 1', 'Option A|Option B|Option C|Option D', 0, 'Explication'),
                (2, 'Question 2', 'Option A|Option B|Option C|Option D', 1, 'Explication 2')
            ]
        ]
        
        response = client.get('/quiz/1')
        assert response.status_code == 200
        
        content = response.data.decode('utf-8')
        assert 'Test Quiz' in content
        assert 'Question 1' in content
    
    def test_quiz_detail_nonexistent(self, client):
        """Test quiz inexistant"""
        with patch('helpers.core.db_request') as mock_db:
            mock_db.return_value = []  # Quiz n'existe pas
            
            response = client.get('/quiz/999')
            assert response.status_code == 400
    
    def test_quiz_update_stats_requires_auth(self, client):
        """Test mise à jour stats nécessite authentification"""
        response = client.post('/quiz/update_stats', data={
            'matiere': 'Droit Civil',
            'posées': '10',
            'trouvées': '8',
            'quiz_id': '1'
        })
        assert_redirect(response, '/auth/login')
    
    @patch('helpers.core.db_request')
    def test_quiz_update_stats_success(self, mock_db_request, client):
        """Test mise à jour stats réussie"""
        # Se connecter
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock : pas d'attempt précédent
        mock_db_request.side_effect = [
            [],  # Pas d'attempt existant
            None,  # Insertion attempt
            [],  # Pas de stats existantes pour cette matière
            None  # Insertion nouvelles stats
        ]
        
        response = client.post('/quiz/update_stats', data={
            'matiere': 'Droit Civil',
            'posées': '10',
            'trouvées': '8',
            'quiz_id': '1'
        })
        
        assert response.status_code == 204
        assert mock_db_request.call_count >= 3
    
    @patch('helpers.core.db_request')
    def test_quiz_update_stats_existing_attempt(self, mock_db_request, client):
        """Test mise à jour stats avec attempt existant"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock : attempt déjà existant
        mock_db_request.return_value = [(1, 1, 1)]  # Attempt existe
        
        response = client.post('/quiz/update_stats', data={
            'matiere': 'Droit Civil',
            'posées': '10',
            'trouvées': '8',
            'quiz_id': '1'
        })
        
        assert response.status_code == 204
        # Ne doit pas mettre à jour si déjà joué
    
    def test_quiz_update_stats_missing_fields(self, client):
        """Test mise à jour stats avec champs manquants"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        response = client.post('/quiz/update_stats', data={
            'matiere': 'Droit Civil',
            # Manque posées, trouvées, quiz_id
        })
        
        assert response.status_code == 400


class TestQuizCreationAndManagement:
    """Tests de création et gestion des quiz"""
    
    def test_quiz_creation_requires_auth(self, client):
        """Test création quiz nécessite authentification"""
        response = client.get('/quiz/create')
        assert_redirect(response, '/auth/login')
    
    @patch('helpers.core.db_request')
    def test_quiz_creation_page(self, mock_db_request, client):
        """Test page de création de quiz"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        response = client.get('/quiz/create')
        assert response.status_code == 200
        
        content = response.data.decode('utf-8')
        assert 'créer' in content.lower() or 'create' in content.lower()
    
    @patch('helpers.core.db_request')
    def test_quiz_creation_success(self, mock_db_request, client):
        """Test création de quiz réussie"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock insertion quiz
        mock_db_request.side_effect = [
            None,  # Insertion quiz
            [(1,)]  # Récupération ID quiz
        ]
        
        quiz_data = {
            'title': 'Nouveau Quiz',
            'description': 'Description du quiz',
            'matiere': 'Droit Civil',
            'is_public': 'on',
            'questions': json.dumps([
                {
                    'question': 'Question test ?',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct': 0,
                    'explanation': 'Explication'
                }
            ])
        }
        
        response = client.post('/quiz/create', data=quiz_data)
        assert_redirect(response)


class TestQuizAPI:
    """Tests des endpoints API pour les quiz"""
    
    @patch('helpers.core.db_request')
    def test_quiz_count_api(self, mock_db_request, client):
        """Test API comptage des quiz"""
        mock_db_request.return_value = 42  # Nombre de quiz
        
        response = client.get('/quiz/count')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['count'] == 42
    
    @patch('helpers.core.db_request')
    def test_quiz_search_api(self, mock_db_request, client):
        """Test API recherche de quiz"""
        mock_db_request.return_value = [
            (1, 'Quiz Trouvé', 'Description', 'Droit Civil', 'testuser', True)
        ]
        
        response = client.get('/quiz/search?q=Civil')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['results']) == 1
        assert 'Quiz Trouvé' in data['results'][0]['title']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
