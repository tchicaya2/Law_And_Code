
document.addEventListener("DOMContentLoaded", function () {
    const message = document.getElementById("message") || document.getElementById("error_msg");
    if (message) {
    setTimeout(() => {
        message.style.transition = "opacity 0.5s";
        message.style.opacity = 0;

        setTimeout(() => message.remove(), 500); // supprime l'élément du DOM
    }, 3000); // délai avant disparition (3 secondes)
    }
});