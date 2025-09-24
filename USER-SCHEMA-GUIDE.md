# User Schema Guide

## Overview
This guide documents the updated user schema that includes all required encrypted personal information fields in the specified order.

## Required Encrypted Fields (in order)

All users in the MongoDB database now have the following encrypted fields in this specific order:

1. **email** (encrypted) - User's email address
2. **password** (hashed) - User's password (Base64 encoded)
3. **streetNumber** (encrypted) - Street number for address
4. **streetName** (encrypted) - Street name for address
5. **apartmentSuite** (encrypted) - Apartment or suite number
6. **secondLine** (encrypted) - Second address line
7. **city** (encrypted) - City name
8. **state** (encrypted) - State or province
9. **zipCode** (encrypted) - ZIP or postal code
10. **phoneNumber** (encrypted) - Phone number

## Database Schema

### User Document Structure

```javascript
{
  _id: ObjectId,
  username: String, // Plain text - used for login
  
  // Encrypted personal information fields (in order)
  email: String, // Encrypted
  email_hash: String, // SHA256 hash for indexing
  password: String, // Base64 encoded (hashed)
  streetNumber: String, // Encrypted
  streetName: String, // Encrypted
  apartmentSuite: String, // Encrypted
  secondLine: String, // Encrypted
  city: String, // Encrypted
  state: String, // Encrypted
  zipCode: String, // Encrypted
  phoneNumber: String, // Encrypted
  
  // Legacy fields (still supported)
  firstName: String, // Encrypted
  lastName: String, // Encrypted
  address: String, // Encrypted (legacy field)
  
  // Role and management
  role: String, // 'User', 'Manager', 'Admin'
  createdBy: String, // ID of user who created this account
  numberOfUsers: Number,
  linkedUsernames: Array,
  
  // Metadata
  createdAt: Date,
  lastLogin: Date,
  isActive: Boolean,
  
  // Encryption metadata
  _encrypted_fields: Array, // List of encrypted field names
  schemaVersion: String, // Current: '2.0'
  lastMigrated: Date,
  
  // Subscription info
  subscription: {
    plan: String,
    status: String,
    userLimit: Number,
    stripeCustomerId: String,
    stripeSubscriptionId: String,
    nextBillingDate: Date,
    trialEndsAt: Date
  }
}
```

## API Endpoints

### Create User
```javascript
POST /api/index
{
  "action": "createUser",
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securePassword123",
  "role": "User",
  "firstName": "John",
  "lastName": "Doe",
  "phoneNumber": "555-123-4567",
  "streetNumber": "123",
  "streetName": "Main Street",
  "apartmentSuite": "Apt 4B",
  "secondLine": "",
  "city": "Springfield",
  "state": "IL",
  "zipCode": "62701"
}
```

### Get User By ID
```javascript
POST /api/index
Headers: { "Authorization": "Bearer <token>" }
{
  "action": "getUserById",
  "userId": "68c5cfeddc3be3c771aa574c"
}
```

### Update User
```javascript
POST /api/index
Headers: { "Authorization": "Bearer <token>" }
{
  "action": "updateUser",
  "userId": "68c5cfeddc3be3c771aa574c",
  "email": "newemail@example.com",
  "firstName": "John",
  "lastName": "Smith",
  "phoneNumber": "555-987-6543",
  "streetNumber": "456",
  "streetName": "Oak Avenue",
  "apartmentSuite": "",
  "secondLine": "Building A",
  "city": "Chicago",
  "state": "IL",
  "zipCode": "60601"
}
```

### Get All Users (Admin/Manager only)
```javascript
POST /api/index
Headers: { "Authorization": "Bearer <token>" }
{
  "action": "getAllUsers"
}
```

### Get Account Info (Self)
```javascript
POST /api/index
Headers: { "Authorization": "Bearer <token>" }
{
  "action": "getAccountInfo"
}
```

## Encryption Details

### Encryption Algorithm
- **Algorithm**: AES-256-GCM
- **Key Derivation**: PBKDF2 (100,000 iterations)
- **Salt Length**: 64 bytes
- **IV Length**: 16 bytes
- **Tag Length**: 16 bytes

### Encrypted Data Format
Each encrypted field is stored as a concatenated hex string:
```
salt (128 hex chars) + iv (32 hex chars) + authTag (32 hex chars) + encrypted_data
```

