/**
 * Frontend Integration Patterns
 * Reusable patterns for API integration with api-v2.js
 * 
 * USE THESE PATTERNS IN YOUR HTML FILES
 */

// ═══════════════════════════════════════════════════════════════════════════
// PATTERN 1: Form Submission with Loading & Error Handling
// ═══════════════════════════════════════════════════════════════════════════

async function handleFormSubmit(event, apiCall, successCallback) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const errorEl = form.querySelector('.error-message');
    
    // Clear previous errors
    if (errorEl) errorEl.style.display = 'none';
    
    // Show loading state
    API.setLoading(submitBtn, true);
    
    try {
        // Call API
        const response = await apiCall();
        
        // Check success
        if (response.success) {
            API.showToast(response.message || 'Success!', 'success');
            if (successCallback) successCallback(response.data);
        }
    } catch(err) {
        // Handle error
        if (errorEl) {
            errorEl.textContent = err.message || 'An error occurred';
            errorEl.style.display = 'block';
        } else {
            API.showToast(err.message || 'An error occurred', 'error');
        }
    } finally {
        // Reset loading state
        API.setLoading(submitBtn, false);
    }
}

// Example Usage:
/*
document.getElementById('login-form').addEventListener('submit', (e) => {
    handleFormSubmit(
        e,
        () => API.auth.login(email.value, password.value),
        (data) => window.location.href = 'home.html'
    );
});
*/


// ═══════════════════════════════════════════════════════════════════════════
// PATTERN 2: Data Loading with Loading/Empty/Error States
// ═══════════════════════════════════════════════════════════════════════════

async function loadData(containerId, apiCall, renderFunction, emptyMessage = 'No data available') {
    const container = document.getElementById(containerId);
    
    // Show loading state
    container.innerHTML = `
        <div class="loading-state" style="text-align:center; padding:2rem; color:var(--text-muted);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 0.8s linear infinite; margin-bottom:0.5rem;">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            <div>Loading...</div>
        </div>
    `;
    
    try {
        const response = await apiCall();
        
        if (response.success) {
            const data = response.data;
            
            // Check if data is empty
            const isEmpty = !data || 
                           (Array.isArray(data) && data.length === 0) ||
                           (typeof data === 'object' && Object.keys(data).length === 0);
            
            if (isEmpty) {
                // Show empty state
                container.innerHTML = `
                    <div class="empty-state" style="text-align:center; padding:2rem; color:var(--text-muted);">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity:0.3; margin-bottom:1rem;">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 6v6l4 2"/>
                        </svg>
                        <div>${emptyMessage}</div>
                    </div>
                `;
            } else {
                // Render data
                renderFunction(data, container);
            }
        }
    } catch(err) {
        // Show error state
        container.innerHTML = `
            <div class="error-state" style="text-align:center; padding:2rem; color:#ef4444;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:1rem;">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <div>Failed to load data</div>
                <button onclick="location.reload()" style="margin-top:1rem; padding:0.5rem 1rem; background:var(--primary); color:#fff; border:none; border-radius:4px; cursor:pointer;">
                    Retry
                </button>
            </div>
        `;
        console.error('Load error:', err);
    }
}

// Example Usage:
/*
loadData(
    'resume-list',
    () => API.resume.history(),
    (data, container) => {
        container.innerHTML = data.resumes.map(r => `
            <div class="resume-item">${r.file_name} - Score: ${r.ats_score}</div>
        `).join('');
    },
    'No resumes uploaded yet'
);
*/


// ═══════════════════════════════════════════════════════════════════════════
// PATTERN 3: File Upload with Validation
// ═══════════════════════════════════════════════════════════════════════════

function setupFileUpload(inputId, buttonId, onUpload, options = {}) {
    const {
        maxSizeMB = 10,
        allowedExtensions = ['.pdf', '.docx', '.txt'],
        onFileSelected = null
    } = options;
    
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    
    let selectedFile = null;
    
    // Trigger file input
    button.addEventListener('click', () => input.click());
    
    // Handle file selection
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        // Validate extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(ext)) {
            API.showToast(
                `Only ${allowedExtensions.join(', ')} files are allowed`,
                'error'
            );
            input.value = '';
            return;
        }
        
        // Validate size
        const sizeMB = file.size / 1024 / 1024;
        if (sizeMB > maxSizeMB) {
            API.showToast(
                `File too large. Maximum size is ${maxSizeMB}MB`,
                'error'
            );
            input.value = '';
            return;
        }
        
        selectedFile = file;
        
        // Callback
        if (onFileSelected) {
            onFileSelected(file, sizeMB);
        }
    });
    
    // Return upload function
    return async () => {
        if (!selectedFile) {
            API.showToast('Please select a file first', 'warning');
            return null;
        }
        
        try {
            const result = await onUpload(selectedFile);
            selectedFile = null;
            input.value = '';
            return result;
        } catch(err) {
            API.handleError(err, 'File Upload');
            return null;
        }
    };
}

// Example Usage:
/*
const uploadResume = setupFileUpload(
    'file-input',
    'select-file-btn',
    (file) => API.resume.upload(file, targetRole),
    {
        maxSizeMB: 10,
        allowedExtensions: ['.pdf'],
        onFileSelected: (file, sizeMB) => {
            document.getElementById('file-info').textContent = 
                `✓ ${file.name} (${sizeMB.toFixed(2)} MB)`;
        }
    }
);

document.getElementById('upload-btn').addEventListener('click', async () => {
    const response = await uploadResume();
    if (response && response.success) {
        console.log('Upload successful:', response.data);
    }
});
*/


