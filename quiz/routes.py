from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for
from helpers import login_required, apology, db_request, arg_is_present, clean_arg

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

matieres = ["Droit Civil", "Droit Pénal", "Droit Administratif", "Droit des Sociétés",
                 "Droit International", "Droit Fiscal", "Droit du Travail", "Droit Constitutionnel",
                 "Droit de l'Union européenne", "Propriété Intellectuelle","Droit des Contrats",
                 "Droit des Sociétés", "Droit des Successions", "Droit des Obligations",
                 "Droit des Biens", "Droit des Assurances", "Droit des Transports", 
                 "Droit de la Concurrence",
                 "Droit de la Consommation",
                 "Responsabilité Civile", "Procédure Civile",
                 "Procédure Pénale", "Droit de la Protection Sociale",
                 "Droit de la Protection des Données"]
niveaux = ["L1", "L2", "L3", "M1", "M2"]

# Affiche la page de choix de quiz public ou privés
@quiz_bp.route("/choix", methods=["GET", "POST"]) 
def choix():
    if request.method == "GET":
        page = int(request.args.get("page")) if request.args.get("page") else 1
        offset = int(page) * 10 - 10 # Nombre de résultats à exclure 
        type = request.args.get("quiz_type")

        # Récupérer directement les quiz publics avec toutes les informations nécessaires
        if type == "public":
            rows = db_request("""
                SELECT qi.titre, u.username, qi.matiere, qi.niveau, COUNT(*) AS nombre_de_questions, qi.likes
                FROM quiz_questions qq
                JOIN quiz_infos qi ON qq.quiz_id = qi.quiz_id
                JOIN users u ON qi.user_id = u.id
                WHERE qi.type = 'public'
                GROUP BY qi.titre, u.username, qi.matiere, qi.niveau, qi.likes, qi.quiz_id
                HAVING COUNT(*) > 3
                ORDER BY qi.likes DESC
                LIMIT 10 OFFSET %s
            """, (offset,))
            total_results = len(db_request("""SELECT qq.quiz_id FROM quiz_questions qq LEFT JOIN quiz_infos qi
            ON qq.quiz_id = qi.quiz_id WHERE type = 'public' GROUP BY qq.quiz_id HAVING COUNT(*) > 3;""", fetch=True))

        else:
            user_id = session.get("user_id")
            rows = db_request("""
                SELECT qi.titre, qi.quiz_id, COUNT(*) AS nombre_de_questions
                FROM quiz_questions qq
                JOIN quiz_infos qi ON qq.quiz_id = qi.quiz_id
                JOIN users u ON qi.user_id = u.id
                WHERE qi.user_id = %s
                GROUP BY qi.titre, qi.quiz_id
                LIMIT 10 OFFSET %s
            """, (user_id, offset))
            total_results = db_request(
            """SELECT COUNT(*) FROM quiz_infos
            WHERE user_id = %s""",
            (user_id,), fetch=True)[0][0]
        
        total_pages = (total_results + 9) // 10
        # Extrait les données de chaque tuple selon le type de quiz (moins de données si quiz privés)
        dossiers = [{"titre": row[0], "user_id": row[1], "matiere": row[2], 
                    "niveau": row[3], "nombre_de_questions": row[4], 
                    "likes": row[5]} for row in rows] if type == "public" else [{"titre": row[0], 
                    "quiz_id": row[1], "nombre_de_questions": row[2]} for row in rows]

        return render_template("choice.html", type=type, response=dossiers, 
                               total_pages=total_pages, page=page)
    
    else: # Méthode POST pour les recherches de quiz avec la barre de recherches
        query = request.form.get("query").strip() if request.form.get("query") else None
        page = int(request.form.get("page")) if request.form.get("page") else 1
        offset = int(page) * 10 - 10
        print("OFFSET:", offset)
        print("TYPE:", request.form.get("quiz_type"))
        type = request.form.get("quiz_type")
    
        if not query:
            return apology("Veuillez fournir un terme de recherche")
        # On nettoie la requête pour éviter les injections SQL
        # Nettoyage spécifique aux requêtes ILIKE
        param = f"%{query}%"
        rows = db_request("""
            SELECT titre, username, matiere, niveau, COUNT(*) AS nombre_de_questions, likes, type 
            FROM quiz_questions 
            JOIN quiz_infos ON quiz_questions.quiz_id = quiz_infos.quiz_id
            JOIN users ON quiz_infos.user_id = users.id
            WHERE type = 'public' 
            AND (titre ILIKE %s
            OR username ILIKE %s
            OR matiere ILIKE %s
            OR niveau ILIKE %s)
            GROUP BY titre, username, matiere, niveau, likes, type
            HAVING COUNT(*) > 3
            ORDER BY likes DESC LIMIT 10 OFFSET %s;
        """, (param, param, param, param, offset,)) if type == "public" else db_request(
        """SELECT titre, COUNT(*) FROM quiz_questions
        JOIN quiz_infos ON quiz_questions.quiz_id = quiz_infos.quiz_id
        WHERE (titre ILIKE %s) AND user_id = %s GROUP BY titre LIMIT 10 OFFSET %s""",
        (param, session.get("user_id"), offset))

        total_results = len(db_request("""SELECT titre FROM quiz_questions 
            JOIN quiz_infos ON quiz_questions.quiz_id = quiz_infos.quiz_id
            JOIN users ON quiz_infos.user_id = users.id
            WHERE type = 'public' AND (titre ILIKE %s OR username ILIKE %s
            OR matiere ILIKE %s OR niveau ILIKE %s) GROUP BY titre
            HAVING COUNT(*) > 3""", 
            (param, param, param, param), fetch=True)) if type == "public" else len(db_request(
        """SELECT titre FROM quiz_infos
        WHERE (titre ILIKE %s) AND user_id = %s;""",
        (param, session.get("user_id"),), fetch=True))

        total_pages = (total_results + 9) // 10  # Arrondi vers le haut pour obtenir le nombre total de pages
        
        # Extrait le premier élément de chaque tuple, 
        # contenu dans la liste de tuples que renvoie la base de données
        dossiers = [{"titre": row[0], "user_id": row[1], "matiere": row[2], 
                    "niveau": row[3], "nombre_de_questions": row[4], "likes": row[5]} for row in rows] if type =="public" else [{"titre": row[0], "nombre_de_questions": row[1]} for row in rows]
        result_feedback = f"{total_results} résultat(s) trouvé(s) pour '{query}'" if dossiers else f"Aucun résultat trouvé pour '{query}'"
        return render_template("choice.html", type=type, response=dossiers, 
                               result_feedback=result_feedback, query=query,
                            total_results=total_results, total_pages=total_pages, page=page)



