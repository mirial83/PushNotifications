// PushNotifications Node.js API
const { MongoClient, ObjectId } = require('mongodb');

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
        const clientId = `${username}_${macAddress.replace(/[:-]/g, '').substr(-6)}`;
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
      const clientId = `${username}_${macAddress.replace(/[:-]/g, '').substr(-6)}_${installationCount}`;
      const installationId = `inst_${macAddress.replace(/[:-]/g, '')}_${installationCount}`;
      const keyId = `key_${macAddress.replace(/[:-]/g, '')}_${Date.now()}`;
      
      // Generate security key for embedding
      const securityKeyValue = this.generateInstallationKey();

      // Store comprehensive installation record in unified structure
      const installationRecord = {
        installationId,
        clientId,
        installationKey,
        keyId,
        
        // MAC address and device info
        macAddress,
        macDetectionMethod,
        
        // User information
        username,
        clientName: generatedClientName,
        userId: keyValidation.user ? new ObjectId(keyValidation.user.id) : null,
        userRole: keyValidation.user ? keyValidation.user.role : 'user',
        
        // System information
        hostname,
        platform,
        version,
        installPath,
        systemInfo,
        
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
            type: { $ne: 'uninstall_request' },
            type: { $ne: 'uninstall_command' }
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
        message: 'Uninstall request submitted successfully',
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
      
      // Get all installations from the unified collection, grouped by MAC address
      const installations = await this.db.collection('installations')
        .find({})
        .sort({ macAddress: 1, createdAt: -1 }) // Sort by MAC address, then by creation date (newest first)
        .toArray();

      // Group installations by MAC address
      const macClientMap = new Map();
      
      for (const installation of installations) {
        const macAddress = installation.macAddress;
        
        if (!macClientMap.has(macAddress)) {
          // Initialize MAC client entry with the first (most recent) installation
          macClientMap.set(macAddress, {
            _id: installation._id.toString(),
            macAddress: installation.macAddress,
            username: installation.username,
            clientName: installation.clientName,
            activeClientId: installation.isActive ? installation.clientId : null,
            installationCount: installation.installationCount || 1,
            hostname: installation.hostname,
            platform: installation.platform,
            createdAt: installation.createdAt,
            registeredAt: installation.registeredAt,
            lastCheckin: installation.lastCheckin,
            // Current active installation (if this one is active)
            activeInstallation: installation.isActive && installation.isCurrentForMac ? {
              clientId: installation.clientId,
              installationId: installation.installationId,
              keyId: installation.keyId,
              installPath: installation.installPath,
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
              installPath: installation.installPath,
              version: installation.version,
              createdAt: installation.createdAt,
              lastCheckin: installation.lastCheckin,
              isActive: installation.isActive,
              isCurrentForMac: installation.isCurrentForMac,
              deactivatedAt: installation.deactivatedAt,
              deactivationReason: installation.deactivationReason
            },
            // Count of all installations for this MAC
            totalInstallations: installations.filter(i => i.macAddress === macAddress).length,
            // Count of active installations for this MAC
            activeInstallations: installations.filter(i => i.macAddress === macAddress && i.isActive).length
          });
        } else {
          // Update existing MAC client entry with active installation info if needed
          const macClient = macClientMap.get(macAddress);
          
          // Update active installation if this installation is current and active
          if (installation.isActive && installation.isCurrentForMac && !macClient.activeInstallation) {
            macClient.activeClientId = installation.clientId;
            macClient.activeInstallation = {
              clientId: installation.clientId,
              installationId: installation.installationId,
              keyId: installation.keyId,
              installPath: installation.installPath,
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
      
      // Try to find an existing client to get user context
      let user = null;
      if (macAddress) {
        const macClient = await this.db.collection('macClients').findOne({ macAddress });
        if (macClient && macClient.activeClientId) {
          // Try to find the client installation record to get user info
          const installation = await this.db.collection('installations').findOne({
            clientId: macClient.activeClientId
          });
          if (installation && installation.userId) {
            user = await this.db.collection('users').findOne({
              _id: installation.userId,
              isActive: true
            });
          }
        }
      }
      
      // If we can't find user context, create a generic update key
      if (!user) {
        console.log(`Creating generic update key for client ${clientId}`);
        
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
          used: false
        });
        
        return {
          success: true,
          installationKey: updateKey,
          message: 'Update installation key generated successfully'
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
        clientId,
        macAddress,
        type: 'update',
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours for updates
        used: false
      });

      return {
        success: true,
        installationKey: updateKey,
        message: 'Update installation key generated successfully'
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
