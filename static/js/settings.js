/**
 * Settings management for AI system
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const settingsForm = document.getElementById('settings-form');
    const downloadModelForm = document.getElementById('download-model-form');
    const cloneModelForm = document.getElementById('clone-model-form');
    const advancedSettingsEditor = document.getElementById('advanced-settings');
    
    // Initialize settings page if we're on it
    if (settingsForm) {
        initializeSettingsPage();
    }
    
    /**
     * Initialize settings page components
     */
    function initializeSettingsPage() {
        // Format JSON in advanced settings textarea
        if (advancedSettingsEditor) {
            try {
                const currentSettings = advancedSettingsEditor.value;
                if (currentSettings) {
                    const formattedSettings = JSON.stringify(JSON.parse(currentSettings), null, 2);
                    advancedSettingsEditor.value = formattedSettings;
                }
            } catch (e) {
                console.error('Error formatting advanced settings JSON:', e);
            }
        }
        
        // Set up model download form
        if (downloadModelForm) {
            downloadModelForm.addEventListener('submit', function(e) {
                e.preventDefault();
                downloadModel();
            });
        }
        
        // Set up model clone form
        if (cloneModelForm) {
            cloneModelForm.addEventListener('submit', function(e) {
                e.preventDefault();
                cloneModel();
            });
        }
        
        // Load available models
        loadAvailableModels();
    }
    
    /**
     * Download a model from Hugging Face or GitHub
     */
    function downloadModel() {
        const modelName = document.getElementById('model-name').value;
        const modelSource = document.getElementById('model-source').value;
        const repoUrl = document.getElementById('repo-url')?.value;
        
        // Validate inputs
        if (!modelName) {
            showAlert('Please enter a model name.', 'danger');
            return;
        }
        
        if (modelSource === 'github' && !repoUrl) {
            showAlert('Please enter a GitHub repository URL.', 'danger');
            return;
        }
        
        // Disable form during download
        toggleFormElements(downloadModelForm, true);
        
        // Show loading status
        showAlert('Starting model download. This may take a while...', 'info', 'download-status');
        
        // Prepare request data
        const data = {
            model_name: modelName,
            source: modelSource
        };
        
        if (modelSource === 'github') {
            data.repo_url = repoUrl;
        }
        
        // Send request to server
        fetch('/api/models/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(data => {
            toggleFormElements(downloadModelForm, false);
            
            if (data.success) {
                showAlert(`Model ${modelName} downloaded successfully!`, 'success', 'download-status');
                // Refresh model list
                loadAvailableModels();
            } else {
                showAlert(`Error downloading model: ${data.error}`, 'danger', 'download-status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toggleFormElements(downloadModelForm, false);
            showAlert(`Error downloading model: ${error.message}`, 'danger', 'download-status');
        });
    }
    
    /**
     * Clone and modify a model
     */
    function cloneModel() {
        const originalModel = document.getElementById('original-model').value;
        const newModelName = document.getElementById('new-model-name').value;
        const modificationsText = document.getElementById('modifications')?.value;
        
        // Validate inputs
        if (!originalModel || !newModelName) {
            showAlert('Please select an original model and provide a name for the clone.', 'danger');
            return;
        }
        
        // Parse modifications JSON if provided
        let modifications = {};
        if (modificationsText) {
            try {
                modifications = JSON.parse(modificationsText);
            } catch (e) {
                showAlert('Invalid JSON in modifications field.', 'danger');
                return;
            }
        }
        
        // Disable form during cloning
        toggleFormElements(cloneModelForm, true);
        
        // Show loading status
        showAlert('Cloning model. This may take a while...', 'info', 'clone-status');
        
        // Send request to server
        fetch('/api/models/clone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                original_model: originalModel,
                new_model_name: newModelName,
                modifications: modifications
            }),
        })
        .then(response => response.json())
        .then(data => {
            toggleFormElements(cloneModelForm, false);
            
            if (data.success) {
                showAlert(`Model cloned successfully to ${newModelName}!`, 'success', 'clone-status');
                // Refresh model list
                loadAvailableModels();
            } else {
                showAlert(`Error cloning model: ${data.error}`, 'danger', 'clone-status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toggleFormElements(cloneModelForm, false);
            showAlert(`Error cloning model: ${error.message}`, 'danger', 'clone-status');
        });
    }
    
    /**
     * Load available models from server
     */
    function loadAvailableModels() {
        const originalModelSelect = document.getElementById('original-model');
        const preferredModelSelect = document.getElementById('preferred-model');
        
        if (!originalModelSelect && !preferredModelSelect) {
            return;
        }
        
        fetch('/api/models/list')
            .then(response => response.json())
            .then(data => {
                const models = data.models || [];
                
                // Update original model select
                if (originalModelSelect) {
                    // Save current selection
                    const currentSelection = originalModelSelect.value;
                    
                    // Clear options
                    originalModelSelect.innerHTML = '';
                    
                    // Add new options
                    models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.name;
                        option.textContent = `${model.name} (${model.source})`;
                        originalModelSelect.appendChild(option);
                    });
                    
                    // Restore selection if possible
                    if (currentSelection && originalModelSelect.querySelector(`option[value="${currentSelection}"]`)) {
                        originalModelSelect.value = currentSelection;
                    }
                }
                
                // Update preferred model select
                if (preferredModelSelect) {
                    // Save current selection
                    const currentSelection = preferredModelSelect.value;
                    
                    // Keep existing options (they come from the server-rendered page)
                    // and add any new ones
                    const existingValues = Array.from(preferredModelSelect.options).map(opt => opt.value);
                    
                    models.forEach(model => {
                        if (!existingValues.includes(model.name)) {
                            const option = document.createElement('option');
                            option.value = model.name;
                            option.textContent = `${model.name} (${model.source})`;
                            preferredModelSelect.appendChild(option);
                        }
                    });
                    
                    // Restore selection
                    if (currentSelection) {
                        preferredModelSelect.value = currentSelection;
                    }
                }
            })
            .catch(error => {
                console.error('Error loading models:', error);
                showAlert('Error loading available models', 'danger');
            });
    }
    
    /**
     * Show an alert message
     */
    function showAlert(message, type, elementId = null) {
        if (elementId) {
            // Show in a specific element
            const element = document.getElementById(elementId);
            if (element) {
                element.innerHTML = `<div class="alert alert-${type} mt-3">${message}</div>`;
            }
        } else {
            // Create a new alert at the top of the page
            const alertContainer = document.getElementById('alert-container') || document.createElement('div');
            alertContainer.id = 'alert-container';
            alertContainer.className = 'container mt-3';
            
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.role = 'alert';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            alertContainer.appendChild(alert);
            
            // Add to page if not already there
            if (!document.getElementById('alert-container')) {
                const contentElement = document.querySelector('main') || document.body;
                contentElement.insertBefore(alertContainer, contentElement.firstChild);
            }
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => {
                    alert.remove();
                    if (alertContainer.children.length === 0) {
                        alertContainer.remove();
                    }
                }, 150);
            }, 5000);
        }
    }
    
    /**
     * Enable or disable all form elements
     */
    function toggleFormElements(form, disabled) {
        if (!form) return;
        
        const elements = form.querySelectorAll('input, select, textarea, button');
        elements.forEach(element => {
            element.disabled = disabled;
        });
    }
});
