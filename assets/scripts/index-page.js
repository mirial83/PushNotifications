// JavaScript for index.html (Login page)
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminUser();
    checkExistingAuth();
    document.getElementById('username').focus();
});

// Initialize admin user if it doesn't exist
async function initializeAdminUser() {
    try {
        console.log('Initializing admin user...');
        
        // Try to create the admin user - this will fail silently if user already exists
        const response = await fetch('/api/index', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'createUser',
                username: 'doldarina1',
                email: 'admin@pushnotifications.local',
                password: 'K@7j@B3l13!',
                role: 'admin'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ Admin user created successfully');
        } else if (result.message && result.message.includes('already exists')) {
            console.log('ℹ️ Admin user already exists');
        } else {
            console.log('⚠️ Admin user creation result:', result.message);
        }
    } catch (error) {
        console.log('⚠️ Admin user initialization error:', error.message);
        // Don't show error to user - this is a background operation
    }
}

const loginForm = document.getElementById('loginForm');
const loginButton = document.getElementById('loginButton');
const loginStatus = document.getElementById('loginStatus');

async function checkExistingAuth() {
    try {
        // Get session token from cookie or localStorage
        const sessionToken = getCookie('sessionToken') || localStorage.getItem('sessionToken');
        
        if (!sessionToken) {
            return; // No session token, user needs to login
        }
        
        const response = await fetch('/api/index', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${sessionToken}`
            },
            body: JSON.stringify({ action: 'checkAuth', token: sessionToken })
        });
        
        const result = await response.json();
        
        if (result.success && result.authenticated) {
            // Redirect based on user role
            if (result.role === 'admin') {
                window.location.href = 'admin.html';
            } else {
                window.location.href = 'user-download.html';
            }
        } else {
            // Invalid session, clear tokens
            clearAuthTokens();
        }
    } catch (error) {
        console.error('Auth check error:', error);
        clearAuthTokens();
    }
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function clearAuthTokens() {
    // Clear cookie
    document.cookie = 'sessionToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    // Clear localStorage
    localStorage.removeItem('sessionToken');
    localStorage.removeItem('authToken');
    sessionStorage.removeItem('sessionId');
}

// Initialize form when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                showStatus('Please enter both username and password', 'error');
                return;
            }
            
            setLoading(true);
            
            try {
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'login',
                        username: username,
                        password: password
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Set persistent session cookie that lasts until browser is closed
                    if (result.sessionToken) {
                        // Set as session cookie (no expires date = cleared when browser closes)
                        document.cookie = `sessionToken=${result.sessionToken}; path=/; SameSite=Strict`;
                        
                        // Also store in localStorage as backup
                        localStorage.setItem('sessionToken', result.sessionToken);
                    }
                    
                    showStatus('Login successful! Redirecting...', 'success');
                    
                    setTimeout(() => {
                        // Redirect based on user role
                        if (result.role === 'admin') {
                            window.location.href = 'admin.html';
                        } else {
                            window.location.href = 'user-download.html';
                        }
                    }, 1000);
                } else {
                    showStatus(result.message || 'Invalid credentials', 'error');
                }
            } catch (error) {
                console.error('Login error:', error);
                showStatus('Login failed. Please check your connection and try again.', 'error');
            } finally {
                setLoading(false);
            }
        });
    }
});

function setLoading(loading) {
    if (loginButton) {
        loginButton.disabled = loading;
        loginButton.textContent = loading ? 'Logging in...' : 'Login';
    }
}

function showStatus(message, type) {
    if (loginStatus) {
        loginStatus.innerHTML = `<div class="${type}-message">${message}</div>`;
        
        if (type === 'success') {
            setTimeout(() => {
                loginStatus.innerHTML = '';
            }, 3000);
        }
    }
}