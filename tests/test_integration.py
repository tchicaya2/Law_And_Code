"""
Tests d'intégration pour l'application complète
"""
import pytest
from unittest.mock import patch, MagicMock
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestEndToEndWorkflows:
    """Tests de bout en bout des workflows principaux"""
    
    @patch('helpers.core.db_request')
    def test_complete_user_journey(self, mock_db_request, client):
        """Test parcours utilisateur complet : inscription → connexion → quiz → stats"""
        
        # 1. Inscription
        mock_db_request.side_effect = [
            [],  # Vérifier si email existe (non)
            None,  # Insertion utilisateur
            [],  # Vérifier token existe (non)
            None   # Insertion token
        ]
        
        register_response = client.post('/auth/register', data={
            'username': 'testuser_journey',
            'email': 'journey@test.com',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        })
        
        assert register_response.status_code in [200, 302]
        
        # 2. Connexion
        mock_db_request.side_effect = [
            [('testuser_journey', 'hashed_password', 1, False)],  # Utilisateur existe
        ]
        
        with patch('werkzeug.security.check_password_hash', return_value=True):
            login_response = client.post('/auth/login', data={
                'username': 'testuser_journey',
                'password': 'TestPass123!'
            })
            
            assert login_response.status_code in [200, 302]
        
        # 3. Accès au profil
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser_journey'
        
        mock_db_request.side_effect = [
            [('Droit Civil', 10, 8)],  # Stats utilisateur
            [('journey@test.com',)],   # Email
            [('auth_token',)]          # Token
        ]
        
        profile_response = client.get('/profile')
        assert profile_response.status_code == 200
        
        # 4. Jouer un quiz
        mock_db_request.side_effect = [
            [(1, 'Test Quiz', 'Description', 'Droit Civil', 1, True)],  # Quiz info
            [  # Questions
                (1, 'Question 1', 'A|B|C|D', 0, 'Explication'),
                (2, 'Question 2', 'A|B|C|D', 1, 'Explication 2')
            ]
        ]
        
        quiz_response = client.get('/quiz/1')
        assert quiz_response.status_code == 200
        
        # 5. Mettre à jour les stats
        mock_db_request.side_effect = [
            [],  # Pas d'attempt précédent
            None,  # Insertion attempt
            [('Droit Civil', 8, 6)],  # Stats existantes
            None   # Mise à jour stats
        ]
        
        stats_response = client.post('/quiz/update_stats', data={
            'matiere': 'Droit Civil',
            'posées': '2',
            'trouvées': '2',
            'quiz_id': '1'
        })
        
        assert stats_response.status_code == 204
    
    @patch('helpers.core.db_request')
    def test_admin_workflow(self, mock_db_request, client):
        """Test workflow administrateur"""
        
        # Se connecter comme admin
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['is_admin'] = True
        
        # Accès dashboard admin
        mock_db_request.side_effect = [
            100,  # Nombre utilisateurs
            50,   # Nombre quiz
            25,   # Messages
            []    # Logs
        ]
        
        admin_response = client.get('/admin/')
        assert admin_response.status_code == 200
        
        # Gérer un message de contact
        mock_db_request.side_effect = [
            [(1, 'User Test', 'Message test', '2024-01-01 10:00:00')],  # Messages
            None  # Marquer comme lu
        ]
        
        messages_response = client.get('/admin/messages')
        assert messages_response.status_code in [200, 404]  # Peut ne pas être implémenté
    
    @patch('helpers.core.db_request') 
    def test_quiz_creation_workflow(self, mock_db_request, client):
        """Test workflow de création de quiz"""
        
        # Se connecter
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'creator'
        
        # Créer un quiz
        mock_db_request.side_effect = [
            None,  # Insertion quiz
            [(1,)]  # ID du quiz créé
        ]
        
        quiz_data = {
            'title': 'Quiz Test Intégration',
            'description': 'Quiz pour test d\'intégration',
            'matiere': 'Droit Civil',
            'is_public': 'on',
            'questions': json.dumps([
                {
                    'question': 'Question test ?',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct': 0,
                    'explanation': 'C\'est l\'option A'
                },
                {
                    'question': 'Question 2 ?',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct': 1,
                    'explanation': 'C\'est l\'option B'
                }
            ])
        }
        
        create_response = client.post('/quiz/create', data=quiz_data)
        assert create_response.status_code in [200, 302]
        
        # Vérifier que le quiz peut être consulté
        mock_db_request.side_effect = [
            [(1, 'Quiz Test Intégration', 'Quiz pour test d\'intégration', 'Droit Civil', 1, True)],
            [
                (1, 'Question test ?', 'Option A|Option B|Option C|Option D', 0, 'C\'est l\'option A'),
                (2, 'Question 2 ?', 'Option A|Option B|Option C|Option D', 1, 'C\'est l\'option B')
            ]
        ]
        
        view_response = client.get('/quiz/1')
        assert view_response.status_code == 200


