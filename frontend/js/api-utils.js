/**
 * API Utility Functions
 * Reusable patterns for API integration
 */

const APIUtils = {
    /**
     * Standard API call wrapper with error handling
     * @param {Function} apiCall - The API function to call
     * @param {Object} options - Configuration options
     * @returns {Promise<Object>} - Response data or null on error
     */
    async safeCall(apiCall, options = {}) {
        const {
            loadingElement = null,
            loadingText = 'Loading...',
            successMessage = null,
            errorMessage = null,
            onSuccess = null,
            onError = null
        } = options;

        // Show loading state
        if (loadingElement) {
            API.setLoading(loadingElement, true, loadingText);
        }

        try {
            const response = await apiCall();
            
            if (response.success) {
                // Show success message
                if (successMessage) {
                    API.showToast(successMessage, 'success');
                }
                
                // Call success callback
                if (onSuccess) {
                    onSuccess(response.data);
                }
                
                return response.data;
            } else {
                throw new Error(response.error?.message || 'Operation failed');
            }
        } catch (error) {
            console.error('API call failed:', error);
            
            // Show error message
            if (errorMessage) {
                API.showToast(errorMessage, 'error');
            }
            
            // Call error callback
            if (onError) {
                onError(error);
            }
            
            return null;
        } finally {
            // Clear loading state
            if (loadingElement) {
                API.setLoading(loadingElement, false);
            }
        }
    },

    /**
     * Debounce function to prevent rapid API calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} - Debounced function
     */
    debounce(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Prevent duplicate API calls
     * @param {string} key - Unique key for the operation
     * @param {Function} apiCall - The API function to call
     * @returns {Promise<Object>} - Response or cached promise
     */
    preventDuplicate(key, apiCall) {
        if (!this._pendingCalls) {
            this._pendingCalls = new Map();
        }

        // Return existing promise if call is in progress
        if (this._pendingCalls.has(key)) {
            return this._pendingCalls.get(key);
        }

        // Create new promise
        const promise = apiCall().finally(() => {
            this._pendingCalls.delete(key);
        });

        this._pendingCalls.set(key, promise);
        return promise;
    },

    /**
     * Validate form data before API call
     * @param {Object} data - Form data to validate
     * @param {Object} rules - Validation rules
     * @returns {Object} - { valid: boolean, errors: Array }
     */
    validateForm(data, rules) {
        const errors = [];

        for (const [field, rule] of Object.entries(rules)) {
            const value = data[field];

            // Required check
            if (rule.required && (!value || value.trim() === '')) {
                errors.push(`${rule.label || field} is required`);
                continue;
            }

            // Min length check
            if (rule.minLength && value && value.length < rule.minLength) {
                errors.push(`${rule.label || field} must be at least ${rule.minLength} characters`);
            }

            // Max length check
            if (rule.maxLength && value && value.length > rule.maxLength) {
                errors.push(`${rule.label || field} must be at most ${rule.maxLength} characters`);
            }

            // Email check
            if (rule.email && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                errors.push(`${rule.label || field} must be a valid email`);
            }

            // Custom validator
            if (rule.validator && value) {
                const customError = rule.validator(value);
                if (customError) {
                    errors.push(customError);
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    },

    /**
     * Handle file upload with validation
     * @param {File} file - File to upload
     * @param {Object} options - Upload options
     * @returns {Object} - { valid: boolean, error: string }
     */
    validateFile(file, options = {}) {
        const {
            maxSize = 5 * 1024 * 1024, // 5MB default
            allowedTypes = ['application/pdf'],
            allowedExtensions = ['.pdf']
        } = options;

        if (!file) {
            return { valid: false, error: 'No file selected' };
        }

        // Check file size
        if (file.size > maxSize) {
            return { 
                valid: false, 
                error: `File size must be less than ${(maxSize / 1024 / 1024).toFixed(0)}MB` 
            };
        }

        // Check file type
        if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
            return { 
                valid: false, 
                error: `File type must be one of: ${allowedExtensions.join(', ')}` 
            };
        }

        return { valid: true };
    },

    /**
     * Retry failed API call
     * @param {Function} apiCall - The API function to call
     * @param {number} maxRetries - Maximum number of retries
     * @param {number} delay - Delay between retries in ms
     * @returns {Promise<Object>} - Response
     */
    async retry(apiCall, maxRetries = 3, delay = 1000) {
        let lastError;

        for (let i = 0; i < maxRetries; i++) {
            try {
                return await apiCall();
            } catch (error) {
                lastError = error;
                if (i < maxRetries - 1) {
                    await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
                }
            }
        }

        throw lastError;
    },

    /**
     * Check network connectivity
     * @returns {boolean} - True if online
     */
    isOnline() {
        return navigator.onLine;
    },

    /**
     * Handle offline state
     */
    handleOffline() {
        if (!this.isOnline()) {
            API.showToast('You are offline. Please check your internet connection.', 'warning');
            return true;
        }
        return false;
    },

    /**
     * Format error message for display
     * @param {Error} error - Error object
     * @returns {string} - Formatted error message
     */
    formatError(error) {
        if (error.code === 'NETWORK_ERROR') {
            return 'Network error. Please check your connection and try again.';
        }
        if (error.code === 'TIMEOUT') {
            return 'Request timed out. Please try again.';
        }
        if (error.code === 'UNAUTHORIZED') {
            return 'Session expired. Please log in again.';
        }
        if (error.code === 'VALIDATION_ERROR') {
            return error.message || 'Please check your input and try again.';
        }
        return error.message || 'An unexpected error occurred. Please try again.';
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIUtils;
}
