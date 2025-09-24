# MongoDB Users Collection Migration

This guide explains how to update your MongoDB users collection with the new address fields.

## What's Being Added

The users collection will be updated to include these new fields:

### New Address Fields
- `streetNumber` - Street number (encrypted)
- `streetName` - Street name (encrypted)  
- `apartmentSuite` - Apartment or suite number (encrypted)
- `secondAddressLine` - Second address line (encrypted)
- `city` - City (encrypted)
- `state` - State/Province (encrypted)
- `zipCode` - ZIP/Postal code (encrypted)

### User Management Fields
- `numberOfUsers` - Number of users an admin can manage
- `linkedUsernames` - Array of usernames they manage

## Before You Start

1. **Backup your database** - Always backup before running migrations
2. **Have your MongoDB connection details ready**
3. **Ensure you have Node.js installed**

## Running the Migration

### Option 1: Run the Migration Script

1. Navigate to the project directory:
   ```bash
   cd /path/to/PushNotifications
   ```

2. Make sure you have the required environment variables:
   ```bash
   # Check if .env file exists and contains MONGODB_CONNECTION_STRING
   cat .env
   ```

3. Run the migration script:
   ```bash
   node api/migrate-users-collection.js
   ```

4. The script will:
   - Connect to your MongoDB database
   - Update existing users with new fields
   - Migrate existing `address` field to structured fields (if possible)
   - Create indexes for the new fields
   - Display the final schema

### Option 2: Manual Database Update

If you prefer to update manually using MongoDB Compass or mongo shell:

```javascript
// Connect to your database
use pushnotifications

// Update all existing users with new fields
db.users.updateMany(
  {},
  {
    $set: {
      streetNumber: "",
      streetName: "",
      apartmentSuite: "",
      secondAddressLine: "",
      city: "",
      state: "",
      zipCode: "",
      numberOfUsers: 0,
      linkedUsernames: [],
      _encrypted_fields: [
        "email", "firstName", "lastName", "phoneNumber", "address",
        "streetNumber", "streetName", "apartmentSuite", "secondAddressLine", 
        "city", "state", "zipCode"
      ]
    }
  }
)

// Create indexes for new fields
db.users.createIndex({ city: 1 }, { sparse: true })
db.users.createIndex({ state: 1 }, { sparse: true })
db.users.createIndex({ zipCode: 1 }, { sparse: true })
db.users.createIndex({ numberOfUsers: 1 })
db.users.createIndex({ linkedUsernames: 1 }, { sparse: true })
```

## Updated API Usage

After migration, you can create users with the new fields:

```javascript
// API call example
const userData = {
  username: "john.doe",
  email: "john@example.com",
  password: "securepassword",
  firstName: "John",
  lastName: "Doe",
  phoneNumber: "555-123-4567",
  streetNumber: "123",
  streetName: "Main Street",
  apartmentSuite: "Apt 4B",
  city: "Springfield",
  state: "IL",
  zipCode: "62701",
  role: "user"
}

fetch('/api/index', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    action: 'createUser',
    ...userData
  })
})
```

## Final Database Schema

After migration, each user document will contain:

```javascript
{
  _id: ObjectId("..."),
  username: "john.doe",
  email: "encrypted_email_data",
  email_hash: "hashed_for_indexing",
  password: "hashed_password",
  firstName: "encrypted_first_name",
  lastName: "encrypted_last_name", 
  phoneNumber: "encrypted_phone",
  address: "encrypted_legacy_address", // Legacy field
  streetNumber: "encrypted_street_number",
  streetName: "encrypted_street_name",
  apartmentSuite: "encrypted_apt_suite",
  secondAddressLine: "encrypted_second_line",
  city: "encrypted_city",
  state: "encrypted_state",
  zipCode: "encrypted_zip_code",
  role: "user",
  numberOfUsers: 0,
  linkedUsernames: [],
  createdAt: ISODate("..."),
  lastLogin: ISODate("..."),
  isActive: true,
  _encrypted_fields: [...],
  subscription: {...}
}
```

## Troubleshooting

- **Connection errors**: Check your MONGODB_CONNECTION_STRING in .env file
- **Permission errors**: Ensure your MongoDB user has write permissions
- **Migration fails**: Check the console output for specific error messages

## Rollback

If you need to rollback, you can remove the new fields:

```javascript
db.users.updateMany(
  {},
  {
    $unset: {
      streetNumber: "",
      streetName: "",
      apartmentSuite: "",
      secondAddressLine: "",
      city: "",
      state: "",
      zipCode: "",
      numberOfUsers: "",
      linkedUsernames: ""
    }
  }
)
```

**Note**: This migration is backward compatible - existing functionality will continue to work.