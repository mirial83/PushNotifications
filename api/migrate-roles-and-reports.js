#!/usr/bin/env node

/**
 * MongoDB Role Migration and InstallationReports Update Script
 * 
 * Updates the users collection role system:
 * - Changes roles from ['user', 'admin', 'master_admin'] to ['User', 'Manager', 'Admin']
 * - Admin: Full control over all managers and users, can act as manager
 * - Manager: Can create users, manage their assigned users and clients
 * - User: Standard user with limited permissions
 * 
 * Updates installationReports collection:
 * - Adds username field (exact username from webform)
 * - Adds administratorUsername field to track which manager/admin manages them
 * 
 * This script will:
 * 1. Connect to MongoDB
 * 2. Update user roles to new system
 * 3. Update installationReports with username tracking
 * 4. Create indexes for the new fields
 */

const { MongoClient, ObjectId } = require('mongodb');
require('dotenv').config();

// Configuration
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';

if (!MONGODB_CONNECTION_STRING) {
  console.error('❌ MONGODB_CONNECTION_STRING not found in environment variables');
  console.error('Please check your .env file or environment configuration');
  process.exit(1);
}

async function migrateRolesAndReports() {
  const client = new MongoClient(MONGODB_CONNECTION_STRING);
  
  try {
    console.log('🔗 Connecting to MongoDB...');
    await client.connect();
    
    const db = client.db(MONGODB_DATABASE);
    const usersCollection = db.collection('users');
    const installationReportsCollection = db.collection('installationReports');
    const installationsCollection = db.collection('installations');
    
    console.log('\\n📊 PHASE 1: Update User Roles');
    console.log('=====================================');
    
    // Role migration mapping
    const roleMapping = {
      'master_admin': 'Admin',
      'admin': 'Manager', 
      'user': 'User'
    };
    
    // Get current users and their roles
    const users = await usersCollection.find({}).toArray();
    console.log(`Found ${users.length} users to potentially update`);
    
    let roleUpdatedCount = 0;
    for (const user of users) {
      const currentRole = user.role;
      const newRole = roleMapping[currentRole] || currentRole;
      
      if (newRole !== currentRole) {
        await usersCollection.updateOne(
          { _id: user._id },
          { $set: { role: newRole } }
        );
        console.log(`✅ Updated ${user.username}: ${currentRole} → ${newRole}`);
        roleUpdatedCount++;
      } else if (['Admin', 'Manager', 'User'].includes(currentRole)) {
        console.log(`ℹ️  ${user.username}: Already using new role system (${currentRole})`);
      } else {
        console.log(`⚠️  ${user.username}: Unknown role '${currentRole}' - consider manual review`);
      }
    }
    
    console.log(`\\n📈 Updated ${roleUpdatedCount} user roles`);
    
    console.log('\\n📊 PHASE 2: Update Installation Reports');
    console.log('=========================================');
    
    // Get all installation reports
    const reports = await installationReportsCollection.find({}).toArray();
    console.log(`Found ${reports.length} installation reports to potentially update`);
    
    let reportsUpdatedCount = 0;
    for (const report of reports) {
      const updateFields = {};
      let needsUpdate = false;
      
      // Add username field if missing
      if (!report.hasOwnProperty('username')) {
        // Try to find username from userId if available
        if (report.userId) {
          try {
            const user = await usersCollection.findOne({ _id: new ObjectId(report.userId) });
            if (user && user.username) {
              updateFields.username = user.username;
              console.log(`📝 Adding username '${user.username}' to report ${report._id}`);
              needsUpdate = true;
            }
          } catch (error) {
            console.log(`⚠️  Could not find user for userId ${report.userId}: ${error.message}`);
          }
        }
        
        // If still no username, try to extract from other fields or set as unknown
        if (!updateFields.username) {
          updateFields.username = report.hostname || report.clientId || 'unknown';
          needsUpdate = true;
        }
      }
      
      // Add administratorUsername field if missing
      if (!report.hasOwnProperty('administratorUsername')) {
        let adminUsername = null;
        
        // Try to find the administrator username
        if (report.userId) {
          try {
            const user = await usersCollection.findOne({ _id: new ObjectId(report.userId) });
            if (user) {
              if (user.createdBy) {
                // Find the admin/manager who created this user
                const creator = await usersCollection.findOne({ _id: new ObjectId(user.createdBy) });
                if (creator) {
                  adminUsername = creator.username;
                }
              } else if (user.role === 'User') {
                // For users without createdBy, try to find a manager/admin
                // This is a fallback - in production you might have better logic
                const admins = await usersCollection.find({ 
                  role: { $in: ['Admin', 'Manager'] } 
                }).toArray();
                if (admins.length > 0) {
                  adminUsername = admins[0].username; // Assign to first admin/manager
                }
              }
            }
          } catch (error) {
            console.log(`⚠️  Could not find administrator for userId ${report.userId}: ${error.message}`);
          }
        }
        
        updateFields.administratorUsername = adminUsername || 'system';
        if (adminUsername) {
          console.log(`👤 Adding administrator '${adminUsername}' to report ${report._id}`);
        } else {
          console.log(`👤 Adding 'system' as administrator to report ${report._id} (no specific admin found)`);
        }
        needsUpdate = true;
      }
      
      if (needsUpdate) {
        await installationReportsCollection.updateOne(
          { _id: report._id },
          { $set: updateFields }
        );
        reportsUpdatedCount++;
      }
    }
    
    console.log(`\\n📈 Updated ${reportsUpdatedCount} installation reports`);
    
    console.log('\\n📊 PHASE 3: Update Installations Collection');
    console.log('=============================================');
    
    // Update installations collection with username and administratorUsername
    const installations = await installationsCollection.find({}).toArray();
    console.log(`Found ${installations.length} installations to potentially update`);
    
    let installationsUpdatedCount = 0;
    for (const installation of installations) {
      const updateFields = {};
      let needsUpdate = false;
      
      // Add username field if missing
      if (!installation.hasOwnProperty('username')) {
        if (installation.userId) {
          try {
            const user = await usersCollection.findOne({ _id: new ObjectId(installation.userId) });
            if (user && user.username) {
              updateFields.username = user.username;
              needsUpdate = true;
            }
          } catch (error) {
            console.log(`⚠️  Could not find user for installation userId ${installation.userId}`);
          }
        }
        
        if (!updateFields.username) {
          updateFields.username = installation.hostname || installation.clientId || 'unknown';
          needsUpdate = true;
        }
      }
      
      // Add administratorUsername field if missing
      if (!installation.hasOwnProperty('administratorUsername')) {
        let adminUsername = null;
        
        if (installation.userId) {
          try {
            const user = await usersCollection.findOne({ _id: new ObjectId(installation.userId) });
            if (user) {
              if (user.createdBy) {
                const creator = await usersCollection.findOne({ _id: new ObjectId(user.createdBy) });
                if (creator) {
                  adminUsername = creator.username;
                }
              } else if (user.role === 'User') {
                const admins = await usersCollection.find({ 
                  role: { $in: ['Admin', 'Manager'] } 
                }).toArray();
                if (admins.length > 0) {
                  adminUsername = admins[0].username;
                }
              }
            }
          } catch (error) {
            // Ignore errors
          }
        }
        
        updateFields.administratorUsername = adminUsername || 'system';
        needsUpdate = true;
      }
      
      if (needsUpdate) {
        await installationsCollection.updateOne(
          { _id: installation._id },
          { $set: updateFields }
        );
        installationsUpdatedCount++;
      }
    }
    
    console.log(`\\n📈 Updated ${installationsUpdatedCount} installations`);
    
    console.log('\\n📊 PHASE 4: Create Indexes');
    console.log('==============================');
    
    try {
      // Update users collection indexes
      await usersCollection.createIndex({ role: 1 });
      await usersCollection.createIndex({ createdBy: 1 }, { sparse: true });
      
      // Update installationReports indexes
      await installationReportsCollection.createIndex({ username: 1 });
      await installationReportsCollection.createIndex({ administratorUsername: 1 });
      await installationReportsCollection.createIndex({ username: 1, administratorUsername: 1 });
      
      // Update installations indexes  
      await installationsCollection.createIndex({ username: 1 });
      await installationsCollection.createIndex({ administratorUsername: 1 });
      await installationsCollection.createIndex({ username: 1, administratorUsername: 1 });
      
      console.log('✅ All indexes created successfully');
    } catch (indexError) {
      console.log('⚠️  Some indexes may already exist:', indexError.message);
    }
    
    console.log('\\n📋 Final Role Distribution:');
    console.log('===========================');
    
    const roleCounts = await usersCollection.aggregate([
      { $group: { _id: '$role', count: { $sum: 1 } } },
      { $sort: { _id: 1 } }
    ]).toArray();
    
    roleCounts.forEach(roleCount => {
      console.log(`${roleCount._id}: ${roleCount.count} users`);
    });
    
    console.log('\\n🏗️  Updated Schema:');
    console.log('====================');
    console.log('Users Collection:');
    console.log('- role: "Admin" | "Manager" | "User"');
    console.log('- createdBy: ObjectId (tracks who created the user)');
    console.log('');
    console.log('InstallationReports Collection:');
    console.log('- username: string (exact username from webform)');
    console.log('- administratorUsername: string (managing admin/manager)');
    console.log('');
    console.log('Installations Collection:');
    console.log('- username: string (exact username from webform)');
    console.log('- administratorUsername: string (managing admin/manager)');
    
    console.log('\\n✅ Migration completed successfully!');
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  } finally {
    await client.close();
    console.log('🔐 Database connection closed');
  }
}

// Run the migration
if (require.main === module) {
  migrateRolesAndReports()
    .then(() => {
      console.log('🎉 Role and reports migration completed');
      process.exit(0);
    })
    .catch((error) => {
      console.error('💥 Migration script failed:', error);
      process.exit(1);
    });
}

module.exports = { migrateRolesAndReports };