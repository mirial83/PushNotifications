// Config endpoint for PushNotifications
const { MongoClient } = require('mongodb');

// Fallback storage for when database is unavailable
const fallbackStorage = {
  customMessages: []
};

// Database connection setup
let client;
let db;

async function connectToDatabase() {
  if (db) return db;
  
  try {
    const connectionString = process.env.MONGODB_URI;
    if (!connectionString) {
      throw new Error('MONGODB_URI environment variable is not set');
    }
    
    client = new MongoClient(connectionString);
    await client.connect();
    db = client.db('pushnotifications');
    return db;
  } catch (error) {
    console.error('Database connection error:', error);
    throw error;
  }
}

// Function to handle cleanup of old data with different timeouts
async function handleCleanupOldData(req, res) {
  try {
    const database = await connectToDatabase();
    
    // Calculate cutoff dates
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    const fortyEightHoursAgo = new Date();
    fortyEightHoursAgo.setHours(fortyEightHoursAgo.getHours() - 48);
    
    let totalDeleted = 0;
    const deletionResults = {};
    const incompleteNotifications = [];
    
    // First, find active notifications that will be deleted to create banners
    try {
      const activeNotificationsCollection = database.collection('activeNotifications');
      const expiredActiveNotifications = await activeNotificationsCollection.find({
        timestamp: { $lt: fortyEightHoursAgo },
        status: { $nin: ['completed', 'acknowledged'] },
        type: { $nin: ['uninstall_request', 'app_deletion', 'app_delete'] }
      }).toArray();
      
      // Store information about incomplete notifications for banner display
      for (const notification of expiredActiveNotifications) {
        incompleteNotifications.push({
          _id: notification._id,
          message: notification.message,
          clientId: notification.clientId,
          timestamp: notification.timestamp,
          removedAt: new Date(),
          reason: 'Incomplete after 48 hours'
        });
      }
      
      // Save incomplete notification records for banner display
      if (incompleteNotifications.length > 0) {
        const incompleteNotificationsCollection = database.collection('incompleteNotifications');
        await incompleteNotificationsCollection.insertMany(incompleteNotifications);
      }
    } catch (error) {
      console.error('Error processing incomplete notifications:', error);
    }
    
    // Collections to clean up with their specific criteria
    const collectionsToClean = [
      {
        name: 'notifications',
        description: 'regular notifications',
        cutoffDate: sevenDaysAgo,
        query: {
          timestamp: { $lt: sevenDaysAgo },
          // Exclude app deletion/uninstall requests
          type: { $nin: ['uninstall_request', 'app_deletion', 'app_delete'] }
        }
      },
      {
        name: 'websiteRequests',
        description: 'website access requests',
        cutoffDate: sevenDaysAgo,
        query: {
          timestamp: { $lt: sevenDaysAgo }
        }
      },
      {
        name: 'activeNotifications',
        description: 'active notifications',
        cutoffDate: fortyEightHoursAgo,
        query: {
          timestamp: { $lt: fortyEightHoursAgo },
          // Exclude app deletion/uninstall requests
          type: { $nin: ['uninstall_request', 'app_deletion', 'app_delete'] }
        }
      }
    ];
    
    // Clean each collection
    for (const collectionInfo of collectionsToClean) {
      try {
        const collection = database.collection(collectionInfo.name);
        const deleteResult = await collection.deleteMany(collectionInfo.query);
        
        deletionResults[collectionInfo.name] = {
          deleted: deleteResult.deletedCount,
          description: collectionInfo.description,
          cutoffHours: collectionInfo.name === 'activeNotifications' ? 48 : 168 // 48 hours or 7 days
        };
        
        totalDeleted += deleteResult.deletedCount;
        
        console.log(`Cleaned ${deleteResult.deletedCount} old ${collectionInfo.description} from ${collectionInfo.name}`);
      } catch (error) {
        console.error(`Error cleaning ${collectionInfo.name}:`, error);
        deletionResults[collectionInfo.name] = {
          deleted: 0,
          error: error.message,
          description: collectionInfo.description
        };
      }
    }
    
    return res.status(200).json({
      success: true,
      message: `Cleanup completed. Removed ${totalDeleted} old records, ${incompleteNotifications.length} incomplete notifications moved to banner display.`,
      data: {
        totalDeleted,
        incompleteNotificationsFound: incompleteNotifications.length,
        activeNotificationsCutoff: fortyEightHoursAgo.toISOString(),
        generalCutoff: sevenDaysAgo.toISOString(),
        results: deletionResults,
        incompleteNotifications: incompleteNotifications.map(n => ({
          message: n.message,
          clientId: n.clientId,
          timestamp: n.timestamp
        })),
        preserved: [
          'Encryption keys (all preserved)',
          'App deletion/uninstall requests (all preserved)',
          'Custom messages (all preserved)',
          'Recent data (within timeouts)',
          'Completed/acknowledged notifications'
        ]
      }
    });
    
  } catch (error) {
    console.error('Error during cleanup:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to cleanup old data',
      error: error.message
    });
  }
}