# Renvoie vers Javascript les arrêts d'un titre donné pour un quiz public
@quiz_bp.route("/get_public_questions")
def get_public_questions():

    quiz_id = request.args.get("quiz_id")
    if not arg_is_present([quiz_id]):
        return apology("titre manquant")

    try:
        rows = db_request("""SELECT réponse, question FROM quiz_questions
                           WHERE quiz_id = %s""", (quiz_id,), fetch=True)
        if len(rows) < 4:
            return apology("Le quiz ne contient pas assez de questions")
        return jsonify(rows)
        
    except Exception as e:
        return apology("Une erreur est survenue. Le titre n'existe peut-être pas")
    

@quiz_bp.route("/get_private_questions") 
# Sur requête de Javascript, renvoie la liste des questions-réponses d'un quiz privé
@login_required
def get_private_questions():

    quiz_id = request.args.get("quiz_id")
    if not arg_is_present([quiz_id]):
        return apology("titre manquant")

    rows = db_request("""SELECT réponse, question FROM quiz_questions
                      WHERE quiz_id = %s""",
                      (quiz_id,), fetch=True)
    if len(rows) < 4:
        return apology("Le quiz ne contient pas assez de questions")
    return jsonify(rows)


@quiz_bp.route("/quiz") # Affiche la page où sera jouée le quiz avec les infos nécessaires
def quiz():

    titre = request.args.get("titre")
    matiere = request.args.get("matiere")
    type = request.args.get("type")
    # auteur peut être le nom complet de l'auteur ou directement son id dans la base de données
    auteur = request.args.get("auteur")
    if type == "public":
        if not arg_is_present([titre, matiere, type, auteur]):
            return apology("Titre, matière, type ou auteur de quiz manquant")
        try:
            # On essaie une conversion dans le cas où l'argument "auteur" est venu sous forme d'id directement
            author_id = int(auteur)
        # En cas d'échec de la conversion, alors l'argument "auteur" est venu sous forme de nom 
        # On utilise alors ce nom pour récupérer l'id dans la base de données
        except ValueError:
            author_id = db_request("SELECT id FROM users WHERE username = %s", (auteur,), fetch=True)
            author_id = author_id[0][0]
        if not author_id:
            return apology("Auteur introuvable")
        # On retrouve l'id du quiz pour l'auteur correspondant
        # Parce qu'un titre peut être partagé par plusieurs auteurs
        quiz_id = db_request("SELECT quiz_id FROM quiz_infos WHERE titre = %s AND user_id = %s",
                            (titre, author_id), fetch=True)
        
        if not quiz_id:
            return apology("Quiz introuvable")
        quiz_id = quiz_id[0][0]

        already_liked = db_request(
            "SELECT 1 FROM quiz_likes WHERE user_id = %s AND quiz_id = %s",
            (session.get("user_id"), quiz_id,)
        )
        if not already_liked:
            already_liked = False
        else:
            already_liked = True
        return render_template("quiz.html", type=type, titre=titre, matiere=matiere,
                            already_liked=already_liked, author_id=author_id, quiz_id=quiz_id)

    elif type == "private":
        if not arg_is_present([titre, type]):
            return apology("Titre ou type de quiz manquant")

        quiz_id = db_request("SELECT quiz_id FROM quiz_infos WHERE titre = %s AND user_id = %s",
                            (titre, session.get("user_id")), fetch=True)
        if not quiz_id:
            return apology("Quiz introuvable")
        quiz_id = quiz_id[0][0]
        print("AUTEUR ET quiz_id:", auteur, quiz_id)

        return render_template("quiz.html", type=type, titre=titre, matiere=matiere, quiz_id=quiz_id,
                            already_liked=True)
    else:
        return apology("Type de quiz invalide")


