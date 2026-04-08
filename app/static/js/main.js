/**
 * Main JavaScript for LoanCRM
 * Handles UI interactions, form validation, and utilities
 */

// ============================================
// DOM Helpers
// ============================================

function $(selector) {
    return document.querySelector(selector);
}

function $$(selector) {
    return document.querySelectorAll(selector);
}

// ============================================
// Sidebar Menu Toggle
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu button
    const mobileMenuBtn = $('#mobile-menu-btn');
    const sidebar = document.querySelector('aside');
    
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', function() {
            sidebar.classList.toggle('hidden');
        });
    }
    
    // Sidebar collapse/expand submenu
    const collapseButtons = $$('[data-toggle]');
    collapseButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const menuId = this.getAttribute('data-toggle');
            const menu = $(`#${menuId}`);
            const chevron = this.querySelector('.fa-chevron-right');
            
            if (menu) {
                menu.classList.toggle('hidden');
                if (chevron) {
                    chevron.style.transform = menu.classList.contains('hidden') ? 'rotate(0)' : 'rotate(90deg)';
                }
            }
        });
    });
    
    // User dropdown menu
    const userMenu = $('#user-menu');
    if (userMenu) {
        const btn = userMenu.querySelector('button');
        const dropdown = userMenu.querySelector('[class*="absolute"]');
        
        if (btn && dropdown) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                dropdown.classList.toggle('hidden');
            });
            
            document.addEventListener('click', function(e) {
                if (!userMenu.contains(e.target)) {
                    dropdown.classList.add('hidden');
                }
            });
        }
    }
});

// ============================================
// Form Validation
// ============================================

/**
 * Validate email format
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate password strength
 */
function validatePassword(password) {
    // Minimum 8 chars, at least one uppercase, one lowercase, one number
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return re.test(password);
}

/**
 * Validate tenant slug format
 */
function validateSlug(slug) {
    const re = /^[a-z0-9-]+$/;
    return re.test(slug) && slug.length >= 3;
}

/**
 * Validate PAN format (Indian)
 */
function validatePAN(pan) {
    const re = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
    return re.test(pan);
}

/**
 * Validate Aadhaar format (Indian)
 */
function validateAadhaar(aadhaar) {
    const re = /^[0-9]{12}$/;
    return re.test(aadhaar);
}

/**
 * Validate phone number (Indian)
 */
function validatePhone(phone) {
    const re = /^[6-9]\d{9}$/;
    return re.test(phone);
}

/**
 * Show validation error on field
 */
function showFieldError(fieldId, message) {
    const field = $(`#${fieldId}`);
    if (!field) return;
    
    field.classList.add('border-red-500', 'focus:ring-red-500');
    
    let errorDiv = field.nextElementSibling;
    if (!errorDiv || !errorDiv.classList.contains('error-message')) {
        errorDiv = document.createElement('p');
        errorDiv.className = 'error-message text-red-600 text-xs mt-1';
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }
    errorDiv.textContent = message;
}

/**
 * Clear validation error on field
 */
function clearFieldError(fieldId) {
    const field = $(`#${fieldId}`);
    if (!field) return;
    
    field.classList.remove('border-red-500', 'focus:ring-red-500');
    
    const errorDiv = field.parentNode.querySelector('.error-message');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// ============================================
// Alerts and Notifications
// ============================================

/**
 * Show a toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-3 rounded-lg text-white text-sm fade-in z-50 ${
        type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' :
        type === 'warning' ? 'bg-yellow-600' :
        'bg-blue-600'
    }`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show a modal dialog
 */
function showModal(title, content, buttons = {}) {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    
    const titleEl = document.createElement('h2');
    titleEl.className = 'text-xl font-bold mb-4';
    titleEl.textContent = title;
    
    const contentEl = document.createElement('div');
    contentEl.className = 'mb-6 text-gray-700';
    contentEl.innerHTML = content;
    
    const buttonsDiv = document.createElement('div');
    buttonsDiv.className = 'flex justify-end space-x-3';
    
    Object.entries(buttons).forEach(([label, callback]) => {
        const btn = document.createElement('button');
        btn.className = label === 'Close' || label === 'Cancel' 
            ? 'px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300'
            : 'px-4 py-2 text-white bg-indigo-600 rounded hover:bg-indigo-700';
        btn.textContent = label;
        btn.addEventListener('click', () => {
            if (callback) callback();
            modal.remove();
        });
        buttonsDiv.appendChild(btn);
    });
    
    modalContent.appendChild(titleEl);
    modalContent.appendChild(contentEl);
    modalContent.appendChild(buttonsDiv);
    modal.appendChild(modalContent);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    document.body.appendChild(modal);
}

// ============================================
// API Helpers
// ============================================

/**
 * Make API request with error handling
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast('An error occurred. Please try again.', 'error');
        throw error;
    }
}

// ============================================
// Utility Functions
// ============================================

/**
 * Format date to readable format
 */
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
    }).format(date);
}

/**
 * Format currency (Indian Rupee)
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

/**
 * Debounce function for search/input
 */
function debounce(func, delay = 300) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), delay);
    };
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard', 'success', 2000);
    }).catch(err => {
        console.error('Copy failed:', err);
    });
}

/**
 * Get URL query parameters
 */
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Redirect to URL
 */
function redirect(url) {
    window.location.href = url;
}

// ============================================
// Export for use in other files
// ============================================

window.LoanCRM = {
    validateEmail,
    validatePassword,
    validateSlug,
    validatePAN,
    validateAadhaar,
    validatePhone,
    showFieldError,
    clearFieldError,
    showToast,
    showModal,
    apiRequest,
    formatDate,
    formatCurrency,
    debounce,
    copyToClipboard,
    getQueryParam,
    redirect
};
