// Simple test endpoint for Node.js API
export default function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle OPTIONS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const response = {
    success: true,
    message: 'Node.js API is working correctly!',
    data: {
      node_version: process.version,
      platform: process.platform,
      timestamp: new Date().toISOString(),
      environment_check: {
        mongodb_connection_string: !!process.env.MONGODB_CONNECTION_STRING,
        mongodb_database: process.env.MONGODB_DATABASE || 'not_set'
      }
    }
  };

  return res.status(200).json(response);
}
