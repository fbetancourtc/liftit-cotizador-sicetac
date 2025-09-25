// API Configuration
// Use configuration from config.js if available
const API_BASE_URL = window.APP_CONFIG ? window.APP_CONFIG.API_BASE : '/sicetac/api';

// Debug logging function
function debugLog(message, data = null) {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${message}`);
    if (data) {
        console.log('  Data:', data);
    }
}

debugLog('='.repeat(80));
debugLog('SICETAC Application Starting');
debugLog(`API Base URL: ${API_BASE_URL}`);
debugLog('Window location:', {
    href: window.location.href,
    pathname: window.location.pathname,
    hash: window.location.hash
});
debugLog('='.repeat(80));

let cachedConfig = null;

async function fetchSupabaseConfig() {
    if (cachedConfig) {
        debugLog('Returning cached Supabase config');
        return cachedConfig;
    }

    debugLog('Fetching Supabase config from API...');
    try {
        const configUrl = `${API_BASE_URL}/config`;
        debugLog(`Config URL: ${configUrl}`);

        const response = await fetch(configUrl);
        debugLog(`Config response status: ${response.status}`);

        if (!response.ok) {
            throw new Error(`Config request failed with status ${response.status}`);
        }
        cachedConfig = await response.json();
        debugLog('Supabase config received:', {
            has_url: !!cachedConfig.supabase_url,
            has_key: !!cachedConfig.supabase_anon_key
        });
    } catch (error) {
        console.error('Failed to load Supabase configuration:', error);
        debugLog('Config fetch failed:', error.message);
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
    debugLog('Checking authentication...');
    let token = localStorage.getItem('access_token');

    if (!token) {
        // Automatically set development token if none exists
        debugLog('No auth token found, setting development token...');
        token = 'development-token';
        localStorage.setItem('access_token', token);
        localStorage.setItem('authToken', token);
        debugLog('Development token set');
        // Don't redirect, just continue with development token
    } else {
        debugLog(`Auth token found: ${token.substring(0, 20)}...`);
    }
    return true;
}

// Get current auth token
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
    debugLog('Auth headers prepared', {
        has_token: !!token,
        auth_header: headers.Authorization ? 'Bearer ...' : 'none'
    });
    return headers;
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

// Period selector functionality
function initializePeriodSelector() {
    const monthSelect = document.getElementById('periodMonth');
    const yearSelect = document.getElementById('periodYear');
    const periodInput = document.getElementById('period');

    if (!monthSelect || !yearSelect || !periodInput) {
        return;
    }

    // Get current date
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1; // JavaScript months are 0-indexed

    // Populate year dropdown (from 2020 to next year)
    for (let year = 2020; year <= currentYear + 1; year++) {
        const option = document.createElement('option');
        option.value = year.toString();
        option.textContent = year;
        yearSelect.appendChild(option);
    }

    // Set current month and year as default
    const currentMonthString = currentMonth.toString().padStart(2, '0');
    monthSelect.value = currentMonthString;
    yearSelect.value = currentYear.toString();

    // Update the hidden period input
    function updatePeriod() {
        const month = monthSelect.value;
        const year = yearSelect.value;

        if (month && year) {
            const periodValue = `${year}${month}`;
            periodInput.value = periodValue;

            // Log for debugging
            const monthName = monthSelect.options[monthSelect.selectedIndex].text;
            debugLog(`Period set to: ${periodValue} (${monthName} ${year})`);
        } else {
            periodInput.value = '';
        }
    }

    // Function to reset to current period
    function setToCurrentPeriod() {
        monthSelect.value = currentMonthString;
        yearSelect.value = currentYear.toString();
        updatePeriod();
    }

    // Add Today button functionality and update its text
    const todayBtn = document.getElementById('todayBtn');
    if (todayBtn) {
        // Get month names in Spanish
        const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                          'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

        // Update button text to show current month/year
        const currentMonthName = monthNames[currentMonth - 1];
        todayBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
                <circle cx="12" cy="16" r="1" fill="currentColor"></circle>
            </svg>
            ${currentMonthName} ${currentYear}
        `;

        todayBtn.addEventListener('click', (e) => {
            e.preventDefault();
            setToCurrentPeriod();
        });
    }

    // Add event listeners
    monthSelect.addEventListener('change', updatePeriod);
    yearSelect.addEventListener('change', updatePeriod);

    // Initialize with current values and ensure visual update
    updatePeriod();

    // Log initialization
    debugLog('Period selector initialized with current date:', {
        month: currentMonthString,
        year: currentYear,
        periodValue: `${currentYear}${currentMonthString}`
    });
}

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    await handleOAuthRedirect();

    // Initialize period selector
    initializePeriodSelector();

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
    debugLog('=' * 60);
    debugLog('QUOTE SUBMISSION STARTED');

    // Validate city selections
    const originCode = document.getElementById('origin').value;
    const destinationCode = document.getElementById('destination').value;
    const originCity = document.getElementById('originCity').value;
    const destinationCity = document.getElementById('destinationCity').value;

    debugLog('City selections:', {
        originCode,
        originCity,
        destinationCode,
        destinationCity
    });

    if (!originCode || !destinationCode) {
        debugLog('ERROR: Missing city codes');
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

    debugLog('Quote request data:', quoteRequest);

    // Company name for saving
    const companyName = formData.get('company_name');
    debugLog(`Company name: ${companyName || 'not provided'}`);

    try {
        showLoading(resultsContainer);
        resultsSection.style.display = 'block';

        // Try to get quote with persistence
        const quotesUrl = `${API_BASE_URL}/quotes/`;
        debugLog(`Attempting to save quote at: ${quotesUrl}`);

        const response = await fetch(quotesUrl, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                request: quoteRequest,
                company_name: companyName
            })
        });

        debugLog(`Quotes API response status: ${response.status}`);
        debugLog(`Response headers:`, {
            contentType: response.headers.get('content-type'),
            contentLength: response.headers.get('content-length')
        });

        if (!response.ok) {
            debugLog('Quote persistence failed, trying direct API...');

            // If persistence fails, try direct quote
            const directUrl = `${API_BASE_URL}/quote`;
            debugLog(`Direct quote URL: ${directUrl}`);

            const directResponse = await fetch(directUrl, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(quoteRequest)
            });

            debugLog(`Direct API response status: ${directResponse.status}`);

            if (!directResponse.ok) {
                const errorText = await directResponse.text();
                debugLog('ERROR: Direct API failed', {
                    status: directResponse.status,
                    statusText: directResponse.statusText,
                    response: errorText
                });
                throw new Error(`Error al obtener cotización: ${directResponse.status}`);
            }

            const data = await directResponse.json();
            debugLog('Direct quote response received:', {
                quotes_count: data.quotes ? data.quotes.length : 0
            });

            displayResults(data);
            showMessage('Cotización obtenida (sin persistencia)', 'success');
        } else {
            const data = await response.json();
            debugLog('Quote saved successfully:', {
                id: data.id,
                quotes_count: data.quotes ? data.quotes.length : 0
            });

            displayQuotationResults(data);
            loadHistory(); // Refresh history
            showMessage('Cotización guardada exitosamente', 'success');
        }
    } catch (error) {
        console.error('Error:', error);
        debugLog('ERROR in quote submission:', {
            message: error.message,
            stack: error.stack
        });
        resultsContainer.innerHTML = `<div class="error">Error al obtener cotización: ${error.message}</div>`;
    }
    debugLog('=' * 60);
}

