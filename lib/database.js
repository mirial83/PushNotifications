const { MongoClient } = require('mongodb');
const { v4: uuidv4 } = require('uuid');

let cachedClient = null;
let cachedDb = null;

async function connectToDatabase() {
  if (cachedClient && cachedDb) {
    return { client: cachedClient, db: cachedDb };
  }

  const client = new MongoClient(process.env.MONGODB_URI);
  await client.connect();
  
  const db = client.db(process.env.DATABASE_NAME || process.env.DB_NAME || 'pushnotifications');
  
  cachedClient = client;
  cachedDb = db;
  
  return { client, db };
}

// Collection names
const COLLECTIONS = {
  NOTIFICATIONS: 'notifications',
  CLIENTS: 'clients',
  SETTINGS: 'settings',
  WEBSITE_REQUESTS: 'website_requests',
  UNINSTALL_REQUESTS: 'uninstall_requests',
  FOLDER_ACCESS_KEYS: 'folder_access_keys',
  FOLDER_ACCESS_REQUESTS: 'folder_access_requests',
  VERSION_UPDATES: 'version_updates',
  INSTALLATION_PROTECTION: 'installation_protection',
  UNAUTHORIZED_DELETIONS: 'unauthorized_deletions'
};

// Database Operations
class DatabaseOperations {
  constructor() {
    this.db = null;
  }

  async init() {
    const { db } = await connectToDatabase();
    this.db = db;
    await this.ensureIndexes();
    return this;
  }

  async ensureIndexes() {
    // Create indexes for better performance
    await this.db.collection(COLLECTIONS.NOTIFICATIONS).createIndex({ clientId: 1 });
    await this.db.collection(COLLECTIONS.NOTIFICATIONS).createIndex({ status: 1 });
    await this.db.collection(COLLECTIONS.NOTIFICATIONS).createIndex({ created: 1 });
    
    await this.db.collection(COLLECTIONS.CLIENTS).createIndex({ clientId: 1 }, { unique: true });
    
    await this.db.collection(COLLECTIONS.WEBSITE_REQUESTS).createIndex({ clientId: 1 });
    await this.db.collection(COLLECTIONS.WEBSITE_REQUESTS).createIndex({ status: 1 });
    
    await this.db.collection(COLLECTIONS.UNINSTALL_REQUESTS).createIndex({ clientId: 1 });
    await this.db.collection(COLLECTIONS.UNINSTALL_REQUESTS).createIndex({ status: 1 });
    
    await this.db.collection(COLLECTIONS.FOLDER_ACCESS_KEYS).createIndex({ clientId: 1 });
    await this.db.collection(COLLECTIONS.FOLDER_ACCESS_KEYS).createIndex({ accessKey: 1 });
    await this.db.collection(COLLECTIONS.FOLDER_ACCESS_KEYS).createIndex({ expires: 1 });
  }

  async isDatabaseInitialized() {
    try {
      const collections = await this.db.listCollections().toArray();
      const collectionNames = collections.map(c => c.name);
      
      const requiredCollections = [
        COLLECTIONS.NOTIFICATIONS,
        COLLECTIONS.CLIENTS,
        COLLECTIONS.SETTINGS
      ];
      
      return requiredCollections.every(name => collectionNames.includes(name));
    } catch (error) {
      return false;
    }
  }

