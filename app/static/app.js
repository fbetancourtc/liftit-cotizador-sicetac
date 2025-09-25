// API Configuration
// Use configuration from config.js if available
const API_BASE_URL = window.APP_CONFIG ? window.APP_CONFIG.API_BASE : '/sicetac/api';

let cachedConfig = null;

async function fetchSupabaseConfig() {
    if (cachedConfig) {
        return cachedConfig;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/config`);
        if (!response.ok) {
            throw new Error(`Config request failed with status ${response.status}`);
        }
        cachedConfig = await response.json();
    } catch (error) {
        console.error('Failed to load Supabase configuration:', error);
        cachedConfig = null;
    }

    return cachedConfig;
}

async function fetchSupabaseUser(accessToken) {
    const config = await fetchSupabaseConfig();
    if (!config || !config.supabase_url || !config.supabase_anon_key) {
        return null;
    }

    try {
        const response = await fetch(`${config.supabase_url}/auth/v1/user`, {
            headers: {
                'apikey': config.supabase_anon_key,
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            console.warn('Supabase user lookup failed:', response.status);
            return null;
        }

        const payload = await response.json();
        return payload?.user ?? payload;
    } catch (error) {
        console.error('Error fetching Supabase user profile:', error);
        return null;
    }
}

async function handleOAuthRedirect() {
    if (!window.location.hash) {
        return;
    }

    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = hashParams.get('access_token');
    if (!accessToken) {
        return;
    }

    const refreshToken = hashParams.get('refresh_token');
    const expiresIn = hashParams.get('expires_in');

    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
    }

    if (expiresIn) {
        const expiresSeconds = parseInt(expiresIn, 10);
        if (!Number.isNaN(expiresSeconds)) {
            const expiresAt = Date.now() + expiresSeconds * 1000;
            localStorage.setItem('token_expires_at', String(expiresAt));
        }
    }

    // Populate user info if we don't have it yet
    if (!localStorage.getItem('user')) {
        const userProfile = await fetchSupabaseUser(accessToken);
        if (userProfile) {
            localStorage.setItem('user', JSON.stringify(userProfile));
        }
    }

    // Remove OAuth fragments from the URL to avoid leaking tokens
    if (history && history.replaceState) {
        history.replaceState(null, '', window.location.pathname + window.location.search);
    } else {
        window.location.hash = '';
    }
}

// Check authentication on page load
function checkAuth() {
    let token = localStorage.getItem('access_token');
    if (!token) {
        // Automatically set development token if none exists
        console.log('No auth token found, setting development token...');
        token = 'development-token';
        localStorage.setItem('access_token', token);
        localStorage.setItem('authToken', token);
        // Don't redirect, just continue with development token
    }
    return true;
}

// Get current auth token
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

// DOM Elements
const quoteForm = document.getElementById('quoteForm');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');
const historyContainer = document.getElementById('historyContainer');
const loginModal = document.getElementById('loginModal');
const authForm = document.getElementById('authForm');
const skipAuth = document.getElementById('skipAuth');
const refreshHistory = document.getElementById('refreshHistory');
const statusFilter = document.getElementById('statusFilter');

// Display user info
function displayUserInfo() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userEmailElement = document.getElementById('userEmail');
    if (userEmailElement && user.email) {
        userEmailElement.textContent = user.email;
    }
}

// Handle logout
async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Clear local storage and redirect
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        localStorage.removeItem('token_expires_at');
        window.location.href = window.APP_CONFIG ? window.APP_CONFIG.ROUTES.LOGIN : '/sicetac';
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    await handleOAuthRedirect();

    // Update footer year automatically
    const yearElement = document.getElementById('currentYear');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    // Check if user is authenticated
    if (!checkAuth()) {
        return;
    }

    // Display user info
    displayUserInfo();

    // Set current period
    const currentDate = new Date();
    const currentPeriod = currentDate.getFullYear().toString() +
                          (currentDate.getMonth() + 1).toString().padStart(2, '0');
    document.getElementById('period').value = currentPeriod;

    // Initialize city selectors
    initializeCitySelector('origin');
    initializeCitySelector('destination');

    // Load history
    loadHistory();

    // Event Listeners
    quoteForm.addEventListener('submit', handleQuoteSubmit);
    if (authForm) authForm.addEventListener('submit', handleAuthSubmit);
    if (skipAuth) skipAuth.addEventListener('click', handleSkipAuth);
    if (refreshHistory) refreshHistory.addEventListener('click', loadHistory);
    if (statusFilter) statusFilter.addEventListener('change', loadHistory);

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
});

// Show authentication modal
function showAuthModal() {
    loginModal.classList.add('active');
}

// Handle authentication form submission
function handleAuthSubmit(e) {
    e.preventDefault();
    authToken = document.getElementById('authToken').value;
    localStorage.setItem('authToken', authToken);
    loginModal.classList.remove('active');
    loadHistory();
}

// Handle skip authentication (for development)
function handleSkipAuth() {
    authToken = 'development-token';
    localStorage.setItem('authToken', authToken);
    loginModal.classList.remove('active');
    showMessage('Modo de desarrollo activado. Algunas funciones pueden estar limitadas.', 'warning');
}

// Handle quote form submission
async function handleQuoteSubmit(e) {
    e.preventDefault();

    // Validate city selections
    const originCode = document.getElementById('origin').value;
    const destinationCode = document.getElementById('destination').value;

    if (!originCode || !destinationCode) {
        showMessage('Por favor seleccione ciudades válidas de origen y destino', 'error');
        return;
    }

    const formData = new FormData(e.target);
    const quoteRequest = {
        period: formData.get('period'),
        configuration: formData.get('configuration'),
        origin: originCode,
        destination: destinationCode,
        cargo_type: formData.get('cargo_type') || null,
        unit_type: formData.get('unit_type') || null,
        logistics_hours: parseFloat(formData.get('logistics_hours')) || 0
    };

    // Company name for saving
    const companyName = formData.get('company_name');

    try {
        showLoading(resultsContainer);
        resultsSection.style.display = 'block';

        // Try to get quote with persistence
        const response = await fetch(`${API_BASE_URL}/quotes/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                request: quoteRequest,
                company_name: companyName
            })
        });

        if (!response.ok) {
            // If persistence fails, try direct quote
            const directResponse = await fetch(`${API_BASE_URL}/quote`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(quoteRequest)
            });

            if (!directResponse.ok) {
                throw new Error('Error al obtener cotización');
            }

            const data = await directResponse.json();
            displayResults(data);
            showMessage('Cotización obtenida (sin persistencia)', 'success');
        } else {
            const data = await response.json();
            displayQuotationResults(data);
            loadHistory(); // Refresh history
            showMessage('Cotización guardada exitosamente', 'success');
        }
    } catch (error) {
        console.error('Error:', error);
        resultsContainer.innerHTML = `<div class="error">Error al obtener cotización: ${error.message}</div>`;
    }
}

