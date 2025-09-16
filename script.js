// PushNotifications Web Interface JavaScript

// Global state management
const state = {
    notifications: [],
    isConnected: false,
    lastRefresh: null,
    refreshInterval: null,
    clientMonitorInterval: null,
    connectionHealthInterval: null,
    dbInitialized: false,
    clientCount: 0,
    registeredClients: [],
    refreshIntervalSetting: 30, // 30 seconds for page refresh
    clientMonitorSetting: 30, // 30 seconds for client monitoring
    connectionHealthSetting: 45, // 45 seconds for connection health
    currentUser: null,
    currentSection: 'notifications',
    backgroundProcessesActive: false
};

// Configuration
const config = {
    API_BASE_URL: window.location.origin,
    REFRESH_COUNTDOWN_UPDATE: 1000, // 1 second
};

// Authentication helper functions
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function setCookie(name, value, options = {}) {
    let cookieString = `${name}=${value}`;
    
    if (options.path) {
        cookieString += `; path=${options.path}`;
    }
    
    if (options.expires) {
        cookieString += `; expires=${options.expires.toUTCString()}`;
    }
    
    if (options.sameSite) {
        cookieString += `; SameSite=${options.sameSite}`;
    }
    
    document.cookie = cookieString;
}

function getSessionToken() {
    // Try cookie first, then localStorage as fallback
    return getCookie('sessionToken') || localStorage.getItem('sessionToken');
}

function setSessionToken(token) {
    // Set as session cookie (expires when browser closes)
    setCookie('sessionToken', token, { path: '/', sameSite: 'Strict' });
    // Also store in localStorage as backup
    localStorage.setItem('sessionToken', token);
}

function clearSessionToken() {
    // Clear cookie
    document.cookie = 'sessionToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    // Clear localStorage
    localStorage.removeItem('sessionToken');
    localStorage.removeItem('authToken');
    sessionStorage.removeItem('sessionId');
}

function isLoggedIn() {
    return !!getSessionToken();
}

// API helper function with authentication
async function apiCall(action, data = {}, useAuth = true) {
    const headers = { 'Content-Type': 'application/json' };
    
    if (useAuth && isLoggedIn()) {
        headers['Authorization'] = `Bearer ${getSessionToken()}`;
    }
    
    const response = await fetch(`${config.API_BASE_URL}/api/index`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ action, ...data })
    });
    
    const result = await response.json();
    
    // Handle session expiration
    if (!result.success && result.message && 
        (result.message.includes('session') || result.message.includes('expired'))) {
        clearSessionToken();
        window.location.href = 'index.html';
        return null;
    }
    
    return result;
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing PushNotifications interface...');
    
    // Check if we're on the login page
    if (window.location.pathname.endsWith('index.html') || 
        window.location.pathname.endsWith('/')) {
        initializeLogin();
        return;
    }
    
    // Check if we're on the user download page
    if (window.location.pathname.endsWith('user-download.html')) {
        initializeUserDownload();
        return;
    }
    
    // Check if we're on any admin page
    const adminPages = ['admin.html', 'data-management.html', 'client-admin.html', 'account-admin.html', 'version-history.html'];
    const isAdminPage = adminPages.some(page => window.location.pathname.endsWith(page));
    
    if (isAdminPage) {
        initializeAdmin();
        return;
    }
    
    console.log('PushNotifications interface initialized');
});

// Login page initialization
function initializeLogin() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

// User download page initialization
function initializeUserDownload() {
    // Validate user session
    validateUserSession();
    
    // Setup event listeners for user download page
    setupUserDownloadEventListeners();
    
    // Load user installation key
    loadUserInstallationKey();
}

// Admin panel initialization
function initializeAdmin() {
    // Validate admin session
    validateAdminSession();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadInitialData();
    
    // Setup refresh timer and background processes
    startRefreshTimer();
    startBackgroundProcesses();
    
    // Setup admin panel
    setupAdminPanel();
    
    // If this is the standalone account-admin page, load dropdowns directly
    if (window.location.pathname.endsWith('account-admin.html')) {
        console.log('Standalone account-admin page detected, loading user dropdowns');
        // Add a small delay to ensure DOM is fully loaded
        setTimeout(() => {
            loadUsersIntoDropdowns();
        }, 500);
    }
    
    // If this is the standalone version-history page, load version history directly
    if (window.location.pathname.endsWith('version-history.html')) {
        console.log('Standalone version-history page detected, loading version history');
        // Add a small delay to ensure DOM is fully loaded
        setTimeout(() => {
            loadVersionHistory();
        }, 500);
    }
    
    // If this is the standalone client-admin page, load client administration data
    if (window.location.pathname.endsWith('client-admin.html')) {
        console.log('Standalone client-admin page detected, loading client administration data');
        // Add a small delay to ensure DOM is fully loaded
        setTimeout(() => {
            initializeClientAdministration();
            // Also load version information for download buttons
            loadAndUpdateVersion();
        }, 500);
    }
}

// Session validation
async function validateUserSession() {
    try {
        const result = await apiCall('validateSession');
        
        if (!result || !result.success) {
            window.location.href = 'index.html';
            return;
        }
        
        state.currentUser = result.user;
        updateUserInfo(result.user);
        
    } catch (error) {
        console.error('Session validation error:', error);
        window.location.href = 'index.html';
    }
}

async function validateAdminSession() {
    try {
        const result = await apiCall('validateSession');
        
        if (!result || !result.success || result.user.role !== 'admin') {
            window.location.href = 'index.html';
            return;
        }
        
        state.currentUser = result.user;
        updateAdminUserInfo(result.user);
        
    } catch (error) {
        console.error('Admin session validation error:', error);
        window.location.href = 'index.html';
    }
}

