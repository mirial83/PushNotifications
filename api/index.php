<?php
// PushNotifications PHP API
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-User-Email');

// Handle OPTIONS preflight request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Database connection class
class DatabaseOperations {
    private $client;
    private $db;
    
    public function __construct() {
        $this->connect();
    }
    
    private function connect() {
        try {
            // MongoDB connection string from environment variable
            $mongoUri = $_ENV['MONGODB_URI'] ?? getenv('MONGODB_URI');
            $dbName = $_ENV['DATABASE_NAME'] ?? $_ENV['DB_NAME'] ?? getenv('DATABASE_NAME') ?? getenv('DB_NAME') ?? 'pushnotifications';
            
            if (!$mongoUri) {
                throw new Exception('MongoDB URI not found in environment variables');
            }
            
            // Use MongoDB PHP driver
            $this->client = new MongoDB\Client($mongoUri);
            $this->db = $this->client->selectDatabase($dbName);
            
        } catch (Exception $e) {
            error_log("Database connection error: " . $e->getMessage());
            throw $e;
        }
    }
    
    public function testConnection() {
        try {
            // Simple ping to test connection
            $this->db->command(['ping' => 1]);
            return ['success' => true, 'message' => 'API communication working', 'timestamp' => date('c')];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Database connection failed: ' . $e->getMessage()];
        }
    }
    
