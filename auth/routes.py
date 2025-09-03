from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, apology, db_request, arg_is_present, generate_reset_token, send_reset_email, is_valid_email, log_user_action, log_security_event, capitalize_first_letter
from helpers.sentry_simple import capture_user_context, capture_custom_event
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route("/login", methods=["GET", "POST"]) # Route pour la connexion de l'utilisateur
def login():

    """Log user in"""

    # Forget any user_id
    session.clear()

    # Soumission des infomations de connexion
    if request.method == "POST":
         # Get the next URL to redirect after login, if provided
        next_url = request.form.get("next") or request.args.get("next") or "/"

        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            special_error_feedback = "Veuillez fournir votre nom d'utilisateur"
            return render_template("login.html", special_error_feedback=special_error_feedback, next=next_url,
                                    username=username), 403

        # Ensure password was submitted
        elif not request.form.get("password"):
            special_error_feedback = "Veuillez fournir votre mot de passe"
            return render_template("login.html", special_error_feedback=special_error_feedback, next=next_url,
            username=username), 403

        # Ensure username exists and password is correct
        rows = db_request("SELECT * FROM users WHERE username = %s", (username,))
        if not rows:
            special_error_feedback = "Mot de passe ou nom d'utilisateur incorrect"
            return render_template("login.html", special_error_feedback=special_error_feedback, next=next_url, 
                                   username=username), 403

        provided_username_id = rows[0][0] # id potentiel de l'utilisateur qui essaie de se connecter (suivant le nom fourni)
        # Vérifier si l'utilisateur a encore le droit d'essayer de se connecter

        most_recent_fail, left_attempts, bans_number = db_request(
            "SELECT last_fail, attempts_left, bans_number FROM login_attempts WHERE user_id = %s", 
            (provided_username_id,), fetch=True)[0]
        if most_recent_fail: #most_recent_fail est NULL jusqu'au tout premier échec de l'utilisateur depuis création du compte  
            now = datetime.now(timezone.utc)
            diff = now - most_recent_fail
            # en minutes
            minutes = diff.total_seconds() / 60
            ban_duration = 5 # Première durée d'interdiction de connexion
            if bans_number > 1:
                for i in range(1, int(bans_number)):
                    ban_duration = ban_duration * 2

            #print(f"Différence en minutes : {now} - {most_recent_fail} = {minutes}")
            if minutes > ban_duration and left_attempts == 0:
                db_request("UPDATE login_attempts SET attempts_left = 5 WHERE user_id = %s", (provided_username_id,), fetch=False)     
            elif minutes < ban_duration and left_attempts == 0:
                    special_error_feedback = "Vous avez épuisé toutes vos tentatives de connexion, réessayez dans " + str(round((ban_duration - minutes), 2)) + " minute(s)"
                    return render_template("login.html", special_error_feedback=special_error_feedback, next=next_url, 
                                    username=username), 403

        # Si l'utilisateur n'existe pas dans la base de données ou que le mot de passe est incorrect
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            special_error_feedback = "Mot de passe ou nom d'utilisateur incorrect"
            
            # Log failed login attempt
            log_security_event('login_failed', {
                'attempted_username': username,
                'reason': 'invalid_credentials'
            })
            
            # Capturer l'événement dans Sentry
            capture_custom_event(
                f"Tentative de connexion échouée pour {username}",
                level='warning',
                extra={'attempted_username': username, 'ip': request.remote_addr}
            )

            # Actualiser le nombre de tentatives de connexion infructueuses dans la base de données
            results = db_request(
                "UPDATE login_attempts SET attempts_left = attempts_left - 1 WHERE user_id = %s AND attempts_left > 0 RETURNING attempts_left",
            (provided_username_id,), fetch=True)
            if results:
                # Si l'utilisateur a épuisé toutes ses tentatives
                if results[0][0] == 0:
                    special_error_feedback = "Vous avez épuisé toutes vos tentatives de connexion, réessayez plus tard"
                    db_request("UPDATE login_attempts SET bans_number = bans_number + 1, last_fail = %s WHERE user_id = %s",
                    (datetime.now(timezone.utc), provided_username_id,), fetch=False)
                    return render_template("login.html", special_error_feedback=special_error_feedback, next=next_url, 
                                    username=username), 403
        
            return render_template("login.html", special_error_feedback=special_error_feedback, next=next_url, 
                                   username=username), 403

        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        session["username"] = username  # Store username in session
        session.modified = True
        
        # Log successful login
        log_user_action('login_success', {
            'username': username,
            'login_method': 'password'
        })
        
        # Définir le contexte utilisateur pour Sentry
        capture_user_context(
            user_id=rows[0][0],
            username=username,
            email=rows[0][3] if len(rows[0]) > 3 else None
        )
        
        # Remettre le nombre d'interdiction de connexions à zéro
        db_request("UPDATE login_attempts SET bans_number = 0, attempts_left = 5 WHERE user_id = %s", 
        (session.get("user_id"),), fetch=False)
        # Vérifier s'il y a une url où rediriger l'utilisateur
        if next_url and next_url != "/":
                # Si next_url est absolue, récupère juste le chemin
                next_url_parsed = urlparse(next_url)
                next_url = next_url_parsed.path or "/"
                # Renvoyer à a page demandée
                return redirect(next_url 
                                + "?message=Bienvenu(e) " + username + " !")

        # Renvoyer à la page d'accueil avec un message
        message = "Bienvenu(e) " + username + " !"
        return redirect(url_for('main.index', message=message))

    # Affiche la page de connexion en stockant éventuellement le next_url
    else:
        next_url = request.args.get("next") or "/"
        return render_template("login.html", next=next_url)
    

