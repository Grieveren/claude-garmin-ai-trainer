/**
 * Main JavaScript for AI-Powered Training Optimization System
 */

// Utility functions
const utils = {
    /**
     * Format duration in seconds to human-readable string
     * @param {number} seconds - Duration in seconds
     * @returns {string} Formatted duration (e.g., "1h 23m 45s")
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        const parts = [];
        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

        return parts.join(' ');
    },

    /**
     * Format distance in meters to kilometers
     * @param {number} meters - Distance in meters
     * @returns {string} Formatted distance (e.g., "5.2 km")
     */
    formatDistance(meters) {
        const km = (meters / 1000).toFixed(2);
        return `${km} km`;
    },

    /**
     * Format pace (min/km)
     * @param {number} seconds - Time in seconds
     * @param {number} meters - Distance in meters
     * @returns {string} Formatted pace (e.g., "5:30 /km")
     */
    formatPace(seconds, meters) {
        const km = meters / 1000;
        const minPerKm = seconds / 60 / km;
        const minutes = Math.floor(minPerKm);
        const secs = Math.floor((minPerKm - minutes) * 60);
        return `${minutes}:${secs.toString().padStart(2, '0')} /km`;
    },

    /**
     * Format date to locale string
     * @param {string} dateString - ISO date string
     * @returns {string} Formatted date
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
};

// API client
const api = {
    baseUrl: '/api',

    /**
     * Make API request
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     * @returns {Promise} Response data
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * Get health status
     * @returns {Promise} Health check data
     */
    async getHealth() {
        return this.request('/health');
    },

    /**
     * Get API info
     * @returns {Promise} API information
     */
    async getInfo() {
        return this.request('/info');
    }
};

// UI interactions
const ui = {
    /**
     * Show loading spinner
     * @param {string} elementId - ID of element to show spinner in
     */
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            // Clear existing content
            element.textContent = '';

            // Create spinner element
            const spinner = document.createElement('div');
            spinner.className = 'spinner mx-auto';
            element.appendChild(spinner);
        }
    },

    /**
     * Create alert element
     * @param {string} message - Alert message
     * @param {string} type - Alert type (error, success, info)
     * @returns {HTMLElement} Alert element
     */
    createAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');

        const colors = {
            error: 'bg-red-100 border-red-400 text-red-700',
            success: 'bg-green-100 border-green-400 text-green-700',
            info: 'bg-blue-100 border-blue-400 text-blue-700',
            warning: 'bg-yellow-100 border-yellow-400 text-yellow-700'
        };

        alertDiv.className = `${colors[type] || colors.info} border px-4 py-3 rounded`;

        const strong = document.createElement('strong');
        strong.textContent = type.charAt(0).toUpperCase() + type.slice(1) + ': ';

        const span = document.createElement('span');
        span.textContent = message;

        alertDiv.appendChild(strong);
        alertDiv.appendChild(span);

        return alertDiv;
    },

    /**
     * Show error message
     * @param {string} message - Error message
     * @param {string} elementId - ID of element to show error in
     */
    showError(message, elementId = null) {
        if (elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = '';
                element.appendChild(this.createAlert(message, 'error'));
            }
        } else {
            console.error(message);
        }
    },

    /**
     * Show success message
     * @param {string} message - Success message
     * @param {string} elementId - ID of element to show message in
     */
    showSuccess(message, elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = '';
            element.appendChild(this.createAlert(message, 'success'));
        }
    },

    /**
     * Show info message
     * @param {string} message - Info message
     * @param {string} elementId - ID of element to show message in
     */
    showInfo(message, elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = '';
            element.appendChild(this.createAlert(message, 'info'));
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('AI-Powered Training Optimization System initialized');

    // Add fade-in animation to main content
    const main = document.querySelector('main');
    if (main) {
        main.classList.add('fade-in');
    }

    // Test API connection
    api.getHealth()
        .then(data => {
            console.log('Health check:', data);
        })
        .catch(error => {
            console.error('Health check failed:', error);
        });
});

// Export for use in other scripts
window.TrainingOptimizer = {
    utils,
    api,
    ui
};
