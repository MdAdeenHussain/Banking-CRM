/**
 * Form Utilities and Validation
 * Handles form submission, validation, and data processing
 */

/**
 * Handle form submission
 */
async function handleFormSubmit(formId, endpoint, options = {}) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form with ID ${formId} not found`);
        return;
    }
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validate form
        if (!validateForm(form)) {
            showNotification('Please fill all required fields correctly', 'warning');
            return;
        }
        
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        try {
            const method = options.method || 'POST';
            let response;
            
            if (method === 'POST') {
                response = await apiPost(endpoint, data);
            } else if (method === 'PUT') {
                response = await apiPut(endpoint, data);
            }
            
            if (response.success) {
                showNotification(response.message || 'Success', 'success');
                
                if (options.redirectUrl) {
                    setTimeout(() => {
                        window.location.href = options.redirectUrl;
                    }, 1000);
                }
                
                if (options.onSuccess) {
                    options.onSuccess(response);
                }
                
                if (options.resetForm) {
                    form.reset();
                }
            } else {
                showNotification(response.message || 'Error occurred', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            showNotification('Error submitting form', 'error');
        }
    });
}

/**
 * Validate form fields
 */
function validateForm(form) {
    let isValid = true;
    
    form.querySelectorAll('[required]').forEach(field => {
        if (!validateField(field)) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Validate individual field
 */
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const pattern = field.pattern;
    
    // Check if empty
    if (!value && field.hasAttribute('required')) {
        return false;
    }
    
    // Type-specific validation
    if (type === 'email') {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    }
    
    if (type === 'tel') {
        return /^[\d\s\-\+\(\)]+$/.test(value) && value.replace(/\D/g, '').length >= 10;
    }
    
    if (type === 'number') {
        return !isNaN(value) && value !== '';
    }
    
    if (type === 'url') {
        try {
            new URL(value);
            return true;
        } catch {
            return false;
        }
    }
    
    // Pattern validation
    if (pattern) {
        return new RegExp(pattern).test(value);
    }
    
    return true;
}

/**
 * Add real-time validation to fields
 */
function enableRealtimeValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.querySelectorAll('input, textarea, select').forEach(field => {
        field.addEventListener('blur', function() {
            if (validateField(this)) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else if (this.hasAttribute('required')) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            }
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                if (validateField(this)) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            }
        });
    });
}

/**
 * Populate form with data
 */
function populateForm(formId, data) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    Object.keys(data).forEach(key => {
        const field = form.elements[key];
        if (field) {
            if (field.type === 'checkbox') {
                field.checked = data[key];
            } else if (field.type === 'radio') {
                form.querySelector(`input[name="${key}"][value="${data[key]}"]`).checked = true;
            } else {
                field.value = data[key];
            }
        }
    });
}

/**
 * Clear form
 */
function clearForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        form.querySelectorAll('.is-invalid, .is-valid').forEach(field => {
            field.classList.remove('is-invalid', 'is-valid');
        });
    }
}

/**
 * Disable form submission button
 */
function disableFormSubmit(formId, message = 'Processing...') {
    const form = document.getElementById(formId);
    const submitBtn = form?.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = message;
    }
}

/**
 * Enable form submission button
 */
function enableFormSubmit(formId, originalText = 'Submit') {
    const form = document.getElementById(formId);
    const submitBtn = form?.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

/**
 * Add form field dynamically
 */
function addFormField(containerId, fieldHTML) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const wrapper = document.createElement('div');
    wrapper.innerHTML = fieldHTML;
    container.appendChild(wrapper.firstElementChild);
}

/**
 * Remove form field
 */
function removeFormField(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.remove();
    }
}

/**
 * Get form data as JSON
 */
function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return null;
    
    const formData = new FormData(form);
    const data = {};
    
    formData.forEach((value, key) => {
        if (data[key]) {
            // Handle multiple values
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    });
    
    return data;
}

/**
 * Show form errors
 */
function showFormErrors(formId, errors) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // Clear previous errors
    form.querySelectorAll('.error-message').forEach(msg => msg.remove());
    
    Object.keys(errors).forEach(fieldName => {
        const field = form.elements[fieldName];
        if (field) {
            field.classList.add('is-invalid');
            
            const errorMsg = document.createElement('div');
            errorMsg.className = 'error-message text-danger small mt-1';
            errorMsg.textContent = errors[fieldName];
            field.parentElement.appendChild(errorMsg);
        }
    });
}

/**
 * Clear form errors
 */
function clearFormErrors(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.querySelectorAll('.is-invalid').forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    form.querySelectorAll('.error-message').forEach(msg => msg.remove());
}
