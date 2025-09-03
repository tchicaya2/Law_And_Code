// Il y avait plus de 20 variables définies en global, j'ai revu le code pour les passer en local 
// et entre fonctions
let quizType;
let counter = 0; // Utilisé à 5 autres endroits, donc mis en variable globale
let chances; // 10 autres endroits
let fin;
let bonne_réponse;
let titre;
let matiere;
let quizMap = new Map();
let selectible = [];
let score, score_final;

// // Récupérer les arrêts associés à la matière choisie par l'utilisateur
async function getArrets(){ 
    // On récupère la route pour récupérer les arrêts associés à un titre 
    // ainsi que la méthode, depuis le contexte global
    let collectArretsRoute = window.collectArretsRoute;
    let quizlengtherrorRoute = window.quizlengtherrorRoute;
    let method = "GET";

    try{
        quiz_id = document.getElementById("quiz_id").textContent;
        // La route Flask "/get_private_questions" appelée avec POST renvoie la liste des arrêts 
        // associés à un quiz_id choisi
        let response = await fetch(`${collectArretsRoute}?quiz_id=${encodeURIComponent(quiz_id)}`, {
            method: method
        });
        let arrets = await response.json();
        return arrets;
    } catch (error){ 
        // Cette erreur peut survenir pour les quiz publics ou privés, 
        // selon la réponse du serveur
        // En cas d'erreur, on déclenche une route Flask qui affiche la page d'erreur
        window.location.href = quizlengtherrorRoute; 
    }
}

async function main(){ 
    // On commence par récupérer les arrêts associés à la matière choisie
    const arrets = await getArrets();
    // Remplir une liste ("selectible") avec tous les noms d'arrêts
    for (let arret of arrets){
        quizMap.set(arret[0], arret[1]); // On associe arret et principe dans un tuple
    }
    for (let[key, value] of quizMap){
        // On remplit la liste selectible avec les noms d'arrêts
        selectible.push(key); 
    }

}

/* Une fois la page chargée, attendre que main remplisse la liste de questions
puis capturer les éléments du DOM pour ensuite y ajouter les données appropriées */
document.addEventListener("DOMContentLoaded", async() => { 
    await main();
    set_and_ask();
});

function set_and_ask(){
    /* On commence par "attraper" les éléments de la page */
    let titre = document.getElementById("titre");
    let pcp = document.getElementById("principe");
    let r1 = document.getElementById("r1");
    let r2 = document.getElementById("r2");
    let r3 = document.getElementById("r3");
    let r4 = document.getElementById("r4");
    score = document.getElementById("score");
    let essais = document.getElementById("essais")
    let feedback = document.getElementById("feedback");
    let clique_réponse = document.getElementById("les_réponses");
    let suivant = document.getElementById("suivant");
    currentQuestion = document.getElementById("current-question");
    totalQuestions = document.getElementById("total-questions");
    let progressBar = document.getElementById("progress-bar");
    let progressText = document.getElementById("progress-text");
    let asked = [];
    let options = [];

    essais.textContent = chances;
    let état = {
        bouttons_inactifs: false // Permet de savoir si les boutons de réponse sont inactifs
    };
    let labels = document.querySelectorAll(".réponse");
    fin = document.querySelector(".fin");
    score_final = document.getElementById("final_score");
    nbre_questions = selectible.length;
    
    // Initialiser la barre de progression
    progressText.textContent = `0 / ${nbre_questions}`;
    
    // Pour afficher la toute première première question, 
    // suivant ne pouvant pas encore être cliqué, on appelle poser_question manuellement
    poser_question(pcp, r1, r2, r3, r4, score, essais, feedback, 
        clique_réponse, suivant, état, labels, asked, options, progressBar, progressText);
    // On ajoute un écouteur d'événement pour le bouton "suivant"
    // qui déclenche la fonction poser_question
    // pour afficher une nouvelle question
    suivant.addEventListener("click", function() {
        poser_question(pcp, r1, r2, r3, r4, score, essais, feedback, 
            clique_réponse, suivant, état, labels, asked, options, progressBar, progressText);
    }); 
    // Cliquer sur le bouton "suivant" 
    // (après avoir répondu à une question) déclenche poser_question 
    // qui affiche donc une nouvelle question,
    //  créant ainsi une boucle gérée par Javascript seul 
    // (cela évite les rechargements de page si Flask gérait cette partie)
    clique_réponse.addEventListener("click", function(event) 
    {vérifier_réponse(event, état, feedback, score, suivant, asked, bonne_réponse, essais)});
}