### Email Hashing
For indexing and uniqueness checking, emails are also stored as SHA256 hashes:
```javascript
email_hash = SHA256(email + ENCRYPTION_KEY)
```

## Migration

### Migration Script
The migration script `api/migrate-user-schema.js` was used to update existing users with the new schema. It:

1. Adds missing encrypted fields with empty values
2. Updates the `_encrypted_fields` array
3. Sets schema version to '2.0'
4. Creates necessary database indexes

### Running Migration
```bash
node api/migrate-user-schema.js
```

## Role-Based Access

### User Permissions
- **User**: Can view/update own profile only
- **Manager**: Can create users, view/update users they created, view/update own profile
- **Admin**: Full access to all users and system functions

### Data Access Rules
1. Users can only access their own encrypted data
2. Managers can access encrypted data of users they created
3. Admins can access all encrypted data
4. All decryption happens server-side; encrypted data is never sent to clients

## Frontend Considerations

When updating frontend forms, ensure they collect all required fields:

### Required Form Fields (in order)
1. Email
2. Password (for creation/changes)
3. Street Number
4. Street Name
5. Apartment/Suite
6. Second Line
7. City
8. State
9. ZIP Code
10. Phone Number

### Optional Legacy Fields
- First Name
- Last Name
- Address (legacy combined field)

## Security Notes

1. **Encryption Keys**: The ENCRYPTION_KEY environment variable must be consistent across all instances
2. **Password Storage**: Passwords are Base64 encoded (consider upgrading to bcrypt for production)
3. **Data at Rest**: All personal information is encrypted in the database
4. **Data in Transit**: API uses HTTPS in production
5. **Access Control**: Role-based permissions control data access
6. **Session Management**: JWT tokens for authentication

## Troubleshooting

### Common Issues

1. **Decryption Errors**: Usually caused by missing or incorrect ENCRYPTION_KEY
2. **Missing Fields**: Run the migration script to add missing schema fields
3. **Permission Errors**: Check user roles and authentication tokens
4. **Email Conflicts**: Email hashes are used for uniqueness checking

### Migration Issues

If users appear to have corrupted encrypted data after migration, it may be due to:
1. Different ENCRYPTION_KEY values during migration vs. runtime
2. Node.js version differences affecting crypto functions
3. Database connection issues during migration

### Recovery

To recover from encryption issues:
1. Backup the database
2. Check ENCRYPTION_KEY consistency
3. Re-run migration script if needed
4. Test with a single user first

## API Response Examples

### Successful User Creation
```json
{
  "success": true,
  "message": "User created successfully",
  "userId": "68c5cfeddc3be3c771aa574c",
  "user": {
    "id": "68c5cfeddc3be3c771aa574c",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "User",
    "streetNumber": "123",
    "streetName": "Main Street",
    "apartmentSuite": "Apt 4B",
    "secondLine": "",
    "city": "Springfield",
    "state": "IL",
    "zipCode": "62701",
    "phoneNumber": "555-123-4567",
    "createdAt": "2025-01-24T20:04:48Z",
    "isActive": true
  }
}
```

### User Data Retrieval
```json
{
  "success": true,
  "data": {
    "id": "68c5cfeddc3be3c771aa574c",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "User",
    "firstName": "John",
    "lastName": "Doe",
    "phoneNumber": "555-123-4567",
    "streetNumber": "123",
    "streetName": "Main Street",
    "apartmentSuite": "Apt 4B",
    "secondLine": "",
    "city": "Springfield",
    "state": "IL",
    "zipCode": "62701",
    "createdAt": "2025-01-24T20:04:48Z",
    "lastLogin": "2025-01-24T20:10:15Z",
    "isActive": true
  }
}
```

## Database Indexes

The following indexes are created for optimal performance:

- `{ email_hash: 1 }` - Unique index for email lookups
- `{ username: 1, role: 1 }` - Compound index for user management
- `{ schemaVersion: 1 }` - Migration tracking
- `{ createdBy: 1 }` - Manager user filtering

## Conclusion

The updated user schema provides comprehensive encrypted storage of all required personal information fields while maintaining backward compatibility with existing functionality. All sensitive data is encrypted at rest and properly managed through role-based access controls.