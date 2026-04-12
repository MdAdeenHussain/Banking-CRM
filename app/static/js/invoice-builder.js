/**
 * LoanAxis CRM — Invoice Builder
 * Dynamic line items with GST auto-calculation.
 */
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('line-items-container');
    const addBtn = document.getElementById('add-line-item');
    const lineItemsInput = document.getElementById('line_items_json');
    if (!container || !addBtn) return;

    let itemCount = 0;

    function addLineItem() {
        itemCount++;
        const row = document.createElement('div');
        row.className = 'grid grid-cols-12 gap-2 items-center line-item mb-2';
        row.innerHTML = `
            <input type="text" placeholder="Description" class="col-span-4 form-control form-control-sm li-desc">
            <input type="text" placeholder="HSN/SAC" class="col-span-2 form-control form-control-sm li-hsn">
            <input type="number" placeholder="Qty" value="1" min="1" class="col-span-1 form-control form-control-sm li-qty">
            <input type="number" placeholder="Rate" step="0.01" class="col-span-2 form-control form-control-sm li-rate">
            <input type="number" placeholder="Amount" readonly class="col-span-2 form-control form-control-sm li-amount" style="background:#f8fafc;">
            <button type="button" class="col-span-1 btn-icon btn-sm remove-line-item">&times;</button>
        `;
        container.appendChild(row);

        const qty = row.querySelector('.li-qty');
        const rate = row.querySelector('.li-rate');
        const amount = row.querySelector('.li-amount');
        const removeBtn = row.querySelector('.remove-line-item');

        function calcAmount() {
            amount.value = ((parseFloat(qty.value) || 0) * (parseFloat(rate.value) || 0)).toFixed(2);
            updateTotals();
        }
        qty.addEventListener('input', calcAmount);
        rate.addEventListener('input', calcAmount);
        removeBtn.addEventListener('click', () => { row.remove(); updateTotals(); });
    }

    function updateTotals() {
        const items = [];
        container.querySelectorAll('.line-item').forEach(row => {
            const desc = row.querySelector('.li-desc').value;
            const hsn = row.querySelector('.li-hsn').value;
            const qty = parseFloat(row.querySelector('.li-qty').value) || 0;
            const rate = parseFloat(row.querySelector('.li-rate').value) || 0;
            const amount = qty * rate;
            items.push({ description: desc, hsn_sac: hsn, qty, rate, amount: parseFloat(amount.toFixed(2)) });
        });
        if (lineItemsInput) lineItemsInput.value = JSON.stringify(items);

        const subtotal = items.reduce((s, i) => s + i.amount, 0);
        const subtotalEl = document.getElementById('display-subtotal');
        if (subtotalEl) subtotalEl.textContent = '₹' + subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 });
    }

    addBtn.addEventListener('click', addLineItem);
    addLineItem(); // Start with one row
});
