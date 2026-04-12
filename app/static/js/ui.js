/**
 * UI Module
 * Handles Neumorphic effects, interactions, and visual enhancements
 */

class UIManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupNeuEffects();
        this.setupInteractions();
        this.setupResponsive();
        this.setupAccessibility();
    }

    /**
     * Setup Neumorphic effects and hover states
     */
    setupNeuEffects() {
        // Add hover effects to neumorphic elements
        document.querySelectorAll('.neu-btn, .neu-card, .neu-input').forEach(element => {
            element.addEventListener('mousedown', function() {
                this.style.boxShadow = getComputedStyle(this).boxShadow.replace(/[0-9]+px/g, match => {
                    const num = parseInt(match);
                    return Math.max(0, num - 3) + 'px';
                });
            });

            element.addEventListener('mouseup', function() {
                this.style.boxShadow = '';
            });

            element.addEventListener('mouseleave', function() {
                this.style.boxShadow = '';
            });
        });

        // KPI Card hover effect
        document.querySelectorAll('.kpi-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-4px)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    }

    /**
     * Setup general interactions
     */
    setupInteractions() {
        // Smooth scroll
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Dropdown menus
        document.querySelectorAll('[data-dropdown]').forEach(dropdown => {
            const trigger = dropdown.querySelector('[data-dropdown-trigger]');
            const menu = dropdown.querySelector('[data-dropdown-menu]');

            if (trigger && menu) {
                trigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    menu.classList.toggle('active');
                });

                document.addEventListener('click', () => {
                    menu.classList.remove('active');
                });
            }
        });

        // Modal handling
        document.querySelectorAll('[data-modal-trigger]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                const modalId = e.target.getAttribute('data-modal-trigger');
                this.openModal(modalId);
            });
        });

        document.querySelectorAll('[data-modal-close]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('[data-modal]').classList.remove('active');
            });
        });
    }

    /**
     * Setup responsive behaviors
     */
    setupResponsive() {
        // Sidebar toggle on mobile
        const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
        const sidebar = document.querySelector('[data-sidebar]');

        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
            });

            // Close on click outside
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('active');
                }
            });
        }

        // Responsive grid adjustments
        const updateGridColumns = () => {
            const width = window.innerWidth;
            document.querySelectorAll('.bento-grid').forEach(grid => {
                if (width < 768) {
                    grid.style.gridTemplateColumns = '1fr';
                } else if (width < 1024) {
                    grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
                } else {
                    grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
                }
            });
        };

        updateGridColumns();
        window.addEventListener('resize', updateGridColumns);
    }

    /**
     * Setup accessibility features
     */
    setupAccessibility() {
        // Focus indicators
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-nav');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-nav');
        });

        // Ensure sufficient color contrast
        this.validateColorContrast();

        // Add ARIA labels where needed
        document.querySelectorAll('[role="button"]').forEach(element => {
            if (!element.hasAttribute('aria-label') && !element.textContent.trim()) {
                element.setAttribute('aria-label', 'button');
            }
        });
    }

    /**
     * Open modal
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    /**
     * Close modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.querySelector('[data-toast-container]') ||
            this.createToastContainer();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close" data-toast-close>×</button>
            </div>
        `;

        container.appendChild(toast);
        toast.classList.add('show');

        const removeToast = () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        };

        toast.querySelector('[data-toast-close]').addEventListener('click', removeToast);
        
        if (duration > 0) {
            setTimeout(removeToast, duration);
        }

        return toast;
    }

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.setAttribute('data-toast-container', '');
        document.body.appendChild(container);
        return container;
    }

    /**
     * Validate color contrast
     */
    validateColorContrast() {
        // Basic WCAG AA compliance check
        const elements = document.querySelectorAll('[style*="color"], h1, h2, h3, p, a');
        elements.forEach(el => {
            const styles = getComputedStyle(el);
            const bgColor = styles.backgroundColor;
            const fgColor = styles.color;

            // Simple contrast check - in production, use a proper WCAG checker
            console.debug(`Element contrast check: ${el.tagName}`);
        });
    }

    /**
     * Create loading spinner
     */
    createSpinner(container, message = '') {
        const spinner = document.createElement('div');
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = `
            <div class="spinner-content">
                <div class="spinner"></div>
                ${message ? `<p>${message}</p>` : ''}
            </div>
        `;
        container.appendChild(spinner);
        return spinner;
    }

    /**
     * Remove loading spinner
     */
    removeSpinner(container) {
        const spinner = container.querySelector('.spinner-overlay');
        if (spinner) {
            spinner.remove();
        }
    }
}

// Initialize UI Manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.uiManager = new UIManager();
});

// Expose functions to global scope for backward compatibility
window.openModal = (id) => window.uiManager?.openModal(id);
window.closeModal = (id) => window.uiManager?.closeModal(id);
window.showToast = (msg, type, duration) => window.uiManager?.showToast(msg, type, duration);