# Renvoie à une page d'erreur lorsque l'utilisateur essaie de lancer un quiz privé trop court
@quiz_bp.route("/quizlengtherror") 
def quizlengtherror():

    return apology("Ce Quiz contient moins de 4 questions et ne peut pas être lancé")


# Met à jour les résultats des utilisateurs dans la base de données
@quiz_bp.route("/update_stats", methods=["POST"]) 
@login_required
def update_stats():

    matiere = request.form.get("matiere").strip() if request.form.get("matiere") else None
    posées = int(request.form.get("posées").strip() if request.form.get("posées") else 0)
    trouvées = int(request.form.get("trouvées").strip() if request.form.get("trouvées") else 0)
    quiz_id = request.form.get("quiz_id").strip() if request.form.get("quiz_id") else None

    if not arg_is_present([matiere, posées, trouvées, quiz_id]):
        return apology("Matière, nombre de questions ou quiz manquant")

    attempt = db_request("SELECT * FROM quiz_attempts WHERE user_id = %s AND quiz_id = %s",
                   (session.get("user_id"), quiz_id))
    if attempt:
        return '', 204  # Si l'utilisateur a déjà joué ce quiz, on n'update pas les stats

    elif not attempt:
        # On enregistre l'essai de l'utilisateur dans la base de données
        db_request("INSERT INTO quiz_attempts (user_id, quiz_id) VALUES (%s, %s)",
                   (session.get("user_id"), quiz_id), fetch=False)
    
    # Vérifier si l'utilisateur a une ligne dans la db pour la matière qu'il vient de jouer
    if not db_request("SELECT matiere FROM stats WHERE matiere = %s AND user_id = %s",
                     (matiere, session.get("user_id"),)):
        # Si l'utilisateur n'a pas encore une ligne pour cette matière (parce qu'il y a jamais joué)
        # On crée une nouvelle ligne pour cette matière pour l'utilisateur
        db_request("INSERT INTO stats (user_id, matiere, posées, trouvées) VALUES (%s, %s, %s, %s)",
                       (session.get("user_id"), matiere, posées, trouvées,), fetch=False)
    else:  
        # Sinon, l'utilisateur a déjà joué à un quiz dans cette matière
        # la ligne est déjà présente, on update juste le nombre les résultats
        # On incrémente le nombre de questions posées et trouvées pour cette matière
        db_request("UPDATE stats SET posées = posées + %s, trouvées = trouvées + %s WHERE user_id = %s AND matiere = %s",
                       (posées, trouvées, session.get("user_id"), matiere,), fetch=False)
    
    # On retourne quand même une réponse valide 
    # même si cette route n'a pas vocation à renvoyer quelque chose à l'appelant
    return '', 204 


