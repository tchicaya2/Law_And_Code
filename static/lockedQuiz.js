document.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll('.réponse').forEach(function(item) {
    item.addEventListener('click', function(e) {
      const count = parseInt(this.getAttribute('data-count'));
      if (count < 4) {
        e.preventDefault();
        const msg = document.getElementById('locked-quiz-message');
        msg.style.display = 'block';
        clearTimeout(msg._timeout);
        msg._timeout = setTimeout(() => {
          msg.style.display = 'none';
        }, 5000);
      }
      // Sinon, le lien fonctionne normalement
    });
  });
});