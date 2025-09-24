#!/usr/bin/env node

// User Schema Migration Script
// This script updates the user collection to include all required encrypted personal information fields
// Fields added in order: email, password, streetNumber, streetName, apartmentSuite, secondLine, city, state, zipCode, phoneNumber

require('dotenv').config();
const { MongoClient, ObjectId } = require('mongodb');
const crypto = require('crypto');

// Environment variables
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'pushnotifications-encryption-key-32chars';

// Encryption constants (same as main API)
const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;
const SALT_LENGTH = 64;
const TAG_LENGTH = 16;
const KEY_LENGTH = 32;

// Encryption utility functions (same as main API)
class CryptoUtils {
  static deriveKey(password, salt) {
    return crypto.pbkdf2Sync(password, salt, 100000, KEY_LENGTH, 'sha256');
  }

  static encrypt(text) {
    try {
      if (!text || typeof text !== 'string') {
        return null;
      }
      
      const salt = crypto.randomBytes(SALT_LENGTH);
      const iv = crypto.randomBytes(IV_LENGTH);
      const key = this.deriveKey(ENCRYPTION_KEY, salt);
      
      const cipher = crypto.createCipherGCM(ALGORITHM, key, iv);
      cipher.setAAD(Buffer.from('pushnotifications'));
      
      let encrypted = cipher.update(text, 'utf8', 'hex');
      encrypted += cipher.final('hex');
      
      const authTag = cipher.getAuthTag();
      
      // Combine salt + iv + authTag + encrypted
      const combined = salt.toString('hex') + iv.toString('hex') + authTag.toString('hex') + encrypted;
      return combined;
    } catch (error) {
      console.error('Encryption error:', error);
      return null;
    }
  }

