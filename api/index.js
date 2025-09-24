// PushNotifications Node.js API
const { MongoClient, ObjectId } = require('mongodb');
const crypto = require('crypto');

// Environment variables
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';
const JWT_SECRET = process.env.JWT_SECRET || 'pushnotifications-secret-key';
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'pushnotifications-encryption-key-32chars';
const SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours

// Encryption constants
const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16; // For GCM, this is always 16
const SALT_LENGTH = 64;
const TAG_LENGTH = 16;
const KEY_LENGTH = 32;

// Encryption utility functions
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
      
      const cipher = crypto.createCipher(ALGORITHM, key);
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
      
      const decipher = crypto.createDecipher(ALGORITHM, key);
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

  static encryptObject(obj, fieldsToEncrypt) {
    if (!obj || !fieldsToEncrypt) return obj;
    
    const encrypted = { ...obj };
    fieldsToEncrypt.forEach(field => {
      if (encrypted[field]) {
        encrypted[`${field}_encrypted`] = this.encrypt(encrypted[field]);
        delete encrypted[field];
      }
    });
    encrypted._encrypted_fields = fieldsToEncrypt;
    return encrypted;
  }

  static decryptObject(obj) {
    if (!obj || !obj._encrypted_fields) return obj;
    
    const decrypted = { ...obj };
    obj._encrypted_fields.forEach(field => {
      const encryptedField = `${field}_encrypted`;
      if (decrypted[encryptedField]) {
        decrypted[field] = this.decrypt(decrypted[encryptedField]);
        delete decrypted[encryptedField];
      }
    });
    delete decrypted._encrypted_fields;
    return decrypted;
  }

  static hashSensitiveData(data) {
    // Create a non-reversible hash for indexing purposes
    return crypto.createHash('sha256').update(data + ENCRYPTION_KEY).digest('hex');
  }
}

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

      // Create indexes for installations collection
      try {
        // Primary lookup indexes
        await this.db.collection('installations').createIndex({ clientId: 1 }, { unique: true });
        await this.db.collection('installations').createIndex({ macAddress: 1 });
        await this.db.collection('installations').createIndex({ userId: 1 });
        await this.db.collection('installations').createIndex({ installationId: 1 }, { unique: true });
        
        // Status and activity indexes
        await this.db.collection('installations').createIndex({ isActive: 1 });
        await this.db.collection('installations').createIndex({ isCurrentForMac: 1 });
        await this.db.collection('installations').createIndex({ macAddress: 1, isCurrentForMac: 1 });
        
        // Time-based indexes
        await this.db.collection('installations').createIndex({ createdAt: -1 });
        await this.db.collection('installations').createIndex({ lastCheckin: -1 });
        await this.db.collection('installations').createIndex({ registeredAt: -1 });
        
        // Combined indexes for common queries
        await this.db.collection('installations').createIndex({ macAddress: 1, isActive: 1 });
        await this.db.collection('installations').createIndex({ userId: 1, isActive: 1 });
        await this.db.collection('installations').createIndex({ hostname: 1 });
        await this.db.collection('installations').createIndex({ platform: 1 });

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
      
      // Check for and sync any new commits (lightweight sync) to ensure current version is up-to-date
      await this.syncNewestCommits();
      
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
      
      // Check for and sync any new commits (lightweight sync)
      await this.syncNewestCommits();
      
      // Fetch from database
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

  async fetchRecentGitHubCommits(limit = 10) {
    try {
      // Check for GitHub token (optional for public repos, but recommended for higher rate limits)
      const githubToken = process.env.GITHUB_TOKEN;
      
      const headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'PushNotifications-API'
      };
      
      if (githubToken) {
        headers['Authorization'] = `Bearer ${githubToken}`;
      }
      
      // Fetch only the most recent commits (lightweight)
      const apiUrl = `https://api.github.com/repos/mirial83/PushNotifications/commits?per_page=${limit}&page=1`;
      
      const response = await fetch(apiUrl, { headers });
      
      if (!response.ok) {
        console.log(`GitHub API error: ${response.status} - ${response.statusText}`);
        return null;
      }
      
      const commits = await response.json();
      
      if (!commits || commits.length === 0) {
        return null;
      }
      
      // Map commits to our format
      const formattedCommits = commits.map((commit, index) => {
        return {
          message: commit.commit.message.split('\n')[0], // First line only
          description: commit.commit.message,
          date: commit.commit.committer.date,
          sha: commit.sha.substring(0, 8),
          author: commit.commit.author.name,
          source: 'github-commits'
        };
      });
      
      return formattedCommits;
      
    } catch (error) {
      console.log('Recent GitHub commits fetch failed:', error.message);
      return null;
    }
  }

  async fetchGitHubCommits() {
    try {
      // Check for GitHub token (optional for public repos, but recommended for higher rate limits)
      const githubToken = process.env.GITHUB_TOKEN;
      
      const headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'PushNotifications-API'
      };
      
      if (githubToken) {
        headers['Authorization'] = `Bearer ${githubToken}`;
      }
      
      // Fetch ALL commits using pagination
      const allCommits = [];
      let page = 1;
      const perPage = 100;
      let hasMorePages = true;
      
      console.log('🚀 Fetching ALL GitHub commits with comprehensive pagination...');
      
      while (hasMorePages && page <= 50) { // Increased limit to 50 pages (5000 commits max)
        const apiUrl = `https://api.github.com/repos/mirial83/PushNotifications/commits?per_page=${perPage}&page=${page}`;
        
        console.log(`📄 Fetching commits page ${page}...`);
        const response = await fetch(apiUrl, { headers });
        
        if (!response.ok) {
          console.log(`❌ GitHub API error on page ${page}: ${response.status} - ${response.statusText}`);
          if (response.status === 404) {
            // Repo not found or no more pages
            hasMorePages = false;
            break;
          } else if (response.status === 403) {
            // Rate limited, wait and try again
            console.log('⏱️ Rate limited, waiting 60 seconds...');
            await new Promise(resolve => setTimeout(resolve, 60000));
            continue;
          } else {
            throw new Error(`GitHub API error: ${response.status} - ${response.statusText}`);
          }
        }
        
        const commits = await response.json();
        
        if (!commits || commits.length === 0) {
          console.log(`📄 Page ${page} returned no commits, stopping pagination`);
          hasMorePages = false;
          break;
        }
        
        allCommits.push(...commits);
        
        // Check if we got less than the requested amount (indicates last page)
        if (commits.length < perPage) {
          console.log(`📄 Page ${page} returned ${commits.length} commits (less than ${perPage}), this is the last page`);
          hasMorePages = false;
        } else {
          page++;
        }
        
        console.log(`   ✅ Got ${commits.length} commits (total so far: ${allCommits.length})`);
        
        // Add delay between pages to avoid rate limiting
        if (page <= 50) {
          await new Promise(resolve => setTimeout(resolve, 500)); // Shorter delay for commits
        }
      }
      
      if (allCommits.length === 0) {
        console.log('❌ No GitHub commits found at all');
        return null;
      }
      
      console.log(`📦 Total commits fetched from GitHub: ${allCommits.length}`);
      
      // Sort commits by date (oldest first) for proper version numbering
      const sortedCommits = allCommits.sort((a, b) => new Date(a.commit.committer.date) - new Date(b.commit.committer.date));
      
      // Map commits to our format with proper versioning
      const formattedCommits = sortedCommits.map((commit, index) => {
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
      });
      
      // Return sorted by date (newest first) for display
      console.log(`📅 Commit date range: ${formattedCommits[0]?.date} to ${formattedCommits[formattedCommits.length - 1]?.date}`);
      return formattedCommits.reverse();
      
    } catch (error) {
      console.log('❌ GitHub commits fetch failed:', error.message);
      console.log('Stack trace:', error.stack);
      return null;
    }
  }

  async fetchGitHubDeployments() {
    try {
      // Check for GitHub token (optional for public repos, but recommended for higher rate limits)
      const githubToken = process.env.GITHUB_TOKEN;
      
      const headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'PushNotifications-API'
      };
      
      if (githubToken) {
        headers['Authorization'] = `Bearer ${githubToken}`;
      }
      
      // Fetch ALL deployments using pagination
      const allDeployments = [];
      let page = 1;
      const perPage = 100;
      let hasMorePages = true;
      
      console.log('🚀 Fetching ALL GitHub deployments with comprehensive pagination...');
      
      while (hasMorePages && page <= 20) { // Increased limit to 20 pages (2000 deployments max)
        const apiUrl = `https://api.github.com/repos/mirial83/PushNotifications/deployments?per_page=${perPage}&page=${page}`;
        
        console.log(`📄 Fetching page ${page}...`);
        const response = await fetch(apiUrl, { headers });
        
        if (!response.ok) {
          console.log(`❌ GitHub API error on page ${page}: ${response.status} - ${response.statusText}`);
          if (response.status === 404) {
            // Repo not found or no more pages
            hasMorePages = false;
            break;
          } else if (response.status === 403) {
            // Rate limited, wait and try again
            console.log('⏱️ Rate limited, waiting 60 seconds...');
            await new Promise(resolve => setTimeout(resolve, 60000));
            continue;
          } else {
            throw new Error(`GitHub API error: ${response.status} - ${response.statusText}`);
          }
        }
        
        const deployments = await response.json();
        
        if (!deployments || deployments.length === 0) {
          console.log(`📄 Page ${page} returned no deployments, stopping pagination`);
          hasMorePages = false;
          break;
        }
        
        allDeployments.push(...deployments);
        
        // Check if we got less than the requested amount (indicates last page)
        if (deployments.length < perPage) {
          console.log(`📄 Page ${page} returned ${deployments.length} deployments (less than ${perPage}), this is the last page`);
          hasMorePages = false;
        } else {
          page++;
        }
        
        console.log(`   ✅ Got ${deployments.length} deployments (total so far: ${allDeployments.length})`);
        
        // Add delay between pages to avoid rate limiting
        if (page <= 20) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      if (allDeployments.length === 0) {
        console.log('❌ No GitHub deployments found at all');
        return null;
      }
      
      console.log(`📦 Total deployments fetched from GitHub: ${allDeployments.length}`);
      
      // TEMPORARILY: Let's be less restrictive and include deployments even without perfect Vercel checks
      const validDeployments = [];
      let processedCount = 0;
      let skippedNoStatus = 0;
      let skippedFailedStatus = 0;
      let includedWithoutVercelChecks = 0;
      let skippedFailedVercelChecks = 0;
      
      console.log(`🔬 Processing ${allDeployments.length} deployments with relaxed filtering...`);
      
      for (const deployment of allDeployments) {
        processedCount++;
        
        if (processedCount % 10 === 0) {
          console.log(`   Processing deployment ${processedCount}/${allDeployments.length}: ${deployment.id}`);
        }
        
        try {
          // Check deployment status
          const statusResponse = await fetch(`https://api.github.com/repos/mirial83/PushNotifications/deployments/${deployment.id}/statuses`, {
            headers
          });
          
          if (!statusResponse.ok) {
            if (statusResponse.status !== 404) {
              console.log(`⚠️ Failed to get deployment status for ${deployment.id}: ${statusResponse.status}`);
            }
            skippedNoStatus++;
            continue;
          }
          
          const statuses = await statusResponse.json();
          const latestStatus = statuses[0]; // Most recent status
          
          // Only proceed if deployment was successful
          if (!latestStatus || latestStatus.state !== 'success') {
            skippedFailedStatus++;
            continue;
          }
          
          // RELAXED APPROACH: Include deployments with successful status, regardless of Vercel checks
          let hasVercelChecks = false;
          let vercelChecksPassed = true;
          
          try {
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
              
              if (vercelChecks.length > 0) {
                hasVercelChecks = true;
                vercelChecksPassed = vercelChecks.every(check => check.state === 'success');
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
                
                if (vercelCheckRuns.length > 0) {
                  hasVercelChecks = true;
                  const allVercelCheckRunsPassed = vercelCheckRuns.every(checkRun => 
                    checkRun.conclusion === 'success' || checkRun.conclusion === 'neutral'
                  );
                  vercelChecksPassed = vercelChecksPassed && allVercelCheckRunsPassed;
                }
              }
            }
          } catch (checkError) {
            // Continue anyway, don't skip due to check errors
            console.log(`⚠️ Error checking Vercel status for ${deployment.id}, but including anyway: ${checkError.message}`);
          }
          
          // RELAXED: Skip only if Vercel checks exist AND failed
          if (hasVercelChecks && !vercelChecksPassed) {
            skippedFailedVercelChecks++;
            continue;
          }
          
          // Include this deployment
          if (!hasVercelChecks) {
            includedWithoutVercelChecks++;
          }
          
          // Get commit info for better messages
          let commitMessage = deployment.description || deployment.payload?.description || `Deployment ${deployment.id}`;
          let commitAuthor = deployment.creator?.login || 'Unknown';
          
          if (deployment.sha) {
            try {
              const commitResponse = await fetch(`https://api.github.com/repos/mirial83/PushNotifications/commits/${deployment.sha}`, {
                headers
              });
              
              if (commitResponse.ok) {
                const commitData = await commitResponse.json();
                commitMessage = commitData.commit.message.split('\n')[0]; // First line only
                commitAuthor = commitData.commit.author.name;
              }
            } catch (commitError) {
              // Use deployment info if commit fetch fails
            }
          }
          
          validDeployments.push({
            ...deployment,
            status: latestStatus,
            commitMessage: commitMessage,
            commitAuthor: commitAuthor
          });
          
          // Add a small delay to avoid rate limiting
          if (processedCount % 20 === 0) {
            await new Promise(resolve => setTimeout(resolve, 500));
          }
          
        } catch (checkError) {
          console.log(`❌ Error processing deployment ${deployment.id}: ${checkError.message}`);
          continue;
        }
      }
      
      console.log(`\n📊 DEPLOYMENT PROCESSING RESULTS:`);
      console.log(`   Total deployments fetched: ${allDeployments.length}`);
      console.log(`   Total processed: ${processedCount}`);
      console.log(`   ✅ Valid deployments: ${validDeployments.length}`);
      console.log(`   ❌ Skipped (no status): ${skippedNoStatus}`);
      console.log(`   ❌ Skipped (failed status): ${skippedFailedStatus}`);
      console.log(`   ⚠️ Included without Vercel checks: ${includedWithoutVercelChecks}`);
      console.log(`   ❌ Skipped (failed Vercel checks): ${skippedFailedVercelChecks}`);
      
      if (validDeployments.length === 0) {
        console.log('❌ No valid deployments found after processing');
        return null;
      }
      
      if (validDeployments.length === 1) {
        console.log('⚠️ WARNING: Only 1 valid deployment found! This might indicate overly restrictive filtering.');
      }
      
      console.log(`🎉 Found ${validDeployments.length} deployments to sync out of ${allDeployments.length} total`);
      
      // Sort by date (oldest first) to maintain chronological order
      validDeployments.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      
      console.log(`📅 Date range: ${validDeployments[0]?.created_at} to ${validDeployments[validDeployments.length - 1]?.created_at}`);
      
      // Convert to our format
      return validDeployments.map((deployment, index) => ({
        version: null, // Will be set by version numbering
        message: deployment.commitMessage,
        description: deployment.commitMessage,
        date: deployment.created_at,
        deploymentId: deployment.id.toString(),
        sha: deployment.sha ? deployment.sha.substring(0, 8) : null,
        url: deployment.status?.target_url || deployment.status?.environment_url || null,
        source: 'github-deployments',
        isCurrent: false, // Will be set later
        author: deployment.commitAuthor,
        environment: deployment.environment || 'production'
      }));
      
    } catch (error) {
      console.log('❌ GitHub deployments fetch failed:', error.message);
      console.log('Stack trace:', error.stack);
      return null;
    }
  }

  async getFallbackVersionHistory() {
    // Fallback static version history
    const deployments = [
      { message: 'Current version - Node.js/MongoDB/Vercel implementation', isCurrent: true },
      { message: 'Website authentication and user management', isCurrent: false },
      { message: 'Security features and MAC address client tracking', isCurrent: false },
      { message: 'Database implementation with Node.js/MongoDB', isCurrent: false },
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

  async registerClientInstallation(installationData) {
    try {
      const {
        installationKey,
        macAddress,
        username,
        clientName,
        hostname,
        platform,
        version,
        installPath,
        macDetectionMethod,
        installerMode,
        timestamp,
        systemInfo
      } = installationData;

      if (this.usesFallback) {
        // Fallback storage for simple registration
        const clientId = `${username}_${macAddress.replace(/[:-]/g, '').slice(-6)}`;
        const client = {
          clientId,
          clientName: clientName || `${username}1`,
          macAddress,
          hostname,
          platform,
          version,
          registered: timestamp || new Date().toISOString(),
          lastSeen: new Date().toISOString()
        };
        fallbackStorage.clients.push(client);
        
        return {
          success: true,
          message: 'Client registered in fallback storage',
          clientId,
          keyId: `key_${macAddress}_${Date.now()}`,
          isNewInstallation: true
        };
      }

      await this.connect();
      const now = new Date();

      // First, validate the installation key and mark it as used during successful registration
      const keyValidation = await this.validateInstallationKey(installationKey, true);
      if (!keyValidation.success) {
        return { success: false, message: 'Invalid installation key' };
      }

      // Check existing installations for this MAC address
      const existingInstallations = await this.db.collection('installations')
        .find({ macAddress, isCurrentForMac: true })
        .toArray();
      
      // Deactivate any existing current installation for this MAC
      if (existingInstallations.length > 0) {
        await this.db.collection('installations').updateMany(
          { macAddress, isCurrentForMac: true },
          { 
            $set: { 
              isActive: false,
              isCurrentForMac: false,
              deactivatedAt: now,
              deactivationReason: 'New installation on same MAC address'
            }
          }
        );
      }
      
      // Count previous installations for this MAC to determine installation count
      const installationCount = await this.db.collection('installations')
        .countDocuments({ macAddress }) + 1;
      
      // Generate client ID and names
      const generatedClientName = clientName || `${username}${installationCount}`;
      const clientId = `${username}_${macAddress.replace(/[:-]/g, '').slice(-6)}_${installationCount}`;
      const installationId = `inst_${macAddress.replace(/[:-]/g, '')}_${installationCount}`;
      const keyId = `key_${macAddress.replace(/[:-]/g, '')}_${Date.now()}`;
      
      // Generate security key for embedding
      const securityKeyValue = this.generateInstallationKey();

      // Store comprehensive installation record with encrypted sensitive data
      const installationRecord = {
        installationId,
        clientId,
        installationKey,
        keyId,
        
        // MAC address and device info (encrypted)
        macAddress: CryptoUtils.encrypt(macAddress),
        macAddress_hash: CryptoUtils.hashSensitiveData(macAddress), // For indexing
        macDetectionMethod,
        
        // User information
        username,
        clientName: generatedClientName,
        userId: keyValidation.user ? new ObjectId(keyValidation.user.id) : null,
        userRole: keyValidation.user ? keyValidation.user.role : 'user',
        
        // System information (encrypt sensitive paths)
        hostname: CryptoUtils.encrypt(hostname),
        platform,
        version,
        installPath: CryptoUtils.encrypt(installPath),
        systemInfo: systemInfo ? CryptoUtils.encrypt(JSON.stringify(systemInfo)) : null,
        _encrypted_fields: ['macAddress', 'hostname', 'installPath', 'systemInfo'],
        
        // Installation metadata
        installerMode,
        registeredAt: timestamp || now.toISOString(),
        createdAt: now,
        lastCheckin: now,
        
        // Status and activity
        isActive: true,
        isCurrentForMac: true,
        installationCount,
        
        // Deactivation info (initially null)
        deactivatedAt: null,
        deactivationReason: null,
        
        // Security keys (embedded)
        securityKeys: {
          encryptionKey: {
            keyValue: securityKeyValue,
            keyType: 'ENCRYPTION_KEY',
            createdAt: now,
            lastUsed: now
          }
        },
        
        // Installation history tracking
        installationHistory: {
          previousInstallations: Math.max(0, installationCount - 1),
          isReinstallation: installationCount > 1,
          replacedInstallationId: existingInstallations.length > 0 ? existingInstallations[0].installationId : null
        },
        
        // Default policy
        policy: {
          allowWebsiteRequests: true,
          snoozeEnabled: true,
          updateCheckInterval: 86400,
          heartbeatInterval: 300
        }
      };

      // Insert into installations collection
      await this.db.collection('installations').insertOne(installationRecord);

      // Report the installation
      await this.reportInstallation(
        keyId,
        macAddress,
        installPath,
        version,
        'completed',
        timestamp || now.toISOString(),
        {
          clientId,
          username,
          hostname,
          platform,
          macDetectionMethod,
          installerMode,
          systemInfo
        }
      );

      return {
        success: true,
        message: 'Client installation registered successfully',
        clientId,
        keyId,
        isNewInstallation: installationCount === 1,
        macAddress,
        clientName,
        policy: {
          allowWebsiteRequests: true,
          snoozeEnabled: true,
          updateCheckInterval: 86400,
          heartbeatInterval: 300
        }
      };
    } catch (error) {
      console.error('Client installation registration error:', error);
      return { success: false, message: error.message };
    }
  }

  // Scheduled Notifications Management
  async scheduleNotification(message, scheduledTime, allowBrowserUsage = false, allowedWebsites = '', sendingUserId = null, sendingUserRole = null, targetClientId = null, recurring = null) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Scheduled notifications require MongoDB connection' };
      }

      await this.connect();
      
      const scheduledNotification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        message,
        clientId: targetClientId || 'all',
        scheduledTime: new Date(scheduledTime),
        status: 'scheduled',
        allowBrowserUsage,
        allowedWebsites,
        sentBy: sendingUserId,
        senderRole: sendingUserRole,
        recurring: recurring || null, // { pattern: 'daily|weekly|monthly', interval: 1, endDate: null }
        created: new Date(),
        sent: false,
        sentAt: null
      };
      
      await this.db.collection('scheduledNotifications').insertOne(scheduledNotification);
      
      return {
        success: true,
        message: 'Notification scheduled successfully',
        notificationId: scheduledNotification.id,
        scheduledTime: scheduledNotification.scheduledTime
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getScheduledNotifications(sendingUserId = null, sendingUserRole = null) {
    try {
      if (this.usesFallback) {
        return { success: true, data: [] };
      }

      await this.connect();
      
      // Build query based on user role
      let query = {};
      if (sendingUserRole === 'admin') {
        // Regular admins can only see their scheduled notifications
        query.sentBy = sendingUserId;
      } else if (sendingUserRole === 'master_admin') {
        // Master admins can see all scheduled notifications
        query = {};
      } else {
        // Regular users can only see their own
        query.sentBy = sendingUserId;
      }
      
      const notifications = await this.db.collection('scheduledNotifications')
        .find(query)
        .sort({ scheduledTime: 1 })
        .toArray();
      
      return {
        success: true,
        data: notifications.map(n => ({
          id: n.id,
          message: n.message,
          clientId: n.clientId,
          scheduledTime: n.scheduledTime,
          status: n.status,
          allowBrowserUsage: n.allowBrowserUsage,
          allowedWebsites: n.allowedWebsites,
          recurring: n.recurring,
          created: n.created,
          sent: n.sent,
          sentAt: n.sentAt
        }))
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async processScheduledNotifications() {
    try {
      if (this.usesFallback) {
        return { success: true, processed: 0 };
      }

      await this.connect();
      const now = new Date();
      
      // Find notifications that should be sent now
      const dueNotifications = await this.db.collection('scheduledNotifications')
        .find({
          scheduledTime: { $lte: now },
          status: 'scheduled',
          sent: false
        })
        .toArray();
      
      let processedCount = 0;
      
      for (const notification of dueNotifications) {
        try {
          // Send the notification
          const sendResult = await this.sendNotificationToAllClients(
            notification.message,
            notification.allowBrowserUsage,
            notification.allowedWebsites,
            notification.sentBy,
            notification.senderRole,
            notification.clientId !== 'all' ? notification.clientId : null
          );
          
          if (sendResult.success) {
            // Mark as sent
            await this.db.collection('scheduledNotifications').updateOne(
              { _id: notification._id },
              { 
                $set: { 
                  sent: true, 
                  sentAt: now,
                  status: 'sent'
                }
              }
            );
            
            // Handle recurring notifications
            if (notification.recurring) {
              await this.createRecurringNotification(notification);
            }
            
            processedCount++;
          }
        } catch (error) {
          console.error(`Error processing scheduled notification ${notification.id}:`, error);
          // Mark as failed
          await this.db.collection('scheduledNotifications').updateOne(
            { _id: notification._id },
            { 
              $set: { 
                status: 'failed',
                errorMessage: error.message,
                failedAt: now
              }
            }
          );
        }
      }
      
      return {
        success: true,
        processed: processedCount,
        found: dueNotifications.length
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async createRecurringNotification(originalNotification) {
    try {
      if (!originalNotification.recurring) {
        return { success: false, message: 'Not a recurring notification' };
      }
      
      const { pattern, interval = 1, endDate } = originalNotification.recurring;
      let nextScheduledTime = new Date(originalNotification.scheduledTime);
      
      // Calculate next occurrence
      switch (pattern) {
        case 'daily':
          nextScheduledTime.setDate(nextScheduledTime.getDate() + interval);
          break;
        case 'weekly':
          nextScheduledTime.setDate(nextScheduledTime.getDate() + (interval * 7));
          break;
        case 'monthly':
          nextScheduledTime.setMonth(nextScheduledTime.getMonth() + interval);
          break;
        default:
          return { success: false, message: 'Invalid recurring pattern' };
      }
      
      // Check if we've reached the end date
      if (endDate && nextScheduledTime > new Date(endDate)) {
        return { success: true, message: 'Recurring notification series completed' };
      }
      
      // Create next occurrence
      const nextNotification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        message: originalNotification.message,
        clientId: originalNotification.clientId,
        scheduledTime: nextScheduledTime,
        status: 'scheduled',
        allowBrowserUsage: originalNotification.allowBrowserUsage,
        allowedWebsites: originalNotification.allowedWebsites,
        sentBy: originalNotification.sentBy,
        senderRole: originalNotification.senderRole,
        recurring: originalNotification.recurring,
        created: new Date(),
        sent: false,
        sentAt: null,
        parentNotificationId: originalNotification.id
      };
      
      await this.db.collection('scheduledNotifications').insertOne(nextNotification);
      
      return {
        success: true,
        message: 'Next recurring notification created',
        nextScheduledTime
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async cancelScheduledNotification(notificationId, userId, userRole) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Scheduled notifications require MongoDB connection' };
      }

      await this.connect();
      
      // Build query based on user role for security
      let query = { id: notificationId };
      if (userRole === 'admin') {
        query.sentBy = userId; // Admins can only cancel their own
      }
      // Master admins can cancel any notification
      
      const result = await this.db.collection('scheduledNotifications').updateOne(
        query,
        { 
          $set: { 
            status: 'cancelled',
            cancelledAt: new Date(),
            cancelledBy: userId
          }
        }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'Notification not found or access denied' };
      }
      
      return {
        success: true,
        message: 'Scheduled notification cancelled successfully'
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async sendNotificationToAllClients(message, allowBrowserUsage = false, allowedWebsites = '', sendingUserId = null, sendingUserRole = null, targetClientId = null) {
    try {
      const notification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        message,
        clientId: targetClientId || 'all',
        status: 'Active',
        allowBrowserUsage,
        allowedWebsites,
        created: new Date().toISOString(),
        sentBy: sendingUserId,
        senderRole: sendingUserRole
      };

      // Apply role-based filtering for client targeting
      let targetedClientCount = 0;
      
      if (this.usesFallback) {
        fallbackStorage.notifications.push(notification);
        targetedClientCount = fallbackStorage.clients.length;
      } else {
        await this.connect();
        
        // Count clients based on user role and hierarchy
        if (sendingUserRole === 'admin') {
          // Regular admins can only send to clients associated with users they created
          const createdUsers = await this.db.collection('users')
            .find({ createdBy: sendingUserId }, { projection: { _id: 1 } })
            .toArray();
          
          const userIds = createdUsers.map(user => user._id);
          userIds.push(new ObjectId(sendingUserId)); // Include the admin's own clients if any
          
          if (targetClientId && targetClientId !== 'all') {
            // Check if the specific client belongs to the admin's users
            const targetInstallation = await this.db.collection('installations').findOne({
              clientId: targetClientId,
              userId: { $in: userIds },
              isActive: true
            });
            
            if (!targetInstallation) {
              return {
                success: false,
                message: 'You do not have permission to send notifications to this client'
              };
            }
            
            targetedClientCount = 1;
          } else {
            // Count all clients associated with the admin's users
            targetedClientCount = await this.db.collection('installations')
              .countDocuments({
                userId: { $in: userIds },
                isActive: true,
                isCurrentForMac: true
              });
          }
        } else if (sendingUserRole === 'master_admin') {
          // Master admins can send to all clients
          if (targetClientId && targetClientId !== 'all') {
            const targetInstallation = await this.db.collection('installations').findOne({
              clientId: targetClientId,
              isActive: true
            });
            
            if (!targetInstallation) {
              return {
                success: false,
                message: 'Target client not found or inactive'
              };
            }
            
            targetedClientCount = 1;
          } else {
            targetedClientCount = await this.db.collection('installations')
              .countDocuments({
                isActive: true,
                isCurrentForMac: true
              });
          }
        } else if (sendingUserRole === 'user') {
          // Regular users can only send to their own clients
          const userObjectId = new ObjectId(sendingUserId);
          
          if (targetClientId && targetClientId !== 'all') {
            // Check if the specific client belongs to the user
            const targetInstallation = await this.db.collection('installations').findOne({
              clientId: targetClientId,
              userId: userObjectId,
              isActive: true
            });
            
            if (!targetInstallation) {
              return {
                success: false,
                message: 'You do not have permission to send notifications to this client'
              };
            }
            
            targetedClientCount = 1;
          } else {
            // Set clientId to user-specific targeting
            notification.clientId = `user_${sendingUserId}`;
            targetedClientCount = await this.db.collection('installations')
              .countDocuments({
                userId: userObjectId,
                isActive: true,
                isCurrentForMac: true
              });
          }
        } else {
          return {
            success: false,
            message: 'Invalid user role for sending notifications'
          };
        }
        
        await this.db.collection('notifications').insertOne(notification);
      }

      return {
        success: true,
        message: `Notification sent to ${targetedClientCount} client(s)`,
        clientCount: targetedClientCount,
        targetedClients: targetedClientCount,
        notificationId: notification.id
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
        created: new Date().toISOString(),
        autoExpire: true, // Mark for automatic cleanup
        expireAfter: new Date(Date.now() + 10 * 60 * 1000) // Auto-expire after 10 minutes
      };

      if (this.usesFallback) {
        fallbackStorage.notifications.push(uninstallNotification);
      } else {
        await this.connect();
        await this.db.collection('notifications').insertOne(uninstallNotification);
      }

      // Schedule automatic cleanup of this command notification after 10 minutes
      setTimeout(async () => {
        await this.cleanupExpiredUninstallCommands();
      }, 10 * 60 * 1000);

      return {
        success: true,
        message: `Uninstall command sent to ${clientCount} active client(s)`,
        clientCount,
        notificationId: uninstallNotification.id
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
        // Filter out uninstall requests and uninstall commands from regular notifications
        notifications = fallbackStorage.notifications.filter(n => 
          n.status !== 'Completed' && 
          n.type !== 'uninstall_request' && 
          n.type !== 'uninstall_command'
        );
      } else {
        await this.connect();
        notifications = await this.db.collection('notifications')
          .find({ 
            status: { $ne: 'Completed' },
            type: { $nin: ['uninstall_request', 'uninstall_command'] }
          })
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
        type: n.type,
        clientId: n.clientId,
        reason: n.reason,
        allowBrowserUsage: n.allowBrowserUsage || false,
        allowedWebsites: Array.isArray(n.allowedWebsites) 
          ? n.allowedWebsites 
          : (n.allowedWebsites ? n.allowedWebsites.split(',') : []),
        created: n.created
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

  async clearAllNotifications() {
    try {
      let clearedCount = 0;
      
      if (this.usesFallback) {
        clearedCount = fallbackStorage.notifications.length;
        fallbackStorage.notifications = [];
      } else {
        await this.connect();
        const result = await this.db.collection('notifications').deleteMany({
          status: { $ne: 'Completed' } // Clear all notifications except completed ones
        });
        clearedCount = result.deletedCount;
      }

      return {
        success: true,
        message: `Cleared all ${clearedCount} active notifications successfully`,
        clearedCount
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Uninstall Request Management Methods
  async requestUninstall(clientId, macAddress, keyId, installPath, timestamp, reason = 'Force quit detected') {
    try {
      // First check if the client is still active in the database
      let clientIsActive = false;
      
      if (this.usesFallback) {
        // Check fallback storage for active client
        clientIsActive = fallbackStorage.clients && fallbackStorage.clients.some(c => 
          c.clientId === clientId || c.macAddress === macAddress
        );
      } else {
        await this.connect();
        // Check both clients and macClients collections for active registrations
        const client = await this.db.collection('clients').findOne({ clientId });
        const macClient = await this.db.collection('macClients').findOne({ 
          $or: [{ clientId }, { activeClientId: clientId }, { macAddress }] 
        });
        clientIsActive = client || macClient;
      }

      // If client is not active in database, allow immediate uninstall
      if (!clientIsActive) {
        // Create an immediate uninstall command notification
        const uninstallNotification = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          message: '__UNINSTALL_APPROVED_COMMAND__',
          clientId: clientId,
          status: 'Active',
          type: 'uninstall_command',
          reason: `Auto-approved: ${reason} (client not found in database)`,
          allowBrowserUsage: false,
          allowedWebsites: '',
          created: new Date().toISOString()
        };

        if (this.usesFallback) {
          fallbackStorage.notifications.push(uninstallNotification);
        } else {
          await this.db.collection('notifications').insertOne(uninstallNotification);
        }

        return {
          success: true,
          message: 'Uninstall approved automatically (client not registered in database)',
          autoApproved: true,
          notificationId: uninstallNotification.id
        };
      }

      // Client is still active, create traditional uninstall request for approval
      const uninstallRequest = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        clientId,
        macAddress,
        keyId,
        installPath,
        reason,
        status: 'pending',
        type: 'uninstall_request',
        requestedAt: timestamp || new Date().toISOString(),
        created: new Date().toISOString()
      };

      if (this.usesFallback) {
        // Add to in-memory storage in a separate uninstall requests collection
        if (!fallbackStorage.uninstallRequests) {
          fallbackStorage.uninstallRequests = [];
        }
        fallbackStorage.uninstallRequests.push(uninstallRequest);
      } else {
        await this.connect();
        await this.db.collection('uninstallRequests').insertOne(uninstallRequest);
      }

      return {
        success: true,
        message: 'Uninstall request submitted successfully (requires approval)',
        autoApproved: false,
        requestId: uninstallRequest.id
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getUninstallRequests() {
    try {
      let requests;
      
      if (this.usesFallback) {
        if (!fallbackStorage.uninstallRequests) {
          fallbackStorage.uninstallRequests = [];
        }
        requests = fallbackStorage.uninstallRequests.filter(req => req.status === 'pending');
      } else {
        await this.connect();
        requests = await this.db.collection('uninstallRequests')
          .find({ status: 'pending' })
          .sort({ requestedAt: -1 })
          .toArray();
      }

      return { success: true, data: requests };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async approveUninstallRequest(requestId, adminUsername) {
    try {
      if (this.usesFallback) {
        if (!fallbackStorage.uninstallRequests) {
          return { success: false, message: 'Uninstall request not found' };
        }
        
        const request = fallbackStorage.uninstallRequests.find(req => req.id === requestId);
        if (!request) {
          return { success: false, message: 'Uninstall request not found' };
        }
        
        // Update the request status
        request.status = 'approved';
        request.approvedBy = adminUsername;
        request.approvedAt = new Date().toISOString();
        
        // Create an uninstall command notification for the client
        const uninstallNotification = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          message: '__UNINSTALL_APPROVED_COMMAND__',
          clientId: request.clientId,
          status: 'Active',
          type: 'uninstall_command',
          reason: `Uninstall approved: ${request.reason}`,
          allowBrowserUsage: false,
          allowedWebsites: '',
          created: new Date().toISOString()
        };
        
        fallbackStorage.notifications.push(uninstallNotification);
        
        return {
          success: true,
          message: `Uninstall request approved and uninstall command sent to client ${request.clientId}`,
          clientId: request.clientId
        };
      } else {
        await this.connect();
        
        // Find and update the request
        const request = await this.db.collection('uninstallRequests').findOne({ id: requestId, status: 'pending' });
        if (!request) {
          return { success: false, message: 'Uninstall request not found or already processed' };
        }
        
        // Update the request status
        await this.db.collection('uninstallRequests').updateOne(
          { id: requestId },
          {
            $set: {
              status: 'approved',
              approvedBy: adminUsername,
              approvedAt: new Date().toISOString()
            }
          }
        );
        
        // Create an uninstall command notification for the client
        const uninstallNotification = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          message: '__UNINSTALL_APPROVED_COMMAND__',
          clientId: request.clientId,
          status: 'Active',
          type: 'uninstall_command',
          reason: `Uninstall approved: ${request.reason}`,
          allowBrowserUsage: false,
          allowedWebsites: '',
          created: new Date().toISOString()
        };
        
        await this.db.collection('notifications').insertOne(uninstallNotification);
        
        return {
          success: true,
          message: `Uninstall request approved and uninstall command sent to client ${request.clientId}`,
          clientId: request.clientId
        };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async denyUninstallRequest(requestId, reason, adminUsername) {
    try {
      if (this.usesFallback) {
        if (!fallbackStorage.uninstallRequests) {
          return { success: false, message: 'Uninstall request not found' };
        }
        
        const request = fallbackStorage.uninstallRequests.find(req => req.id === requestId);
        if (!request) {
          return { success: false, message: 'Uninstall request not found' };
        }
        
        // Update the request status
        request.status = 'denied';
        request.deniedBy = adminUsername;
        request.deniedAt = new Date().toISOString();
        request.denialReason = reason;
        
        return {
          success: true,
          message: `Uninstall request denied for client ${request.clientId}`,
          clientId: request.clientId
        };
      } else {
        await this.connect();
        
        // Find and update the request
        const request = await this.db.collection('uninstallRequests').findOne({ id: requestId, status: 'pending' });
        if (!request) {
          return { success: false, message: 'Uninstall request not found or already processed' };
        }
        
        // Update the request status
        await this.db.collection('uninstallRequests').updateOne(
          { id: requestId },
          {
            $set: {
              status: 'denied',
              deniedBy: adminUsername,
              deniedAt: new Date().toISOString(),
              denialReason: reason
            }
          }
        );
        
        return {
          success: true,
          message: `Uninstall request denied for client ${request.clientId}`,
          clientId: request.clientId
        };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Website Request Management Methods
  async approveWebsiteRequest(requestId, adminUsername) {
    try {
      if (this.usesFallback) {
        // Look for website request in notifications (since they might be stored there)
        const requestIndex = fallbackStorage.notifications.findIndex(
          n => (n.id === requestId || n._id === requestId) && n.type === 'website_request' && n.status === 'pending'
        );
        
        if (requestIndex === -1) {
          return { success: false, message: 'Website request not found or already processed' };
        }
        
        const request = fallbackStorage.notifications[requestIndex];
        
        // Update the request status
        request.status = 'approved';
        request.approvedBy = adminUsername;
        request.approvedAt = new Date().toISOString();
        
        // Create a website approval notification for the client
        const approvalNotification = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          message: '__WEBSITE_APPROVED_COMMAND__',
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url,
          status: 'Active',
          type: 'website_approval',
          allowBrowserUsage: false,
          allowedWebsites: '',
          created: new Date().toISOString()
        };
        
        fallbackStorage.notifications.push(approvalNotification);
        
        // Remove the original request from active notifications list
        fallbackStorage.notifications.splice(requestIndex, 1);
        
        return {
          success: true,
          message: `Website access approved for ${request.websiteUrl || request.url}`,
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url
        };
      } else {
        await this.connect();
        
        // Look in both notifications and websiteRequests collections
        let request;
        
        // Try with string ID first, then ObjectId if it's a valid ObjectId
        const query = { type: 'website_request', status: 'pending' };
        if (requestId.length === 24) {
          // Might be an ObjectId
          query.$or = [{ id: requestId }, { _id: new ObjectId(requestId) }];
        } else {
          query.id = requestId;
        }
        
        request = await this.db.collection('notifications').findOne(query);
        
        if (!request) {
          // Try websiteRequests collection as backup
          const websiteQuery = { status: 'pending' };
          if (requestId.length === 24) {
            websiteQuery.$or = [{ id: requestId }, { _id: new ObjectId(requestId) }];
          } else {
            websiteQuery.id = requestId;
          }
          request = await this.db.collection('websiteRequests').findOne(websiteQuery);
        }
        
        if (!request) {
          return { success: false, message: 'Website request not found or already processed' };
        }
        
        // Update the request status in the original collection
        const updateData = {
          status: 'approved',
          approvedBy: adminUsername,
          approvedAt: new Date().toISOString()
        };
        
        if (request.type === 'website_request') {
          const updateQuery = requestId.length === 24 ? 
            { $or: [{ id: requestId }, { _id: new ObjectId(requestId) }] } : 
            { id: requestId };
          await this.db.collection('notifications').updateOne(updateQuery, { $set: updateData });
        } else {
          const updateQuery = requestId.length === 24 ? 
            { $or: [{ id: requestId }, { _id: new ObjectId(requestId) }] } : 
            { id: requestId };
          await this.db.collection('websiteRequests').updateOne(updateQuery, { $set: updateData });
        }
        
        // Create a website approval notification for the client
        const approvalNotification = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          message: '__WEBSITE_APPROVED_COMMAND__',
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url,
          status: 'Active',
          type: 'website_approval',
          allowBrowserUsage: false,
          allowedWebsites: '',
          created: new Date().toISOString()
        };
        
        await this.db.collection('notifications').insertOne(approvalNotification);
        
        return {
          success: true,
          message: `Website access approved for ${request.websiteUrl || request.url}`,
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url
        };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }
  
  async denyWebsiteRequest(requestId, reason, adminUsername) {
    try {
      if (this.usesFallback) {
        // Look for website request in notifications
        const requestIndex = fallbackStorage.notifications.findIndex(
          n => (n.id === requestId || n._id === requestId) && n.type === 'website_request' && n.status === 'pending'
        );
        
        if (requestIndex === -1) {
          return { success: false, message: 'Website request not found or already processed' };
        }
        
        const request = fallbackStorage.notifications[requestIndex];
        
        // Update the request status
        request.status = 'denied';
        request.deniedBy = adminUsername;
        request.deniedAt = new Date().toISOString();
        request.denialReason = reason;
        
        // Create a website denial notification for the client
        const denialNotification = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          message: '__WEBSITE_DENIED_COMMAND__',
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url,
          denialReason: reason,
          status: 'Active',
          type: 'website_denial',
          allowBrowserUsage: false,
          allowedWebsites: '',
          created: new Date().toISOString()
        };
        
        fallbackStorage.notifications.push(denialNotification);
        
        // Remove the original request from active notifications list
        fallbackStorage.notifications.splice(requestIndex, 1);
        
        return {
          success: true,
          message: `Website access denied for ${request.websiteUrl || request.url}`,
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url
        };
      } else {
        await this.connect();
        
        // Look in both notifications and websiteRequests collections
        let request;
        
        // Try with string ID first, then ObjectId if it's a valid ObjectId
        const query = { type: 'website_request', status: 'pending' };
        if (requestId.length === 24) {
          // Might be an ObjectId
          query.$or = [{ id: requestId }, { _id: new ObjectId(requestId) }];
        } else {
          query.id = requestId;
        }
        
        request = await this.db.collection('notifications').findOne(query);
        
        if (!request) {
          // Try websiteRequests collection as backup
          const websiteQuery = { status: 'pending' };
          if (requestId.length === 24) {
            websiteQuery.$or = [{ id: requestId }, { _id: new ObjectId(requestId) }];
          } else {
            websiteQuery.id = requestId;
          }
          request = await this.db.collection('websiteRequests').findOne(websiteQuery);
        }
        
        if (!request) {
          return { success: false, message: 'Website request not found or already processed' };
        }
        
        // Update the request status in the original collection
        const updateData = {
          status: 'denied',
          deniedBy: adminUsername,
          deniedAt: new Date().toISOString(),
          denialReason: reason
        };
        
        if (request.type === 'website_request') {
          const updateQuery = requestId.length === 24 ? 
            { $or: [{ id: requestId }, { _id: new ObjectId(requestId) }] } : 
            { id: requestId };
          await this.db.collection('notifications').updateOne(updateQuery, { $set: updateData });
        } else {
          const updateQuery = requestId.length === 24 ? 
            { $or: [{ id: requestId }, { _id: new ObjectId(requestId) }] } : 
            { id: requestId };
          await this.db.collection('websiteRequests').updateOne(updateQuery, { $set: updateData });
        }
        
        // Create a website denial notification for the client
        const denialNotification = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          message: '__WEBSITE_DENIED_COMMAND__',
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url,
          denialReason: reason,
          status: 'Active',
          type: 'website_denial',
          allowBrowserUsage: false,
          allowedWebsites: '',
          created: new Date().toISOString()
        };
        
        await this.db.collection('notifications').insertOne(denialNotification);
        
        return {
          success: true,
          message: `Website access denied for ${request.websiteUrl || request.url}`,
          clientId: request.clientId,
          websiteUrl: request.websiteUrl || request.url
        };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Notification Management Methods
  async acknowledgeNotification(notificationId, adminUsername) {
    try {
      if (this.usesFallback) {
        const notificationIndex = fallbackStorage.notifications.findIndex(
          n => (n.id === notificationId || n._id === notificationId) && n.status !== 'completed'
        );
        
        if (notificationIndex === -1) {
          return { success: false, message: 'Notification not found or already completed' };
        }
        
        const notification = fallbackStorage.notifications[notificationIndex];
        
        // Update the notification status
        notification.status = 'completed';
        notification.acknowledgedBy = adminUsername;
        notification.acknowledgedAt = new Date().toISOString();
        
        return {
          success: true,
          message: `Notification acknowledged and marked as complete`,
          clientId: notification.clientId
        };
      } else {
        await this.connect();
        
        // Look for notification in notifications collection
        const query = notificationId.length === 24 ? 
          { $or: [{ id: notificationId }, { _id: new ObjectId(notificationId) }] } : 
          { id: notificationId };
        
        const notification = await this.db.collection('notifications').findOne({
          ...query,
          status: { $ne: 'completed' }
        });
        
        if (!notification) {
          return { success: false, message: 'Notification not found or already completed' };
        }
        
        // Update the notification status
        await this.db.collection('notifications').updateOne(
          query,
          {
            $set: {
              status: 'completed',
              acknowledgedBy: adminUsername,
              acknowledgedAt: new Date().toISOString()
            }
          }
        );
        
        return {
          success: true,
          message: `Notification acknowledged and marked as complete`,
          clientId: notification.clientId
        };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async snoozeNotification(notificationId, minutes, adminUsername) {
    try {
      if (this.usesFallback) {
        const notificationIndex = fallbackStorage.notifications.findIndex(
          n => (n.id === notificationId || n._id === notificationId) && n.status !== 'completed'
        );
        
        if (notificationIndex === -1) {
          return { success: false, message: 'Notification not found or already completed' };
        }
        
        const notification = fallbackStorage.notifications[notificationIndex];
        
        // Calculate snooze until time
        const snoozeUntil = new Date();
        snoozeUntil.setMinutes(snoozeUntil.getMinutes() + minutes);
        
        // Update the notification status
        notification.status = 'snoozed';
        notification.snoozeUntil = snoozeUntil.toISOString();
        notification.snoozedBy = adminUsername;
        notification.snoozedAt = new Date().toISOString();
        notification.snoozeMinutes = minutes;
        
        return {
          success: true,
          message: `Notification snoozed for ${minutes} minutes`,
          clientId: notification.clientId,
          snoozeUntil: snoozeUntil.toISOString()
        };
      } else {
        await this.connect();
        
        // Look for notification in notifications collection
        const query = notificationId.length === 24 ? 
          { $or: [{ id: notificationId }, { _id: new ObjectId(notificationId) }] } : 
          { id: notificationId };
        
        const notification = await this.db.collection('notifications').findOne({
          ...query,
          status: { $ne: 'completed' }
        });
        
        if (!notification) {
          return { success: false, message: 'Notification not found or already completed' };
        }
        
        // Calculate snooze until time
        const snoozeUntil = new Date();
        snoozeUntil.setMinutes(snoozeUntil.getMinutes() + minutes);
        
        // Update the notification status
        await this.db.collection('notifications').updateOne(
          query,
          {
            $set: {
              status: 'snoozed',
              snoozeUntil: snoozeUntil.toISOString(),
              snoozedBy: adminUsername,
              snoozedAt: new Date().toISOString(),
              snoozeMinutes: minutes
            }
          }
        );
        
        return {
          success: true,
          message: `Notification snoozed for ${minutes} minutes`,
          clientId: notification.clientId,
          snoozeUntil: snoozeUntil.toISOString()
        };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Custom Message Management Methods
  async saveCustomMessage(text, description, allowBrowserUsage, allowedWebsites, adminUsername) {
    try {
      // Validate required fields
      if (!text || text.trim().length === 0) {
        return { success: false, message: 'Message text is required' };
      }

      if (this.usesFallback) {
        // For fallback mode, store in memory (won't persist)
        if (!fallbackStorage.customMessages) {
          fallbackStorage.customMessages = [];
        }
        
        // Check if message already exists
        const existingMessage = fallbackStorage.customMessages.find(msg => msg.text.trim() === text.trim());
        if (existingMessage) {
          return { success: false, message: 'A message with this text already exists' };
        }
        
        const messageData = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          text: text.trim(),
          description: description?.trim() || 'Custom message',
          allowBrowserUsage: Boolean(allowBrowserUsage),
          allowedWebsites: Array.isArray(allowedWebsites) ? allowedWebsites : [],
          createdBy: adminUsername,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        
        fallbackStorage.customMessages.push(messageData);
        return {
          success: true,
          message: 'Custom message saved successfully (in memory)',
          data: messageData
        };
      } else {
        await this.connect();
        
        // Check if a message with the same text already exists
        const existingMessage = await this.db.collection('customMessages').findOne({ text: text.trim() });
        if (existingMessage) {
          return { success: false, message: 'A message with this text already exists' };
        }
        
        // Prepare the message data
        const messageData = {
          text: text.trim(),
          description: description?.trim() || 'Custom message',
          allowBrowserUsage: Boolean(allowBrowserUsage),
          allowedWebsites: Array.isArray(allowedWebsites) ? allowedWebsites : [],
          createdBy: adminUsername,
          createdAt: new Date(),
          updatedAt: new Date()
        };
        
        // Insert the new custom message
        const result = await this.db.collection('customMessages').insertOne(messageData);
        
        return {
          success: true,
          message: 'Custom message saved successfully',
          data: {
            _id: result.insertedId.toString(),
            ...messageData
          }
        };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async deleteCustomMessage(messageId, adminUsername) {
    try {
      if (!messageId) {
        return { success: false, message: 'Message ID is required' };
      }

      if (this.usesFallback) {
        if (!fallbackStorage.customMessages) {
          fallbackStorage.customMessages = [];
        }
        
        const messageIndex = fallbackStorage.customMessages.findIndex(
          msg => msg.id === messageId || msg._id === messageId
        );
        
        if (messageIndex === -1) {
          return { success: false, message: 'Custom message not found' };
        }
        
        const deletedMessage = fallbackStorage.customMessages.splice(messageIndex, 1)[0];
        return {
          success: true,
          message: 'Custom message deleted successfully (from memory)',
          deletedMessage: deletedMessage
        };
      } else {
        await this.connect();
        
        // Build query for different ID formats
        const query = messageId.length === 24 ? 
          { $or: [{ _id: new ObjectId(messageId) }, { id: messageId }] } : 
          { id: messageId };
        
        const result = await this.db.collection('customMessages').deleteOne(query);
        
        if (result.deletedCount === 0) {
          return { success: false, message: 'Custom message not found' };
        }
        
        return {
          success: true,
          message: 'Custom message deleted successfully',
          deletedCount: result.deletedCount
        };
      }
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
      // Find the installation with this clientId and embedded security keys
      const installation = await this.db.collection('installations').findOne({
        clientId,
        isActive: true,
        'securityKeys': { $exists: true }
      });

      if (installation && installation.securityKeys) {
        // Look for the specific key type in the embedded security keys
        const matchingKey = Object.values(installation.securityKeys).find(key => 
          key && typeof key === 'object' && key.keyType === keyType
        );
        
        if (matchingKey && matchingKey.keyValue) {
          // Update last used timestamp for this specific key
          const keyName = Object.keys(installation.securityKeys).find(name => 
            installation.securityKeys[name] === matchingKey
          );
          
          if (keyName) {
            await this.db.collection('installations').updateOne(
              { clientId, isActive: true },
              { 
                $set: { 
                  [`securityKeys.${keyName}.lastUsed`]: new Date(),
                  'securityKeys.lastUpdated': new Date()
                }
              }
            );
          }
          
          return { success: true, key: matchingKey.keyValue };
        }
      }
      
      return { success: false, message: 'Security key not found' };
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
      const now = new Date();
      
      // Find the installation with this clientId
      const installation = await this.db.collection('installations').findOne({
        clientId,
        isActive: true
      });
      
      if (!installation) {
        return { success: false, message: 'No active installation found for this client ID' };
      }
      
      // Create security key data structure
      const keyData = {
        keyValue,
        keyType,
        createdAt: now,
        lastUsed: now,
        updatedAt: now
      };
      
      // Determine the key name based on key type
      let keyName;
      switch (keyType.toUpperCase()) {
        case 'ENCRYPTION_KEY':
          keyName = 'encryptionKey';
          break;
        case 'AUTH_KEY':
          keyName = 'authKey';
          break;
        case 'ACCESS_KEY':
          keyName = 'accessKey';
          break;
        default:
          keyName = keyType.toLowerCase() + 'Key';
          break;
      }
      
      // Update the installation record to include/update the security key
      const updatePath = `securityKeys.${keyName}`;
      const result = await this.db.collection('installations').updateOne(
        { clientId, isActive: true },
        { 
          $set: { 
            [updatePath]: keyData,
            'securityKeys.lastUpdated': now
          }
        }
      );
      
      if (result.modifiedCount > 0) {
        return {
          success: true,
          message: `Security key ${keyType} created/updated for installation ${installation.installationId}`,
          installationId: installation.installationId,
          clientId,
          keyType,
          keyName,
          createdAt: now
        };
      } else {
        return { success: false, message: 'Failed to create/update security key' };
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
      const now = new Date();
      
      // Find the installation with this clientId and embedded security keys
      const installation = await this.db.collection('installations').findOne({
        clientId,
        isActive: true,
        'securityKeys': { $exists: true }
      });
      
      if (!installation) {
        return { 
          success: false, 
          message: 'No active installation found for this client ID',
          updated: false
        };
      }
      
      // Look for the specific key type in the embedded security keys
      const matchingKey = Object.values(installation.securityKeys).find(key => 
        key && typeof key === 'object' && key.keyType === keyType
      );
      
      if (!matchingKey) {
        return { 
          success: false, 
          message: `Security key of type '${keyType}' not found for this installation`,
          updated: false
        };
      }
      
      // Find the key name
      const keyName = Object.keys(installation.securityKeys).find(name => 
        installation.securityKeys[name] === matchingKey
      );
      
      if (!keyName) {
        return { 
          success: false, 
          message: 'Unable to identify key name for update',
          updated: false
        };
      }
      
      // Update the last used timestamp for the specific key
      const result = await this.db.collection('installations').updateOne(
        { clientId, isActive: true },
        { 
          $set: { 
            [`securityKeys.${keyName}.lastUsed`]: now,
            'securityKeys.lastUpdated': now
          }
        }
      );

      return { 
        success: true, 
        message: `Key last used timestamp updated for ${keyType}`,
        updated: result.modifiedCount > 0,
        installationId: installation.installationId,
        keyType,
        keyName,
        lastUsed: now
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
      
      // Find installation in the unified installations collection
      // Use machineId as a loose search criterion in system info, and match on hostname or installPath
      const installation = await this.db.collection('installations').findOne({
        $or: [
          { hostname },
          { installPath },
          // Search for machineId in systemInfo if provided
          ...(machineId ? [{ 'systemInfo.machineId': machineId }] : [])
        ],
        isActive: true
      });

      if (installation) {
        return { 
          success: true, 
          clientId: installation.clientId,
          installationId: installation.installationId,
          hostname: installation.hostname,
          installPath: installation.installPath,
          platform: installation.platform,
          version: installation.version,
          macAddress: installation.macAddress,
          username: installation.username,
          createdAt: installation.createdAt,
          lastCheckin: installation.lastCheckin,
          isCurrentForMac: installation.isCurrentForMac
        };
      } else {
        return { success: false, message: 'Client installation not found' };
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
      
      // In the unified system, client info should already be created during installation registration
      // This method now serves as a compatibility layer and verification function
      
      // Check if installation exists in the unified installations collection
      const installation = await this.db.collection('installations').findOne({
        $or: [
          { clientId },
          { installationId },
          { installPath, hostname }
        ],
        isActive: true
      });
      
      if (installation) {
        // Installation exists, update it with any new information if needed
        const updateFields = {};
        
        if (version && version !== installation.version) {
          updateFields.version = version;
        }
        if (machineId && (!installation.systemInfo || installation.systemInfo.machineId !== machineId)) {
          updateFields['systemInfo.machineId'] = machineId;
        }
        
        // Always update the lastCheckin timestamp
        updateFields.lastCheckin = new Date();
        updateFields.updatedAt = new Date();
        
        if (Object.keys(updateFields).length > 2) { // More than just timestamps
          const result = await this.db.collection('installations').updateOne(
            { _id: installation._id },
            { $set: updateFields }
          );
          
          return { 
            success: true, 
            message: 'Client installation info updated',
            installationId: installation.installationId,
            clientId: installation.clientId,
            updated: result.modifiedCount > 0
          };
        } else {
          // Just update timestamps
          await this.db.collection('installations').updateOne(
            { _id: installation._id },
            { $set: updateFields }
          );
          
          return { 
            success: true, 
            message: 'Client checkin updated',
            installationId: installation.installationId,
            clientId: installation.clientId,
            updated: true
          };
        }
      } else {
        // Installation not found - this suggests the client wasn't properly registered
        // In the unified system, installations should be created via registerClientInstallation
        return { 
          success: false, 
          message: 'Client installation not found in unified system. Please register the installation first.',
          recommendation: 'Use registerClientInstallation method for new installations',
          clientId,
          installationId
        };
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
      const now = new Date();
      
      // Find the installation record for this client ID in the unified installations collection
      const installation = await this.db.collection('installations').findOne({
        clientId,
        isActive: true
      });
      
      if (!installation) {
        return {
          success: false,
          message: `No active installation found for client ID: ${clientId}`,
          updated: false
        };
      }
      
      // Update the installation record with the latest checkin and version
      const updateFields = {
        lastCheckin: now,
        version: version || installation.version || 'unknown'
      };
      
      const result = await this.db.collection('installations').updateOne(
        { clientId, isActive: true },
        { $set: updateFields }
      );
      
      return { 
        success: true, 
        message: 'Client checkin updated',
        updated: result.modifiedCount > 0,
        clientId,
        installationId: installation.installationId,
        lastCheckin: now,
        previousVersion: installation.version,
        newVersion: updateFields.version,
        versionChanged: version && version !== installation.version
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
      
      // Get all active installations that have embedded security keys
      const installations = await this.db.collection('installations')
        .find({ 
          isActive: true,
          securityKeys: { $exists: true }
        })
        .sort({ createdAt: -1 })
        .toArray();

      // Extract and flatten all embedded security keys
      const processedKeys = [];
      
      installations.forEach(installation => {
        if (installation.securityKeys) {
          // Process each type of security key (e.g., encryptionKey, authKey, etc.)
          Object.entries(installation.securityKeys).forEach(([keyName, keyData]) => {
            // Skip the lastUpdated timestamp field
            if (keyName === 'lastUpdated' || !keyData || typeof keyData !== 'object') {
              return;
            }
            
            // Only include if it has the key structure we expect
            if (keyData.keyValue && keyData.keyType) {
              processedKeys.push({
                _id: `${installation._id}_${keyName}`,
                installationId: installation.installationId,
                clientId: installation.clientId,
                keyType: keyData.keyType,
                keyName: keyName, // e.g., 'encryptionKey', 'authKey', etc.
                hostname: installation.hostname,
                installPath: installation.installPath,
                macAddress: installation.macAddress,
                username: installation.username,
                platform: installation.platform,
                version: installation.version,
                createdAt: keyData.createdAt,
                lastUsed: keyData.lastUsed,
                // Installation context
                installationCreatedAt: installation.createdAt,
                lastCheckin: installation.lastCheckin,
                isCurrentForMac: installation.isCurrentForMac
              });
            }
          });
        }
      });
      
      // Sort by creation date (newest first)
      processedKeys.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

      return { 
        success: true, 
        data: processedKeys,
        totalKeys: processedKeys.length,
        totalInstallations: installations.length
      };
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
      
      // Get all installations from the unified installations collection
      const installations = await this.db.collection('installations')
        .find({})
        .sort({ createdAt: -1 })
        .toArray();

      // Extract client info from installations
      const processedClients = installations.map(installation => ({
        _id: installation._id.toString(),
        clientId: installation.clientId,
        installationId: installation.installationId,
        hostname: installation.hostname,
        platform: installation.platform,
        version: installation.version,
        installPath: installation.installPath,
        createdAt: installation.createdAt,
        lastCheckin: installation.lastCheckin,
        // Additional fields from unified installations collection
        macAddress: installation.macAddress,
        username: installation.username,
        clientName: installation.clientName,
        registeredAt: installation.registeredAt,
        isActive: installation.isActive,
        isCurrentForMac: installation.isCurrentForMac,
        installationCount: installation.installationCount,
        keyId: installation.keyId,
        // User context
        userId: installation.userId ? installation.userId.toString() : null,
        userRole: installation.userRole,
        // Installation metadata
        installerMode: installation.installerMode,
        macDetectionMethod: installation.macDetectionMethod,
        // Status information
        deactivatedAt: installation.deactivatedAt,
        deactivationReason: installation.deactivationReason,
        // Policy information  
        policy: installation.policy,
        // System information
        systemInfo: installation.systemInfo
      }));

      // Enhanced response with metadata
      const totalInstallations = installations.length;
      const activeInstallations = installations.filter(i => i.isActive).length;
      const uniqueClients = new Set(installations.map(i => i.clientId)).size;
      const uniqueMacs = new Set(installations.map(i => i.macAddress)).size;
      const platforms = [...new Set(installations.map(i => i.platform).filter(Boolean))];
      const dateRange = installations.length > 0 ? {
        earliest: installations[installations.length - 1].createdAt,
        latest: installations[0].createdAt
      } : null;

      return { 
        success: true, 
        data: processedClients,
        metadata: {
          totalInstallations,
          activeInstallations,
          inactiveInstallations: totalInstallations - activeInstallations,
          uniqueClientIds: uniqueClients,
          uniqueMacAddresses: uniqueMacs,
          platforms,
          dateRange
        }
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // MAC Address-based Client Management Methods (Legacy support)
  async authenticateClientByMac(macAddress, username, installPath, platform, version) {
    try {
      if (this.usesFallback) {
        // In-memory fallback - create a temporary client
        const clientId = `${username}_${macAddress.replace(/:/g, '').substr(-6)}`;
        const clientData = {
          clientId,
          clientName: `${username}1`,
          macAddress,
          registered: new Date().toISOString(),
          lastSeen: new Date().toISOString()
        };
        fallbackStorage.clients.push(clientData);
        return { success: true, clientId, clientName: `${username}1`, isNewInstallation: true };
      }

      await this.connect();
      const now = new Date();

      // Check if MAC address already has installations
      const existingInstallations = await this.db.collection('installations')
        .find({ macAddress, isActive: true })
        .sort({ createdAt: -1 })
        .toArray();
      
      // Check for current active installation
      const currentInstallation = existingInstallations.find(install => install.isCurrentForMac === true);
      
      if (currentInstallation) {
        // Found existing active installation - return its details
        return {
          success: true,
          clientId: currentInstallation.clientId,
          clientName: currentInstallation.clientName,
          isNewInstallation: false,
          macAddress: currentInstallation.macAddress,
          installationCount: currentInstallation.installationNumber || 1,
          keyId: currentInstallation.keyId,
          message: 'Existing client installation authenticated'
        };
      }
      
      // If no current installation, check for any previous installations on this MAC
      const allInstallations = await this.db.collection('installations')
        .find({ macAddress })
        .sort({ installationNumber: -1 })
        .toArray();
      
      const installationCount = allInstallations.length + 1;
      const clientName = `${username}${installationCount}`;
      const clientId = `${username}_${macAddress.replace(/:/g, '').substr(-6)}_${installationCount}`;
      
      // Deactivate any existing installations for this MAC
      if (allInstallations.length > 0) {
        await this.db.collection('installations').updateMany(
          { macAddress, isActive: true },
          { 
            $set: { 
              isActive: false,
              isCurrentForMac: false,
              deactivatedAt: now,
              deactivationReason: 'New installation detected on same MAC address'
            }
          }
        );
      }
      
      // This method is for authentication only - actual installation record
      // should be created via registerClientInstallation method
      
      return {
        success: true,
        clientId,
        clientName,
        isNewInstallation: true,
        macAddress,
        installationCount,
        message: 'Authentication successful - ready for installation registration'
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

      // Find and update the installation record for this client ID
      const installation = await this.db.collection('installations').findOne({
        clientId,
        isActive: true
      });

      if (!installation) {
        return {
          success: false,
          message: `No active installation found for client ID: ${clientId}`,
          updated: false
        };
      }

      // Update the installation record with the latest checkin and version
      const result = await this.db.collection('installations').updateOne(
        { clientId, isActive: true },
        { 
          $set: { 
            lastCheckin: now,
            version: version || installation.version || 'unknown'
          }
        }
      );

      const additionalInfo = {
        installationId: installation.installationId,
        macAddress: installation.macAddress,
        hostname: installation.hostname,
        isCurrentForMac: installation.isCurrentForMac,
        previousVersion: installation.version,
        newVersion: version || installation.version || 'unknown',
        versionChanged: version && version !== installation.version
      };

      return { 
        success: true, 
        message: `Client checkin updated for ${clientId}`,
        updated: result.modifiedCount > 0,
        clientId,
        lastCheckin: now,
        ...additionalInfo
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
      
      // Get all installations for this MAC address from the unified installations collection
      const installations = await this.db.collection('installations')
        .find({ macAddress })
        .sort({ createdAt: -1 }) // Sort by creation date (newest first)
        .toArray();
      
      if (installations.length === 0) {
        return { success: false, message: 'No installations found for this MAC address' };
      }

      // Find the current active installation for this MAC address
      const currentActiveInstallation = installations.find(install => 
        install.isActive && install.isCurrentForMac
      );

      // Get the most recent installation regardless of active status
      const latestInstallation = installations[0]; // Already sorted by newest first

      // Create a MAC client summary compatible with the old API structure
      const macClient = {
        _id: latestInstallation._id.toString(),
        macAddress,
        username: latestInstallation.username,
        clientName: latestInstallation.clientName,
        activeClientId: currentActiveInstallation ? currentActiveInstallation.clientId : null,
        installationCount: latestInstallation.installationCount || 1,
        hostname: latestInstallation.hostname,
        platform: latestInstallation.platform,
        createdAt: latestInstallation.createdAt,
        registeredAt: latestInstallation.registeredAt,
        lastCheckin: currentActiveInstallation ? currentActiveInstallation.lastCheckin : latestInstallation.lastCheckin,
        // Enhanced information from unified installations
        totalInstallations: installations.length,
        activeInstallations: installations.filter(i => i.isActive).length,
        userId: latestInstallation.userId ? latestInstallation.userId.toString() : null,
        userRole: latestInstallation.userRole
      };

      // Create an active client summary if there's a current active installation
      const activeClient = currentActiveInstallation ? {
        _id: currentActiveInstallation._id.toString(),
        clientId: currentActiveInstallation.clientId,
        installationId: currentActiveInstallation.installationId,
        keyId: currentActiveInstallation.keyId,
        installPath: currentActiveInstallation.installPath,
        hostname: currentActiveInstallation.hostname,
        platform: currentActiveInstallation.platform,
        version: currentActiveInstallation.version,
        username: currentActiveInstallation.username,
        clientName: currentActiveInstallation.clientName,
        isActive: currentActiveInstallation.isActive,
        isCurrentForMac: currentActiveInstallation.isCurrentForMac,
        createdAt: currentActiveInstallation.createdAt,
        lastCheckin: currentActiveInstallation.lastCheckin,
        registeredAt: currentActiveInstallation.registeredAt,
        installationCount: currentActiveInstallation.installationCount,
        // Security information
        securityKeys: currentActiveInstallation.securityKeys,
        // Policy information
        policy: currentActiveInstallation.policy,
        // User context
        userId: currentActiveInstallation.userId ? currentActiveInstallation.userId.toString() : null,
        userRole: currentActiveInstallation.userRole
      } : null;

      // Include detailed installation history
      const installationHistory = installations.map(installation => ({
        _id: installation._id.toString(),
        clientId: installation.clientId,
        installationId: installation.installationId,
        keyId: installation.keyId,
        hostname: installation.hostname,
        version: installation.version,
        installPath: installation.installPath,
        isActive: installation.isActive,
        isCurrentForMac: installation.isCurrentForMac,
        createdAt: installation.createdAt,
        lastCheckin: installation.lastCheckin,
        deactivatedAt: installation.deactivatedAt,
        deactivationReason: installation.deactivationReason,
        installationCount: installation.installationCount,
        userRole: installation.userRole
      }));

      return {
        success: true,
        macAddress,
        macClient,
        activeClient,
        installationHistory,
        metadata: {
          totalInstallations: installations.length,
          activeInstallations: installations.filter(i => i.isActive).length,
          inactiveInstallations: installations.filter(i => !i.isActive).length,
          hasCurrentInstallation: !!currentActiveInstallation,
          latestInstallationDate: latestInstallation.createdAt,
          oldestInstallationDate: installations[installations.length - 1].createdAt
        }
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getAllMacClients(requestingUserId = null, requestingUserRole = null) {
    try {
      if (this.usesFallback) {
        return { success: true, data: fallbackStorage.clients };
      }

      await this.connect();
      
      // Build query based on user role and hierarchy
      let installationQuery = {};
      
      if (requestingUserRole === 'admin') {
        // Regular admins can only see clients associated with users they created
        const createdUsers = await this.db.collection('users')
          .find({ createdBy: requestingUserId }, { projection: { _id: 1 } })
          .toArray();
        
        const userIds = createdUsers.map(user => user._id);
        userIds.push(new ObjectId(requestingUserId)); // Include the admin's own clients if any
        
        installationQuery = { userId: { $in: userIds } };
      } else if (requestingUserRole === 'master_admin') {
        // Master admins can see all clients
        installationQuery = {};
      } else if (requestingUserRole === 'user') {
        // Regular users can only see their own clients
        installationQuery = { userId: new ObjectId(requestingUserId) };
      } else {
        // No role or invalid role - return empty result
        return { success: true, data: [] };
      }
      
      // Get all installations from the unified collection, grouped by MAC address
      const installations = await this.db.collection('installations')
        .find(installationQuery)
        .sort({ macAddress_hash: 1, createdAt: -1 }) // Sort by MAC address hash, then by creation date (newest first)
        .toArray();

      // Group installations by MAC address hash (since MAC is encrypted)
      const macClientMap = new Map();
      
      for (const installation of installations) {
        // Decrypt sensitive data
        const decryptedMacAddress = CryptoUtils.decrypt(installation.macAddress);
        const decryptedHostname = CryptoUtils.decrypt(installation.hostname);
        const decryptedInstallPath = CryptoUtils.decrypt(installation.installPath);
        const decryptedSystemInfo = installation.systemInfo ? 
          JSON.parse(CryptoUtils.decrypt(installation.systemInfo) || '{}') : null;
        
        const macAddressKey = installation.macAddress_hash; // Use hash as key for grouping
        
        if (!macClientMap.has(macAddressKey)) {
          // Initialize MAC client entry with the first (most recent) installation
          macClientMap.set(macAddressKey, {
            _id: installation._id.toString(),
            macAddress: decryptedMacAddress,
            username: installation.username,
            clientName: installation.clientName,
            activeClientId: installation.isActive ? installation.clientId : null,
            installationCount: installation.installationCount || 1,
            hostname: decryptedHostname,
            platform: installation.platform,
            createdAt: installation.createdAt,
            registeredAt: installation.registeredAt,
            lastCheckin: installation.lastCheckin,
            // Current active installation (if this one is active)
            activeInstallation: installation.isActive && installation.isCurrentForMac ? {
              clientId: installation.clientId,
              installationId: installation.installationId,
              keyId: installation.keyId,
              installPath: decryptedInstallPath,
              version: installation.version,
              createdAt: installation.createdAt,
              lastCheckin: installation.lastCheckin,
              isActive: installation.isActive,
              isCurrentForMac: installation.isCurrentForMac
            } : null,
            // Latest installation (this one, since sorted by newest first)
            latestInstallation: {
              clientId: installation.clientId,
              installationId: installation.installationId,
              keyId: installation.keyId,
              installPath: decryptedInstallPath,
              version: installation.version,
              createdAt: installation.createdAt,
              lastCheckin: installation.lastCheckin,
              isActive: installation.isActive,
              isCurrentForMac: installation.isCurrentForMac,
              deactivatedAt: installation.deactivatedAt,
              deactivationReason: installation.deactivationReason
            },
            // Count of all installations for this MAC (use hash for comparison)
            totalInstallations: installations.filter(i => i.macAddress_hash === installation.macAddress_hash).length,
            // Count of active installations for this MAC
            activeInstallations: installations.filter(i => i.macAddress_hash === installation.macAddress_hash && i.isActive).length
          });
        } else {
          // Update existing MAC client entry with active installation info if needed
          const macClient = macClientMap.get(macAddressKey);
          
          // Update active installation if this installation is current and active
          if (installation.isActive && installation.isCurrentForMac && !macClient.activeInstallation) {
            macClient.activeClientId = installation.clientId;
            macClient.activeInstallation = {
              clientId: installation.clientId,
              installationId: installation.installationId,
              keyId: installation.keyId,
              installPath: decryptedInstallPath,
              version: installation.version,
              createdAt: installation.createdAt,
              lastCheckin: installation.lastCheckin,
              isActive: installation.isActive,
              isCurrentForMac: installation.isCurrentForMac
            };
            
            // Update last checkin if this is more recent
            if (installation.lastCheckin > macClient.lastCheckin) {
              macClient.lastCheckin = installation.lastCheckin;
            }
          }
        }
      }

      // Convert map to array and maintain compatibility with old API format
      const processedClients = Array.from(macClientMap.values()).map(macClient => ({
        _id: macClient._id,
        macAddress: macClient.macAddress,
        username: macClient.username,
        clientName: macClient.clientName,
        activeClientId: macClient.activeClientId,
        installationCount: macClient.installationCount,
        hostname: macClient.hostname,
        platform: macClient.platform,
        createdAt: macClient.createdAt,
        registeredAt: macClient.registeredAt,
        lastCheckin: macClient.lastCheckin,
        // Maintain compatibility with old API structure
        activeClient: macClient.activeInstallation ? {
          installPath: macClient.activeInstallation.installPath,
          version: macClient.activeInstallation.version,
          createdAt: macClient.activeInstallation.createdAt,
          lastCheckin: macClient.activeInstallation.lastCheckin,
          isActive: macClient.activeInstallation.isActive
        } : null,
        latestClient: macClient.latestInstallation ? {
          installPath: macClient.latestInstallation.installPath,
          version: macClient.latestInstallation.version,
          createdAt: macClient.latestInstallation.createdAt,
          lastCheckin: macClient.latestInstallation.lastCheckin,
          isActive: macClient.latestInstallation.isActive,
          deactivatedAt: macClient.latestInstallation.deactivatedAt,
          deactivationReason: macClient.latestInstallation.deactivationReason
        } : null,
        // Enhanced information from unified installations
        installationDetails: {
          totalInstallations: macClient.totalInstallations,
          activeInstallations: macClient.activeInstallations,
          currentInstallation: macClient.activeInstallation,
          latestInstallation: macClient.latestInstallation
        }
      }));

      // Sort by last checkin (most recent first)
      processedClients.sort((a, b) => new Date(b.lastCheckin) - new Date(a.lastCheckin));

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
      
      // Query the installations collection for historical data
      const query = macAddress ? { macAddress } : {};
      const installations = await this.db.collection('installations')
        .find(query)
        .sort({ createdAt: -1 }) // Sort by creation date (newest first)
        .toArray();

      // Map installations to the expected client history format
      const processedHistory = installations.map(installation => ({
        _id: installation._id.toString(),
        macAddress: installation.macAddress,
        clientId: installation.clientId,
        clientName: installation.clientName,
        username: installation.username,
        hostname: installation.hostname,
        installPath: installation.installPath,
        platform: installation.platform,
        version: installation.version,
        isActive: installation.isActive,
        createdAt: installation.createdAt,
        lastCheckin: installation.lastCheckin,
        deactivatedAt: installation.deactivatedAt,
        deactivationReason: installation.deactivationReason,
        // Enhanced fields from unified installations collection
        installationId: installation.installationId,
        keyId: installation.keyId,
        installationCount: installation.installationCount,
        isCurrentForMac: installation.isCurrentForMac,
        registeredAt: installation.registeredAt,
        userId: installation.userId ? installation.userId.toString() : null,
        userRole: installation.userRole,
        // Installation metadata
        installerMode: installation.installerMode,
        macDetectionMethod: installation.macDetectionMethod,
        // Policy information
        policy: installation.policy,
        // Installation history tracking
        installationHistory: installation.installationHistory
      }));

      // Enhanced response with additional metadata
      const totalInstallations = installations.length;
      const activeInstallations = installations.filter(i => i.isActive).length;
      const uniqueMacs = new Set(installations.map(i => i.macAddress)).size;
      const dateRange = installations.length > 0 ? {
        earliest: installations[installations.length - 1].createdAt,
        latest: installations[0].createdAt
      } : null;

      return { 
        success: true, 
        data: processedHistory,
        metadata: {
          totalInstallations,
          activeInstallations,
          inactiveInstallations: totalInstallations - activeInstallations,
          uniqueMacAddresses: uniqueMacs,
          dateRange,
          filteredByMac: macAddress ? true : false,
          macAddress: macAddress || null
        }
      };
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

      // Find the installation record for this client ID
      const installation = await this.db.collection('installations').findOne({
        clientId,
        isActive: true
      });

      if (!installation) {
        return {
          success: false,
          message: `No active installation found for client ID: ${clientId}`,
          deactivated: false
        };
      }

      // Deactivate the installation
      const result = await this.db.collection('installations').updateOne(
        { clientId, isActive: true },
        {
          $set: {
            isActive: false,
            isCurrentForMac: false, // Also unmark as current for MAC
            deactivatedAt: now,
            deactivationReason: reason
          }
        }
      );

      let additionalInfo = {};
      if (result.modifiedCount > 0) {
        // Check if there are other active installations for the same MAC address
        const otherActiveInstallations = await this.db.collection('installations')
          .find({
            macAddress: installation.macAddress,
            isActive: true,
            clientId: { $ne: clientId } // Exclude the one we just deactivated
          })
          .sort({ createdAt: -1 }) // Get the most recent one
          .toArray();

        // If there are other active installations, mark the most recent one as current
        if (otherActiveInstallations.length > 0) {
          const mostRecentInstallation = otherActiveInstallations[0];
          await this.db.collection('installations').updateOne(
            { _id: mostRecentInstallation._id },
            { $set: { isCurrentForMac: true } }
          );
          
          additionalInfo.newCurrentInstallation = {
            clientId: mostRecentInstallation.clientId,
            installationId: mostRecentInstallation.installationId,
            createdAt: mostRecentInstallation.createdAt
          };
        }

        additionalInfo.deactivatedInstallation = {
          installationId: installation.installationId,
          macAddress: installation.macAddress,
          hostname: installation.hostname,
          version: installation.version,
          createdAt: installation.createdAt,
          deactivatedAt: now,
          deactivationReason: reason
        };
      }

      return {
        success: true,
        message: `Client ${clientId} deactivated successfully`,
        deactivated: result.modifiedCount > 0,
        clientId,
        ...additionalInfo
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async deactivateMacClient(macAddress, reason = 'Manual deactivation') {
    try {
      if (this.usesFallback) {
        const clientIndex = fallbackStorage.clients.findIndex(c => c.macAddress === macAddress);
        if (clientIndex >= 0) {
          fallbackStorage.clients.splice(clientIndex, 1);
        }
        return { success: true, message: 'MAC client deactivated in memory' };
      }

      await this.connect();
      const now = new Date();

      // Find all installations for this MAC address
      const installations = await this.db.collection('installations')
        .find({ macAddress, isActive: true })
        .toArray();

      if (installations.length === 0) {
        return {
          success: false,
          message: `No active installations found for MAC address: ${macAddress}`,
          macAddress,
          deactivated: false
        };
      }

      // Deactivate all installations for this MAC address
      const result = await this.db.collection('installations').updateMany(
        { macAddress, isActive: true },
        {
          $set: {
            isActive: false,
            isCurrentForMac: false,
            deactivatedAt: now,
            deactivationReason: reason
          }
        }
      );

      // Collect information about deactivated installations
      const deactivatedInstallations = installations.map(installation => ({
        clientId: installation.clientId,
        installationId: installation.installationId,
        hostname: installation.hostname,
        username: installation.username,
        version: installation.version,
        createdAt: installation.createdAt,
        deactivatedAt: now,
        deactivationReason: reason
      }));

      return {
        success: true,
        message: `All installations for MAC address ${macAddress} deactivated successfully`,
        macAddress,
        deactivated: result.modifiedCount > 0,
        deactivatedInstallations,
        totalDeactivated: result.modifiedCount,
        installationDetails: {
          totalInstallationsFound: installations.length,
          totalDeactivated: result.modifiedCount,
          clientIds: installations.map(i => i.clientId),
          hostnames: [...new Set(installations.map(i => i.hostname))],
          usernames: [...new Set(installations.map(i => i.username))]
        }
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // Update security key management to work with embedded keys in installations
  async createSecurityKeyForMac(macAddress, keyType, keyValue, installPath, hostname) {
    try {
      if (this.usesFallback) {
        return { success: true, message: 'Security key created in memory' };
      }

      await this.connect();
      
      // Find the active installation for this MAC address
      const installation = await this.db.collection('installations').findOne({
        macAddress,
        isActive: true,
        isCurrentForMac: true
      });
      
      if (!installation) {
        return { success: false, message: 'No active installation found for this MAC address' };
      }

      const now = new Date();
      const keyData = {
        keyValue,
        keyType,
        createdAt: now,
        lastUsed: now,
        updatedAt: now
      };

      // Update the installation record to include/update the security key
      const updatePath = `securityKeys.${keyType.toLowerCase()}Key`;
      const result = await this.db.collection('installations').updateOne(
        { _id: installation._id },
        { 
          $set: { 
            [updatePath]: keyData,
            'securityKeys.lastUpdated': now
          }
        }
      );

      if (result.modifiedCount > 0) {
        return {
          success: true,
          message: `Security key ${keyType} created/updated for installation ${installation.installationId}`,
          installationId: installation.installationId,
          clientId: installation.clientId,
          keyType,
          createdAt: now
        };
      } else {
        return { success: false, message: 'Failed to update security key' };
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
      
      // Find the active installation for this MAC address
      const installation = await this.db.collection('installations').findOne({
        macAddress,
        isActive: true,
        isCurrentForMac: true
      });
      
      if (!installation) {
        return { success: false, message: 'No active installation found for this MAC address' };
      }

      // Get the security key from the embedded keys structure
      const keyPath = `securityKeys.${keyType.toLowerCase()}Key`;
      const securityKey = installation.securityKeys && installation.securityKeys[`${keyType.toLowerCase()}Key`];
      
      if (!securityKey || !securityKey.keyValue) {
        return { success: false, message: `Security key ${keyType} not found for this installation` };
      }

      // Update last used timestamp for the security key
      const now = new Date();
      await this.db.collection('installations').updateOne(
        { _id: installation._id },
        { 
          $set: { 
            [`${keyPath}.lastUsed`]: now,
            'securityKeys.lastUpdated': now
          }
        }
      );
      
      return { 
        success: true, 
        key: securityKey.keyValue,
        installationId: installation.installationId,
        clientId: installation.clientId,
        keyType,
        lastUsed: now,
        createdAt: securityKey.createdAt
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  // User Management Methods
  async createUser(username, email, password, role = 'user', createdBy = null, firstName = '', lastName = '', phoneNumber = '', address = '') {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      // Validate role
      const validRoles = ['user', 'admin', 'master_admin'];
      if (!validRoles.includes(role)) {
        return { success: false, message: 'Invalid role specified' };
      }
      
      // Check if user already exists
      const emailHash = CryptoUtils.hashSensitiveData(email);
      const existingUser = await this.db.collection('users').findOne({
        $or: [{ username }, { email_hash: emailHash }]
      });
      
      if (existingUser) {
        return { success: false, message: 'Username or email already exists' };
      }

      // Hash password (in production, use bcrypt)
      const hashedPassword = Buffer.from(password).toString('base64');
      
      // Prepare user data with sensitive information
      const userData = {
        username,
        email: CryptoUtils.encrypt(email), // Encrypt email
        email_hash: CryptoUtils.hashSensitiveData(email), // For indexing
        password: hashedPassword,
        role,
        firstName: firstName ? CryptoUtils.encrypt(firstName) : '',
        lastName: lastName ? CryptoUtils.encrypt(lastName) : '',
        phoneNumber: phoneNumber ? CryptoUtils.encrypt(phoneNumber) : '',
        address: address ? CryptoUtils.encrypt(address) : '',
        createdBy: createdBy, // ID of the user who created this account
        createdAt: new Date(),
        lastLogin: null,
        isActive: true,
        _encrypted_fields: ['email', 'firstName', 'lastName', 'phoneNumber', 'address'],
        // Password management fields
        passwordGenerated: false,
        passwordNeedsReset: false,
        passwordGeneratedBy: null,
        passwordGeneratedAt: null,
        subscription: {
          plan: role === 'admin' || role === 'master_admin' ? 'trial' : 'none',
          status: 'trial',
          userLimit: role === 'admin' || role === 'master_admin' ? 1 : 0,
          stripeCustomerId: null,
          stripeSubscriptionId: null,
          nextBillingDate: null,
          trialEndsAt: role === 'admin' || role === 'master_admin' ? 
            new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) : null // 30-day trial
        }
      };

      const result = await this.db.collection('users').insertOne(userData);
      
      return {
        success: true,
        message: 'User created successfully',
        userId: result.insertedId.toString(),
        user: {
          id: result.insertedId.toString(),
          username,
          email: email, // Return original unencrypted for response
          role,
          firstName: firstName || '',
          lastName: lastName || '',
          phoneNumber: phoneNumber || '',
          address: address || '',
          subscription: userData.subscription
        }
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
      
      // Try to find user by username or email hash
      const emailHash = CryptoUtils.hashSensitiveData(username);
      const user = await this.db.collection('users').findOne({
        $or: [{ username }, { email_hash: emailHash }],
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
          email: CryptoUtils.decrypt(user.email) || '',
          role: user.role
        },
        sessionToken,
        role: user.role,
        passwordNeedsReset: user.passwordNeedsReset || false,
        passwordGenerated: user.passwordGenerated || false
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

  async generateUpdateInstallationKey(clientId, macAddress) {
    try {
      if (this.usesFallback) {
        // In fallback mode, generate a simple update key
        return {
          success: true,
          installationKey: this.generateInstallationKey(),
          message: 'Update key generated (fallback mode)'
        };
      }

      await this.connect();
      
      // Try to find an existing client to get user context from the unified installations collection
      let user = null;
      let installation = null;
      
      // First try to find by clientId directly
      if (clientId) {
        installation = await this.db.collection('installations').findOne({
          clientId,
          isActive: true
        });
      }
      
      // If not found by clientId and we have a MAC address, try to find by MAC address
      if (!installation && macAddress) {
        installation = await this.db.collection('installations').findOne({
          macAddress,
          isActive: true,
          isCurrentForMac: true
        });
      }
      
      // If we have an installation, try to get user info
      if (installation && installation.userId) {
        user = await this.db.collection('users').findOne({
          _id: installation.userId,
          isActive: true
        });
      }
      
      // If we can't find user context, create a generic update key
      if (!user || !installation) {
        console.log(`Creating generic update key for client ${clientId} (MAC: ${macAddress})`);
        
        // Generate update-specific installation key
        const updateKey = this.generateInstallationKey();
        
        // Store as a special update key with shorter expiration (2 hours)
        await this.db.collection('updateKeys').insertOne({
          clientId,
          macAddress,
          installationKey: updateKey,
          type: 'update',
          createdAt: new Date(),
          expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours
          used: false,
          // Include installation context if available
          ...(installation ? {
            installationId: installation.installationId,
            hostname: installation.hostname,
            username: installation.username,
            platform: installation.platform
          } : {})
        });
        
        return {
          success: true,
          installationKey: updateKey,
          message: 'Update installation key generated successfully',
          context: installation ? 'with_installation_context' : 'generic'
        };
      }
      
      // Generate update key with user context
      const updateKey = this.generateInstallationKey();
      
      // Store the update key with user context and shorter expiration
      await this.db.collection('downloadKeys').insertOne({
        userId: user._id,
        username: user.username,
        role: user.role,
        installationKey: updateKey,
        clientId: installation.clientId,
        macAddress: installation.macAddress,
        type: 'update',
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours for updates
        used: false,
        // Include additional installation context
        installationId: installation.installationId,
        hostname: installation.hostname,
        platform: installation.platform,
        version: installation.version
      });

      return {
        success: true,
        installationKey: updateKey,
        message: 'Update installation key generated successfully',
        context: 'with_user_context',
        user: {
          id: user._id.toString(),
          username: user.username,
          role: user.role
        },
        installation: {
          installationId: installation.installationId,
          clientId: installation.clientId,
          hostname: installation.hostname,
          platform: installation.platform,
          version: installation.version
        }
      };
    } catch (error) {
      console.error('Error generating update installation key:', error);
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

  async validateInstallationKey(installationKey, markAsUsed = false) {
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
        // Only mark the key as used if explicitly requested (during actual registration)
        if (markAsUsed) {
          await this.db.collection('downloadKeys').updateOne(
            { _id: downloadKey._id },
            { $set: { used: true, usedAt: new Date() } }
          );
        }
        
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

  async registerClientWithInstallationKey(clientId, installationKey, validatedUser, validatedAt, installPath, hostname, platform, version, registeredAt) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Client registration requires MongoDB connection' };
      }

      await this.connect();
      
      // Validate that the installation key was previously validated
      const downloadKey = await this.db.collection('downloadKeys').findOne({
        installationKey,
        used: true
      });
      
      if (!downloadKey) {
        return { success: false, message: 'Installation key not found or not validated' };
      }
      
      // Create or update client installation record
      const installationRecord = {
        clientId,
        installationKey,
        userId: downloadKey.userId,
        username: downloadKey.username,
        userRole: downloadKey.role,
        validatedUser,
        validatedAt,
        installPath,
        hostname,
        platform,
        version,
        registeredAt,
        createdAt: new Date()
      };
      
      // Store in clientInstallations collection
      await this.db.collection('clientInstallations').insertOne(installationRecord);
      
      return {
        success: true,
        message: 'Client registered with installation key successfully',
        clientId,
        userId: downloadKey.userId.toString(),
        username: downloadKey.username
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async getAllUsers(requestingUserId = null, requestingUserRole = null) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'User management requires MongoDB connection' };
      }

      await this.connect();
      
      let userQuery = {};
      
      // Apply role-based filtering
      if (requestingUserRole === 'admin') {
        // Regular admins can only see users they created
        userQuery = { createdBy: requestingUserId };
      } else if (requestingUserRole === 'master_admin') {
        // Master admins can see all users
        userQuery = {};
      } else {
        // Regular users cannot access this function
        return { success: false, message: 'Insufficient permissions' };
      }
      
      const users = await this.db.collection('users')
        .find(userQuery, { projection: { password: 0 } })
        .sort({ createdAt: -1 })
        .toArray();

      const processedUsers = users.map(user => ({
        id: user._id.toString(),
        username: user.username,
        email: user.email,
        role: user.role,
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        phoneNumber: user.phoneNumber || '',
        address: user.address || '',
        createdBy: user.createdBy,
        installationKey: user.installationKey,
        createdAt: user.createdAt,
        lastLogin: user.lastLogin,
        isActive: user.isActive,
        subscription: user.subscription || {}
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

  async cleanupExpiredUninstallCommands() {
    try {
      const now = new Date();
      let cleanedCount = 0;
      
      if (this.usesFallback) {
        const originalLength = fallbackStorage.notifications.length;
        fallbackStorage.notifications = fallbackStorage.notifications.filter(n => {
          // Remove uninstall command notifications that have auto-expire set and are past their expiration
          if (n.type === 'uninstall_command' && n.autoExpire && n.expireAfter) {
            const expireDate = new Date(n.expireAfter);
            if (now > expireDate) {
              return false; // Remove this notification
            }
          }
          return true; // Keep this notification
        });
        cleanedCount = originalLength - fallbackStorage.notifications.length;
      } else {
        await this.connect();
        const result = await this.db.collection('notifications').deleteMany({
          type: 'uninstall_command',
          autoExpire: true,
          expireAfter: { $lt: now }
        });
        cleanedCount = result.deletedCount;
      }

      if (cleanedCount > 0) {
        console.log(`Cleaned up ${cleanedCount} expired uninstall command notifications`);
      }
      
      return {
        success: true,
        message: `Cleaned ${cleanedCount} expired uninstall command notifications`,
        cleanedCount
      };
    } catch (error) {
      console.error('Error cleaning expired uninstall commands:', error);
      return { success: false, message: error.message };
    }
  }

  // Password Management Methods
  async generateUserPassword(adminUserId, targetUserId, length = 16) {
    try {
      const PasswordUtils = require('../../../utils/password-utils');
      
      if (this.usesFallback) {
        return { success: false, message: 'Password management requires MongoDB connection' };
      }

      await this.connect();
      
      // Verify admin permissions
      const admin = await this.db.collection('users').findOne({ _id: new ObjectId(adminUserId) });
      if (!admin || (admin.role !== 'admin' && admin.role !== 'master_admin')) {
        return { success: false, message: 'Admin privileges required' };
      }
      
      // Find target user
      const targetUser = await this.db.collection('users').findOne({ _id: new ObjectId(targetUserId) });
      if (!targetUser) {
        return { success: false, message: 'Target user not found' };
      }
      
      // Check if admin can manage this user
      if (admin.role === 'admin' && targetUser.createdBy !== adminUserId) {
        return { success: false, message: 'You can only manage users you created' };
      }
      
      // Generate secure password
      const newPassword = PasswordUtils.generateSecurePassword(length);
      const validation = PasswordUtils.validatePassword(newPassword);
      
      if (!validation.isValid) {
        return { success: false, message: 'Failed to generate valid password: ' + validation.errors.join(', ') };
      }
      
      // Hash the new password
      const hashedPassword = Buffer.from(newPassword).toString('base64');
      
      // Update user with new password and tracking fields
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(targetUserId) },
        { 
          $set: { 
            password: hashedPassword,
            passwordGenerated: true,
            passwordNeedsReset: true,
            passwordGeneratedBy: adminUserId,
            passwordGeneratedAt: new Date(),
            updatedAt: new Date()
          }
        }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'Failed to update password' };
      }
      
      return {
        success: true,
        message: 'Password generated successfully',
        password: newPassword,
        strength: PasswordUtils.checkPasswordStrength(newPassword)
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async setUserPassword(adminUserId, targetUserId, newPassword) {
    try {
      const PasswordUtils = require('../../../utils/password-utils');
      
      if (this.usesFallback) {
        return { success: false, message: 'Password management requires MongoDB connection' };
      }

      await this.connect();
      
      // Validate password first
      const validation = PasswordUtils.validatePassword(newPassword);
      if (!validation.isValid) {
        return { success: false, message: 'Password requirements not met: ' + validation.errors.join(', ') };
      }
      
      // Verify admin permissions
      const admin = await this.db.collection('users').findOne({ _id: new ObjectId(adminUserId) });
      if (!admin || (admin.role !== 'admin' && admin.role !== 'master_admin')) {
        return { success: false, message: 'Admin privileges required' };
      }
      
      // Find target user
      const targetUser = await this.db.collection('users').findOne({ _id: new ObjectId(targetUserId) });
      if (!targetUser) {
        return { success: false, message: 'Target user not found' };
      }
      
      // Check if admin can manage this user
      if (admin.role === 'admin' && targetUser.createdBy !== adminUserId) {
        return { success: false, message: 'You can only manage users you created' };
      }
      
      // Hash the new password
      const hashedPassword = Buffer.from(newPassword).toString('base64');
      
      // Update user with new password and tracking fields
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(targetUserId) },
        { 
          $set: { 
            password: hashedPassword,
            passwordGenerated: true,
            passwordNeedsReset: false, // Admin-set passwords don't require reset
            passwordGeneratedBy: adminUserId,
            passwordGeneratedAt: new Date(),
            updatedAt: new Date()
          }
        }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'Failed to update password' };
      }
      
      return {
        success: true,
        message: 'Password set successfully',
        strength: PasswordUtils.checkPasswordStrength(newPassword)
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async resetOwnPassword(userId, currentPassword, newPassword) {
    try {
      const PasswordUtils = require('../../../utils/password-utils');
      
      if (this.usesFallback) {
        return { success: false, message: 'Password management requires MongoDB connection' };
      }

      await this.connect();
      
      // Validate new password first
      const validation = PasswordUtils.validatePassword(newPassword);
      if (!validation.isValid) {
        return { success: false, message: 'Password requirements not met: ' + validation.errors.join(', ') };
      }
      
      // Find user
      const user = await this.db.collection('users').findOne({ _id: new ObjectId(userId) });
      if (!user) {
        return { success: false, message: 'User not found' };
      }
      
      // Verify current password (unless it's a generated password that needs reset)
      if (!user.passwordNeedsReset) {
        const hashedCurrentPassword = Buffer.from(currentPassword).toString('base64');
        if (hashedCurrentPassword !== user.password) {
          return { success: false, message: 'Current password is incorrect' };
        }
      }
      
      // Hash the new password
      const hashedPassword = Buffer.from(newPassword).toString('base64');
      
      // Update user with new password
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(userId) },
        { 
          $set: { 
            password: hashedPassword,
            passwordGenerated: false,
            passwordNeedsReset: false,
            passwordGeneratedBy: null,
            passwordGeneratedAt: null,
            updatedAt: new Date()
          }
        }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'Failed to update password' };
      }
      
      return {
        success: true,
        message: 'Password updated successfully',
        strength: PasswordUtils.checkPasswordStrength(newPassword)
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async generatePasswordOptions(count = 3, length = 16) {
    try {
      const PasswordUtils = require('../../../utils/password-utils');
      const passwords = PasswordUtils.generatePasswordOptions(count, length);
      
      return {
        success: true,
        passwords: passwords.map(pwd => ({
          password: pwd,
          strength: PasswordUtils.checkPasswordStrength(pwd)
        }))
      };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  async updateAccountInfo(userId, updateData) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Account management requires MongoDB connection' };
      }

      await this.connect();
      
      // Build update object with only allowed fields
      const allowedFields = ['firstName', 'lastName', 'email', 'phoneNumber', 'address'];
      const updateFields = {};
      
      for (const field of allowedFields) {
        if (updateData.hasOwnProperty(field)) {
          updateFields[field] = updateData[field];
        }
      }
      
      // Handle subscription updates separately
      if (updateData.subscription) {
        if (updateData.subscription.userLimit && typeof updateData.subscription.userLimit === 'number') {
          updateFields['subscription.userLimit'] = updateData.subscription.userLimit;
        }
      }
      
      if (Object.keys(updateFields).length === 0) {
        return { success: false, message: 'No valid fields to update' };
      }
      
      updateFields.updatedAt = new Date();
      
      const result = await this.db.collection('users').updateOne(
        { _id: new ObjectId(userId) },
        { $set: updateFields }
      );
      
      if (result.modifiedCount === 0) {
        return { success: false, message: 'User not found or no changes made' };
      }
      
      // Return updated user info (excluding password)
      const updatedUser = await this.db.collection('users').findOne(
        { _id: new ObjectId(userId) },
        { projection: { password: 0 } }
      );
      
      return {
        success: true,
        message: 'Account information updated successfully',
        user: {
          id: updatedUser._id.toString(),
          username: updatedUser.username,
          email: updatedUser.email,
          firstName: updatedUser.firstName,
          lastName: updatedUser.lastName,
          phoneNumber: updatedUser.phoneNumber,
          address: updatedUser.address,
          role: updatedUser.role,
          subscription: updatedUser.subscription
        }
      };
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

      // Get user's installations before deleting for reporting purposes
      const userInstallations = await this.db.collection('installations')
        .find({ userId: new ObjectId(userId) })
        .toArray();
      
      console.log(`Deleting user ${user.username} (${userId}) and ${userInstallations.length} associated installations`);

      // Delete user and all associated data
      // Using Promise.all for concurrent operations
      const deleteResults = await Promise.all([
        // Delete user sessions
        this.db.collection('sessions').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete download keys associated with the user
        this.db.collection('downloadKeys').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete update keys associated with the user (if any exist)
        this.db.collection('updateKeys').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete user's notifications
        this.db.collection('notifications').deleteMany({ userId: new ObjectId(userId) }),
        
        // Delete or deactivate user's installations from unified installations collection
        this.db.collection('installations').updateMany(
          { userId: new ObjectId(userId) },
          { 
            $set: {
              isActive: false,
              isCurrentForMac: false,
              deactivatedAt: new Date(),
              deactivationReason: `User account deleted: ${user.username}`,
              userDeleted: true,
              userDeletedAt: new Date()
            },
            $unset: {
              userId: "",
              userRole: ""
            }
          }
        ),
        
        // Delete installation reports associated with user installations
        this.db.collection('installationReports').deleteMany({
          clientId: { $in: userInstallations.map(i => i.clientId) }
        })
      ]);
      
      // Get deletion counts for reporting
      const [sessionsResult, downloadKeysResult, updateKeysResult, notificationsResult, installationsResult, reportsResult] = deleteResults;
      
      // Finally, delete the user record itself
      const userResult = await this.db.collection('users').deleteOne({ _id: new ObjectId(userId) });
      
      if (userResult.deletedCount === 0) {
        return { success: false, message: 'Failed to delete user' };
      }

      console.log(`User deletion completed:`);
      console.log(`  - Sessions deleted: ${sessionsResult.deletedCount}`);
      console.log(`  - Download keys deleted: ${downloadKeysResult.deletedCount}`);
      console.log(`  - Update keys deleted: ${updateKeysResult.deletedCount}`);
      console.log(`  - Notifications deleted: ${notificationsResult.deletedCount}`);
      console.log(`  - Installations deactivated: ${installationsResult.modifiedCount}`);
      console.log(`  - Installation reports deleted: ${reportsResult.deletedCount}`);

      return { 
        success: true, 
        message: 'User and associated data deleted successfully',
        deletionSummary: {
          username: user.username,
          userId: userId,
          sessionsDeleted: sessionsResult.deletedCount,
          downloadKeysDeleted: downloadKeysResult.deletedCount,
          updateKeysDeleted: updateKeysResult.deletedCount,
          notificationsDeleted: notificationsResult.deletedCount,
          installationsDeactivated: installationsResult.modifiedCount,
          installationReportsDeleted: reportsResult.deletedCount,
          totalInstallations: userInstallations.length,
          installationDetails: userInstallations.map(i => ({
            clientId: i.clientId,
            installationId: i.installationId,
            macAddress: i.macAddress,
            hostname: i.hostname,
            platform: i.platform,
            createdAt: i.createdAt,
            lastCheckin: i.lastCheckin
          }))
        }
      };
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
    // Priority order: GitHub commits > GitHub releases > GitHub deployments
    // Changed to prioritize commits so we get ALL development history
    let externalData = await this.fetchGitHubCommits();
    
    if (!externalData || externalData.length === 0) {
      externalData = await this.fetchGitHubReleases();
    }
    
    if (!externalData || externalData.length === 0) {
      externalData = await this.fetchGitHubDeployments();
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
  
  async syncNewestCommits() {
    try {
      if (this.usesFallback) {
        return;
      }
      
      await this.connect();
      
      // Fetch just the first few commits to check for new ones (lightweight)
      const recentCommits = await this.fetchRecentGitHubCommits(10); // Only get 10 recent commits
      
      if (!recentCommits || recentCommits.length === 0) {
        return;
      }
      
      // Get the latest commit from database
      const latestDbCommit = await this.db.collection('versionHistory')
        .findOne({}, { sort: { versionNumber: -1 } });
      
      if (!latestDbCommit) {
        // No commits in DB, don't auto-sync all (that's for syncAllCommits)
        return;
      }
      
      // Check if the newest commit from GitHub is newer than our latest
      const newestGitHubCommit = recentCommits[0]; // First one is newest
      
      // Check if this commit already exists
      if (latestDbCommit.sha && latestDbCommit.sha === newestGitHubCommit.sha) {
        // Latest commit already in database
        return;
      }
      
      // Check by date as fallback
      const newestDate = new Date(newestGitHubCommit.date);
      const latestDbDate = new Date(latestDbCommit.date || latestDbCommit.createdAt);
      
      if (newestDate <= latestDbDate) {
        // Not newer
        return;
      }
      
      // New commit found - add it
      await this.addNewestVersionToDatabase(newestGitHubCommit, latestDbCommit);
      
    } catch (error) {
      console.log('Lightweight commit sync failed:', error.message);
    }
  }
  
  async syncAllCommits() {
    try {
      console.log('🚀 Starting comprehensive commit history sync...');
      
      if (this.usesFallback) {
        console.log('Cannot sync commits - using fallback storage');
        return { success: false, message: 'Commit sync requires MongoDB connection' };
      }
      
      await this.connect();
      
      // Get all commits from GitHub
      console.log('📦 Fetching ALL commits from GitHub...');
      const externalVersions = await this.fetchGitHubCommits();
      
      if (!externalVersions || externalVersions.length === 0) {
        console.log('❌ No external commits found for sync');
        return { success: true, message: 'No commits found', newCommits: 0 };
      }
      
      console.log(`📊 Found ${externalVersions.length} commits from GitHub`);
      
      // Get existing versions from database
      const existingVersions = await this.db.collection('versionHistory')
        .find({})
        .toArray();
      
      const existingShas = new Set(existingVersions.map(d => d.sha).filter(Boolean));
      
      console.log(`💾 Found ${existingVersions.length} existing versions in database`);
      
      // Sort external versions by date (oldest first)
      const sortedExternalVersions = [...externalVersions].sort((a, b) => new Date(a.date) - new Date(b.date));
      
      // Filter out commits that already exist
      const newCommits = sortedExternalVersions.filter(commit => {
        // Check by SHA (most reliable for commits)
        if (commit.sha && existingShas.has(commit.sha)) {
          return false;
        }
        
        // Check by message and date combination as fallback
        const matchingRecord = existingVersions.find(existing => 
          existing.message === commit.message && 
          existing.date === commit.date
        );
        
        return !matchingRecord;
      });
      
      console.log(`🆕 Found ${newCommits.length} new commits to add`);
      
      if (newCommits.length === 0) {
        return { 
          success: true, 
          message: 'No new commits found - database is up to date', 
          newCommits: 0,
          totalExternal: externalVersions.length,
          totalExisting: existingVersions.length
        };
      }
      
      // Get the current highest version number
      const highestVersionRecord = await this.db.collection('versionHistory')
        .findOne({}, { sort: { versionNumber: -1 } });
      
      let nextVersionNumber = highestVersionRecord ? highestVersionRecord.versionNumber + 1 : 1;
      
      // Create version records for new commits
      const newVersionRecords = [];
      
      for (const commit of newCommits) {
        const semanticVersion = this.calculateSemanticVersion(nextVersionNumber - 1);
        
        const versionRecord = {
          versionNumber: nextVersionNumber,
          version: semanticVersion,
          message: commit.message || 'No message',
          description: commit.description || commit.message || '',
          date: commit.date,
          sha: commit.sha || null,
          deploymentId: null, // Commits don't have deployment IDs
          author: commit.author || 'Unknown',
          source: commit.source || 'github-commits',
          isCurrent: false, // Will be updated later
          createdAt: new Date(),
          url: null // Commits don't have deployment URLs
        };
        
        newVersionRecords.push(versionRecord);
        nextVersionNumber++;
      }
      
      // Insert new commit records
      if (newVersionRecords.length > 0) {
        await this.db.collection('versionHistory').insertMany(newVersionRecords);
        
        // Update the current version flag - mark the highest version number as current
        await this.db.collection('versionHistory').updateMany(
          {},
          { $set: { isCurrent: false } }
        );
        
        const latestVersion = await this.db.collection('versionHistory')
          .findOne({}, { sort: { versionNumber: -1 } });
        
        if (latestVersion) {
          await this.db.collection('versionHistory').updateOne(
            { _id: latestVersion._id },
            { $set: { isCurrent: true } }
          );
        }
        
        console.log(`✅ Successfully added ${newVersionRecords.length} new commits`);
        console.log(`📅 Version range: ${newVersionRecords[0].version} to ${newVersionRecords[newVersionRecords.length-1].version}`);
      }
      
      return {
        success: true,
        message: `Successfully synced ${newVersionRecords.length} new commits`,
        newCommits: newVersionRecords.length,
        totalExternal: externalVersions.length,
        totalExisting: existingVersions.length,
        totalAfterSync: existingVersions.length + newVersionRecords.length,
        versionRange: newVersionRecords.length > 0 ? {
          first: newVersionRecords[0].version,
          last: newVersionRecords[newVersionRecords.length-1].version
        } : null
      };
      
    } catch (error) {
      console.error('❌ Error performing comprehensive commit sync:', error);
      return { success: false, message: error.message };
    }
  }
  
  async syncAllDeployments() {
    try {
      console.log('Starting comprehensive deployment sync...');
      
      if (this.usesFallback) {
        console.log('Cannot sync deployments - using fallback storage');
        return { success: false, message: 'Deployment sync requires MongoDB connection' };
      }
      
      await this.connect();
      
      // Get all deployments from GitHub
      const externalVersions = await this.fetchGitHubDeployments();
      
      if (!externalVersions || externalVersions.length === 0) {
        console.log('No external deployments found for sync');
        return { success: true, message: 'No deployments found', newDeployments: 0 };
      }
      
      console.log(`Found ${externalVersions.length} verified deployments from GitHub`);
      
      // Get existing deployments from database
      const existingDeployments = await this.db.collection('versionHistory')
        .find({})
        .toArray();
      
      const existingDeploymentIds = new Set(existingDeployments.map(d => d.deploymentId).filter(Boolean));
      const existingShas = new Set(existingDeployments.map(d => d.sha).filter(Boolean));
      
      console.log(`Found ${existingDeployments.length} existing deployments in database`);
      
      // Sort external versions by date (oldest first)
      const sortedExternalVersions = [...externalVersions].sort((a, b) => new Date(a.date) - new Date(b.date));
      
      // Filter out deployments that already exist
      const newDeployments = sortedExternalVersions.filter(deployment => {
        // Check by deployment ID first (most reliable)
        if (deployment.deploymentId && existingDeploymentIds.has(deployment.deploymentId)) {
          return false;
        }
        
        // Check by SHA as fallback
        if (deployment.sha && existingShas.has(deployment.sha)) {
          return false;
        }
        
        // Check by message and date combination
        const matchingRecord = existingDeployments.find(existing => 
          existing.message === deployment.message && 
          existing.date === deployment.date
        );
        
        return !matchingRecord;
      });
      
      console.log(`Found ${newDeployments.length} new deployments to add`);
      
      if (newDeployments.length === 0) {
        return { 
          success: true, 
          message: 'No new deployments found - database is up to date', 
          newDeployments: 0,
          totalExternal: externalVersions.length,
          totalExisting: existingDeployments.length
        };
      }
      
      // Get the current highest version number
      const highestVersionRecord = await this.db.collection('versionHistory')
        .findOne({}, { sort: { versionNumber: -1 } });
      
      let nextVersionNumber = highestVersionRecord ? highestVersionRecord.versionNumber + 1 : 1;
      
      // Create version records for new deployments
      const newVersionRecords = [];
      
      for (const deployment of newDeployments) {
        const semanticVersion = this.calculateSemanticVersion(nextVersionNumber - 1);
        
        const versionRecord = {
          versionNumber: nextVersionNumber,
          version: semanticVersion,
          message: deployment.message || 'No message',
          description: deployment.description || deployment.message || '',
          date: deployment.date,
          sha: deployment.sha || null,
          deploymentId: deployment.deploymentId || null,
          author: deployment.author || 'Unknown',
          source: deployment.source || 'github-deployments',
          isCurrent: false, // Will be updated later
          createdAt: new Date(),
          url: deployment.url || null
        };
        
        newVersionRecords.push(versionRecord);
        nextVersionNumber++;
      }
      
      // Insert new deployment records
      if (newVersionRecords.length > 0) {
        await this.db.collection('versionHistory').insertMany(newVersionRecords);
        
        // Update the current version flag - mark the highest version number as current
        await this.db.collection('versionHistory').updateMany(
          {},
          { $set: { isCurrent: false } }
        );
        
        const latestVersion = await this.db.collection('versionHistory')
          .findOne({}, { sort: { versionNumber: -1 } });
        
        if (latestVersion) {
          await this.db.collection('versionHistory').updateOne(
            { _id: latestVersion._id },
            { $set: { isCurrent: true } }
          );
        }
        
        console.log(`Successfully added ${newVersionRecords.length} new deployments`);
        console.log(`New version range: ${newVersionRecords[0].version} to ${newVersionRecords[newVersionRecords.length-1].version}`);
      }
      
      return {
        success: true,
        message: `Successfully synced ${newVersionRecords.length} new deployments`,
        newDeployments: newVersionRecords.length,
        totalExternal: externalVersions.length,
        totalExisting: existingDeployments.length,
        totalAfterSync: existingDeployments.length + newVersionRecords.length,
        versionRange: newVersionRecords.length > 0 ? {
          first: newVersionRecords[0].version,
          last: newVersionRecords[newVersionRecords.length-1].version
        } : null
      };
      
    } catch (error) {
      console.error('Error performing comprehensive deployment sync:', error);
      return { success: false, message: error.message };
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

  // Installation Reporting Methods
  async reportInstallation(keyId, macAddress, installPath, version, status, timestamp, additionalData = {}) {
    try {
      const installationReport = {
        keyId,
        macAddress,
        installPath,
        version,
        status,
        timestamp: timestamp || new Date().toISOString(),
        reportedAt: new Date(),
        ...additionalData
      };

      if (this.usesFallback) {
        // In fallback mode, just log the installation report
        console.log('Installation report (fallback):', installationReport);
        return { success: true, message: 'Installation reported in fallback mode' };
      }

      await this.connect();
      
      // Store installation report in database
      await this.db.collection('installationReports').insertOne(installationReport);
      
      return {
        success: true,
        message: 'Installation reported successfully',
        reportId: installationReport._id?.toString()
      };
    } catch (error) {
      console.error('Installation reporting error:', error);
      return { success: false, message: error.message };
    }
  }

  async getInstallationReports(limit = 50, macAddress = null) {
    try {
      if (this.usesFallback) {
        return { success: true, data: [] };
      }

      await this.connect();
      
      const query = macAddress ? { macAddress } : {};
      const reports = await this.db.collection('installationReports')
        .find(query)
        .sort({ reportedAt: -1 })
        .limit(limit)
        .toArray();

      const processedReports = reports.map(report => ({
        _id: report._id.toString(),
        keyId: report.keyId,
        macAddress: report.macAddress,
        installPath: report.installPath,
        version: report.version,
        status: report.status,
        timestamp: report.timestamp,
        reportedAt: report.reportedAt,
        clientId: report.clientId,
        username: report.username,
        hostname: report.hostname,
        platform: report.platform,
        macDetectionMethod: report.macDetectionMethod,
        installerMode: report.installerMode,
        systemInfo: report.systemInfo
      }));

      return { success: true, data: processedReports };
    } catch (error) {
      console.error('Get installation reports error:', error);
      return { success: false, message: error.message };
    }
  }

  // Database Cleanup Methods
  async cleanupUnusedCollections() {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Database cleanup requires MongoDB connection' };
      }

      await this.connect();
      
      const collectionsToRemove = [
        'macClients',      // Replaced by installations collection
        'clientHistory',   // Replaced by installations collection
        'securityKeys',    // Keys now embedded in installations collection
        'clientInfo',      // Info now stored in installations collection
        'clients',         // Legacy client registration, replaced by installations
        'clientInstallations'  // Old installation tracking, replaced by installations
      ];
      
      const cleanupResults = [];
      const existingCollections = await this.db.listCollections().toArray();
      const existingCollectionNames = existingCollections.map(col => col.name);
      
      console.log('🔍 Checking for unused collections to cleanup...');
      console.log(`📋 Database has ${existingCollectionNames.length} collections: ${existingCollectionNames.join(', ')}`);
      
      for (const collectionName of collectionsToRemove) {
        if (existingCollectionNames.includes(collectionName)) {
          try {
            // Get document count before deletion
            const documentCount = await this.db.collection(collectionName).countDocuments();
            
            // Drop the collection
            await this.db.collection(collectionName).drop();
            
            cleanupResults.push({
              collection: collectionName,
              status: 'removed',
              documentCount,
              message: `Removed collection '${collectionName}' with ${documentCount} documents`
            });
            
            console.log(`✅ Removed collection '${collectionName}' (${documentCount} documents)`);
          } catch (error) {
            cleanupResults.push({
              collection: collectionName,
              status: 'error',
              documentCount: 0,
              message: `Failed to remove '${collectionName}': ${error.message}`
            });
            
            console.log(`❌ Failed to remove collection '${collectionName}': ${error.message}`);
          }
        } else {
          cleanupResults.push({
            collection: collectionName,
            status: 'not_found',
            documentCount: 0,
            message: `Collection '${collectionName}' does not exist`
          });
          
          console.log(`ℹ️ Collection '${collectionName}' does not exist (already cleaned up)`);
        }
      }
      
      const removedCount = cleanupResults.filter(r => r.status === 'removed').length;
      const errorCount = cleanupResults.filter(r => r.status === 'error').length;
      const totalDocuments = cleanupResults.reduce((sum, r) => sum + r.documentCount, 0);
      
      console.log(`\n📊 CLEANUP SUMMARY:`);
      console.log(`   Collections removed: ${removedCount}`);
      console.log(`   Collections with errors: ${errorCount}`);
      console.log(`   Total documents removed: ${totalDocuments}`);
      
      return {
        success: true,
        message: `Database cleanup completed. Removed ${removedCount} collections with ${totalDocuments} total documents.`,
        results: cleanupResults,
        summary: {
          collectionsRemoved: removedCount,
          collectionsWithErrors: errorCount,
          totalDocumentsRemoved: totalDocuments,
          collectionsChecked: collectionsToRemove.length
        }
      };
    } catch (error) {
      console.error('❌ Database cleanup error:', error);
      return { success: false, message: error.message };
    }
  }

  async listAllCollections() {
    try {
      if (this.usesFallback) {
        return {
          success: true,
          collections: ['fallback_storage'],
          message: 'Using fallback storage - no MongoDB collections'
        };
      }

      await this.connect();
      
      const collections = await this.db.listCollections().toArray();
      const collectionInfo = [];
      
      console.log(`📋 Found ${collections.length} collections in database:`);
      
      for (const collection of collections) {
        try {
          const documentCount = await this.db.collection(collection.name).countDocuments();
          const collectionStats = await this.db.collection(collection.name).stats();
          
          const info = {
            name: collection.name,
            documentCount,
            size: collectionStats.size || 0,
            storageSize: collectionStats.storageSize || 0,
            avgDocumentSize: documentCount > 0 ? Math.round((collectionStats.size || 0) / documentCount) : 0
          };
          
          collectionInfo.push(info);
          console.log(`   📁 ${collection.name}: ${documentCount} documents (${Math.round((collectionStats.size || 0) / 1024)} KB)`);
        } catch (error) {
          collectionInfo.push({
            name: collection.name,
            documentCount: 0,
            size: 0,
            storageSize: 0,
            avgDocumentSize: 0,
            error: error.message
          });
          console.log(`   ❌ ${collection.name}: Error getting stats - ${error.message}`);
        }
      }
      
      const totalDocuments = collectionInfo.reduce((sum, col) => sum + col.documentCount, 0);
      const totalSize = collectionInfo.reduce((sum, col) => sum + col.size, 0);
      
      return {
        success: true,
        collections: collectionInfo,
        summary: {
          totalCollections: collections.length,
          totalDocuments,
          totalSize,
          totalSizeKB: Math.round(totalSize / 1024),
          totalSizeMB: Math.round(totalSize / (1024 * 1024))
        },
        message: `Found ${collections.length} collections with ${totalDocuments} total documents`
      };
    } catch (error) {
      console.error('❌ Error listing collections:', error);
      return { success: false, message: error.message };
    }
  }

  async backupCollectionBeforeCleanup(collectionName) {
    try {
      if (this.usesFallback) {
        return { success: false, message: 'Backup requires MongoDB connection' };
      }

      await this.connect();
      
      // Check if collection exists
      const collections = await this.db.listCollections({ name: collectionName }).toArray();
      if (collections.length === 0) {
        return { success: false, message: `Collection '${collectionName}' does not exist` };
      }
      
      // Get all documents from the collection
      const documents = await this.db.collection(collectionName).find({}).toArray();
      
      if (documents.length === 0) {
        return {
          success: true,
          message: `Collection '${collectionName}' is empty - no backup needed`,
          documentCount: 0
        };
      }
      
      // Create backup collection name with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupCollectionName = `backup_${collectionName}_${timestamp}`;
      
      // Insert documents into backup collection
      await this.db.collection(backupCollectionName).insertMany(documents);
      
      console.log(`✅ Backed up ${documents.length} documents from '${collectionName}' to '${backupCollectionName}'`);
      
      return {
        success: true,
        message: `Backed up ${documents.length} documents to '${backupCollectionName}'`,
        originalCollection: collectionName,
        backupCollection: backupCollectionName,
        documentCount: documents.length
      };
    } catch (error) {
      console.error('❌ Backup error:', error);
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
module.exports = async function handler(req, res) {
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
        // Handle comprehensive client registration from the installer
        if (params.installationKey && params.macAddress) {
          // This is a full client installation registration
          result = await db.registerClientInstallation({
            installationKey: params.installationKey,
            macAddress: params.macAddress,
            username: params.username || '',
            clientName: params.clientName || '',
            hostname: params.hostname || '',
            platform: params.platform || '',
            version: params.version || '',
            installPath: params.installPath || '',
            macDetectionMethod: params.macDetectionMethod || 'unknown',
            installerMode: params.installerMode || 'standard',
            timestamp: params.timestamp || new Date().toISOString(),
            systemInfo: params.systemInfo || {}
          });
        } else {
          // Fallback to simple registration for backward compatibility
          result = await db.registerClient(
            params.clientId || '',
            params.clientName || '',
            params.computerName || ''
          );
        }
        break;

      case 'sendNotificationToAllClients':
      case 'sendNotification': {
        // Get user context for role-based targeting
        const notificationAuthHeader = req.headers.authorization;
        const notificationToken = notificationAuthHeader && notificationAuthHeader.startsWith('Bearer ')
          ? notificationAuthHeader.substring(7)
          : (params.token || '');
        
        let sendingUserId = null;
        let sendingUserRole = null;
        
        if (notificationToken) {
          const validation = await db.validateSession(notificationToken);
          if (validation.success) {
            sendingUserId = validation.user?.id;
            sendingUserRole = validation.role || validation.user?.role;
          } else {
            result = { success: false, message: 'Authentication required to send notifications' };
            break;
          }
        } else {
          result = { success: false, message: 'Authentication token required' };
          break;
        }
        
        const allowBrowserUsage = params.allowBrowserUsage === 'true' || params.allowBrowserUsage === true;
        let allowedWebsites = params.allowedWebsites || '';
        if (Array.isArray(allowedWebsites)) {
          allowedWebsites = allowedWebsites.filter(Boolean).join(',');
        }
        
        result = await db.sendNotificationToAllClients(
          params.message || '',
          allowBrowserUsage,
          allowedWebsites,
          sendingUserId,
          sendingUserRole,
          params.targetClientId || null
        );
        break;
      }

      case 'getActiveNotifications':
      case 'getNotifications':
        // If clientId is provided, get client-specific notifications (includes uninstall commands)
        if (params.clientId) {
          result = await db.getClientNotifications(params.clientId);
          if (result.success) {
            result.notifications = result.data;
            result.clientCount = 0;
          }
        } else {
          // Admin view - get all active notifications (excludes uninstall commands)
          result = await db.getActiveNotifications();
          if (result.success) {
            result.notifications = result.data;
            result.clientCount = 0;
          }
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

      case 'getAllMacClients': {
        // Get user context for role-based filtering
        const macClientsAuthHeader = req.headers.authorization;
        const macClientsToken = macClientsAuthHeader && macClientsAuthHeader.startsWith('Bearer ')
          ? macClientsAuthHeader.substring(7)
          : (params.token || '');
        
        let requestingUserId = null;
        let requestingUserRole = null;
        
        if (macClientsToken) {
          const validation = await db.validateSession(macClientsToken);
          if (validation.success) {
            requestingUserId = validation.user?.id;
            requestingUserRole = validation.role || validation.user?.role;
          }
        }
        
        result = await db.getAllMacClients(requestingUserId, requestingUserRole);
        break;
      }

      case 'getClientHistory':
        result = await db.getClientHistory(params.macAddress || null);
        break;

      case 'deactivateClient':
        result = await db.deactivateClient(
          params.clientId || '',
          params.reason || 'Manual deactivation'
        );
        break;

      case 'deactivateMacClient':
        result = await db.deactivateMacClient(
          params.macAddress || '',
          params.reason || 'Manual deactivation'
        );
        break;

      // Installation Reporting Actions
      case 'reportInstallation':
        result = await db.reportInstallation(
          params.keyId || '',
          params.macAddress || '',
          params.installPath || '',
          params.version || '',
          params.status || 'completed',
          params.timestamp || new Date().toISOString(),
          // Pass any additional parameters as additional data
          Object.fromEntries(
            Object.entries(params).filter(([key]) => 
              !['action', 'keyId', 'macAddress', 'installPath', 'version', 'status', 'timestamp'].includes(key)
            )
          )
        );
        break;

      case 'getInstallationReports': {
        const reportsAuthHeader = req.headers.authorization;
        const reportsToken = reportsAuthHeader && reportsAuthHeader.startsWith('Bearer ')
          ? reportsAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(reportsToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.getInstallationReports(
          parseInt(params.limit) || 50,
          params.macAddress || null
        );
        break;
      }

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
      case 'registerUser': {
        // For user registration, validate session if createdBy should be set
        let createdBy = null;
        
        if (params.requireAuth !== false) { // Allow bypassing auth for initial registration
          const createAuthHeader = req.headers.authorization;
          const createToken = createAuthHeader && createAuthHeader.startsWith('Bearer ')
            ? createAuthHeader.substring(7)
            : (params.token || '');
          
          if (createToken) {
            const validation = await db.validateSession(createToken);
            if (validation.success) {
              const userRole = validation.role || validation.user?.role;
              // Only admins and master_admins can create users
              if (userRole === 'admin' || userRole === 'master_admin') {
                createdBy = validation.user?.id;
              }
            }
          }
        }
        
        result = await db.createUser(
          params.username || '',
          params.email || '',
          params.password || '',
          params.role || 'user',
          createdBy,
          params.firstName || '',
          params.lastName || '',
          params.phoneNumber || '',
          params.address || ''
        );
        break;
      }

      // Installation Key Management Actions
      case 'validateInstallationKey':
        result = await db.validateInstallationKey(params.installationKey || '');
        break;

      case 'registerClientWithInstallationKey':
        result = await db.registerClientWithInstallationKey(
          params.clientId || '',
          params.installationKey || '',
          params.validatedUser || null,
          params.validatedAt || '',
          params.installPath || '',
          params.hostname || '',
          params.platform || '',
          params.version || '',
          params.registeredAt || new Date().toISOString()
        );
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
        const userRole = validation.role || validation.user?.role;
        const isAdmin = userRole === 'admin' || userRole === 'master_admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        result = await db.getAllUsers(validation.user?.id, userRole);
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

      // Password Management Actions (Admin)
      case 'generateUserPassword': {
        const genAuthHeader = req.headers.authorization;
        const genToken = genAuthHeader && genAuthHeader.startsWith('Bearer ')
          ? genAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(genToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const userRole = validation.role || validation.user?.role;
        const isAdmin = userRole === 'admin' || userRole === 'master_admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.generateUserPassword(
          validation.user?.id,
          params.targetUserId || '',
          parseInt(params.length) || 16
        );
        break;
      }

      case 'setUserPassword': {
        const setAuthHeader = req.headers.authorization;
        const setToken = setAuthHeader && setAuthHeader.startsWith('Bearer ')
          ? setAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(setToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const userRole = validation.role || validation.user?.role;
        const isAdmin = userRole === 'admin' || userRole === 'master_admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.setUserPassword(
          validation.user?.id,
          params.targetUserId || '',
          params.newPassword || ''
        );
        break;
      }

      case 'generatePasswordOptions': {
        const optAuthHeader = req.headers.authorization;
        const optToken = optAuthHeader && optAuthHeader.startsWith('Bearer ')
          ? optAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(optToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const userRole = validation.role || validation.user?.role;
        const isAdmin = userRole === 'admin' || userRole === 'master_admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.generatePasswordOptions(
          parseInt(params.count) || 3,
          parseInt(params.length) || 16
        );
        break;
      }

      // Password Reset Actions (Self)
      case 'resetOwnPassword': {
        const resetOwnAuthHeader = req.headers.authorization;
        const resetOwnToken = resetOwnAuthHeader && resetOwnAuthHeader.startsWith('Bearer ')
          ? resetOwnAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(resetOwnToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        
        result = await db.resetOwnPassword(
          validation.user?.id,
          params.currentPassword || '',
          params.newPassword || ''
        );
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

      // Account Settings Actions (Self-update)
      case 'updateAccountInfo': {
        const updateAuthHeader = req.headers.authorization;
        const updateToken = updateAuthHeader && updateAuthHeader.startsWith('Bearer ')
          ? updateAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(updateToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        
        // Users can only update their own account info
        const userId = validation.user?.id;
        if (!userId) {
          result = { success: false, message: 'User ID not found in session' };
          break;
        }
        
        result = await db.updateAccountInfo(userId, {
          firstName: params.firstName,
          lastName: params.lastName,
          email: params.email,
          phoneNumber: params.phoneNumber,
          address: params.address,
          subscription: params.subscription
        });
        break;
      }

      case 'getAccountInfo': {
        const accountAuthHeader = req.headers.authorization;
        const accountToken = accountAuthHeader && accountAuthHeader.startsWith('Bearer ')
          ? accountAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(accountToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        
        // Return user's own account information
        const userId = validation.user?.id;
        if (!userId) {
          result = { success: false, message: 'User ID not found in session' };
          break;
        }
        
        try {
          await db.connect();
          const user = await db.db.collection('users').findOne(
            { _id: new ObjectId(userId) },
            { projection: { password: 0 } }
          );
          
          if (!user) {
            result = { success: false, message: 'User not found' };
            break;
          }
          
          result = {
            success: true,
            user: {
              id: user._id.toString(),
              username: user.username,
              email: user.email,
              firstName: user.firstName || '',
              lastName: user.lastName || '',
              phoneNumber: user.phoneNumber || '',
              address: user.address || '',
              role: user.role,
              subscription: user.subscription || {},
              createdAt: user.createdAt,
              lastLogin: user.lastLogin
            }
          };
        } catch (error) {
          result = { success: false, message: error.message };
        }
        break;
      }

      // Version History Actions
      case 'getVersionHistory':
        result = await db.getVersionHistory();
        break;
        
      case 'checkForUpdates':
        const clientVersionNumber = parseInt(params.versionNumber || '0');
        const clientId = params.clientId || 'unknown';
        const macAddress = params.macAddress || '';
        
        // Get the latest version info from database
        const versionInfo = await db.getVersionInfo();
        
        if (versionInfo.success && versionInfo.versionNumber) {
          const latestVersionNumber = versionInfo.versionNumber;
          const updateAvailable = latestVersionNumber > clientVersionNumber;
          
          if (updateAvailable) {
            // Generate installation key for the update
            const updateKeyResult = await db.generateUpdateInstallationKey(clientId, macAddress);
            
            result = {
              success: true,
              updateAvailable,
              latestVersion: versionInfo.currentVersion,
              latestVersionNumber,
              currentVersionNumber: clientVersionNumber,
              releaseNotes: versionInfo.releaseNotes || 'New version available',
              downloadUrl: `/api/download?file=client&updateKey=${updateKeyResult.success ? updateKeyResult.installationKey : ''}`,
              installationKey: updateKeyResult.success ? updateKeyResult.installationKey : null,
              forceUpdate: false,
              timestamp: new Date().toISOString()
            };
          } else {
            result = {
              success: true,
              updateAvailable,
              latestVersion: versionInfo.currentVersion,
              latestVersionNumber,
              currentVersionNumber: clientVersionNumber,
              releaseNotes: versionInfo.releaseNotes || 'You are running the latest version',
              downloadUrl: '/api/download?file=client',
              forceUpdate: false,
              timestamp: new Date().toISOString()
            };
          }
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

      // Clear All Notifications Action (Admin only)
      case 'clearAllNotifications': {
        const clearAllAuthHeader = req.headers.authorization;
        const clearAllToken = clearAllAuthHeader && clearAllAuthHeader.startsWith('Bearer ')
          ? clearAllAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(clearAllToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.clearAllNotifications();
        break;
      }
      
      // Sync All Commits Action (Admin only)
      case 'syncAllCommits': {
        const syncCommitsAuthHeader = req.headers.authorization;
        const syncCommitsToken = syncCommitsAuthHeader && syncCommitsAuthHeader.startsWith('Bearer ')
          ? syncCommitsAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(syncCommitsToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.syncAllCommits();
        break;
      }
      
      // Sync All Deployments Action (Admin only)
      case 'syncAllDeployments': {
        const syncAuthHeader = req.headers.authorization;
        const syncToken = syncAuthHeader && syncAuthHeader.startsWith('Bearer ')
          ? syncAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(syncToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.syncAllDeployments();
        break;
      }
      
      // Client Uninstall Request Actions
      case 'requestUninstall':
        result = await db.requestUninstall(
          params.clientId || '',
          params.macAddress || '',
          params.keyId || '',
          params.installPath || '',
          params.timestamp || new Date().toISOString(),
          params.reason || 'Force quit detected'
        );
        break;
        
      case 'getUninstallRequests': {
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
        
        result = await db.getUninstallRequests();
        break;
      }
      
      case 'approveUninstallRequest': {
        const approveAuthHeader = req.headers.authorization;
        const approveToken = approveAuthHeader && approveAuthHeader.startsWith('Bearer ')
          ? approveAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(approveToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.approveUninstallRequest(
          params.requestId || '',
          validation.user.username || 'Admin'
        );
        break;
      }
      
      case 'denyUninstallRequest': {
        const denyAuthHeader = req.headers.authorization;
        const denyToken = denyAuthHeader && denyAuthHeader.startsWith('Bearer ')
          ? denyAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(denyToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.denyUninstallRequest(
          params.requestId || '',
          params.reason || 'Request denied by administrator',
          validation.user.username || 'Admin'
        );
        break;
      }
      
      // Website Request Approval Actions
      case 'approveWebsiteRequest': {
        const approveAuthHeader = req.headers.authorization;
        const approveToken = approveAuthHeader && approveAuthHeader.startsWith('Bearer ')
          ? approveAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(approveToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.approveWebsiteRequest(
          params.requestId || '',
          validation.user.username || 'Admin'
        );
        break;
      }
      
      case 'denyWebsiteRequest': {
        const denyAuthHeader = req.headers.authorization;
        const denyToken = denyAuthHeader && denyAuthHeader.startsWith('Bearer ')
          ? denyAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(denyToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.denyWebsiteRequest(
          params.requestId || '',
          params.reason || 'Request denied by administrator',
          validation.user.username || 'Admin'
        );
        break;
      }
      
      // Notification Management Actions
      case 'acknowledgeNotification': {
        const ackAuthHeader = req.headers.authorization;
        const ackToken = ackAuthHeader && ackAuthHeader.startsWith('Bearer ')
          ? ackAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(ackToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.acknowledgeNotification(
          params.notificationId || '',
          validation.user.username || 'Admin'
        );
        break;
      }
      
      case 'snoozeNotification': {
        const snoozeAuthHeader = req.headers.authorization;
        const snoozeToken = snoozeAuthHeader && snoozeAuthHeader.startsWith('Bearer ')
          ? snoozeAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(snoozeToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.snoozeNotification(
          params.notificationId || '',
          parseInt(params.minutes) || 15,
          validation.user.username || 'Admin'
        );
        break;
      }
      
      // Save Custom Message Action
      case 'saveCustomMessage': {
        const saveAuthHeader = req.headers.authorization;
        const saveToken = saveAuthHeader && saveAuthHeader.startsWith('Bearer ')
          ? saveAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(saveToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.saveCustomMessage(
          params.text || '',
          params.description || '',
          params.allowBrowserUsage || false,
          params.allowedWebsites || [],
          validation.user.username || 'Admin'
        );
        break;
      }
      
      // Delete Custom Message Action
      case 'deleteCustomMessage': {
        const deleteAuthHeader = req.headers.authorization;
        const deleteToken = deleteAuthHeader && deleteAuthHeader.startsWith('Bearer ')
          ? deleteAuthHeader.substring(7)
          : (params.token || '');

        const validation = await db.validateSession(deleteToken);
        if (!validation.success) {
          result = { success: false, message: 'Authentication required' };
          break;
        }
        const isAdmin = validation.role === 'admin' || validation.user?.role === 'admin';
        if (!isAdmin) {
          result = { success: false, message: 'Admin privileges required' };
          break;
        }
        
        result = await db.deleteCustomMessage(
          params.messageId || '',
          validation.user.username || 'Admin'
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