// Function to get incomplete notifications for banner display
async function handleGetIncompleteNotifications(req, res) {
  try {
    const database = await connectToDatabase();
    const incompleteNotificationsCollection = database.collection('incompleteNotifications');
    
    // Get incomplete notifications from last 7 days (for banner display)
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    const incompleteNotifications = await incompleteNotificationsCollection.find({
      removedAt: { $gte: sevenDaysAgo }
    }).sort({ removedAt: -1 }).toArray();
    
    return res.status(200).json({
      success: true,
      data: {
        incompleteNotifications: incompleteNotifications
      }
    });
  } catch (error) {
    console.error('Error fetching incomplete notifications:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to fetch incomplete notifications'
    });
  }
}

// Function to dismiss incomplete notification banner
async function handleDismissIncompleteNotification(req, res) {
  try {
    const { notificationId } = req.body;
    
    if (!notificationId) {
      return res.status(400).json({
        success: false,
        message: 'Notification ID is required'
      });
    }
    
    const database = await connectToDatabase();
    const incompleteNotificationsCollection = database.collection('incompleteNotifications');
    
    const result = await incompleteNotificationsCollection.deleteOne({
      _id: new database.constructor.ObjectId ? new database.constructor.ObjectId(notificationId) : notificationId
    });
    
    return res.status(200).json({
      success: true,
      message: 'Incomplete notification banner dismissed',
      deleted: result.deletedCount > 0
    });
  } catch (error) {
    console.error('Error dismissing incomplete notification:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to dismiss incomplete notification'
    });
  }
}

// Function to handle saving custom messages
async function handleSaveCustomMessage(req, res) {
  try {
    const { text, description, allowBrowserUsage, allowedWebsites } = req.body;
    
    // Validate required fields
    if (!text || text.trim().length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Message text is required'
      });
    }
    
    const database = await connectToDatabase();
    const customMessagesCollection = database.collection('customMessages');
    
    // Check if a message with the same text already exists
    const existingMessage = await customMessagesCollection.findOne({ text: text.trim() });
    if (existingMessage) {
      return res.status(400).json({
        success: false,
        message: 'A message with this text already exists'
      });
    }
    
    // Prepare the message data
    const messageData = {
      text: text.trim(),
      description: description?.trim() || 'Custom message',
      allowBrowserUsage: Boolean(allowBrowserUsage),
      allowedWebsites: Array.isArray(allowedWebsites) ? allowedWebsites : [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    // Insert the new custom message
    const result = await customMessagesCollection.insertOne(messageData);
    
    return res.status(201).json({
      success: true,
      message: 'Custom message saved successfully',
      data: {
        _id: result.insertedId.toString(),
        ...messageData
      }
    });
    
  } catch (error) {
    console.error('Error saving custom message:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to save custom message'
    });
  }
}

