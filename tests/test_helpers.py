"""
Tests pour les fonctions helpers - basés sur le code réel
"""
import pytest
from unittest.mock import patch, MagicMock, call
import psycopg2
from psycopg2 import pool
import os
from flask import session, request


class TestConnectionPool:
    """Tests pour la gestion du pool de connexions"""
    
    @patch('helpers.core.psycopg2.pool.ThreadedConnectionPool')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'})
    def test_initialize_db_pool_success(self, mock_pool_class):
        """Test initialisation réussie du pool de connexions"""
        from helpers.core import initialize_db_pool, _connection_pool
        
        # Reset global pool
        import helpers.core
        helpers.core._connection_pool = None
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        initialize_db_pool()
        
        mock_pool_class.assert_called_once_with(
            minconn=2,
            maxconn=10,
            dsn='postgresql://test:test@localhost/test'
        )
    
    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_db_pool_no_url(self):
        """Test initialisation du pool sans DATABASE_URL"""
        from helpers.core import initialize_db_pool
        
        # Reset global pool
        import helpers.core
        helpers.core._connection_pool = None
        
        with pytest.raises(Exception, match="DATABASE_URL environment variable is not set"):
            initialize_db_pool()
    
    @patch('helpers.core.psycopg2.pool.ThreadedConnectionPool')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'})
    def test_initialize_db_pool_connection_error(self, mock_pool_class):
        """Test initialisation du pool avec erreur de connexion"""
        from helpers.core import initialize_db_pool
        
        # Reset global pool
        import helpers.core
        helpers.core._connection_pool = None
        
        mock_pool_class.side_effect = psycopg2.OperationalError("Connection failed")
        
        with pytest.raises(psycopg2.OperationalError):
            initialize_db_pool()
    
    @patch('helpers.core._connection_pool')
    def test_get_connection_success(self, mock_pool):
        """Test récupération d'une connexion du pool"""
        from helpers.core import get_connection
        
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        
        result = get_connection()
        
        assert result == mock_conn
        mock_pool.getconn.assert_called_once()
    
    @patch('helpers.core.initialize_db_pool')
    def test_get_connection_initializes_pool_if_none(self, mock_init):
        """Test que get_connection initialise le pool s'il n'existe pas"""
        from helpers.core import get_connection
        
        # Reset global pool
        import helpers.core
        helpers.core._connection_pool = None
        
        mock_pool = MagicMock()
        mock_init.side_effect = lambda: setattr(helpers.core, '_connection_pool', mock_pool)
        
        get_connection()
        
        mock_init.assert_called_once()
    
    @patch('helpers.core._connection_pool')
    def test_return_connection(self, mock_pool):
        """Test retour d'une connexion au pool"""
        from helpers.core import return_connection
        
        mock_conn = MagicMock()
        
        return_connection(mock_conn)
        
        mock_pool.putconn.assert_called_once_with(mock_conn)


class TestLoginRequired:
    """Tests pour le décorateur login_required"""
    
    def test_login_required_with_authenticated_user(self, test_app, authenticated_user):
        """Test login_required avec utilisateur authentifié"""
        from helpers.core import login_required
        
        @login_required
        def test_route():
            return "Success"
        
        with test_app.test_request_context():
            with test_app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                
                result = test_route()
                assert result == "Success"
    
    def test_login_required_without_authentication(self, test_app):
        """Test login_required sans authentification"""
        from helpers.core import login_required
        
        @login_required
        def test_route():
            return "Success"
        
        with test_app.test_request_context('/protected'):
            result = test_route()
            
            # Devrait rediriger vers login
            assert result.status_code == 302
            assert 'login' in result.location
            assert 'next=' in result.location


class TestUtilityFunctions:
    """Tests pour les fonctions utilitaires"""
    
    def test_capitalize_first_letter_normal_text(self):
        """Test capitalisation normale"""
        from helpers.core import capitalize_first_letter
        
        assert capitalize_first_letter("hello") == "Hello"
        assert capitalize_first_letter("HELLO") == "HELLO"
        assert capitalize_first_letter("hELLO") == "HELLO"
    
    def test_capitalize_first_letter_empty_text(self):
        """Test capitalisation avec texte vide"""
        from helpers.core import capitalize_first_letter
        
        assert capitalize_first_letter("") == ""
        assert capitalize_first_letter(None) is None
    
    def test_capitalize_first_letter_number_start(self):
        """Test capitalisation avec nombre au début"""
        from helpers.core import capitalize_first_letter
        
        assert capitalize_first_letter("123abc") == "123abc"
        assert capitalize_first_letter("5test") == "5test"
    
    def test_clean_arg_normal_text(self):
        """Test nettoyage d'argument normal"""
        from helpers.core import clean_arg
        
        assert clean_arg("  hello  ") == "Hello"
        assert clean_arg("test") == "Test"
    
    def test_clean_arg_empty_or_none(self):
        """Test nettoyage d'argument vide ou None"""
        from helpers.core import clean_arg
        
        assert clean_arg("") == ""
        assert clean_arg(None) is None
        assert clean_arg("   ") == ""


