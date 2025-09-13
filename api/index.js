// PushNotifications Node.js API
import { MongoClient } from 'mongodb';

// Environment variables
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';

// In-memory fallback storage
let fallbackStorage = {
  settings: [
    {
      setting: 'preset_messages',
      value: JSON.stringify([
        'Do your schoolwork',
        'Clean your room',
        'Take out the trash',
        'Walk the dog',
        'Do the dishes'
      ]),
      description: 'Preset notification messages',
      created: new Date().toISOString()
    },
    {
      setting: 'default_snooze',
      value: '15',
      description: 'Default snooze time in minutes',
      created: new Date().toISOString()
    },
    {
      setting: 'max_notifications',
      value: '5',
      description: 'Maximum number of active notifications per client',
      created: new Date().toISOString()
    }
  ],
  notifications: [],
  clients: []
};

// Database operations class
class DatabaseOperations {
  constructor() {
    this.client = null;
    this.db = null;
    this.usesFallback = !MONGODB_CONNECTION_STRING;
  }

  async connect() {
    if (this.usesFallback) {
      return true;
    }

    try {
      if (!this.client) {
        this.client = new MongoClient(MONGODB_CONNECTION_STRING);
        await this.client.connect();
        this.db = this.client.db(MONGODB_DATABASE);
      }
      return true;
    } catch (error) {
      console.error('MongoDB connection failed:', error);
      this.usesFallback = true;
      return false;
    }
  }

  async testConnection() {
    try {
      const result = {
        success: true,
        timestamp: new Date().toISOString(),
        mongodb_configured: !!MONGODB_CONNECTION_STRING,
        using_fallback: this.usesFallback
      };

      if (!this.usesFallback) {
        await this.connect();
        // Test MongoDB connection
        try {
          await this.db.collection('test').findOne({});
          result.message = 'MongoDB connection successful';
          result.mongodb_status = 'connected';
          result.database_name = MONGODB_DATABASE;
        } catch (error) {
          result.message = 'MongoDB connection failed, using fallback storage';
          result.mongodb_status = 'failed';
          result.mongodb_error = error.message;
          this.usesFallback = true;
        }
      } else {
        result.message = 'Using in-memory storage - MongoDB not configured';
        result.mongodb_status = 'not_configured';
      }

      return result;
    } catch (error) {
      return {
        success: false,
        message: 'Connection test failed: ' + error.message
      };
    }
  }

