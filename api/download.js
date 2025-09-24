// Download API endpoint for PushNotifications
const fs = require('fs');
const path = require('path');
const { MongoClient } = require('mongodb');

// Database configuration
const MONGODB_CONNECTION_STRING = process.env.MONGODB_CONNECTION_STRING;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || 'pushnotifications';

class DownloadHandler {
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

  async close() {
    if (this.client) {
      await this.client.close();
      this.client = null;
      this.db = null;
    }
  }

  async getCurrentVersionInfo() {
    try {
      if (this.usesFallback) {
        return {
          versionNumber: 1,
          version: '1.1.9',
          message: 'Fallback version - MongoDB not configured'
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
            versionNumber: latestVersion.versionNumber,
            version: latestVersion.version,
            message: latestVersion.message || 'Latest deployment'
          };
        }
        
        // No versions found, return default
        return {
          versionNumber: 1,
          version: '1.0.0',
          message: 'No deployment history found'
        };
      }
      
      return {
        versionNumber: currentVersion.versionNumber,
        version: currentVersion.version,
        message: currentVersion.message || 'Latest deployment'
      };
    } catch (error) {
      console.error('Error getting version info:', error);
      return {
        versionNumber: 1,
        version: '1.0.0',
        message: 'Error retrieving version info'
      };
    }
  }

  async serveInstallerFile(res) {
    try {
      // Get current version info from database
      const versionInfo = await this.getCurrentVersionInfo();
      
      // Read the installer.py file
      const installerPath = path.join(process.cwd(), 'installer.py');
      
      if (!fs.existsSync(installerPath)) {
        return res.status(404).json({
          success: false,
          message: 'Installer file not found'
        });
      }

      let installerContent = fs.readFileSync(installerPath, 'utf8');
      
      // Replace the hardcoded version with the current version from database
      // Look for the version in the docstring and CLIENT_CONFIG
      installerContent = installerContent.replace(
        /Version: \d+\.\d+\.\d+/g,
        `Version: ${versionInfo.version}`
      );
      
      // Replace INSTALLER_VERSION variable
      installerContent = installerContent.replace(
        /INSTALLER_VERSION\s*=\s*'[^']*'/g,
        `INSTALLER_VERSION = '${versionInfo.version}'`
      );
      
      // Replace in CLIENT_CONFIG (if it exists)
      installerContent = installerContent.replace(
        /'client_version': '\d+\.\d+\.\d+'/g,
        `'client_version': '${versionInfo.version}'`
      );
      
      // Also replace in the README version field
      installerContent = installerContent.replace(
        /- Client Version: \d+\.\d+\.\d+/g,
        `- Client Version: ${versionInfo.version}`
      );

      // Replace VERSION_NUMBER if it exists
      if (installerContent.match(/VERSION_NUMBER\s*=\s*\d+/)) {
        installerContent = installerContent.replace(/VERSION_NUMBER\s*=\s*\d+/, `VERSION_NUMBER = ${versionInfo.versionNumber}`);
      }

      // Add a comment header with version metadata
      const versionHeader = `#!/usr/bin/env python3
# PushNotifications Client Installer
# Downloaded Version: ${versionInfo.version}
# Version Number: ${versionInfo.versionNumber}
# Download Date: ${new Date().toISOString()}
# ${versionInfo.message}

`;

      // Remove the existing shebang and add our header
      installerContent = installerContent.replace(/^#!\/usr\/bin\/env python3\r?\n/, '');
      installerContent = versionHeader + installerContent;

      // Set appropriate headers for file download
      res.setHeader('Content-Type', 'application/octet-stream');
      res.setHeader('Content-Disposition', 'attachment; filename="installer.py"');
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
      
      // Add custom headers with version info
      res.setHeader('X-Client-Version', versionInfo.version);
      res.setHeader('X-Version-Number', versionInfo.versionNumber.toString());

      return res.status(200).send(installerContent);
      
    } catch (error) {
      console.error('Error serving installer file:', error);
      return res.status(500).json({
        success: false,
        message: 'Error serving installer file: ' + error.message
      });
    }
  }

  async serveFile(fileType, res) {
    switch (fileType) {
      case 'client':
      case 'installer':
        return await this.serveInstallerFile(res);
      
      default:
        return res.status(400).json({
          success: false,
          message: 'Unknown file type requested'
        });
    }
  }
}

module.exports = async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Handle OPTIONS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Only allow GET requests for downloads
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      message: 'Method not allowed'
    });
  }

  const { file } = req.query;
  
  if (!file) {
    return res.status(400).json({
      success: false,
      message: 'File parameter is required'
    });
  }

  const downloadHandler = new DownloadHandler();
  
  try {
    await downloadHandler.serveFile(file, res);
  } finally {
    await downloadHandler.close();
  }
}