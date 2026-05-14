// =====================================================
// AUTO CERRAR ALERTAS
// =====================================================
setTimeout(() => {

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(alert => {

        alert.style.transition = "0.5s";
        alert.style.opacity = "0";

        setTimeout(() => {
            alert.remove();
        }, 500);

    });

}, 4000);


// =====================================================
// PREVENIR DOBLE SUBMIT
// =====================================================
document.addEventListener("submit", function(e) {

    const form = e.target;

    const submitButtons = form.querySelectorAll(
        "button[type='submit']"
    );

    submitButtons.forEach(button => {

        button.disabled = true;

        const original = button.innerHTML;

        button.dataset.original = original;

        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Procesando...
        `;

    });

});