// Display results from direct quote
function displayResults(data) {
    if (!data.quotes || data.quotes.length === 0) {
        resultsContainer.innerHTML = '<div class="error">No se encontraron cotizaciones para los parámetros especificados</div>';
        return;
    }

    // Show loading skeletons first for smooth transition
    let html = '<div class="quotes-grid">';
    for (let i = 0; i < data.quotes.length && i < 3; i++) {
        html += quoteCard.createSkeletonCard();
    }
    html += '</div>';
    resultsContainer.innerHTML = html;
    resultsSection.style.display = 'block';

    // Process and display actual results after brief delay
    setTimeout(() => {
        let resultsHtml = '<div class="quotes-grid">';

        data.quotes.forEach((quote, index) => {
            // Transform the quote data to match V0 component format
            const enhancedQuote = {
                origin_city: data.origin_city || quote.origin_city || 'Origen',
                destination_city: data.destination_city || quote.destination_city || 'Destino',
                configuration: data.configuration || quote.configuration || 'N/A',
                total_price: quote.mobilization_value || quote.minimum_payable || 0,
                base_price: quote.ton_value || (quote.mobilization_value - (quote.hour_value || 0)),
                logistics_cost: quote.hour_value || 0,
                cargo_type: quote.cargo_type || data.cargo_type,
                unit_type: quote.unit_type || data.unit_type,
                distance: quote.distance_km,
                estimated_days: quote.estimated_days || Math.ceil((quote.distance_km || 500) / 400),
                route_name: quote.route_name
            };

            // Use V0 component if available
            if (typeof quoteCard !== 'undefined') {
                resultsHtml += quoteCard.createCard(enhancedQuote);
            } else {
                // Fallback to original display
                resultsHtml += `
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
            }
        });

        resultsHtml += '</div>';
        resultsContainer.innerHTML = resultsHtml;

        // Initialize V0 component animations
        if (typeof quoteCard !== 'undefined') {
            quoteCard.init();
        }
    }, 300);
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
        } else if (e.key === 'Enter') {
            e.preventDefault();

            // If user navigated with arrows, select the highlighted option
            if (selectedIndex >= 0 && options[selectedIndex]) {
                selectCity(options[selectedIndex], input, hiddenInput, dropdown);
            }
            // If there's only one option and no selection, auto-select it
            else if (options.length === 1) {
                selectCity(options[0], input, hiddenInput, dropdown);
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