class TestApology:
    """Tests pour la fonction apology"""
    
    def test_apology_default_code(self, test_app):
        """Test apology avec code par défaut"""
        from helpers.core import apology
        
        with test_app.test_request_context():
            result = apology("Test error message")
            
            assert result[1] == 400  # Code par défaut
            assert "Test error message" in str(result[0])
    
    def test_apology_custom_code(self, test_app):
        """Test apology avec code personnalisé"""
        from helpers.core import apology
        
        with test_app.test_request_context():
            result = apology("Custom error", 500)
            
            assert result[1] == 500
            assert "Custom error" in str(result[0])


class TestArgumentValidation:
    """Tests pour la validation d'arguments"""
    
    def test_arg_is_present_all_present(self):
        """Test arg_is_present avec tous les arguments présents"""
        from helpers.core import arg_is_present
        
        assert arg_is_present(["value1", "value2", "value3"]) == True
        assert arg_is_present(["test"]) == True
    
    def test_arg_is_present_some_missing(self):
        """Test arg_is_present avec arguments manquants"""
        from helpers.core import arg_is_present
        
        assert arg_is_present(["value1", None, "value3"]) == False
        assert arg_is_present(["value1", "", "value3"]) == False
        assert arg_is_present([None]) == False
    
    def test_arg_is_present_empty_list(self):
        """Test arg_is_present avec liste vide"""
        from helpers.core import arg_is_present
        
        assert arg_is_present([]) == True  # Liste vide devrait retourner True


class TestDatabaseRequest:
    """Tests pour db_request"""
    
    @patch('helpers.core.get_connection')
    def test_db_request_fetch_true(self, mock_get_conn):
        """Test db_request avec fetch=True"""
        from helpers.core import db_request
        
        # Mock de la connexion et du curseur
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('result1',), ('result2',)]
        mock_get_conn.return_value = mock_conn
        
        result = db_request("SELECT * FROM test", fetch=True)
        
        assert result == [('result1',), ('result2',)]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test", None)
        mock_cursor.fetchall.assert_called_once()
    
    @patch('helpers.core.get_connection')
    def test_db_request_fetch_false(self, mock_get_conn):
        """Test db_request avec fetch=False"""
        from helpers.core import db_request
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = db_request("INSERT INTO test VALUES (%s)", ("value",), fetch=False)
        
        assert result is None
        mock_cursor.execute.assert_called_once_with("INSERT INTO test VALUES (%s)", ("value",))
        mock_conn.commit.assert_called_once()
    
    @patch('helpers.core.get_connection')
    def test_db_request_with_parameters(self, mock_get_conn):
        """Test db_request avec paramètres"""
        from helpers.core import db_request
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('result',)]
        mock_get_conn.return_value = mock_conn
        
        result = db_request("SELECT * FROM test WHERE id = %s", (123,))
        
        assert result == [('result',)]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id = %s", (123,))


class TestTokenGeneration:
    """Tests pour la génération de tokens"""
    
    def test_generate_reset_token(self):
        """Test génération de token de réinitialisation"""
        from helpers.core import generate_reset_token
        
        token = generate_reset_token()
        
        assert isinstance(token, str)
        assert len(token) > 10  # Token devrait être assez long
    
    def test_generate_reset_token_unique(self):
        """Test que les tokens générés sont uniques"""
        from helpers.core import generate_reset_token
        
        token1 = generate_reset_token()
        token2 = generate_reset_token()
        
        assert token1 != token2


class TestEmailValidation:
    """Tests pour la validation d'email"""
    
    def test_is_valid_email_valid_addresses(self):
        """Test validation avec adresses email valides"""
        from helpers.core import is_valid_email
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        for email in valid_emails:
            assert is_valid_email(email) == True, f"'{email}' should be valid"
    
    def test_is_valid_email_invalid_addresses(self):
        """Test validation avec adresses email invalides"""
        from helpers.core import is_valid_email
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..name@example.com",
            "user name@example.com",
            ""
        ]
        
        for email in invalid_emails:
            assert is_valid_email(email) == False, f"'{email}' should be invalid"


class TestEmailSending:
    """Tests pour l'envoi d'emails"""
    
    @patch('helpers.core.current_app')
    def test_send_reset_email_success(self, mock_app):
        """Test envoi d'email de réinitialisation réussi"""
        from helpers.core import send_reset_email
        
        mock_mail = MagicMock()
        mock_app.extensions = {'mail': mock_mail}
        
        result = send_reset_email("test@example.com", "testuser", "reset_token")
        
        assert result == True
        mock_mail.send.assert_called_once()
    
    @patch('helpers.core.current_app')
    def test_send_reset_email_failure(self, mock_app):
        """Test envoi d'email de réinitialisation échoué"""
        from helpers.core import send_reset_email
        
        mock_mail = MagicMock()
        mock_mail.send.side_effect = Exception("SMTP Error")
        mock_app.extensions = {'mail': mock_mail}
        
        result = send_reset_email("test@example.com", "testuser", "reset_token")
        
        assert result == False
