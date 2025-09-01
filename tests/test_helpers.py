"""
Tests unitaires pour les fonctions helpers
"""
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
