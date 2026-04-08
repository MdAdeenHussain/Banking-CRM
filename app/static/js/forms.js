/**
 * Shared form behavior for Phase 2.
 * Adds basic validation UI feedback without backend submission.
 */
(function initializeFormValidation() {
  const forms = document.querySelectorAll(".needs-validation");

  forms.forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });
})();
