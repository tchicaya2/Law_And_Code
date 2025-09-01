document.addEventListener("DOMContentLoaded", function() {
    
    let delete_account = document.getElementById("delete_account");
    let confirmDeletion = document.getElementById("confirm_deletion");
    delete_account.addEventListener("click", function(event) {
            event.preventDefault(); // Empêche le lien de rediriger immédiatement
            let deletion_confirmed = document.getElementById("deletion_confirmed");
            let deletion_cancelled = document.getElementById("deletion_cancelled");
            confirmDeletion.hidden = false;
            deletion_confirmed.addEventListener("click", function(){
                // Rediriger vers le lien de suppression
                window.location.href = delete_account.href; 
            })
            deletion_cancelled.addEventListener("click", function(){
                confirmDeletion.hidden = true; // Cache la confirmation de suppression
            })
        });
        // Pour la suppression de l'email
        const removeEmailBtn = document.getElementById("remove-email-btn");
        if (removeEmailBtn) {
            removeEmailBtn.addEventListener("click", function(event) {
                event.preventDefault();
                
                if (confirm("Êtes-vous sûr de vouloir supprimer votre adresse email ?\n\nVous ne pourrez plus récupérer votre mot de passe par email.")) {
                    document.getElementById("remove-email-form").submit();
                }
            });
        }
});