  async isDatabaseInitialized() {
    try {
      if (this.usesFallback) {
        const initialized = fallbackStorage.settings.length > 0;
        return { success: true, initialized };
      }

      await this.connect();
      const settings = await this.db.collection('settings').findOne({ setting: 'preset_messages' });
      return { success: true, initialized: !!settings };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async initializeDatabase() {
    try {
      if (this.usesFallback) {
        // Fallback storage is already initialized
        return { success: true, message: 'In-memory database initialized successfully' };
      }

      await this.connect();
      
      // Initialize settings
      const settings = [
        {
          setting: 'preset_messages',
          value: JSON.stringify([
            'Do your schoolwork',
            'Clean your room',
            'Take out the trash',
            'Walk the dog',
            'Do the dishes'
          ]),
          description: 'Preset notification messages',
          created: new Date().toISOString()
        },
        {
          setting: 'default_snooze',
          value: '15',
          description: 'Default snooze time in minutes',
          created: new Date().toISOString()
        },
        {
          setting: 'max_notifications',
          value: '5',
          description: 'Maximum number of active notifications per client',
          created: new Date().toISOString()
        }
      ];

      // Check if settings already exist to avoid duplicates
      const existingSettings = await this.db.collection('settings').findOne({ setting: 'preset_messages' });
      if (!existingSettings) {
        await this.db.collection('settings').insertMany(settings);
      }

      // Create indexes for security collections
      try {
        // Security Keys collection indexes
        await this.db.collection('securityKeys').createIndex({ clientId: 1, keyType: 1 }, { unique: true });
        await this.db.collection('securityKeys').createIndex({ hostname: 1 });
        await this.db.collection('securityKeys').createIndex({ createdAt: -1 });
        await this.db.collection('securityKeys').createIndex({ lastUsed: -1 });

        // Client Info collection indexes
        await this.db.collection('clientInfo').createIndex({ clientId: 1 }, { unique: true });
        await this.db.collection('clientInfo').createIndex({ machineId: 1 });
        await this.db.collection('clientInfo').createIndex({ hostname: 1 });
        await this.db.collection('clientInfo').createIndex({ installPath: 1 });
        await this.db.collection('clientInfo').createIndex({ createdAt: -1 });
        await this.db.collection('clientInfo').createIndex({ lastCheckin: -1 });

        // Notification collection indexes (if not already created)
        await this.db.collection('notifications').createIndex({ status: 1 });
        await this.db.collection('notifications').createIndex({ clientId: 1 });
        await this.db.collection('notifications').createIndex({ created: -1 });

        console.log('Database indexes created successfully');
      } catch (indexError) {
        // Indexes might already exist, which is fine
        console.log('Some indexes may already exist:', indexError.message);
      }

      return { success: true, message: 'MongoDB database and security collections initialized successfully' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getVersionInfo() {
    return {
      success: true,
      currentVersion: '2.1.0',
      latestVersion: '2.1.0',
      releaseNotes: 'Node.js/MongoDB/Vercel version with enhanced reliability',
      updateAvailable: false,
      autoUpdateEnabled: true,
      forceUpdate: false,
      downloadUrl: '/api/download?file=client',
      timestamp: new Date().toISOString()
    };
  }

  async registerClient(clientId, clientName, computerName) {
    try {
      const client = {
        clientId,
        clientName,
        computerName,
        registered: new Date().toISOString(),
        lastSeen: new Date().toISOString()
      };

      if (this.usesFallback) {
        fallbackStorage.clients.push(client);
      } else {
        await this.connect();
        await this.db.collection('clients').insertOne(client);
      }

      return { success: true, message: 'Client registered' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async sendNotificationToAllClients(message, allowBrowserUsage = false, allowedWebsites = '') {
    try {
      const notification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        message,
        clientId: 'all',
        status: 'Active',
        allowBrowserUsage,
        allowedWebsites,
        created: new Date().toISOString()
      };

      if (this.usesFallback) {
        fallbackStorage.notifications.push(notification);
      } else {
        await this.connect();
        await this.db.collection('notifications').insertOne(notification);
      }

      const clientCount = this.usesFallback 
        ? fallbackStorage.clients.length 
        : await this.db.collection('clients').countDocuments();

      return {
        success: true,
        message: 'Notification sent to all clients',
        clientCount
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getActiveNotifications() {
    try {
      let notifications;
      
      if (this.usesFallback) {
        notifications = fallbackStorage.notifications.filter(n => n.status !== 'Completed');
      } else {
        await this.connect();
        notifications = await this.db.collection('notifications')
          .find({ status: { $ne: 'Completed' } })
          .toArray();
      }

      return { success: true, data: notifications };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getClientNotifications(clientId) {
    try {
      let notifications;
      
      if (this.usesFallback) {
        notifications = fallbackStorage.notifications.filter(n => 
          (n.clientId === clientId || n.clientId === 'all') && n.status !== 'Completed'
        );
      } else {
        await this.connect();
        notifications = await this.db.collection('notifications')
          .find({ 
            $and: [
              { $or: [{ clientId }, { clientId: 'all' }] },
              { status: { $ne: 'Completed' } }
            ]
          })
          .toArray();
      }

      const processedNotifications = notifications.map(n => ({
        id: n.id || n._id?.toString(),
        message: n.message,
        status: n.status,
        allowBrowserUsage: n.allowBrowserUsage || false,
        allowedWebsites: n.allowedWebsites ? n.allowedWebsites.split(',') : []
      }));

      return { success: true, data: processedNotifications };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Security Key Management Methods
  async getSecurityKey(clientId, keyType) {
    try {
      if (this.usesFallback) {
        // In-memory fallback - generate a temporary key
        const key = 'fallback_key_' + Math.random().toString(36).substr(2, 16);
        return { success: true, key };
      }

      await this.connect();
      const securityKey = await this.db.collection('securityKeys').findOne({
        clientId,
        keyType
      });

      if (securityKey) {
        // Update last used timestamp
        await this.db.collection('securityKeys').updateOne(
          { _id: securityKey._id },
          { $set: { lastUsed: new Date() } }
        );
        
        return { success: true, key: securityKey.keyValue };
      } else {
        return { success: false, message: 'Security key not found' };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async createSecurityKey(clientId, keyType, keyValue, installPath, hostname) {
    try {
      if (this.usesFallback) {
        // In-memory fallback - just acknowledge creation
        return { success: true, message: 'Security key created in memory' };
      }

      await this.connect();
      const securityKeyData = {
        clientId,
        keyType,
        keyValue,
        installPath,
        hostname,
        createdAt: new Date(),
        lastUsed: new Date()
      };

      // Check if key already exists
      const existingKey = await this.db.collection('securityKeys').findOne({
        clientId,
        keyType
      });

      if (existingKey) {
        // Update existing key
        await this.db.collection('securityKeys').updateOne(
          { _id: existingKey._id },
          { 
            $set: { 
              keyValue,
              lastUsed: new Date(),
              updatedAt: new Date()
            }
          }
        );
        return { success: true, message: 'Security key updated' };
      } else {
        // Insert new key
        await this.db.collection('securityKeys').insertOne(securityKeyData);
        return { success: true, message: 'Security key created' };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async updateKeyLastUsed(clientId, keyType) {
    try {
      if (this.usesFallback) {
        return { success: true, message: 'Key usage updated in memory' };
      }

      await this.connect();
      const result = await this.db.collection('securityKeys').updateOne(
        { clientId, keyType },
        { $set: { lastUsed: new Date() } }
      );

      return { 
        success: true, 
        message: 'Key last used timestamp updated',
        updated: result.modifiedCount > 0
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Client Info Management Methods
  async getClientInfo(machineId, installPath, hostname) {
    try {
      if (this.usesFallback) {
        // In-memory fallback - find by hostname
        const client = fallbackStorage.clients.find(c => 
          c.computerName === hostname || c.clientName === hostname
        );
        if (client) {
          return { success: true, clientId: client.clientId };
        }
        return { success: false, message: 'Client not found' };
      }

      await this.connect();
      const clientInfo = await this.db.collection('clientInfo').findOne({
        $or: [
          { machineId },
          { hostname },
          { installPath }
        ]
      });

      if (clientInfo) {
        return { success: true, clientId: clientInfo.clientId };
      } else {
        return { success: false, message: 'Client info not found' };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async createClientInfo(clientId, machineId, installationId, installPath, hostname, platform, version) {
    try {
      if (this.usesFallback) {
        // In-memory fallback
        const clientData = {
          clientId,
          clientName: hostname,
          computerName: hostname,
          registered: new Date().toISOString(),
          lastSeen: new Date().toISOString()
        };
        fallbackStorage.clients.push(clientData);
        return { success: true, message: 'Client registered in memory' };
      }

      await this.connect();
      const clientInfoData = {
        clientId,
        machineId,
        installationId,
        installPath,
        hostname,
        platform,
        version,
        createdAt: new Date(),
        lastCheckin: new Date()
      };

      // Check if client already exists
      const existingClient = await this.db.collection('clientInfo').findOne({
        $or: [
          { clientId },
          { machineId },
          { installPath }
        ]
      });

      if (existingClient) {
        // Update existing client
        await this.db.collection('clientInfo').updateOne(
          { _id: existingClient._id },
          { 
            $set: { 
              version,
              lastCheckin: new Date(),
              updatedAt: new Date()
            }
          }
        );
        return { success: true, message: 'Client info updated' };
      } else {
        // Insert new client
        await this.db.collection('clientInfo').insertOne(clientInfoData);
        return { success: true, message: 'Client info created' };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async updateClientCheckin(clientId, version) {
    try {
      if (this.usesFallback) {
        // Update in-memory client
        const client = fallbackStorage.clients.find(c => c.clientId === clientId);
        if (client) {
          client.lastSeen = new Date().toISOString();
        }
        return { success: true, message: 'Client checkin updated in memory' };
      }

      await this.connect();
      const result = await this.db.collection('clientInfo').updateOne(
        { clientId },
        { 
          $set: { 
            lastCheckin: new Date(),
            version: version || 'unknown'
          }
        }
      );

      return { 
        success: true, 
        message: 'Client checkin updated',
        updated: result.modifiedCount > 0
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getAllSecurityKeys() {
    try {
      if (this.usesFallback) {
        return { success: true, data: [] };
      }

      await this.connect();
      const keys = await this.db.collection('securityKeys')
        .find({})
        .sort({ createdAt: -1 })
        .toArray();

      // Don't return actual key values for security
      const processedKeys = keys.map(key => ({
        _id: key._id.toString(),
        clientId: key.clientId,
        keyType: key.keyType,
        hostname: key.hostname,
        installPath: key.installPath,
        createdAt: key.createdAt,
        lastUsed: key.lastUsed
      }));

      return { success: true, data: processedKeys };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getAllClientInfo() {
    try {
      if (this.usesFallback) {
        return { success: true, data: fallbackStorage.clients };
      }

      await this.connect();
      const clients = await this.db.collection('clientInfo')
        .find({})
        .sort({ createdAt: -1 })
        .toArray();

      const processedClients = clients.map(client => ({
        _id: client._id.toString(),
        clientId: client.clientId,
        hostname: client.hostname,
        platform: client.platform,
        version: client.version,
        installPath: client.installPath,
        createdAt: client.createdAt,
        lastCheckin: client.lastCheckin
      }));

      return { success: true, data: processedClients };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async close() {
    if (this.client) {
      await this.client.close();
    }
  }
}

// Main API handler
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-User-Email');

  // Handle OPTIONS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const db = new DatabaseOperations();
    let action, params;

    // Get action and params
    if (req.method === 'GET') {
      action = req.query.action || '';
      params = req.query;
    } else {
      action = req.body?.action || '';
      params = req.body || {};
    }

    // Debug info if no action
    if (!action) {
      return res.status(200).json({
        success: false,
        message: 'No action specified',
        available_actions: [
          'testConnection',
          'isDatabaseInitialized',
          'initializeDatabase',
          'getActiveNotifications',
          'registerClient',
          'sendNotificationToAllClients',
          'get_version'
        ],
        debug: {
          method: req.method,
          body: req.body,
          query: req.query,
          timestamp: new Date().toISOString()
        }
      });
    }

    let result = { success: false, message: 'Unknown action: ' + action };

    // Handle actions
    switch (action) {
      case 'testConnection':
        result = await db.testConnection();
        break;

      case 'get_version':
        result = await db.getVersionInfo();
        break;

      case 'isDatabaseInitialized':
        result = await db.isDatabaseInitialized();
        break;

      case 'initializeDatabase':
        result = await db.initializeDatabase();
        break;

      case 'registerClient':
        result = await db.registerClient(
          params.clientId || '',
          params.clientName || '',
          params.computerName || ''
        );
        break;

      case 'sendNotificationToAllClients':
      case 'sendNotification':
        const allowBrowserUsage = params.allowBrowserUsage === 'true' || params.allowBrowserUsage === true;
        let allowedWebsites = params.allowedWebsites || '';
        if (Array.isArray(allowedWebsites)) {
          allowedWebsites = allowedWebsites.filter(Boolean).join(',');
        }
        result = await db.sendNotificationToAllClients(
          params.message || '',
          allowBrowserUsage,
          allowedWebsites
        );
        break;

      case 'getActiveNotifications':
      case 'getNotifications':
        result = await db.getActiveNotifications();
        if (result.success) {
          result.notifications = result.data;
          result.clientCount = 0;
        }
        break;

      case 'getClientNotifications':
        result = await db.getClientNotifications(params.clientId || '');
        break;

      // Security Key Management Actions
      case 'getSecurityKey':
        result = await db.getSecurityKey(
          params.clientId || '',
          params.keyType || 'ENCRYPTION_KEY'
        );
        break;

      case 'createSecurityKey':
        result = await db.createSecurityKey(
          params.clientId || '',
          params.keyType || 'ENCRYPTION_KEY',
          params.keyValue || '',
          params.installPath || '',
          params.hostname || ''
        );
        break;

      case 'updateKeyLastUsed':
        result = await db.updateKeyLastUsed(
          params.clientId || '',
          params.keyType || 'ENCRYPTION_KEY'
        );
        break;

      // Client Info Management Actions
      case 'getClientInfo':
        result = await db.getClientInfo(
          params.machineId || '',
          params.installPath || '',
          params.hostname || ''
        );
        break;

      case 'createClientInfo':
        result = await db.createClientInfo(
          params.clientId || '',
          params.machineId || '',
          params.installationId || '',
          params.installPath || '',
          params.hostname || '',
          params.platform || '',
          params.version || ''
        );
        break;

      case 'updateClientCheckin':
        result = await db.updateClientCheckin(
          params.clientId || '',
          params.version || ''
        );
        break;

      // Security Management Dashboard Actions
      case 'getAllSecurityKeys':
        result = await db.getAllSecurityKeys();
        break;

      case 'getAllClientInfo':
        result = await db.getAllClientInfo();
        break;
    }

    await db.close();
    return res.status(200).json(result);

  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({
      success: false,
      message: 'API Error: ' + error.message,
      debug: {
        error: error.message,
        stack: error.stack
      }
    });
  }
}
