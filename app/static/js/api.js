/**
 * API Helper Functions
 * Handles all API calls and communication with backend
 */

const API_BASE_URL = '/api';

/**
 * Make a GET request
 */
async function apiGet(endpoint, params = null) {
    let url = `${API_BASE_URL}${endpoint}`;
    
    if (params) {
        const queryString = new URLSearchParams(params).toString();
        url += '?' + queryString;
    }
    
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('GET request failed:', error);
        showNotification('Error fetching data', 'error');
        throw error;
    }
}

/**
 * Make a POST request
 */
async function apiPost(endpoint, data = null) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: data ? JSON.stringify(data) : null
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('POST request failed:', error);
        showNotification('Error processing request', 'error');
        throw error;
    }
}

/**
 * Make a PUT request
 */
async function apiPut(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('PUT request failed:', error);
        showNotification('Error updating data', 'error');
        throw error;
    }
}

/**
 * Make a DELETE request
 */
async function apiDelete(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('DELETE request failed:', error);
        showNotification('Error deleting data', 'error');
        throw error;
    }
}

/**
 * Get authentication token from storage
 */
function getAuthToken() {
    return localStorage.getItem('auth_token') || '';
}

/**
 * Set authentication token
 */
function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
}

/**
 * Remove authentication token
 */
function removeAuthToken() {
    localStorage.removeItem('auth_token');
}

/**
 * Make a file upload request
 */
async function apiUploadFile(endpoint, file, additionalData = null) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('File upload failed:', error);
        showNotification('Error uploading file', 'error');
        throw error;
    }
}

/**
 * Check if request failed due to authentication
 */
function isAuthError(status) {
    return status === 401 || status === 403;
}

/**
 * Handle authentication errors
 */
function handleAuthError() {
    removeAuthToken();
    window.location.href = '/auth/login';
}