# Page de choix de fichier pour créer ou compléter un quiz privé
@quiz_bp.route("/choose_file", methods=["GET"])  
@login_required
def choose_file():

    results = db_request("SELECT titre, matiere FROM quiz_infos WHERE user_id = %s ORDER BY titre", 
                         (session.get("user_id"),))
    
    # Au cas où il y aurait un message à afficher
    message = request.args.get("message") if request.args.get("message") else None
    error_msg = request.args.get("error_msg") if request.args.get("error_msg") else None
    error = request.args.get("error") if request.args.get("error") else None


    return render_template("choosefile.html", dossiers=results, message=message, error_msg=error_msg, 
                           matieres=matieres, niveaux=niveaux, error=error)


# Route pour créer un nouveau dossier pour un quiz privé
@quiz_bp.route("/create_new_quiz_file", methods=["POST"]) 
@login_required
def create_new_quiz_file():

    nom_de_dossier = clean_arg(request.form.get("dossier")) # Entrée de l'utilisateur, donc on utilise clean_arg
    matiere = request.form.get("matiere") # Valeur contrôlée (champ select), donc pas de clean_arg 
    niveau = request.form.get("niveau")

    if not arg_is_present([nom_de_dossier, matiere, niveau]):
        message = "Veuillez renseigner correctement tous les champs pour créer un dossier"
        return redirect(url_for('quiz.choose_file', message=message))
    if len(nom_de_dossier) > 100:
        message = "Le nom de dossier est trop long. Il doit faire moins de 100 caractères"
        return redirect(url_for('quiz.choose_file', message=message))
    # Vérifier si un dossier avec le même nom existe déjà pour l'utilisateur
    if db_request("SELECT * FROM quiz_infos WHERE user_id = %s AND titre = %s",
                   (session.get("user_id"), nom_de_dossier), fetch=True):
        error_msg = "Un dossier avec ce nom existe déjà"
        # Redirige vers la page de choix de fichier si le dossier existe déjà
        return redirect(url_for('quiz.choose_file', error_msg=error_msg, error=True))
    if matiere.lower() not in [m.lower() for m in matieres]:
        print("MATIERE", matiere)
        message = "Matière invalide. Veuillez choisir une matière valide"
        return redirect(url_for('quiz.choose_file', message=message))
    if niveau.lower() not in [n.lower() for n in niveaux]:
        message = "Niveau invalide. Veuillez choisir un niveau valide"
        return redirect(url_for('quiz.choose_file', message=message))
    # Si tout est bon, on crée le dossier
    else:
        # Redirige vers la page de modification des questions du quiz privé 
        # avec le dossier sélectionné
        db_request("INSERT INTO quiz_infos (user_id, titre, matiere, niveau) VALUES (%s, %s, %s, %s)",
                   (session.get("user_id"), nom_de_dossier, matiere, niveau), fetch=False)
        message = "Dossier créé avec succès"
        return redirect(url_for('quiz.modify_quiz_questions',
                                dossier=nom_de_dossier, matiere=matiere, message=message))