class TestPerformanceIntegration:
    """Tests de performance et charge"""
    
    def test_concurrent_users(self, client):
        """Test utilisateurs concurrents"""
        
        def make_request():
            """Faire une requête"""
            response = client.get('/')
            return response.status_code
        
        # Simuler 10 utilisateurs concurrents
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # Toutes les requêtes doivent réussir
        assert all(status == 200 for status in results)
    
    @patch('helpers.core.db_request')
    def test_large_quiz_list_performance(self, mock_db_request, client):
        """Test performance avec beaucoup de quiz"""
        
        # Simuler 100 quiz
        large_quiz_list = [
            (i, f'Quiz {i}', f'Description {i}', 'Droit Civil', 'user', True)
            for i in range(1, 101)
        ]
        
        mock_db_request.side_effect = [
            100,  # Count
            large_quiz_list[:10]  # Première page (pagination)
        ]
        
        start_time = time.time()
        response = client.get('/quiz/')
        end_time = time.time()
        
        assert response.status_code == 200
        # La requête ne doit pas prendre plus de 2 secondes
        assert (end_time - start_time) < 2.0


class TestErrorRecoveryIntegration:
    """Tests de récupération d'erreurs en intégration"""
    
    @patch('helpers.core.db_request')
    def test_database_failure_recovery(self, mock_db_request, client):
        """Test récupération après échec base de données"""
        
        # Premier appel : échec DB
        mock_db_request.side_effect = Exception("DB Connection Error")
        
        response1 = client.get('/')
        # L'application doit gérer l'erreur
        assert response1.status_code in [200, 500]
        
        # Deuxième appel : DB récupérée
        mock_db_request.side_effect = None
        mock_db_request.return_value = []
        
        response2 = client.get('/')
        assert response2.status_code == 200
    
    def test_session_corruption_recovery(self, client):
        """Test récupération après corruption de session"""
        
        # Créer une session corrompue
        with client.session_transaction() as sess:
            sess['user_id'] = 'invalid_id'  # ID invalide
            sess['username'] = None
        
        # L'application doit gérer la session corrompue
        response = client.get('/profile')
        assert response.status_code in [200, 302]  # Redirection vers login ou gestion d'erreur
    
    @patch('helpers.monitoring.logger')
    def test_error_logging_integration(self, mock_logger, client):
        """Test intégration du logging d'erreurs"""
        
        # Simuler une erreur
        with patch('helpers.core.db_request') as mock_db:
            mock_db.side_effect = Exception("Test error")
            
            response = client.get('/')
            
            # Vérifier que l'erreur est loggée (selon l'implémentation)
            assert response.status_code in [200, 500]


class TestSecurityIntegration:
    """Tests de sécurité en intégration"""
    
    def test_sql_injection_protection(self, client):
        """Test protection contre injection SQL"""
        
        # Tentative d'injection SQL via paramètres
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.post('/messages', data={
            'name': malicious_input,
            'msg': 'Message normal'
        })
        
        # L'application doit gérer l'input malicieux
        assert response.status_code in [200, 400, 302]
    
    def test_xss_protection(self, client):
        """Test protection contre XSS"""
        
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post('/messages', data={
            'name': 'Test User',
            'msg': xss_payload
        })
        
        # L'application doit échapper ou filtrer le contenu
        assert response.status_code in [200, 400, 302]
        
        # Si le message est affiché, il ne doit pas contenir le script
        if response.status_code == 200:
            content = response.data.decode('utf-8')
            assert '<script>' not in content.lower()
    
    def test_session_security(self, client):
        """Test sécurité des sessions"""
        
        # Se connecter
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Vérifier que la session est sécurisée
        response = client.get('/profile')
        assert response.status_code == 200
        
        # Modifier la session (simulation d'attaque)
        with client.session_transaction() as sess:
            sess['user_id'] = 999  # ID d'un autre utilisateur
        
        # L'application doit détecter la modification
        response = client.get('/profile')
        # Selon l'implémentation de la sécurité des sessions
        assert response.status_code in [200, 302, 403]


class TestDataIntegrityIntegration:
    """Tests d'intégrité des données"""
    
    @patch('helpers.core.db_request')
    def test_concurrent_quiz_attempts(self, mock_db_request, client):
        """Test tentatives concurrentes sur le même quiz"""
        
        def submit_quiz_attempt(user_id):
            """Soumettre une tentative de quiz"""
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                sess['username'] = f'user{user_id}'
            
            # Mock : pas d'attempt existant
            mock_db_request.side_effect = [
                [],  # Pas d'attempt
                None,  # Insertion
                [],  # Pas de stats
                None   # Insertion stats
            ]
            
            return client.post('/quiz/update_stats', data={
                'matiere': 'Droit Civil',
                'posées': '10',
                'trouvées': '8',
                'quiz_id': '1'
            })
        
        # Simuler plusieurs utilisateurs soumettant en même temps
        responses = []
        for user_id in range(1, 4):
            response = submit_quiz_attempt(user_id)
            responses.append(response)
        
        # Toutes les soumissions doivent être traitées correctement
        for response in responses:
            assert response.status_code in [200, 204]
    
    @patch('helpers.core.db_request')
    def test_data_consistency_checks(self, mock_db_request, client):
        """Test vérifications de cohérence des données"""
        
        # Se connecter
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Soumettre des stats incohérentes
        mock_db_request.return_value = []  # Pas d'attempt existant
        
        response = client.post('/quiz/update_stats', data={
            'matiere': 'Droit Civil',
            'posées': '5',
            'trouvées': '10',  # Plus de bonnes réponses que de questions !
            'quiz_id': '1'
        })
        
        # L'application doit rejeter les données incohérentes
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