// Login handling
async function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const username = formData.get('username');
    const password = formData.get('password');
    
    try {
        showStatus('Logging in...', 'info');
        
        const result = await apiCall('login', { username, password }, false);
        
        if (result && result.success) {
            setSessionToken(result.sessionToken);
            
            // Redirect based on role
            if (result.user.role === 'admin') {
                window.location.href = 'admin.html';
            } else {
                window.location.href = 'user-download.html';
            }
        } else {
            showStatus(result ? result.message : 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showStatus('Login failed. Please try again.', 'error');
    }
}

// Logout handling
async function handleLogout() {
    try {
        // Stop background processes before logging out
        stopBackgroundProcesses();
        
        await apiCall('logout');
        clearSessionToken();
        window.location.href = 'index.html';
    } catch (error) {
        console.error('Logout error:', error);
        
        // Stop background processes even if logout fails
        stopBackgroundProcesses();
        
        clearSessionToken();
        window.location.href = 'index.html';
    }
}

function updateAdminUserInfo(user) {
    const adminUsername = document.getElementById('adminUsername');
    if (adminUsername && user) {
        adminUsername.textContent = `Admin: ${user.username}`;
    }
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
    
    // Security management tabs
    const clientInfoTab = document.getElementById('clientInfoTab');
    const securityKeysTab = document.getElementById('securityKeysTab');
    if (clientInfoTab) {
        clientInfoTab.addEventListener('click', () => switchSecurityTab('clientInfo'));
    }
    if (securityKeysTab) {
        securityKeysTab.addEventListener('click', () => switchSecurityTab('securityKeys'));
    }
    
    // Security management refresh buttons
    const refreshClientsBtn = document.getElementById('refreshClients');
    const refreshSecurityKeysBtn = document.getElementById('refreshSecurityKeys');
    if (refreshClientsBtn) {
        refreshClientsBtn.addEventListener('click', loadClientInfo);
    }
    if (refreshSecurityKeysBtn) {
        refreshSecurityKeysBtn.addEventListener('click', loadSecurityKeys);
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
    
    // Clear all notifications button
    document.getElementById('clearAllNotifications')?.addEventListener('click', handleClearAllNotifications);
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
    
    // Load registered clients immediately for dropdown
    loadRegisteredClientsBackground();
    
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
            
            // Also refresh client dropdown data to keep it up-to-date
            loadRegisteredClientsBackground();
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

async function handleSendNotification() {
    // Get form elements
    const targetClientSelect = document.getElementById('targetClientSelect');
    const messageTypeRadios = document.querySelectorAll('input[name="messageType"]');
    const presetSelect = document.getElementById('presetSelect');
    const customText = document.getElementById('customText');
    const allowBrowserUsage = document.getElementById('allowBrowserUsage');
    const allowedWebsites = document.getElementById('allowedWebsites');
    
    // Get selected message type
    const messageType = Array.from(messageTypeRadios).find(radio => radio.checked)?.value;
    
    // Get message text
    let message = '';
    if (messageType === 'preset') {
        const selectedPreset = presetSelect.value;
        if (!selectedPreset) {
            showStatus('Please select a preset message', 'error');
            return;
        }
        message = presetSelect.options[presetSelect.selectedIndex].text;
    } else if (messageType === 'custom') {
        message = customText.value.trim();
        if (!message) {
            showStatus('Please enter a custom message', 'error');
            return;
        }
    } else {
        showStatus('Please select a message type', 'error');
        return;
    }
    
    // Get target client
    const targetClient = targetClientSelect.value;
    
    // Get website settings
    const browserUsageEnabled = allowBrowserUsage.checked;
    let websiteList = [];
    if (browserUsageEnabled && allowedWebsites.value.trim()) {
        websiteList = allowedWebsites.value
            .split('\n')
            .map(url => url.trim())
            .filter(url => url.length > 0);
    }
    
    const notificationData = {
        action: 'sendNotification',
        targetClient: targetClient,
        message: message,
        messageType: messageType,
        browserUsageEnabled: browserUsageEnabled,
        allowedWebsites: websiteList
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
            
            // Reset form elements
            const messageTypeRadios = document.querySelectorAll('input[name="messageType"]');
            const customText = document.getElementById('customText');
            const allowBrowserUsage = document.getElementById('allowBrowserUsage');
            const allowedWebsites = document.getElementById('allowedWebsites');
            const presetSelect = document.getElementById('presetSelect');
            
            if (presetSelect) presetSelect.value = '';
            if (customText) customText.value = '';
            if (allowBrowserUsage) allowBrowserUsage.checked = false;
            if (allowedWebsites) allowedWebsites.value = '';
            
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
    showConfirmationModal({
        title: 'Snooze Notification',
        message: 'How many minutes would you like to snooze this notification?',
        confirmText: 'Snooze',
        cancelText: 'Cancel',
        inputType: 'text',
        inputLabel: 'Minutes:',
        inputPlaceholder: 'Enter number of minutes',
        inputValue: '15',
        onConfirm: async (minutes) => {
            if (!minutes || isNaN(minutes) || minutes <= 0) {
                showStatus('Please enter a valid number of minutes', 'error');
                return;
            }
            
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
    });
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
    showConfirmationModal({
        title: 'Approve Uninstall Request',
        message: 'Are you sure you want to approve this uninstall request? This will permanently remove the client from the user\'s computer.',
        confirmText: 'Approve',
        cancelText: 'Cancel',
        dangerMode: true,
        onConfirm: async () => {
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
    });
}

async function denyUninstallRequest(requestId) {
    showConfirmationModal({
        title: 'Deny Uninstall Request',
        message: 'Why are you denying this uninstall request?',
        confirmText: 'Deny Request',
        cancelText: 'Cancel',
        inputType: 'text',
        inputLabel: 'Reason:',
        inputPlaceholder: 'Enter reason for denial',
        inputValue: 'Request denied by administrator',
        dangerMode: true,
        onConfirm: async (reason) => {
            if (!reason) {
                showStatus('A reason is required to deny the request', 'error');
                return;
            }
            
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
    });
}

async function handleUninstallAllClients() {
    showConfirmationModal({
        title: 'Uninstall All Clients',
        message: 'Are you sure you want to uninstall ALL clients? This action cannot be undone and will remove the software from all connected computers.',
        confirmText: 'Continue',
        cancelText: 'Cancel',
        dangerMode: true,
        onConfirm: () => {
            // Show second modal for reason input
            showConfirmationModal({
                title: 'Provide Reason',
                message: 'Please provide a reason for uninstalling all clients:',
                confirmText: 'Uninstall All',
                cancelText: 'Cancel',
                inputType: 'text',
                inputLabel: 'Reason:',
                inputPlaceholder: 'Administrative action',
                inputValue: 'Administrative action',
                dangerMode: true,
                onConfirm: async (reason) => {
                    if (!reason) {
                        showStatus('A reason is required to proceed', 'error');
                        return;
                    }
                    
                    try {
                        showStatus('Uninstalling all clients...', 'info');
                        
                        const result = await apiCall('uninstallAllClients', {
                            reason: reason
                        });
                        
                        if (result && result.success) {
                            showStatus(`Uninstall command sent to ${result.clientCount || 0} client(s)!`, 'success');
                            refreshNotifications();
                        } else {
                            const errorMessage = result ? (result.message || result.error) : 'Unknown error';
                            showStatus(`Failed to uninstall clients: ${errorMessage}`, 'error');
                        }
                    } catch (error) {
                        console.error('Error uninstalling all clients:', error);
                        showStatus('Failed to uninstall clients.', 'error');
                    }
                }
            });
        }
    });
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

// Start background processes for continuous monitoring
function startBackgroundProcesses() {
    if (state.backgroundProcessesActive) {
        console.log('Background processes already running');
        return;
    }
    
    console.log('Starting background processes...');
    state.backgroundProcessesActive = true;
    
    // Start client monitoring
    startClientMonitoring();
    
    // Start connection health monitoring
    startConnectionHealthMonitoring();
}

function stopBackgroundProcesses() {
    console.log('Stopping background processes...');
    
    if (state.clientMonitorInterval) {
        clearInterval(state.clientMonitorInterval);
        state.clientMonitorInterval = null;
    }
    
    if (state.connectionHealthInterval) {
        clearInterval(state.connectionHealthInterval);
        state.connectionHealthInterval = null;
    }
    
    state.backgroundProcessesActive = false;
}

// Client monitoring - updates sidebar and maintains client status
function startClientMonitoring() {
    if (state.clientMonitorInterval) {
        clearInterval(state.clientMonitorInterval);
    }
    
    state.clientMonitorInterval = setInterval(async () => {
        try {
            // Load registered clients for sidebar on all pages
            await loadRegisteredClientsBackground();
            
            // Update client status in global state
            await updateGlobalClientStatus();
        } catch (error) {
            console.error('Error in client monitoring:', error);
        }
    }, state.clientMonitorSetting * 1000);
    
    console.log(`Client monitoring started (${state.clientMonitorSetting}s interval)`);
}

// Connection health monitoring - ensures database connectivity
function startConnectionHealthMonitoring() {
    if (state.connectionHealthInterval) {
        clearInterval(state.connectionHealthInterval);
    }
    
    state.connectionHealthInterval = setInterval(async () => {
        try {
            await performConnectionHealthCheck();
        } catch (error) {
            console.error('Error in connection health monitoring:', error);
        }
    }, state.connectionHealthSetting * 1000);
    
    console.log(`Connection health monitoring started (${state.connectionHealthSetting}s interval)`);
}

// Populate main notification form client dropdown
function populateTargetClientDropdown(clients) {
    console.log('🎯 populateTargetClientDropdown called with:', clients.length, 'clients');
    const targetClientSelect = document.getElementById('targetClientSelect');
    if (!targetClientSelect) {
        console.warn('❌ targetClientSelect element not found');
        return;
    }
    
    console.log('🔧 Clearing existing options in dropdown');
    // Clear existing options
    targetClientSelect.innerHTML = '';
    
    console.log('➕ Adding default option');
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Send to all clients';
    targetClientSelect.appendChild(defaultOption);
    
    // Show all registered clients regardless of online status
    const registeredClients = clients.filter(client => 
        client.macAddress && client.clientName
    );
    
    if (registeredClients.length === 0) {
        const noClientsOption = document.createElement('option');
        noClientsOption.value = '';
        noClientsOption.textContent = 'No registered clients available';
        noClientsOption.disabled = true;
        targetClientSelect.appendChild(noClientsOption);
        return;
    }
    
    // Add each registered client as an option
    registeredClients.forEach(client => {
        const option = document.createElement('option');
        // Use activeClientId if available, otherwise use a fallback ID based on MAC
        option.value = client.activeClientId || `mac_${client.macAddress.replace(/[:-]/g, '')}`;
        
        // Show online status in the dropdown text
        const isOnline = client.activeClientId && isRecentCheckin(client.lastCheckin);
        const statusIcon = isOnline ? '🟢' : '⚫';
        const statusText = isOnline ? 'Online' : 'Offline';
        
        // Format: ClientName (username) - MAC [Status]
        option.textContent = `${statusIcon} ${client.clientName} (${client.username}) - ${client.macAddress} [${statusText}]`;
        targetClientSelect.appendChild(option);
    });
    
    console.log(`Populated targetClientSelect with ${registeredClients.length} registered clients`);
}

// Background client loading (silent, no status messages)
async function loadRegisteredClientsBackground() {
    try {
        console.log('🔍 Calling getAllMacClients API...');
        const result = await apiCall('getAllMacClients');
        console.log('📋 getAllMacClients API response:', result);
        
        if (result && result.success) {
            state.registeredClients = result.data || [];
            console.log('📊 Total registered clients found:', state.registeredClients.length);
            if (state.registeredClients.length > 0) {
                console.log('🔍 First client sample:', state.registeredClients[0]);
            }
            
            displayRegisteredClientsList(state.registeredClients);
            
            // Also populate the main notification form dropdown
            populateTargetClientDropdown(state.registeredClients);
        } else {
            console.error('❌ getAllMacClients failed:', result);
        }
    } catch (error) {
        console.error('Background client loading error:', error);
    }
}

// Update global client status and count
async function updateGlobalClientStatus() {
    try {
        const result = await apiCall('getActiveNotifications');
        
        if (result && result.success) {
            const newClientCount = result.clientCount || 0;
            
            // Update client count if it changed
            if (state.clientCount !== newClientCount) {
                state.clientCount = newClientCount;
                
                // Update UI elements that show client count
                const clientCountElement = document.getElementById('clientCount');
                if (clientCountElement) {
                    clientCountElement.textContent = `${state.clientCount} client(s)`;
                }
            }
        }
    } catch (error) {
        console.error('Global client status update error:', error);
    }
}

// Perform connection health check
async function performConnectionHealthCheck() {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index?action=healthCheck`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${getSessionToken()}`
            }
        });
        
        const isHealthy = response.ok;
        
        // Update connection status if it changed
        if (state.isConnected !== isHealthy) {
            updateConnectionStatus(isHealthy);
            
            if (!isHealthy) {
                console.warn('Database connection health check failed');
            } else {
                console.log('Database connection restored');
            }
        }
    } catch (error) {
        console.error('Connection health check error:', error);
        updateConnectionStatus(false);
    }
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

function showStatus(message, type = 'info', duration = null) {
    // Remove existing status messages
    document.querySelectorAll('.status-message').forEach(el => el.remove());
    
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${type}`;
    
    // Check if message contains HTML
    if (message.includes('<')) {
        statusDiv.innerHTML = message;
    } else {
        statusDiv.textContent = message;
    }
    
    // Add to main panel content or body if no main panel
    let container = document.querySelector('.main-panel-content') || document.querySelector('.user-content') || document.body;
    
    if (container) {
        container.insertBefore(statusDiv, container.firstChild);
        
        // Auto-hide based on duration or type
        let hideDelay = duration;
        if (hideDelay === null) {
            if (type === 'success') {
                hideDelay = 5000;
            } else if (type === 'info') {
                hideDelay = 3000;
            }
            // Error messages don't auto-hide by default
        }
        
        if (hideDelay && hideDelay > 0) {
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.remove();
                }
            }, hideDelay);
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
                        
                        // Update quick-add buttons
                        updateQuickAddButtons();
                        
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
                        
                        // Update quick-add buttons
                        updateQuickAddButtons();
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
    
    // Update quick-add buttons
    updateQuickAddButtons();
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

// Clear all notifications functionality
async function handleClearAllNotifications() {
    // Show confirmation modal
    showConfirmationModal({
        title: 'Clear All Notifications',
        message: 'Are you sure you want to clear ALL active notifications? This action cannot be undone and will permanently remove all currently active notifications from the system.',
        confirmText: 'Clear All Notifications',
        cancelText: 'Cancel',
        dangerMode: true,
        onConfirm: async () => {
            try {
                showStatus('Clearing all notifications...', 'info');
                
                const result = await apiCall('clearAllNotifications');
                
                if (result && result.success) {
                    showStatus('All notifications cleared successfully!', 'success');
                    
                    // Refresh notifications to show updated list
                    await refreshNotifications();
                } else {
                    showStatus(result ? result.message : 'Failed to clear notifications', 'error');
                }
            } catch (error) {
                console.error('Error clearing all notifications:', error);
                showStatus('Failed to clear notifications. Please try again.', 'error');
            }
        }
    });
}

// Cleanup old data functionality
async function handleCleanupOldData() {
    const confirmMessage = `Are you sure you want to cleanup old data? This will permanently remove:

• Active notifications older than 48 hours
• Regular notifications older than 7 days
• Website requests older than 7 days

This will PRESERVE:
• All encryption keys and passwords
• All user accounts
• App deletion/uninstall requests
• Custom messages
• Unacknowledged completion notifications
• All recent data (within the time limits above)

This action cannot be undone.`;
    
    if (!confirm(confirmMessage)) {
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

// Update quick-add website buttons visibility and functionality
async function updateQuickAddButtons() {
    console.log('updateQuickAddButtons called');
    const quickAddContainer = document.getElementById('quickAddWebsites');
    const allowBrowserUsage = document.getElementById('allowBrowserUsage');
    
    console.log('Elements found:', {
        quickAddContainer: !!quickAddContainer,
        allowBrowserUsage: !!allowBrowserUsage
    });
    
    if (!quickAddContainer) {
        console.warn('quickAddWebsites container not found');
        return;
    }
    
    // Show quick-add buttons when browser usage is enabled
    const showQuickAdd = allowBrowserUsage && allowBrowserUsage.checked;
    
    console.log('Current state:', {
        browserUsageChecked: allowBrowserUsage?.checked,
        showQuickAdd: showQuickAdd
    });
    
    if (showQuickAdd) {
        quickAddContainer.classList.remove('hidden');
        console.log('Removed hidden class from quick-add container');
        
        // Load website button groups if not already loaded
        if (!quickAddContainer.hasAttribute('data-loaded')) {
            console.log('Loading quick-add website buttons');
            await loadQuickAddWebsiteButtons();
            quickAddContainer.setAttribute('data-loaded', 'true');
        } else {
            console.log('Quick-add buttons already loaded');
        }
    } else {
        quickAddContainer.classList.add('hidden');
        console.log('Added hidden class to quick-add container');
    }
}

// Load quick-add website buttons from config
async function loadQuickAddWebsiteButtons() {
    console.log('loadQuickAddWebsiteButtons called');
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/config?type=preset-messages`);
        const result = await response.json();
        
        console.log('API response:', result);
        
        if (result.success && result.data && result.data.presetMessages) {
            const schoolworkPreset = result.data.presetMessages.find(p => p.text === 'Do your schoolwork');
            console.log('Schoolwork preset found:', schoolworkPreset);
            
            if (schoolworkPreset && schoolworkPreset.websiteButtons) {
                console.log('Website buttons found:', schoolworkPreset.websiteButtons);
                const buttonsContainer = document.querySelector('#quickAddWebsites .button-group');
                console.log('Buttons container found:', !!buttonsContainer);
                
                if (buttonsContainer) {
                    buttonsContainer.innerHTML = '';
                    
                    schoolworkPreset.websiteButtons.forEach(buttonGroup => {
                        console.log('Creating button for:', buttonGroup.name);
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.className = 'btn-small';
                        button.textContent = buttonGroup.name;
                        button.onclick = () => addWebsiteGroup(buttonGroup.websites);
                        buttonsContainer.appendChild(button);
                    });
                    
                    console.log('Added', schoolworkPreset.websiteButtons.length, 'buttons to container');
                } else {
                    console.warn('Buttons container not found: #quickAddWebsites .button-group');
                }
            } else {
                console.log('No websiteButtons found in schoolwork preset');
            }
        } else {
            console.log('Invalid API response structure');
        }
    } catch (error) {
        console.error('Failed to load quick-add website buttons:', error);
    }
}

// Add a group of websites to the allowed websites textarea
function addWebsiteGroup(websites) {
    const allowedWebsitesTextarea = document.getElementById('allowedWebsites');
    if (!allowedWebsitesTextarea || !websites || !Array.isArray(websites)) return;
    
    const currentWebsites = allowedWebsitesTextarea.value.trim();
    const newWebsites = websites.join('\n');
    
    if (currentWebsites) {
        allowedWebsitesTextarea.value = currentWebsites + '\n' + newWebsites;
    } else {
        allowedWebsitesTextarea.value = newWebsites;
    }
    
    updateWebsiteCount();
}

// Export for global access
window.dismissIncompleteNotification = dismissIncompleteNotification;

// Add website count listener
document.addEventListener('DOMContentLoaded', function() {
    // Hide modal on page load to prevent it from showing inappropriately
    hideModalOnLoad();
    
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
    
    // Add account administration listeners
    const createNewUserBtn = document.getElementById('createNewUser');
    if (createNewUserBtn) {
        createNewUserBtn.addEventListener('click', showCreateUserModal);
    }
    
    const resetUserPasswordBtn = document.getElementById('resetUserPassword');
    if (resetUserPasswordBtn) {
        resetUserPasswordBtn.addEventListener('click', showResetPasswordModal);
    }
    
    const removeUserAccountBtn = document.getElementById('removeUserAccount');
    if (removeUserAccountBtn) {
        removeUserAccountBtn.addEventListener('click', handleRemoveUserAccount);
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
        allowBrowserUsage.addEventListener('change', function() {
            toggleBrowserUsageUI();
            updateQuickAddButtons();
        });
    }
    
    // Add preset selection listener for quick-add buttons
    const presetSelect = document.getElementById('presetSelect');
    if (presetSelect) {
        // Listen for preset changes to update quick-add buttons
        const originalListener = presetSelect.onchange;
        presetSelect.addEventListener('change', function(event) {
            // Let the original handler run first
            if (originalListener) originalListener.call(this, event);
            // Then update quick-add buttons
            setTimeout(updateQuickAddButtons, 100);
        });
    }
    
    // Initialize toggle states
    toggleMessageType();
    toggleBrowserUsageUI();
    
    // Load initial security data
    loadClientInfo();
    loadSecurityKeys();
});

// Security Management Functions
function switchSecurityTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Content`).classList.add('active');
    
    // Load data for the active tab
    if (tabName === 'clientInfo') {
        loadClientInfo();
    } else if (tabName === 'securityKeys') {
        loadSecurityKeys();
    }
}

async function loadClientInfo() {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'getAllMacClients'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayMacClientInfo(result.data || []);
            updateLastRefreshed('clientsLastRefreshed');
        } else {
            displayClientInfoError(result.message);
        }
    } catch (error) {
        console.error('Error loading MAC client info:', error);
        displayClientInfoError(error.message);
    }
}

async function loadSecurityKeys() {
    try {
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'getAllSecurityKeys'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySecurityKeys(result.data || []);
            updateLastRefreshed('keysLastRefreshed');
        } else {
            displaySecurityKeysError(result.message);
        }
    } catch (error) {
        console.error('Error loading security keys:', error);
        displaySecurityKeysError(error.message);
    }
}

function displayMacClientInfo(macClients) {
    const container = document.getElementById('clientInfoList');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (macClients.length === 0) {
        container.innerHTML = '<div class="no-data">No MAC client registrations found</div>';
        return;
    }
    
    macClients.forEach(macClient => {
        const clientDiv = document.createElement('div');
        clientDiv.className = 'data-item mac-client-info-item';
        
        const lastCheckinTime = formatTimestamp(macClient.lastCheckin);
        const createdTime = formatTimestamp(macClient.createdAt);
        const isOnline = isRecentCheckin(macClient.lastCheckin);
        const hasActiveClient = macClient.activeClientId && macClient.activeClient;
        
        // Client management buttons
        const clientActions = hasActiveClient ? `
            <div class="client-actions">
                <button class="btn-small btn-warning" onclick="deactivateMacClient('${macClient.activeClientId}')" title="Deactivate current installation">
                    Deactivate
                </button>
                <button class="btn-small" onclick="viewClientHistory('${macClient.macAddress}')" title="View installation history">
                    History
                </button>
            </div>
        ` : '';
        
        clientDiv.innerHTML = `
            <div class="data-header">
                <div class="data-title">
                    <div class="mac-address">📱 ${escapeHtml(macClient.macAddress)}</div>
                    <div class="client-name">${escapeHtml(macClient.clientName)} (${escapeHtml(macClient.username)})</div>
                </div>
                <div class="data-status ${isOnline && hasActiveClient ? 'online' : 'offline'}">
                    ${isOnline && hasActiveClient ? '🟢 Online' : '⚫ Offline'}
                </div>
            </div>
            <div class="data-details">
                <div class="detail-row">
                    <strong>Username:</strong> ${escapeHtml(macClient.username)}
                </div>
                <div class="detail-row">
                    <strong>Client Name:</strong> ${escapeHtml(macClient.clientName)}
                </div>
                <div class="detail-row">
                    <strong>Installation Count:</strong> ${macClient.installationCount}
                </div>
                <div class="detail-row">
                    <strong>Active Client ID:</strong> ${escapeHtml(macClient.activeClientId || 'None')}
                </div>
                <div class="detail-row">
                    <strong>Hostname:</strong> ${escapeHtml(macClient.hostname || 'Unknown')}
                </div>
                <div class="detail-row">
                    <strong>Platform:</strong> ${escapeHtml(macClient.platform || 'Unknown')}
                </div>
                ${hasActiveClient ? `
                    <div class="detail-row">
                        <strong>Version:</strong> ${escapeHtml(macClient.activeClient.version || 'Unknown')}
                    </div>
                    <div class="detail-row">
                        <strong>Install Path:</strong> <code>${escapeHtml(macClient.activeClient.installPath || 'Unknown')}</code>
                    </div>
                    <div class="detail-row">
                        <strong>Client Created:</strong> ${formatTimestamp(macClient.activeClient.createdAt)}
                    </div>
                    <div class="detail-row">
                        <strong>Client Last Checkin:</strong> ${formatTimestamp(macClient.activeClient.lastCheckin)}
                    </div>
                ` : '<div class="detail-row"><em>No active client installation</em></div>'}
                <div class="detail-row">
                    <strong>MAC First Registered:</strong> ${createdTime}
                </div>
                <div class="detail-row">
                    <strong>MAC Last Activity:</strong> ${lastCheckinTime}
                </div>
            </div>
            ${clientActions}
        `;
        
        container.appendChild(clientDiv);
    });
}

// Legacy function for backward compatibility
function displayClientInfo(clients) {
    return displayMacClientInfo(clients);
}

function displaySecurityKeys(keys) {
    const container = document.getElementById('securityKeysList');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (keys.length === 0) {
        container.innerHTML = '<div class="no-data">No security keys found</div>';
        return;
    }
    
    keys.forEach(key => {
        const keyDiv = document.createElement('div');
        keyDiv.className = 'data-item security-key-item';
        
        const createdTime = formatTimestamp(key.createdAt);
        const lastUsedTime = formatTimestamp(key.lastUsed);
        const isRecentlyUsed = isRecentUsage(key.lastUsed);
        
        keyDiv.innerHTML = `
            <div class="data-header">
                <div class="data-title">${escapeHtml(key.keyType)}</div>
                <div class="data-status ${isRecentlyUsed ? 'active' : 'inactive'}">
                    ${isRecentlyUsed ? '🔄 Active' : '⏸️ Inactive'}
                </div>
            </div>
            <div class="data-details">
                <div class="detail-row">
                    <strong>Client ID:</strong> ${escapeHtml(key.clientId)}
                </div>
                <div class="detail-row">
                    <strong>Hostname:</strong> ${escapeHtml(key.hostname || 'Unknown')}
                </div>
                <div class="detail-row">
                    <strong>Install Path:</strong> <code>${escapeHtml(key.installPath || 'Unknown')}</code>
                </div>
                <div class="detail-row">
                    <strong>Created:</strong> ${createdTime}
                </div>
                <div class="detail-row">
                    <strong>Last Used:</strong> ${lastUsedTime}
                </div>
                <div class="security-note">
                    🔐 <em>Key values are never displayed for security reasons</em>
                </div>
            </div>
        `;
        
        container.appendChild(keyDiv);
    });
}

function displayClientInfoError(message) {
    const container = document.getElementById('clientInfoList');
    if (!container) return;
    
    container.innerHTML = `
        <div class="error-state">
            <div class="error-icon">⚠️</div>
            <div>Failed to load client information</div>
            <div style="font-size: 14pt; margin-top: 0.5rem;">${escapeHtml(message)}</div>
            <button class="btn-small" onclick="loadClientInfo()">Retry</button>
        </div>
    `;
}

function displaySecurityKeysError(message) {
    const container = document.getElementById('securityKeysList');
    if (!container) return;
    
    container.innerHTML = `
        <div class="error-state">
            <div class="error-icon">⚠️</div>
            <div>Failed to load security keys</div>
            <div style="font-size: 14pt; margin-top: 0.5rem;">${escapeHtml(message)}</div>
            <button class="btn-small" onclick="loadSecurityKeys()">Retry</button>
        </div>
    `;
}

function updateLastRefreshed(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = `Last refreshed: ${new Date().toLocaleTimeString()}`;
    }
}

function isRecentCheckin(lastCheckin) {
    if (!lastCheckin) return false;
    
    try {
        const checkinTime = new Date(lastCheckin);
        const now = new Date();
        const diffMinutes = (now - checkinTime) / (1000 * 60);
        return diffMinutes < 2; // Consider online if checked in within last 2 minutes (client heartbeats every 30s)
    } catch (error) {
        return false;
    }
}

function isRecentUsage(lastUsed) {
    if (!lastUsed) return false;
    
    try {
        const usedTime = new Date(lastUsed);
        const now = new Date();
        const diffHours = (now - usedTime) / (1000 * 60 * 60);
        return diffHours < 24; // Consider active if used within last 24 hours
    } catch (error) {
        return false;
    }
}

// MAC Client Management Functions
async function deactivateMacClient(clientId) {
    if (!confirm('Are you sure you want to deactivate this client installation? The user will need to restart the client to continue receiving notifications.')) {
        return;
    }
    
    const reason = prompt('Reason for deactivation:', 'Manual deactivation by administrator');
    if (!reason) return;
    
    try {
        showStatus('Deactivating client...', 'info');
        
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'deactivateClient',
                clientId: clientId,
                reason: reason
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Client deactivated successfully!', 'success');
            loadClientInfo(); // Refresh the client list
        } else {
            showStatus(`Failed to deactivate client: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error deactivating client:', error);
        showStatus('Failed to deactivate client.', 'error');
    }
}

async function viewClientHistory(macAddress) {
    try {
        showStatus('Loading client history...', 'info');
        
        const response = await fetch(`${config.API_BASE_URL}/api/index`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'getClientHistory',
                macAddress: macAddress
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayClientHistoryModal(result.data || [], macAddress);
        } else {
            showStatus(`Failed to load client history: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error loading client history:', error);
        showStatus('Failed to load client history.', 'error');
    }
}

function displayClientHistoryModal(history, macAddress) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    
    // Create modal content
    const modal = document.createElement('div');
    modal.className = 'modal-content';
    
    let historyHTML = `
        <div class="modal-header">
            <h3>Client Installation History</h3>
            <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
            <div class="mac-address">📱 ${escapeHtml(macAddress)}</div>
        </div>
    `;
    
    if (history.length === 0) {
        historyHTML += '<div class="no-data">No installation history found</div>';
    } else {
        historyHTML += '<div class="history-list">';
        
        history.forEach(record => {
            const isActive = record.isActive;
            const createdTime = formatTimestamp(record.createdAt);
            const lastCheckinTime = formatTimestamp(record.lastCheckin);
            const deactivatedTime = record.deactivatedAt ? formatTimestamp(record.deactivatedAt) : null;
            
            historyHTML += `
                <div class="history-item ${isActive ? 'active' : 'inactive'}">
                    <div class="history-header">
                        <div class="history-title">${escapeHtml(record.clientName)} (${escapeHtml(record.username)})</div>
                        <div class="history-status ${isActive ? 'online' : 'offline'}">
                            ${isActive ? '🟢 Active' : '⚫ Inactive'}
                        </div>
                    </div>
                    <div class="history-details">
                        <div class="detail-row">
                            <strong>Client ID:</strong> ${escapeHtml(record.clientId)}
                        </div>
                        <div class="detail-row">
                            <strong>Hostname:</strong> ${escapeHtml(record.hostname || 'Unknown')}
                        </div>
                        <div class="detail-row">
                            <strong>Platform:</strong> ${escapeHtml(record.platform || 'Unknown')}
                        </div>
                        <div class="detail-row">
                            <strong>Version:</strong> ${escapeHtml(record.version || 'Unknown')}
                        </div>
                        <div class="detail-row">
                            <strong>Install Path:</strong> <code>${escapeHtml(record.installPath || 'Unknown')}</code>
                        </div>
                        <div class="detail-row">
                            <strong>Created:</strong> ${createdTime}
                        </div>
                        <div class="detail-row">
                            <strong>Last Checkin:</strong> ${lastCheckinTime}
                        </div>
                        ${!isActive && deactivatedTime ? `
                            <div class="detail-row">
                                <strong>Deactivated:</strong> ${deactivatedTime}
                            </div>
                            <div class="detail-row">
                                <strong>Deactivation Reason:</strong> ${escapeHtml(record.deactivationReason || 'Unknown')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        
        historyHTML += '</div>';
    }
    
    historyHTML += `
        <div class="modal-footer">
            <button class="btn-small" onclick="this.closest('.modal-overlay').remove()">Close</button>
        </div>
    `;
    
    modal.innerHTML = historyHTML;
    overlay.appendChild(modal);
    
    // Close on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    });
    
    // Add to page
    document.body.appendChild(overlay);
    
    showStatus('Client history loaded', 'success');
}

// User Download Page Functions
function updateUserInfo(user) {
    const usernameElement = document.getElementById('currentUsername');
    if (usernameElement && user) {
        usernameElement.textContent = user.username;
    }
}

function setupUserDownloadEventListeners() {
    // Download client button (now generates key and downloads)
    const downloadButton = document.getElementById('downloadClient');
    if (downloadButton) {
        downloadButton.addEventListener('click', handleDownloadClient);
    }
    
    // Logout button
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
}

async function loadUserInstallationKey() {
    // No longer needed since we generate keys per download
    // Just ensure the UI is set up for download
    const downloadSection = document.getElementById('downloadSection');
    if (downloadSection) {
        downloadSection.style.display = 'block';
    }
    
    // Load and update the version information
    await loadAndUpdateVersion();
}

async function handleDownloadClient() {
    const downloadButton = document.getElementById('downloadClient');
    const keySection = document.getElementById('installationKeySection');
    const keyDisplay = document.getElementById('installationKeyDisplay');
    const copyKeyButton = document.getElementById('copyInstallationKey');
    
    if (!downloadButton) return;
    
    // Disable button and show loading
    downloadButton.disabled = true;
    downloadButton.textContent = 'Generating Download Key...';
    
    try {
        showStatus('Generating installation key...', 'info');
        
        // Generate download key
        const result = await apiCall('generateDownloadKey');
        
        if (result && result.success) {
            const installationKey = result.installationKey;
            
            // Show the key section
            if (keySection) {
                keySection.style.display = 'block';
            }
            
            // Display the key
            if (keyDisplay) {
                keyDisplay.textContent = installationKey;
            }
            
            // Setup copy button
            if (copyKeyButton) {
                copyKeyButton.onclick = () => copyToClipboard(installationKey);
            }
            
            // Update button for download
            downloadButton.textContent = 'Download Client Now';
            downloadButton.disabled = false;
            
            // Change button action to actual download
            downloadButton.onclick = () => {
                // Initiate download
                const downloadUrl = `${config.API_BASE_URL}/api/download?file=client`;
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = 'installer.py';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Show instructions
                showDownloadInstructions(installationKey);
            };
            
            showStatus('Installation key generated! Click "Download Client Now" to download.', 'success');
            
        } else {
            throw new Error(result ? result.message : 'Failed to generate download key');
        }
    } catch (error) {
        console.error('Download key generation error:', error);
        showStatus('Failed to generate download key: ' + error.message, 'error');
        
        // Reset button
        downloadButton.disabled = false;
        downloadButton.textContent = 'Download Client';
    }
}

function showDownloadInstructions(installationKey) {
    const instructions = `
        <div class="download-instructions">
            <h3>Download Started</h3>
            <p>Your client download has started. Please follow these steps:</p>
            <ol>
                <li>Save the downloaded file to your desired location</li>
                <li>Run the installer</li>
                <li>Use this installation key when prompted: <strong>${installationKey}</strong></li>
            </ol>
            <p><strong>Note:</strong> This installation key will expire in 24 hours.</p>
        </div>
    `;
    
    showStatus(instructions, 'info', 15000); // Show for 15 seconds
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showStatus('Installation key copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showStatus('Failed to copy to clipboard', 'error');
        
        // Fallback - select the text
        const keyDisplay = document.getElementById('installationKeyDisplay');
        if (keyDisplay) {
            keyDisplay.select();
        }
    }
}

// Function to load and update version information on download buttons
async function loadAndUpdateVersion() {
    console.log('🔍 loadAndUpdateVersion called - checking for version elements...');
    
    // Check if version elements exist before making API call
    const versionTextElements = document.querySelectorAll('.version-text');
    const versionBadges = document.querySelectorAll('.version-badge');
    console.log(`Found ${versionTextElements.length} version text elements and ${versionBadges.length} version badges`);
    
    if (versionTextElements.length === 0 && versionBadges.length === 0) {
        console.warn('⚠️ No version elements found on this page, skipping version update');
        return;
    }
    
    try {
        console.log('📡 Making API call to get_version...');
        const result = await apiCall('get_version', {}, false); // No auth required for version check
        console.log('📡 get_version API response:', result);
        
        if (result && result.success && result.currentVersion) {
            const currentVersion = result.currentVersion;
            console.log('✅ Loaded current version:', currentVersion);
            
            // Update all download buttons with version text
            versionTextElements.forEach((element, index) => {
                const oldText = element.textContent;
                element.textContent = `v${currentVersion}`;
                console.log(`📝 Updated version element ${index + 1}: "${oldText}" → "v${currentVersion}"`);
            });
            
            // Update version badges if they exist
            versionBadges.forEach((badge, index) => {
                const oldText = badge.textContent;
                badge.textContent = `Current Version: ${currentVersion}`;
                console.log(`📝 Updated version badge ${index + 1}: "${oldText}" → "Current Version: ${currentVersion}"`);
            });
            
            console.log(`✅ Successfully updated ${versionTextElements.length} version text elements and ${versionBadges.length} version badges`);
        } else {
            console.warn('⚠️ Failed to load version info from API:', result);
            console.log('🔄 Falling back to default version v2.1.0');
            
            // Fall back to a default version if API call fails
            versionTextElements.forEach((element, index) => {
                const oldText = element.textContent;
                element.textContent = 'v2.1.0';
                console.log(`📝 Fallback update ${index + 1}: "${oldText}" → "v2.1.0"`);
            });
        }
    } catch (error) {
        console.error('❌ Error loading version information:', error);
        console.log('🔄 Falling back to default version v2.1.0 due to error');
        
        // Fall back to existing version on error
        versionTextElements.forEach((element, index) => {
            const oldText = element.textContent;
            element.textContent = 'v2.1.0';
            console.log(`📝 Error fallback ${index + 1}: "${oldText}" → "v2.1.0"`);
        });
    }
}

// Admin Panel Functions
function setupAdminPanel() {
    // Setup admin menu navigation
    const adminMenuButtons = document.querySelectorAll('.admin-menu button');
    adminMenuButtons.forEach(button => {
        button.addEventListener('click', () => {
            const section = button.dataset.section;
            if (section) {
                switchAdminSection(section);
            }
        });
    });
    
    // Setup admin functionality buttons
    setupAdminButtonListeners();
    
    // Load registered clients for sidebar
    loadRegisteredClients();
}

function setupAdminButtonListeners() {
    // User management buttons
    document.getElementById('viewAllUsers')?.addEventListener('click', loadAllUsers);
    document.getElementById('createNewUser')?.addEventListener('click', showCreateUserModal);
    document.getElementById('exportUserData')?.addEventListener('click', exportUserData);
    
    // Client administration buttons
    document.getElementById('viewAllClients')?.addEventListener('click', loadAllClients);
    document.getElementById('deactivateAllClients')?.addEventListener('click', deactivateAllClients);
    document.getElementById('exportClientData')?.addEventListener('click', exportClientData);
    document.getElementById('uninstallSpecificClient')?.addEventListener('click', handleUninstallSpecificClientModal);
    
    // Download client button (available on client administration pages)
    document.getElementById('downloadClient')?.addEventListener('click', handleDownloadClient);
    
    // Data management buttons
    document.getElementById('backupDatabase')?.addEventListener('click', backupDatabase);
    document.getElementById('cleanupOldData')?.addEventListener('click', handleCleanupOldData);
    document.getElementById('exportNotifications')?.addEventListener('click', exportNotifications);
    document.getElementById('removeOldActiveNotifications')?.addEventListener('click', handleRemoveOldActiveNotifications);
    document.getElementById('cleanOldNotifications')?.addEventListener('click', handleCleanOldNotifications);
    document.getElementById('clearOldWebsiteRequests')?.addEventListener('click', handleClearOldWebsiteRequests);
    
    // Version history button
    document.getElementById('refreshVersionHistory')?.addEventListener('click', loadVersionHistory);
    
    // Logout button
    document.getElementById('adminLogoutButton')?.addEventListener('click', handleLogout);
}

function switchAdminSection(sectionName) {
    // Update active menu item
    document.querySelectorAll('.admin-menu button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`)?.classList.add('active');
    
    // Update visible section
    document.querySelectorAll('.admin-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionName)?.classList.add('active');
    
    // Update state
    state.currentSection = sectionName;
    
    // Background processes (refresh timer, client monitoring, connection health) 
    // continue running seamlessly during section switches - no restart needed
    console.log(`Switched to ${sectionName} section - background processes continue running`);
    
    // Load section-specific data
    switch (sectionName) {
        case 'notifications':
            refreshNotifications();
            break;
        case 'data-management':
            // Load data management info
            break;
        case 'client-administration':
            loadAllClients();
            break;
        case 'account-administration':
            loadAllUsers();
            loadUsersIntoDropdowns();
            break;
        case 'version-history':
            loadVersionHistory();
            break;
    }
}

async function loadAllUsers() {
    try {
        showStatus('Loading users...', 'info');
        
        const result = await apiCall('getAllUsers');
        
        if (result && result.success) {
            displayUsersTable(result.data);
            showStatus('Users loaded successfully', 'success');
        } else {
            showStatus(result ? result.message : 'Failed to load users', 'error');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showStatus('Failed to load users.', 'error');
    }
}

function displayUsersTable(users) {
    const container = document.getElementById('usersTableContainer');
    if (!container) return;
    
    if (users.length === 0) {
        container.innerHTML = '<div class="no-data">No users found</div>';
        return;
    }
    
    let tableHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Created</th>
                    <th>Last Login</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    users.forEach(user => {
        tableHTML += `
            <tr>
                <td>${escapeHtml(user.username)}</td>
                <td>${escapeHtml(user.email)}</td>
                <td><span class="role-badge role-${user.role}">${user.role}</span></td>
                <td>${formatTimestamp(user.createdAt)}</td>
                <td>${user.lastLogin ? formatTimestamp(user.lastLogin) : 'Never'}</td>
                <td><span class="status-badge ${user.isActive ? 'active' : 'inactive'}">${user.isActive ? 'Active' : 'Inactive'}</span></td>
                <td>
                    <button class="btn-small" onclick="editUser('${user.id}')">Edit</button>
                    ${user.isActive ? 
                        `<button class="btn-small btn-warning" onclick="deactivateUser('${user.id}')">Deactivate</button>` : 
                        `<button class="btn-small btn-success" onclick="activateUser('${user.id}')">Activate</button>`
                    }
                </td>
            </tr>
        `;
    });
    
    tableHTML += '</tbody></table>';
    container.innerHTML = tableHTML;
}

async function loadAllClients() {
    try {
        showStatus('Loading clients...', 'info');
        
        const result = await apiCall('getAllMacClients');
        
        if (result && result.success) {
            displayClientsTable(result.data);
            showStatus('Clients loaded successfully', 'success');
        } else {
            showStatus(result ? result.message : 'Failed to load clients', 'error');
        }
    } catch (error) {
        console.error('Error loading clients:', error);
        showStatus('Failed to load clients.', 'error');
    }
}

function displayClientsTable(clients) {
    const container = document.getElementById('clientsTableContainer');
    if (!container) return;
    
    if (clients.length === 0) {
        container.innerHTML = '<div class="no-data">No clients found</div>';
        return;
    }
    
    let tableHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>MAC Address</th>
                    <th>Username</th>
                    <th>Client Name</th>
                    <th>Platform</th>
                    <th>Version</th>
                    <th>Last Checkin</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    clients.forEach(client => {
        // Determine client status based on activeClient availability and isActive status
        const hasActiveClient = client.activeClient && client.activeClient.isActive;
        const isOnline = hasActiveClient && isRecentCheckin(client.lastCheckin) && client.activeClientId;
        
        // Use activeClient version if available and active, otherwise fall back to latestClient or 'Unknown'
        const version = hasActiveClient 
            ? client.activeClient.version 
            : (client.latestClient?.version || 'Unknown');
        
        // Determine appropriate status text and class
        let statusText, statusClass;
        if (hasActiveClient) {
            if (isOnline) {
                statusText = 'Online';
                statusClass = 'online';
            } else {
                statusText = 'Offline';
                statusClass = 'offline';
            }
        } else {
            statusText = 'Inactive';
            statusClass = 'inactive';
        }
        
        tableHTML += `
            <tr>
                <td><code>${escapeHtml(client.macAddress)}</code></td>
                <td>${escapeHtml(client.username)}</td>
                <td>${escapeHtml(client.clientName)}</td>
                <td>${escapeHtml(client.platform || 'Unknown')}</td>
                <td>${escapeHtml(version)}</td>
                <td>${formatTimestamp(client.lastCheckin)}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    <button class="btn-small" onclick="viewClientHistory('${client.macAddress}')">History</button>
                    ${hasActiveClient && client.activeClientId ? 
                        `<button class="btn-small btn-warning" onclick="deactivateMacClient('${client.activeClientId}')">Deactivate</button>` : 
                        ''
                    }
                </td>
            </tr>
        `;
    });
    
    tableHTML += '</tbody></table>';
    container.innerHTML = tableHTML;
}

async function loadRegisteredClients() {
    try {
        const result = await apiCall('getAllMacClients');
        
        if (result && result.success) {
            displayRegisteredClientsList(result.data);
        }
    } catch (error) {
        console.error('Error loading registered clients:', error);
    }
}

function displayRegisteredClientsList(clients) {
    const container = document.getElementById('registeredClientsList');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (clients.length === 0) {
        container.innerHTML = '<div class="no-clients">No registered clients</div>';
        return;
    }
    
    clients.forEach(client => {
        const isOnline = isRecentCheckin(client.lastCheckin) && client.activeClientId;
        
        const clientDiv = document.createElement('div');
        clientDiv.className = `client-item ${isOnline ? 'online' : 'offline'}`;
        
        clientDiv.innerHTML = `
            <div class="client-status"></div>
            <div class="client-info">
                <div class="client-name">${escapeHtml(client.clientName)}</div>
                <div class="client-details">${escapeHtml(client.username)} • ${escapeHtml(client.platform || 'Unknown')}</div>
            </div>
        `;
        
        container.appendChild(clientDiv);
    });
}

async function loadVersionHistory() {
    const container = document.getElementById('versionHistoryContainer');
    if (!container) return;
    
    // Show loading state
    container.innerHTML = '<div class="loading-state">Loading version history...</div>';
    
    try {
        const result = await apiCall('getVersionHistory');
        
        if (result && result.success && result.data) {
            displayVersionHistory(result.data, result.totalDeployments, result.lastRefreshed, result.source);
        } else {
            container.innerHTML = '<div class="error-state">Failed to load version history</div>';
        }
    } catch (error) {
        console.error('Error loading version history:', error);
        container.innerHTML = '<div class="error-state">Failed to load version history</div>';
    }
}

function displayVersionHistory(deployments, totalDeployments, lastRefreshed, source = 'unknown') {
    const container = document.getElementById('versionHistoryContainer');
    if (!container) return;
    
    let html = `
        <div class="version-history-header">
            <h4>Version History (${totalDeployments} versions)</h4>
            <p class="last-refreshed">Last refreshed: ${formatTimestamp(lastRefreshed)}</p>
        </div>
        <div class="versions-table">
            <div class="version-table-header">
                <div class="column-date">Date/Time</div>
                <div class="column-version">Version</div>
                <div class="column-message">Message</div>
            </div>
    `;
    
    if (deployments.length === 0) {
        html += '<div class="no-data">No version history found</div>';
    } else {
        deployments.forEach(version => {
            const isCurrentBadge = version.isCurrent ? ' <span class="current-badge">CURRENT</span>' : '';
            const versionDate = version.date ? formatTimestamp(version.date) : 'Unknown';
            const versionNumber = `v${escapeHtml(version.version)}${isCurrentBadge}`;
            const versionMessage = escapeHtml(version.message);
            
            html += `
                <div class="version-row ${version.isCurrent ? 'current' : ''}">
                    <div class="column-date">${versionDate}</div>
                    <div class="column-version">${versionNumber}</div>
                    <div class="column-message">${versionMessage}</div>
                </div>
            `;
        });
    }
    
    html += '</div></div>';
    container.innerHTML = html;
}


// User administration functions
function showCreateUserModal() {
    // Get the username from the input field
    const username = document.getElementById('newUsername')?.value?.trim();
    const role = document.getElementById('newUserRole')?.value || 'user';
    
    if (!username) {
        showStatus('Please enter a valid username', 'error');
        return;
    }
    
    // Show confirmation modal with role information
    const roleDisplay = role === 'admin' ? 'Administrator' : 'User';
    showConfirmationModal({
        title: 'Create New User',
        message: `Create new user with username "${username}" and role "${roleDisplay}"? A random password will be generated.`,
        confirmText: 'Create User',
        cancelText: 'Cancel',
        onConfirm: () => {
            handleCreateUser(username, role);
        }
    });
}

async function handleCreateUser(username, role) {
    try {
        showStatus('Creating new user...', 'info');
        
        // Generate a random password
        const password = generateRandomPassword();
        
        // Call the API to create user (email is optional)
        const result = await apiCall('createUser', {
            username: username,
            password: password,
            role: role || 'user' // Use provided role or default to 'user'
        });
        
        if (result && result.success) {
            // Show password in styled modal
            showPasswordModal('User Created Successfully', {
                username: username,
                password: password,
                message: 'User has been created with the following credentials:'
            });
            
            // Clear the username input field
            const usernameInput = document.getElementById('newUsername');
            if (usernameInput) {
                usernameInput.value = '';
            }
            
            // Clear any existing result display
            const resultElement = document.getElementById('createUserResult');
            if (resultElement) {
                resultElement.innerHTML = '';
            }
            
            // Refresh the user list
            loadAllUsers();
            
            // Refresh the dropdowns to include the new user
            loadUsersIntoDropdowns();
            
            // Show success notification
            showStatus('User created successfully!', 'success');
        } else {
            const errorMessage = result ? result.message : 'Failed to create user';
            showStatus(`Failed to create user: ${errorMessage}`, 'error');
            
            // Show error in the result element
            const resultElement = document.getElementById('createUserResult');
            if (resultElement) {
                resultElement.innerHTML = `<div class="error-message">${escapeHtml(errorMessage)}</div>`;
            }
        }
    } catch (error) {
        console.error('Error creating user:', error);
        showStatus('Failed to create user. Please check console for details.', 'error');
        
        // Show error in the result element
        const resultElement = document.getElementById('createUserResult');
        if (resultElement) {
            resultElement.innerHTML = `<div class="error-message">Error: ${escapeHtml(error.message)}</div>`;
        }
    }
}

// Generate a random password with at least one uppercase, lowercase, number, and special character
function generateRandomPassword() {
    const length = 12;
    const charset = {
        uppercase: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        lowercase: 'abcdefghijklmnopqrstuvwxyz',
        numbers: '0123456789',
        special: '!@#$%^&*()-_=+[{]}\\|;:,<.>/?'
    };
    
    // Ensure at least one of each character type
    let password = '';
    password += charset.uppercase.charAt(Math.floor(Math.random() * charset.uppercase.length));
    password += charset.lowercase.charAt(Math.floor(Math.random() * charset.lowercase.length));
    password += charset.numbers.charAt(Math.floor(Math.random() * charset.numbers.length));
    password += charset.special.charAt(Math.floor(Math.random() * charset.special.length));
    
    // Fill the rest of the password
    const allChars = charset.uppercase + charset.lowercase + charset.numbers + charset.special;
    for (let i = 4; i < length; i++) {
        password += allChars.charAt(Math.floor(Math.random() * allChars.length));
    }
    
    // Shuffle the password characters
    return password.split('').sort(() => 0.5 - Math.random()).join('');
}

// Load users into dropdown selects
async function loadUsersIntoDropdowns() {
    console.log('loadUsersIntoDropdowns called');
    try {
        const result = await apiCall('getAllUsers');
        console.log('getAllUsers result:', result);
        
        if (result && result.success) {
            const users = result.data;
            console.log('Users data:', users);
            
            // Update reset password dropdown
            const resetPasswordSelect = document.getElementById('resetPasswordUser');
            console.log('resetPasswordSelect element:', resetPasswordSelect);
            if (resetPasswordSelect) {
                resetPasswordSelect.innerHTML = '<option value="">Select a user...</option>';
                users.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    // Handle optional email field
                    const displayText = user.email ? `${user.username} (${user.email})` : user.username;
                    option.textContent = displayText;
                    resetPasswordSelect.appendChild(option);
                    console.log('Added user to reset dropdown:', displayText);
                });
            } else {
                console.warn('resetPasswordUser element not found');
            }
            
            // Update remove user dropdown
            const removeUserSelect = document.getElementById('removeUser');
            console.log('removeUserSelect element:', removeUserSelect);
            if (removeUserSelect) {
                removeUserSelect.innerHTML = '<option value="">Select a user...</option>';
                users.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    // Handle optional email field
                    const displayText = user.email ? `${user.username} (${user.email})` : user.username;
                    option.textContent = displayText;
                    removeUserSelect.appendChild(option);
                    console.log('Added user to remove dropdown:', displayText);
                });
            } else {
                console.warn('removeUser element not found');
            }
        } else {
            console.error('Failed to get users or no success:', result);
        }
    } catch (error) {
        console.error('Error loading users into dropdowns:', error);
    }
}

// Show reset password modal
function showResetPasswordModal() {
    const userSelect = document.getElementById('resetPasswordUser');
    const userId = userSelect?.value;
    
    if (!userId) {
        showStatus('Please select a user to reset password for', 'error');
        return;
    }
    
    const username = userSelect.options[userSelect.selectedIndex].text.split(' (')[0];
    
    // Show confirmation modal
    showConfirmationModal({
        title: 'Reset User Password',
        message: `Reset password for user "${username}"? A new random password will be generated.`,
        confirmText: 'Reset Password',
        cancelText: 'Cancel',
        onConfirm: () => {
            handleResetUserPassword(userId, username);
        }
    });
}

// Handle reset user password
async function handleResetUserPassword(userId, username) {
    try {
        showStatus('Resetting user password...', 'info');
        
        // Generate new password
        const newPassword = generateRandomPassword();
        
        // Call API to reset password (this would need to be implemented in the API)
        const result = await apiCall('resetUserPassword', {
            userId: userId,
            newPassword: newPassword
        });
        
        if (result && result.success) {
            // Show password in styled modal
            showPasswordModal('Password Reset Successfully', {
                username: username,
                password: newPassword,
                message: 'Password has been reset for the following user:'
            });
            
            // Clear any existing result display
            const resultElement = document.getElementById('resetPasswordResult');
            if (resultElement) {
                resultElement.innerHTML = '';
            }
            
            // Reset the dropdown
            const userSelect = document.getElementById('resetPasswordUser');
            if (userSelect) {
                userSelect.value = '';
            }
            
            showStatus('Password reset successfully!', 'success');
        } else {
            const errorMessage = result ? result.message : 'Failed to reset password';
            showStatus(`Failed to reset password: ${errorMessage}`, 'error');
            
            const resultElement = document.getElementById('resetPasswordResult');
            if (resultElement) {
                resultElement.innerHTML = `<div class="error-message">${escapeHtml(errorMessage)}</div>`;
            }
        }
    } catch (error) {
        console.error('Error resetting password:', error);
        showStatus('Failed to reset password. Please check console for details.', 'error');
        
        const resultElement = document.getElementById('resetPasswordResult');
        if (resultElement) {
            resultElement.innerHTML = `<div class="error-message">Error: ${escapeHtml(error.message)}</div>`;
        }
    }
}

// Handle remove user account
async function handleRemoveUserAccount() {
    const userSelect = document.getElementById('removeUser');
    const userId = userSelect?.value;
    
    if (!userId) {
        showStatus('Please select a user to delete', 'error');
        return;
    }
    
    const username = userSelect.options[userSelect.selectedIndex].text.split(' (')[0];
    
    showConfirmationModal({
        title: 'Delete User Account',
        message: `Are you sure you want to permanently delete user "${username}"? This action cannot be undone and will permanently delete the user account and all associated data.`,
        confirmText: 'Delete User',
        cancelText: 'Cancel',
        dangerMode: true,
        onConfirm: async () => {
            try {
                showStatus('Deleting user account...', 'info');
                
                // Get session token for authorization
                const token = localStorage.getItem('sessionToken') || '';
                
                // Call API to delete user
                const response = await fetch(`${config.API_BASE_URL}/api/index`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token ? { 'Authorization': 'Bearer ' + token } : {})
                    },
                    body: JSON.stringify({ action: 'deleteUser', userId })
                });
                
                const result = await response.json();
                
                if (result && result.success) {
                    showStatus('User account deleted successfully!', 'success');
                    
                    // Reset the dropdown
                    userSelect.value = '';
                    
                    // Refresh user lists
                    loadAllUsers();
                    loadUsersIntoDropdowns();
                } else {
                    const errorMessage = result ? result.message : 'Failed to delete user';
                    showStatus(`Failed to delete user: ${errorMessage}`, 'error');
                }
            } catch (error) {
                console.error('Error deleting user:', error);
                showStatus('Failed to delete user. Please check console for details.', 'error');
            }
        }
    });
}