# Route pour l'inscription d'un nouvel utilisateur
@auth_bp.route("/register", methods=["GET", "POST"]) 
def register():

    """Register user"""
    if request.method == "GET": # Affiche la page d'inscription
        return render_template("register.html")
    
    elif request.method == "POST":  # Soumission d'informations d'inscription
        username = capitalize_first_letter(request.form.get("username").strip()) if request.form.get("username") else None
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email", "").strip()  # Récupère l'email, vide par défaut
        if not arg_is_present([username, password, confirmation]):
                return apology("Veuillez renseigner tous les champs")
        if password != confirmation:
            special_error_feedback = "Le mot de passe et la confirmation ne correspondent pas"
            return render_template("register.html", special_error_feedback=special_error_feedback, username=username), 400
        match = re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$', password)
        if not match:
            special_error_feedback = "Votre mot de passe doit contenir au moins 8 caractères : une lettre majuscule (A–Z), une lettre minuscule (a–z), un chiffre (0–9), un caractère spécial (par ex. !, @, #, $, %, etc.)"
            return render_template("register.html", special_error_feedback=special_error_feedback, username=username), 400
        if db_request("SELECT username FROM users WHERE username = %s", (username,), fetch=True):
            special_error_feedback = "Ce nom d'utilisateur est déjà pris"
            return render_template("register.html", special_error_feedback=special_error_feedback, username=username), 400
        # Si l'utilisateur n'existe pas, on l'enregistre dans la base de données
        if len(username) > 50:
            special_error_feedback = "Le nom d'utilisateur est trop long, il doit faire moins de 50 caractères"
            return render_template("register.html", special_error_feedback=special_error_feedback, username=username), 400
        if len(password) > 64:
            special_error_feedback = "Le mot de passe est trop long, il doit faire moins de 64 caractères"
            return render_template("register.html", special_error_feedback=special_error_feedback, username=username), 400
        if len(confirmation) > 64:
            special_error_feedback = "La confirmation est trop longue, elle doit faire moins de 64 caractères"
            return render_template("register.html", message=special_error_feedback, username=username), 400
        if len(username) < 3:
            special_error_feedback = "Le nom d'utilisateur doit faire au moins 3 caractères"
            return render_template("register.html", message=special_error_feedback, username=username), 400
        # Si les informations d'inscription sont valides
        # On enregistre l'utilisateur dans la base de données
        if email and not is_valid_email(email):
            special_error_feedback = "Veuillez saisir une adresse email valide ou laisser vide"
            return render_template("register.html", special_error_feedback=special_error_feedback, username=username, email=email), 400
        if email and db_request("SELECT email FROM users WHERE email = %s", (email,), fetch=True):
            special_error_feedback = "Cette adresse email est déjà associée à un compte"
            return render_template("register.html", special_error_feedback=special_error_feedback, username=username), 400
        # Enregistrer l'utilisateur dans la base de données
        else:
            email = email if email else None  # email est NULL s'il n'est pas fourni
            db_request("INSERT INTO users (username, hash, email, authentication_token) VALUES (%s, %s, %s, %s)",
                      (username, generate_password_hash(password), email,
                       generate_reset_token()), fetch=False)
            # Connecter l'utilisateur nouvellement créé
            rows = db_request("SELECT id FROM users WHERE username = %s", (username,))
            user_id = rows[0][0]
            # Créer une nouvelle ligne pour le nouvel utilisateur dans la table des tentatives de connexion
            db_request("INSERT INTO login_attempts (user_id) VALUES (%s)",
                      (user_id,), fetch=False)
            # Log successful registration
            log_user_action('user_registered', {
                'username': username,
                'email_provided': bool(email)
            })
            
            session["user_id"] = user_id
            session["username"] = username  # Store username in session
            session.modified = True
            message = "Inscription réussie ! Bienvenu(e) " + username + " !"
            return redirect(url_for('main.index', message=message))

