from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from flask_session import Session
from flask_cors import CORS
from flask_mail import Mail
import os

# Import du système de monitoring
from helpers.monitoring import setup_logging, setup_error_handling, setup_request_monitoring, health_check, log_user_action
from helpers.sentry_simple import init_sentry
from helpers.core import initialize_db_pool

print("=== DÉMARRAGE DE L'APPLICATION ===")
print(f"DATABASE_URL is {'set' if os.environ.get('DATABASE_URL') else 'NOT SET'}")
print(f"SECRET_KEY is {'set' if os.environ.get('SECRET_KEY') else 'NOT SET'}")

# Import blueprints
from admin.routes import admin_bp
from auth.routes import auth_bp
from main.routes import main_bp
from quiz.routes import quiz_bp

app = Flask(__name__)
CORS(app)

# Configurer le monitoring dès que possible
app_logger = setup_logging(app)
app_logger.info("Application Flask initialisée")

# Initialiser Sentry pour monitoring d'erreurs
init_sentry(app)

# Configure secret key 
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_très_secrète_123') 
app_logger.info("Configuration de la clé secrète terminée")

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["ADMIN_USER_ID"] = os.environ.get('ADMIN_USER_ID')

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# LOGS DE DEBUGGING
print("=== CONFIGURATION EMAIL ===")
print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
print(f"ADMIN_USER_ID: {app.config['ADMIN_USER_ID']}")
print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
print(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"MAIL_PASSWORD: {'***set***' if app.config['MAIL_PASSWORD'] else 'NOT SET'}")
print(f"MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")

Session(app)
mail = Mail(app)

# Make mail available to blueprints
app.mail = mail

# Initialiser le pool de connexions base de données
try:
    initialize_db_pool()
    app_logger.info("Pool de connexions base de données initialisé")
except Exception as e:
    app_logger.error(f"Erreur lors de l'initialisation du pool DB: {e}", exc_info=True)

# Configurer le monitoring des erreurs et requêtes
setup_error_handling(app)
setup_request_monitoring(app)

# Route de health check
@app.route('/health')
def health():
    return jsonify(health_check())

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(quiz_bp)

app_logger.info("Tous les blueprints enregistrés")

if __name__ == '__main__':
    print("=== LANCEMENT DE FLASK ===")
    # Pour production, utiliser Gunicorn
    # Pour développement local uniquement
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')