# Route pour ajouter une nouvelle question dans un quiz privé
@quiz_bp.route("/add_new_question", methods=["POST"]) 
@login_required
def add_new_question():

    if request.method == "POST": 
        question = clean_arg(request.form.get("question"))
        if len(question) > 500:
            return apology("La question est trop longue, elle doit faire 500 caractères maximum")
        reponse = clean_arg(request.form.get("réponse"))
        if len(reponse) > 250:
            return apology("La réponse est trop longue, elle doit faire 250 caractères maximum")
        dossier = request.args.get("dossier")
        matiere = request.args.get("matiere")
        if not arg_is_present([question, reponse, dossier, matiere]):
                return apology("Veuillez renseigner tous les champs")
        
        # Vérifier si la question existe déjà dans le dossier de l'utilisateur
        if db_request("""SELECT * FROM quiz_questions 
                      JOIN quiz_infos ON quiz_questions.quiz_id = quiz_infos.quiz_id 
                      WHERE user_id = %s AND question = %s AND titre = %s""",
                       (session.get("user_id"), question, dossier), fetch=True):
            error_msg = "Cette question existe déjà dans ce dossier"
            return redirect(url_for('quiz.modify_quiz_questions', dossier=dossier, error_msg=error_msg, matiere=matiere))
        else: # Si la question n'existe pas, on l'insère
            quiz_id_row = db_request("SELECT quiz_id FROM quiz_infos WHERE titre = %s AND user_id = %s",
                                 (dossier, session.get("user_id"),), fetch=True)
            if not quiz_id_row:
                return apology("Quiz introuvable")
            quiz_id = quiz_id_row[0][0]
            db_request("""INSERT INTO quiz_questions (quiz_id, question, réponse) 
                       VALUES (%s, %s, %s)""",
                      (quiz_id, question, reponse), fetch=False)
            message = "Question ajoutée avec succès"
            # Redirige vers la page de modification des questions du quiz privé 
            # avec le dossier sélectionné
            return redirect(url_for('quiz.modify_quiz_questions', dossier=dossier, message=message, matiere=matiere))


 # Modifier les questions d'un quiz privé
@quiz_bp.route("/modify_quiz_questions", methods=["GET", "POST"])
@login_required
def modify_quiz_questions():

    # Affiche la page de modification d'un quiz privé avec les questions existantes
    if request.method == "GET": 
        dossier = request.args.get("dossier").strip() if request.args.get("dossier") else None
        matiere = request.args.get("matiere").strip() if request.args.get("matiere") else None
        message = request.args.get("message") if request.args.get("message") else None
        error_msg = request.args.get("error_msg") if request.args.get("error_msg") else None
        if not arg_is_present([dossier, matiere]):
            return apology("Dossier ou matière manquant")
        rows = db_request("""SELECT question, réponse FROM quiz_questions 
                          JOIN quiz_infos ON quiz_questions.quiz_id = quiz_infos.quiz_id 
                          WHERE titre = %s AND user_id = %s ORDER BY quiz_questions.id""",
                          (dossier, session.get("user_id"),))
        # Récupérer le type d'accès au quiz (accès public ou privé)
        access = db_request("SELECT type FROM quiz_infos WHERE titre = %s AND user_id = %s",
                           (dossier, session.get("user_id"),), fetch=True)
        if not access:
            return apology("Dossier introuvable")
        access = access[0][0]  # On récupère le type d'accès (public ou privé)

        # Si le dossier est vide, alors c'est un nouveau dossier que l'utilisateur veut créer
        # On renvoie donc la page de modification de questions pour ce nouveau dossier
        if not rows: 
            return render_template("modify_questions.html", dossier=dossier, message=message,
            error_msg=error_msg, access=access, matiere=matiere)
        # Sinon, on renvoie la page de modification avec les questions existantes
        return render_template("modify_questions.html", questions=rows, dossier=dossier, 
                               access=access, message=message, error_msg=error_msg, matiere=matiere)

    # Gère la modification d'une question d'un quiz privé
    else:
        initial_question = request.form.get("initial_question")
        initial_reponse = request.form.get("initial_answer")
        if not arg_is_present([initial_question, initial_reponse]):
            return apology("Question ou réponse initiale manquante")
        question = clean_arg(request.form.get("question"))
        reponse = clean_arg(request.form.get("réponse"))
        dossier = request.args.get("dossier") # J'utilise clean_arg que sur les entrées utilisateurs,
        # pas sur les champs que j'ai moi-même passés au template
        matiere = request.args.get("matiere")
        if not arg_is_present([question, reponse, dossier]):
            return apology("Veuillez renseigner tous les champs")
        if len(question) > 500:
            return apology("La question est trop longue, elle doit faire moins de 500 caractères")
        if len(reponse) > 250:
            return apology("La réponse est trop longue, elle doit faire moins de 250 caractères")
        # Vérifier si la question existe déjà dans le dossier de l'utilisateur
        if db_request("""SELECT id FROM quiz_questions
                      JOIN quiz_infos ON quiz_questions.quiz_id = quiz_infos.quiz_id
                      WHERE user_id = %s AND question = %s AND réponse = %s AND titre = %s""",
                       (session.get("user_id"), question, reponse, dossier), fetch=True):
            error_msg = "Cette question existe déjà dans ce dossier"
            return redirect(url_for('quiz.modify_quiz_questions', dossier=dossier, error_msg=error_msg, matiere=matiere))
        quiz_id_row = db_request("SELECT quiz_id FROM quiz_infos WHERE titre = %s AND user_id = %s",
                                 (dossier, session.get("user_id"),), fetch=True)

        if not quiz_id_row:
            return apology("Quiz introuvable")
        quiz_id = quiz_id_row[0][0]
        # On met à jour la question et la réponse dans la base de données
        db_request("""UPDATE quiz_questions
                   SET question = %s, réponse = %s WHERE quiz_id = %s
                   AND question = %s AND réponse = %s""",
                    (question, reponse, quiz_id, initial_question, initial_reponse,), fetch=False)
        message = "Question modifiée avec succès"
        # Redirige vers la page de modification des questions du quiz privé 
        # avec le dossier sélectionné
        return redirect(url_for('quiz.modify_quiz_questions', dossier=dossier, message=message, matiere=matiere))


