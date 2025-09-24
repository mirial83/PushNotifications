// Account settings functionality
        let currentUserData = null;

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            loadAccountInfo();
            
            // Setup form handlers
            document.getElementById('personalInfoForm').addEventListener('submit', handlePersonalInfoSave);
            document.getElementById('updateUserLimit').addEventListener('click', handleUserLimitUpdate);
            document.getElementById('manageSubscription').addEventListener('click', () => {
                showStatus('Stripe integration coming soon!', 'info');
            });
            document.getElementById('viewBillingHistory').addEventListener('click', () => {
                showStatus('Billing history feature coming soon!', 'info');
            });
        });
        
        // Load account information
        async function loadAccountInfo() {
            try {
                const token = getCookie('sessionToken') || localStorage.getItem('sessionToken');
                if (!token) {
                    window.location.href = 'login.html';
                    return;
                }
                
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ action: 'getAccountInfo' })
                });
                
                const result = await response.json();
                
                if (result.success && result.user) {
                    currentUserData = result.user;
                    populateForm(result.user);
                } else {
                    showStatus('Failed to load account information: ' + (result.message || 'Unknown error'), 'error');
                    if (result.message && result.message.includes('Authentication')) {
                        setTimeout(() => {
                            window.location.href = 'login.html';
                        }, 2000);
                    }
                }
            } catch (error) {
                console.error('Error loading account info:', error);
                showStatus('Failed to load account information. Please try again.', 'error');
            }
        }
        
        // Populate form with user data
        function populateForm(user) {
            document.getElementById('firstName').value = user.firstName || '';
            document.getElementById('lastName').value = user.lastName || '';
            document.getElementById('email').value = user.email || '';
            document.getElementById('username').value = user.username || '';
            document.getElementById('phoneNumber').value = user.phoneNumber || '';
            document.getElementById('address').value = user.address || '';
            
            // Populate subscription info
            const subscription = user.subscription || {};
            document.getElementById('userLimit').value = subscription.userLimit || 1;
            document.getElementById('currentUserLimit').textContent = subscription.userLimit || 1;
            
            // Set plan info
            const planType = document.getElementById('planType');
            const planStatus = document.getElementById('planStatus');
            
            if (subscription.status === 'trial') {
                planType.textContent = 'Free Trial';
                planStatus.textContent = 'Trial';
                planStatus.className = 'status-badge trial';
            } else if (subscription.status === 'active') {
                planType.textContent = 'Admin Plan';
                planStatus.textContent = 'Active';
                planStatus.className = 'status-badge active';
            } else {
                planType.textContent = 'No Active Plan';
                planStatus.textContent = 'Expired';
                planStatus.className = 'status-badge expired';
            }
            
            // Set billing info
            const nextBilling = document.getElementById('nextBilling');
            if (subscription.nextBillingDate) {
                nextBilling.textContent = new Date(subscription.nextBillingDate).toLocaleDateString();
            } else if (subscription.trialEndsAt) {
                nextBilling.textContent = 'Trial ends: ' + new Date(subscription.trialEndsAt).toLocaleDateString();
            } else {
                nextBilling.textContent = 'N/A';
            }
            
            // Set security info
            document.getElementById('userRole').textContent = user.role || 'Unknown';
            document.getElementById('accountCreated').textContent = user.createdAt ? 
                new Date(user.createdAt).toLocaleDateString() : 'Unknown';
            document.getElementById('lastLogin').textContent = user.lastLogin ? 
                new Date(user.lastLogin).toLocaleDateString() : 'Never';
        }
        
        // Handle personal info form submission
        async function handlePersonalInfoSave(e) {
            e.preventDefault();
            
            const button = document.getElementById('savePersonalInfo');
            button.classList.add('loading');
            button.textContent = 'Saving';
            
            try {
                const token = getCookie('sessionToken') || localStorage.getItem('sessionToken');
                const formData = new FormData(e.target);
                
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        action: 'updateAccountInfo',
                        firstName: formData.get('firstName'),
                        lastName: formData.get('lastName'),
                        email: formData.get('email'),
                        phoneNumber: formData.get('phoneNumber'),
                        address: formData.get('address')
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Personal information updated successfully!', 'success');
                    currentUserData = result.user;
                } else {
                    showStatus('Failed to update information: ' + (result.message || 'Unknown error'), 'error');
                }
            } catch (error) {
                console.error('Error updating personal info:', error);
                showStatus('Failed to update information. Please try again.', 'error');
            } finally {
                button.classList.remove('loading');
                button.textContent = 'Save Personal Information';
            }
        }
        
        // Handle user limit update
        async function handleUserLimitUpdate() {
            const button = document.getElementById('updateUserLimit');
            button.classList.add('loading');
            button.textContent = 'Updating';
            
            try {
                const token = getCookie('sessionToken') || localStorage.getItem('sessionToken');
                const userLimit = parseInt(document.getElementById('userLimit').value);
                
                if (userLimit < 1 || userLimit > 50) {
                    showStatus('User limit must be between 1 and 50', 'error');
                    return;
                }
                
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        action: 'updateAccountInfo',
                        subscription: {
                            userLimit: userLimit
                        }
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus(`User limit updated to ${userLimit} users successfully!`, 'success');
                    document.getElementById('currentUserLimit').textContent = userLimit;
                    
                    // Calculate new pricing
                    const monthlyCost = 10 + (userLimit - 1) * 5;
                    showStatus(`New monthly cost: $${monthlyCost} (Note: Full billing integration coming soon)`, 'info');
                } else {
                    showStatus('Failed to update user limit: ' + (result.message || 'Unknown error'), 'error');
                }
            } catch (error) {
                console.error('Error updating user limit:', error);
                showStatus('Failed to update user limit. Please try again.', 'error');
            } finally {
                button.classList.remove('loading');
                button.textContent = 'Update User Limit';
            }
        }
        
        // Utility functions
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }
        
        function showStatus(message, type = 'info') {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.innerHTML = `<div class="status-message ${type}">${message}</div>`;
            
            // Auto-hide after 5 seconds for success messages
            if (type === 'success') {
                setTimeout(() => {
                    statusDiv.innerHTML = '';
                }, 5000);
            }
        }