docuement.addEventListener("DOMContentLoaded", function() {
    window.quizType = document.getElementById("quiztype").textContent;
    if (window.quizType == "public"){
        window.collectArretsRoute = "{{ url_for('quiz.get_public_questions') }}";
    } else if (window.quizType == "private") {
        window.collectArretsRoute = "{{ url_for('quiz.get_private_questions') }}";
    }
    window.quizlengtherrorRoute = "{{ url_for('quiz.quizlengtherror') }}";
});