/* Cette fonction organise les données pour chaque question,
en sélectionnant au hasard un arrêt (qui sera la bonne réponse), 
le principe associé à cet arrêt qui sera la question,
et en sélectionnant 3 autres arrêts distracteurs qui seront donc les mauvaises réponses */
function process(asked, options){
    // Avant de poser toute question, on vérifie si la liste d'arrêts est épuisée, 
    // auquel cas on affiche le menu de fin avec le score
    if (selectible.length == 0){ 
        // Mettre à jour la barre de progression à 100%
        let progressBar = document.getElementById("progress-bar");
        let progressText = document.getElementById("progress-text");
        if (progressBar && progressText) {
            progressBar.style.width = '100%';
            progressText.textContent = `${asked.length} / ${asked.length}`;
        }
        
        author_id = document.getElementById("author_id").textContent;
        player_id = document.getElementById("player_id").textContent;
        // On enregistre les scores uniquement pour les quiz publics 
        // et uniquement si le joueur n'est pas l'auteur du quiz
        if (window.quizType == "public" && author_id != player_id) { 
            posées = asked.length;
            matiere = document.getElementById("matiere").textContent;
            quiz_id = document.getElementById("quiz_id").textContent;
            // On envoie les statistiques au serveur pour les enregistrer dans la base de données
            try {
                fetch('/quiz/update_stats', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                },
                    body: `matiere=${encodeURIComponent(matiere)}&posées=
                    ${encodeURIComponent(posées)}&trouvées=${encodeURIComponent(counter)}&quiz_id=${encodeURIComponent(quiz_id)}`
                });
            } catch (error) {
                console.error("Erreur lors de la mise à jour des statistiques :", error);
            }
        }
        document.getElementById("les_réponses").classList.add("disabled");

        fin.hidden = false;
        score_final.textContent = counter + "/" + nbre_questions;
        return;
    }
    /* Sinon, on traite les éléments à afficher pour la question en cours */

    // Je vide le contenu précédent de la liste des options 
    // (donc la liste contenant les 3 réponses distractrices et la bonne réponse)
    options.length = 0; 
    // Je mélange la liste selectible (liste d'où on tire les noms d'arrêts)
    selectible.sort(() => Math.random() - 0.5); 
    // On détermine un index au hasard dans la liste selectible
    let index = Math.floor(Math.random() * (selectible.length));
    // Je tire l'arrêt à l'index choisi au hasard dans la liste selectible
    bonne_réponse = selectible[index]; 
    // Je retire l'arrêt sélectionné de la liste sélectible
    selectible.splice(index, 1); 
    // Je rajoute la bonne réponse dans la liste des options
    options.push(bonne_réponse); 
    // J'extrais de la map le principe associé à la bonne réponse
    let principe = quizMap.get(bonne_réponse); 
    // Je remélange la liste sélectible pour récuprer les 3 réponses distractrices
    selectible.sort(() => Math.random() - 0.5);
     //Je rajoute les arrêts distracteurs 
     // (les 3 premiers éléments de la liste selectible) à la liste des options
    options.push(selectible[0], selectible[1], selectible[2]); 
    let j = 0;
    for (let i = 0; i < options.length; i++){ 
        // Pour chaque élément dans la liste des options
        // Si l'élément est undefined (ce qui arrive dès que la liste selectible 
        // contient désormais moins de 4 arrêts)
        if (!options[i]) {
            // Insérer l'élément j de la liste des questions déjà posées (liste "asked")
            options[i] = asked[j]; 
            j++;
        }
    }
    // Je mélange la liste des options (pour éviter d'avoir toujours le même ordre d'affichage : 
    // bonne réponse, puis les 3 distracteurs)
    options.sort(() => Math.random() - 0.5); 
    return {principe, options}; // Je retourne enfin la question et les 4 options
}


function poser_question(pcp, r1, r2, r3, r4, score, essais, feedback, 
    clique_réponse, suivant, état, labels, asked, options, progressBar, progressText){

    // Mettre à jour la barre de progression
    let questionNumber = asked.length + 1;
    let total = nbre_questions;
    let progressPercent = (asked.length / total) * 100;
    progressBar.style.width = progressPercent + '%';
    progressText.textContent = `${asked.length} / ${total}`;
    
    labels.forEach(function (label) {
        // On retire la couleur verte appliqué à la bonne réponse
        label.parentElement.classList.remove("trouvé"); 
    });
    // On rend les boutons de réponse actifs
    clique_réponse.classList.remove("disabled"); 

    // DÉCOCHER TOUS LES INPUTS RADIO
    let radios = clique_réponse.querySelectorAll('input[type="radio"]');
    radios.forEach(function(radio) {
        radio.checked = false;
    });

    // Je récupère le principe et les 4 options renvoyés par la fonction process
    qa = process(asked, options); 
    // Process retourne un objet, d'où cette syntaxe
    let principe = qa.principe; 
    options = qa.options;

    chances = 1; // L'utilisateur a trois essais pour cliquer sur la bonne réponse
    // On affiche les données dans les éléments HTML appropriés
    essais.textContent = chances;
    pcp.textContent = principe;
    r1.textContent = options[0];
    r2.textContent = options[1];
    r3.textContent = options[2];
    r4.textContent = options[3];
    score.textContent = counter;
    feedback.hidden = true;
    suivant.hidden = true;
    état.bouttons_inactifs = false;
     /* Si on clique sur l'une des réponses (option[0] à option[3]), 
     ça déclenchera la fonction de vérification des réponses */

}

