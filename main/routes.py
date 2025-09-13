from flask import Blueprint, redirect, make_response, render_template, request, url_for, session
from helpers import apology, db_request, arg_is_present, login_required, generate_reset_token

main_bp = Blueprint('main', __name__)

@main_bp.route("/") # Affiche la page d'accueil
def index():
    message = request.args.get("message")
    return render_template("index.html", message=message)

# Gère l'envoi de messages à l'administrateur
@main_bp.route("/messages", methods=["POST"]) 
def messages(): 

    if request.method == "POST":
        # Honeypot check - if the "website" field is filled, it's likely a bot
        honeypot = request.form.get("website")
        if honeypot:
            # Silently reject bot submissions without error message
            return redirect(url_for('main.about', message="Message envoyé !"))
            
        sender = request.form.get("name").strip() if request.form.get("name") else None
        message_to_send = request.form.get("msg").strip() if request.form.get("msg") else None
        if not arg_is_present([sender, message_to_send]):
            return apology("Veuillez renseigner tous les champs")
        if len(message_to_send) > 500:
            return apology("Le message est trop long, il doit faire moins de 500 caractères")
        if len(sender) > 50:
            return apology("Le nom est trop long, il doit faire moins de 50 caractères")
        try:
            db_request("INSERT INTO messages (name, message) VALUES (%s, %s)",
                        (sender, message_to_send), fetch=False)
        except Exception as e:
            return apology("Une erreur s'est produite")
        message = "Message envoyé !"
        return redirect(url_for('main.about', message=message))
    
# Affiche la page de profil de l'utilisateur avec ses résultats
@main_bp.route("/profile") 
@login_required
def profile():
    user_id = session.get("user_id")
    
    # Récupérer les statistiques utilisateur directement
    rows = db_request("SELECT matiere, posées, trouvées FROM stats WHERE user_id = %s", (user_id,))
    email = db_request("SELECT email FROM users WHERE id = %s", (user_id,), fetch=True)
    authentication_token = db_request("SELECT authentication_token FROM users WHERE id = %s", 
    (user_id,))[0][0]
    
    # Récupérer un éventuel message d'erreur si une route a renvoyé vers la route "/profile"
    # avec une variable "message" contenant un texte d'erreur
    message = request.args.get("message") if request.args.get("message") else None

    response = make_response(render_template(
        "profile.html", 
        rows=rows, 
        email=email[0][0] if email else None, 
        message=message,
        authentication_token=authentication_token
    ))

    # Interdit l'exécution de scripts inline pour éviter les attaques XSS
    response.headers['Content-Security-Policy'] = "script-src 'self';"
    response.headers['X-Frame-Options'] = "DENY;"
    response.headers['X-Content-Type-Options'] = "script-src 'self';"
    return response

@main_bp.route("/about") # Affiche la page d'informations du site
def about():
    message = request.args.get("message")
    return render_template("about.html", message=message)