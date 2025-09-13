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
    refreshIntervalSetting: 60, // 1 minute (changed from 30 seconds)
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

// Background client loading (silent, no status messages)
async function loadRegisteredClientsBackground() {
    try {
        const result = await apiCall('getAllMacClients');
        
        if (result && result.success) {
            state.registeredClients = result.data || [];
            displayRegisteredClientsList(state.registeredClients);
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
    if (!confirm('Are you sure you want to clear ALL active notifications? This action cannot be undone.')) {
        return;
    }
    
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
        return diffMinutes < 5; // Consider online if checked in within last 5 minutes
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
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    // Create modal content
    const modal = document.createElement('div');
    modal.className = 'client-history-modal';
    modal.style.cssText = `
        background: white;
        border-radius: 8px;
        padding: 20px;
        max-width: 800px;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    `;
    
    let historyHTML = `
        <div class="modal-header">
            <h3>Client Installation History</h3>
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
                link.download = 'pushnotifications.py';
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
    
    // Data management buttons
    document.getElementById('backupDatabase')?.addEventListener('click', backupDatabase);
    document.getElementById('cleanupOldData')?.addEventListener('click', handleCleanupOldData);
    document.getElementById('exportNotifications')?.addEventListener('click', exportNotifications);
    
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
        const isOnline = isRecentCheckin(client.lastCheckin) && client.activeClientId;
        const version = client.activeClient?.version || 'Unknown';
        
        tableHTML += `
            <tr>
                <td><code>${escapeHtml(client.macAddress)}</code></td>
                <td>${escapeHtml(client.username)}</td>
                <td>${escapeHtml(client.clientName)}</td>
                <td>${escapeHtml(client.platform || 'Unknown')}</td>
                <td>${escapeHtml(version)}</td>
                <td>${formatTimestamp(client.lastCheckin)}</td>
                <td><span class="status-badge ${isOnline ? 'online' : 'offline'}">${isOnline ? 'Online' : 'Offline'}</span></td>
                <td>
                    <button class="btn-small" onclick="viewClientHistory('${client.macAddress}')">History</button>
                    ${client.activeClientId ? 
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


// Placeholder functions for admin features (to be implemented)
function showCreateUserModal() {
    alert('Create user modal - to be implemented');
}

function editUser(userId) {
    alert(`Edit user ${userId} - to be implemented`);
}

function deactivateUser(userId) {
    alert(`Deactivate user ${userId} - to be implemented`);
}

function activateUser(userId) {
    alert(`Activate user ${userId} - to be implemented`);
}

function deactivateAllClients() {
    alert('Deactivate all clients - to be implemented');
}

function exportUserData() {
    alert('Export user data - to be implemented');
}

function exportClientData() {
    alert('Export client data - to be implemented');
}

function backupDatabase() {
    alert('Backup database - to be implemented');
}

function exportNotifications() {
    alert('Export notifications - to be implemented');
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
