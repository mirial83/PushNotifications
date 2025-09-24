# Frontend Form Update Guide

## Overview
This guide provides instructions for updating frontend forms to collect all the new required encrypted personal information fields.

## Required Form Fields

All user registration and profile forms must collect these fields in order:

### Core Personal Information
1. **Email** - Email address (required)
2. **Password** - Password (required for registration)
3. **Phone Number** - Phone number (required)

### Address Information (in specific order)
4. **Street Number** - Street number (required)
5. **Street Name** - Street name (required) 
6. **Apartment/Suite** - Apartment or suite number (optional)
7. **Second Line** - Second address line (optional)
8. **City** - City name (required)
9. **State** - State or province (required)
10. **ZIP Code** - ZIP or postal code (required)

### Optional Legacy Fields
- **First Name** - First name (optional, legacy)
- **Last Name** - Last name (optional, legacy)
- **Address** - Combined address field (optional, legacy)

## HTML Form Examples

### User Registration Form
```html
<form id="userRegistrationForm">
  <!-- Basic Info -->
  <div class="form-group">
    <label for="username">Username *</label>
    <input type="text" id="username" name="username" required>
  </div>

  <div class="form-group">
    <label for="email">Email *</label>
    <input type="email" id="email" name="email" required>
  </div>

  <div class="form-group">
    <label for="password">Password *</label>
    <input type="password" id="password" name="password" required>
  </div>

  <div class="form-group">
    <label for="phoneNumber">Phone Number *</label>
    <input type="tel" id="phoneNumber" name="phoneNumber" required>
  </div>

  <!-- Address Information (in required order) -->
  <div class="form-group">
    <label for="streetNumber">Street Number *</label>
    <input type="text" id="streetNumber" name="streetNumber" required>
  </div>

  <div class="form-group">
    <label for="streetName">Street Name *</label>
    <input type="text" id="streetName" name="streetName" required>
  </div>

  <div class="form-group">
    <label for="apartmentSuite">Apartment/Suite</label>
    <input type="text" id="apartmentSuite" name="apartmentSuite">
  </div>

  <div class="form-group">
    <label for="secondLine">Second Address Line</label>
    <input type="text" id="secondLine" name="secondLine">
  </div>

  <div class="form-group">
    <label for="city">City *</label>
    <input type="text" id="city" name="city" required>
  </div>

  <div class="form-group">
    <label for="state">State *</label>
    <input type="text" id="state" name="state" required>
  </div>

  <div class="form-group">
    <label for="zipCode">ZIP Code *</label>
    <input type="text" id="zipCode" name="zipCode" required>
  </div>

  <!-- Optional Legacy Fields -->
  <div class="form-group">
    <label for="firstName">First Name</label>
    <input type="text" id="firstName" name="firstName">
  </div>

  <div class="form-group">
    <label for="lastName">Last Name</label>
    <input type="text" id="lastName" name="lastName">
  </div>

  <button type="submit">Create User</button>
</form>
```

