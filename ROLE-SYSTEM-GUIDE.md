# PushNotifications Role System Guide

## Overview

The PushNotifications system now uses a three-tier role system designed for hierarchical user management and clear permission boundaries.

## Role Hierarchy

### 🔴 **Admin** (Highest Level)
**Full System Control**
- Complete access to all system functions
- Can manage all Managers and Users across the entire system
- Can act as a Manager from their dashboard
- Can create, modify, and delete any user account
- Access to all admin panels and system settings
- Can see all notifications, reports, and analytics
- Full database and system administration capabilities

**Dashboard Access:**
- ✅ Notifications (send to any user/client)
- ✅ Account Administration (all users)
- ✅ Data Management (system-wide)
- ✅ Client Administration (all clients)
- ✅ Version History
- ✅ Account Management (personal settings)
- ✅ System Configuration

### 🟡 **Manager** (Middle Level)
**Limited Administrative Control**
- Can create and manage User accounts
- Manages only their assigned users and clients
- Access to core administrative functions
- Cannot manage other Managers or Admins
- Limited to their own managed clients and data

**Dashboard Access:**
- ✅ Notifications (send to their managed users)
- ✅ Account Administration (their users only)
- ✅ Data Management (their data only)
- ✅ Account Management (personal settings + subscription)
- ✅ Client Management (their managed clients only)
- ❌ System-wide administration
- ❌ Other managers' data

### 🟢 **User** (Standard Level)
**End User Access**
- Standard user with client installation access
- Can download and install client software
- Limited to personal account functions
- No administrative capabilities

**Dashboard Access:**
- ✅ Personal client download
- ✅ Personal account settings
- ❌ Administrative functions
- ❌ User management
- ❌ System configuration

## Permission Matrix

| Function | Admin | Manager | User |
|----------|-------|---------|------|
| **User Management** |
| Create Users | ✅ All | ✅ Users only | ❌ |
| View Users | ✅ All | ✅ Their users | ❌ |
| Delete Users | ✅ All | ✅ Their users | ❌ |
| Modify Roles | ✅ All | ❌ | ❌ |
| **Notifications** |
| Send Notifications | ✅ System-wide | ✅ Their users | ❌ |
| View Notifications | ✅ All | ✅ Their scope | ❌ |
| **Data Management** |
| Database Cleanup | ✅ System-wide | ✅ Their data | ❌ |
| View Reports | ✅ All | ✅ Their scope | ❌ |
| **Client Management** |
| View Clients | ✅ All | ✅ Their clients | ✅ Own only |
| Uninstall Clients | ✅ All | ✅ Their clients | ❌ |
| Security Keys | ✅ All | ✅ Their clients | ❌ |

## Database Schema Changes

### Users Collection
```javascript
{
  role: "Admin" | "Manager" | "User", // Updated from old system
  createdBy: ObjectId, // Tracks who created this user
  numberOfUsers: Number, // How many users they can manage
  linkedUsernames: Array // Array of managed usernames
}
```

### InstallationReports Collection
```javascript
{
  username: String, // Exact username from webform
  administratorUsername: String, // Managing admin/manager
  // ... existing fields
}
```

### Installations Collection
```javascript
{
  username: String, // Exact username from webform  
  administratorUsername: String, // Managing admin/manager
  // ... existing fields
}
```

## Migration Instructions

### 1. Run Role Migration Script
```bash
# Install dependencies if not already installed
npm install mongodb dotenv

# Run the migration script
node api/migrate-roles-and-reports.js
```

### 2. Migration Process
The script will:
- Update user roles: `master_admin` → `Admin`, `admin` → `Manager`, `user` → `User`
- Add `username` and `administratorUsername` to installation reports
- Add tracking fields to installations collection  
- Create indexes for new fields
- Display final role distribution

### 3. Role Mapping
| Old Role | New Role | Permissions |
|----------|----------|-------------|
| `master_admin` | `Admin` | Full system control |
| `admin` | `Manager` | Limited admin functions |
| `user` | `User` | Standard user access |

## API Usage Examples

### Create a User (Manager/Admin only)
```javascript
const response = await fetch('/api/index', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-session-token'
  },
  body: JSON.stringify({
    action: 'createUser',
    username: 'john.doe',
    email: 'john@example.com', 
    password: 'secure-password',
    role: 'User', // User, Manager, or Admin
    firstName: 'John',
    lastName: 'Doe'
    // ... other fields
  })
});
```

### Check User Role
```javascript
const response = await fetch('/api/index', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-session-token'
  },
  body: JSON.stringify({
    action: 'checkAuth'
  })
});

const result = await response.json();
console.log('User role:', result.role); // Admin, Manager, or User
```

## Manager Dashboard Features

### Account Management Page
- Update personal information (name, email, phone, address)
- Manage subscription settings
- View billing information
- Adjust user limits

### Client Management Page  
- View all managed clients and installations
- Uninstall specific clients remotely
- View client security keys and configuration
- Monitor client activity and status
- Filter by managed users only

### Access Controls
- Can only see data for users they created
- Cannot access other managers' or admins' data
- Cannot modify system-wide settings
- Limited to their assigned user quota

## Security Features

### Hierarchical Access Control
- Admins can act as Managers but not vice versa
- Users are automatically assigned to their creating Manager/Admin
- Installation reports track administrative relationships
- Clear audit trail of user creation and management

### Data Isolation
- Managers see only their managed users and clients
- Installation reports filtered by administrator relationship
- Prevents cross-manager data access
- Maintains data privacy between management groups

## Troubleshooting

### Common Issues
1. **Role not updating**: Run the migration script
2. **Permission denied**: Check user role and session validity
3. **Missing installation data**: Run the installation reports migration
4. **Dashboard access issues**: Verify role permissions in database

### Verification Commands
```javascript
// Check role distribution
db.users.aggregate([
  { $group: { _id: "$role", count: { $sum: 1 } } }
]);

// Verify installation tracking
db.installationReports.find({ username: { $exists: true } }).count();
db.installations.find({ administratorUsername: { $exists: true } }).count();
```

## Best Practices

### Role Assignment
- Start new organizations with one Admin
- Create Managers for department heads or team leads
- Assign Users to appropriate Managers based on organizational structure
- Regularly audit role assignments

### User Management
- Managers should create users within their scope
- Admins can override Manager assignments if needed
- Keep user quotas reasonable for subscription management
- Document Manager responsibilities and user assignments

The new role system provides clear separation of responsibilities while maintaining flexibility for different organizational structures.