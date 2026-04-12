/**
 * LoanAxis CRM — Duplicate Check
 * Real-time AJAX duplicate detection on lead form.
 */
document.addEventListener('DOMContentLoaded', () => {
    const mobileInput = document.getElementById('mobile_primary');
    const loanTypeSelect = document.getElementById('loan_type');
    const warningDiv = document.getElementById('duplicate-warning');

    if (!mobileInput || !loanTypeSelect) return;

    let debounceTimer;
    function checkDuplicate() {
        clearTimeout(debounceTimer);
        const mobile = mobileInput.value.trim();
        const loanType = loanTypeSelect.value;
        if (mobile.length < 10 || !loanType) {
            if (warningDiv) warningDiv.style.display = 'none';
            return;
        }
        debounceTimer = setTimeout(() => {
            fetch('/leads/api/duplicate-check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mobile_primary: mobile, loan_type: loanType }),
            })
            .then(r => r.json())
            .then(data => {
                if (data.is_duplicate && warningDiv) {
                    const lead = data.existing_lead;
                    warningDiv.innerHTML = `
                        <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
                            <strong>⚠️ Duplicate Detected!</strong><br>
                            Lead #${lead.lead_number} — ${lead.customer_name}<br>
                            Stage: ${lead.pipeline_stage} | Type: ${lead.loan_type}<br>
                            <label class="mt-2 flex items-center gap-2">
                                <input type="checkbox" name="override_duplicate" value="true">
                                Override and create anyway
                            </label>
                        </div>`;
                    warningDiv.style.display = 'block';
                } else if (warningDiv) {
                    warningDiv.style.display = 'none';
                }
            })
            .catch(() => {});
        }, 500);
    }

    mobileInput.addEventListener('input', checkDuplicate);
    loanTypeSelect.addEventListener('change', checkDuplicate);
});