### Profile Update Form
```html
<form id="profileUpdateForm">
  <!-- Email -->
  <div class="form-group">
    <label for="email">Email *</label>
    <input type="email" id="email" name="email" required>
  </div>

  <div class="form-group">
    <label for="phoneNumber">Phone Number *</label>
    <input type="tel" id="phoneNumber" name="phoneNumber" required>
  </div>

  <!-- Address Information -->
  <div class="form-section">
    <h3>Address Information</h3>
    
    <div class="form-group">
      <label for="streetNumber">Street Number *</label>
      <input type="text" id="streetNumber" name="streetNumber" required>
    </div>

    <div class="form-group">
      <label for="streetName">Street Name *</label>
      <input type="text" id="streetName" name="streetName" required>
    </div>

    <div class="form-group">
      <label for="apartmentSuite">Apartment/Suite</label>
      <input type="text" id="apartmentSuite" name="apartmentSuite">
    </div>

    <div class="form-group">
      <label for="secondLine">Second Address Line</label>
      <input type="text" id="secondLine" name="secondLine">
    </div>

    <div class="form-group">
      <label for="city">City *</label>
      <input type="text" id="city" name="city" required>
    </div>

    <div class="form-group">
      <label for="state">State *</label>
      <input type="text" id="state" name="state" required>
    </div>

    <div class="form-group">
      <label for="zipCode">ZIP Code *</label>
      <input type="text" id="zipCode" name="zipCode" required>
    </div>
  </div>

  <!-- Optional Fields -->
  <div class="form-section">
    <h3>Optional Information</h3>
    
    <div class="form-group">
      <label for="firstName">First Name</label>
      <input type="text" id="firstName" name="firstName">
    </div>

    <div class="form-group">
      <label for="lastName">Last Name</label>
      <input type="text" id="lastName" name="lastName">
    </div>
  </div>

  <button type="submit">Update Profile</button>
</form>
```

## JavaScript Form Handling

### User Registration
```javascript
document.getElementById('userRegistrationForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const userData = {
    action: 'createUser',
    username: formData.get('username'),
    email: formData.get('email'),
    password: formData.get('password'),
    phoneNumber: formData.get('phoneNumber'),
    streetNumber: formData.get('streetNumber'),
    streetName: formData.get('streetName'),
    apartmentSuite: formData.get('apartmentSuite') || '',
    secondLine: formData.get('secondLine') || '',
    city: formData.get('city'),
    state: formData.get('state'),
    zipCode: formData.get('zipCode'),
    firstName: formData.get('firstName') || '',
    lastName: formData.get('lastName') || '',
    role: 'User'
  };

  try {
    const response = await fetch('/api/index', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });

    const result = await response.json();
    
    if (result.success) {
      alert('User created successfully!');
      e.target.reset();
    } else {
      alert('Error: ' + result.message);
    }
  } catch (error) {
    alert('Network error: ' + error.message);
  }
});
```

### Profile Update
```javascript
document.getElementById('profileUpdateForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const updateData = {
    action: 'updateUser',
    userId: getCurrentUserId(), // Your function to get current user ID
    email: formData.get('email'),
    phoneNumber: formData.get('phoneNumber'),
    streetNumber: formData.get('streetNumber'),
    streetName: formData.get('streetName'),
    apartmentSuite: formData.get('apartmentSuite'),
    secondLine: formData.get('secondLine'),
    city: formData.get('city'),
    state: formData.get('state'),
    zipCode: formData.get('zipCode'),
    firstName: formData.get('firstName'),
    lastName: formData.get('lastName')
  };

  try {
    const response = await fetch('/api/index', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + getAuthToken() // Your function to get auth token
      },
      body: JSON.stringify(updateData)
    });

    const result = await response.json();
    
    if (result.success) {
      alert('Profile updated successfully!');
    } else {
      alert('Error: ' + result.message);
    }
  } catch (error) {
    alert('Network error: ' + error.message);
  }
});
```

### Loading User Data for Edit Forms
```javascript
async function loadUserProfile() {
  try {
    const response = await fetch('/api/index', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + getAuthToken()
      },
      body: JSON.stringify({ action: 'getAccountInfo' })
    });

    const result = await response.json();
    
    if (result.success && result.user) {
      const user = result.user;
      
      // Populate form fields
      document.getElementById('email').value = user.email || '';
      document.getElementById('phoneNumber').value = user.phoneNumber || '';
      document.getElementById('streetNumber').value = user.streetNumber || '';
      document.getElementById('streetName').value = user.streetName || '';
      document.getElementById('apartmentSuite').value = user.apartmentSuite || '';
      document.getElementById('secondLine').value = user.secondLine || '';
      document.getElementById('city').value = user.city || '';
      document.getElementById('state').value = user.state || '';
      document.getElementById('zipCode').value = user.zipCode || '';
      document.getElementById('firstName').value = user.firstName || '';
      document.getElementById('lastName').value = user.lastName || '';
    }
  } catch (error) {
    console.error('Error loading user profile:', error);
  }
}
```

