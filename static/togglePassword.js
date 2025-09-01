document.addEventListener("DOMContentLoaded", function() {
      const togglePassword = document.querySelectorAll(".togglePassword");

      togglePassword.forEach(function(element) {
        element.addEventListener("click", function() {
          const passwordInput = element.parentElement.querySelector("input");
          const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
          passwordInput.setAttribute("type", type);
          this.querySelector("i").classList.toggle("fa-eye-slash");
        });
      });
});