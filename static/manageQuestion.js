
document.addEventListener("DOMContentLoaded", function () {

        // Ajout dynamique d'une nouvelle question
    const addBtn = document.getElementById("add-question-btn");
    const container = document.getElementById("new-question-container");
    const questionCount = parseInt(document.getElementById("question-count").textContent) + 1; 
    const dossier = document.getElementById("dossier").textContent;
    const matiere = document.getElementById("matiere").textContent

    addBtn.addEventListener("click", function () {
      const createNewQuestion = `/quiz/add_new_question?dossier=${encodeURIComponent(dossier)}&matiere=${encodeURIComponent(matiere)}`;
      const section = document.createElement("section");
      section.className = "container text-center py-5";
      section.style = "display: flex; justify-content: center; align-items: center; flex-direction: column; margin-top: 10px; background: linear-gradient(135deg, #e6ecf7, #d9dee8, #b3b6bb, #bfc6d3, #cfdef1); border-radius: 15px; border: 1px solid linear gradient (90 deg, #e6ecf7, #d9dee8, #edf2fb, #bfc6d3, #cfdef3)";

      section.innerHTML = `
        <form action="${createNewQuestion}" method="post" style="width: 80vw">
          <div class="mb-3">
            <label class="form-label">Question ${questionCount}</label>
            <textarea style="border: none;" class="form-control" name="question" rows="5" placeholder="Entrez le principe" required></textarea>
          </div>
          <div class="mb-3">
            <label class="form-label">Réponse ${questionCount}</label>
            <textarea style="border: none;" class="form-control" name="réponse" rows="5" placeholder="Entrez la référence du principe" required></textarea>
          </div>
          <button class="btn btn-primary" style="background: linear-gradient(90deg, #00bcd4, #0097a7); border: none;" type="submit">Enregistrer</button>
        </form>
      `;
      container.appendChild(section);
      questionCount++;
    });

    let delete_question = document.querySelectorAll(".delete_question");
    let confirmDeletion = document.getElementById("confirm_deletion");

        delete_question.forEach(function(element) {
            element.addEventListener("click", function(event) {
                event.preventDefault(); // Empêche le lien de rediriger immédiatement
                let deletion_confirmed = document.getElementById("deletion_confirmed");
                let deletion_cancelled = document.getElementById("deletion_cancelled");
                let questionNumber = element.parentElement.previousElementSibling.getAttribute("data-index");
                document.getElementById("question_number").textContent = questionNumber;
                confirmDeletion.hidden = false;
                deletion_confirmed.addEventListener("click", function(){
                    element.parentElement.submit(); // Soumet le formulaire en POST
                    confirmDeletion.hidden = true; // Cache la confirmation de suppression
                })
                deletion_cancelled.addEventListener("click", function(){
                    confirmDeletion.hidden = true; // Cache la confirmation de suppression
                })
            });
        });

  });