function vérifier_réponse(event, état, feedback, score, suivant, asked, bonne_réponse, essais){
    // On vérifie si l'élément cliqué est un label et que les boutons ne sont pas inactifs
    if (event.target.tagName == "LABEL" && état.bouttons_inactifs == false){ 
        // Si l'utilisateur a cliqué sur la bonne réponse
        if (event.target.textContent == bonne_réponse){
            // On empêche de prendre en compte les clics sur les réponses
            // en mettant à jour l'état des boutons
            état.bouttons_inactifs = true;
            // Supprimer l'une quelconque des deux classes d'alert préexistantes sur feedback
            feedback.classList.remove("alert-danger", "alert-success"); 
            // Rajouter la coloration verte au feedback
            feedback.classList.add("alert", "alert-success"); 
            // Je rajoute la classe "trouvé" au boutton de réponse pour le colorer en vert
            event.target.parentElement.classList.add("trouvé"); 
            // Animation bounce pour la bonne réponse
            event.target.classList.add("bounce");
            setTimeout(() => {
                event.target.classList.remove("bounce");
            }, 600);
            feedback.textContent = "Correct !";
            feedback.style.color = "green";
            feedback.style.margin = "10px";
            feedback.hidden = false;
            // J'incrémente le score de 1 et j'affiche le nouveau score
            counter++;
            score.textContent = counter;
            // Animation pulse pour la boîte score
            let scoreBox = score.closest('.score-box');
            scoreBox.classList.add('pulse');
            setTimeout(() => {
                scoreBox.classList.remove('pulse');
            }, 800);
            // Une fois la réponse vérifiée et juste, 
            // on affiche le bouton "suivant" qui en cas de clic déclenche poser_question
            // qui est la fonction qui affiche la question suivante 
            suivant.hidden = false;  
            // Je rajoute la question à la liste des questions posées
            asked.push(bonne_réponse); 
            // On désactive les boutons de réponse pour éviter de cliquer sur une réponse 
            // après avoir trouvé la bonne réponse donc
            document.getElementById("les_réponses").classList.add("disabled"); 
        }

        // Si l'utilisateur a cliqué sur une mauvaise réponse 
        // et qu'il lui restait seulement une chance
        else if (event.target.textContent != bonne_réponse && chances == 1){ 
            // On affiche la bonne réponse
            feedback.textContent = "Dommage, la bonne réponse était : " + bonne_réponse; 
            // Supprimer l'une quelconque des deux classes d'alert préexistantes sur feedback
            feedback.classList.remove("alert-danger", "alert-success"); 
            // Rajouter la coloratio rouge au feedback
            feedback.classList.add("alert", "alert-danger"); 
            // On colore en rouge la mauvaise réponse cliquée en dernier
            event.target.classList.add("faux"); 
            // Animation shake pour la mauvaise réponse
            event.target.classList.add("shake");
            setTimeout(() => {
                event.target.classList.remove("shake");
            }, 600);
            // La coloration de la mauvaise réponse disparait au bout de 2 secondes
            setTimeout(() => {
                event.target.parentElement.classList.remove("faux");
            }, 2000);
            // chances est maintenant égal à 0, l'utilisateur a épuisé toutes ses chances
            chances--; 
            essais.textContent = chances;
            // Animation pulse pour la boîte essais
            let essaisBox = essais.closest('.essais-box');
            essaisBox.classList.add('pulse');
            setTimeout(() => {
                essaisBox.classList.remove('pulse');
            }, 800);
            état.bouttons_inactifs = true;
            feedback.style.color = "red";
            feedback.style.margin = "10px";
            feedback.hidden = false;
            suivant.hidden = false;
            // On rajoute la question à la liste de questions posées
            asked.push(bonne_réponse);
            // On désactive les boutons de réponse 
            // pour éviter de cliquer sur une réponse après avoir trouvé la bonne
            document.getElementById("les_réponses").classList.add("disabled"); 
        }
        // Enfin, dans le cas où l'utilisateur n'a pas trouvé la bonne réponse 
        // mais qu'il lui reste encore des essais disponibles
        else{ 
            // On affiche que la réponse est incorrecte
            feedback.textContent = "Incorrect";
            // Supprimer l'une quelconque des deux classes d'alert préexistantes
            feedback.classList.remove("alert-danger", "alert-success"); 
            // Rajouter la coloration rouge au feedback
            feedback.classList.add("alert", "alert-danger"); 
            // On colore en rouge pendant 2 secondes la mauvaise réponse cliquée 
            event.target.parentElement.classList.add("faux");
            // Animation shake pour la mauvaise réponse
            event.target.classList.add("shake");
            setTimeout(() => {
                event.target.classList.remove("shake");
            }, 600);
            setTimeout(() => {
                event.target.parentElement.classList.remove("faux");
            }, 2000);
            feedback.style.color = "red";
            feedback.hidden = false;
            chances--;
            essais.textContent = chances;
            // Animation pulse pour la boîte essais
            let essaisBox = essais.closest('.essais-box');
            essaisBox.classList.add('pulse');
            setTimeout(() => {
                essaisBox.classList.remove('pulse');
            }, 800);
        }
    }
}
