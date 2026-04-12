/**
 * LoanAxis CRM — Dashboard JavaScript
 * KPI count-up animations and chart initialization.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── Count-Up Animation ───────────────────────────
    document.querySelectorAll('[data-count-to]').forEach(el => {
        const target = parseFloat(el.dataset.countTo);
        const prefix = el.dataset.prefix || '';
        const suffix = el.dataset.suffix || '';
        const isFloat = el.dataset.decimal === 'true';
        const duration = 1500;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;

            if (isFloat) {
                el.textContent = prefix + current.toLocaleString('en-IN', { maximumFractionDigits: 0 }) + suffix;
            } else {
                el.textContent = prefix + Math.floor(current).toLocaleString('en-IN') + suffix;
            }

            if (progress < 1) requestAnimationFrame(update);
        }

        requestAnimationFrame(update);
    });

    // ── Monthly Leads Bar Chart ──────────────────────
    const monthlyChartEl = document.getElementById('monthlyLeadsChart');
    if (monthlyChartEl) {
        fetch('/api/monthly-leads')
            .then(r => r.json())
            .then(data => {
                new Chart(monthlyChartEl, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Leads',
                            data: data.values,
                            backgroundColor: 'rgba(108, 99, 255, 0.7)',
                            borderRadius: 8,
                            borderSkipped: false,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                            x: { grid: { display: false } },
                        }
                    }
                });
            })
            .catch(() => {});
    }

    // ── Pipeline Funnel Chart ────────────────────────
    const funnelChartEl = document.getElementById('pipelineFunnelChart');
    if (funnelChartEl) {
        fetch('/api/pipeline-summary')
            .then(r => r.json())
            .then(data => {
                const labels = Object.keys(data);
                const values = Object.values(data);
                const colors = ['#94A3B8', '#3B82F6', '#F59E0B', '#6366F1', '#8B5CF6', '#14B8A6', '#22C55E', '#EF4444', '#1E293B'];

                new Chart(funnelChartEl, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values,
                            backgroundColor: colors,
                            borderRadius: 6,
                            borderSkipped: false,
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                            y: { grid: { display: false } },
                        }
                    }
                });
            })
            .catch(() => {});
    }
});
