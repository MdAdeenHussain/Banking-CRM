// Load KPI data
    async function loadKPIs() {
        const response = await fetch('/dashboard/api/kpis');
        const data = await response.json();
        
        document.getElementById('total-leads').textContent = data.total_leads;
        document.getElementById('converted-leads').textContent = data.converted_leads;
        document.getElementById('conversion-rate').textContent = data.conversion_rate;
        document.getElementById('total-commission').textContent = '₹ ' + data.total_commission.toLocaleString();
        document.getElementById('pending-commission').textContent = '₹ ' + data.pending_commission.toLocaleString();
        document.getElementById('disbursed-amount').textContent = '₹ ' + data.disbursed_amount.toLocaleString();
        document.getElementById('active-employees').textContent = data.active_employees;
        document.getElementById('pending-tasks').textContent = data.pending_tasks;
    }

    loadKPIs();
    setInterval(loadKPIs, 60000); // Refresh every minute

