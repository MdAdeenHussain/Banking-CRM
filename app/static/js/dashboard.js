/**
 * Dashboard Functions
 * Handles dashboard interactions, data loading, and updates
 * Implements Neumorphism + Bento Grid + Data UI
 */

let dashboardCharts = {};
let autoRefreshInterval = null;

/**
 * Initialize dashboard
 */
function initializeDashboard() {
    console.log('Initializing dashboard...');
    
    loadDashboardData();
    setUpDashboardEventListeners();
    attachRefreshHandlers();
    setupAutoRefresh();
    animateDashboardCards();
}

/**
 * Setup auto-refresh of dashboard data
 */
function setupAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
        loadDashboardData();
    }, 30000); // Refresh every 30 seconds
}

/**
 * Load dashboard data
 */
async function loadDashboardData() {
    try {
        const response = await fetch('/dashboard/api/kpis').then(res => res.json());
        updateDashboardUI(response);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

/**
 * Update dashboard UI with data
 */
function updateDashboardUI(data) {
    updateKPICards(data.kpis || {});
    updateActivityFeed(data.activities || []);
    updateCharts(data);
}

/**
 * Update KPI cards
 */
function updateKPICards(kpis) {
    Object.keys(kpis).forEach(key => {
        const element = document.querySelector(`[data-kpi="${key}"]`);
        if (element) {
            const value = document.querySelector(`[data-kpi="${key}"] .value`);
            const trend = document.querySelector(`[data-kpi="${key}"] .trend`);
            
            if (value) value.textContent = formatValue(kpis[key].value);
            if (trend && kpis[key].trend) {
                trend.textContent = `${kpis[key].trend}%`;
                trend.classList.toggle('positive', kpis[key].trend >= 0);
                trend.classList.toggle('negative', kpis[key].trend < 0);
            }
        }
    });
}

/**
 * Update activity feed
 */
function updateActivityFeed(activities) {
    const feedContainer = document.querySelector('.activity-feed');
    if (!feedContainer) return;
    
    feedContainer.innerHTML = activities
        .slice(0, 10)
        .map(activity => `
            <div class="activity-item">
                <span class="activity-badge ${activity.type}">${activity.type}</span>
                <div class="activity-content">
                    <p>${activity.message}</p>
                    <small>${formatDate(activity.timestamp)}</small>
                </div>
            </div>
        `).join('');
}

/**
 * Initialize dashboard charts
 */
function initializeDashboardCharts(data) {
    // Create performance chart
    if (document.getElementById('performanceChart')) {
        dashboardCharts.performance = createPerformanceChart(
            'performanceChart',
            data.months,
            data.performance
        );
    }
    
    // Create comparison chart
    if (document.getElementById('conversionChart')) {
        dashboardCharts.conversion = createBarChart(
            'conversionChart',
            {
                labels: data.banks,
                datasets: [{
                    label: 'Conversion Rate',
                    data: data.conversionRates,
                    backgroundColor: CHART_COLORS.success
                }]
            }
        );
    }
    
    // Create pie chart
    if (document.getElementById('statusChart')) {
        dashboardCharts.status = createPieChart(
            'statusChart',
            {
                labels: ['Active', 'Inactive', 'Pending'],
                datasets: [{
                    data: [data.active, data.inactive, data.pending],
                    backgroundColor: [
                        CHART_COLORS.success,
                        CHART_COLORS.danger,
                        CHART_COLORS.warning
                    ]
                }]
            }
        );
    }
}

/**
 * Set up dashboard event listeners
 */
function setUpDashboardEventListeners() {
    // Period selector buttons
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const period = this.getAttribute('data-period');
            handlePeriodChange(period);
        });
    });
    
    // Refresh button
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadDashboardData);
    }
    
    // Tab switching
    document.querySelectorAll('.nav-tabs .nav-link').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const tabId = this.getAttribute('data-bs-target');
            showTab(tabId);
        });
    });
}

/**
 * Handle period change
 */
async function handlePeriodChange(period) {
    try {
        const response = await apiGet('/api/dashboard/data', { period: period });
        updateDashboardUI(response);
        
        updateActivePeriodButton(period);
    } catch (error) {
        console.error('Failed to load period data:', error);
        showNotification('Failed to load data for selected period', 'error');
    }
}

/**
 * Update active period button
 */
function updateActivePeriodButton(period) {
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-period') === period);
    });
}

/**
 * Attach refresh handlers for auto-update
 */
function attachRefreshHandlers() {
    // Auto-refresh every 5 minutes
    setInterval(loadDashboardData, 5 * 60 * 1000);
}

/**
 * Show tab content
 */
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active', 'show');
    });
    
    const tabContent = document.querySelector(tabId);
    if (tabContent) {
        tabContent.classList.add('active', 'show');
    }
}

/**
 * Animate dashboard cards on load
 */
function animateDashboardCards() {
    const cards = document.querySelectorAll('.kpi-card, .neu-card');
    cards.forEach((card, index) => {
        card.style.animation = `none`;
        setTimeout(() => {
            card.classList.add('animate-fade-in');
        }, index * 50);
    });
}

/**
 * Format value with currency or number format
 */
function formatValue(value) {
    if (typeof value === 'number') {
        if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K';
        }
        return value.toLocaleString();
    }
    return value;
}

/**
 * Clean up on page unload
 */
window.addEventListener('beforeunload', function() {
    Object.keys(dashboardCharts).forEach(key => {
        destroyChart(dashboardCharts[key]);
    });
});

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
}
