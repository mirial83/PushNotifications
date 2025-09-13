// PushNotifications Web Interface JavaScript

// Global state management
const state = {
    notifications: [],
    isConnected: false,
    lastRefresh: null,
    refreshInterval: null,
    dbInitialized: false,
    clientCount: 0,
    refreshIntervalSetting: 30 // Default to 30 seconds
};

// Configuration
const config = {
    API_BASE_URL: window.location.origin,
    REFRESH_COUNTDOWN_UPDATE: 1000, // 1 second
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing PushNotifications interface...');
    
    // Initialize user authentication
    initializeUserAuth();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadInitialData();
    
    // Setup refresh timer
    startRefreshTimer();
    
    console.log('PushNotifications interface initialized');
});

function initializeUserAuth() {
    // Authentication removed - no user verification needed
}

function setupEventListeners() {
    // Send notification button
    const sendButton = document.getElementById('sendNotification');
    if (sendButton) {
        sendButton.addEventListener('click', handleSendNotification);
    }
    
    // Initialize database button
    const initDbButton = document.getElementById('initDatabase');
    if (initDbButton) {
        initDbButton.addEventListener('click', handleInitializeDatabase);
    }
    
    // Quick message buttons
    document.querySelectorAll('.btn-small').forEach(button => {
        button.addEventListener('click', function() {
            const message = this.textContent.trim();
            if (message === 'Do your schoolwork' || 
                message === 'Stop watching YouTube' || 
                message === 'Get to work!') {
                addQuickMessage(message);
            }
        });
    });
    
    // Work mode radio buttons
    document.querySelectorAll('input[name="workMode"]').forEach(radio => {
        radio.addEventListener('change', updateWorkModeDescription);
    });
    
    // Browser usage radio buttons
    document.querySelectorAll('input[name="browserUsage"]').forEach(radio => {
        radio.addEventListener('change', updateBrowserUsageDescription);
    });
    
    // Quick add website buttons
    document.querySelectorAll('.quick-add-websites .btn-small').forEach(button => {
        button.addEventListener('click', function() {
            addQuickWebsite(this.textContent.trim());
        });
    });
    
    // Refresh notifications manually
    document.getElementById('refreshNotifications')?.addEventListener('click', refreshNotifications);
    
    // Uninstall all clients button
    document.getElementById('uninstallAllClients')?.addEventListener('click', handleUninstallAllClients);
    
    // Cleanup old data button
    document.getElementById('cleanupOldData')?.addEventListener('click', handleCleanupOldData);
}

function loadInitialData() {
    // Load notifications
    refreshNotifications();
    
    // Initialize database if needed
    initializeDatabase();
    
    // Load preset messages
    loadPresetMessages();
    
    // Load incomplete notification banners
    loadIncompleteNotificationBanners();
    
    // Update UI state
    updateConnectionStatus(false);
}

async function initializeDatabase() {
    try {
        // First check if database is already initialized
        const checkResponse = await fetch(`${config.API_BASE_URL}/api/index?action=isDatabaseInitialized`, {
            method: 'GET'
        });
        
        const checkResult = await checkResponse.json();
        
        if (checkResult.success && checkResult.initialized) {
            state.dbInitialized = true;
            hideSetupSection();
            return;
        }
        
        console.log('Database not initialized, will show setup section');
    } catch (error) {
        console.log('Error checking database status, will show setup section');
    }
}

