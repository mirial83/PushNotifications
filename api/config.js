// Config endpoint for PushNotifications
export default function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle OPTIONS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const type = req.query.type;

  if (type === 'preset-messages') {
    // Return preset messages configuration
    const presetMessages = [
      {
        text: 'Do your schoolwork',
        description: 'Schoolwork time with educational websites allowed',
        allowBrowserUsage: true,
        allowedWebsites: [
          'drive.google.com',
          '*.aop.com', 
          '*.yourcloudlibrary.com',
          '*.gutenberg.org',
          'search.google.com',
          '*.codecademy.com'
        ]
      },
      {
        text: 'Clean your room',
        description: 'Time to clean up - no browser access needed',
        allowBrowserUsage: false,
        allowedWebsites: []
      },
      {
        text: 'Take out the trash',
        description: 'Quick chore - no browser access needed',
        allowBrowserUsage: false,
        allowedWebsites: []
      },
      {
        text: 'Walk the dog',
        description: 'Exercise time - no browser access needed',
        allowBrowserUsage: false,
        allowedWebsites: []
      },
      {
        text: 'Do the dishes',
        description: 'Kitchen cleanup - no browser access needed',
        allowBrowserUsage: false,
        allowedWebsites: []
      }
    ];

    return res.status(200).json({
      success: true,
      data: {
        presetMessages: presetMessages
      }
    });
  }

  return res.status(400).json({
    success: false,
    message: 'Invalid config type requested'
  });
}
