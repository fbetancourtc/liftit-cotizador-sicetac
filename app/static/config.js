// Configuration for multi-tenant deployment
// This file centralizes all path configurations for the SICETAC application

window.APP_CONFIG = {
    // Base path for the application (must match Vercel routing configuration)
    BASE_PATH: '/sicetac',

    // API endpoints
    API_BASE: '/sicetac/api',

    // Public URL for OAuth callbacks and external references
    PUBLIC_URL: 'https://micarga.flexos.ai/sicetac',

    // Application routes
    ROUTES: {
        LOGIN: '/sicetac',
        APP: '/sicetac/app',
        DASHBOARD: '/sicetac/dashboard',
        STATIC: '/sicetac/static'
    },

    // Helper function to construct full API URLs
    getApiUrl: function(endpoint) {
        return this.API_BASE + endpoint;
    },

    // Helper function to construct full app URLs
    getAppUrl: function(path) {
        return this.BASE_PATH + (path.startsWith('/') ? path : '/' + path);
    }
};

// Export for module systems if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.APP_CONFIG;
}