async function handleInitializeDatabase() {
    try {
        showStatus('Initializing database...', 'info');
        
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'initializeDatabase'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            state.dbInitialized = true;
            showStatus('Database initialized successfully!', 'success');
            hideSetupSection();
        } else {
            showStatus(`Database initialization failed: ${result.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Database initialization error:', error);
        showStatus('Database initialization failed. Please check console for details.', 'error');
    }
}

async function refreshNotifications() {
    try {
        updateConnectionStatus(true);
        
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'getActiveNotifications'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const responseText = await response.text();
        console.log('Raw API response:', responseText);
        
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            console.error('Response text:', responseText);
            throw new Error('Invalid JSON response from API: ' + responseText.substring(0, 100));
        }
        
        if (result.success) {
            state.notifications = result.notifications || result.data || [];
            state.clientCount = result.clientCount || 0;
            state.lastRefresh = new Date();
            
            updateNotificationsList();
            updateConnectionStatus(true);
        } else {
            throw new Error(result.message || result.error || 'Failed to fetch notifications');
        }
    } catch (error) {
        console.error('Error refreshing notifications:', error);
        updateConnectionStatus(false);
        displayNotificationsError(error.message);
    }
}

function updateNotificationsList() {
    const notificationsList = document.getElementById('activeNotificationsList');
    if (!notificationsList) return;
    
    // Clear existing content
    notificationsList.innerHTML = '';
    
    if (state.notifications.length === 0) {
        notificationsList.innerHTML = '<div class="no-notifications">No active notifications</div>';
        return;
    }
    
    // Group notifications by type
    const regularNotifications = state.notifications.filter(n => n.type !== 'website_request' && n.type !== 'uninstall_request');
    const websiteRequests = state.notifications.filter(n => n.type === 'website_request');
    const uninstallRequests = state.notifications.filter(n => n.type === 'uninstall_request');
    
    // Render uninstall requests first
    uninstallRequests.forEach(notification => {
        notificationsList.appendChild(createUninstallRequestElement(notification));
    });
    
    // Render website requests
    websiteRequests.forEach(notification => {
        notificationsList.appendChild(createWebsiteRequestElement(notification));
    });
    
    // Render regular notifications
    regularNotifications.forEach((notification, index) => {
        notificationsList.appendChild(createNotificationElement(notification, index + 1));
    });
}

function createNotificationElement(notification, index) {
    const div = document.createElement('div');
    div.className = 'notification-item';
    div.dataset.notificationId = notification._id || notification.id;
    
    div.innerHTML = `
        <div class="notification-header">
            <div class="notification-number">#${index}</div>
        </div>
        <div class="notification-message">${escapeHtml(notification.message)}</div>
        <div class="notification-meta">
            <div class="notification-client">
                <strong>Client:</strong> ${escapeHtml(notification.clientId || 'Unknown')}
            </div>
            <div class="notification-time">
                <strong>Sent:</strong> ${formatTimestamp(notification.timestamp)}
            </div>
        </div>
        <div class="notification-status ${notification.status || 'pending'}">
            Status: ${(notification.status || 'pending').toUpperCase()}
            ${notification.snoozeUntil ? `(Snoozed until ${formatTimestamp(notification.snoozeUntil)})` : ''}
        </div>
        <div class="notification-actions">
            <button class="btn-small btn-warning" onclick="acknowledgeNotification('${notification._id || notification.id}')">
                Complete
            </button>
            <button class="btn-small" onclick="snoozeNotification('${notification._id || notification.id}')">
                Snooze
            </button>
        </div>
    `;
    
    return div;
}

function createWebsiteRequestElement(request) {
    const div = document.createElement('div');
    div.className = 'notification-item website-request';
    div.dataset.notificationId = request._id || request.id;
    
    div.innerHTML = `
        <div class="notification-header">
            <div class="notification-number">WEBSITE REQUEST</div>
        </div>
        <div class="notification-message">Website Access Request</div>
        <div class="website-request-details">
            <div class="website-url"><strong>URL:</strong> ${escapeHtml(request.websiteUrl || request.url)}</div>
            <div class="website-reason"><strong>Reason:</strong> ${escapeHtml(request.reason || 'No reason provided')}</div>
        </div>
        <div class="notification-meta">
            <div class="notification-client">
                <strong>Client:</strong> ${escapeHtml(request.clientId || 'Unknown')}
            </div>
            <div class="notification-time">
                <strong>Requested:</strong> ${formatTimestamp(request.timestamp)}
            </div>
        </div>
        <div class="website-request-actions">
            <button class="btn-small btn-approve" onclick="approveWebsiteRequest('${request._id || request.id}')">
                Approve
            </button>
            <button class="btn-small btn-deny" onclick="denyWebsiteRequest('${request._id || request.id}')">
                Deny
            </button>
        </div>
    `;
    
    return div;
}

function createUninstallRequestElement(request) {
    const div = document.createElement('div');
    div.className = 'notification-item priority-urgent';
    div.dataset.notificationId = request._id || request.id;
    
    div.innerHTML = `
        <div class="notification-header">
            <div class="notification-number">UNINSTALL REQUEST</div>
        </div>
        <div class="notification-message">Client Uninstall Request</div>
        <div class="uninstall-request-details">
            <div><strong>Reason:</strong> ${escapeHtml(request.reason || 'No reason provided')}</div>
            <div><strong>Explanation:</strong> ${escapeHtml(request.explanation || 'No explanation provided')}</div>
        </div>
        <div class="notification-meta">
            <div class="notification-client">
                <strong>Client:</strong> ${escapeHtml(request.clientId || 'Unknown')}
            </div>
            <div class="notification-time">
                <strong>Requested:</strong> ${formatTimestamp(request.timestamp)}
            </div>
        </div>
        <div class="notification-actions">
            <button class="btn-small btn-approve" onclick="approveUninstallRequest('${request._id || request.id}')">
                Approve
            </button>
            <button class="btn-small btn-deny" onclick="denyUninstallRequest('${request._id || request.id}')">
                Deny
            </button>
        </div>
    `;
    
    return div;
}

function displayNotificationsError(errorMessage) {
    const notificationsList = document.getElementById('activeNotificationsList');
    if (!notificationsList) return;
    
    notificationsList.innerHTML = `
        <div class="error-state">
            <div class="error-icon">⚠️</div>
            <div>Failed to load notifications</div>
            <div style="font-size: 14pt; margin-top: 0.5rem;">${escapeHtml(errorMessage)}</div>
            <button class="btn-small" onclick="refreshNotifications()">Retry</button>
        </div>
    `;
}

async function handleSendNotification(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const notificationData = {
        action: 'sendNotification',
        
        message: formData.get('message'),
        workMode: formData.get('workMode'),
        browserUsage: formData.get('browserUsage'),
        allowedWebsites: formData.get('allowedWebsites')?.split('\n').filter(url => url.trim()),
        snoozeMinutes: parseInt(formData.get('snoozeMinutes')) || 0
    };
    
    try {
        showStatus('Sending notification...', 'info');
        
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(notificationData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(`Notification sent successfully to ${result.clientCount || 0} client(s)!`, 'success');
            form.reset();
            updateWorkModeDescription(); // Reset descriptions
            updateBrowserUsageDescription();
            refreshNotifications();
        } else {
            showStatus(`Failed to send notification: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error sending notification:', error);
        showStatus('Failed to send notification. Please check console for details.', 'error');
    }
}

async function acknowledgeNotification(notificationId) {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'acknowledgeNotification',
                
                notificationId: notificationId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Notification marked as complete!', 'success');
            refreshNotifications();
        } else {
            showStatus(`Failed to complete notification: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error acknowledging notification:', error);
        showStatus('Failed to complete notification.', 'error');
    }
}

async function snoozeNotification(notificationId) {
    const minutes = prompt('Snooze for how many minutes?', '15');
    if (!minutes || isNaN(minutes)) return;
    
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'snoozeNotification',
                
                notificationId: notificationId,
                minutes: parseInt(minutes)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(`Notification snoozed for ${minutes} minutes!`, 'success');
            refreshNotifications();
        } else {
            showStatus(`Failed to snooze notification: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error snoozing notification:', error);
        showStatus('Failed to snooze notification.', 'error');
    }
}

async function approveWebsiteRequest(requestId) {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'approveWebsiteRequest',
                
                requestId: requestId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Website access approved!', 'success');
            refreshNotifications();
        } else {
            showStatus(`Failed to approve website request: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error approving website request:', error);
        showStatus('Failed to approve website request.', 'error');
    }
}

async function denyWebsiteRequest(requestId) {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'denyWebsiteRequest',
                
                requestId: requestId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Website access denied!', 'success');
            refreshNotifications();
        } else {
            showStatus(`Failed to deny website request: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error denying website request:', error);
        showStatus('Failed to deny website request.', 'error');
    }
}

async function approveUninstallRequest(requestId) {
    if (!confirm('Are you sure you want to approve this uninstall request? This will permanently remove the client from the user\'s computer.')) {
        return;
    }
    
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'approveUninstallRequest',
                
                requestId: requestId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Uninstall request approved!', 'success');
            refreshNotifications();
        } else {
            showStatus(`Failed to approve uninstall request: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error approving uninstall request:', error);
        showStatus('Failed to approve uninstall request.', 'error');
    }
}

async function denyUninstallRequest(requestId) {
    const reason = prompt('Why are you denying this uninstall request?', 'Request denied by administrator');
    if (!reason) return;
    
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'denyUninstallRequest',
                
                requestId: requestId,
                reason: reason
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Uninstall request denied!', 'success');
            refreshNotifications();
        } else {
            showStatus(`Failed to deny uninstall request: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error denying uninstall request:', error);
        showStatus('Failed to deny uninstall request.', 'error');
    }
}

async function handleUninstallAllClients() {
    if (!confirm('Are you sure you want to uninstall ALL clients? This action cannot be undone and will remove the software from all connected computers.')) {
        return;
    }
    
    const reason = prompt('Please provide a reason for uninstalling all clients:', 'Administrative action');
    if (!reason) return;
    
    try {
        showStatus('Uninstalling all clients...', 'info');
        
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'uninstallAllClients',
                
                reason: reason
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(`Uninstall command sent to ${result.clientCount || 0} client(s)!`, 'success');
            refreshNotifications();
        } else {
            showStatus(`Failed to uninstall clients: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error uninstalling all clients:', error);
        showStatus('Failed to uninstall clients.', 'error');
    }
}

function addQuickMessage(message) {
    const messageInput = document.getElementById('message');
    if (messageInput) {
        messageInput.value = message;
    }
}

function addQuickWebsite(website) {
    const websitesTextarea = document.getElementById('allowedWebsites');
    if (websitesTextarea) {
        const currentValue = websitesTextarea.value.trim();
        const newValue = currentValue ? currentValue + '\n' + website : website;
        websitesTextarea.value = newValue;
        updateWebsiteCount();
    }
}

function updateWorkModeDescription() {
    const workModeRadios = document.querySelectorAll('input[name="workMode"]');
    const descriptionElement = document.querySelector('.work-mode-description');
    
    if (!descriptionElement) return;
    
    const selectedMode = Array.from(workModeRadios).find(radio => radio.checked)?.value;
    
    let description = '';
    switch (selectedMode) {
        case 'work':
            description = 'Work mode will block distracting websites and applications to help maintain focus.';
            break;
        case 'break':
            description = 'Break mode allows relaxed internet usage with fewer restrictions.';
            break;
        case 'normal':
        default:
            description = 'Normal mode applies standard internet usage policies.';
            break;
    }
    
    descriptionElement.textContent = description;
}

function updateBrowserUsageDescription() {
    const browserRadios = document.querySelectorAll('input[name="browserUsage"]');
    const descriptionElement = document.querySelector('.browser-usage-description');
    
    if (!descriptionElement) return;
    
    const selectedUsage = Array.from(browserRadios).find(radio => radio.checked)?.value;
    
    let description = '';
    switch (selectedUsage) {
        case 'allowed':
            description = 'Browser access is permitted with website filtering applied.';
            break;
        case 'blocked':
            description = 'All browser access is completely blocked.';
            break;
        case 'restricted':
            description = 'Browser access is limited to specifically approved websites only.';
            break;
        default:
            description = 'Browser usage policy will be applied based on current settings.';
            break;
    }
    
    descriptionElement.textContent = description;
}

function updateWebsiteCount() {
    const websitesTextarea = document.getElementById('allowedWebsites');
    const countElement = document.querySelector('#websiteCount .count-display');
    
    if (!websitesTextarea || !countElement) return;
    
    const websites = websitesTextarea.value.split('\n').filter(url => url.trim()).length;
    
    if (websites === 0) {
        countElement.textContent = '0 websites will be allowed';
        countElement.className = 'count-display warning';
    } else {
        countElement.textContent = `${websites} website(s) will be allowed`;
        countElement.className = 'count-display success';
    }
}

function startRefreshTimer() {
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
    }
    
    state.refreshInterval = setInterval(() => {
        refreshNotifications();
    }, state.refreshIntervalSetting * 1000);
    
    startCountdown();
}

function startCountdown() {
    let timeLeft = state.refreshIntervalSetting;
    
    const updateCountdown = () => {
        const countdownElement = document.getElementById('refreshCountdown');
        if (countdownElement) {
            if (timeLeft <= 0) {
                countdownElement.textContent = 'Refreshing...';
                timeLeft = state.refreshIntervalSetting;
            } else {
                countdownElement.textContent = `Next refresh: ${timeLeft}s`;
                timeLeft--;
            }
        }
    };
    
    // Update immediately
    updateCountdown();
    
    // Update every second
    setInterval(updateCountdown, config.REFRESH_COUNTDOWN_UPDATE);
}

function updateConnectionStatus(isConnected) {
    state.isConnected = isConnected;
    
    const statusDot = document.getElementById('connectionStatus');
    if (statusDot) {
        statusDot.className = `status-dot ${isConnected ? 'online' : 'offline'}`;
    }
    
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
    }
    
    const clientCountElement = document.getElementById('clientCount');
    if (clientCountElement) {
        clientCountElement.textContent = `${state.clientCount} client(s)`;
    }
}

function hideSetupSection() {
    const setupSection = document.querySelector('.setup-section');
    if (setupSection) {
        setupSection.style.opacity = '0';
        setupSection.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            setupSection.style.display = 'none';
        }, 500);
    }
}

function showStatus(message, type = 'info') {
    // Remove existing status messages
    document.querySelectorAll('.status-message').forEach(el => el.remove());
    
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    
    // Add to main panel content
    const mainPanelContent = document.querySelector('.main-panel-content');
    if (mainPanelContent) {
        mainPanelContent.insertBefore(statusDiv, mainPanelContent.firstChild);
        
        // Auto-hide after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.remove();
            }, 5000);
        }
    }
}

async function loadPresetMessages() {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/config?type=preset-messages`);
        const result = await response.json();
        
        if (result.success && result.data && result.data.presetMessages) {
            const presetMessages = result.data.presetMessages;
            const presetSelect = document.getElementById('presetSelect');
            
            if (presetSelect) {
                // Clear existing options
                presetSelect.innerHTML = '<option value="">Select a preset message...</option>';
                
                // Add preset message options
                presetMessages.forEach(preset => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify(preset);
                    option.textContent = preset.text;
                    option.title = preset.description || '';
                    presetSelect.appendChild(option);
                });
                
                // Add change event listener
                presetSelect.addEventListener('change', function() {
                    if (this.value) {
                        const preset = JSON.parse(this.value);
                        
                        // Set custom message
                        const customText = document.getElementById('customText');
                        if (customText) {
                            customText.value = preset.text;
                        }
                        
                        // Set browser usage checkbox
                        const allowBrowserUsage = document.getElementById('allowBrowserUsage');
                        if (allowBrowserUsage) {
                            allowBrowserUsage.checked = preset.allowBrowserUsage || false;
                        }
                        
                        // Set allowed websites and clear first
                        const allowedWebsites = document.getElementById('allowedWebsites');
                        if (allowedWebsites) {
                            if (preset.allowedWebsites && preset.allowedWebsites.length > 0) {
                                allowedWebsites.value = preset.allowedWebsites.join('\n');
                            } else {
                                allowedWebsites.value = '';
                            }
                            updateWebsiteCount();
                        }
                        
                        // Update UI visibility based on browser usage
                        toggleBrowserUsageUI();
                        
                        // Switch to custom message mode to show the message
                        const customMessageRadio = document.getElementById('customMessage');
                        if (customMessageRadio) {
                            customMessageRadio.checked = true;
                            toggleMessageType();
                        }
                    } else {
                        // Reset form when no preset selected
                        const customText = document.getElementById('customText');
                        if (customText) customText.value = '';
                        
                        const allowBrowserUsage = document.getElementById('allowBrowserUsage');
                        if (allowBrowserUsage) allowBrowserUsage.checked = false;
                        
                        const allowedWebsites = document.getElementById('allowedWebsites');
                        if (allowedWebsites) {
                            allowedWebsites.value = '';
                            updateWebsiteCount();
                        }
                        
                        toggleBrowserUsageUI();
                    }
                });
            }
        }
    } catch (error) {
        console.error('Failed to load preset messages:', error);
        // Fallback to basic options
        const presetSelect = document.getElementById('presetSelect');
        if (presetSelect) {
            presetSelect.innerHTML = `
                <option value="">Select a preset message...</option>
                <option value='{"text":"Do your schoolwork","allowBrowserUsage":true,"allowedWebsites":["drive.google.com","*.aop.com"]}'>Do your schoolwork</option>
                <option value='{"text":"Clean the kitchen","allowBrowserUsage":false,"allowedWebsites":[]}'>Clean the kitchen</option>
                <option value='{"text":"Take a shower","allowBrowserUsage":false,"allowedWebsites":[]}'>Take a shower</option>
            `;
        }
    }
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    try {
        const date = new Date(timestamp);
        return date.toLocaleString();
    } catch (error) {
        return 'Invalid date';
    }
}

