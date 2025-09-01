
document.addEventListener("DOMContentLoaded", function() {
    let nouveauDoc = document.getElementById("nouveau_dossier");
    let createNewDoc = document.getElementById("createdoc");
    nouveauDoc.addEventListener("click", function() {
        if (createNewDoc.hidden == true){
            createNewDoc.hidden = false;
        }
        else {
            createNewDoc.hidden = true;
        }
    });

    let renameFile = document.querySelectorAll(".renommer");
    renameFile.forEach(function(element){
        element.addEventListener("click", function(event) {
            let form = element.parentElement.parentElement.nextElementSibling;
            if (form && form.classList.contains("renamedoc")){
                // Affiche ou cache le formulaire de renommage
                form.hidden = !form.hidden;
            }
            else { 
                // Si le formulaire de renommage n'est pas trouvé, 
                // on regarde le voisin du parent
                form = element.parentElement.nextElementSibling; 
                form.hidden = !form.hidden;
            } 
        });
    });
    
    let delete_file = document.querySelectorAll(".delete_file");
    let confirmDeletion = document.getElementById("confirm_deletion");
    delete_file.forEach(function(element) {
        element.addEventListener("click", function(event) {
            event.preventDefault(); // Empêche le lien de rediriger immédiatement
            let deletion_confirmed = document.getElementById("deletion_confirmed");
            let deletion_cancelled = document.getElementById("deletion_cancelled");
            let fileToDelete = document.getElementById("file_to_delete");
            fileToDelete.textContent = element.name;
            confirmDeletion.hidden = false;
            deletion_confirmed.addEventListener("click", function(){
                // Rediriger vers le lien de suppression
                window.location.href = element.href; 
            })
            deletion_cancelled.addEventListener("click", function(){
                confirmDeletion.hidden = true; // Cache la confirmation de suppression
            })
        });
    });
});
