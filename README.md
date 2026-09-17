# Law and Code - Plateforme Interactive d'Apprentissage Juridique

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)


> 🎯 **Plateforme gamifiée d'apprentissage du droit** - Fusionnant technologie moderne et éducation juridique.

## 📋 Table des Matières
- [Vue d'ensemble](#-vue-densemble)
- [Fonctionnalités](#-fonctionnalités)
- [Stack Technique](#-stack-technique)
- [Installation](#-installation)
- [Déploiement](#-déploiement)
- [Architecture](#-architecture)
- [Monitoring](#-monitoring)
- [Tests](#-tests)
- [Contribution](#-contribution)

## 🎯 Vue d'ensemble

**Law and Code** est une application web moderne conçue pour les étudiants en droit, offrant une approche interactive et gamifiée pour réviser les principes juridiques fondamentaux. La plateforme permet aux utilisateurs de tester leurs connaissances via des quiz où l'objectif est d'identifier le bon arrêt de justice correspondant à un principe légal donné.

### 🔥 Objectifs du Projet
- **Innovation pédagogique** : Moderniser l'apprentissage du droit par la technologie
- **Accessibilité** : Rendre les quiz juridiques accessibles à tous
- **Community-driven** : Permettre aux utilisateurs de créer et partager du contenu

## ✨ Fonctionnalités

### 🌍 Quiz Publics
- **Accès libre** : Aucune inscription requise
- **Domaines variés** : Droit Civil, Pénal, Administratif, etc.
- **Système de likes** : Valorisation du contenu de qualité
- **Recherche avancée** : Filtres par matière et niveau

### 🔐 Quiz Privés
- **Création personnalisée** : Outils intuitifs pour créer ses propres quiz
- **Gestion de contenu** : Modification, suppression, organisation
- **Contrôle d'accès** : Public/Privé configurable

### 👤 Système Utilisateur
- **Authentification sécurisée** : Sessions Flask + hashage des mots de passe
- **Profils personnalisés** : Statistiques, liste des quiz, ajout/modification/supression email, suppression de compte 
- **Récupération mot de passe** : email avec token sécurisé via SendGrid

### 📊 Monitoring & Analytics
- **Logging structuré** : JSON logs pour analyse
- **Health checks** : Surveillance de l'état système
- **Error tracking** : Intégration Sentry
- **Métriques temps réel** : Dashboard de monitoring

## 🛠️ Stack Technique

### Backend
- **Flask 3.0** - Framework web Python moderne
- **PostgreSQL 16** - Base de données relationnelle robuste
- **Gunicorn** - Serveur WSGI pour production
- **psycopg2** - Connecteur PostgreSQL optimisé

### Frontend
- **Jinja2** - Templating engine intégré Flask
- **Bootstrap 5** - Framework CSS responsive
- **Vanilla JavaScript** - Interactions client-side
- **Font Awesome** - Iconographie moderne

### Infrastructure & DevOps
- **Docker** - Containerisation pour développement
- **Render/Railway** - Déploiement cloud
- **SendGrid** - Service email transactionnel
- **Sentry** - Monitoring d'erreurs en production

### Monitoring & Observability
- **Structured Logging** - Logs JSON pour parsing
- **Health Endpoints** - `/health` pour load balancers
- **Performance Metrics** - Temps de réponse et usage
- **Error Tracking** - Capture automatique d'exceptions

## 🚀 Installation

### Prérequis
- Python 3.13+
- PostgreSQL 16+
- Git

### Setup Local

```bash
# Cloner le repository
git clone https://github.com/ton-username/law-and-code.git
cd law-and-code

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec tes valeurs

# Lancer l'application
flask run --debug
```

### Variables d'Environnement

```bash
# Base de données
DATABASE_URL=postgresql://user:password@localhost/lawandcode

# Sécurité
SECRET_KEY=ton-secret-key-ultra-securise

# Email (SendGrid)
MAIL_SERVER=smtp.sendgrid.net
MAIL_USERNAME=apikey
MAIL_PASSWORD=ton-api-key-sendgrid
MAIL_DEFAULT_SENDER=une-adresse-mail-expéditeur

# Monitoring (optionnel)
SENTRY_DSN=https://ton-dsn@sentry.io/projet

# Admin
ADMIN_USER_ID=1
```

## 🌐 Déploiement

### Render (Recommandé)

```bash
# Build Command
pip install -r requirements.txt

# Start Command  
gunicorn app:app

# Variables d'environnement
# Ajouter toutes les variables dans l'interface Render
```

### Railway (Alternative)

```bash
# Deploy automatique depuis GitHub
# Configuration via railway.app
```

### Docker

```bash
# Build
docker build -t lawandcode .

# Run
docker run -p 5000:5000 --env-file .env lawandcode
```

## 🏗️ Architecture

### Structure des Fichiers

```
law-and-code/
├── app.py                    # Point d'entrée principal Flask
├── requirements.txt          # Dépendances Python
├── Procfile                  # Configuration Render/Heroku
├── runtime.txt              # Version Python pour déploiement
├── docker-compose.yml       # Configuration Docker développement
├── Dockerfile               # Image Docker pour production
├── .dockerignore           # Exclusions Docker
├── .gitignore              # Exclusions Git
├── .env                    # Variables d'environnement (local)
├── monitoring_dashboard.py  # Dashboard de monitoring
├── demo_sentry.py          # Démonstration Sentry
├── run_tests.sh            # Script d'exécution des tests
│
├── helpers/                # Modules utilitaires
│   ├── __init__.py        # Exports principaux
│   ├── core.py            # Fonctions core (DB, auth, email)
│   ├── monitoring.py      # Système de monitoring & logging
│   ├── sentry_simple.py   # Configuration Sentry
│   └── sentry_config.py   # Configuration Sentry avancée
│
├── templates/             # Templates Jinja2
│   ├── layout.html       # Template de base
│   ├── index.html        # Page d'accueil
│   ├── about.html        # Page à propos
│   ├── choice.html       # Sélection de quiz
│   ├── choosefile.html   # Sélection de fichier quiz
│   ├── quiz.html         # Interface de jeu
│   ├── profile.html      # Profil utilisateur
│   ├── login.html        # Connexion
│   ├── register.html     # Inscription
│   ├── forgot_password.html    # Mot de passe oublié
│   ├── reset_password.html     # Réinitialisation mot de passe
│   ├── modify_questions.html   # Modification des questions
│   ├── messages.html     # Messages/Contact
│   └── apology.html      # Page d'erreur
│
├── static/               # Assets statiques
│   ├── CSS/
│   │   ├── main_style.css        # Styles principaux
│   │   ├── login_register.css    # Styles auth
│   │   ├── profile.css           # Styles profil
│   │   ├── quiz_page.css         # Styles quiz
│   │   ├── quizCards.css         # Styles cartes quiz
│   │   ├── search_bar.css        # Styles barre recherche
│   │   └── view_messages.css     # Styles messages
│   ├── JavaScript/
│   │   ├── quizlogic.js          # Logique des quiz
│   │   ├── deleteAccount.js      # Confirmation suppression compte
│   │   ├── lockedQuiz.js         # Feedback quiz verrouillés
│   │   ├── manageFile.js         # Gestion fichiers quiz
│   │   ├── manageQuestion.js     # Gestion questions quiz
│   │   ├── questionsRoute.js     # Routing questions
│   │   ├── removeFlashMsg.js     # Suppression messages flash
│   │   ├── textMaxLenght.js      # Limitation longueur texte
│   │   └── togglePassword.js     # Affichage/masquage mot de passe
│   ├── Images/
│   │   └── 1750383440064.jpg     # Photo profil
│   └── Documents/
│       └── CV Tchicaya.pdf       # CV téléchargeable
│
├── admin/                # Module administration
│   ├── __init__.py      # Package admin
│   └── routes.py        # Routes admin
│
├── auth/                 # Module authentification
│   ├── __init__.py      # Package auth
│   └── routes.py        # Routes auth (login, register, reset)
│
├── main/                 # Routes principales
│   ├── __init__.py      # Package main
│   └── routes.py        # Routes principales (accueil, profil, messages)
│
├── quiz/                 # Module quiz
│   ├── __init__.py      # Package quiz
│   └── routes.py        # Routes quiz (création, jeu, gestion)
│
├── tests/               # Suite de tests
│   ├── __init__.py      # Package tests
│   ├── conftest.py      # Configuration pytest
│   ├── test_auth.py     # Tests authentification
│   ├── test_helpers.py  # Tests fonctions utilitaires
│   ├── test_integration.py # Tests d'intégration
│   ├── test_main.py     # Tests routes principales
│   └── test_quiz.py     # Tests module quiz
│
├── logs/                # Logs applicatifs
│   ├── app.log          # Logs généraux
│   └── errors.log       # Logs d'erreurs
│
├── flask_session/       # Sessions Flask (filesystem)
│
├── Documentation/       # Documentation projet
│   ├── MONITORING_GUIDE.md     # Guide monitoring
│   ├── SENTRY_INTEGRATION.md   # Guide Sentry
│   ├── TESTING_GUIDE.md        # Guide tests
│   └── TESTS_SUMMARY.md        # Résumé des tests
│
└── pytest.ini          # Configuration pytest
```

### Base de Données

```sql
-- Tables principales
quiz_infos      -- Métadonnées des quiz
quiz_questions  -- Questions et réponses
users          -- Comptes utilisateurs
quiz_likes     -- Tracking des likes
user_stats     -- Statistiques utilisateur
```

## 📊 Monitoring

### Health Check
```bash
curl https://ton-app.com/health
# Retourne le statut système et métriques
```

### Logs Structurés
```json
{
  "timestamp": "2025-09-01T15:30:45.123Z",
  "level": "INFO",
  "logger": "law_quiz_app",
  "message": "User login successful",
  "user_id": 123,
  "ip": "192.168.1.1",
  "response_time": 0.045
}
```

### Dashboard de Monitoring
```bash
python monitoring_dashboard.py --url https://ton-app.com
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest tests.py -v

# Tests avec coverage
pytest --cov=. tests.py

# Tests en mode watch
ptw tests.py
```

### Structure des Tests
- **Tests unitaires** : Fonctions helpers
- **Tests d'intégration** : Routes Flask
- **Tests de bout en bout** : Parcours utilisateur

## 🤝 Contribution

### Guidelines

1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tes changements (`git commit -m 'Add: Amazing Feature'`)
4. **Push** sur la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrir** une Pull Request

---

<div align="center">
  <p>
    <a href="https://lawandcode-app.onrender.com">🌐 Site Web</a> •
    <a href="mailto:law.and.code.website@gmail.com">📧 Contact</a> •
    <a href="https://www.linkedin.com/in/divin-tchicaya-19950b255">🐦 LinkedIn</a>
  </p>
</div>