// Export functions for global access (for onclick handlers)
window.acknowledgeNotification = acknowledgeNotification;
window.snoozeNotification = snoozeNotification;
window.approveWebsiteRequest = approveWebsiteRequest;
window.denyWebsiteRequest = denyWebsiteRequest;
window.approveUninstallRequest = approveUninstallRequest;
window.denyUninstallRequest = denyUninstallRequest;
window.refreshNotifications = refreshNotifications;

// Helper functions for preset message handling
function toggleMessageType() {
    const customMessageRadio = document.getElementById('customMessage');
    const quickMessageRadio = document.getElementById('quickMessage');
    const customMessageSection = document.querySelector('.custom-message-section');
    const quickMessageSection = document.querySelector('.quick-message-section');
    
    if (customMessageRadio && customMessageRadio.checked) {
        if (customMessageSection) customMessageSection.style.display = 'block';
        if (quickMessageSection) quickMessageSection.style.display = 'none';
    } else if (quickMessageRadio && quickMessageRadio.checked) {
        if (customMessageSection) customMessageSection.style.display = 'none';
        if (quickMessageSection) quickMessageSection.style.display = 'block';
    }
}

function toggleBrowserUsageOptions() {
    const allowBrowserUsage = document.getElementById('allowBrowserUsage');
    const browserOptionsSection = document.querySelector('.browser-options-section');
    
    if (browserOptionsSection) {
        if (allowBrowserUsage && allowBrowserUsage.checked) {
            browserOptionsSection.style.display = 'block';
        } else {
            browserOptionsSection.style.display = 'none';
        }
    }
}