  async initializeDatabase() {
    try {
      // Initialize settings with default values
      const settings = [
        {
          setting: 'preset_messages',
          value: JSON.stringify([
            {
              text: 'Do your schoolwork',
              allowedWebsites: 'drive.google.com,*.aop.com,*.yourcloudlibrary.com,*.gutenberg.org,search.google.com,*.codecademy.com',
              allowBrowserUsage: true
            },
            'Clean the kitchen',
            'Clean the living room', 
            'Empty the kitchen trash',
            'Bring the trash to the road',
            'Bring the trash down from your room',
            'Fill the dog food',
            'Take a shower'
          ]),
          description: 'Custom household task messages'
        },
        {
          setting: 'default_snooze',
          value: '15',
          description: 'Default snooze time in minutes'
        },
        {
          setting: 'max_notifications',
          value: '5',
          description: 'Maximum number of active notifications per client'
        },
        {
          setting: 'notification_timeout',
          value: '3600',
          description: 'Auto-dismiss timeout in seconds'
        },
        {
          setting: 'enable_website_blocking',
          value: 'true',
          description: 'Enable website blocking functionality'
        }
      ];

      await this.db.collection(COLLECTIONS.SETTINGS).insertMany(settings);
      
      return { success: true, message: 'Database initialized successfully' };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  // Notification Operations
  async getActiveNotifications() {
    try {
      const notifications = await this.db.collection(COLLECTIONS.NOTIFICATIONS)
        .find({ 
          status: { $ne: 'Completed' }
        })
        .sort({ priority: -1, created: 1 })
        .toArray();
      
      return { success: true, data: notifications };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async getCompletedNotifications() {
    try {
      const notifications = await this.db.collection(COLLECTIONS.NOTIFICATIONS)
        .find({ 
          status: 'Completed'
        })
        .sort({ updated: -1 })
        .toArray();
      
      return { success: true, data: notifications };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async sendNotificationToAllClients(message, allowBrowserUsage = false, allowedWebsites = '', priority = 1) {
    try {
      const clients = await this.db.collection(COLLECTIONS.CLIENTS).find({}).toArray();
      
      if (clients.length === 0) {
        return { success: true, message: 'No clients registered', clientCount: 0 };
      }

      const now = new Date();
      const notifications = [];

      for (const client of clients) {
        notifications.push({
          id: uuidv4(),
          clientId: client.clientId,
          message,
          status: 'Pending',
          created: now,
          updated: now,
          snoozeUntil: null,
          allowBrowserUsage,
          allowedWebsites,
          priority
        });
      }

      await this.db.collection(COLLECTIONS.NOTIFICATIONS).insertMany(notifications);
      
      return { 
        success: true, 
        message: `Notification sent to ${clients.length} client(s)`, 
        clientCount: clients.length 
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async getClientNotifications(clientId) {
    try {
      const now = new Date();
      const notifications = await this.db.collection(COLLECTIONS.NOTIFICATIONS)
        .find({ 
          clientId, 
          status: { $ne: 'Completed' },
          $or: [
            { snoozeUntil: null },
            { snoozeUntil: { $lte: now } }
          ]
        })
        .sort({ priority: -1, created: 1 })
        .toArray();

      const processedNotifications = notifications.map(n => ({
        id: n.id,
        message: n.message,
        status: n.status,
        allowBrowserUsage: n.allowBrowserUsage,
        allowedWebsites: n.allowedWebsites ? n.allowedWebsites.split(',').map(site => site.trim()) : [],
        priority: n.priority
      }));
      
      return { success: true, data: processedNotifications };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async updateNotificationStatus(notificationId, status, snoozeMinutes = 0) {
    try {
      const now = new Date();
      const updateData = {
        status,
        updated: now
      };

      if (snoozeMinutes > 0) {
        updateData.snoozeUntil = new Date(now.getTime() + (snoozeMinutes * 60000));
      }

      const result = await this.db.collection(COLLECTIONS.NOTIFICATIONS)
        .updateOne({ id: notificationId }, { $set: updateData });

      if (result.matchedCount === 0) {
        return { success: false, message: 'Notification not found' };
      }

      return { success: true };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  // Client Operations
  async registerClient(clientId, clientName, computerName) {
    try {
      const now = new Date();
      const result = await this.db.collection(COLLECTIONS.CLIENTS)
        .updateOne(
          { clientId },
          {
            $set: {
              clientId,
              clientName,
              lastSeen: now,
              status: 'Online',
              computerName
            }
          },
          { upsert: true }
        );

      return { 
        success: true, 
        message: result.upsertedCount > 0 ? 'Client registered' : 'Client updated' 
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async isClientAuthorized(clientId) {
    try {
      const client = await this.db.collection(COLLECTIONS.CLIENTS)
        .findOne({ clientId });
      return client !== null;
    } catch (error) {
      return false;
    }
  }

  async getClientConnectionStatus() {
    try {
      const now = new Date();
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

      const totalClients = await this.db.collection(COLLECTIONS.CLIENTS).countDocuments();
      const activeClients = await this.db.collection(COLLECTIONS.CLIENTS)
        .countDocuments({ lastSeen: { $gt: fiveMinutesAgo } });

      return {
        success: true,
        data: {
          totalClients,
          activeClients,
          hasActiveClients: activeClients > 0,
          connectionStatus: activeClients > 0 ? 'connected' : 'disconnected'
        }
      };
    } catch (error) {
      return {
        success: false,
        message: error.toString(),
        data: {
          totalClients: 0,
          activeClients: 0,
          hasActiveClients: false,
          connectionStatus: 'error'
        }
      };
    }
  }

  // Settings Operations
  async getPresetMessages() {
    try {
      const setting = await this.db.collection(COLLECTIONS.SETTINGS)
        .findOne({ setting: 'preset_messages' });

      if (setting) {
        return { success: true, data: JSON.parse(setting.value) };
      }

      // Return default messages if not found
      return {
        success: true,
        data: [
          {
            text: 'Do your schoolwork',
            allowedWebsites: 'drive.google.com,*.aop.com,*.yourcloudlibrary.com,*.gutenberg.org,search.google.com,*.codecademy.com',
            allowBrowserUsage: true
          },
          'Clean the kitchen',
          'Clean the living room',
          'Empty the kitchen trash',
          'Bring the trash to the road',
          'Bring the trash down from your room',
          'Fill the dog food',
          'Take a shower'
        ]
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  // Website Access Requests
  async requestWebsiteAccess(clientId, url, reason) {
    try {
      const requestId = uuidv4();
      const now = new Date();

      await this.db.collection(COLLECTIONS.WEBSITE_REQUESTS).insertOne({
        requestId,
        clientId,
        url,
        reason,
        status: 'Pending',
        created: now,
        reviewedBy: null
      });

      return {
        success: true,
        requestId,
        message: 'Website access request submitted. It will be reviewed via the web interface.'
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async getWebsiteAccessRequests() {
    try {
      const requests = await this.db.collection(COLLECTIONS.WEBSITE_REQUESTS)
        .find({})
        .sort({ created: -1 })
        .toArray();

      return { success: true, data: requests };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async reviewWebsiteAccessRequest(requestId, action, reviewerEmail) {
    try {
      const status = action === 'approve' ? 'Approved' : 'Denied';
      const request = await this.db.collection(COLLECTIONS.WEBSITE_REQUESTS)
        .findOne({ requestId });

      if (!request) {
        return { success: false, message: 'Request not found' };
      }

      await this.db.collection(COLLECTIONS.WEBSITE_REQUESTS)
        .updateOne(
          { requestId },
          { 
            $set: { 
              status, 
              reviewedBy: reviewerEmail 
            } 
          }
        );

      // If approved, add website to client's active notifications
      if (action === 'approve') {
        const updateResult = await this.addWebsiteToClientNotification(request.clientId, request.url);
        if (!updateResult.success) {
          console.log(`Warning: Could not add website to notification: ${updateResult.message}`);
        }
      }

      return {
        success: true,
        message: `Website access request ${status.toLowerCase()}`,
        url: request.url,
        clientId: request.clientId
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async addWebsiteToClientNotification(clientId, websiteUrl) {
    try {
      const notifications = await this.db.collection(COLLECTIONS.NOTIFICATIONS)
        .find({
          clientId,
          status: { $ne: 'Completed' },
          allowBrowserUsage: true
        })
        .toArray();

      for (const notification of notifications) {
        let websitesList = [];
        if (notification.allowedWebsites) {
          websitesList = notification.allowedWebsites.split(',').map(site => site.trim());
        }

        const cleanWebsite = websiteUrl.replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/$/, '');
        
        const isAlreadyAllowed = websitesList.some(site => {
          const cleanSite = site.replace(/^www\./, '').replace(/\/$/, '');
          return cleanSite.toLowerCase() === cleanWebsite.toLowerCase();
        });

        if (!isAlreadyAllowed) {
          websitesList.push(cleanWebsite);
          const updatedWebsites = websitesList.join(', ');
          
          await this.db.collection(COLLECTIONS.NOTIFICATIONS)
            .updateOne(
              { id: notification.id },
              { $set: { allowedWebsites: updatedWebsites } }
            );

          return {
            success: true,
            message: `Website ${cleanWebsite} added to notification whitelist`,
            updatedWebsites
          };
        }
      }

      return {
        success: false,
        message: 'No active notifications with browser usage enabled found for this client'
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  // Uninstall Operations
  async requestUninstall(clientId, reason, explanation) {
    try {
      const client = await this.db.collection(COLLECTIONS.CLIENTS)
        .findOne({ clientId });

      const requestId = uuidv4();
      const now = new Date();

      await this.db.collection(COLLECTIONS.UNINSTALL_REQUESTS).insertOne({
        requestId,
        clientId,
        clientName: client?.clientName || 'Unknown',
        computerName: client?.computerName || 'Unknown',
        reason,
        explanation,
        status: 'Pending',
        created: now,
        denialReason: null
      });

      return {
        success: true,
        requestId,
        message: 'Uninstall request submitted successfully. It will be reviewed by an administrator.'
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async getUninstallRequests() {
    try {
      const requests = await this.db.collection(COLLECTIONS.UNINSTALL_REQUESTS)
        .find({ status: 'Pending' })
        .sort({ created: -1 })
        .toArray();

      return { success: true, data: requests };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async reviewUninstallRequest(requestId, action, reviewerEmail, denialReason = '') {
    try {
      const status = action === 'approve' ? 'Approved' : 'Denied';
      const updateData = { status, reviewedBy: reviewerEmail };
      
      if (action === 'deny' && denialReason) {
        updateData.denialReason = denialReason;
      }

      const request = await this.db.collection(COLLECTIONS.UNINSTALL_REQUESTS)
        .findOne({ requestId });

      if (!request) {
        return { success: false, message: 'Request not found' };
      }

      await this.db.collection(COLLECTIONS.UNINSTALL_REQUESTS)
        .updateOne({ requestId }, { $set: updateData });

      return {
        success: true,
        message: `Uninstall request ${status.toLowerCase()} for ${request.clientName}`,
        clientId: request.clientId,
        clientName: request.clientName,
        approved: action === 'approve'
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async checkUninstallApproval(clientId) {
    try {
      const request = await this.db.collection(COLLECTIONS.UNINSTALL_REQUESTS)
        .findOne({ clientId }, { sort: { created: -1 } });

      if (!request) {
        return { success: true, approved: false, message: 'No uninstall request found.' };
      }

      if (request.status === 'Approved') {
        return {
          success: true,
          approved: true,
          message: 'Uninstall approved. Proceeding with removal.'
        };
      } else if (request.status === 'Denied') {
        return {
          success: true,
          approved: false,
          message: `Uninstall request denied: ${request.denialReason || 'No reason provided'}`
        };
      }

      return { success: true, approved: false, message: 'Uninstall request still pending.' };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  // Administrative Operations
  async clearAllNotifications() {
    try {
      const now = new Date();
      const result = await this.db.collection(COLLECTIONS.NOTIFICATIONS)
        .updateMany(
          { status: { $ne: 'Completed' } },
          { $set: { status: 'Completed', updated: now } }
        );

      return {
        success: true,
        message: `Cleared ${result.modifiedCount} notifications`,
        count: result.modifiedCount
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async uninstallAllClients() {
    try {
      const clients = await this.db.collection(COLLECTIONS.CLIENTS).find({}).toArray();
      
      if (clients.length === 0) {
        return { success: true, message: 'No clients to uninstall', count: 0 };
      }

      const now = new Date();
      const notifications = [];

      // Generate access keys and create uninstall notifications
      for (const client of clients) {
        const keyResult = await this.generateFolderAccessKey(client.clientId, 'mass_uninstall', 60);
        
        if (keyResult.success) {
          notifications.push({
            id: uuidv4(),
            clientId: client.clientId,
            message: `SYSTEM_UNINSTALL:${keyResult.accessKey}`,
            status: 'System',
            created: now,
            updated: now,
            snoozeUntil: null,
            allowBrowserUsage: false,
            allowedWebsites: '',
            priority: 10
          });
        }
      }

      if (notifications.length > 0) {
        await this.db.collection(COLLECTIONS.NOTIFICATIONS).insertMany(notifications);
      }

      return {
        success: true,
        message: `Mass uninstall initiated for ${clients.length} clients`,
        count: clients.length
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  // Folder Access Key Operations
  async generateFolderAccessKey(clientId, operation = 'uninstall', durationMinutes = 30) {
    try {
      const keyId = uuidv4();
      const accessKey = uuidv4() + '-' + uuidv4();
      const now = new Date();
      const expires = new Date(now.getTime() + (durationMinutes * 60000));

      await this.db.collection(COLLECTIONS.FOLDER_ACCESS_KEYS).insertOne({
        keyId,
        clientId,
        accessKey,
        operation,
        created: now,
        expires,
        used: false
      });

      return {
        success: true,
        keyId,
        accessKey,
        expires,
        message: `Folder access key generated for ${operation} operation`
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  async validateFolderAccessKey(clientId, accessKey, operation = 'uninstall') {
    try {
      const now = new Date();
      const key = await this.db.collection(COLLECTIONS.FOLDER_ACCESS_KEYS)
        .findOne({
          clientId,
          accessKey,
          operation,
          used: false,
          expires: { $gt: now }
        });

      if (!key) {
        return { success: false, message: 'Invalid, expired, or already used access key' };
      }

      // Mark key as used
      await this.db.collection(COLLECTIONS.FOLDER_ACCESS_KEYS)
        .updateOne(
          { keyId: key.keyId },
          { $set: { used: true } }
        );

      return {
        success: true,
        message: 'Access key validated successfully',
        keyId: key.keyId
      };
    } catch (error) {
      return { success: false, message: error.toString() };
    }
  }

  // Version Management
  async getVersionInfo() {
    try {
      return {
        success: true,
        currentVersion: process.env.CLIENT_VERSION || '2.1.0',
        latestVersion: process.env.CLIENT_VERSION || '2.1.0',
        releaseNotes: 'MongoDB/Vercel version with enhanced security',
        updateAvailable: false,
        autoUpdateEnabled: process.env.AUTO_UPDATE_ENABLED === 'true',
        forceUpdate: process.env.FORCE_UPDATE === 'true',
        downloadUrl: '/api/download?file=client',
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        success: false,
        currentVersion: '2.1.0',
        latestVersion: '2.1.0',
        updateAvailable: false,
        error: 'Failed to check for updates: ' + error.toString()
      };
    }
  }
}

module.exports = { DatabaseOperations, COLLECTIONS };