// ═══════════════════════════════════════════════════════════════════════════
// PATTERN 4: Debounced Search/Filter
// ═══════════════════════════════════════════════════════════════════════════

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function setupDebouncedSearch(inputId, searchFunction, delay = 300) {
    const input = document.getElementById(inputId);
    
    const debouncedSearch = debounce(async (query) => {
        if (query.trim().length === 0) return;
        
        try {
            await searchFunction(query);
        } catch(err) {
            console.error('Search error:', err);
        }
    }, delay);
    
    input.addEventListener('input', (e) => {
        debouncedSearch(e.target.value);
    });
}

// Example Usage:
/*
setupDebouncedSearch(
    'search-input',
    async (query) => {
        const response = await API.search(query);
        if (response.success) {
            renderResults(response.data);
        }
    },
    300
);
*/


// ═══════════════════════════════════════════════════════════════════════════
// PATTERN 5: Retry Failed Requests
// ═══════════════════════════════════════════════════════════════════════════

async function retryableAction(apiCall, maxRetries = 2, delayMs = 1000) {
    let lastError;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await apiCall();
            if (response.success) return response;
        } catch(err) {
            lastError = err;
            
            if (attempt < maxRetries) {
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, delayMs * (attempt + 1)));
                console.log(`Retrying... (attempt ${attempt + 2}/${maxRetries + 1})`);
            }
        }
    }
    
    throw lastError;
}

// Example Usage:
/*
try {
    const response = await retryableAction(
        () => API.interview.start(role, level),
        2,  // max 2 retries
        1000  // 1 second delay
    );
    console.log('Success:', response.data);
} catch(err) {
    API.handleError(err, 'Interview Start');
}
*/


// ═══════════════════════════════════════════════════════════════════════════
// PATTERN 6: Pagination Helper
// ═══════════════════════════════════════════════════════════════════════════

function setupPagination(containerId, apiCall, renderFunction, itemsPerPage = 10) {
    let currentPage = 1;
    let totalItems = 0;
    
    async function loadPage(page) {
        try {
            const response = await apiCall(page, itemsPerPage);
            
            if (response.success) {
                const data = response.data;
                totalItems = data.total || 0;
                
                renderFunction(data.items || data, document.getElementById(containerId));
                renderPaginationControls(page);
            }
        } catch(err) {
            API.handleError(err, 'Load Page');
        }
    }
    
    function renderPaginationControls(page) {
        const totalPages = Math.ceil(totalItems / itemsPerPage);
        const controls = document.getElementById(containerId + '-pagination');
        
        if (!controls || totalPages <= 1) return;
        
        controls.innerHTML = `
            <button ${page === 1 ? 'disabled' : ''} onclick="loadPage(${page - 1})">Previous</button>
            <span>Page ${page} of ${totalPages}</span>
            <button ${page === totalPages ? 'disabled' : ''} onclick="loadPage(${page + 1})">Next</button>
        `;
    }
    
    // Initial load
    loadPage(1);
    
    // Expose loadPage globally
    window.loadPage = loadPage;
}

// Example Usage:
/*
setupPagination(
    'results-container',
    (page, limit) => API.getResults(page, limit),
    (items, container) => {
        container.innerHTML = items.map(item => `
            <div class="item">${item.name}</div>
        `).join('');
    },
    10
);
*/


// ═══════════════════════════════════════════════════════════════════════════
// PATTERN 7: Confirmation Dialog
// ═══════════════════════════════════════════════════════════════════════════

function confirmAction(message, onConfirm, onCancel = null) {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.7); z-index: 9999;
        display: flex; align-items: center; justify-content: center;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: var(--bg-panel); border-radius: 12px;
        padding: 2rem; max-width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    `;
    
    dialog.innerHTML = `
        <h3 style="margin: 0 0 1rem 0; color: var(--text-main);">Confirm Action</h3>
        <p style="margin: 0 0 1.5rem 0; color: var(--text-muted);">${message}</p>
        <div style="display: flex; gap: 0.75rem; justify-content: flex-end;">
            <button id="cancel-btn" class="btn-secondary">Cancel</button>
            <button id="confirm-btn" class="btn-primary">Confirm</button>
        </div>
    `;
    
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    
    dialog.querySelector('#cancel-btn').addEventListener('click', () => {
        overlay.remove();
        if (onCancel) onCancel();
    });
    
    dialog.querySelector('#confirm-btn').addEventListener('click', () => {
        overlay.remove();
        onConfirm();
    });
}

// Example Usage:
/*
document.getElementById('delete-btn').addEventListener('click', () => {
    confirmAction(
        'Are you sure you want to delete this item?',
        async () => {
            const response = await API.deleteItem(itemId);
            if (response.success) {
                API.showToast('Item deleted', 'success');
            }
        }
    );
});
*/


// ═══════════════════════════════════════════════════════════════════════════
// Export for use in other files
// ═══════════════════════════════════════════════════════════════════════════

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        handleFormSubmit,
        loadData,
        setupFileUpload,
        debounce,
        setupDebouncedSearch,
        retryableAction,
        setupPagination,
        confirmAction
    };
}
