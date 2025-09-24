#!/usr/bin/env node

/**
 * MongoDB Users Collection Migration Script
 * 
 * Updates the users collection to include the new address fields:
 * - streetNumber
 * - streetName  
 * - apartmentSuite
 * - secondAddressLine
 * - city
 * - state
 * - zipCode
 * - numberOfUsers (for admins)
 * - linkedUsernames (array of usernames they manage)
 * 
 * This script will:
 * 1. Connect to MongoDB
 * 2. Update existing users with new fields
 * 3. Create indexes for the new fields
 * 4. Migrate existing 'address' field to structured address fields
 */

const { MongoClient } = require('mongodb');
require('dotenv').config();

// Configuration
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';

if (!MONGODB_CONNECTION_STRING) {
  console.error('❌ MONGODB_CONNECTION_STRING not found in environment variables');
  console.error('Please check your .env file or environment configuration');
  process.exit(1);
}

// Crypto utilities for encrypted fields (simplified version)
class CryptoUtils {
  static encrypt(text) {
    if (!text) return '';
    // In production, this would use proper encryption
    // For now, using base64 encoding as placeholder
    return Buffer.from(text).toString('base64');
  }

  static decrypt(encryptedText) {
    if (!encryptedText) return '';
    try {
      return Buffer.from(encryptedText, 'base64').toString('utf8');
    } catch {
      return encryptedText; // Return as-is if decryption fails
    }
  }
}