  static decrypt(encryptedData) {
    try {
      if (!encryptedData || typeof encryptedData !== 'string') {
        return null;
      }
      
      // Extract components
      const saltHex = encryptedData.substr(0, SALT_LENGTH * 2);
      const ivHex = encryptedData.substr(SALT_LENGTH * 2, IV_LENGTH * 2);
      const authTagHex = encryptedData.substr((SALT_LENGTH + IV_LENGTH) * 2, TAG_LENGTH * 2);
      const encrypted = encryptedData.substr((SALT_LENGTH + IV_LENGTH + TAG_LENGTH) * 2);
      
      const salt = Buffer.from(saltHex, 'hex');
      const iv = Buffer.from(ivHex, 'hex');
      const authTag = Buffer.from(authTagHex, 'hex');
      const key = this.deriveKey(ENCRYPTION_KEY, salt);
      
      const decipher = crypto.createDecipherGCM(ALGORITHM, key, iv);
      decipher.setAuthTag(authTag);
      decipher.setAAD(Buffer.from('pushnotifications'));
      
      let decrypted = decipher.update(encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      
      return decrypted;
    } catch (error) {
      console.error('Decryption error:', error);
      return null;
    }
  }

  static hashSensitiveData(data) {
    return crypto.createHash('sha256').update(data + ENCRYPTION_KEY).digest('hex');
  }
}

async function migrateUserSchema() {
  let client;
  
  try {
    console.log('🚀 Starting User Schema Migration...\n');
    
    if (!MONGODB_CONNECTION_STRING) {
      throw new Error('MONGODB_CONNECTION_STRING environment variable is required');
    }
    
    // Connect to MongoDB
    client = new MongoClient(MONGODB_CONNECTION_STRING);
    await client.connect();
    const db = client.db(MONGODB_DATABASE);
    console.log(`✅ Connected to MongoDB database: ${MONGODB_DATABASE}`);
    
    // Get users collection
    const usersCollection = db.collection('users');
    
    // Get all users
    const users = await usersCollection.find({}).toArray();
    console.log(`📊 Found ${users.length} users to migrate`);
    
    if (users.length === 0) {
      console.log('✅ No users found to migrate');
      return;
    }
    
    let migrated = 0;
    let skipped = 0;
    let errors = 0;
    
    console.log('\n🔄 Processing users...');
    
    for (const user of users) {
      try {
        console.log(`\n👤 Processing user: ${user.username} (${user._id})`);
        
        // Build the update object with all required encrypted fields in the specified order
        const updateData = {
          $set: {},
          $addToSet: {}
        };
        
        let needsUpdate = false;
        
        // Required fields in the specified order:
        // email, password, streetNumber, streetName, apartmentSuite, secondLine, city, state, zipCode, phoneNumber
        
        // 1. Email - already exists but ensure it's encrypted
        if (user.email && !user.email.includes('pushnotifications')) {
          // Email is not encrypted yet, encrypt it
          updateData.$set.email = CryptoUtils.encrypt(user.email);
          updateData.$set.email_hash = CryptoUtils.hashSensitiveData(user.email);
          needsUpdate = true;
          console.log('   📧 Email will be encrypted');
        }
        
        // 2. Password - already exists and is hashed, no changes needed
        // Password is already Base64 encoded, which is fine
        
        // 3. Street Number - new field
        if (!user.streetNumber) {
          updateData.$set.streetNumber = '';
          needsUpdate = true;
          console.log('   🏠 Adding streetNumber field');
        }
        
        // 4. Street Name - new field  
        if (!user.streetName) {
          updateData.$set.streetName = '';
          needsUpdate = true;
          console.log('   🛣️  Adding streetName field');
        }
        
        // 5. Apartment/Suite - already exists as apartmentSuite
        if (!user.apartmentSuite) {
          updateData.$set.apartmentSuite = '';
          needsUpdate = true;
          console.log('   🏢 Adding apartmentSuite field');
        }
        
        // 6. Second Line - new field (different from secondAddressLine)
        if (!user.secondLine) {
          updateData.$set.secondLine = '';
          needsUpdate = true;
          console.log('   📄 Adding secondLine field');
        }
        
        // 7. City - already exists
        if (!user.city) {
          updateData.$set.city = '';
          needsUpdate = true;
          console.log('   🏙️  Adding city field');
        }
        
        // 8. State - already exists
        if (!user.state) {
          updateData.$set.state = '';
          needsUpdate = true;
          console.log('   🗺️  Adding state field');
        }
        
        // 9. Zip Code - already exists as zipCode
        if (!user.zipCode) {
          updateData.$set.zipCode = '';
          needsUpdate = true;
          console.log('   📮 Adding zipCode field');
        }
        
        // 10. Phone Number - already exists as phoneNumber
        if (!user.phoneNumber) {
          updateData.$set.phoneNumber = '';
          needsUpdate = true;
          console.log('   📞 Adding phoneNumber field');
        }
        
        // Update the _encrypted_fields array to include all encrypted fields in the correct order
        const requiredEncryptedFields = [
          'email', 'streetNumber', 'streetName', 'apartmentSuite', 'secondLine', 
          'city', 'state', 'zipCode', 'phoneNumber'
        ];
        
        // Add any missing encrypted fields to the array
        const existingEncryptedFields = user._encrypted_fields || [];
        const missingFields = requiredEncryptedFields.filter(field => 
          !existingEncryptedFields.includes(field)
        );
        
        if (missingFields.length > 0) {
          updateData.$addToSet._encrypted_fields = { $each: missingFields };
          needsUpdate = true;
          console.log(`   🔐 Adding ${missingFields.length} fields to encrypted fields list: ${missingFields.join(', ')}`);
        }
        
        // Update migration timestamp
        updateData.$set.schemaVersion = '2.0';
        updateData.$set.lastMigrated = new Date();
        updateData.$set.migrationNotes = 'User schema updated with all required encrypted personal information fields';
        
        if (needsUpdate) {
          // Perform the update
          const result = await usersCollection.updateOne(
            { _id: user._id },
            updateData
          );
          
          if (result.modifiedCount > 0) {
            migrated++;
            console.log(`   ✅ User migrated successfully`);
          } else {
            console.log(`   ⚠️  User update had no effect`);
          }
        } else {
          skipped++;
          console.log(`   ⏭️  User already up to date, skipping`);
        }
        
      } catch (error) {
        errors++;
        console.error(`   ❌ Error migrating user ${user.username}:`, error.message);
      }
    }
    
    // Create indexes for the new fields
    console.log('\n🗂️  Creating indexes for new fields...');
    try {
      // Index for email hash (for lookups)
      await usersCollection.createIndex({ email_hash: 1 }, { sparse: true });
      console.log('   ✅ Created index on email_hash');
      
      // Index for schema version
      await usersCollection.createIndex({ schemaVersion: 1 }, { sparse: true });
      console.log('   ✅ Created index on schemaVersion');
      
      // Compound index for username and role
      await usersCollection.createIndex({ username: 1, role: 1 });
      console.log('   ✅ Created compound index on username and role');
      
    } catch (indexError) {
      console.log('   ⚠️  Some indexes may already exist:', indexError.message);
    }
    
    // Summary
    console.log('\n📊 MIGRATION SUMMARY:');
    console.log(`   Total users: ${users.length}`);
    console.log(`   ✅ Successfully migrated: ${migrated}`);
    console.log(`   ⏭️  Skipped (already up to date): ${skipped}`);
    console.log(`   ❌ Errors: ${errors}`);
    
    if (errors === 0) {
      console.log('\n🎉 User schema migration completed successfully!');
    } else {
      console.log(`\n⚠️  User schema migration completed with ${errors} error(s).`);
    }
    
    console.log('\n📋 All users now have the following encrypted fields in order:');
    console.log('   1. email (encrypted)');
    console.log('   2. password (hashed)');
    console.log('   3. streetNumber (encrypted)');
    console.log('   4. streetName (encrypted)');
    console.log('   5. apartmentSuite (encrypted)');
    console.log('   6. secondLine (encrypted)');
    console.log('   7. city (encrypted)');
    console.log('   8. state (encrypted)');
    console.log('   9. zipCode (encrypted)');
    console.log('   10. phoneNumber (encrypted)');
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  } finally {
    if (client) {
      await client.close();
      console.log('\n🔒 Database connection closed');
    }
  }
}

// Run the migration
if (require.main === module) {
  migrateUserSchema().then(() => {
    console.log('\n✨ Migration script completed');
    process.exit(0);
  }).catch(error => {
    console.error('💥 Migration script failed:', error);
    process.exit(1);
  });
}

module.exports = { migrateUserSchema, CryptoUtils };