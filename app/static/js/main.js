/**
 * DSA CRM - Main JavaScript File
 * Handles common functionality across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeToggleMenus();
    initializeNotifications();
    initializeFormValidation();
    initializeDataBind();
});

/**
 * Toggle User Menu and Notifications Dropdown
 */
function initializeToggleMenus() {
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    const notificationBell = document.getElementById('notificationBell');
    const notificationDropdown = document.getElementById('notificationDropdown');
    
    // User Menu Toggle
    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.style.display = userDropdown.style.display === 'none' ? 'block' : 'none';
            if (notificationDropdown) notificationDropdown.style.display = 'none';
        });
    }
    
    // Notification Bell Toggle
    if (notificationBell && notificationDropdown) {
        notificationBell.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationDropdown.style.display = notificationDropdown.style.display === 'none' ? 'block' : 'none';
            if (userDropdown) userDropdown.style.display = 'none';
        });
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        if (userDropdown) userDropdown.style.display = 'none';
        if (notificationDropdown) notificationDropdown.style.display = 'none';
    });
}

/**
 * Initialize Notifications
 */
function initializeNotifications() {
    fetchNotifications();
    // Refresh notifications every 30 seconds
    setInterval(fetchNotifications, 30000);
}

function fetchNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            const notificationList = document.getElementById('notificationList');
            const notificationCount = document.getElementById('notificationCount');
            
            if (data.notifications && data.notifications.length > 0) {
                notificationCount.textContent = data.unread_count;
                let html = '';
                data.notifications.forEach(notif => {
                    html += `
                        <div class="notification-item" onclick="markNotificationAsRead('${notif.id}')">
                            <div class="notification-title">${notif.title}</div>
                            <div class="notification-message">${notif.message}</div>
                            <div class="notification-time">${formatTime(notif.created_at)}</div>
                        </div>
                    `;
                });
                if (notificationList) notificationList.innerHTML = html;
            }
        })
        .catch(error => console.log('Error fetching notifications:', error));
}

function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/mark-read`, {method: 'POST'})
        .then(response => response.json())
        .then(data => fetchNotifications())
        .catch(error => console.log('Error marking notification as read:', error));
}

/**
 * Initialize Form Validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    const inputs = form.querySelectorAll('[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showError(input, 'This field is required');
            isValid = false;
        } else if (input.type === 'email' && !isValidEmail(input.value)) {
            showError(input, 'Invalid email address');
            isValid = false;
        }
    });
    
    return isValid;
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showError(input, message) {
    input.classList.add('error');
    let errorDiv = input.nextElementSibling;
    if (!errorDiv || !errorDiv.classList.contains('error-message')) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        input.parentNode.insertBefore(errorDiv, input.nextSibling);
    }
    errorDiv.textContent = message;
}

function clearError(input) {
    input.classList.remove('error');
    const errorDiv = input.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains('error-message')) {
        errorDiv.remove();
    }
}

/**
 * Global Search
 */
function initializeDataBind() {
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        globalSearch.addEventListener('keyup', debounce(function(e) {
            const query = e.target.value;
            if (query.length > 2) {
                performGlobalSearch(query);
            }
        }, 300));
    }
}

function performGlobalSearch(query) {
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            console.log('Search results:', data);
            // Display search results in dropdown
        })
        .catch(error => console.log('Search error:', error));
}

/**
 * Utility Functions
 */
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

function formatTime(isoString) {
    const date = new Date(isoString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function formatPhoneNumber(phone) {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
        return `+91 ${cleaned.substring(0, 5)} ${cleaned.substring(5)}`;
    }
    return phone;
}

/**
 * Show Alert/Toast
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} fade-in`;
    alert.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 1.2rem;">×</button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 10000; max-width: 400px;';
    document.body.appendChild(container);
    return container;
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Export functions for use in other scripts
 */
window.CRM = {
    showAlert: showAlert,
    formatCurrency: formatCurrency,
    formatPhoneNumber: formatPhoneNumber,
    formatTime: formatTime,
    debounce: debounce
};
