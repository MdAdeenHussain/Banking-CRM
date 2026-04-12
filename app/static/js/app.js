/**
 * LoanAxis CRM — Global JavaScript
 * Dark mode toggle, toast auto-dismiss, CSRF setup, icon init.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── Dark Mode Toggle ─────────────────────────────
    const toggle = document.getElementById('dark-mode-toggle');
    const html = document.documentElement;

    // Load saved preference
    const savedTheme = localStorage.getItem('loanaxis-theme') || 'light';
    html.setAttribute('data-theme', savedTheme);

    if (toggle) {
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('loanaxis-theme', next);
            lucide.createIcons();
        });
    }

    // ── Toast Auto-Dismiss ───────────────────────────
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.classList.add('animate__fadeOutRight');
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    });

    // ── CSRF Header for AJAX ─────────────────────────
    const csrfToken = window.CSRF_TOKEN;
    if (csrfToken) {
        // Patch fetch
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (options.method && options.method !== 'GET') {
                options.headers = options.headers || {};
                if (typeof options.headers === 'object' && !(options.headers instanceof Headers)) {
                    options.headers['X-CSRFToken'] = csrfToken;
                }
            }
            return originalFetch(url, options);
        };
    }

    // ── Flatpickr Init ───────────────────────────────
    if (typeof flatpickr !== 'undefined') {
        flatpickr('input[type="date"]', { dateFormat: 'Y-m-d', allowInput: true });
    }

    // ── Notification Polling ─────────────────────────
    function pollNotifications() {
        fetch('/notifications/api/unread-count')
            .then(r => r.json())
            .then(data => {
                const badge = document.querySelector('.notif-badge');
                if (data.count > 0) {
                    if (badge) {
                        badge.textContent = data.count;
                        badge.style.display = 'flex';
                    }
                } else if (badge) {
                    badge.style.display = 'none';
                }
            })
            .catch(() => {});
    }

    // Poll every 60 seconds
    setInterval(pollNotifications, 60000);

    // ── Mark All Read Button ─────────────────────────
    const markAllBtn = document.getElementById('mark-all-read-btn');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', () => {
            fetch('/notifications/mark-all-read', { method: 'POST' })
                .then(r => r.json())
                .then(() => {
                    const badge = document.querySelector('.notif-badge');
                    if (badge) badge.style.display = 'none';
                    const list = document.getElementById('notif-list');
                    if (list) list.innerHTML = '<div class="notif-empty">No unread notifications</div>';
                });
        });
    }

    // ── Re-initialize Lucide icons ───────────────────
    lucide.createIcons();
});