## Form Validation

### Client-Side Validation
```javascript
function validateUserForm(formData) {
  const errors = [];
  
  // Required fields validation
  const requiredFields = [
    'username', 'email', 'password', 'phoneNumber',
    'streetNumber', 'streetName', 'city', 'state', 'zipCode'
  ];
  
  requiredFields.forEach(field => {
    if (!formData.get(field) || formData.get(field).trim() === '') {
      errors.push(`${field} is required`);
    }
  });
  
  // Email validation
  const email = formData.get('email');
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (email && !emailRegex.test(email)) {
    errors.push('Please enter a valid email address');
  }
  
  // Phone validation (basic)
  const phone = formData.get('phoneNumber');
  const phoneRegex = /^[\d\s\-\(\)\+]+$/;
  if (phone && !phoneRegex.test(phone)) {
    errors.push('Please enter a valid phone number');
  }
  
  // ZIP code validation (basic)
  const zipCode = formData.get('zipCode');
  const zipRegex = /^[\d\-\s]+$/;
  if (zipCode && !zipRegex.test(zipCode)) {
    errors.push('Please enter a valid ZIP code');
  }
  
  return errors;
}
```

## CSS Styling

### Form Styling Example
```css
.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-section {
  margin-bottom: 2rem;
  padding: 1rem;
  border: 1px solid #e9ecef;
  border-radius: 6px;
}

.form-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #495057;
}

.required::after {
  content: " *";
  color: #dc3545;
}

button[type="submit"] {
  background-color: #007bff;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

button[type="submit"]:hover {
  background-color: #0056b3;
}

.error {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
```

## Files to Update

Based on your existing codebase, you'll likely need to update these files:

### HTML Files
- `setup-admin.html` - Initial admin setup form
- `account-settings.html` - User profile management
- Any user registration forms

### JavaScript Files
- `assets/scripts/script.js` - Main application logic
- `assets/scripts/account-settings.js` - Profile management
- `assets/scripts/login.js` - User authentication

## Migration Considerations

### For Existing Forms
1. **Backup existing forms** before making changes
2. **Add new fields gradually** to avoid breaking existing functionality
3. **Make new fields optional initially** during transition period
4. **Update validation logic** to include new fields
5. **Test thoroughly** with different user roles

### Data Migration
- Existing users will have empty values for new fields
- Forms should handle empty/null values gracefully
- Consider providing data import functionality for bulk updates

## Testing Checklist

### Form Testing
- [ ] All required fields validate correctly
- [ ] Optional fields can be left empty
- [ ] Form submission creates/updates users successfully
- [ ] Error messages display appropriately
- [ ] Form data persists after validation errors
- [ ] All user roles can access appropriate forms

### Data Testing
- [ ] New user creation includes all fields
- [ ] Profile updates modify correct fields
- [ ] Encrypted data is not visible in browser/network tools
- [ ] Existing users can update their profiles
- [ ] Manager/Admin forms work correctly for user management

## Security Notes

1. **Never store sensitive data** in browser localStorage or sessionStorage
2. **Always validate data** on both client and server side
3. **Use HTTPS** for all form submissions
4. **Sanitize input** before sending to server
5. **Handle errors gracefully** without exposing sensitive information

## Troubleshooting

### Common Issues
1. **Missing fields in API calls** - Check field names match exactly
2. **Validation errors** - Ensure required fields are marked correctly
3. **Empty form data** - Check FormData extraction logic
4. **Permission errors** - Verify authentication tokens are sent
5. **Old data not loading** - User may need to log out/in after updates

This guide should help you update all frontend forms to collect the new required encrypted personal information fields while maintaining a good user experience.