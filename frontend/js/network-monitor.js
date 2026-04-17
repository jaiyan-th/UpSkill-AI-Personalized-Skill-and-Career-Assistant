/**
 * Network Monitor
 * Handles online/offline state and connection quality
 */

class NetworkMonitor {
    constructor() {
        this.isOnline = navigator.onLine;
        this.listeners = [];
        this.init();
    }

    init() {
        // Listen for online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Check connection on page load
        if (!this.isOnline) {
            this.handleOffline();
        }
    }

    handleOnline() {
        this.isOnline = true;
        console.log('✅ Network connection restored');
        
        // Show notification
        if (typeof API !== 'undefined') {
            API.showToast('Connection restored', 'success');
        }

        // Notify listeners
        this.notifyListeners('online');

        // Remove offline indicator
        this.removeOfflineIndicator();
    }

    handleOffline() {
        this.isOnline = false;
        console.warn('⚠️ Network connection lost');
        
        // Show notification
        if (typeof API !== 'undefined') {
            API.showToast('You are offline. Some features may not work.', 'warning');
        }

        // Notify listeners
        this.notifyListeners('offline');

        // Show offline indicator
        this.showOfflineIndicator();
    }

    showOfflineIndicator() {
        // Remove existing indicator
        this.removeOfflineIndicator();

        // Create offline banner
        const banner = document.createElement('div');
        banner.id = 'offline-indicator';
        banner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #ef4444;
            color: #fff;
            padding: 0.75rem;
            text-align: center;
            font-size: 0.9rem;
            font-weight: 600;
            z-index: 10000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        `;
        banner.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 0.5rem;">
                <line x1="1" y1="1" x2="23" y2="23"/>
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                <path d="M10.71 5.05A16 16 0 0 1 22.58 9"/>
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
                <line x1="12" y1="20" x2="12.01" y2="20"/>
            </svg>
            You are offline - Some features may not work
        `;
        document.body.appendChild(banner);
    }

    removeOfflineIndicator() {
        const existing = document.getElementById('offline-indicator');
        if (existing) {
            existing.remove();
        }
    }

    /**
     * Add listener for network state changes
     * @param {Function} callback - Callback function (receives 'online' or 'offline')
     */
    addListener(callback) {
        this.listeners.push(callback);
    }

    /**
     * Remove listener
     * @param {Function} callback - Callback function to remove
     */
    removeListener(callback) {
        this.listeners = this.listeners.filter(cb => cb !== callback);
    }

    /**
     * Notify all listeners of state change
     * @param {string} state - 'online' or 'offline'
     */
    notifyListeners(state) {
        this.listeners.forEach(callback => {
            try {
                callback(state);
            } catch (error) {
                console.error('Error in network listener:', error);
            }
        });
    }

    /**
     * Check if online
     * @returns {boolean}
     */
    checkOnline() {
        return this.isOnline;
    }

    /**
     * Test connection by pinging server
     * @returns {Promise<boolean>}
     */
    async testConnection() {
        try {
            const response = await fetch('/health', {
                method: 'GET',
                cache: 'no-cache',
                signal: AbortSignal.timeout(5000)
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Initialize network monitor
const networkMonitor = new NetworkMonitor();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NetworkMonitor;
}
