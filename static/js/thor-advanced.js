/**
 * THOR Advanced Capabilities JavaScript
 * Handles all interactions with THOR's advanced features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ====== Code Generation ======
    const generateCodeBtn = document.getElementById('generateCodeBtn');
    const codeDescription = document.getElementById('codeDescription');
    const codeLanguage = document.getElementById('codeLanguage');
    const generatedCode = document.getElementById('generatedCode');
    const copyCodeBtn = document.getElementById('copyCodeBtn');
    const saveCodeBtn = document.getElementById('saveCodeBtn');

    if (generateCodeBtn) {
        generateCodeBtn.addEventListener('click', function() {
            if (!codeDescription.value.trim()) {
                alert('Please provide a description of the code you want to generate.');
                return;
            }

            // Show loading state
            generatedCode.textContent = 'Generating code...';
            generateCodeBtn.disabled = true;
            saveCodeBtn.disabled = true;

            // Make API request to generate code
            fetch('/api/thor/generate-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: codeDescription.value,
                    language: codeLanguage.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    generatedCode.textContent = data.code;
                    saveCodeBtn.disabled = false;
                } else {
                    generatedCode.textContent = `Error: ${data.message || 'Failed to generate code'}`;
                }
            })
            .catch(error => {
                console.error('Error generating code:', error);
                generatedCode.textContent = `Error: ${error.message || 'An unexpected error occurred'}`;
            })
            .finally(() => {
                generateCodeBtn.disabled = false;
            });
        });
    }

    if (copyCodeBtn) {
        copyCodeBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(generatedCode.textContent)
                .then(() => {
                    const originalTitle = copyCodeBtn.getAttribute('data-bs-original-title');
                    copyCodeBtn.setAttribute('data-bs-original-title', 'Copied!');
                    const tooltip = bootstrap.Tooltip.getInstance(copyCodeBtn);
                    if (tooltip) {
                        tooltip.show();
                        
                        setTimeout(() => {
                            copyCodeBtn.setAttribute('data-bs-original-title', originalTitle);
                            tooltip.hide();
                        }, 1000);
                    }
                })
                .catch(error => {
                    console.error('Failed to copy:', error);
                    alert('Failed to copy code to clipboard');
                });
        });
    }

    // ====== Code Analysis ======
    const analyzeCodeBtn = document.getElementById('analyzeCodeBtn');
    const codeToAnalyze = document.getElementById('codeToAnalyze');
    const issuesList = document.getElementById('issuesList');
    const improvementsList = document.getElementById('improvementsList');
    const analysisSummary = document.getElementById('analysisSummary');
    const exportAnalysisBtn = document.getElementById('exportAnalysisBtn');

    if (analyzeCodeBtn) {
        analyzeCodeBtn.addEventListener('click', function() {
            if (!codeToAnalyze.value.trim()) {
                alert('Please paste code to analyze.');
                return;
            }

            // Show loading state
            issuesList.innerHTML = '<li class="list-group-item">Analyzing code...</li>';
            improvementsList.innerHTML = '<li class="list-group-item">Analyzing code...</li>';
            analysisSummary.textContent = 'Analyzing code...';
            analyzeCodeBtn.disabled = true;
            exportAnalysisBtn.disabled = true;

            // Make API request to analyze code
            fetch('/api/thor/analyze-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: codeToAnalyze.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Display the analysis results
                    displayAnalysisResults(data.analysis);
                    exportAnalysisBtn.disabled = false;
                } else {
                    issuesList.innerHTML = `<li class="list-group-item text-danger">Error: ${data.message || 'Failed to analyze code'}</li>`;
                    improvementsList.innerHTML = `<li class="list-group-item text-danger">Error: ${data.message || 'Failed to analyze code'}</li>`;
                    analysisSummary.textContent = `Error: ${data.message || 'Failed to analyze code'}`;
                }
            })
            .catch(error => {
                console.error('Error analyzing code:', error);
                issuesList.innerHTML = `<li class="list-group-item text-danger">Error: ${error.message || 'An unexpected error occurred'}</li>`;
                improvementsList.innerHTML = `<li class="list-group-item text-danger">Error: ${error.message || 'An unexpected error occurred'}</li>`;
                analysisSummary.textContent = `Error: ${error.message || 'An unexpected error occurred'}`;
            })
            .finally(() => {
                analyzeCodeBtn.disabled = false;
            });
        });
    }

    function displayAnalysisResults(analysis) {
        // Reset content
        issuesList.innerHTML = '';
        improvementsList.innerHTML = '';

        // If analysis result is a string, handle it differently
        if (typeof analysis === 'string') {
            analysisSummary.textContent = analysis;
            issuesList.innerHTML = '<li class="list-group-item">No specific issues identified.</li>';
            improvementsList.innerHTML = '<li class="list-group-item">No specific improvements suggested.</li>';
            return;
        }

        // Parse and display issues
        if (analysis.issues && analysis.issues.length > 0) {
            analysis.issues.forEach(issue => {
                const severityClass = getSeverityClass(issue.severity);
                issuesList.innerHTML += `
                    <li class="list-group-item">
                        <span class="badge ${severityClass} me-2">${issue.severity || 'Info'}</span>
                        <strong>${issue.title || 'Issue'}</strong>
                        <p class="mb-0 mt-1">${issue.description || ''}</p>
                        ${issue.line ? `<small class="text-muted">Line: ${issue.line}</small>` : ''}
                    </li>
                `;
            });
        } else {
            issuesList.innerHTML = '<li class="list-group-item">No issues found.</li>';
        }

        // Parse and display improvements
        if (analysis.improvements && analysis.improvements.length > 0) {
            analysis.improvements.forEach(improvement => {
                improvementsList.innerHTML += `
                    <li class="list-group-item">
                        <strong>${improvement.title || 'Improvement'}</strong>
                        <p class="mb-0 mt-1">${improvement.description || ''}</p>
                        ${improvement.example ? `<pre class="mt-2 bg-dark text-light p-2 rounded">${improvement.example}</pre>` : ''}
                    </li>
                `;
            });
        } else {
            improvementsList.innerHTML = '<li class="list-group-item">No specific improvements suggested.</li>';
        }

        // Display summary
        analysisSummary.textContent = analysis.summary || 'No summary provided.';
    }

    function getSeverityClass(severity) {
        switch (severity?.toLowerCase()) {
            case 'critical':
                return 'bg-danger';
            case 'high':
                return 'bg-warning text-dark';
            case 'medium':
                return 'bg-info text-dark';
            case 'low':
                return 'bg-success';
            default:
                return 'bg-secondary';
        }
    }

    // ====== Dataset Creation ======
    const generateDatasetBtn = document.getElementById('generateDatasetBtn');
    const datasetDescription = document.getElementById('datasetDescription');
    const datasetFormat = document.getElementById('datasetFormat');
    const datasetSize = document.getElementById('datasetSize');
    const generatedDataset = document.getElementById('generatedDataset');
    const copyDatasetBtn = document.getElementById('copyDatasetBtn');
    const downloadDatasetBtn = document.getElementById('downloadDatasetBtn');

    if (generateDatasetBtn) {
        generateDatasetBtn.addEventListener('click', function() {
            if (!datasetDescription.value.trim()) {
                alert('Please provide a description of the dataset you want to create.');
                return;
            }

            // Show loading state
            generatedDataset.textContent = 'Generating dataset...';
            generateDatasetBtn.disabled = true;
            downloadDatasetBtn.disabled = true;

            // Make API request to generate dataset
            fetch('/api/thor/create-dataset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: datasetDescription.value,
                    format: datasetFormat.value,
                    size: parseInt(datasetSize.value)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Format the dataset for display
                    let displayData = data.dataset;
                    if (typeof displayData === 'object') {
                        displayData = JSON.stringify(displayData, null, 2);
                    }
                    generatedDataset.textContent = displayData;
                    downloadDatasetBtn.disabled = false;
                } else {
                    generatedDataset.textContent = `Error: ${data.message || 'Failed to generate dataset'}`;
                }
            })
            .catch(error => {
                console.error('Error generating dataset:', error);
                generatedDataset.textContent = `Error: ${error.message || 'An unexpected error occurred'}`;
            })
            .finally(() => {
                generateDatasetBtn.disabled = false;
            });
        });
    }

    if (copyDatasetBtn) {
        copyDatasetBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(generatedDataset.textContent)
                .then(() => {
                    const originalTitle = copyDatasetBtn.getAttribute('data-bs-original-title');
                    copyDatasetBtn.setAttribute('data-bs-original-title', 'Copied!');
                    const tooltip = bootstrap.Tooltip.getInstance(copyDatasetBtn);
                    if (tooltip) {
                        tooltip.show();
                        
                        setTimeout(() => {
                            copyDatasetBtn.setAttribute('data-bs-original-title', originalTitle);
                            tooltip.hide();
                        }, 1000);
                    }
                })
                .catch(error => {
                    console.error('Failed to copy:', error);
                    alert('Failed to copy dataset to clipboard');
                });
        });
    }

    if (downloadDatasetBtn) {
        downloadDatasetBtn.addEventListener('click', function() {
            const dataStr = generatedDataset.textContent;
            const dataBlob = new Blob([dataStr], { type: 'text/plain' });
            const url = URL.createObjectURL(dataBlob);
            
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `dataset.${datasetFormat.value}`;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        });
    }

    // ====== Network Scan ======
    const generateNetworkScanBtn = document.getElementById('generateNetworkScanBtn');
    const networkDescription = document.getElementById('networkDescription');
    const networkScript = document.getElementById('networkScript');
    const scriptExplanation = document.getElementById('scriptExplanation');
    const copyNetworkScriptBtn = document.getElementById('copyNetworkScriptBtn');
    const saveNetworkScriptBtn = document.getElementById('saveNetworkScriptBtn');

    if (generateNetworkScanBtn) {
        generateNetworkScanBtn.addEventListener('click', function() {
            if (!networkDescription.value.trim()) {
                alert('Please provide a description of the network task.');
                return;
            }

            // Show loading state
            networkScript.textContent = 'Generating script...';
            scriptExplanation.innerHTML = '<p class="text-muted">Generating explanation...</p>';
            generateNetworkScanBtn.disabled = true;
            saveNetworkScriptBtn.disabled = true;

            // Make API request to generate network scan script
            fetch('/api/thor/network-scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target_description: networkDescription.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    networkScript.textContent = data.result.script || 'No script generated.';
                    scriptExplanation.innerHTML = `<p>${data.result.explanation || 'No explanation provided.'}</p>`;
                    saveNetworkScriptBtn.disabled = false;
                } else {
                    networkScript.textContent = `Error: ${data.message || 'Failed to generate network scan script'}`;
                    scriptExplanation.innerHTML = `<p class="text-danger">Error: ${data.message || 'Failed to generate explanation'}</p>`;
                }
            })
            .catch(error => {
                console.error('Error generating network scan:', error);
                networkScript.textContent = `Error: ${error.message || 'An unexpected error occurred'}`;
                scriptExplanation.innerHTML = `<p class="text-danger">Error: ${error.message || 'An unexpected error occurred'}</p>`;
            })
            .finally(() => {
                generateNetworkScanBtn.disabled = false;
            });
        });
    }

    if (copyNetworkScriptBtn) {
        copyNetworkScriptBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(networkScript.textContent)
                .then(() => {
                    const originalTitle = copyNetworkScriptBtn.getAttribute('data-bs-original-title');
                    copyNetworkScriptBtn.setAttribute('data-bs-original-title', 'Copied!');
                    const tooltip = bootstrap.Tooltip.getInstance(copyNetworkScriptBtn);
                    if (tooltip) {
                        tooltip.show();
                        
                        setTimeout(() => {
                            copyNetworkScriptBtn.setAttribute('data-bs-original-title', originalTitle);
                            tooltip.hide();
                        }, 1000);
                    }
                })
                .catch(error => {
                    console.error('Failed to copy:', error);
                    alert('Failed to copy script to clipboard');
                });
        });
    }

    // ====== Clone Manager ======
    const refreshClonesBtn = document.getElementById('refreshClonesBtn');
    const clonesTableBody = document.getElementById('clonesTableBody');
    const deactivateAllClonesBtn = document.getElementById('deactivateAllClonesBtn');
    const createCloneForm = document.getElementById('createCloneForm');
    const cloneDescription = document.getElementById('cloneDescription');
    const createCloneResult = document.getElementById('createCloneResult');
    const updateCloneForm = document.getElementById('updateCloneForm');
    const cloneToUpdate = document.getElementById('cloneToUpdate');
    const updateDescription = document.getElementById('updateDescription');
    const updateCapabilities = document.getElementById('updateCapabilities');
    const updateCloneResult = document.getElementById('updateCloneResult');
    
    // Load clone list when the modal is shown
    const cloneManagerModal = document.getElementById('cloneManagerModal');
    if (cloneManagerModal) {
        cloneManagerModal.addEventListener('shown.bs.modal', function() {
            loadCloneList();
        });
    }

    // Refresh clones button
    if (refreshClonesBtn) {
        refreshClonesBtn.addEventListener('click', function() {
            loadCloneList();
        });
    }

    // Deactivate all clones button
    if (deactivateAllClonesBtn) {
        deactivateAllClonesBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to deactivate all THOR clones?')) {
                deactivateAllClonesBtn.disabled = true;
                deactivateAllClonesBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deactivating...';
                
                fetch('/api/thor/deactivate-clones', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showAlert('All clones deactivated successfully', 'success');
                        loadCloneList();
                    } else {
                        showAlert(`Error: ${data.message || 'Failed to deactivate clones'}`, 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error deactivating clones:', error);
                    showAlert(`Error: ${error.message || 'An unexpected error occurred'}`, 'danger');
                })
                .finally(() => {
                    deactivateAllClonesBtn.disabled = false;
                    deactivateAllClonesBtn.innerHTML = '<i class="fas fa-power-off me-2"></i>Deactivate All Clones';
                });
            }
        });
    }

    // Create clone form
    if (createCloneForm) {
        createCloneForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            if (!cloneDescription.value.trim()) {
                alert('Please provide a description for the clone.');
                return;
            }
            
            const submitBtn = createCloneForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';
            createCloneResult.innerHTML = '<div class="alert alert-info">Creating clone...</div>';
            
            fetch('/api/thor/create-clone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: cloneDescription.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    createCloneResult.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Success!</strong> Clone "${data.clone.name}" created successfully.
                        </div>
                    `;
                    cloneDescription.value = '';
                    // Update clone list and select the new clone
                    loadCloneList().then(() => {
                        // Switch to the clones tab
                        const clonesTab = document.getElementById('cloneList-tab');
                        if (clonesTab) {
                            const tab = new bootstrap.Tab(clonesTab);
                            tab.show();
                        }
                    });
                } else {
                    createCloneResult.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Error!</strong> ${data.message || 'Failed to create clone'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error creating clone:', error);
                createCloneResult.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error!</strong> ${error.message || 'An unexpected error occurred'}
                    </div>
                `;
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-clone me-2"></i>Create THOR Clone';
            });
        });
    }

    // Update clone form
    if (updateCloneForm) {
        updateCloneForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            if (!cloneToUpdate.value) {
                alert('Please select a clone to update.');
                return;
            }
            
            let capabilitiesObj = {};
            if (updateCapabilities.value.trim()) {
                try {
                    capabilitiesObj = JSON.parse(updateCapabilities.value);
                } catch (e) {
                    alert('Invalid JSON in capabilities field. Please check the format and try again.');
                    return;
                }
            }
            
            const submitBtn = updateCloneForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Updating...';
            updateCloneResult.innerHTML = '<div class="alert alert-info">Updating clone...</div>';
            
            const updates = {
                description: updateDescription.value.trim() || undefined,
                capabilities: Object.keys(capabilitiesObj).length > 0 ? capabilitiesObj : undefined
            };
            
            fetch('/api/thor/update-clone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    clone_name: cloneToUpdate.value,
                    updates: updates
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateCloneResult.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Success!</strong> Clone "${cloneToUpdate.value}" updated successfully.
                        </div>
                    `;
                    // Update clone list
                    loadCloneList().then(() => {
                        // Switch to the clones tab
                        const clonesTab = document.getElementById('cloneList-tab');
                        if (clonesTab) {
                            const tab = new bootstrap.Tab(clonesTab);
                            tab.show();
                        }
                    });
                } else {
                    updateCloneResult.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Error!</strong> ${data.message || 'Failed to update clone'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error updating clone:', error);
                updateCloneResult.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error!</strong> ${error.message || 'An unexpected error occurred'}
                    </div>
                `;
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-sync me-2"></i>Update Clone';
            });
        });
    }

    function loadCloneList() {
        if (!clonesTableBody) return Promise.resolve();
        
        clonesTableBody.innerHTML = '<tr><td colspan="6" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading clones...</td></tr>';
        
        return fetch('/api/thor/list-clones')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (data.clones && data.clones.length > 0) {
                        clonesTableBody.innerHTML = '';
                        
                        // Populate the table
                        data.clones.forEach(clone => {
                            const createdDate = new Date(clone.created_at).toLocaleString();
                            const statusBadge = clone.is_active 
                                ? '<span class="badge bg-success">Active</span>' 
                                : '<span class="badge bg-secondary">Inactive</span>';
                            
                            clonesTableBody.innerHTML += `
                                <tr>
                                    <td>${clone.name}</td>
                                    <td>${clone.description || 'No description'}</td>
                                    <td>${clone.base_version || 'Unknown'}</td>
                                    <td>${createdDate}</td>
                                    <td>${statusBadge}</td>
                                    <td>
                                        ${!clone.is_active ? 
                                            `<button class="btn btn-sm btn-success activate-clone-btn" data-clone="${clone.name}">
                                                <i class="fas fa-power-off"></i> Activate
                                            </button>` : 
                                            `<button class="btn btn-sm btn-secondary" disabled>
                                                <i class="fas fa-check"></i> Active
                                            </button>`
                                        }
                                    </td>
                                </tr>
                            `;
                        });
                        
                        // Add event listeners for the activate buttons
                        document.querySelectorAll('.activate-clone-btn').forEach(btn => {
                            btn.addEventListener('click', function() {
                                const cloneName = this.getAttribute('data-clone');
                                activateClone(cloneName, this);
                            });
                        });
                        
                        // Update the select for updating clones
                        if (cloneToUpdate) {
                            const currentValue = cloneToUpdate.value;
                            cloneToUpdate.innerHTML = '<option value="" disabled>Select a clone to update...</option>';
                            
                            data.clones.forEach(clone => {
                                const option = document.createElement('option');
                                option.value = clone.name;
                                option.textContent = `${clone.name} (${clone.is_active ? 'Active' : 'Inactive'})`;
                                cloneToUpdate.appendChild(option);
                            });
                            
                            // Restore selection if possible
                            if (currentValue && Array.from(cloneToUpdate.options).some(opt => opt.value === currentValue)) {
                                cloneToUpdate.value = currentValue;
                            }
                        }
                    } else {
                        clonesTableBody.innerHTML = '<tr><td colspan="6" class="text-center">No clones found. Create your first THOR clone!</td></tr>';
                        if (cloneToUpdate) {
                            cloneToUpdate.innerHTML = '<option value="" selected disabled>No clones available</option>';
                        }
                    }
                } else {
                    clonesTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${data.message || 'Failed to load clones'}</td></tr>`;
                }
            })
            .catch(error => {
                console.error('Error loading clones:', error);
                clonesTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${error.message || 'An unexpected error occurred'}</td></tr>`;
                return Promise.reject(error);
            });
    }

    function activateClone(cloneName, buttonElement) {
        if (!cloneName) return;
        
        buttonElement.disabled = true;
        buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        fetch('/api/thor/activate-clone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                clone_name: cloneName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert(`Clone "${cloneName}" activated successfully`, 'success');
                loadCloneList();
            } else {
                showAlert(`Error: ${data.message || 'Failed to activate clone'}`, 'danger');
                buttonElement.disabled = false;
                buttonElement.innerHTML = '<i class="fas fa-power-off"></i> Activate';
            }
        })
        .catch(error => {
            console.error('Error activating clone:', error);
            showAlert(`Error: ${error.message || 'An unexpected error occurred'}`, 'danger');
            buttonElement.disabled = false;
            buttonElement.innerHTML = '<i class="fas fa-power-off"></i> Activate';
        });
    }

    // ====== Self-Improvement ======
    const requestImprovementsBtn = document.getElementById('requestImprovementsBtn');
    const improvementSuggestions = document.getElementById('improvementSuggestions');
    const implementImprovementsBtn = document.getElementById('implementImprovementsBtn');

    if (requestImprovementsBtn) {
        requestImprovementsBtn.addEventListener('click', function() {
            // Show loading state
            improvementSuggestions.innerHTML = `
                <div class="text-center p-4">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p>THOR is analyzing systems and generating improvement suggestions...</p>
                </div>
            `;
            requestImprovementsBtn.disabled = true;
            implementImprovementsBtn.disabled = true;

            // Make API request for improvement suggestions
            fetch('/api/thor/suggest-improvements', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    displayImprovementSuggestions(data.suggestions);
                    implementImprovementsBtn.disabled = false;
                } else {
                    improvementSuggestions.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            <strong>Error:</strong> ${data.message || 'Failed to generate improvement suggestions'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error requesting improvements:', error);
                improvementSuggestions.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        <strong>Error:</strong> ${error.message || 'An unexpected error occurred'}
                    </div>
                `;
            })
            .finally(() => {
                requestImprovementsBtn.disabled = false;
            });
        });
    }

    function displayImprovementSuggestions(suggestions) {
        if (!improvementSuggestions) return;
        
        if (!suggestions || (Array.isArray(suggestions) && suggestions.length === 0)) {
            improvementSuggestions.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No improvement suggestions at this time. THOR systems are running optimally.
                </div>
            `;
            return;
        }
        
        // If suggestions is a string, display it directly
        if (typeof suggestions === 'string') {
            improvementSuggestions.innerHTML = `<p>${suggestions}</p>`;
            return;
        }
        
        // If it's an object with a text property
        if (suggestions.text) {
            improvementSuggestions.innerHTML = `<p>${suggestions.text}</p>`;
            return;
        }
        
        // Otherwise, assume it's an array of suggestion objects
        let html = '<div class="list-group">';
        
        suggestions.forEach((suggestion, index) => {
            const title = suggestion.title || `Improvement ${index + 1}`;
            const description = suggestion.description || suggestion.text || 'No description provided';
            const priority = suggestion.priority || 'medium';
            const priorityBadge = getPriorityBadge(priority);
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="mb-0">${title}</h5>
                        ${priorityBadge}
                    </div>
                    <p>${description}</p>
                    ${suggestion.implementation ? `
                        <div class="mt-2">
                            <strong>Implementation:</strong>
                            <pre class="bg-dark text-light p-2 rounded mt-1">${suggestion.implementation}</pre>
                        </div>
                    ` : ''}
                    <div class="form-check mt-2">
                        <input class="form-check-input" type="checkbox" value="" id="improvement${index}" checked>
                        <label class="form-check-label" for="improvement${index}">
                            Select for implementation
                        </label>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        improvementSuggestions.innerHTML = html;
    }

    function getPriorityBadge(priority) {
        switch (priority.toLowerCase()) {
            case 'critical':
                return '<span class="badge bg-danger">Critical</span>';
            case 'high':
                return '<span class="badge bg-warning text-dark">High</span>';
            case 'medium':
                return '<span class="badge bg-info text-dark">Medium</span>';
            case 'low':
                return '<span class="badge bg-success">Low</span>';
            default:
                return '<span class="badge bg-secondary">Normal</span>';
        }
    }

    // ====== Helper Functions ======
    function showAlert(message, type = 'info') {
        // Create alert container if it doesn't exist
        let alertContainer = document.getElementById('thor-alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'thor-alert-container';
            alertContainer.style.position = 'fixed';
            alertContainer.style.top = '20px';
            alertContainer.style.right = '20px';
            alertContainer.style.zIndex = '9999';
            document.body.appendChild(alertContainer);
        }
        
        // Create alert
        const alertId = 'thor-alert-' + Date.now();
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.id = alertId;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add alert to container
        alertContainer.appendChild(alertElement);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
});