    public function isDatabaseInitialized() {
        try {
            $collections = $this->db->listCollections();
            $collectionNames = [];
            foreach ($collections as $collection) {
                $collectionNames[] = $collection->getName();
            }
            
            $requiredCollections = ['notifications', 'clients', 'settings'];
            $initialized = count(array_intersect($requiredCollections, $collectionNames)) === count($requiredCollections);
            
            return ['success' => true, 'initialized' => $initialized];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function initializeDatabase() {
        try {
            // Load preset messages from configuration file
            $presetMessagesFile = '../config/preset-messages.json';
            $presetMessages = [];
            
            if (file_exists($presetMessagesFile)) {
                $configContent = file_get_contents($presetMessagesFile);
                $configData = json_decode($configContent, true);
                if ($configData && isset($configData['presetMessages'])) {
                    $presetMessages = $configData['presetMessages'];
                }
            }
            
            // Initialize settings with default values
            $settings = [
                [
                    'setting' => 'preset_messages',
                    'value' => json_encode($presetMessages),
                    'description' => 'Custom household task messages from configuration file'
                ],
                [
                    'setting' => 'default_snooze',
                    'value' => '15',
                    'description' => 'Default snooze time in minutes'
                ],
                [
                    'setting' => 'max_notifications',
                    'value' => '5',
                    'description' => 'Maximum number of active notifications per client'
                ]
            ];
            
            $this->db->settings->insertMany($settings);
            
            return ['success' => true, 'message' => 'Database initialized successfully'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getVersionInfo() {
        try {
            return [
                'success' => true,
                'currentVersion' => $_ENV['CLIENT_VERSION'] ?? getenv('CLIENT_VERSION') ?? '2.1.0',
                'latestVersion' => $_ENV['CLIENT_VERSION'] ?? getenv('CLIENT_VERSION') ?? '2.1.0',
                'releaseNotes' => 'PHP/MongoDB/Vercel version with enhanced security',
                'updateAvailable' => false,
                'autoUpdateEnabled' => ($_ENV['AUTO_UPDATE_ENABLED'] ?? getenv('AUTO_UPDATE_ENABLED') ?? 'true') === 'true',
                'forceUpdate' => ($_ENV['FORCE_UPDATE'] ?? getenv('FORCE_UPDATE') ?? 'false') === 'true',
                'downloadUrl' => '/api/download.php?file=client',
                'timestamp' => date('c')
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'currentVersion' => '2.1.0',
                'latestVersion' => '2.1.0',
                'updateAvailable' => false,
                'error' => 'Failed to check for updates: ' . $e->getMessage()
            ];
        }
    }
    
    public function registerClient($clientId, $clientName, $computerName) {
        try {
            $now = new MongoDB\BSON\UTCDateTime();
            $result = $this->db->clients->updateOne(
                ['clientId' => $clientId],
                ['$set' => [
                    'clientId' => $clientId,
                    'clientName' => $clientName,
                    'computerName' => $computerName,
                    'lastSeen' => $now,
                    'status' => 'Online'
                ]],
                ['upsert' => true]
            );
            
            $message = $result->getUpsertedCount() > 0 ? 'Client registered' : 'Client updated';
            return ['success' => true, 'message' => $message];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function sendNotificationToAllClients($message, $allowBrowserUsage = false, $allowedWebsites = '', $priority = 1) {
        try {
            $clients = $this->db->clients->find()->toArray();
            
            if (count($clients) === 0) {
                return ['success' => true, 'message' => 'No clients registered', 'clientCount' => 0];
            }
            
            $now = new MongoDB\BSON\UTCDateTime();
            $notifications = [];
            
            foreach ($clients as $client) {
                $notifications[] = [
                    'id' => (string) new MongoDB\BSON\ObjectId(),
                    'clientId' => $client['clientId'],
                    'message' => $message,
                    'status' => 'Pending',
                    'created' => $now,
                    'updated' => $now,
                    'snoozeUntil' => null,
                    'allowBrowserUsage' => $allowBrowserUsage,
                    'allowedWebsites' => $allowedWebsites,
                    'priority' => $priority
                ];
            }
            
            $this->db->notifications->insertMany($notifications);
            
            return [
                'success' => true,
                'message' => 'Notification sent to ' . count($clients) . ' client(s)',
                'clientCount' => count($clients)
            ];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getActiveNotifications() {
        try {
            $notifications = $this->db->notifications->find(
                ['status' => ['$ne' => 'Completed']],
                ['sort' => ['priority' => -1, 'created' => 1]]
            )->toArray();
            
            return ['success' => true, 'data' => $notifications];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getClientNotifications($clientId) {
        try {
            $now = new MongoDB\BSON\UTCDateTime();
            $notifications = $this->db->notifications->find(
                [
                    'clientId' => $clientId,
                    'status' => ['$ne' => 'Completed'],
                    '$or' => [
                        ['snoozeUntil' => null],
                        ['snoozeUntil' => ['$lte' => $now]]
                    ]
                ],
                ['sort' => ['priority' => -1, 'created' => 1]]
            )->toArray();
            
            $processedNotifications = [];
            foreach ($notifications as $n) {
                $processedNotifications[] = [
                    'id' => $n['id'],
                    'message' => $n['message'],
                    'status' => $n['status'],
                    'allowBrowserUsage' => $n['allowBrowserUsage'] ?? false,
                    'allowedWebsites' => $n['allowedWebsites'] ? explode(',', $n['allowedWebsites']) : [],
                    'priority' => $n['priority'] ?? 1
                ];
            }
            
            return ['success' => true, 'data' => $processedNotifications];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
}

// Main API handler
try {
    $method = $_SERVER['REQUEST_METHOD'];
    $input = json_decode(file_get_contents('php://input'), true);
    
    // Get action from either GET or POST
    if ($method === 'GET') {
        $action = $_GET['action'] ?? '';
        $params = $_GET;
    } else {
        $action = $input['action'] ?? '';
        $params = $input;
    }
    
    $db = new DatabaseOperations();
    $result = ['success' => false, 'message' => 'Unknown action'];
    
    switch ($action) {
        case 'testConnection':
            $result = $db->testConnection();
            break;
            
        case 'get_version':
            $result = $db->getVersionInfo();
            break;
            
        case 'isDatabaseInitialized':
            $result = $db->isDatabaseInitialized();
            break;
            
        case 'initializeDatabase':
            $result = $db->initializeDatabase();
            break;
            
        case 'registerClient':
            $clientId = $params['clientId'] ?? '';
            $clientName = $params['clientName'] ?? '';
            $computerName = $params['computerName'] ?? '';
            $result = $db->registerClient($clientId, $clientName, $computerName);
            break;
            
        case 'sendNotificationToAllClients':
        case 'sendNotification':
            $message = $params['message'] ?? '';
            $allowBrowserUsage = ($params['allowBrowserUsage'] ?? 'false') === 'true';
            $allowedWebsites = $params['allowedWebsites'] ?? '';
            if (is_array($allowedWebsites)) {
                $allowedWebsites = implode(',', array_filter($allowedWebsites));
            }
            $priority = (int)($params['priority'] ?? 1);
            $result = $db->sendNotificationToAllClients($message, $allowBrowserUsage, $allowedWebsites, $priority);
            break;
            
        case 'getActiveNotifications':
        case 'getNotifications':
            $result = $db->getActiveNotifications();
            if ($result['success']) {
                $result['notifications'] = $result['data'];
                $result['clientCount'] = 0; // Could implement client counting
            }
            break;
            
        case 'getClientNotifications':
            $clientId = $params['clientId'] ?? '';
            $result = $db->getClientNotifications($clientId);
            break;
            
        default:
            $result = ['success' => false, 'message' => 'Unknown API action: ' . $action];
    }
    
    echo json_encode($result);
    
} catch (Exception $e) {
    error_log('API Error: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'API Error: ' . $e->getMessage()
    ]);
}
?>
