import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# TEST DES ROUTES PUBLIQUES 

def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Law and Code" in response.data

def test_about(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert "À Propos" in response.data.decode("utf-8")

def test_choix(client):
    response = client.get("/quiz/choix")
    assert response.status_code == 200
    assert b"Choisissez" in response.data
    assert b"Droit Civil" in response.data
    assert b"Droit Constitutionnel" in response.data

def test_play_public_quiz(client):
    response = client.get("/quiz/quiz?type=public&dossier=Droit%20Civil")
    assert response.status_code == 200
    assert b"Droit Civil" in response.data

def test_register_get(client):
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Inscription" in response.data

def test_login_get(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Connexion" in response.data or b"login" in response.data

def test_quizlengtherror(client):
    response = client.get("/quiz/quizlengtherror")
    assert response.status_code == 400 # Apology returns 400
    assert b"<!-- https://memegen.link/ -->" in response.data

def test_logout(client):
    response = client.get("/auth/logout")
    assert response.status_code == 200
    # response.data.decode car non ascii utilisé
    assert "Vous êtes déconnecté" in response.data.decode("utf-8") 

def test_arrets_missing_titre(client):
    response = client.get("/quiz/get_public_questions")
    assert response.status_code == 400
    assert b"<!-- https://memegen.link/ -->" in response.data

def test_quiz_missing_params(client):
    response = client.get("/quiz/quiz")
    assert response.status_code == 400

# TEST DES ROUTES PRIVÉES

def test_choose_file(client): # Test route de choix de fichier pour créer ou compléter un quiz
    # Simule un utilisateur connecté
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # ou l'ID d'un utilisateur existant

    response = client.get("/quiz/choose_file")
    assert response.status_code == 200
    assert b"Choisir un dossier" in response.data
     # Vérifie que les dossiers propres à l'utilisateur sont présents
    assert b"Bonsoir" in response.data and b"Hello" in response.data

def test_create_new_quiz_file(client): # Test route de création d'un quiz avec un dossier
    # Simule un utilisateur connecté
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # ou l'ID d'un utilisateur existant

    response = client.get("/quiz/create_new_quiz_file?dossier=Bonsoir")
    assert response.status_code == 200
    assert b"Hello" in response.data
    # Vérifie que les dossiers propres à l'utilisateur sont présents
    assert b"Question" in response.data and "Réponse" in response.data.decode("utf-8") 

def test_view_profile(client): 
    # Simule un utilisateur connecté
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # ou l'ID d'un utilisateur existant

    response = client.get("/quiz/get_stats")
    assert response.status_code == 200
    # Vérifie que le nom de l'utilisateur est affiché
    assert "Résultats pour Divin" in response.data.decode("utf-8")  

def test_private_choice(client): # Test route de choix d'un quiz privé
    # Simule un utilisateur connecté
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # ou l'ID d'un utilisateur existant

    response = client.get("/quiz/private_choice")
    assert response.status_code == 200
    assert b"Choisissez un dossier" in response.data
    # Vérifie que les dossiers propres à l'utilisateur sont présents
    assert b"Bonsoir" in response.data and b"Hello" in response.data 

def test_play_private_quiz(client): # Test route de lancement d'un quiz privé
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # ou l'ID d'un utilisateur existant

    response = client.get("/quiz/quiz?type=private&dossier=Hello")
    assert response.status_code == 200
    assert b"Hello" in response.data
    assert b"A" in response.data or b"B" in response.data  or b"C" in response.data or b"D" in response.data  

def test_logout(client):
    # Simule un utilisateur connecté
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # ou l'ID d'un utilisateur existant

    response = client.get("/auth/logout")
    assert response.status_code == 200
    # Vérifie que le message de déconnexion est affiché
    assert "Vous êtes déconnecté" in response.data.decode("utf-8")

def test_read_messages_admin(client): # Test route de lecture des messages par l'admin
    # Simule un utilisateur connecté
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # ou l'ID d'un utilisateur existant

    response = client.get("/admin/read_messages")
    assert response.status_code == 200
    assert b"Messages" in response.data 

# Test route de lecture des messages par un utilisateur non admin
def test_read_messages_not_admin(client): 
    # Simule un utilisateur connecté
    with client.session_transaction() as sess:
        sess["user_id"] = 2  # ou l'ID d'un utilisateur non admin

    response = client.get("/admin/read_messages")
    assert response.status_code == 403  # Accès interdit



