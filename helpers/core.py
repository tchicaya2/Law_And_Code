from flask import redirect, request, render_template, session, url_for
from functools import wraps
import psycopg2
from psycopg2 import pool
import os
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from flask import current_app
import secrets
from datetime import datetime, timedelta
import logging

# Logger pour ce module
logger = logging.getLogger('law_quiz_app.helpers')

# Connection pool global
_connection_pool = None

def initialize_db_pool():
    """Initialize the database connection pool"""
    global _connection_pool
    if _connection_pool is None:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable is not set")
        
        try:
            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,  # Minimum 2 connections
                maxconn=10, # Maximum 10 connections  
                dsn=database_url
            )
            logger.info("Database connection pool initialized successfully", extra={
                'min_connections': 2,
                'max_connections': 10
            })
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}", exc_info=True)
            raise

def get_connection():
    """Get a connection from the pool"""
    global _connection_pool
    if _connection_pool is None:
        initialize_db_pool()
    
    try:
        return _connection_pool.getconn()
    except Exception as e:
        logger.error(f"Failed to get connection from pool: {e}", exc_info=True)
        raise

def return_connection(conn):
    """Return a connection to the pool"""
    global _connection_pool
    if _connection_pool and conn:
        _connection_pool.putconn(conn)

"""  FONCTIONS UTILITAIRES  """


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            next_url = request.url # Store the current URL to redirect after login
            logger.info(f"User not logged in, redirecting to login page", extra={
                'next_url': next_url,
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent')
            })
            # next_url is used to redirect back after login
            return redirect(url_for("auth.login", next=next_url)) 
        return f(*args, **kwargs)

    return decorated_function

def capitalize_first_letter(text):
    if not text:
        return text
    return text[0].upper() + text[1:]

def clean_arg(arg):
    return capitalize_first_letter(arg).strip() if arg else None


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

def get_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable is not set")
    
    return psycopg2.connect(database_url)

def arg_is_present(args):
    # Regarde les éléments contenus dans une liste et si un élément est None, retourner False
    for arg in args:
        if not arg:
            return False
    return True

def db_request(text, params=None, fetch=True):
    """
    Execute a database request using connection pool.

    Args:
        text (str): SQL query to execute.
        params (tuple or list, optional): Parameters to pass with the SQL query. 
        Defaults to None.
        fetch (bool, optional): Whether to fetch and return results. Defaults to True.

    Returns:
        list or None: Query results if fetch is True, otherwise None.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params is None:
            params = ()
        cursor.execute(text, params)
        if fetch:
            rows = cursor.fetchall()
        else:
            rows = None # Return value is None if no fetch requested
        conn.commit()
        return rows
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erreur base de données: {e}", extra={
            'query': text[:100],  # Première partie de la requête
            'params_count': len(params) if params else 0,
            'user_id': session.get('user_id') if session else None
        }, exc_info=True)
        return apology("Une erreur s'est produite lors de la requête à la base de données.")
    finally:
        if conn:
            return_connection(conn)

def generate_reset_token():
    """Génère un token sécurisé pour la réinitialisation de mot de passe"""
    return secrets.token_urlsafe(32)

def send_reset_email(email, username, token):
    """Envoie un email de réinitialisation de mot de passe"""
    try:
        logger.info(f"Tentative d'envoi email de réinitialisation", extra={
            'email': email,
            'username': username,
            'smtp_server': current_app.config.get('MAIL_SERVER'),
            'mail_configured': bool(current_app.config.get('MAIL_PASSWORD'))
        })
        
        msg = Message(
            subject="Réinitialisation de votre mot de passe - LawAndCode",
            recipients=[email],
            html=f"""
            <h2>Réinitialisation de mot de passe</h2>
            <p>Bonjour {username},</p>
            <p>Cliquez sur le lien suivant pour réinitialiser votre mot de passe :</p>
            <p><a href="http://localhost:5000/auth/reset_password/{token}">Réinitialiser mon mot de passe</a></p>
            <p>Ce lien expire dans 1 heure.</p>
            <p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
            <br>
            <p>Cordialement,<br>L'équipe LawAndCode</p>
            """,
            body=f"Réinitialisation mot de passe - Token: {token}"
        )
        
        current_app.mail.send(msg)
        logger.info("Email de réinitialisation envoyé avec succès", extra={
            'email': email,
            'username': username
        })
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation", extra={
            'email': email,
            'username': username,
            'error_type': type(e).__name__,
            'error_message': str(e)
        }, exc_info=True)
        return False

def is_valid_email(email):
    """Valide le format d'un email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None # Ensure the email matches the pattern