function toggleBrowserUsageUI() {
    const allowBrowserUsage = document.getElementById('allowBrowserUsage');
    const browserUsageWarning = document.getElementById('browserUsageWarning');
    const websitesGroup = document.getElementById('websitesGroup');
    
    const isChecked = allowBrowserUsage && allowBrowserUsage.checked;
    
    // Show/hide browser usage warning
    if (browserUsageWarning) {
        if (isChecked) {
            browserUsageWarning.classList.remove('hidden');
        } else {
            browserUsageWarning.classList.add('hidden');
        }
    }
    
    // Show/hide websites group
    if (websitesGroup) {
        if (isChecked) {
            websitesGroup.classList.remove('hidden');
        } else {
            websitesGroup.classList.add('hidden');
        }
    }
}

// Save Custom Message functionality
async function saveCustomMessage() {
    // Get current form values
    const messageText = getCurrentMessageText();
    const allowBrowserUsage = document.getElementById('allowBrowserUsage')?.checked || false;
    const allowedWebsites = document.getElementById('allowedWebsites')?.value
        .split('\n')
        .map(site => site.trim())
        .filter(site => site.length > 0) || [];
    const saveMessageName = document.getElementById('saveMessageName')?.value?.trim();
    
    // Validate that there's a message to save
    if (!messageText) {
        alert('Please enter a message before saving.');
        return;
    }
    
    // Use the provided name or generate a simple description
    const description = saveMessageName || `Custom: ${messageText.substring(0, 50)}${messageText.length > 50 ? '...' : ''}`;
    
    // Prepare the data to send
    const messageData = {
        action: 'saveCustomMessage',
        text: messageText,
        description: description,
        allowBrowserUsage: allowBrowserUsage,
        allowedWebsites: allowedWebsites
    };
    
    try {
        // Disable the save button while saving
        const saveButton = document.getElementById('saveCustomMessage');
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.textContent = 'Saving...';
        }
        
        // Send request to save custom message
        const response = await fetch(`${config.API_BASE_URL}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(messageData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Custom message saved successfully!', 'success');
            
            // Clear the save message name input
            const saveMessageNameInput = document.getElementById('saveMessageName');
            if (saveMessageNameInput) {
                saveMessageNameInput.value = '';
            }
            
            // Reload the preset messages to include the new custom message
            await loadPresetMessages();
        } else {
            showStatus(`Failed to save custom message: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error saving custom message:', error);
        showStatus('Error saving custom message. Please try again.', 'error');
    } finally {
        // Re-enable the save button
        const saveButton = document.getElementById('saveCustomMessage');
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.textContent = 'Save Preset';
        }
    }
}

