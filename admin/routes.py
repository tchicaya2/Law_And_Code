from helpers import login_required, apology, db_request
from flask import Blueprint, render_template, session, current_app

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

"""  ROUTE ADMINISTRATEUR (Route réservée à l'administrateur) """

# Route pour lire les messages envoyés par les utilisateurs
@admin_bp.route("/read_messages")
@login_required
def read_messages():
    admin_id = current_app.config["ADMIN_USER_ID"]
    print(type(admin_id), type(session.get("user_id")))

    if "user_id" in session and int(session.get("user_id")) == admin_id:
        rows = db_request("SELECT name, message FROM messages")
        return render_template("messages.html", messages=rows)
    else:
        return apology("Accès interdit", 403)