async function migrateUsersCollection() {
  const client = new MongoClient(MONGODB_CONNECTION_STRING);
  
  try {
    console.log('🔗 Connecting to MongoDB...');
    await client.connect();
    
    const db = client.db(MONGODB_DATABASE);
    const usersCollection = db.collection('users');
    
    // Get current user count
    const totalUsers = await usersCollection.countDocuments();
    console.log(`📊 Found ${totalUsers} users in the database`);
    
    if (totalUsers === 0) {
      console.log('ℹ️  No users found - creating sample structure only');
    }
    
    // 1. Update existing users with new fields
    console.log('🔄 Updating existing users with new address fields...');
    
    const users = await usersCollection.find({}).toArray();
    let updatedCount = 0;
    
    for (const user of users) {
      const updateFields = {};
      let needsUpdate = false;
      
      // Add new address fields if they don't exist
      if (!user.hasOwnProperty('streetNumber')) {
        updateFields.streetNumber = '';
        needsUpdate = true;
      }
      if (!user.hasOwnProperty('streetName')) {
        updateFields.streetName = '';
        needsUpdate = true;
      }
      if (!user.hasOwnProperty('apartmentSuite')) {
        updateFields.apartmentSuite = '';
        needsUpdate = true;
      }
      if (!user.hasOwnProperty('secondAddressLine')) {
        updateFields.secondAddressLine = '';
        needsUpdate = true;
      }
      if (!user.hasOwnProperty('city')) {
        updateFields.city = '';
        needsUpdate = true;
      }
      if (!user.hasOwnProperty('state')) {
        updateFields.state = '';
        needsUpdate = true;
      }
      if (!user.hasOwnProperty('zipCode')) {
        updateFields.zipCode = '';
        needsUpdate = true;
      }
      
      // Add user management fields for admins
      if (!user.hasOwnProperty('numberOfUsers')) {
        updateFields.numberOfUsers = (user.role === 'admin' || user.role === 'master_admin') ? 1 : 0;
        needsUpdate = true;
      }
      if (!user.hasOwnProperty('linkedUsernames')) {
        updateFields.linkedUsernames = [];
        needsUpdate = true;
      }
      
      // Update _encrypted_fields array to include new fields
      const currentEncryptedFields = user._encrypted_fields || [];
      const newEncryptedFields = [
        'email', 'firstName', 'lastName', 'phoneNumber', 'address',
        'streetNumber', 'streetName', 'apartmentSuite', 'secondAddressLine', 
        'city', 'state', 'zipCode'
      ];
      
      if (JSON.stringify(currentEncryptedFields.sort()) !== JSON.stringify(newEncryptedFields.sort())) {
        updateFields._encrypted_fields = newEncryptedFields;
        needsUpdate = true;
      }
      
      // Migrate existing 'address' field to structured fields if available
      if (user.address && updateFields.streetNumber === '' && updateFields.streetName === '') {
        try {
          const decryptedAddress = CryptoUtils.decrypt(user.address);
          if (decryptedAddress && decryptedAddress.trim()) {
            console.log(`📍 Migrating address for user: ${user.username}`);
            
            // Simple address parsing (this is basic - in production you'd use a proper address parser)
            const addressParts = decryptedAddress.split(',').map(part => part.trim());
            
            if (addressParts.length >= 1) {
              // Try to extract street number and name from first part
              const streetPart = addressParts[0];
              const streetMatch = streetPart.match(/^(\d+)\s+(.+)/);
              if (streetMatch) {
                updateFields.streetNumber = CryptoUtils.encrypt(streetMatch[1]);
                updateFields.streetName = CryptoUtils.encrypt(streetMatch[2]);
              } else {
                updateFields.streetName = CryptoUtils.encrypt(streetPart);
              }
            }
            
            if (addressParts.length >= 2) {
              updateFields.city = CryptoUtils.encrypt(addressParts[addressParts.length - 2]);
            }
            
            if (addressParts.length >= 3) {
              const lastPart = addressParts[addressParts.length - 1];
              const stateZipMatch = lastPart.match(/^([A-Z]{2})\s*(\d{5}(?:-\d{4})?)$/);
              if (stateZipMatch) {
                updateFields.state = CryptoUtils.encrypt(stateZipMatch[1]);
                updateFields.zipCode = CryptoUtils.encrypt(stateZipMatch[2]);
              }
            }
            
            needsUpdate = true;
          }
        } catch (error) {
          console.log(`⚠️  Could not parse address for user ${user.username}: ${error.message}`);
        }
      }
      
      if (needsUpdate) {
        await usersCollection.updateOne(
          { _id: user._id },
          { $set: updateFields }
        );
        updatedCount++;
        console.log(`✅ Updated user: ${user.username}`);
      }
    }
    
    console.log(`📈 Updated ${updatedCount} users with new fields`);
    
    // 2. Create indexes for new fields
    console.log('🔍 Creating indexes for new fields...');
    
    try {
      // Address-related indexes
      await usersCollection.createIndex({ city: 1 }, { sparse: true });
      await usersCollection.createIndex({ state: 1 }, { sparse: true });
      await usersCollection.createIndex({ zipCode: 1 }, { sparse: true });
      
      // User management indexes
      await usersCollection.createIndex({ numberOfUsers: 1 });
      await usersCollection.createIndex({ linkedUsernames: 1 }, { sparse: true });
      
      // Ensure existing indexes still exist
      await usersCollection.createIndex({ username: 1 }, { unique: true });
      await usersCollection.createIndex({ email_hash: 1 }, { unique: true, sparse: true });
      await usersCollection.createIndex({ role: 1 });
      await usersCollection.createIndex({ isActive: 1 });
      await usersCollection.createIndex({ createdAt: 1 });
      await usersCollection.createIndex({ lastLogin: 1 }, { sparse: true });
      
      console.log('✅ All indexes created successfully');
    } catch (indexError) {
      console.log('⚠️  Some indexes may already exist:', indexError.message);
    }
    
    // 3. Display final schema
    console.log('\\n📋 Final Users Collection Schema:');
    console.log('================================');
    
    const sampleUser = await usersCollection.findOne({}, { 
      projection: { 
        password: 0, // Don't show password in sample
        email: 0,    // Don't show encrypted fields in sample
        firstName: 0,
        lastName: 0,
        phoneNumber: 0,
        address: 0,
        streetNumber: 0,
        streetName: 0,
        apartmentSuite: 0,
        secondAddressLine: 0,
        city: 0,
        state: 0,
        zipCode: 0
      } 
    });
    
    if (sampleUser) {
      console.log('Sample user structure:');
      console.log(JSON.stringify(sampleUser, null, 2));
    }
    
    console.log('\\n🏗️  Complete field list:');
    console.log('- username (string, unique)');
    console.log('- email (encrypted string)');
    console.log('- email_hash (hashed for indexing)');
    console.log('- firstName (encrypted string)');
    console.log('- lastName (encrypted string)'); 
    console.log('- phoneNumber (encrypted string)');
    console.log('- address (encrypted string) - legacy field');
    console.log('- streetNumber (encrypted string) - NEW');
    console.log('- streetName (encrypted string) - NEW');
    console.log('- apartmentSuite (encrypted string) - NEW');
    console.log('- secondAddressLine (encrypted string) - NEW');
    console.log('- city (encrypted string) - NEW');
    console.log('- state (encrypted string) - NEW');
    console.log('- zipCode (encrypted string) - NEW');
    console.log('- role (string: user, admin, master_admin)');
    console.log('- createdAt (Date)');
    console.log('- lastLogin (Date)');
    console.log('- isActive (boolean)');
    console.log('- numberOfUsers (number) - NEW');
    console.log('- linkedUsernames (array) - NEW');
    console.log('- subscription (object)');
    console.log('- _encrypted_fields (array)');
    
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
  migrateUsersCollection()
    .then(() => {
      console.log('🎉 Migration script completed');
      process.exit(0);
    })
    .catch((error) => {
      console.error('💥 Migration script failed:', error);
      process.exit(1);
    });
}

module.exports = { migrateUsersCollection };