
document.addEventListener("DOMContentLoaded", function() {
    // Pour chaque textarea ayant une classe .form-control 
    document.querySelectorAll('textarea.form-control').forEach(function(textarea) {
        // Cherche le compteur juste après le textarea
        const count = textarea.parentElement.querySelector('.char-count');
        // Fonction de mise à jour du compteur
        function updateCount() {
            if (count.previousElementSibling.getAttribute('name') === 'question') {
                count.textContent = `${textarea.value.length} / 500`;
            } else if (count.previousElementSibling.getAttribute('name') === 'réponse') {
                count.textContent = `${textarea.value.length} / 200`;
            } else if (count.previousElementSibling.getAttribute('name') === 'msg') {
                count.textContent = `${textarea.value.length} / 500`;
            }
        }
        // Mets à jour au chargement (utile si pré-rempli)
        updateCount();
        // Mets à jour à chaque saisie
        textarea.addEventListener('input', updateCount);
    });
});