import pytest
from unittest.mock import patch, MagicMock
from helpers.core import (
    login_required, 
    apology, 
    arg_is_present, 
    clean_arg, 
    capitalize_first_letter,
    is_valid_email,
    generate_reset_token
)
from helpers.monitoring import MetricsCollector
from flask import session


class TestHelperFunctions:
    """Tests des fonctions utilitaires"""
    
    def test_arg_is_present_with_valid_args(self):
        """Test arg_is_present avec arguments valides"""
        args = ["test", "value", 123]
        assert arg_is_present(args) == True
    
    def test_arg_is_present_with_none_values(self):
        """Test arg_is_present avec valeurs None"""
        args = ["test", None, "value"]
        assert arg_is_present(args) == False
    
    def test_arg_is_present_with_empty_strings(self):
        """Test arg_is_present avec chaînes vides"""
        args = ["test", "", "value"]
        assert arg_is_present(args) == False
    
    def test_clean_arg_strips_whitespace(self):
        """Test clean_arg supprime les espaces"""
        assert clean_arg("  test  ") == "test"
        assert clean_arg("\n\tvalue\n") == "value"
    
    def test_capitalize_first_letter(self):
        """Test capitalisation première lettre"""
        assert capitalize_first_letter("hello") == "Hello"
        assert capitalize_first_letter("WORLD") == "WORLD"
        assert capitalize_first_letter("") == ""
    
    def test_is_valid_email_with_valid_emails(self):
        """Test validation email avec emails valides"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        for email in valid_emails:
            assert is_valid_email(email) == True
    
    def test_is_valid_email_with_invalid_emails(self):
        """Test validation email avec emails invalides"""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            ""
        ]
        for email in invalid_emails:
            assert is_valid_email(email) == False
    
    def test_generate_reset_token_length(self):
        """Test génération token de réinitialisation"""
        token = generate_reset_token()
        assert len(token) > 20  # Doit être suffisamment long
        assert isinstance(token, str)
    
    def test_generate_reset_token_uniqueness(self):
        """Test unicité des tokens générés"""
        tokens = [generate_reset_token() for _ in range(10)]
        assert len(set(tokens)) == 10  # Tous uniques


class TestMetricsCollector:
    """Tests du collecteur de métriques"""
    
    def test_increment_metric(self):
        """Test incrémentation métrique"""
        metrics = MetricsCollector()
        
        metrics.increment("test_counter")
        metrics.increment("test_counter")
        
        assert metrics.get_metrics()["test_counter:"] == 2
    
    def test_gauge_metric(self):
        """Test métrique gauge"""
        metrics = MetricsCollector()
        
        metrics.gauge("active_users", 150)
        metrics.gauge("active_users", 175)  # Override
        
        assert metrics.get_metrics()["active_users:"] == 175
    
    def test_timer_metric(self):
        """Test métrique timer"""
        metrics = MetricsCollector()
        
        metrics.timer("request_duration", 0.123)
        metrics.timer("request_duration", 0.456)
        
        timers = metrics.get_metrics()["request_duration_duration:"]
        assert len(timers) == 2
        assert 0.123 in timers
        assert 0.456 in timers
    
    def test_metrics_with_tags(self):
        """Test métriques avec tags"""
        metrics = MetricsCollector()
        
        metrics.increment("http_requests", tags="status_200")
        metrics.increment("http_requests", tags="status_404")
        
        data = metrics.get_metrics()
        assert data["http_requests:status_200"] == 1
        assert data["http_requests:status_404"] == 1
    
    def test_metrics_reset(self):
        """Test reset des métriques"""
        metrics = MetricsCollector()
        
        metrics.increment("test_metric")
        assert len(metrics.get_metrics()) > 0
        
        metrics.reset()
        assert len(metrics.get_metrics()) == 0


@pytest.mark.integration
class TestDatabaseHelpers:
    """Tests d'intégration avec la base de données"""
    
    @patch('helpers.core.get_connection')
    def test_db_request_success(self, mock_get_connection):
        """Test requête DB réussie"""
        # Mock de la connexion
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('result1',), ('result2',)]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        from helpers.core import db_request
        result = db_request("SELECT * FROM test", fetch=True)
        
        # Vérifications
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test", ())
        mock_cursor.fetchall.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        assert result == [('result1',), ('result2',)]
    
    @patch('helpers.core.get_connection')
    def test_db_request_with_params(self, mock_get_connection):
        """Test requête DB avec paramètres"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        from helpers.core import db_request
        db_request("SELECT * FROM users WHERE id = %s", (123,), fetch=False)
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", (123,))
    
    @patch('helpers.core.get_connection')
    def test_db_request_error_handling(self, mock_get_connection):
        """Test gestion d'erreur DB"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB Error")
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        from helpers.core import db_request
        result = db_request("INVALID SQL", fetch=True)
        
        # Doit retourner une page d'erreur
        assert result is not None  # apology() retourne quelque chose
        mock_conn.close.assert_called_once()  # Connexion fermée même en cas d'erreur


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
