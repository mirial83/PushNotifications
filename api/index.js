// PushNotifications Node.js API
import { MongoClient, ObjectId } from 'mongodb';
import crypto from 'crypto';

// Environment variables
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';
const JWT_SECRET = process.env.JWT_SECRET || 'pushnotifications-secret-key';
const SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours

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
        await this.db.collection('securityKeys').createIndex({ macAddress: 1 });
        await this.db.collection('securityKeys').createIndex({ hostname: 1 });
        await this.db.collection('securityKeys').createIndex({ createdAt: -1 });
        await this.db.collection('securityKeys').createIndex({ lastUsed: -1 });

        // MAC-based Client Management collection indexes
        await this.db.collection('macClients').createIndex({ macAddress: 1 }, { unique: true });
        await this.db.collection('macClients').createIndex({ activeClientId: 1 });
        await this.db.collection('macClients').createIndex({ createdAt: -1 });
        await this.db.collection('macClients').createIndex({ lastCheckin: -1 });

        // Client Installation History collection indexes
        await this.db.collection('clientHistory').createIndex({ macAddress: 1 });
        await this.db.collection('clientHistory').createIndex({ clientId: 1 });
        await this.db.collection('clientHistory').createIndex({ isActive: 1 });
        await this.db.collection('clientHistory').createIndex({ createdAt: -1 });

        // Legacy Client Info collection indexes (for backward compatibility)
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

        // Version History collection indexes
        await this.db.collection('versionHistory').createIndex({ versionNumber: 1 }, { unique: true });
        await this.db.collection('versionHistory').createIndex({ versionNumber: -1 });
        await this.db.collection('versionHistory').createIndex({ createdAt: -1 });
        await this.db.collection('versionHistory').createIndex({ date: -1 });
        await this.db.collection('versionHistory').createIndex({ isCurrent: 1 });
        await this.db.collection('versionHistory').createIndex({ sha: 1 }, { sparse: true });
        await this.db.collection('versionHistory').createIndex({ deploymentId: 1 }, { sparse: true });

        console.log('Database indexes created successfully');
      } catch (indexError) {
        // Indexes might already exist, which is fine
        console.log('Some indexes may already exist:', indexError.message);
      }

      // Perform initial version history sync if collection is empty
      const versionCount = await this.db.collection('versionHistory').countDocuments();
      if (versionCount === 0) {
        console.log('Version history collection is empty, performing initial sync...');
        await this.performInitialVersionSync();
      }

      return { success: true, message: 'MongoDB database and security collections initialized successfully' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getVersionInfo() {
    try {
      if (this.usesFallback) {
        return {
          success: true,
          currentVersion: '1.0.0',
          latestVersion: '1.0.0',
          releaseNotes: 'Fallback version - MongoDB not configured',
          updateAvailable: false,
          autoUpdateEnabled: true,
          forceUpdate: false,
          downloadUrl: '/api/download?file=client',
          timestamp: new Date().toISOString()
        };
      }

      await this.connect();
      
      // Get the current version (highest version number) from database
      const currentVersion = await this.db.collection('versionHistory')
        .findOne({ isCurrent: true });
      
      if (!currentVersion) {
        // If no current version found, try to get the highest version number
        const latestVersion = await this.db.collection('versionHistory')
          .findOne({}, { sort: { versionNumber: -1 } });
        
        if (latestVersion) {
          // Mark it as current
          await this.db.collection('versionHistory').updateOne(
            { _id: latestVersion._id },
            { $set: { isCurrent: true } }
          );
          
          return {
            success: true,
            currentVersion: latestVersion.version,
            latestVersion: latestVersion.version,
            releaseNotes: latestVersion.message || 'Latest deployment',
            updateAvailable: false,
            autoUpdateEnabled: true,
            forceUpdate: false,
            downloadUrl: '/api/download?file=client',
            timestamp: new Date().toISOString(),
            versionNumber: latestVersion.versionNumber
          };
        }
        
        // No versions found, return default
        return {
          success: true,
          currentVersion: '1.0.0',
          latestVersion: '1.0.0',
          releaseNotes: 'No deployment history found',
          updateAvailable: false,
          autoUpdateEnabled: true,
          forceUpdate: false,
          downloadUrl: '/api/download?file=client',
          timestamp: new Date().toISOString(),
          versionNumber: 1
        };
      }
      
      return {
        success: true,
        currentVersion: currentVersion.version,
        latestVersion: currentVersion.version,
        releaseNotes: currentVersion.message || 'Latest deployment',
        updateAvailable: false,
        autoUpdateEnabled: true,
        forceUpdate: false,
        downloadUrl: '/api/download?file=client',
        timestamp: new Date().toISOString(),
        versionNumber: currentVersion.versionNumber
      };
    } catch (error) {
      return {
        success: false,
        message: 'Error retrieving version info: ' + error.message,
        currentVersion: '1.0.0',
        latestVersion: '1.0.0',
        updateAvailable: false
      };
    }
  }

  async getVersionHistory() {
    try {
      if (this.usesFallback) {
        return this.getFallbackVersionHistory();
      }

      await this.connect();
      
      // First, try to sync new versions from external sources
      await this.syncVersionHistory();
      
      // Then fetch from database
      const versions = await this.db.collection('versionHistory')
        .find({})
        .sort({ versionNumber: -1 }) // Sort by version number descending (newest first)
        .toArray();
      
      if (versions.length === 0) {
        // If no versions in database, perform initial sync
        await this.performInitialVersionSync();
        const syncedVersions = await this.db.collection('versionHistory')
          .find({})
          .sort({ versionNumber: -1 })
          .toArray();
        
        return this.formatVersionHistoryResponse(syncedVersions);
      }
      
      return this.formatVersionHistoryResponse(versions);
    } catch (error) {
      console.error('Error fetching version history:', error);
      
      return {
        success: false,
        data: [],
        totalDeployments: 0,
        currentVersion: '1.1.9',
        source: 'error',
        lastRefreshed: new Date().toISOString(),
        error: 'Failed to fetch deployment data: ' + error.message
      };
    }
  }

  async fetchGitHubReleases() {
    try {
      const response = await fetch('https://api.github.com/repos/mirial83/PushNotifications/releases?per_page=100');
      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
      }
      
      const releases = await response.json();
      return releases.map((release, index) => ({
        version: release.tag_name,
        message: release.name || release.tag_name,
        description: release.body || '',
        date: release.published_at,
        isCurrent: index === 0,
        source: 'github-releases'
      }));
    } catch (error) {
      console.log('GitHub releases fetch failed:', error.message);
      return null;
    }
  }

  async fetchGitHubCommits() {
    try {
      const response = await fetch('https://api.github.com/repos/mirial83/PushNotifications/commits?per_page=100');
      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
      }
      
      const commits = await response.json();
      
      // Reverse the commits array so oldest is first, then map with proper versioning
      const reversedCommits = commits.reverse();
      
      return reversedCommits.map((commit, index) => {
        // Calculate version number: start at 1.0.0 and increment
        const major = 1;
        const minor = Math.floor(index / 10);
        const patch = index % 10;
        const version = `${major}.${minor}.${patch}`;
        
        return {
          version: version,
          message: commit.commit.message.split('\n')[0], // First line only
          description: commit.commit.message,
          date: commit.commit.committer.date,
          sha: commit.sha.substring(0, 8),
          author: commit.commit.author.name,
          isCurrent: false, // Will be set later in getVersionHistory
          source: 'github-commits'
        };
      }).reverse(); // Reverse back so newest is first for display
    } catch (error) {
      console.log('GitHub commits fetch failed:', error.message);
      return null;
    }
  }

  async fetchGitHubDeployments() {
    try {
      // Check for GitHub token (optional for public repos, but recommended for higher rate limits)
      const githubToken = process.env.GITHUB_TOKEN;
      
      // Build API URL for GitHub deployments API
      const apiUrl = 'https://api.github.com/repos/mirial83/PushNotifications/deployments?per_page=100';
      
      const headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
      };
      
      if (githubToken) {
        headers['Authorization'] = `Bearer ${githubToken}`;
      }
      
      const response = await fetch(apiUrl, { headers });
      
      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} - ${response.statusText}`);
      }
      
      const deployments = await response.json();
      
      if (!deployments || deployments.length === 0) {
        console.log('No GitHub deployments found');
        return null;
      }
      
      // Get deployments with successful deployment status AND passing Vercel checks
      const validDeployments = [];
      
      for (const deployment of deployments.slice(0, 20)) { // Limit to 20 to avoid rate limits
        try {
          // Check deployment status
          const statusResponse = await fetch(`https://api.github.com/repos/mirial83/PushNotifications/deployments/${deployment.id}/statuses`, {
            headers
          });
          
          if (!statusResponse.ok) {
            console.log(`Failed to get deployment status for ${deployment.id}`);
            continue;
          }
          
          const statuses = await statusResponse.json();
          const latestStatus = statuses[0]; // Most recent status
          
          // Only proceed if deployment was successful
          if (!latestStatus || latestStatus.state !== 'success') {
            continue;
          }
          
          // Check Vercel status checks for this commit
          const checksResponse = await fetch(`https://api.github.com/repos/mirial83/PushNotifications/commits/${deployment.sha}/status`, {
            headers
          });
          
          if (checksResponse.ok) {
            const checksData = await checksResponse.json();
            
            // Look for Vercel checks in the status checks
            const vercelChecks = checksData.statuses?.filter(status => 
              status.context && (
                status.context.toLowerCase().includes('vercel') ||
                status.context.toLowerCase().includes('deployment')
              )
            ) || [];
            
            // If there are Vercel checks, ensure they all passed
            if (vercelChecks.length > 0) {
              const allVercelChecksPassed = vercelChecks.every(check => check.state === 'success');
              if (!allVercelChecksPassed) {
                console.log(`Deployment ${deployment.id} has failing Vercel checks`);
                continue;
              }
            }
            
            // Also check GitHub check runs (newer API)
            const checkRunsResponse = await fetch(`https://api.github.com/repos/mirial83/PushNotifications/commits/${deployment.sha}/check-runs`, {
              headers
            });
            
            if (checkRunsResponse.ok) {
              const checkRunsData = await checkRunsResponse.json();
              
              // Look for Vercel check runs
              const vercelCheckRuns = checkRunsData.check_runs?.filter(checkRun => 
                checkRun.name && (
                  checkRun.name.toLowerCase().includes('vercel') ||
                  checkRun.name.toLowerCase().includes('deployment') ||
                  checkRun.app?.name?.toLowerCase().includes('vercel')
                )
              ) || [];
              
              // If there are Vercel check runs, ensure they all passed
              if (vercelCheckRuns.length > 0) {
                const allVercelCheckRunsPassed = vercelCheckRuns.every(checkRun => 
                  checkRun.conclusion === 'success' || checkRun.conclusion === 'neutral'
                );
                if (!allVercelCheckRunsPassed) {
                  console.log(`Deployment ${deployment.id} has failing Vercel check runs`);
                  continue;
                }
              }
            }
          }
          
          // If we get here, the deployment is successful and Vercel checks passed
          validDeployments.push({
            ...deployment,
            status: latestStatus
          });
          
        } catch (checkError) {
          console.log(`Failed to check Vercel status for deployment ${deployment.id}:`, checkError.message);
          // Skip this deployment if we can't verify Vercel checks
          continue;
        }
      }
      
      if (validDeployments.length === 0) {
        console.log('No GitHub deployments found with passing Vercel checks');
        return null;
      }
      
      console.log(`Found ${validDeployments.length} deployments with passing Vercel checks`);
      
      // Convert to our format
      return validDeployments.map((deployment, index) => ({
        version: null, // Will be set by applyVersionNumbering
        message: deployment.description || deployment.payload?.description || `Deployment ${deployment.id}`,
        description: deployment.description || deployment.payload?.description || '',
        date: deployment.created_at,
        deploymentId: deployment.id.toString(),
        sha: deployment.sha ? deployment.sha.substring(0, 8) : null,
        url: deployment.status?.target_url || deployment.status?.environment_url || null,
        source: 'github-deployments',
        isCurrent: index === 0,
        author: deployment.creator?.login || 'Unknown',
        environment: deployment.environment || 'production'
      }));
      
    } catch (error) {
      console.log('GitHub deployments fetch failed:', error.message);
      return null;
    }
  }

  async getFallbackVersionHistory() {
    // Fallback static version history
    const deployments = [
      { message: 'Current version - Node.js/MongoDB/Vercel implementation', isCurrent: true },
      { message: 'Website authentication and user management', isCurrent: false },
      { message: 'Security features and MAC address client tracking', isCurrent: false },
      { message: 'Database migration from PHP to Node.js/MongoDB', isCurrent: false },
      { message: 'Client installer improvements', isCurrent: false },
      { message: 'Visual updates and UI improvements', isCurrent: false },
      { message: 'Quick action buttons and notifications', isCurrent: false },
      { message: 'Initial Node.js API development', isCurrent: false }
    ];

    return deployments.map((deployment, index) => ({
      version: index === 0 ? '1.1.9' : `1.${Math.floor((deployments.length - index - 1) / 10)}.${(deployments.length - index - 1) % 10}`,
      message: deployment.message,
      isCurrent: deployment.isCurrent,
      source: 'fallback',
      date: new Date(Date.now() - (index * 24 * 60 * 60 * 1000)).toISOString() // Simulate dates
    }));
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

  async uninstallAllClients(reason = 'Administrative uninstall') {
    try {
      // Get count of active clients before uninstalling
      let clientCount = 0;
      
      if (this.usesFallback) {
        clientCount = fallbackStorage.clients.length;
      } else {
        await this.connect();
        // Count active clients (those that have checked in recently)
        const activeClients = await this.db.collection('macClients')
          .find({ activeClientId: { $ne: null } })
          .toArray();
        clientCount = activeClients.length;
      }

      // Create special uninstall notification for all active clients
      const uninstallNotification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        message: '__UNINSTALL_ALL_COMMAND__',
        clientId: 'all',
        status: 'Active',
        type: 'uninstall_command',
        reason: reason,
        allowBrowserUsage: false,
        allowedWebsites: '',
        created: new Date().toISOString()
      };

      if (this.usesFallback) {
        fallbackStorage.notifications.push(uninstallNotification);
      } else {
        await this.connect();
        await this.db.collection('notifications').insertOne(uninstallNotification);
      }

      return {
        success: true,
        message: `Uninstall command sent to ${clientCount} active client(s)`,
        clientCount
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async uninstallSpecificClient(clientId, reason = 'Administrative uninstall') {
    try {
      if (!clientId) {
        return { success: false, message: 'Client ID is required' };
      }

      // Check if the client exists
      let clientExists = false;
      
      if (this.usesFallback) {
        clientExists = fallbackStorage.clients.some(c => c.clientId === clientId);
      } else {
        await this.connect();
        // Check both clients and macClients collections
        const client = await this.db.collection('clients').findOne({ clientId });
        const macClient = await this.db.collection('macClients').findOne({ 
          $or: [{ clientId }, { activeClientId: clientId }] 
        });
        clientExists = client || macClient;
      }

      if (!clientExists) {
        return { success: false, message: `Client with ID "${clientId}" not found` };
      }

      // Create special uninstall notification for the specific client
      const uninstallNotification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        message: '__UNINSTALL_SPECIFIC_COMMAND__',
        clientId: clientId,
        status: 'Active',
        type: 'uninstall_command',
        reason: reason,
        allowBrowserUsage: false,
        allowedWebsites: '',
        created: new Date().toISOString()
      };

      if (this.usesFallback) {
        fallbackStorage.notifications.push(uninstallNotification);
      } else {
        await this.connect();
        await this.db.collection('notifications').insertOne(uninstallNotification);
      }

      return {
        success: true,
        message: `Uninstall command sent to client "${clientId}"`,
        clientId
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

  async removeOldActiveNotifications(days = 2) {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      
      let deletedCount = 0;
      
      if (this.usesFallback) {
        const originalLength = fallbackStorage.notifications.length;
        fallbackStorage.notifications = fallbackStorage.notifications.filter(n => {
          if (n.status === 'Active' && new Date(n.created) < cutoffDate) {
            return false; // Remove this notification
          }
          return true; // Keep this notification
        });
        deletedCount = originalLength - fallbackStorage.notifications.length;
      } else {
        await this.connect();
        const result = await this.db.collection('notifications').deleteMany({
          status: 'Active',
          created: { $lt: cutoffDate.toISOString() }
        });
        deletedCount = result.deletedCount;
      }

      return {
        success: true,
        message: `Removed ${deletedCount} old active notifications older than ${days} day(s)`,
        removedCount: deletedCount,
        cutoffDate: cutoffDate.toISOString()
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async cleanOldNotifications(days = 7) {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      
      let cleanedCount = 0;
      
      if (this.usesFallback) {
        const originalLength = fallbackStorage.notifications.length;
        fallbackStorage.notifications = fallbackStorage.notifications.filter(n => {
          if ((n.status === 'Completed' || n.status === 'Acknowledged' || n.status === 'Dismissed') && new Date(n.created) < cutoffDate) {
            return false; // Remove this notification
          }
          return true; // Keep this notification
        });
        cleanedCount = originalLength - fallbackStorage.notifications.length;
      } else {
        await this.connect();
        const result = await this.db.collection('notifications').deleteMany({
          status: { $in: ['Completed', 'Acknowledged', 'Dismissed'] },
          created: { $lt: cutoffDate.toISOString() }
        });
        cleanedCount = result.deletedCount;
      }

      return {
        success: true,
        message: `Cleaned ${cleanedCount} old notifications older than ${days} day(s)`,
        cleanedCount,
        cutoffDate: cutoffDate.toISOString()
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async clearOldWebsiteRequests(days = 7) {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      
      let clearedCount = 0;
      
      if (this.usesFallback) {
        const originalLength = fallbackStorage.notifications.length;
        fallbackStorage.notifications = fallbackStorage.notifications.filter(n => {
          if (n.type === 'website_request' && new Date(n.created || n.timestamp) < cutoffDate) {
            return false; // Remove this website request
          }
          return true; // Keep this notification
        });
        clearedCount = originalLength - fallbackStorage.notifications.length;
      } else {
        await this.connect();
        const result = await this.db.collection('notifications').deleteMany({
          type: 'website_request',
          $or: [
            { created: { $lt: cutoffDate.toISOString() } },
            { timestamp: { $lt: cutoffDate } }
          ]
        });
        clearedCount = result.deletedCount;
      }

      return {
        success: true,
        message: `Cleared ${clearedCount} old website requests older than ${days} day(s)`,
        clearedCount,
        cutoffDate: cutoffDate.toISOString()
      };
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

  // MAC Address-based Client Management Methods
  async authenticateClientByMac(macAddress, username, hostname, installPath, platform, version) {
    try {
      if (this.usesFallback) {
        // In-memory fallback - create a temporary client
        const clientId = `${username}_${macAddress.replace(/:/g, '').substr(-6)}`;
        const clientData = {
          clientId,
          clientName: `${username}1`,
          computerName: hostname,
          macAddress,
          registered: new Date().toISOString(),
          lastSeen: new Date().toISOString()
        };
        fallbackStorage.clients.push(clientData);
        return { success: true, clientId, clientName: `${username}1`, isNewInstallation: true };
      }

      await this.connect();
      const now = new Date();

      // Check if MAC address already exists
      let macClient = await this.db.collection('macClients').findOne({ macAddress });
      let clientName, clientId, isNewInstallation = false;

      if (!macClient) {
        // First installation on this MAC address
        clientName = `${username}1`;
        clientId = `${username}_${macAddress.replace(/:/g, '').substr(-6)}_1`;
        isNewInstallation = true;

        // Create new MAC client record
        macClient = {
          macAddress,
          username,
          clientName,
          activeClientId: clientId,
          installationCount: 1,
          createdAt: now,
          lastCheckin: now,
          hostname,
          platform
        };
        await this.db.collection('macClients').insertOne(macClient);

        // Create client history record
        const historyRecord = {
          macAddress,
          clientId,
          clientName,
          username,
          hostname,
          installPath,
          platform,
          version,
          isActive: true,
          createdAt: now,
          lastCheckin: now
        };
        await this.db.collection('clientHistory').insertOne(historyRecord);

      } else {
        // Existing MAC address - deactivate previous installation and create new one
        if (macClient.activeClientId) {
          // Deactivate previous client
          await this.db.collection('clientHistory').updateOne(
            { clientId: macClient.activeClientId },
            { 
              $set: { 
                isActive: false, 
                deactivatedAt: now,
                deactivationReason: 'New installation on same MAC address'
              }
            }
          );
        }

        // Create new installation
        const newInstallationNumber = macClient.installationCount + 1;
        clientName = `${username}${newInstallationNumber}`;
        clientId = `${username}_${macAddress.replace(/:/g, '').substr(-6)}_${newInstallationNumber}`;
        isNewInstallation = true;

        // Update MAC client record
        await this.db.collection('macClients').updateOne(
          { _id: macClient._id },
          {
            $set: {
              activeClientId: clientId,
              clientName,
              installationCount: newInstallationNumber,
              lastCheckin: now,
              hostname,
              platform
            }
          }
        );

        // Create new client history record
        const historyRecord = {
          macAddress,
          clientId,
          clientName,
          username,
          hostname,
          installPath,
          platform,
          version,
          isActive: true,
          createdAt: now,
          lastCheckin: now
        };
        await this.db.collection('clientHistory').insertOne(historyRecord);
      }

      return {
        success: true,
        clientId,
        clientName,
        isNewInstallation,
        macAddress,
        message: isNewInstallation ? 'New client installation registered' : 'Client authentication successful'
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async updateClientMacCheckin(clientId, version) {
    try {
      if (this.usesFallback) {
        const client = fallbackStorage.clients.find(c => c.clientId === clientId);
        if (client) {
          client.lastSeen = new Date().toISOString();
        }
        return { success: true, message: 'Client checkin updated in memory' };
      }

      await this.connect();
      const now = new Date();

      // Update client history record
      const historyResult = await this.db.collection('clientHistory').updateOne(
        { clientId, isActive: true },
        { 
          $set: { 
            lastCheckin: now,
            version: version || 'unknown'
          }
        }
      );

      if (historyResult.modifiedCount > 0) {
        // Update MAC client record
        const clientHistory = await this.db.collection('clientHistory').findOne({ clientId, isActive: true });
        if (clientHistory) {
          await this.db.collection('macClients').updateOne(
            { macAddress: clientHistory.macAddress },
            { $set: { lastCheckin: now } }
          );
        }
      }

      return { 
        success: true, 
        message: 'Client checkin updated',
        updated: historyResult.modifiedCount > 0
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getClientByMac(macAddress) {
    try {
      if (this.usesFallback) {
        const client = fallbackStorage.clients.find(c => c.macAddress === macAddress);
        return client ? { success: true, client } : { success: false, message: 'Client not found' };
      }

      await this.connect();
      const macClient = await this.db.collection('macClients').findOne({ macAddress });
      
      if (!macClient) {
        return { success: false, message: 'No client found for this MAC address' };
      }

      const activeClient = await this.db.collection('clientHistory').findOne({
        clientId: macClient.activeClientId,
        isActive: true
      });

      return {
        success: true,
        macClient,
        activeClient
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getAllMacClients() {
    try {
      if (this.usesFallback) {
        return { success: true, data: fallbackStorage.clients };
      }

      await this.connect();
      
      // Get all MAC clients with their active client details
      const macClients = await this.db.collection('macClients')
        .find({})
        .sort({ lastCheckin: -1 })
        .toArray();

      const processedClients = [];
      
      for (const macClient of macClients) {
        const activeClient = macClient.activeClientId ? 
          await this.db.collection('clientHistory').findOne({
            clientId: macClient.activeClientId,
            isActive: true
          }) : null;

        processedClients.push({
          _id: macClient._id.toString(),
          macAddress: macClient.macAddress,
          username: macClient.username,
          clientName: macClient.clientName,
          activeClientId: macClient.activeClientId,
          installationCount: macClient.installationCount,
          hostname: macClient.hostname,
          platform: macClient.platform,
          createdAt: macClient.createdAt,
          lastCheckin: macClient.lastCheckin,
          activeClient: activeClient ? {
            installPath: activeClient.installPath,
            version: activeClient.version,
            createdAt: activeClient.createdAt,
            lastCheckin: activeClient.lastCheckin
          } : null
        });
      }

      return { success: true, data: processedClients };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getClientHistory(macAddress = null) {
    try {
      if (this.usesFallback) {
        return { success: true, data: [] };
      }

      await this.connect();
      
      const query = macAddress ? { macAddress } : {};
      const history = await this.db.collection('clientHistory')
        .find(query)
        .sort({ createdAt: -1 })
        .toArray();

      const processedHistory = history.map(record => ({
        _id: record._id.toString(),
        macAddress: record.macAddress,
        clientId: record.clientId,
        clientName: record.clientName,
        username: record.username,
        hostname: record.hostname,
        installPath: record.installPath,
        platform: record.platform,
        version: record.version,
        isActive: record.isActive,
        createdAt: record.createdAt,
        lastCheckin: record.lastCheckin,
        deactivatedAt: record.deactivatedAt,
        deactivationReason: record.deactivationReason
      }));

      return { success: true, data: processedHistory };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async deactivateClient(clientId, reason = 'Manual deactivation') {
    try {
      if (this.usesFallback) {
        const clientIndex = fallbackStorage.clients.findIndex(c => c.clientId === clientId);
        if (clientIndex >= 0) {
          fallbackStorage.clients.splice(clientIndex, 1);
        }
        return { success: true, message: 'Client deactivated in memory' };
      }

      await this.connect();
      const now = new Date();

      // Deactivate the client in history
      const result = await this.db.collection('clientHistory').updateOne(
        { clientId, isActive: true },
        {
          $set: {
            isActive: false,
            deactivatedAt: now,
            deactivationReason: reason
          }
        }
      );

      if (result.modifiedCount > 0) {
        // Clear the active client ID from MAC client record
        const clientHistory = await this.db.collection('clientHistory').findOne({ clientId });
        if (clientHistory) {
          await this.db.collection('macClients').updateOne(
            { macAddress: clientHistory.macAddress },
            { $set: { activeClientId: null } }
          );
        }
      }

      return {
        success: true,
        message: 'Client deactivated successfully',
        deactivated: result.modifiedCount > 0
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Update security key management to work with MAC addresses
  async createSecurityKeyForMac(macAddress, keyType, keyValue, installPath, hostname) {
    try {
      if (this.usesFallback) {
        return { success: true, message: 'Security key created in memory' };
      }

      await this.connect();
      
      // Get the active client for this MAC address
      const macClient = await this.db.collection('macClients').findOne({ macAddress });
      if (!macClient || !macClient.activeClientId) {
        return { success: false, message: 'No active client found for this MAC address' };
      }

      const securityKeyData = {
        clientId: macClient.activeClientId,
        macAddress,
        keyType,
        keyValue,
        installPath,
        hostname,
        createdAt: new Date(),
        lastUsed: new Date()
      };

      // Check if key already exists for this client
      const existingKey = await this.db.collection('securityKeys').findOne({
        clientId: macClient.activeClientId,
        keyType
      });

      if (existingKey) {
        // Update existing key
        await this.db.collection('securityKeys').updateOne(
          { _id: existingKey._id },
          { 
            $set: { 
              keyValue,
              macAddress,
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

  async getSecurityKeyByMac(macAddress, keyType) {
    try {
      if (this.usesFallback) {
        const key = 'fallback_key_' + Math.random().toString(36).substr(2, 16);
        return { success: true, key };
      }

      await this.connect();
      
      // Get the active client for this MAC address
      const macClient = await this.db.collection('macClients').findOne({ macAddress });
      if (!macClient || !macClient.activeClientId) {
        return { success: false, message: 'No active client found for this MAC address' };
      }

      const securityKey = await this.db.collection('securityKeys').findOne({
        clientId: macClient.activeClientId,
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

  // User Management Methods
  async createUser(username, email, password, role = 'user') {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      // Check if user already exists
      const existingUser = await this.db.collection('users').findOne({
        $or: [{ username }, { email }]
      });
      
      if (existingUser) {
        return { success: false, message: 'Username or email already exists' };
      }

      // Hash password (in production, use bcrypt)
      const hashedPassword = Buffer.from(password).toString('base64');
      
      const userData = {
        username,
        email,
        password: hashedPassword,
        role,
        createdAt: new Date(),
        lastLogin: null,
        isActive: true
      };

      const result = await this.db.collection('users').insertOne(userData);
      
      return {
        success: true,
        message: 'User created successfully',
        userId: result.insertedId.toString()
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async authenticateUser(username, password) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Authentication requires MongoDB connection' };
      }

      await this.connect();
      
      const user = await this.db.collection('users').findOne({
        $or: [{ username }, { email: username }],
        isActive: true
      });
      
      if (!user) {
        return { success: false, message: 'Invalid credentials' };
      }

      // Verify password (in production, use bcrypt.compare)
      const hashedInput = Buffer.from(password).toString('base64');
      if (hashedInput !== user.password) {
        return { success: false, message: 'Invalid credentials' };
      }

      // Update last login
      await this.db.collection('users').updateOne(
        { _id: user._id },
        { $set: { lastLogin: new Date() } }
      );

      // Create persistent session token
      const sessionToken = this.generateSessionToken();
      
      // Remove any existing sessions for this user to prevent multiple sessions
      await this.db.collection('sessions').deleteMany({ userId: user._id });
      
      // Create new session that expires when browser is closed (no explicit expiration)
      await this.db.collection('sessions').insertOne({
        userId: user._id,
        username: user.username,
        role: user.role,
        token: sessionToken,
        createdAt: new Date(),
        persistent: true, // Flag for persistent session
        lastActivity: new Date()
      });

      return {
        success: true,
        message: 'Authentication successful',
        user: {
          id: user._id.toString(),
          username: user.username,
          email: user.email,
          role: user.role
        },
        sessionToken,
        role: user.role
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async validateSession(token) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Session validation requires MongoDB connection' };
      }

      await this.connect();
      
      const session = await this.db.collection('sessions').findOne({
        token
      });
      
      if (!session) {
        return { success: false, message: 'Invalid session', authenticated: false };
      }

      const user = await this.db.collection('users').findOne({
        _id: session.userId,
        isActive: true
      });
      
      if (!user) {
        // Clean up invalid session
        await this.db.collection('sessions').deleteOne({ token });
        return { success: false, message: 'User not found or inactive', authenticated: false };
      }

      // Update last activity for persistent sessions
      if (session.persistent) {
        await this.db.collection('sessions').updateOne(
          { token },
          { $set: { lastActivity: new Date() } }
        );
      }

      return {
        success: true,
        authenticated: true,
        user: {
          id: user._id.toString(),
          username: user.username,
          email: user.email,
          role: user.role
        },
        role: user.role
      };
    } catch (error) {
      return { success: false, message: error.message, authenticated: false };
    }
  }

  async logout(token) {
    try {
      if (this.usesFallback) {
        return { success: true, message: 'Logged out' };
      }

      await this.connect();
      
      await this.db.collection('sessions').deleteOne({ token });
      
      return { success: true, message: 'Logged out successfully' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async generateDownloadKey(userId) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Download key generation requires MongoDB connection' };
      }

      await this.connect();
      
      // Validate user exists and is active
      const user = await this.db.collection('users').findOne({
        _id: new ObjectId(userId),
        isActive: true
      });
      
      if (!user) {
        return { success: false, message: 'User not found or inactive' };
      }

      // Generate new installation key for this download
      const downloadKey = this.generateInstallationKey();
      
      // Store the download key with expiration (24 hours)
      await this.db.collection('downloadKeys').insertOne({
        userId: user._id,
        username: user.username,
        role: user.role,
        installationKey: downloadKey,
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
        used: false
      });

      return {
        success: true,
        message: 'Download key generated successfully',
        installationKey: downloadKey
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async regenerateInstallationKey(userId) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Key regeneration requires MongoDB connection' };
      }

      await this.connect();
      
      const newKey = this.generateInstallationKey();
      
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(userId) },
        { $set: { installationKey: newKey } }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'User not found' };
      }

      return {
        success: true,
        message: 'Installation key regenerated',
        installationKey: newKey
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async validateInstallationKey(installationKey) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Key validation requires MongoDB connection' };
      }

      await this.connect();
      
      // Check for valid download key first
      const downloadKey = await this.db.collection('downloadKeys').findOne({
        installationKey,
        expiresAt: { $gt: new Date() },
        used: false
      });
      
      if (downloadKey) {
        // Mark the key as used
        await this.db.collection('downloadKeys').updateOne(
          { _id: downloadKey._id },
          { $set: { used: true, usedAt: new Date() } }
        );
        
        return {
          success: true,
          message: 'Installation key valid',
          user: {
            id: downloadKey.userId.toString(),
            username: downloadKey.username,
            role: downloadKey.role
          }
        };
      }
      
      return { success: false, message: 'Invalid or expired installation key' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getAllUsers() {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      const users = await this.db.collection('users')
        .find({}, { projection: { password: 0 } })
        .sort({ createdAt: -1 })
        .toArray();

      const processedUsers = users.map(user => ({
        id: user._id.toString(),
        username: user.username,
        email: user.email,
        role: user.role,
        installationKey: user.installationKey,
        createdAt: user.createdAt,
        lastLogin: user.lastLogin,
        isActive: user.isActive
      }));

      return { success: true, data: processedUsers };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async updateUserRole(userId, newRole) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(userId) },
        { $set: { role: newRole } }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'User not found' };
      }

      return { success: true, message: 'User role updated successfully' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async deactivateUser(userId) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(userId) },
        { $set: { isActive: false } }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'User not found' };
      }

      // Also invalidate all sessions for this user
      await this.db.collection('sessions').deleteMany({ userId: new ObjectId(userId) });

      return { success: true, message: 'User deactivated successfully' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async deleteUser(userId) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      // Check if user exists first
      const user = await this.db.collection('users').findOne({ _id: new ObjectId(userId) });
      if (!user) {
        return { success: false, message: 'User not found' };
      }

      // Delete user and all associated data
      // Using Promise.all for concurrent operations
      await Promise.all([
        // Delete user sessions
        this.db.collection('sessions').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete security keys associated with the user
        this.db.collection('securityKeys').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete download keys associated with the user
        this.db.collection('downloadKeys').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete user's notifications
        this.db.collection('notifications').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete user's MAC clients
        this.db.collection('macClients').deleteMany({ userId: new ObjectId(userId) })
      ]);
      
      // Finally, delete the user record itself
      const result = await this.db.collection('users').deleteOne({ _id: new ObjectId(userId) });
      
      if (result.deletedCount === 0) {
        return { success: false, message: 'Failed to delete user' };
      }

      return { success: true, message: 'User and associated data deleted successfully' };
    } catch (error) {
      console.error('Error deleting user:', error);
      return { success: false, message: error.message };
    }
  }

  async resetUserPassword(userId, newPassword) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      // Check if user exists first
      const user = await this.db.collection('users').findOne({ _id: new ObjectId(userId) });
      if (!user) {
        return { success: false, message: 'User not found' };
      }

      // Hash the new password (in production, use bcrypt)
      const hashedPassword = Buffer.from(newPassword).toString('base64');
      
      // Update user's password
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(userId) },
        { 
          $set: { 
            password: hashedPassword,
            passwordResetAt: new Date()
          }
        }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'Failed to update password' };
      }

      // Invalidate all existing sessions for this user to force re-login
      await this.db.collection('sessions').deleteMany({ userId: new ObjectId(userId) });

      return { 
        success: true, 
        message: 'Password reset successfully',
        username: user.username
      };
    } catch (error) {
      console.error('Error resetting user password:', error);
      return { success: false, message: error.message };
    }
  }

  // Version History Management Methods
  async syncVersionHistory() {
    try {
      // Get the latest version from database
      const latestDbVersion = await this.db.collection('versionHistory')
        .findOne({}, { sort: { versionNumber: -1 } });
      
      // Fetch latest versions from external sources
      const externalVersions = await this.fetchLatestExternalVersions();
      
      if (!externalVersions || externalVersions.length === 0) {
        return;
      }
      
      // Sort external versions by date (newest first) to get the most recent
      const sortedExternalVersions = [...externalVersions].sort((a, b) => new Date(b.date) - new Date(a.date));
      const newestExternal = sortedExternalVersions[0];
      
      // Check if we need to add the newest version
      if (!latestDbVersion || this.isNewerVersion(newestExternal, latestDbVersion)) {
        await this.addNewestVersionToDatabase(newestExternal, latestDbVersion);
      }
    } catch (error) {
      console.log('Version sync failed:', error.message);
    }
  }
  
  
  async fetchLatestExternalVersions() {
    // Priority order: GitHub deployments > GitHub releases > GitHub commits
    let externalData = await this.fetchGitHubDeployments();
    
    if (!externalData || externalData.length === 0) {
      externalData = await this.fetchGitHubReleases();
    }
    
    if (!externalData || externalData.length === 0) {
      externalData = await this.fetchGitHubCommits();
    }
    
    return externalData;
  }
  
  isNewerVersion(externalVersion, dbVersion) {
    // Compare by date and unique identifiers
    const externalDate = new Date(externalVersion.date);
    const dbDate = new Date(dbVersion.date || dbVersion.createdAt);
    
    if (externalDate > dbDate) {
      return true;
    }
    
    // Also check for unique identifiers like commit SHA or deployment ID
    if (externalVersion.sha && dbVersion.sha && externalVersion.sha !== dbVersion.sha) {
      return true;
    }
    
    if (externalVersion.deploymentId && dbVersion.deploymentId && externalVersion.deploymentId !== dbVersion.deploymentId) {
      return true;
    }
    
    return false;
  }
  
  async addNewestVersionToDatabase(newestExternal, latestDbVersion) {
    try {
      // Get the current highest version number
      const highestVersion = await this.db.collection('versionHistory')
        .findOne({}, { sort: { versionNumber: -1 } });
      
      const nextVersionNumber = highestVersion ? highestVersion.versionNumber + 1 : 1;
      
      // Check if this version already exists
      const exists = await this.db.collection('versionHistory').findOne({
        $or: [
          newestExternal.sha ? { sha: newestExternal.sha } : {},
          newestExternal.deploymentId ? { deploymentId: newestExternal.deploymentId } : {},
          { message: newestExternal.message, date: newestExternal.date }
        ].filter(obj => Object.keys(obj).length > 0)
      });
      
      if (!exists) {
        // Calculate semantic version using the helper method
        const semanticVersion = this.calculateSemanticVersion(nextVersionNumber - 1);
        
        const versionRecord = {
          versionNumber: nextVersionNumber,
          version: semanticVersion,
          message: newestExternal.message || 'No message',
          description: newestExternal.description || '',
          date: newestExternal.date,
          sha: newestExternal.sha || null,
          deploymentId: newestExternal.deploymentId || null,
          author: newestExternal.author || 'Unknown',
          source: newestExternal.source || 'unknown',
          isCurrent: true, // Mark as current since it's the newest
          createdAt: new Date(),
          url: newestExternal.url || null
        };
        
        // Remove current flag from all existing versions
        await this.db.collection('versionHistory').updateMany(
          {},
          { $set: { isCurrent: false } }
        );
        
        // Insert the new version
        await this.db.collection('versionHistory').insertOne(versionRecord);
        
        console.log(`Added new version ${nextVersionNumber} (${semanticVersion}) to database: ${newestExternal.message}`);
      }
    } catch (error) {
      console.error('Error adding newest version to database:', error);
    }
  }
  
  async updateCurrentVersionFlag() {
    try {
      // Remove current flag from all versions
      await this.db.collection('versionHistory').updateMany(
        {},
        { $set: { isCurrent: false } }
      );
      
      // Set the highest version number as current
      const latestVersion = await this.db.collection('versionHistory')
        .findOne({}, { sort: { versionNumber: -1 } });
      
      if (latestVersion) {
        await this.db.collection('versionHistory').updateOne(
          { _id: latestVersion._id },
          { $set: { isCurrent: true } }
        );
      }
    } catch (error) {
      console.error('Error updating current version flag:', error);
    }
  }
  
  async performInitialVersionSync() {
    try {
      console.log('Performing initial version history sync...');
      
      const externalVersions = await this.fetchLatestExternalVersions();
      
      if (!externalVersions || externalVersions.length === 0) {
        console.log('No external versions found for initial sync');
        return;
      }
      
      // Sort by date (oldest first) so oldest versions get lowest numbers
      const sortedVersions = [...externalVersions].sort((a, b) => new Date(a.date) - new Date(b.date));
      
      const versionRecords = sortedVersions.map((version, index) => {
        const versionNumber = index + 1; // Oldest gets number 1, then 2, 3, etc.
        const semanticVersion = this.calculateSemanticVersion(index);
        
        return {
          versionNumber,
          version: semanticVersion,
          message: version.message || 'No message',
          description: version.description || '',
          date: version.date,
          sha: version.sha || null,
          deploymentId: version.deploymentId || null,
          author: version.author || 'Unknown',
          source: version.source || 'unknown',
          isCurrent: index === sortedVersions.length - 1, // Mark the newest (last in sorted array) as current
          createdAt: new Date(),
          url: version.url || null
        };
      });
      
      if (versionRecords.length > 0) {
        await this.db.collection('versionHistory').insertMany(versionRecords);
        console.log(`Initial sync completed: ${versionRecords.length} versions added`);
        console.log(`Version range: ${versionRecords[0].version} (oldest) to ${versionRecords[versionRecords.length-1].version} (newest)`);
      }
    } catch (error) {
      console.error('Error performing initial version sync:', error);
    }
  }
  
  formatVersionHistoryResponse(versions) {
    const currentVersion = process.env.npm_package_version || '1.1.9';
    
    // Format versions for response
    const formattedVersions = versions.map(v => ({
      version: v.version,
      message: v.message,
      description: v.description,
      date: v.date,
      isCurrent: v.isCurrent,
      source: v.source,
      author: v.author,
      sha: v.sha,
      deploymentId: v.deploymentId,
      url: v.url
    }));
    
    return {
      success: true,
      data: formattedVersions,
      totalDeployments: versions.length,
      currentVersion: currentVersion,
      source: versions.length > 0 ? 'database' : 'no-data',
      lastRefreshed: new Date().toISOString()
    };
  }
  
  // Helper methods
  calculateSemanticVersion(index) {
    // Start with version 1.0.0 for index 0
    // Increment the rightmost digit first, then the middle, then the leftmost
    // Only the leftmost section can be multiple digits
    
    if (index === 0) {
      return '1.0.0';
    }
    
    // Calculate version components
    let patch = index % 10;
    let minor = Math.floor(index / 10) % 10;
    let major = Math.floor(index / 100) + 1; // Start at 1 and increment
    
    // For the first 10 versions (index 0-9): 1.0.0, 1.0.1, 1.0.2, ..., 1.0.9
    // For the next 10 versions (index 10-19): 1.1.0, 1.1.1, 1.1.2, ..., 1.1.9  
    // For versions 20-29: 1.2.0, 1.2.1, ..., 1.2.9
    // ...
    // For versions 90-99: 1.9.0, 1.9.1, ..., 1.9.9
    // For versions 100-109: 2.0.0, 2.0.1, ..., 2.0.9
    // And so on...
    
    return `${major}.${minor}.${patch}`;
  }
  
  applyVersionNumbering(deploymentData) {
    if (!deploymentData || deploymentData.length === 0) {
      return deploymentData;
    }

    // Sort deployments by date (oldest first) to apply proper numbering
    const sortedDeployments = [...deploymentData].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Apply version numbers using the semantic version calculator
    const numberedDeployments = sortedDeployments.map((deployment, index) => {
      const version = this.calculateSemanticVersion(index);
      
      return {
        ...deployment,
        version: version
      };
    });
    
    // Return sorted by date (newest first) for display
    return numberedDeployments.reverse();
  }

  generateInstallationKey() {
    return 'PNK_' + Math.random().toString(36).substr(2, 16).toUpperCase() + '_' + Date.now().toString(36).toUpperCase();
  }

  generateSessionToken() {
    return 'PNS_' + Math.random().toString(36).substr(2, 32) + '_' + Date.now().toString(36);
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

      case 'retrieveSecurityKey': {
        const retrieveAuthHeader = req.headers.authorization;
        const retrieveToken = retrieveAuthHeader && retrieveAuthHeader.startsWith('Bearer ')
          ? retrieveAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(retrieveToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        const keyResult = await db.getSecurityKey(
          params.clientId || '',
          params.keyType || 'ENCRYPTION_KEY'
        );
        
        if (keyResult.success) {
          result = {
            success: true,
            securityKey: keyResult.key,
            clientId: params.clientId
          };
        } else {
          result = keyResult;
        }
        break;
      }

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

      // MAC Address-based Client Management Actions
      case 'authenticateClientByMac':
        result = await db.authenticateClientByMac(
          params.macAddress || '',
          params.username || '',
          params.hostname || '',
          params.installPath || '',
          params.platform || '',
          params.version || ''
        );
        break;

      case 'updateClientMacCheckin':
        result = await db.updateClientMacCheckin(
          params.clientId || '',
          params.version || ''
        );
        break;

      case 'getClientByMac':
        result = await db.getClientByMac(params.macAddress || '');
        break;

      case 'getAllMacClients':
        result = await db.getAllMacClients();
        break;

      case 'getClientHistory':
        result = await db.getClientHistory(params.macAddress || null);
        break;

      case 'deactivateClient':
        result = await db.deactivateClient(
          params.clientId || '',
          params.reason || 'Manual deactivation'
        );
        break;

      // MAC Address-based Security Key Management Actions
      case 'createSecurityKeyForMac':
        result = await db.createSecurityKeyForMac(
          params.macAddress || '',
          params.keyType || 'ENCRYPTION_KEY',
          params.keyValue || '',
          params.installPath || '',
          params.hostname || ''
        );
        break;

      case 'getSecurityKeyByMac':
        result = await db.getSecurityKeyByMac(
          params.macAddress || '',
          params.keyType || 'ENCRYPTION_KEY'
        );
        break;

      // User Authentication Actions
      case 'login':
      case 'authenticateUser':
        result = await db.authenticateUser(
          params.username || '',
          params.password || ''
        );
        break;

      case 'logout':
        const authHeader = req.headers.authorization;
        const token = authHeader && authHeader.startsWith('Bearer ') 
          ? authHeader.substring(7)
          : (params.token || '');
        result = await db.logout(token);
        break;

      case 'validateSession':
        const sessionAuthHeader = req.headers.authorization;
        const sessionToken = sessionAuthHeader && sessionAuthHeader.startsWith('Bearer ') 
          ? sessionAuthHeader.substring(7)
          : (params.token || '');
        result = await db.validateSession(sessionToken);
        break;

      case 'checkAuth':
        // Check authentication from cookies or headers
        const checkAuthHeader = req.headers.authorization;
        const checkToken = checkAuthHeader && checkAuthHeader.startsWith('Bearer ') 
          ? checkAuthHeader.substring(7)
          : (params.token || req.cookies?.sessionToken || '');
        
        if (!checkToken) {
          result = { success: true, authenticated: false };
        } else {
          const authResult = await db.validateSession(checkToken);
          result = {
            success: true,
            authenticated: authResult.success,
            role: authResult.role || null,
            user: authResult.user || null
          };
        }
        break;

      case 'createUser':
      case 'registerUser':
        result = await db.createUser(
          params.username || '',
          params.email || '',
          params.password || '',
          params.role || 'user'
        );
        break;

      // Installation Key Management Actions
      case 'validateInstallationKey':
        result = await db.validateInstallationKey(params.installationKey || '');
        break;

      case 'generateDownloadKey':
        const keyAuthHeader = req.headers.authorization;
        const keyToken = keyAuthHeader && keyAuthHeader.startsWith('Bearer ') 
          ? keyAuthHeader.substring(7)
          : (params.token || '');
        
        // Validate session first
        const sessionValidation = await db.validateSession(keyToken);
        if (!sessionValidation.success) {
          result = { success: false, message: 'Authentication required' };
        } else {
          result = await db.generateDownloadKey(sessionValidation.user.id);
        }
        break;

      case 'regenerateInstallationKey':
        result = await db.regenerateInstallationKey(params.userId || '');
        break;

      // User Management Actions (Admin only)
      case 'getAllUsers': {
        const getUsersAuthHeader = req.headers.authorization;
        const getUsersToken = getUsersAuthHeader && getUsersAuthHeader.startsWith('Bearer ')
          ? getUsersAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(getUsersToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        result = await db.getAllUsers();
        break;
      }

      case 'updateUserRole':
        result = await db.updateUserRole(
          params.userId || '',
          params.newRole || 'user'
        );
        break;

      case 'deactivateUser':
        result = await db.deactivateUser(params.userId || '');
        break;

      case 'deleteUser': {
        const delAuthHeader = req.headers.authorization;
        const delToken = delAuthHeader && delAuthHeader.startsWith('Bearer ')
          ? delAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(delToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        if ((params.userId || '') === (validation.user?.id || validation.user?._id)) {
          result = { success: false, message: 'You cannot delete your own account' };
          break;
        }
        result = await db.deleteUser(params.userId || '');
        break;
      }

      case 'resetUserPassword': {
        const resetAuthHeader = req.headers.authorization;
        const resetToken = resetAuthHeader && resetAuthHeader.startsWith('Bearer ')
          ? resetAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(resetToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        result = await db.resetUserPassword(
          params.userId || '',
          params.newPassword || ''
        );
        break;
      }

      // Version History Actions
      case 'getVersionHistory':
        result = await db.getVersionHistory();
        break;
        
      case 'checkForUpdates':
        const clientVersionNumber = parseInt(params.versionNumber || '0');
        
        // Get the latest version info from database
        const versionInfo = await db.getVersionInfo();
        
        if (versionInfo.success && versionInfo.versionNumber) {
          const latestVersionNumber = versionInfo.versionNumber;
          const updateAvailable = latestVersionNumber > clientVersionNumber;
          
          result = {
            success: true,
            updateAvailable,
            latestVersion: versionInfo.currentVersion,
            latestVersionNumber,
            currentVersionNumber: clientVersionNumber,
            releaseNotes: versionInfo.releaseNotes || 'New version available',
            downloadUrl: '/api/download?file=client',
            forceUpdate: false,
            timestamp: new Date().toISOString()
          };
        } else {
          result = {
            success: true,
            updateAvailable: false,
            message: 'Unable to check for updates',
            timestamp: new Date().toISOString()
          };
        }
        break;

      // Uninstall All Clients Action (Admin only)
      case 'uninstallAllClients': {
        const uninstallAuthHeader = req.headers.authorization;
        const uninstallToken = uninstallAuthHeader && uninstallAuthHeader.startsWith('Bearer ')
          ? uninstallAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(uninstallToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.uninstallAllClients(
          params.reason || 'Administrative uninstall'
        );
        break;
      }

      // Uninstall Specific Client Action (Admin only)
      case 'uninstallSpecificClient': {
        const uninstallSpecificAuthHeader = req.headers.authorization;
        const uninstallSpecificToken = uninstallSpecificAuthHeader && uninstallSpecificAuthHeader.startsWith('Bearer ')
          ? uninstallSpecificAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(uninstallSpecificToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.uninstallSpecificClient(
          params.clientId || '',
          params.reason || 'Administrative uninstall'
        );
        break;
      }

      // Remove Old Active Notifications Action (Admin only)
      case 'removeOldActiveNotifications': {
        const removeOldAuthHeader = req.headers.authorization;
        const removeOldToken = removeOldAuthHeader && removeOldAuthHeader.startsWith('Bearer ')
          ? removeOldAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(removeOldToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.removeOldActiveNotifications(
          parseInt(params.days) || 2 // Default to 2 days (48 hours)
        );
        break;
      }

      // Clean Old Notifications Action (Admin only)
      case 'cleanOldNotifications': {
        const cleanOldAuthHeader = req.headers.authorization;
        const cleanOldToken = cleanOldAuthHeader && cleanOldAuthHeader.startsWith('Bearer ')
          ? cleanOldAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(cleanOldToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.cleanOldNotifications(
          parseInt(params.days) || 7 // Default to 7 days
        );
        break;
      }

      // Clear Old Website Requests Action (Admin only)
      case 'clearOldWebsiteRequests': {
        const clearWebsiteAuthHeader = req.headers.authorization;
        const clearWebsiteToken = clearWebsiteAuthHeader && clearWebsiteAuthHeader.startsWith('Bearer ')
          ? clearWebsiteAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(clearWebsiteToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.clearOldWebsiteRequests(
          parseInt(params.days) || 7 // Default to 7 days
        );
        break;
      }
        
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
