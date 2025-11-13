document.addEventListener("DOMContentLoaded", function() {
        const toggleIcons = document.querySelectorAll(".toggle-password-icon");

    toggleIcons.forEach(function(icon) {
        
        icon.addEventListener("click", function() {

            const inputField = this.parentElement.querySelector('input');

            if (inputField) {
                const type = inputField.getAttribute("type") === "password" ? "text" : "password";
                inputField.setAttribute("type", type);
                
                this.classList.toggle("fa-eye");
                this.classList.toggle("fa-eye-slash");
            }
        });
    });
});