// Helper function to get current message text from active input
function getCurrentMessageText() {
    const presetSelect = document.getElementById('presetSelect');
    const customText = document.getElementById('customText');
    
    // If a preset is selected, use its text
    if (presetSelect?.value) {
        try {
            const preset = JSON.parse(presetSelect.value);
            return preset.text;
        } catch (e) {
            console.warn('Failed to parse preset value:', e);
        }
    }
    
    // Otherwise use custom text
    return customText?.value?.trim() || '';
}

// addWebsite function removed - quick add buttons no longer present

// Cleanup old data functionality
async function handleCleanupOldData() {
    if (!confirm('Are you sure you want to cleanup old data? This will permanently remove old notifications and website requests.')) {
        return;
    }
    
    try {
        showStatus('Cleaning up old data...', 'info');
        
        const response = await fetch(`${config.API_BASE_URL}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'cleanupOldData'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(result.message, 'success');
            
            // Refresh notifications to show updated list
            await refreshNotifications();
            
            // Reload incomplete notification banners
            await loadIncompleteNotificationBanners();
        } else {
            showStatus(`Cleanup failed: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error during cleanup:', error);
        showStatus('Cleanup failed. Please try again.', 'error');
    }
}

// Load and display incomplete notification banners
async function loadIncompleteNotificationBanners() {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/config?type=incomplete-notifications`);
        const result = await response.json();
        
        if (result.success && result.data && result.data.incompleteNotifications) {
            displayIncompleteNotificationBanners(result.data.incompleteNotifications);
        } else {
            // Clear banners if no incomplete notifications
            const bannersContainer = document.getElementById('incompleteNotificationsBanner');
            if (bannersContainer) {
                bannersContainer.innerHTML = '';
            }
        }
    } catch (error) {
        console.error('Error loading incomplete notification banners:', error);
    }
}

// Display incomplete notification banners
function displayIncompleteNotificationBanners(incompleteNotifications) {
    const bannersContainer = document.getElementById('incompleteNotificationsBanner');
    if (!bannersContainer) return;
    
    // Clear existing banners
    bannersContainer.innerHTML = '';
    
    if (incompleteNotifications.length === 0) {
        return;
    }
    
    // Create banner for each incomplete notification
    incompleteNotifications.forEach(notification => {
        const bannerDiv = document.createElement('div');
        bannerDiv.className = 'incomplete-notification-banner';
        bannerDiv.dataset.notificationId = notification._id;
        
        const timeSinceRemoved = getTimeSinceRemoved(notification.removedAt);
        
        bannerDiv.innerHTML = `
            <div class="banner-content">
                <div class="banner-icon">⏰</div>
                <div class="banner-message">
                    <strong>Incomplete Task Removed:</strong> "${escapeHtml(notification.message)}"
                </div>
                <div class="banner-details">
                    <span>Client: ${escapeHtml(notification.clientId || 'Unknown')}</span>
                    <span>Removed: ${timeSinceRemoved}</span>
                    <span>Reason: ${escapeHtml(notification.reason)}</span>
                </div>
            </div>
            <button class="banner-dismiss" onclick="dismissIncompleteNotification('${notification._id}')">
                ✕
            </button>
        `;
        
        bannersContainer.appendChild(bannerDiv);
    });
}

// Dismiss an incomplete notification banner
async function dismissIncompleteNotification(notificationId) {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'dismissIncompleteNotification',
                notificationId: notificationId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Remove the banner from the UI
            const banner = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (banner) {
                banner.remove();
            }
            
            // Check if there are no more banners
            const bannersContainer = document.getElementById('incompleteNotificationsBanner');
            if (bannersContainer && bannersContainer.children.length === 0) {
                bannersContainer.innerHTML = '';
            }
        } else {
            showStatus(`Failed to dismiss banner: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error dismissing incomplete notification:', error);
        showStatus('Failed to dismiss banner.', 'error');
    }
}

