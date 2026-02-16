// MedSync AI – Frontend API Integration Layer
// Shared utilities used by all pages

const API = {
    baseUrl: '',

    async get(url) {
        const res = await fetch(this.baseUrl + url, {
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        return res.json();
    },

    async post(url, data = {}) {
        const res = await fetch(this.baseUrl + url, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async put(url, data = {}) {
        const res = await fetch(this.baseUrl + url, {
            method: 'PUT',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async delete(url) {
        const res = await fetch(this.baseUrl + url, {
            method: 'DELETE',
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        });
        return res.json();
    },

    async checkSession() {
        try {
            const result = await this.get('/api/auth/session');
            if (result.success && result.data.authenticated) {
                return result.data;
            }
            return null;
        } catch (e) {
            return null;
        }
    },

    async logout() {
        try {
            await this.post('/api/auth/logout');
        } catch (e) {}
        window.location.href = '/';
    }
};

/**
 * Require authentication. Redirects to login if not authenticated.
 * @param {string} role - 'patient' or 'doctor'
 * @returns {object|null} user data
 */
async function requireAuth(role = null) {
    const session = await API.checkSession();
    if (!session) {
        const loginPage = role === 'doctor' ? '/doctor/login' : '/login';
        window.location.href = loginPage;
        return null;
    }
    if (role && session.role !== role) {
        const redirect = session.role === 'doctor' ? '/doctor/dashboard' : '/patient/dashboard';
        window.location.href = redirect;
        return null;
    }
    return session;
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'info', duration = 4000) {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    // Style the toast
    Object.assign(toast.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: '10000',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '14px 20px',
        borderRadius: '10px',
        background: type === 'success' ? '#059669' :
                    type === 'error'   ? '#dc2626' :
                    type === 'warning' ? '#d97706' : '#2563eb',
        color: '#fff',
        fontSize: '0.9rem',
        fontFamily: "'Poppins', sans-serif",
        boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
        animation: 'slideIn 0.3s ease',
        maxWidth: '400px'
    });

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Format a date string for display
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format a datetime for display
 */
function formatDateTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Get relative time string (e.g., "2 hours ago")
 */
function timeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return formatDate(dateStr);
}

// Add animation keyframes dynamically
(function() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; transform: translateY(-10px); }
        }
        .toast-close {
            background: none;
            border: none;
            color: rgba(255,255,255,0.7);
            font-size: 18px;
            cursor: pointer;
            padding: 0 0 0 8px;
            line-height: 1;
        }
        .toast-close:hover { color: #fff; }
    `;
    document.head.appendChild(style);
})();

// --- Landing page session-aware navbar ---
(function() {
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        API.checkSession().then(session => {
            const authLinks = document.getElementById('authLinks');
            if (!authLinks) return;

            if (session) {
                const dashUrl = session.role === 'doctor' ? '/doctor/dashboard' : '/patient/dashboard';
                authLinks.innerHTML = `
                    <a href="${dashUrl}" class="btn btn-primary btn-sm">Dashboard</a>
                    <button class="btn btn-sm btn-secondary" onclick="API.logout()">Logout</button>
                `;
            }
        });
    }
})();