# Supprimer une question d'un quiz privé
@quiz_bp.route("/delete_quiz_questions", methods=["POST"])
@login_required
def delete_quiz_questions():

    if request.method == "POST":
        dossier = request.form.get("dossier").strip() if request.form.get("dossier") else None
        question = request.form.get("question").strip() if request.form.get("question") else None
        reponse = request.form.get("réponse").strip() if request.form.get("réponse") else None
        matiere = request.form.get("matiere").strip() if request.form.get("réponse") else None
        if not arg_is_present([dossier, question, reponse, matiere]):
            return apology("Dossier, question ou réponse manquante")
        quiz_id = db_request("SELECT quiz_id FROM quiz_infos WHERE titre = %s AND user_id = %s",
                             (dossier, session.get("user_id"),), fetch=True)
        if not quiz_id:
            return apology("Quiz introuvable")
        # On récupère l'ID du quiz pour supprimer la question
        quiz_id = quiz_id[0][0]
        db_request("""DELETE FROM quiz_questions
                   WHERE quiz_id = %s AND question = %s AND réponse = %s""",
                    (quiz_id, question, reponse), fetch=False)
        message = "Question supprimée avec succès"
        # Redirige vers la page de modification des questions du quiz privé 
        # avec le dossier sélectionné
        return redirect(url_for('quiz.modify_quiz_questions', dossier=dossier, message=message, matiere=matiere))


# Renommer un dossier de quiz privé
@quiz_bp.route("/rename_file", methods=["POST"])
@login_required
def rename_file():

    nouveau_nom = clean_arg(request.form.get("newName"))
    dossier = request.args.get("dossier")
    if not arg_is_present([dossier, nouveau_nom]):
        return apology("Dossier ou nouveau nom manquant")
    if len(nouveau_nom) > 100:
        return apology("Le nouveau nom est trop long, il doit faire moins de 50 caractères")
    if db_request("SELECT * FROM quiz_infos WHERE titre = %s AND user_id = %s",
                   (nouveau_nom, session.get("user_id"),), fetch=True):
        message = "Un dossier avec ce nom existe déjà"
        # Redirige vers la page de choix de fichier si le nom existe déjà
        # pour éviter les doublons
        return redirect(url_for('quiz.choose_file', message=message)) 
    db_request("UPDATE quiz_infos SET titre = %s WHERE titre = %s AND user_id = %s",
               (nouveau_nom, dossier, session.get("user_id"),), fetch=False)

    message = "Dossier renommé avec succès"
    return redirect(url_for('quiz.choose_file', message=message))


