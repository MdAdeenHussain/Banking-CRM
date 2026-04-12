// Initialize dashboard when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof initializeDashboard === 'function') {
            initializeDashboard();
        }
    });