// Display results from direct quote
function displayResults(data) {
    if (!data.quotes || data.quotes.length === 0) {
        resultsContainer.innerHTML = '<div class="error">No se encontraron cotizaciones para los parámetros especificados</div>';
        return;
    }

    let html = '<div class="quotes-grid">';

    data.quotes.forEach((quote, index) => {
        html += `
            <div class="quote-result">
                <h3>${quote.unit_type || 'N/A'} - ${quote.cargo_type || 'N/A'}</h3>
                <div class="quote-details">
                    <div class="detail-item">
                        <div class="detail-label">Ruta</div>
                        <div class="detail-value">${quote.route_name || 'N/A'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Valor Movilización</div>
                        <div class="detail-value price">$${formatNumber(quote.mobilization_value)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Valor por Tonelada</div>
                        <div class="detail-value">$${formatNumber(quote.ton_value)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Valor por Hora</div>
                        <div class="detail-value">$${formatNumber(quote.hour_value)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Distancia</div>
                        <div class="detail-value">${quote.distance_km} km</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Valor Mínimo a Pagar</div>
                        <div class="detail-value price">$${formatNumber(quote.minimum_payable)}</div>
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    resultsContainer.innerHTML = html;
}

// Display results from saved quotation
function displayQuotationResults(quotation) {
    const data = quotation.quotes_data;
    displayResults(data);
}

// Load history of quotations
async function loadHistory() {
    try {
        showLoading(historyContainer);

        const status = statusFilter.value;
        let url = `${API_BASE_URL}/quotes/`;
        if (status) {
            url += `?status=${status}`;
        }

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Error al cargar historial');
        }

        const quotations = await response.json();
        displayHistory(quotations);
    } catch (error) {
        console.error('Error:', error);
        historyContainer.innerHTML = '<div class="error">Error al cargar historial. Verifica tu autenticación.</div>';
    }
}

// Display history of quotations
function displayHistory(quotations) {
    if (!quotations || quotations.length === 0) {
        historyContainer.innerHTML = '<p>No hay cotizaciones en el historial</p>';
        return;
    }

    let html = '';
    quotations.forEach(quotation => {
        const date = new Date(quotation.created_at).toLocaleString('es-CO');
        const statusClass = `status-${quotation.status}`;

        // Get city names from codes
        const originCity = getCityByCode(quotation.origin_code);
        const destinationCity = getCityByCode(quotation.destination_code);
        const originName = originCity ? originCity.name : quotation.origin_code;
        const destinationName = destinationCity ? destinationCity.name : quotation.destination_code;

        html += `
            <div class="history-item" onclick="viewQuotation(${quotation.id})">
                <div class="history-header">
                    <div>
                        <strong>${originName} → ${destinationName}</strong>
                        <div class="history-date">${date}</div>
                    </div>
                    <span class="history-status ${statusClass}">${quotation.status}</span>
                </div>
                <div>
                    Configuración: ${quotation.configuration} |
                    Período: ${quotation.period}
                    ${quotation.company_name ? ` | Empresa: ${quotation.company_name}` : ''}
                </div>
            </div>
        `;
    });

    historyContainer.innerHTML = html;
}

// View a specific quotation
async function viewQuotation(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/quotes/${id}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Error al cargar cotización');
        }

        const quotation = await response.json();
        displayQuotationResults(quotation);
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al cargar cotización', 'error');
    }
}

// City Selector Functions
function initializeCitySelector(type) {
    const input = document.getElementById(type + 'City');
    const hiddenInput = document.getElementById(type);
    const dropdown = document.getElementById(type + 'CityList');
    let selectedIndex = -1;

    // Handle input typing
    input.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        if (query.length < 2) {
            dropdown.classList.remove('active');
            dropdown.innerHTML = '';
            hiddenInput.value = '';
            return;
        }

        const results = searchCities(query);
        displayCityDropdown(results, dropdown, input, hiddenInput);
    });

    // Handle keyboard navigation
    input.addEventListener('keydown', (e) => {
        const options = dropdown.querySelectorAll('.city-option');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, options.length - 1);
            highlightOption(options, selectedIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
            highlightOption(options, selectedIndex);
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            if (options[selectedIndex]) {
                selectCity(options[selectedIndex], input, hiddenInput, dropdown);
            }
        } else if (e.key === 'Escape') {
            dropdown.classList.remove('active');
            selectedIndex = -1;
        }
    });

    // Handle focus/blur
    input.addEventListener('focus', () => {
        if (input.value.trim().length >= 2) {
            const results = searchCities(input.value.trim());
            displayCityDropdown(results, dropdown, input, hiddenInput);
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
}

function displayCityDropdown(cities, dropdown, input, hiddenInput) {
    dropdown.innerHTML = '';

    if (cities.length === 0) {
        dropdown.innerHTML = '<div class="city-no-results">No se encontraron ciudades</div>';
        dropdown.classList.add('active');
        return;
    }

    cities.slice(0, 10).forEach(city => {
        const option = document.createElement('div');
        option.className = 'city-option';
        option.dataset.code = city.code;
        option.dataset.name = city.name;
        option.innerHTML = `
            <span class="city-name">${city.name}</span>
            <span class="city-department">${city.department}</span>
        `;

        option.addEventListener('click', () => {
            selectCity(option, input, hiddenInput, dropdown);
        });

        dropdown.appendChild(option);
    });

    dropdown.classList.add('active');
}

function selectCity(option, input, hiddenInput, dropdown) {
    const cityName = option.dataset.name;
    const cityCode = option.dataset.code;

    input.value = cityName;
    hiddenInput.value = cityCode;

    dropdown.classList.remove('active');

    // Mark as valid
    input.classList.remove('error');
    hiddenInput.setCustomValidity('');
}

function highlightOption(options, index) {
    options.forEach((opt, i) => {
        if (i === index) {
            opt.classList.add('selected');
            opt.scrollIntoView({ block: 'nearest' });
        } else {
            opt.classList.remove('selected');
        }
    });
}

// Utility Functions
function formatNumber(number) {
    if (number == null) return 'N/A';
    return new Intl.NumberFormat('es-CO').format(number);
}

function showLoading(container) {
    container.innerHTML = '<div class="loading"><div class="spinner"></div>Cargando...</div>';
}

function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'error' ? 'error' : 'success';
    messageDiv.textContent = message;

    resultsContainer.innerHTML = '';
    resultsContainer.appendChild(messageDiv);

    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}
