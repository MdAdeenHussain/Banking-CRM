/**
 * LoanAxis CRM — Charts Factory
 * Initializes all Chart.js charts on the analytics page.
 */
document.addEventListener('DOMContentLoaded', () => {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16, font: { family: 'DM Sans' } } },
        },
    };

    function loadChart(elId, url, builder) {
        const el = document.getElementById(elId);
        if (!el) return;
        fetch(url).then(r => r.json()).then(data => builder(el, data)).catch(console.error);
    }

    // Monthly Leads vs Disbursals
    loadChart('monthlyChart', '/analytics/api/monthly-leads', (el, data) => {
        new Chart(el, {
            type: 'bar', data: {
                labels: data.labels,
                datasets: [
                    { label: 'Leads', data: data.leads, backgroundColor: 'rgba(108,99,255,0.7)', borderRadius: 8 },
                    { label: 'Disbursals', data: data.disbursals, backgroundColor: 'rgba(34,197,94,0.7)', borderRadius: 8 },
                ]
            }, options: { ...chartOptions, scales: { y: { beginAtZero: true } } }
        });
    });

    // Conversion Funnel
    loadChart('funnelChart', '/analytics/api/conversion-funnel', (el, data) => {
        new Chart(el, {
            type: 'bar', data: {
                labels: Object.keys(data), datasets: [{
                    data: Object.values(data),
                    backgroundColor: ['#94A3B8','#3B82F6','#F59E0B','#6366F1','#8B5CF6','#14B8A6','#22C55E','#EF4444','#1E293B'],
                    borderRadius: 6,
                }]
            }, options: { ...chartOptions, indexAxis: 'y', plugins: { legend: { display: false } } }
        });
    });

    // Lead Sources (Donut)
    loadChart('sourceChart', '/analytics/api/lead-sources', (el, data) => {
        new Chart(el, {
            type: 'doughnut', data: {
                labels: Object.keys(data), datasets: [{
                    data: Object.values(data),
                    backgroundColor: ['#6C63FF','#FF6B9D','#22C55E','#F59E0B','#3B82F6','#8B5CF6','#14B8A6','#EF4444'],
                }]
            }, options: { ...chartOptions, cutout: '65%' }
        });
    });

    // Loan Types (Pie)
    loadChart('loanTypeChart', '/analytics/api/loan-types', (el, data) => {
        new Chart(el, {
            type: 'pie', data: {
                labels: Object.keys(data), datasets: [{
                    data: Object.values(data),
                    backgroundColor: ['#6C63FF','#FF6B9D','#22C55E','#F59E0B','#3B82F6','#8B5CF6','#14B8A6','#EF4444','#64748B'],
                }]
            }, options: chartOptions
        });
    });

    // Commission Trend (Area)
    loadChart('commTrendChart', '/analytics/api/commission-trend', (el, data) => {
        new Chart(el, {
            type: 'line', data: {
                labels: data.labels, datasets: [{
                    label: 'Commission (₹)', data: data.values,
                    borderColor: '#6C63FF', backgroundColor: 'rgba(108,99,255,0.1)',
                    fill: true, tension: 0.4, pointRadius: 3,
                }]
            }, options: { ...chartOptions, scales: { y: { beginAtZero: true } } }
        });
    });

    // CIBIL Distribution
    loadChart('cibilChart', '/analytics/api/cibil-distribution', (el, data) => {
        new Chart(el, {
            type: 'bar', data: {
                labels: Object.keys(data), datasets: [{
                    label: 'Leads', data: Object.values(data),
                    backgroundColor: ['#EF4444','#F59E0B','#F59E0B','#22C55E','#22C55E','#3B82F6','#6C63FF'],
                    borderRadius: 6,
                }]
            }, options: { ...chartOptions, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
        });
    });
});
