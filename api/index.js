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

      await this.db.collection('settings').insertMany(settings);
      return { success: true, message: 'MongoDB database initialized successfully' };
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

  async sendNotificationToAllClients(message, allowBrowserUsage = false, allowedWebsites = '', priority = 1) {
    try {
      const notification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        message,
        clientId: 'all',
        status: 'Active',
        allowBrowserUsage,
        allowedWebsites,
        priority,
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
        allowedWebsites: n.allowedWebsites ? n.allowedWebsites.split(',') : [],
        priority: n.priority || 1
      }));

      return { success: true, data: processedNotifications };
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
        const priority = parseInt(params.priority || '1');
        result = await db.sendNotificationToAllClients(
          params.message || '',
          allowBrowserUsage,
          allowedWebsites,
          priority
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
