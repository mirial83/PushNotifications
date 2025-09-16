# Unified Installations Collection Schema

This document defines the consolidated schema for the `installations` collection that replaces `clients`, `macClients`, `clientHistory`, and `securityKeys` collections.

## Collection: `installations`

Each document represents a single client installation with complete information.

```javascript
{
  // Primary identifiers
  _id: ObjectId,
  installationId: String, // Unique installation identifier
  clientId: String, // Client identifier (username_macAddress_installNumber format)
  
  // Installation key and authentication
  installationKey: String, // Key used for initial installation
  keyId: String, // Unique key identifier
  
  // MAC address and device info
  macAddress: String, // MAC address of the device
  macDetectionMethod: String, // How MAC was detected (automatic, manual, etc.)
  
  // User information
  username: String, // System username
  clientName: String, // Display name (e.g., "username1", "username2")
  userId: ObjectId, // Reference to users collection
  userRole: String, // Role of the user who installed (admin, user)
  
  // System information
  hostname: String, // Computer hostname
  platform: String, // OS platform (Windows, macOS, Linux)
  version: String, // Client software version
  installPath: String, // Installation directory path
  systemInfo: Object, // Additional system information
  
  // Installation metadata
  installerMode: String, // How it was installed (gui, silent, etc.)
  registeredAt: Date, // When installation was registered
  createdAt: Date, // When record was created
  lastCheckin: Date, // Last time client checked in
  
  // Status and activity
  isActive: Boolean, // Whether this installation is currently active
  isCurrentForMac: Boolean, // Whether this is the current active installation for this MAC
  installationCount: Number, // Installation number for this MAC address (1, 2, 3, etc.)
  
  // Deactivation info (when isActive = false)
  deactivatedAt: Date,
  deactivationReason: String,
  
  // Security keys (embedded instead of separate collection)
  securityKeys: {
    encryptionKey: {
      keyValue: String,
      keyType: String, // "ENCRYPTION_KEY"
      createdAt: Date,
      lastUsed: Date
    },
    // Can add other key types as needed
  },
  
  // Installation history tracking
  installationHistory: {
    previousInstallations: Number, // Count of previous installations on this MAC
    isReinstallation: Boolean, // Whether this replaced a previous installation
    replacedInstallationId: String // ID of installation this replaced (if any)
  },
  
  // Policy and configuration
  policy: {
    allowWebsiteRequests: Boolean,
    snoozeEnabled: Boolean,
    updateCheckInterval: Number,
    heartbeatInterval: Number
  }
}
```

## Indexes

Required indexes for optimal performance:

```javascript
// Primary lookup indexes
{ installationId: 1 }, // unique
{ clientId: 1 }, // unique
{ macAddress: 1 }, // for MAC-based operations
{ userId: 1 }, // for user-based operations

// Status and activity indexes
{ isActive: 1 },
{ isCurrentForMac: 1 },
{ macAddress: 1, isCurrentForMac: 1 },

// Time-based indexes
{ createdAt: -1 },
{ lastCheckin: -1 },
{ registeredAt: -1 },

// Combined indexes for common queries
{ macAddress: 1, isActive: 1 },
{ userId: 1, isActive: 1 },
{ hostname: 1 },
{ platform: 1 }
```

## Migration Strategy

1. **Preserve all existing data** by migrating from multiple collections
2. **Maintain MAC-based client management** logic
3. **Keep installation history** within each document
4. **Embed security keys** to eliminate separate collection
5. **Support backwards compatibility** during transition

## Key Benefits

1. **Single source of truth** for all client installation data
2. **Atomic operations** - no need to update multiple collections
3. **Better performance** - fewer joins and lookups
4. **Simplified queries** - all data in one place
5. **Easier maintenance** - one collection to manage
6. **Consistent data model** - no risk of orphaned records between collections

## Breaking Changes

- Frontend code must be updated to work with new data structure
- API methods need to query single collection instead of joining multiple
- Installation process simplified to single collection insert
- Security key retrieval now embedded in installation document
