document.addEventListener('DOMContentLoaded', function() {
    
    // Éléments DOM
    const deleteAccountBtn = document.getElementById('delete_account_btn');
    const confirmDeletion = document.getElementById('confirm_deletion');
    const deleteForm = document.getElementById('delete_account_form');
    const passwordInput = document.getElementById('confirmation_password');
    const cancelBtn = document.getElementById('cancel_delete_btn');
    const passwordError = document.getElementById('password_error');
    
    // Afficher la modal de confirmation au clic sur le bouton
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function() {
            confirmDeletion.hidden = false;
            
            // Focus automatique sur le champ mot de passe
            setTimeout(() => passwordInput.focus(), 100);
            
            // Réinitialiser le formulaire
            passwordInput.value = '';
            passwordError.style.display = 'none';
            passwordInput.style.borderColor = '#bfc6d3';
        });
    }
    
    // Fermer la modal au clic sur Annuler
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            confirmDeletion.hidden = true;
        });
    }
    
    // Validation du formulaire avant soumission
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            const password = passwordInput.value.trim();
            
            if (!password) {
                e.preventDefault();
                passwordError.textContent = 'Veuillez entrer votre mot de passe';
                passwordError.style.display = 'block';
                passwordInput.style.borderColor = '#dc3545';
                passwordInput.focus();
                return;
            }
            
            // Si tout est OK, désactiver le bouton pour éviter double soumission
            const submitBtn = document.getElementById('confirm_delete_btn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Suppression en cours...';
        });
    }
    
    // Validation en temps réel
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            if (this.value.trim()) {
                passwordError.style.display = 'none';
                this.style.borderColor = '#28a745';
            } else {
                this.style.borderColor = '#bfc6d3';
            }
        });
        
        // Permettre soumission avec Entrée
        passwordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && this.value.trim()) {
                deleteForm.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    // Code existant pour suppression email (inchangé)
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