// Helper function to get time since removed
function getTimeSinceRemoved(removedAt) {
    if (!removedAt) return 'Unknown';
    
    try {
        const now = new Date();
        const removed = new Date(removedAt);
        const diffMs = now - removed;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (diffHours > 24) {
            const diffDays = Math.floor(diffHours / 24);
            return `${diffDays} day(s) ago`;
        } else if (diffHours > 0) {
            return `${diffHours} hour(s) ago`;
        } else {
            return `${diffMins} minute(s) ago`;
        }
    } catch (error) {
        return 'Unknown';
    }
}

// Export for global access
window.dismissIncompleteNotification = dismissIncompleteNotification;

// Add website count listener
document.addEventListener('DOMContentLoaded', function() {
    const websitesTextarea = document.getElementById('allowedWebsites');
    if (websitesTextarea) {
        websitesTextarea.addEventListener('input', updateWebsiteCount);
        updateWebsiteCount(); // Initial count
    }
    
    // Add save custom message listener
    const saveCustomMessageBtn = document.getElementById('saveCustomMessage');
    if (saveCustomMessageBtn) {
        saveCustomMessageBtn.addEventListener('click', saveCustomMessage);
    }
    
    // Initialize descriptions
    updateWorkModeDescription();
    updateBrowserUsageDescription();
    
    // Add message type toggle listeners
    const messageTypeRadios = document.querySelectorAll('input[name="messageType"]');
    messageTypeRadios.forEach(radio => {
        radio.addEventListener('change', toggleMessageType);
    });
    
    // Add browser usage toggle listener
    const allowBrowserUsage = document.getElementById('allowBrowserUsage');
    if (allowBrowserUsage) {
        allowBrowserUsage.addEventListener('change', toggleBrowserUsageUI);
    }
    
    // Initialize toggle states
    toggleMessageType();
    toggleBrowserUsageUI();
});
