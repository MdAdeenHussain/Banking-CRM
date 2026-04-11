/**
 * Notification System
 * Handles toast notifications, alerts, and user feedback
 */

// Notification configuration
const NOTIFICATION_CONFIG = {
    position: 'top-right',
    duration: 3000,
    maxNotifications: 3
};

let notificationQueue = [];

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = NOTIFICATION_CONFIG.duration) {
    const notification = createNotificationElement(message, type);
    
    const container = document.getElementById('notification-container') ||
                     createNotificationContainer();
    
    container.appendChild(notification);
    notificationQueue.push(notification);
    
    // Limit number of notifications
    while (notificationQueue.length > NOTIFICATION_CONFIG.maxNotifications) {
        const old = notificationQueue.shift();
        old.remove();
    }
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            removeNotification(notification);
        }, duration);
    }
    
    return notification;
}

/**
 * Create notification element
 */
function createNotificationElement(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icons[type] || icons.info}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    return notification;
}

/**
 * Create notification container
 */
function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.className = 'notification-container';
    
    const style = document.createElement('style');
    style.textContent = `
        .notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        }
        
        .notification {
            margin: 10px 0;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: center;
        }
        
        .notification-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        
        .notification-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        
        .notification-warning {
            background: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffc107;
        }
        
        .notification-info {
            background: #d1ecf1;
            color: #0c5460;
            border-left: 4px solid #17a2b8;
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            width: 100%;
        }
        
        .notification-icon {
            font-weight: bold;
            margin-right: 12px;
            font-size: 1.2em;
        }
        
        .notification-message {
            flex: 1;
        }
        
        .notification-close {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            opacity: 0.7;
            padding: 0;
            margin-left: 12px;
            transition: opacity 0.2s;
        }
        
        .notification-close:hover {
            opacity: 1;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @media (max-width: 768px) {
            .notification-container {
                right: 10px;
                left: 10px;
                max-width: none;
            }
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(container);
    
    return container;
}

/**
 * Remove notification
 */
function removeNotification(notification) {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => {
        notification.remove();
        notificationQueue = notificationQueue.filter(n => n !== notification);
    }, 300);
}

/**
 * Show success notification
 */
function notifySuccess(message) {
    return showNotification(message, 'success');
}

/**
 * Show error notification
 */
function notifyError(message) {
    return showNotification(message, 'error', 5000);
}

/**
 * Show warning notification
 */
function notifyWarning(message) {
    return showNotification(message, 'warning', 4000);
}

/**
 * Show info notification
 */
function notifyInfo(message) {
    return showNotification(message, 'info');
}

/**
 * Show confirmation dialog
 */
function showConfirmDialog(title, message, onConfirm, onCancel) {
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog-overlay';
    
    dialog.innerHTML = `
        <div class="confirm-dialog">
            <h4>${title}</h4>
            <p>${message}</p>
            <div class="dialog-buttons">
                <button class="btn btn-secondary" id="cancelBtn">Cancel</button>
                <button class="btn btn-primary" id="confirmBtn">Confirm</button>
            </div>
        </div>
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        .confirm-dialog-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10001;
        }
        
        .confirm-dialog {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            max-width: 400px;
            text-align: center;
        }
        
        .dialog-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        }
        
        .dialog-buttons button {
            padding: 0.6rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(dialog);
    
    dialog.querySelector('#confirmBtn').addEventListener('click', () => {
        if (onConfirm) onConfirm();
        dialog.remove();
    });
    
    dialog.querySelector('#cancelBtn').addEventListener('click', () => {
        if (onCancel) onCancel();
        dialog.remove();
    });
    
    dialog.addEventListener('click', (e) => {
        if (e.target === dialog) {
            if (onCancel) onCancel();
            dialog.remove();
        }
    });
}

/**
 * Load notification styles if not already present
 */
function initializeNotifications() {
    if (!document.getElementById('notification-container')) {
        createNotificationContainer();
    }
}

// Initialize on document ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNotifications);
} else {
    initializeNotifications();
}
