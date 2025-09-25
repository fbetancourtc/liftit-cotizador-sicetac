// Authentication handling
// Use configuration from config.js if available
const API_BASE = window.APP_CONFIG ? window.APP_CONFIG.API_BASE : '/sicetac/api';

// Tab switching
function switchTab(tab) {
    const tabs = document.querySelectorAll('.auth-tab');
    const forms = document.querySelectorAll('.auth-form');

    tabs.forEach(t => t.classList.remove('active'));
    forms.forEach(f => f.style.display = 'none');

    if (tab === 'login') {
        tabs[0].classList.add('active');
        document.getElementById('loginForm').style.display = 'block';
    } else {
        tabs[1].classList.add('active');
        document.getElementById('signupForm').style.display = 'block';
    }

    clearAlerts();
}

// Show alert message
function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = `
        <div class="alert alert-${type}">
            ${message}
        </div>
    `;
}

// Clear alerts
function clearAlerts() {
    document.getElementById('alertContainer').innerHTML = '';
}

// Show/hide loading
function setLoading(show) {
    const loading = document.querySelector('.loading');
    const buttons = document.querySelectorAll('.btn-submit');

    if (show) {
        loading.classList.add('active');
        buttons.forEach(btn => btn.disabled = true);
    } else {
        loading.classList.remove('active');
        buttons.forEach(btn => btn.disabled = false);
    }
}

// Store authentication tokens
function storeAuth(data) {
    if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
    }
    if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
    }
    if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
    }
}

// Clear authentication tokens
function clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
}

// Check if user is authenticated
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

// Get stored auth token
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Redirect to dashboard if already authenticated
if (isAuthenticated()) {
    window.location.href = window.APP_CONFIG ? window.APP_CONFIG.ROUTES.LOGIN : '/sicetac';
}

// Handle login form submission
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlerts();
    setLoading(true);

    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        storeAuth(data);
        showAlert('¡Inicio de sesión exitoso! Redirigiendo...', 'success');

        setTimeout(() => {
            window.location.href = window.APP_CONFIG ? window.APP_CONFIG.ROUTES.LOGIN : '/sicetac';
        }, 1500);

    } catch (error) {
        showAlert(error.message || 'Error al iniciar sesión', 'error');
    } finally {
        setLoading(false);
    }
});

// Handle signup form submission
document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlerts();

    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');

    // Validate passwords match
    if (password !== confirmPassword) {
        showAlert('Las contraseñas no coinciden', 'error');
        return;
    }

    // Validate password length
    if (password.length < 6) {
        showAlert('La contraseña debe tener al menos 6 caracteres', 'error');
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }

        if (data.message && data.message.includes('email')) {
            showAlert(data.message, 'info');
            // Clear form
            e.target.reset();
        } else {
            storeAuth(data);
            showAlert('¡Registro exitoso! Redirigiendo...', 'success');
            setTimeout(() => {
                window.location.href = window.APP_CONFIG ? window.APP_CONFIG.ROUTES.LOGIN : '/sicetac';
            }, 1500);
        }

    } catch (error) {
        showAlert(error.message || 'Error al registrarse', 'error');
    } finally {
        setLoading(false);
    }
});

// Refresh token when it expires
async function refreshAuthToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        clearAuth();
        window.location.href = window.APP_CONFIG ? window.APP_CONFIG.ROUTES.LOGIN : '/sicetac';
        return null;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            throw new Error('Token refresh failed');
        }

        const data = await response.json();
        storeAuth(data);
        return data.access_token;

    } catch (error) {
        clearAuth();
        window.location.href = window.APP_CONFIG ? window.APP_CONFIG.ROUTES.LOGIN : '/sicetac';
        return null;
    }
}

// Export functions for use in other scripts
window.authUtils = {
    isAuthenticated,
    getAuthToken,
    refreshAuthToken,
    clearAuth
};