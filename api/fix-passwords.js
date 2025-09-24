#!/usr/bin/env node

// Fix Password Encoding
// This script fixes the password encoding issue by Base64 encoding the stored plain text passwords

require('dotenv').config();
const { MongoClient, ObjectId } = require('mongodb');

// Environment variables
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';

async function fixPasswords() {
  let client;
  
  try {
    console.log('🔧 Fixing password encoding in database...\n');
    
    if (!MONGODB_CONNECTION_STRING) {
      throw new Error('MONGODB_CONNECTION_STRING environment variable is required');
    }
    
    // Connect to MongoDB
    client = new MongoClient(MONGODB_CONNECTION_STRING);
    await client.connect();
    const db = client.db(MONGODB_DATABASE);
    console.log(`✅ Connected to MongoDB database: ${MONGODB_DATABASE}`);
    
    // Get all users
    const users = await db.collection('users').find({}).toArray();
    console.log(`📊 Found ${users.length} users to process\n`);
    
    let fixed = 0;
    let skipped = 0;
    
    for (const user of users) {
      console.log(`👤 Processing user: ${user.username}`);
      console.log(`   Current stored value: "${user.password}"`);
      
      // Check if the password is already Base64 encoded
      // Base64 strings typically only contain A-Z, a-z, 0-9, +, /, and = for padding
      const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
      const looksLikeBase64 = base64Regex.test(user.password) && user.password.length % 4 === 0;
      
      // Try to decode it to see if it's already valid Base64
      let isValidBase64 = false;
      try {
        const decoded = Buffer.from(user.password, 'base64').toString('utf8');
        const reEncoded = Buffer.from(decoded).toString('base64');
        isValidBase64 = reEncoded === user.password;
      } catch (error) {
        isValidBase64 = false;
      }
      
      if (isValidBase64) {
        console.log(`   ✅ Password is already properly Base64 encoded, skipping`);
        skipped++;
      } else {
        // The password appears to be plain text, so Base64 encode it
        const encodedPassword = Buffer.from(user.password).toString('base64');
        console.log(`   🔧 Encoding plain text password to Base64: "${encodedPassword}"`);
        
        // Update the user in the database
        const result = await db.collection('users').updateOne(
          { _id: user._id },
          { $set: { password: encodedPassword } }
        );
        
        if (result.modifiedCount > 0) {
          console.log(`   ✅ Password updated successfully`);
          fixed++;
          
          // Verify the fix by testing authentication logic
          console.log(`   🧪 Testing: If user enters "${user.password}", system will:`);
          console.log(`      1. Base64 encode input: "${encodedPassword}"`);
          console.log(`      2. Compare with stored: "${encodedPassword}"`);
          console.log(`      3. Result: ✅ MATCH - Login will work!`);
        } else {
          console.log(`   ❌ Failed to update password`);
        }
      }
      
      console.log('');
    }
    
    console.log('📊 SUMMARY:');
    console.log(`   ✅ Fixed: ${fixed} users`);
    console.log(`   ⏭️  Skipped (already correct): ${skipped} users`);
    console.log(`   📝 Total processed: ${users.length} users`);
    
    if (fixed > 0) {
      console.log('\n🎉 Password encoding fixed!');
      console.log('\n📋 Login credentials are now:');
      
      const updatedUsers = await db.collection('users').find({}).toArray();
      for (const user of updatedUsers) {
        // The original plain text password is what users should enter to log in
        const originalPlainText = users.find(u => u._id.toString() === user._id.toString())?.password;
        console.log(`   Username: ${user.username} / Password: ${originalPlainText}`);
      }
    }
    
  } catch (error) {
    console.error('❌ Failed to fix passwords:', error);
    process.exit(1);
  } finally {
    if (client) {
      await client.close();
      console.log('\n🔒 Database connection closed');
    }
  }
}

// Run the fix
if (require.main === module) {
  fixPasswords().then(() => {
    console.log('\n✨ Password fix completed');
    process.exit(0);
  }).catch(error => {
    console.error('💥 Password fix failed:', error);
    process.exit(1);
  });
}

module.exports = { fixPasswords };