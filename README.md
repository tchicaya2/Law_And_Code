# 🏛️ Law and Code - Plateforme Interactive d'Apprentissage Juridique

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🎯 **Plateforme gamifiée d'apprentissage du droit** - Fusionnant technologie moderne et éducation juridique pour révolutionner l'apprentissage des principes légaux.

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
- **Gamification** : Encourager l'engagement par des mécaniques de jeu
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
- **Statistiques détaillées** : Suivi des performances

### 👤 Système Utilisateur
- **Authentification sécurisée** : Sessions Flask + hashage bcrypt
- **Profils personnalisés** : Historique et statistiques
- **Système de notifications** : Email via SendGrid
- **Administration** : Panel admin pour la modération

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
MAIL_DEFAULT_SENDER=contact@lawandcode.com

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
├── app.py                 # Point d'entrée principal
├── requirements.txt       # Dépendances Python
├── Procfile              # Configuration Heroku/Render
├── runtime.txt           # Version Python
│
├── helpers/              # Modules utilitaires
│   ├── __init__.py      # Exports principaux
│   ├── core.py          # Fonctions core (DB, auth)
│   ├── monitoring.py    # Système de monitoring
│   └── sentry_simple.py # Configuration Sentry
│
├── templates/           # Templates Jinja2
│   ├── layout.html     # Template de base
│   ├── index.html      # Page d'accueil
│   ├── choice.html     # Sélection de quiz
│   ├── quiz.html       # Interface de jeu
│   └── profile.html    # Profil utilisateur
│
├── static/             # Assets statiques
│   ├── main_style.css # Styles principaux
│   ├── quizlogic.js   # Logique des quiz
│   └── img/           # Images et assets
│
├── admin/              # Module administration
├── auth/               # Module authentification
├── main/               # Routes principales
├── quiz/               # Module quiz
│
├── tests.py           # Suite de tests
├── pytest.ini        # Configuration tests
└── logs/              # Logs applicatifs
```

### Base de Données

```sql
-- Tables principales
quiz_infos      -- Métadonnées des quiz
quiz_questions  -- Questions et réponses
users          -- Comptes utilisateurs
quiz_likes     -- Système de likes
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

### Standards de Code
- **PEP 8** pour Python
- **JSDoc** pour JavaScript
- **Tests obligatoires** pour nouvelles features
- **Logs structurés** pour toute nouvelle fonctionnalité

## 📈 Roadmap

### Version 2.0
- [ ] **API REST** complète
- [ ] **Mobile app** React Native
- [ ] **AI-powered** suggestions de questions
- [ ] **Collaborative features** équipes/classes

### Version 1.1
- [ ] **Export PDF** des résultats
- [ ] **Thèmes sombres/clairs**
- [ ] **Notifications push**
- [ ] **Statistiques avancées**

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **CS50x** - Cours qui a initié ce projet
- **Flask Community** - Documentation exceptionnelle
- **PostgreSQL Team** - Base de données robuste
- **Bootstrap Team** - Framework CSS moderne

---

<div align="center">
  <p><strong>Développé avec ❤️ pour démocratiser l'apprentissage du droit</strong></p>
  <p>
    <a href="https://lawandcode.com">🌐 Site Web</a> •
    <a href="mailto:contact@lawandcode.com">📧 Contact</a> •
    <a href="https://twitter.com/lawandcode">🐦 Twitter</a>
  </p>
</div>

