// Password validation and UI logic for password reset page
let sessionToken = localStorage.getItem('sessionToken');

// If no session token, redirect to login
if (!sessionToken) {
    window.location.href = 'index.html';
}

// Password requirement validation
function validatePassword(password) {
    const requirements = {
        length: password.length >= 12,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /[0-9]/.test(password),
        symbol: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password),
        unique: new Set(password.split('')).size === password.length
    };
    
    return requirements;
}

// Update requirement indicators
function updatePasswordRequirements(password) {
    const requirements = validatePassword(password);
    
    Object.keys(requirements).forEach(req => {
        const element = document.querySelector(`[data-requirement="${req}"]`);
        if (element) {
            if (requirements[req]) {
                element.classList.add('met');
                element.textContent = element.textContent.replace('✗', '✓');
            } else {
                element.classList.remove('met');
                element.textContent = element.textContent.replace('✓', '✗');
            }
        }
    });
    
    return Object.values(requirements).every(met => met);
}

// Password strength indicator
function updatePasswordStrength(password) {
    const strengthEl = document.getElementById('passwordStrength');
    const requirements = validatePassword(password);
    const metCount = Object.values(requirements).filter(met => met).length;
    
    let strength = 'Very Weak';
    let className = 'very-weak';
    
    if (metCount === 6) {
        strength = 'Very Strong';
        className = 'very-strong';
    } else if (metCount >= 5) {
        strength = 'Strong';
        className = 'strong';
    } else if (metCount >= 4) {
        strength = 'Good';
        className = 'good';
    } else if (metCount >= 3) {
        strength = 'Fair';
        className = 'fair';
    } else if (metCount >= 2) {
        strength = 'Weak';
        className = 'weak';
    }
    
    strengthEl.innerHTML = `<span class="strength-indicator ${className}">Strength: ${strength}</span>`;
    return metCount === 6;
}

// Toggle password visibility
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    
    if (input.type === 'password') {
        input.type = 'text';
        button.textContent = '🙈';
    } else {
        input.type = 'password';
        button.textContent = '👁️';
    }
}

// Enable/disable submit button
function updateSubmitButton() {
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const currentPassword = document.getElementById('currentPassword').value;
    const resetBtn = document.getElementById('resetPasswordBtn');
    
    const passwordValid = updatePasswordRequirements(newPassword);
    const passwordsMatch = newPassword === confirmPassword && newPassword.length > 0;
    const hasCurrentPassword = currentPassword.length > 0;
    
    resetBtn.disabled = !(passwordValid && passwordsMatch && hasCurrentPassword);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Event listeners
    document.getElementById('newPassword').addEventListener('input', function() {
        updatePasswordStrength(this.value);
        updatePasswordRequirements(this.value);
        updateSubmitButton();
    });
    
    document.getElementById('confirmPassword').addEventListener('input', updateSubmitButton);
    document.getElementById('currentPassword').addEventListener('input', updateSubmitButton);
    
    // Add event listeners for password visibility toggle buttons
    const showPasswordBtns = document.querySelectorAll('.show-password-btn');
    showPasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const inputId = this.previousElementSibling.id;
            togglePasswordVisibility(inputId);
        });
    });
    
    // Form submission
    document.getElementById('passwordResetForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const resultDiv = document.getElementById('resetResult');
        const resetBtn = document.getElementById('resetPasswordBtn');
        
        // Show loading state
        resetBtn.querySelector('.btn-text').style.display = 'none';
        resetBtn.querySelector('.btn-loading').classList.remove('hidden');
        resetBtn.disabled = true;
        
        // Validate passwords match
        if (newPassword !== confirmPassword) {
            resultDiv.innerHTML = '<div class="error-message">Passwords do not match</div>';
            resetBtn.querySelector('.btn-text').style.display = 'inline';
            resetBtn.querySelector('.btn-loading').classList.add('hidden');
            resetBtn.disabled = false;
            return;
        }
        
        try {
            const response = await fetch('/api/index', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionToken}`
                },
                body: JSON.stringify({
                    action: 'resetOwnPassword',
                    currentPassword: currentPassword,
                    newPassword: newPassword
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                resultDiv.innerHTML = '<div class="success-message">Password reset successful! Redirecting to admin panel...</div>';
                
                // Redirect after 2 seconds
                setTimeout(() => {
                    window.location.href = 'admin.html';
                }, 2000);
            } else {
                resultDiv.innerHTML = `<div class="error-message">${result.message}</div>`;
                resetBtn.querySelector('.btn-text').style.display = 'inline';
                resetBtn.querySelector('.btn-loading').classList.add('hidden');
                resetBtn.disabled = false;
            }
        } catch (error) {
            console.error('Password reset error:', error);
            resultDiv.innerHTML = '<div class="error-message">Network error. Please try again.</div>';
            resetBtn.querySelector('.btn-text').style.display = 'inline';
            resetBtn.querySelector('.btn-loading').classList.add('hidden');
            resetBtn.disabled = false;
        }
    });
});