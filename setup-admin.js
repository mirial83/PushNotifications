// Setup script to create admin user for PushNotifications
import { MongoClient } from 'mongodb';
import crypto from 'crypto';

// Environment variables
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';

// Admin user credentials
const ADMIN_USERNAME = 'doldarina1';
const ADMIN_EMAIL = 'admin@pushnotifications.local';
const ADMIN_PASSWORD = 'K@7j@B3l13!';

async function createAdminUser() {
    console.log('🔧 Setting up PushNotifications admin user...');
    
    // Check if MongoDB connection string is available
    if (!MONGODB_CONNECTION_STRING) {
        console.error('❌ Error: MONGODB_CONNECTION_STRING environment variable not set.');
        console.log('💡 This script requires a MongoDB connection to create the admin user.');
        console.log('   If you\'re using local development, the fallback storage won\'t work for user management.');
        return;
    }

    let client;
    try {
        // Connect to MongoDB
        console.log('🔗 Connecting to MongoDB...');
        client = new MongoClient(MONGODB_CONNECTION_STRING);
        await client.connect();
        const db = client.db(MONGODB_DATABASE);

        // Check if admin user already exists
        console.log('🔍 Checking if admin user already exists...');
        const existingUser = await db.collection('users').findOne({
            $or: [
                { username: ADMIN_USERNAME },
                { email: ADMIN_EMAIL }
            ]
        });

        if (existingUser) {
            console.log('✅ Admin user already exists!');
            console.log(`   Username: ${existingUser.username}`);
            console.log(`   Email: ${existingUser.email}`);
            console.log(`   Role: ${existingUser.role}`);
            console.log(`   Active: ${existingUser.isActive}`);
            console.log(`   Created: ${existingUser.createdAt}`);
            return;
        }

        // Create admin user
        console.log('👨‍💼 Creating admin user...');
        
        // Hash password (same method as in the API)
        const hashedPassword = Buffer.from(ADMIN_PASSWORD).toString('base64');
        
        const userData = {
            username: ADMIN_USERNAME,
            email: ADMIN_EMAIL,
            password: hashedPassword,
            role: 'admin',
            createdAt: new Date(),
            lastLogin: null,
            isActive: true
        };

        const result = await db.collection('users').insertOne(userData);
        
        if (result.insertedId) {
            console.log('✅ Admin user created successfully!');
            console.log('📋 Admin User Details:');
            console.log(`   Username: ${ADMIN_USERNAME}`);
            console.log(`   Email: ${ADMIN_EMAIL}`);
            console.log(`   Role: admin`);
            console.log(`   User ID: ${result.insertedId}`);
            console.log(`   Created: ${userData.createdAt}`);
            console.log('');
            console.log('🔐 Login Credentials:');
            console.log(`   Username: ${ADMIN_USERNAME}`);
            console.log(`   Password: ${ADMIN_PASSWORD}`);
            console.log('');
            console.log('🎉 You can now log in to the admin panel with these credentials!');
        } else {
            console.error('❌ Failed to create admin user - no inserted ID returned');
        }

    } catch (error) {
        console.error('❌ Error setting up admin user:', error);
        console.error('   Error details:', error.message);
    } finally {
        if (client) {
            await client.close();
            console.log('🔌 Database connection closed.');
        }
    }
}

// Alternative method: Create user via API call (if MongoDB is not directly accessible)
async function createAdminUserViaAPI() {
    console.log('🌐 Attempting to create admin user via API...');
    
    try {
        const response = await fetch('/api/index', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'createUser',
                username: ADMIN_USERNAME,
                email: ADMIN_EMAIL,
                password: ADMIN_PASSWORD,
                role: 'admin'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ Admin user created successfully via API!');
            console.log(`   User ID: ${result.userId}`);
        } else {
            console.error('❌ Failed to create admin user via API:', result.message);
        }
    } catch (error) {
        console.error('❌ Error creating admin user via API:', error);
    }
}

// Run the setup
if (process.argv[1].endsWith('setup-admin.js')) {
    // Check if we should try API method
    if (process.argv.includes('--api')) {
        createAdminUserViaAPI();
    } else {
        createAdminUser();
    }
}

export { createAdminUser, createAdminUserViaAPI };