# Déconnecte l'utilisateur et renvoie à la page d'accueil avec un message de déconnexion
@auth_bp.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    return render_template("index.html", message="Vous êtes déconnecté !")


@auth_bp.route("/add_email", methods=["POST"])
@login_required
def add_email():
    """Ajouter une adresse email au compte utilisateur"""
    
    email = request.form.get("email", "").strip()
    user_id = session.get("user_id")
    provided_authentication_token = request.form.get("authentication_token")
    
    if not email:
        message = "Veuillez saisir une adresse email"
        return redirect(url_for('main.profile', message=message))

    if not is_valid_email(email):
        message = "Veuillez saisir une adresse email valide"
        return redirect(url_for('main.profile', message=message))

    actual_authentication_token = db_request("SELECT authentication_token FROM users WHERE id = %s", 
    (user_id,))[0][0]

    if not provided_authentication_token or provided_authentication_token != actual_authentication_token:
        return apology("Erreur sur la provenance de la requête") 
    
    results = db_request("UPDATE users SET email = %s WHERE id = %s AND NOT EXISTS (SELECT 1 FROM users WHERE email = %s AND id != %s) RETURNING id;", 
    (email, user_id, email, user_id), fetch=True)
    if not results: # Si results retourne rien, alors aucun update n'a eu lieu parce qu'un autre compte utilise déjà l'adresse mail
        message = "Cette adresse email est déjà utilisée par un autre compte"
        return redirect(url_for('main.profile', message=message))   

    message = "Adresse email ajoutée avec succès !"
    return redirect(url_for('main.profile', message=message))