# Supprime un dossier de quiz privé
@quiz_bp.route("/delete_file")
@login_required
def delete_file():

    dossier = request.args.get("dossier").strip() if request.args.get("dossier") else None
    if not dossier:
        return apology("Dossier manquant")
    db_request("DELETE FROM quiz_infos WHERE titre = %s AND user_id = %s", 
               (dossier, session.get("user_id"),), fetch=False)
    # Redirige vers la page de choix de fichier après la suppression du dossier
    message = "Dossier supprimé avec succès"
    print("SESSION USER ID:", session.get("user_id"))
    return redirect(url_for('quiz.choose_file', message=message))

# Aimer un quiz public
@quiz_bp.route("/like_quiz", methods=["POST"])
@login_required
def like_quiz():

    data = request.get_json()
    titre = data.get("titre") if data else None
    author_id = data.get("author_id") if data else None
    
    if not titre:
        return jsonify(success=False, error="Titre manquant")
    
    # Vérifier si l'utilisateur a déjà aimé ce quiz
    if db_request("""SELECT * FROM quiz_likes JOIN quiz_infos ON quiz_likes.quiz_id = quiz_infos.quiz_id 
                  WHERE quiz_likes.user_id = %s AND quiz_infos.titre = %s""",
                   (session.get("user_id"), titre), fetch=True):
      
        return jsonify(success=False, error="Vous avez déjà aimé ce quiz")

    # Ajouter le like dans la base de données
    quiz_id_row = db_request("SELECT quiz_id FROM quiz_infos WHERE titre = %s AND user_id = %s"
                             , (titre, author_id), fetch=True)
    if not quiz_id_row:
        return jsonify(success=False, error="Quiz introuvable")
    quiz_id = quiz_id_row[0][0]
    db_request("INSERT INTO quiz_likes (user_id, quiz_id) VALUES (%s, %s) ON CONFLICT (quiz_id, user_id) DO NOTHING",
               (session.get("user_id"), quiz_id), fetch=False)

    # Incrémenter le nombre de likes dans la table quiz_infos
    db_request("UPDATE quiz_infos SET likes = likes + 1 WHERE quiz_id = %s", (quiz_id,), fetch=False)

    return jsonify(success=True, message="Quiz aimé avec succès")

@quiz_bp.route("/modify_quiz_accessibility", methods=["POST"])
@login_required
def modify_quiz_accessibility():

    type = request.form.get("type").strip() if request.form.get("type") else None
    titre = request.form.get("titre").strip() if request.form.get("titre") else None
    matiere = request.form.get("matiere").strip() if request.form.get("matiere") else None
    author_id = session.get("user_id")
    if not arg_is_present([titre, type, matiere]):
        return redirect(url_for('quiz.modify_quiz_questions', 
                                message="Titre, type d'accès ou matière manquant", dossier=titre))
    if type not in ["public", "private"]:
        return redirect(url_for('quiz.modify_quiz_questions', 
                                message="Type d'accès invalide", dossier=titre, matiere=matiere))
    # Vérifier si le titre existe pour l'utilisateur
    if not db_request("SELECT * FROM quiz_infos WHERE titre = %s AND user_id = %s",
                      (titre, author_id), fetch=True):
        return redirect(url_for('quiz.modify_quiz_questions', 
                                message="Quiz introuvable", dossier=titre, matiere=matiere))
    # Mettre à jour le type d'accès du quiz
    updated = db_request("UPDATE quiz_infos SET type = %s WHERE titre = %s AND user_id = %s",
               (type, titre, author_id), fetch=False)
    if type == "public":
        message = "Le quiz est désormais accessible publiquement (à condition qu'il ait au moins 4 questions)"
    else:
        message = "Le quiz est désormais privé"

    return redirect(url_for('quiz.modify_quiz_questions', 
                            message=message, dossier=titre, matiere=matiere))
