// Login page JavaScript
        const loginForm = document.getElementById('loginForm');
        const loginButton = document.getElementById('loginButton');
        const loginSpinner = document.getElementById('loginSpinner');
        const loginButtonText = document.getElementById('loginButtonText');
        const loginStatus = document.getElementById('loginStatus');
        
        // Registration form elements
        const registerForm = document.getElementById('registerForm');
        const registerButton = document.getElementById('registerButton');
        const registerSpinner = document.getElementById('registerSpinner');
        const registerButtonText = document.getElementById('registerButtonText');
        
        // Check if already logged in
        document.addEventListener('DOMContentLoaded', function() {
            checkExistingAuth();
        });
        
        async function checkExistingAuth() {
            try {
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'checkAuth' })
                });
                
                const result = await response.json();
                
                if (result.success && result.authenticated) {
                    showStatus('Already logged in, redirecting...', 'success');
                    setTimeout(() => {
                        // Redirect based on user role
                        if (result.role === 'Admin' || result.role === 'Manager') {
                            window.location.href = 'admin.html';
                        } else if (result.role === 'User') {
                            window.location.href = 'download.html';
                        } else {
                            // Fallback for unknown roles or legacy admin role
                            window.location.href = 'admin.html';
                        }
                    }, 1000);
                }
            } catch (error) {
                console.error('Auth check error:', error);
            }
        }
        
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
                    
                    // Legacy token support
                    if (result.token) {
                        localStorage.setItem('adminToken', result.token);
                    }
                    if (result.sessionId) {
                        sessionStorage.setItem('adminSession', result.sessionId);
                    }
                    
                    showStatus('Login successful! Redirecting to admin panel...', 'success');
                    
                    setTimeout(() => {
                        // Redirect based on user role
                        if (result.role === 'Admin' || result.role === 'Manager') {
                            window.location.href = 'admin.html';
                        } else if (result.role === 'User') {
                            window.location.href = 'download.html';
                        } else {
                            // Fallback for unknown roles or legacy admin role
                            window.location.href = 'admin.html';
                        }
                    }, 1500);
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
        
        function setLoading(loading) {
            loginButton.disabled = loading;
            loginSpinner.style.display = loading ? 'inline-block' : 'none';
            loginButtonText.textContent = loading ? 'Logging in...' : 'Login to Admin Panel';
        }
        
        function showStatus(message, type) {
            loginStatus.innerHTML = `<div class="${type}-message">${message}</div>`;
            
            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    loginStatus.innerHTML = '';
                }, 3000);
            }
        }
        
        // Registration form handler
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                firstName: document.getElementById('regFirstName').value.trim(),
                lastName: document.getElementById('regLastName').value.trim(),
                username: document.getElementById('regUsername').value.trim(),
                email: document.getElementById('regEmail').value.trim(),
                password: document.getElementById('regPassword').value,
                confirmPassword: document.getElementById('regConfirmPassword').value,
                phoneNumber: document.getElementById('regPhoneNumber').value.trim(),
                address: document.getElementById('regAddress').value.trim()
            };
            
            // Validation
            if (!formData.firstName || !formData.lastName || !formData.username || 
                !formData.email || !formData.password) {
                showStatus('Please fill in all required fields', 'error');
                return;
            }
            
            if (formData.password !== formData.confirmPassword) {
                showStatus('Passwords do not match', 'error');
                return;
            }
            
            if (formData.password.length < 8) {
                showStatus('Password must be at least 8 characters long', 'error');
                return;
            }
            
            setRegisterLoading(true);
            
            try {
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: 'createUser',
                        username: formData.username,
                        email: formData.email,
                        password: formData.password,
                        role: 'admin',
                        firstName: formData.firstName,
                        lastName: formData.lastName,
                        phoneNumber: formData.phoneNumber,
                        address: formData.address,
                        requireAuth: false // Allow registration without existing auth
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Account created successfully! You can now log in with your credentials.', 'success');
                    
                    // Clear form
                    registerForm.reset();
                    
                    // Switch back to login form after a delay
                    setTimeout(() => {
                        toggleForm();
                        // Pre-fill username in login form
                        document.getElementById('username').value = formData.username;
                        document.getElementById('password').focus();
                    }, 2000);
                } else {
                    showStatus(result.message || 'Failed to create account', 'error');
                }
            } catch (error) {
                console.error('Registration error:', error);
                showStatus('Registration failed. Please check your connection and try again.', 'error');
            } finally {
                setRegisterLoading(false);
            }
        });
        
        function setRegisterLoading(loading) {
            registerButton.disabled = loading;
            registerSpinner.style.display = loading ? 'inline-block' : 'none';
            registerButtonText.textContent = loading ? 'Creating Account...' : 'Create Admin Account';
        }
        
        function toggleForm() {
            const isLoginVisible = loginForm.style.display !== 'none';
            const headerTitle = document.querySelector('.login-header h1');
            const headerSubtitle = document.querySelector('.login-header p');
            const footerText = document.getElementById('footerText');
            const toggleToRegister = document.getElementById('toggleToRegister');
            const toggleToLogin = document.getElementById('toggleToLogin');
            
            if (isLoginVisible) {
                // Switch to registration
                loginForm.style.display = 'none';
                registerForm.style.display = 'block';
                headerTitle.innerHTML = '📝 Create Admin Account';
                headerSubtitle.textContent = 'PushNotifications Control Panel - Registration';
                footerText.textContent = 'Start your 30-day free trial today';
                toggleToRegister.style.display = 'none';
                toggleToLogin.style.display = 'inline';
                document.getElementById('regFirstName').focus();
            } else {
                // Switch to login
                loginForm.style.display = 'block';
                registerForm.style.display = 'none';
                headerTitle.innerHTML = '🔐 Admin Login';
                headerSubtitle.textContent = 'PushNotifications Control Panel';
                footerText.textContent = 'Access restricted to authorized administrators only';
                toggleToRegister.style.display = 'inline';
                toggleToLogin.style.display = 'none';
                document.getElementById('username').focus();
            }
            
            // Clear any existing status messages
            loginStatus.innerHTML = '';
        }
        
        // Auto-focus username field
        document.getElementById('username').focus();
        
        // Handle Enter key in password field
        document.getElementById('password').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loginForm.dispatchEvent(new Event('submit'));
            }
        });
        
        // Handle Enter key in confirm password field
        document.getElementById('regConfirmPassword').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                registerForm.dispatchEvent(new Event('submit'));
            }
        });