// Edit User function - opens a modal for editing user details
function editUser(userId) {
    // Find the user in the current users data
    const usersTable = document.getElementById('usersTableContainer');
    if (!usersTable) {
        showStatus('User table not available', 'error');
        return;
    }
    
    // For now, we'll show a simple prompt-based editor
    // In a full implementation, this would be a proper modal
    showStatus('Edit user functionality - advanced modal editor would be implemented here', 'info');
}

// Deactivate User function
async function deactivateUser(userId) {
    if (!confirm('Are you sure you want to deactivate this user? They will not be able to log in until reactivated.')) {
        return;
    }
    
    const reason = prompt('Reason for deactivation:', 'Administrative deactivation');
    if (!reason) return;
    
    try {
        showStatus('Deactivating user...', 'info');
        
        const result = await apiCall('deactivateUser', {
            userId: userId,
            reason: reason
        });
        
        if (result && result.success) {
            showStatus('User deactivated successfully!', 'success');
            loadAllUsers(); // Refresh the users list
        } else {
            showStatus(`Failed to deactivate user: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error deactivating user:', error);
        showStatus('Failed to deactivate user. Please try again.', 'error');
    }
}

// Activate User function
async function activateUser(userId) {
    if (!confirm('Are you sure you want to activate this user? They will be able to log in again.')) {
        return;
    }
    
    try {
        showStatus('Activating user...', 'info');
        
        const result = await apiCall('activateUser', {
            userId: userId
        });
        
        if (result && result.success) {
            showStatus('User activated successfully!', 'success');
            loadAllUsers(); // Refresh the users list
        } else {
            showStatus(`Failed to activate user: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error activating user:', error);
        showStatus('Failed to activate user. Please try again.', 'error');
    }
}

// Deactivate All Clients function
async function deactivateAllClients() {
    if (!confirm('Are you sure you want to deactivate ALL active clients? This will disconnect all users from receiving notifications until they restart their clients.')) {
        return;
    }
    
    const reason = prompt('Reason for mass deactivation:', 'Administrative mass deactivation');
    if (!reason) return;
    
    try {
        showStatus('Deactivating all clients...', 'info');
        
        const result = await apiCall('deactivateAllClients', {
            reason: reason
        });
        
        if (result && result.success) {
            showStatus(`Successfully deactivated ${result.deactivatedCount || 0} client(s)!`, 'success');
            loadAllClients(); // Refresh the clients list
            loadRegisteredClients(); // Refresh sidebar
        } else {
            showStatus(`Failed to deactivate clients: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error deactivating all clients:', error);
        showStatus('Failed to deactivate all clients. Please try again.', 'error');
    }
}

// Export User Data function
async function exportUserData() {
    try {
        showStatus('Preparing user data export...', 'info');
        
        const result = await apiCall('exportUserData');
        
        if (result && result.success) {
            // Create and download the file
            const blob = new Blob([result.data], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `user-data-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            showStatus('User data exported successfully!', 'success');
        } else {
            showStatus(`Failed to export user data: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error exporting user data:', error);
        showStatus('Failed to export user data. Please try again.', 'error');
    }
}

// Export Client Data function
async function exportClientData() {
    try {
        showStatus('Preparing client data export...', 'info');
        
        const result = await apiCall('exportClientData');
        
        if (result && result.success) {
            // Create and download the file
            const blob = new Blob([result.data], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `client-data-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            showStatus('Client data exported successfully!', 'success');
        } else {
            showStatus(`Failed to export client data: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error exporting client data:', error);
        showStatus('Failed to export client data. Please try again.', 'error');
    }
}

// Backup Database function
async function backupDatabase() {
    if (!confirm('Create a full database backup? This may take some time depending on the amount of data.')) {
        return;
    }
    
    try {
        showStatus('Creating database backup...', 'info');
        
        const result = await apiCall('backupDatabase');
        
        if (result && result.success) {
            if (result.downloadUrl) {
                // If the API provides a download URL
                const link = document.createElement('a');
                link.href = result.downloadUrl;
                link.download = `database-backup-${new Date().toISOString().split('T')[0]}.zip`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else if (result.data) {
                // If the API provides the data directly
                const blob = new Blob([result.data], { type: 'application/octet-stream' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `database-backup-${new Date().toISOString().split('T')[0]}.zip`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }
            
            showStatus('Database backup created successfully!', 'success');
        } else {
            showStatus(`Failed to create database backup: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error creating database backup:', error);
        showStatus('Failed to create database backup. Please try again.', 'error');
    }
}

// Export Notifications function
async function exportNotifications() {
    const days = prompt('Export notifications from how many days? (Enter number of days, or "all" for complete history)', '30');
    if (!days) return;
    
    try {
        showStatus('Preparing notifications export...', 'info');
        
        const result = await apiCall('exportNotifications', {
            days: days === 'all' ? 'all' : parseInt(days)
        });
        
        if (result && result.success) {
            // Create and download the file
            const blob = new Blob([result.data], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            const fileName = days === 'all' ? 
                `notifications-export-all-${new Date().toISOString().split('T')[0]}.json` :
                `notifications-export-${days}days-${new Date().toISOString().split('T')[0]}.json`;
            link.download = fileName;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            showStatus(`Notifications exported successfully! (${result.count || 0} records)`, 'success');
        } else {
            showStatus(`Failed to export notifications: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error exporting notifications:', error);
        showStatus('Failed to export notifications. Please try again.', 'error');
    }
}

// Handle uninstall specific client
async function handleUninstallSpecificClient() {
    const clientId = prompt('Enter the Client ID to uninstall:', '');
    if (!clientId) return;
    
    if (!confirm(`Are you sure you want to uninstall the client with ID "${clientId}"? This action cannot be undone and will remove the software from that specific computer.`)) {
        return;
    }
    
    const reason = prompt('Please provide a reason for uninstalling this client:', 'Administrative uninstall');
    if (!reason) return;
    
    try {
        showStatus('Uninstalling specific client...', 'info');
        
        const result = await apiCall('uninstallSpecificClient', {
            clientId: clientId,
            reason: reason
        });
        
        if (result && result.success) {
            showStatus(`Uninstall command sent to client "${clientId}"!`, 'success');
            loadAllClients(); // Refresh client list
        } else {
            showStatus(`Failed to uninstall client: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error uninstalling specific client:', error);
        showStatus('Failed to uninstall client. Please try again.', 'error');
    }
}


// Handle remove old active notifications
async function handleRemoveOldActiveNotifications() {
    const days = prompt('Remove active notifications older than how many days?', '30');
    if (!days || isNaN(days) || days <= 0) {
        showStatus('Please enter a valid number of days', 'error');
        return;
    }
    
    if (!confirm(`Are you sure you want to remove all active notifications older than ${days} days? This action cannot be undone.`)) {
        return;
    }
    
    try {
        showStatus('Removing old active notifications...', 'info');
        
        const result = await apiCall('removeOldActiveNotifications', {
            days: parseInt(days)
        });
        
        if (result && result.success) {
            showStatus(`Successfully removed ${result.removedCount || 0} old active notifications!`, 'success');
            refreshNotifications(); // Refresh the notifications display
        } else {
            showStatus(`Failed to remove old notifications: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error removing old active notifications:', error);
        showStatus('Failed to remove old notifications. Please try again.', 'error');
    }
}

// Handle clean old notifications
async function handleCleanOldNotifications() {
    const days = prompt('Clean completed/acknowledged notifications older than how many days?', '90');
    if (!days || isNaN(days) || days <= 0) {
        showStatus('Please enter a valid number of days', 'error');
        return;
    }
    
    if (!confirm(`Are you sure you want to permanently delete all completed/acknowledged notifications older than ${days} days? This action cannot be undone.`)) {
        return;
    }
    
    try {
        showStatus('Cleaning old notifications...', 'info');
        
        const result = await apiCall('cleanOldNotifications', {
            days: parseInt(days)
        });
        
        if (result && result.success) {
            showStatus(`Successfully cleaned ${result.cleanedCount || 0} old notifications!`, 'success');
        } else {
            showStatus(`Failed to clean old notifications: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error cleaning old notifications:', error);
        showStatus('Failed to clean old notifications. Please try again.', 'error');
    }
}

// Handle clear old website requests
async function handleClearOldWebsiteRequests() {
    const days = prompt('Clear website access requests older than how many days?', '30');
    if (!days || isNaN(days) || days <= 0) {
        showStatus('Please enter a valid number of days', 'error');
        return;
    }
    
    if (!confirm(`Are you sure you want to clear all website access requests older than ${days} days? This action cannot be undone.`)) {
        return;
    }
    
    try {
        showStatus('Clearing old website requests...', 'info');
        
        const result = await apiCall('clearOldWebsiteRequests', {
            days: parseInt(days)
        });
        
        if (result && result.success) {
            showStatus(`Successfully cleared ${result.clearedCount || 0} old website requests!`, 'success');
            refreshNotifications(); // Refresh to update any website request displays
        } else {
            showStatus(`Failed to clear old website requests: ${result ? result.message : 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error clearing old website requests:', error);
        showStatus('Failed to clear old website requests. Please try again.', 'error');
    }
}

// Reusable modal function for showing passwords
function showPasswordModal(title, options) {
    const { username, password, message = 'User credentials:' } = options;
    
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    
    // Create modal content
    const modal = document.createElement('div');
    modal.className = 'password-modal';
    
    modal.innerHTML = `
        <div class="modal-header">
            <h3>${escapeHtml(title)}</h3>
            <button class="modal-close">×</button>
        </div>
        <div class="modal-body">
            <p>${escapeHtml(message)}</p>
            <div class="credentials-container">
                <div class="credential-field">
                    <label>Username:</label>
                    <div>${escapeHtml(username)}</div>
                </div>
                <div class="credential-field">
                    <label>Password:</label>
                    <div id="passwordDisplay">${escapeHtml(password)}</div>
                </div>
            </div>
            <div class="warning-message">
                ⚠️ <strong>Important:</strong> Please copy this password immediately. For security reasons, it will not be shown again.
            </div>
        </div>
        <div class="modal-footer">
            <button id="copyPasswordBtn" class="btn-copy">
                📋 Copy Password
            </button>
            <button id="closeModalBtn" class="btn-secondary">
                Close
            </button>
        </div>
    `;
    
    // Add event listeners
    const copyBtn = modal.querySelector('#copyPasswordBtn');
    const closeBtn = modal.querySelector('#closeModalBtn');
    const closeXBtn = modal.querySelector('.modal-close');
    
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(password);
            copyBtn.innerHTML = '✅ Copied!';
            copyBtn.style.background = '#198754';
            setTimeout(() => {
                copyBtn.innerHTML = '📋 Copy Password';
                copyBtn.style.background = '#28a745';
            }, 2000);
        } catch (error) {
            console.error('Failed to copy password:', error);
            copyBtn.innerHTML = '❌ Copy Failed';
            copyBtn.style.background = '#dc3545';
            setTimeout(() => {
                copyBtn.innerHTML = '📋 Copy Password';
                copyBtn.style.background = '#28a745';
            }, 2000);
        }
    });
    
    closeBtn.addEventListener('click', () => {
        overlay.remove();
    });
    
    closeXBtn.addEventListener('click', () => {
        overlay.remove();
    });
    
    // Close on overlay click (but not on modal content)
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    });
    
    // Close on Escape key
    const escapeKeyHandler = (e) => {
        if (e.key === 'Escape') {
            overlay.remove();
            document.removeEventListener('keydown', escapeKeyHandler);
        }
    };
    document.addEventListener('keydown', escapeKeyHandler);
    
    // Add to DOM
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Focus the copy button for better accessibility
    setTimeout(() => copyBtn.focus(), 100);
}

// General-purpose confirmation modal with input field
function showConfirmationModal(options) {
    const {
        title,
        message,
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        inputType = null, // 'text' for text input, 'textarea' for textarea
        inputLabel = '',
        inputPlaceholder = '',
        inputValue = '',
        onConfirm = null,
        onCancel = null,
        dangerMode = false
    } = options;

    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    
    // Create modal content
    const modal = document.createElement('div');
    modal.className = 'password-modal confirmation-modal';
    
    let inputHTML = '';
    if (inputType) {
        if (inputType === 'textarea') {
            inputHTML = `
                <div class="input-field">
                    <label>${escapeHtml(inputLabel)}</label>
                    <textarea id="confirmationInput" placeholder="${escapeHtml(inputPlaceholder)}" rows="3" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: Arial, sans-serif;">${escapeHtml(inputValue)}</textarea>
                </div>
            `;
        } else {
            inputHTML = `
                <div class="input-field">
                    <label>${escapeHtml(inputLabel)}</label>
                    <input type="${inputType}" id="confirmationInput" placeholder="${escapeHtml(inputPlaceholder)}" value="${escapeHtml(inputValue)}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: Arial, sans-serif;" />
                </div>
            `;
        }
    }
    
    modal.innerHTML = `
        <div class="modal-header">
            <h3>${escapeHtml(title)}</h3>
            <button class="modal-close">×</button>
        </div>
        <div class="modal-body">
            <p>${escapeHtml(message)}</p>
            ${inputHTML}
        </div>
        <div class="modal-footer">
            <button id="confirmBtn" class="btn-${dangerMode ? 'danger' : 'primary'}">
                ${escapeHtml(confirmText)}
            </button>
            <button id="cancelBtn" class="btn-secondary">
                ${escapeHtml(cancelText)}
            </button>
        </div>
    `;
    
    // Add event listeners
    const confirmBtn = modal.querySelector('#confirmBtn');
    const cancelBtn = modal.querySelector('#cancelBtn');
    const closeXBtn = modal.querySelector('.modal-close');
    const inputField = modal.querySelector('#confirmationInput');
    
    // Confirm action
    confirmBtn.addEventListener('click', () => {
        const inputValue = inputField ? inputField.value.trim() : null;
        overlay.remove();
        if (onConfirm) {
            onConfirm(inputValue);
        }
    });
    
    // Cancel action
    const cancelAction = () => {
        overlay.remove();
        if (onCancel) {
            onCancel();
        }
    };
    
    cancelBtn.addEventListener('click', cancelAction);
    closeXBtn.addEventListener('click', cancelAction);
    
    // Close on overlay click (but not on modal content)
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            cancelAction();
        }
    });
    
    // Close on Escape key
    const escapeKeyHandler = (e) => {
        if (e.key === 'Escape') {
            cancelAction();
            document.removeEventListener('keydown', escapeKeyHandler);
        }
    };
    document.addEventListener('keydown', escapeKeyHandler);
    
    // Add to DOM
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Focus input field if present, otherwise focus confirm button
    setTimeout(() => {
        if (inputField) {
            inputField.focus();
        } else {
            confirmBtn.focus();
        }
    }, 100);
}

// Installation Key Modal - similar to password modal but with download functionality
function showInstallationKeyModal(installationKey) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    
    // Create modal content
    const modal = document.createElement('div');
    modal.className = 'password-modal installation-key-modal';
    
    modal.innerHTML = `
        <div class="modal-header">
            <h3>🔑 Installation Key Generated</h3>
            <button class="modal-close">×</button>
        </div>
        <div class="modal-body">
            <p>Your installation key has been generated successfully:</p>
            <div class="credentials-container">
                <div class="credential-field">
                    <label>Installation Key:</label>
                    <div id="installationKeyDisplay" style="background: #f8f9fa; padding: 15px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 16pt; word-break: break-all; margin: 10px 0; color: #dc3545; font-weight: bold; border: 2px solid #e9ecef;">${escapeHtml(installationKey)}</div>
                </div>
            </div>
            <div class="warning-message">
                ⚠️ <strong>Important:</strong> This key expires in 24 hours. Copy it now and use it during installation.
            </div>
            <div class="installation-instructions">
                <h4>Installation Steps:</h4>
                <ol>
                    <li>Download the client installer</li>
                    <li>Run the installer file</li>
                    <li>Enter this installation key when prompted</li>
                </ol>
            </div>
        </div>
        <div class="modal-footer">
            <button id="downloadClientBtn" class="btn-primary">
                📥 Download Client
            </button>
            <button id="copyKeyBtn" class="btn-copy">
                📋 Copy Key
            </button>
            <button id="closeKeyModalBtn" class="btn-secondary">
                Close
            </button>
        </div>
    `;
    
    // Add event listeners
    const downloadBtn = modal.querySelector('#downloadClientBtn');
    const copyBtn = modal.querySelector('#copyKeyBtn');
    const closeBtn = modal.querySelector('#closeKeyModalBtn');
    const closeXBtn = modal.querySelector('.modal-close');
    
    // Download functionality
    downloadBtn.addEventListener('click', () => {
        try {
            // Initiate download
            const downloadUrl = `${config.API_BASE_URL}/api/download?file=client`;
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = 'installer.py';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Update button to show success
            downloadBtn.innerHTML = '✅ Download Started!';
            downloadBtn.style.background = '#198754';
            downloadBtn.disabled = true;
            
            setTimeout(() => {
                downloadBtn.innerHTML = '📥 Download Client';
                downloadBtn.style.background = '#007bff';
                downloadBtn.disabled = false;
            }, 3000);
            
            showStatus('Client download started! The file will be saved as "installer.py"', 'success');
        } catch (error) {
            console.error('Download error:', error);
            downloadBtn.innerHTML = '❌ Download Failed';
            downloadBtn.style.background = '#dc3545';
            setTimeout(() => {
                downloadBtn.innerHTML = '📥 Download Client';
                downloadBtn.style.background = '#007bff';
            }, 3000);
        }
    });
    
    // Copy key functionality
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(installationKey);
            copyBtn.innerHTML = '✅ Copied!';
            copyBtn.style.background = '#198754';
            setTimeout(() => {
                copyBtn.innerHTML = '📋 Copy Key';
                copyBtn.style.background = '#28a745';
            }, 2000);
        } catch (error) {
            console.error('Failed to copy key:', error);
            copyBtn.innerHTML = '❌ Copy Failed';
            copyBtn.style.background = '#dc3545';
            setTimeout(() => {
                copyBtn.innerHTML = '📋 Copy Key';
                copyBtn.style.background = '#28a745';
            }, 2000);
        }
    });
    
    // Close functionality
    closeBtn.addEventListener('click', () => {
        overlay.remove();
    });
    
    closeXBtn.addEventListener('click', () => {
        overlay.remove();
    });
    
    // Close on overlay click (but not on modal content)
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    });
    
    // Close on Escape key
    const escapeKeyHandler = (e) => {
        if (e.key === 'Escape') {
            overlay.remove();
            document.removeEventListener('keydown', escapeKeyHandler);
        }
    };
    document.addEventListener('keydown', escapeKeyHandler);
    
    // Add to DOM
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Focus the download button for better user experience
    setTimeout(() => downloadBtn.focus(), 100);
}

// Client Administration Page Initialization
function initializeClientAdministration() {
    console.log('Initializing client administration page...');
    
    // Determine which tab is currently active and refresh its data
    const activeTab = document.querySelector('.tab-button.active');
    
    if (activeTab) {
        const tabId = activeTab.id;
        console.log('Active tab detected:', tabId);
        
        if (tabId === 'clientInfoTab') {
            console.log('Loading client information data');
            loadClientInfo();
        } else if (tabId === 'securityKeysTab') {
            console.log('Loading security keys data');
            loadSecurityKeys();
        }
    } else {
        // Default to loading client info if no active tab detected
        console.log('No active tab detected, defaulting to client info');
        loadClientInfo();
    }
}

// Handle client download
async function handleDownloadClient() {
    // Check if we're on the user download page (has key generation UI)
    const isUserDownloadPage = document.getElementById('installationKeySection') !== null;
    
    if (isUserDownloadPage) {
        // Use the user download flow with key generation
        return handleUserDownloadClient();
    } else {
        // Admin download flow - direct download without key generation
        return handleAdminDownloadClient();
    }
}

// User download client function (with key generation)
async function handleUserDownloadClient() {
    const downloadButton = document.getElementById('downloadClient');
    
    if (!downloadButton) return;
    
    // Disable button and show loading
    downloadButton.disabled = true;
    downloadButton.textContent = 'Generating Download Key...';
    
    try {
        showStatus('Generating installation key...', 'info');
        
        // Generate download key
        const result = await apiCall('generateDownloadKey');
        
        if (result && result.success) {
            const installationKey = result.installationKey;
            
            // Show installation key in popup modal (similar to password modal)
            showInstallationKeyModal(installationKey);
            
            showStatus('Installation key generated! Use it when prompted during installation.', 'success');
            
        } else {
            throw new Error(result ? result.message : 'Failed to generate download key');
        }
    } catch (error) {
        console.error('Download key generation error:', error);
        showStatus('Failed to generate download key: ' + error.message, 'error');
    } finally {
        // Reset button
        downloadButton.disabled = false;
        downloadButton.textContent = 'Download Client';
    }
}

// Admin download client function (direct download)
async function handleAdminDownloadClient() {
    try {
        showStatus('Starting client download...', 'info');
        
        // Direct download using the same endpoint as user download
        const downloadUrl = `${config.API_BASE_URL}/api/download?file=client`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = 'installer.py';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showStatus('Client download started successfully!', 'success');
        
    } catch (error) {
        console.error('Error downloading client:', error);
        showStatus('Failed to download client. Please try again or contact support.', 'error');
    }
}

// Modal management functions
function closeModal() {
    const modal = document.getElementById('clientSelectionModal');
    if (modal) {
        modal.style.display = 'none !important';
        modal.style.visibility = 'hidden';
        
        // Clear modal content
        const modalResult = document.getElementById('modalResult');
        if (modalResult) {
            modalResult.innerHTML = '';
        }
        
        // Reset client select
        const clientSelect = document.getElementById('modalClientSelect');
        if (clientSelect) {
            clientSelect.innerHTML = '<option value="">Loading clients...</option>';
        }
    }
    
    // Also close any other modal overlays
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.remove();
    });
}

// Hide modal on page load to ensure it's not visible
function hideModalOnLoad() {
    const modal = document.getElementById('clientSelectionModal');
    if (modal) {
        modal.style.display = 'none !important';
        modal.style.visibility = 'hidden';
    }
}

function showClientSelectionModal(title, actionType, callback) {
    const modal = document.getElementById('clientSelectionModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalActionBtn = document.getElementById('modalActionBtn');
    const clientSelect = document.getElementById('modalClientSelect');
    
    if (!modal || !modalTitle || !modalActionBtn || !clientSelect) {
        console.error('Modal elements not found');
        return;
    }
    
    // Set modal title
    modalTitle.textContent = title;
    
    // Load clients into select
    loadClientsIntoSelect(clientSelect);
    
    // Set up action button
    modalActionBtn.textContent = actionType;
    modalActionBtn.onclick = () => {
        const selectedClientId = clientSelect.value;
        if (!selectedClientId) {
            showModalError('Please select a client');
            return;
        }
        
        if (callback) {
            callback(selectedClientId);
        }
    };
    
    // Show modal - override CSS with important
    modal.style.display = 'flex !important';
    modal.style.visibility = 'visible';
    
    // Add event listeners for closing
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Close on Escape key
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}

async function loadClientsIntoSelect(selectElement) {
    try {
        selectElement.innerHTML = '<option value="">Loading clients...</option>';
        
        const result = await apiCall('getAllMacClients');
        
        if (result && result.success) {
            const clients = result.data.filter(client => client.activeClientId); // Only active clients
            
            selectElement.innerHTML = '<option value="">Select a client...</option>';
            
            if (clients.length === 0) {
                selectElement.innerHTML = '<option value="">No active clients found</option>';
                return;
            }
            
            clients.forEach(client => {
                const option = document.createElement('option');
                option.value = client.activeClientId;
                option.textContent = `${client.clientName} (${client.username}) - ${client.macAddress}`;
                selectElement.appendChild(option);
            });
        } else {
            selectElement.innerHTML = '<option value="">Failed to load clients</option>';
        }
    } catch (error) {
        console.error('Error loading clients into select:', error);
        selectElement.innerHTML = '<option value="">Error loading clients</option>';
    }
}

function showModalError(message) {
    const modalResult = document.getElementById('modalResult');
    if (modalResult) {
        modalResult.innerHTML = `<div class="error-message">${escapeHtml(message)}</div>`;
    }
}

function showModalSuccess(message) {
    const modalResult = document.getElementById('modalResult');
    if (modalResult) {
        modalResult.innerHTML = `<div class="success-message">${escapeHtml(message)}</div>`;
    }
}

// Enhanced client management functions that use the modal
async function handleUninstallSpecificClientModal() {
    showClientSelectionModal('Uninstall Specific Client', 'Uninstall', async (clientId) => {
        const reason = prompt('Please provide a reason for uninstalling this client:', 'Administrative uninstall');
        if (!reason) return;
        
        if (!confirm(`Are you sure you want to uninstall this client? This action cannot be undone and will remove the software from that specific computer.`)) {
            return;
        }
        
        try {
            showModalError('Uninstalling client...');
            
            const result = await apiCall('uninstallSpecificClient', {
                clientId: clientId,
                reason: reason
            });
            
            if (result && result.success) {
                showModalSuccess(`Uninstall command sent to client successfully!`);
                setTimeout(() => {
                    closeModal();
                    loadAllClients(); // Refresh client list
                    showStatus('Client uninstall command sent successfully!', 'success');
                }, 2000);
            } else {
                showModalError(`Failed to uninstall client: ${result ? result.message : 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error uninstalling specific client:', error);
            showModalError('Failed to uninstall client. Please try again.');
        }
    });
}


// Export security and client management functions for global access
window.loadClientInfo = loadClientInfo;
window.loadSecurityKeys = loadSecurityKeys;
window.deactivateMacClient = deactivateMacClient;
window.viewClientHistory = viewClientHistory;
window.loadAllUsers = loadAllUsers;
window.loadAllClients = loadAllClients;
window.editUser = editUser;
window.deactivateUser = deactivateUser;
window.activateUser = activateUser;
window.handleUninstallSpecificClient = handleUninstallSpecificClient;
// window.handleRetrieveSecurityKey = handleRetrieveSecurityKey; // Function not implemented yet
window.handleRemoveOldActiveNotifications = handleRemoveOldActiveNotifications;
window.handleCleanOldNotifications = handleCleanOldNotifications;
window.handleClearOldWebsiteRequests = handleClearOldWebsiteRequests;
window.handleClearAllNotifications = handleClearAllNotifications;
window.handleDownloadClient = handleDownloadClient;
window.closeModal = closeModal;
window.showClientSelectionModal = showClientSelectionModal;
window.handleUninstallSpecificClientModal = handleUninstallSpecificClientModal;