@auth_bp.route("/update_email", methods=["POST"])
@login_required
def update_email():
    """Modifier l'adresse email du compte utilisateur"""
    
    email = request.form.get("email", "").strip()
    user_id = session.get("user_id")
    provided_authentication_token = request.form.get("authentication_token")
    
    if not email:
        message = "Veuillez saisir une adresse email"
        return redirect(url_for('main.profile', message=message))

    if not is_valid_email(email):
        message = "Veuillez saisir une adresse email valide"
        return redirect(url_for('main.profile', message=message))
    
    actual_authentication_token = db_request("SELECT authentication_token FROM users WHERE id = %s", 
    (user_id,))[0][0]

    if not provided_authentication_token or provided_authentication_token != actual_authentication_token:
        return apology("Erreur sur la provenance de la requête")
    
    # Vérifier si l'email est déjà utilisé par un autre utilisateur
    existing_user = db_request("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
    if existing_user:
        message = "Cette adresse email est déjà utilisée par un autre compte"
        return redirect(url_for('main.profile', message=message))

    # Récupérer l'email actuel pour vérification
    current_email = db_request("SELECT email FROM users WHERE id = %s", (user_id,))
    current_email = current_email[0][0] if current_email else None
    
    if current_email == email:
        message = "Cette adresse email est déjà configurée sur votre compte"
        return redirect(url_for('main.profile', message=message))

    # Mettre à jour l'email
    db_request("UPDATE users SET email = %s WHERE id = %s", (email, user_id), fetch=False)
    
    # Supprimer les tokens de réinitialisation existants (sécurité)
    db_request("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,), fetch=False)

    message = "Adresse email modifiée avec succès !"
    return redirect(url_for('main.profile', message=message))


@auth_bp.route("/remove_email", methods=["POST"])
@login_required
def remove_email():
    """Supprimer l'adresse email du compte utilisateur"""
    
    user_id = session.get("user_id")
    confirm_remove = request.form.get("confirm_remove")
    provided_authentication_token = request.form.get("authentication_token")

    if not confirm_remove:
        message = "Confirmation requise pour supprimer l'adresse email"
        return redirect(url_for('main.profile', message=message))

    actual_authentication_token = db_request("SELECT authentication_token FROM users WHERE id = %s", 
    (user_id,))[0][0]

    if not provided_authentication_token or provided_authentication_token != actual_authentication_token:
        return apology("Erreur sur la provenance de la requête")

    # Vérifier que l'utilisateur a bien un email
    current_email = db_request("SELECT email FROM users WHERE id = %s", (user_id,))
    current_email = current_email[0][0] if current_email else None
    
    if not current_email:
        message = "Aucune adresse email n'est configurée sur votre compte"
        return redirect(url_for('main.profile', message=message))

    # Supprimer l'email (mettre à NULL)
    db_request("UPDATE users SET email = NULL WHERE id = %s", (user_id,), fetch=False)
    
    # Supprimer tous les tokens de réinitialisation associés (sécurité)
    db_request("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,), fetch=False)

    message = "Adresse email supprimée avec succès. Vous ne pourrez plus récupérer votre mot de passe par email."
    return redirect(url_for('main.profile', message=message))

        
@auth_bp.route("/delete_account") # Route pour supprimer le compte de l'utilisateur
@login_required
def delete_account():

    user_id = session.get("user_id")
    # Supprimer l'utilisateur de la table users
    # Les autres données associées seront supprimées par la contrainte ON DELETE CASCADE
    db_request("DELETE FROM users WHERE id = %s", (user_id,), fetch=False)

    session.clear()
    message = "Votre compte ainsi que toutes les données associées ont été supprimés avec succès."
    return redirect(url_for('main.index', message=message))


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Demande de réinitialisation de mot de passe"""
    
    if request.method == "GET":
        return render_template("forgot_password.html")
    
    elif request.method == "POST":
        email = request.form.get("email", "").strip()
        
        if not email:
            special_error_feedback = "Veuillez saisir votre adresse email"
            return render_template("forgot_password.html", special_error_feedback=special_error_feedback), 400
        
        if not is_valid_email(email):
            special_error_feedback = "Veuillez saisir une adresse email valide"
            return render_template("forgot_password.html", special_error_feedback=special_error_feedback, email=email), 400
        
        # Vérifier si l'utilisateur existe ET a un email
        user = db_request("SELECT id, username, email FROM users WHERE email = %s AND email IS NOT NULL", (email,))
        
        if not user:
            # Message générique pour ne pas révéler si le compte existe
            success_message = """Si cette adresse email est associée à un compte avec email configuré, 
                                vous recevrez un email avec les instructions de réinitialisation."""
            return render_template("forgot_password.html", success_message=success_message)
        
        user_id, username, user_email = user[0]
        
        # Générer un token de réinitialisation
        token = generate_reset_token()
        expires_at = datetime.now() + timedelta(hours=1)  # Expire dans 1 heure
        
        # Supprimer tout token préexistant pour l'utilisateur 
        db_request("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,), fetch=False)

        # Sauvegarder le token dans la base de données
        db_request(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user_id, token, expires_at),
            fetch=False
        )
        
        # Envoyer l'email
        if send_reset_email(user_email, username, token):
            success_message = "Si cette adresse email est associée à un compte, vous recevrez un email avec les instructions de réinitialisation."
            return render_template("forgot_password.html", success_message=success_message)
        else:
            special_error_feedback = "Erreur lors de l'envoi de l'email. Veuillez réessayer plus tard."
            return render_template("forgot_password.html", special_error_feedback=special_error_feedback), 500

@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Réinitialisation du mot de passe avec token"""
    print("TOKEN REÇU :", token)
    # Vérifier la validité du token
    token_data = db_request(
        """SELECT prt.id, prt.user_id, u.username, prt.expires_at, prt.used 
           FROM password_reset_tokens prt 
           JOIN users u ON prt.user_id = u.id 
           WHERE prt.token = %s""",
        (token,)
    )
    
    if not token_data:
        return render_template("reset_password.html", special_error_feedback="Token invalide ou expiré"), 400
    
    token_id, user_id, username, expires_at, used = token_data[0]
    
    # Vérifier si le token a expiré ou a été utilisé
    if used or datetime.now() > expires_at:
        return render_template("reset_password.html", special_error_feedback="Token invalide ou expiré"), 400
    
    if request.method == "GET":
        return render_template("reset_password.html", token=token, username=username)
    
    elif request.method == "POST":
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        if not password or not confirmation:
            special_error_feedback = "Veuillez renseigner tous les champs"
            return render_template("reset_password.html", special_error_feedback=special_error_feedback, token=token, username=username), 400
        
        if password != confirmation:
            special_error_feedback = "Le mot de passe et la confirmation ne correspondent pas"
            return render_template("reset_password.html", special_error_feedback=special_error_feedback, token=token, username=username), 400
        
        # Vérifier la complexité du mot de passe
        match = re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$', password)
        if not match:
            special_error_feedback = "Votre mot de passe doit contenir au moins 8 caractères : une lettre majuscule (A–Z), une lettre minuscule (a–z), un chiffre (0–9), un caractère spécial (par ex. !, @, #, $, %, etc.)"
            return render_template("reset_password.html", special_error_feedback=special_error_feedback, token=token, username=username), 400
        
        if len(password) > 64:
            special_error_feedback = "Le mot de passe est trop long, il doit faire moins de 64 caractères"
            return render_template("reset_password.html", special_error_feedback=special_error_feedback, token=token, username=username), 400
        
        # Mettre à jour le mot de passe
        hashed_password = generate_password_hash(password)
        db_request("UPDATE users SET hash = %s WHERE id = %s", (hashed_password, user_id), fetch=False)
        
        # Marquer le token comme utilisé
        results = db_request("UPDATE password_reset_tokens SET used = TRUE WHERE id = %s AND used = FALSE RETURNING user_id;", 
        (token_id,), fetch=True)
        
        if not results: # L'update du token a échoué, c'est qu'il avait déjà été utilisé
            special_error_feedback = "Token déjà utilisé"
            return render_template("reset_password.html", special_error_feedback=special_error_feedback, token=token, username=username), 400

        # Nettoyer les anciens tokens de cet utilisateur
        db_request("DELETE FROM password_reset_tokens WHERE user_id = %s AND used = TRUE", (user_id,), fetch=False)
        
        success_message = "Votre mot de passe a été réinitialisé avec succès ! Vous pouvez maintenant vous connecter."
        return render_template("login.html", message=success_message)
