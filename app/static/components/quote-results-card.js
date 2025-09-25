// Enhanced Quote Results Card Component with V0 Design
class QuoteResultsCard {
    constructor() {
        this.formatter = new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    animateValue(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = this.formatter.format(Math.round(current));
        }, 16);
    }

    getVehicleIcon(configuration) {
        const icons = {
            '2': '🚚',
            '3': '🚛',
            '2S2': '🚚🚛',
            '2S3': '🚚🚛',
            '3S2': '🚛🚛',
            '3S3': '🚛🚛🚛'
        };
        return icons[configuration] || '🚚';
    }

    createSkeletonCard() {
        return `
            <div class="quote-card skeleton-card">
                <div class="skeleton-pulse skeleton-header"></div>
                <div class="skeleton-pulse skeleton-price"></div>
                <div class="skeleton-pulse skeleton-details"></div>
                <div class="skeleton-pulse skeleton-actions"></div>
            </div>
        `;
    }

    createCard(quote) {
        const {
            origin_city,
            destination_city,
            configuration,
            total_price,
            base_price,
            logistics_cost,
            cargo_type,
            unit_type,
            distance,
            estimated_days
        } = quote;

        const cardId = `quote-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        return `
            <div class="quote-card" id="${cardId}">
                <!-- Route Header -->
                <div class="quote-route">
                    <div class="route-city">
                        <div class="city-icon">📍</div>
                        <div class="city-info">
                            <span class="city-label">Origen</span>
                            <span class="city-name">${origin_city}</span>
                        </div>
                    </div>
                    <div class="route-line">
                        <div class="route-arrow">→</div>
                        <span class="route-distance">${distance || '---'} km</span>
                    </div>
                    <div class="route-city">
                        <div class="city-icon">🎯</div>
                        <div class="city-info">
                            <span class="city-label">Destino</span>
                            <span class="city-name">${destination_city}</span>
                        </div>
                    </div>
                </div>

                <!-- Price Display -->
                <div class="quote-price-section">
                    <div class="price-main">
                        <span class="price-label">Precio Total</span>
                        <div class="price-value" data-value="${total_price}">
                            ${this.formatter.format(0)}
                        </div>
                    </div>
                    <div class="price-badge ${this.getPriceTrend(total_price)}">
                        ${this.getPriceTrendIcon(total_price)}
                        <span>Precio competitivo</span>
                    </div>
                </div>

                <!-- Configuration & Details -->
                <div class="quote-details">
                    <div class="detail-item">
                        <span class="detail-icon">${this.getVehicleIcon(configuration)}</span>
                        <div class="detail-info">
                            <span class="detail-label">Configuración</span>
                            <span class="detail-value">${configuration}</span>
                        </div>
                    </div>
                    ${cargo_type ? `
                    <div class="detail-item">
                        <span class="detail-icon">📦</span>
                        <div class="detail-info">
                            <span class="detail-label">Tipo de Carga</span>
                            <span class="detail-value">${cargo_type}</span>
                        </div>
                    </div>` : ''}
                    ${unit_type ? `
                    <div class="detail-item">
                        <span class="detail-icon">🚛</span>
                        <div class="detail-info">
                            <span class="detail-label">Unidad</span>
                            <span class="detail-value">${unit_type}</span>
                        </div>
                    </div>` : ''}
                    ${estimated_days ? `
                    <div class="detail-item">
                        <span class="detail-icon">⏱️</span>
                        <div class="detail-info">
                            <span class="detail-label">Tiempo Estimado</span>
                            <span class="detail-value">${estimated_days} días</span>
                        </div>
                    </div>` : ''}
                </div>

                <!-- Price Breakdown -->
                <div class="price-breakdown">
                    <div class="breakdown-header">
                        <span>Desglose de Precio</span>
                        <button class="breakdown-toggle" onclick="quoteCard.toggleBreakdown('${cardId}')">
                            <svg class="breakdown-icon" width="16" height="16" viewBox="0 0 16 16">
                                <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" fill="none"/>
                            </svg>
                        </button>
                    </div>
                    <div class="breakdown-content">
                        <div class="breakdown-item">
                            <span>Tarifa Base</span>
                            <span>${this.formatter.format(base_price || 0)}</span>
                        </div>
                        ${logistics_cost ? `
                        <div class="breakdown-item">
                            <span>Horas Logísticas</span>
                            <span>${this.formatter.format(logistics_cost)}</span>
                        </div>` : ''}
                        <div class="breakdown-divider"></div>
                        <div class="breakdown-item breakdown-total">
                            <span>Total</span>
                            <span>${this.formatter.format(total_price)}</span>
                        </div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="quote-actions">
                    <button class="btn-save" onclick="quoteCard.saveQuote('${cardId}', ${JSON.stringify(quote).replace(/"/g, '&quot;')})">
                        <svg width="16" height="16" viewBox="0 0 16 16" class="action-icon">
                            <path d="M3 2h10v12L8 11L3 14V2z" fill="none" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        Guardar
                    </button>
                    <button class="btn-request" onclick="quoteCard.requestService('${cardId}', ${JSON.stringify(quote).replace(/"/g, '&quot;')})">
                        Solicitar Servicio
                        <svg width="16" height="16" viewBox="0 0 16 16" class="action-icon">
                            <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="1.5" fill="none"/>
                        </svg>
                    </button>
                </div>

                <!-- Real-time Update Indicator -->
                <div class="update-indicator" style="display: none;">
                    <span class="update-pulse"></span>
                    <span class="update-text">Actualización en tiempo real</span>
                </div>
            </div>
        `;
    }

    getPriceTrend(price) {
        // Logic to determine if price is good, average, or high
        return 'good'; // Simplified for demo
    }

    getPriceTrendIcon(price) {
        const trend = this.getPriceTrend(price);
        if (trend === 'good') return '✓';
        if (trend === 'average') return '~';
        return '!';
    }

    toggleBreakdown(cardId) {
        const card = document.getElementById(cardId);
        const content = card.querySelector('.breakdown-content');
        const icon = card.querySelector('.breakdown-icon');

        content.classList.toggle('expanded');
        icon.classList.toggle('rotated');
    }

    saveQuote(cardId, quote) {
        const card = document.getElementById(cardId);
        const saveBtn = card.querySelector('.btn-save');

        // Add saving animation
        saveBtn.classList.add('saving');

        // Save to localStorage
        const savedQuotes = JSON.parse(localStorage.getItem('savedQuotes') || '[]');
        savedQuotes.push({
            ...quote,
            savedAt: new Date().toISOString()
        });
        localStorage.setItem('savedQuotes', JSON.stringify(savedQuotes));

        setTimeout(() => {
            saveBtn.classList.remove('saving');
            saveBtn.classList.add('saved');
            saveBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" class="action-icon">
                    <path d="M3 8L6 11L13 4" stroke="currentColor" stroke-width="2" fill="none"/>
                </svg>
                Guardado
            `;
        }, 500);
    }

    requestService(cardId, quote) {
        const card = document.getElementById(cardId);
        const requestBtn = card.querySelector('.btn-request');

        requestBtn.classList.add('requesting');

        // Simulate service request
        setTimeout(() => {
            requestBtn.classList.remove('requesting');
            this.showNotification('Solicitud enviada correctamente');
        }, 1000);
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'quote-notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    updatePrice(cardId, newPrice) {
        const card = document.getElementById(cardId);
        if (!card) return;

        const priceElement = card.querySelector('.price-value');
        const currentPrice = parseFloat(priceElement.dataset.value);
        const indicator = card.querySelector('.update-indicator');

        // Show update indicator
        indicator.style.display = 'flex';

        // Animate price change
        this.animateValue(priceElement, currentPrice, newPrice, 500);
        priceElement.dataset.value = newPrice;

        // Add pulse effect
        card.classList.add('price-updating');

        setTimeout(() => {
            card.classList.remove('price-updating');
            indicator.style.display = 'none';
        }, 2000);
    }

    init() {
        // Initialize animations when cards are rendered
        document.querySelectorAll('.quote-card:not(.initialized)').forEach(card => {
            card.classList.add('initialized');

            const priceElement = card.querySelector('.price-value');
            if (priceElement) {
                const targetValue = parseFloat(priceElement.dataset.value);
                this.animateValue(priceElement, 0, targetValue, 1000);
            }

            // Add entrance animation
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(() => {
                card.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        });
    }
}

// Initialize the quote card component
const quoteCard = new QuoteResultsCard();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuoteResultsCard;
}