module.exports = async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle OPTIONS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const type = req.query.type;
  
  try {
    // Handle POST requests
    if (req.method === 'POST') {
      switch (req.body?.action) {
        case 'saveCustomMessage':
          return await handleSaveCustomMessage(req, res);
        case 'cleanupOldData':
          return await handleCleanupOldData(req, res);
        case 'dismissIncompleteNotification':
          return await handleDismissIncompleteNotification(req, res);
        default:
          // Continue to GET handlers below
          break;
      }
    }
    
    // Handle GET requests
    if (req.method === 'GET') {
      if (type === 'incomplete-notifications') {
        return await handleGetIncompleteNotifications(req, res);
      }
    }

    if (type === 'preset-messages') {
    // Return preset messages configuration (built-in + custom)
    const builtInMessages = [
      {
        text: 'Do your schoolwork',
        description: 'Schoolwork time with educational websites allowed',
        allowBrowserUsage: true,
        isBuiltIn: true,
        allowedWebsites: [
          // Google Workspace - Full Suite
          'drive.google.com',
          'docs.google.com',
          'sheets.google.com',
          'slides.google.com',
          'forms.google.com',
          'calendar.google.com',
          'mail.google.com',
          'classroom.google.com',
          'scholar.google.com',
          'books.google.com',
          'translate.google.com',
          'search.google.com',
          'accounts.google.com',
          
          // Educational Resources
          '*.aop.com', 
          '*.yourcloudlibrary.com',
          '*.gutenberg.org',
          '*.codecademy.com',
          '*.wikipedia.org',
          
          // Communication & Collaboration
          '*.discord.com',
          
          // Reference & Research
          'britannica.com',
          'merriam-webster.com',
          'dictionary.com',
          'thesaurus.com'
        ],
        websiteButtons: [
          {
            name: 'Google Suite',
            websites: [
              'drive.google.com',
              'docs.google.com',
              'sheets.google.com',
              'slides.google.com',
              'forms.google.com',
              'calendar.google.com',
              'mail.google.com',
              'classroom.google.com',
              'scholar.google.com',
              'books.google.com',
              'translate.google.com',
              'search.google.com',
              'accounts.google.com'
            ]
          },
          {
            name: 'Monarch',
            websites: ['*.aop.com']
          },
          {
            name: 'Cambria Library',
            websites: ['*.yourcloudlibrary.com']
          },
          {
            name: 'Gutenberg Library',
            websites: ['*.gutenberg.org']
          },
          {
            name: 'CodeCademy',
            websites: ['*.codecademy.com']
          },
          {
            name: 'Wikipedia',
            websites: ['*.wikipedia.org']
          },
          {
            name: 'Discord',
            websites: ['*.discord.com']
          },
          {
            name: 'Encyclopedia Britannica',
            websites: ['britannica.com']
          },
          {
            name: 'Mirriam-Webster Dictionary',
            websites: ['merriam-webster.com']
          },
          {
            name: 'Dictionary',
            websites: ['dictionary.com']
          },
          {
            name: 'Thesaurus',
            websites: ['thesaurus.com']
          }
        ]
      },
      {
        text: 'Clean your room',
        description: 'Time to clean up - no browser access needed',
        allowBrowserUsage: false,
        isBuiltIn: true,
        allowedWebsites: []
      },
      {
        text: 'Take out the trash',
        description: 'Quick chore - no browser access needed',
        allowBrowserUsage: false,
        isBuiltIn: true,
        allowedWebsites: []
      },
      {
        text: 'Walk the dog',
        description: 'Exercise time - no browser access needed',
        allowBrowserUsage: false,
        isBuiltIn: true,
        allowedWebsites: []
      },
      {
        text: 'Do the dishes',
        description: 'Kitchen cleanup - no browser access needed',
        allowBrowserUsage: false,
        isBuiltIn: true,
        allowedWebsites: []
      }
    ];
    
    // Load custom messages from database or fallback storage
    let customMessages = [];
    try {
      const database = await connectToDatabase();
      const customMessagesCollection = database.collection('customMessages');
      const customMessagesData = await customMessagesCollection.find({}).toArray();
      customMessages = customMessagesData.map(msg => ({
        ...msg,
        isBuiltIn: false,
        _id: msg._id.toString() // Convert ObjectId to string
      }));
    } catch (error) {
      console.error('Error loading custom messages from database:', error);
      // Use fallback storage if database fails
      customMessages = fallbackStorage.customMessages.map(msg => ({
        ...msg,
        isBuiltIn: false,
        _id: msg.id || msg._id // Use id for fallback messages
      }));
    }
    
    // Combine built-in and custom messages
    const allMessages = [...builtInMessages, ...customMessages];

    return res.status(200).json({
      success: true,
      data: {
        presetMessages: allMessages
      }
    });
    }

    return res.status(400).json({
      success: false,
      message: 'Invalid config type requested'
    });
    
  } catch (error) {
    console.error('Error in config handler:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
}
