const { DatabaseOperations } = require('../lib/database');

let dbOps = null;

async function getDbOps() {
  if (!dbOps) {
    dbOps = await new DatabaseOperations().init();
  }
  return dbOps;
}

// Simple authentication check
function isAuthorizedUser(email) {
  if (!process.env.AUTHORIZED_USERS) {
    return true; // If no users specified, allow all (for testing)
  }
  
  const authorizedEmails = process.env.AUTHORIZED_USERS.split(',').map(e => e.trim());
  return authorizedEmails.includes(email);
}

// CORS handler
function setCORSHeaders(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-User-Email');
}

// Main handler function
module.exports = async (req, res) => {
  setCORSHeaders(res);
  
  // Handle OPTIONS preflight request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const db = await getDbOps();
    const { action } = req.method === 'GET' ? req.query : req.body;
    
    // Test connection endpoint
    if (action === 'testConnection') {
      return res.json({
        success: true,
        message: 'API communication working',
        timestamp: new Date().toISOString()
      });
    }

    // Get version info (no auth required)
    if (action === 'get_version') {
      const result = await db.getVersionInfo();
      return res.json(result);
    }

    // Check if database is initialized (no auth required)
    if (action === 'isDatabaseInitialized') {
      const result = await db.isDatabaseInitialized();
      return res.json(result);
    }

    // Client-side operations (no auth required)
    const clientActions = [
      'registerClient', 'getClientNotifications', 'updateNotificationStatus',
      'requestWebsiteAccess', 'requestUninstall', 'checkUninstallApproval',
      'validateFolderKey', 'validateUninstallProtection', 'reportUnauthorizedDeletion'
    ];

    if (clientActions.includes(action)) {
      let result;
      
      switch (action) {
        case 'registerClient':
          const { clientId, clientName, computerName } = req.method === 'GET' ? req.query : req.body;
          result = await db.registerClient(clientId, clientName, computerName);
          break;
          
        case 'getClientNotifications':
          const clientIdForNotifs = req.method === 'GET' ? req.query.clientId : req.body.clientId;
          if (!await db.isClientAuthorized(clientIdForNotifs)) {
            result = { success: false, message: 'Client not authorized or not registered' };
          } else {
            result = await db.getClientNotifications(clientIdForNotifs);
          }
          break;
          
        case 'updateNotificationStatus':
          const { notificationId, status, snoozeMinutes } = req.method === 'GET' ? req.query : req.body;
          result = await db.updateNotificationStatus(notificationId, status, parseInt(snoozeMinutes) || 0);
          break;
          
        case 'requestWebsiteAccess':
          const { clientId: clientIdWebsite, url, reason } = req.method === 'GET' ? req.query : req.body;
          result = await db.requestWebsiteAccess(clientIdWebsite, url, reason || 'User requested access');
          break;
          
        case 'requestUninstall':
          const { clientId: clientIdUninstall, reason: uninstallReason, explanation } = req.method === 'GET' ? req.query : req.body;
          result = await db.requestUninstall(clientIdUninstall, uninstallReason, explanation);
          break;
          
        case 'checkUninstallApproval':
          const clientIdApproval = req.method === 'GET' ? req.query.clientId : req.body.clientId;
          result = await db.checkUninstallApproval(clientIdApproval);
          break;
          
        case 'validateFolderKey':
          const { clientId: clientIdKey, accessKey, operation } = req.method === 'GET' ? req.query : req.body;
          result = await db.validateFolderAccessKey(clientIdKey, accessKey, operation || 'uninstall');
          break;
          
        default:
          result = { success: false, message: 'Unknown client action: ' + action };
      }
      
      return res.json(result);
    }

    // Admin operations (require authentication - simplified for now)
    // In a real implementation, you'd want proper JWT or OAuth authentication
    const adminActions = [
      'initializeDatabase', 'getActiveNotifications', 'getCompletedNotifications',
      'getPresetMessages', 'sendNotificationToAllClients', 'getRegisteredClients',
      'getClientConnectionStatus', 'getWebsiteAccessRequests', 'reviewWebsiteAccessRequest',
      'getUninstallRequests', 'reviewUninstallRequest', 'clearAllNotifications',
      'uninstallAllClients', 'getCurrentUser'
    ];

    if (adminActions.includes(action)) {
      // For now, allow all admin actions (you should implement proper auth)
      let result;
      
      switch (action) {
        case 'initializeDatabase':
          result = await db.initializeDatabase();
          break;
          
        case 'getActiveNotifications':
          result = await db.getActiveNotifications();
          break;
          
        case 'getCompletedNotifications':
          result = await db.getCompletedNotifications();
          break;
          
        case 'getPresetMessages':
          result = await db.getPresetMessages();
          break;
          
        case 'sendNotificationToAllClients':
          const { 0: message, 1: allowBrowserUsage, 2: allowedWebsites, 3: priority } = 
            req.method === 'GET' ? [req.query.message, req.query.allowBrowserUsage, req.query.allowedWebsites, req.query.priority] :
            [req.body.message, req.body.allowBrowserUsage, req.body.allowedWebsites, req.body.priority];
          result = await db.sendNotificationToAllClients(message, allowBrowserUsage === 'true', allowedWebsites, parseInt(priority) || 1);
          break;
          
        case 'getClientConnectionStatus':
          result = await db.getClientConnectionStatus();
          break;
          
        case 'getWebsiteAccessRequests':
          result = await db.getWebsiteAccessRequests();
          break;
          
        case 'reviewWebsiteAccessRequest':
          const { 0: requestId, 1: actionType, 2: reviewerEmail } = 
            req.method === 'GET' ? [req.query.requestId, req.query.action, req.query.reviewerEmail] :
            [req.body.requestId, req.body.action, req.body.reviewerEmail];
          result = await db.reviewWebsiteAccessRequest(requestId, actionType, reviewerEmail || 'admin@example.com');
          break;
          
        case 'getUninstallRequests':
          result = await db.getUninstallRequests();
          break;
          
        case 'reviewUninstallRequest':
          const { 0: uninstallRequestId, 1: uninstallAction, 2: uninstallReviewerEmail, 3: denialReason } = 
            req.method === 'GET' ? [req.query.requestId, req.query.action, req.query.reviewerEmail, req.query.denialReason] :
            [req.body.requestId, req.body.action, req.body.reviewerEmail, req.body.denialReason];
          result = await db.reviewUninstallRequest(uninstallRequestId, uninstallAction, uninstallReviewerEmail || 'admin@example.com', denialReason || '');
          break;
          
        case 'clearAllNotifications':
          result = await db.clearAllNotifications();
          break;
          
        case 'uninstallAllClients':
          result = await db.uninstallAllClients();
          break;
          
        case 'getCurrentUser':
          result = { email: 'admin@example.com', isAuthorized: true };
          break;
          
        default:
          result = { success: false, message: 'Unknown admin action: ' + action };
      }
      
      return res.json(result);
    }

    // Unknown action
    res.status(400).json({ success: false, message: 'Unknown API action: ' + action });

  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'API Error: ' + error.message 
    });
  }
};
