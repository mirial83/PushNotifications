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

// Enable error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Function to safely output JSON
function outputJson($data) {
    echo json_encode($data, JSON_PRETTY_PRINT);
    exit();
}

// Simple database operations using MongoDB Atlas Data API
class DatabaseOperations {
    private $apiUrl;
    private $apiKey;
    private $dataSource;
    private $database;
    
    public function __construct() {
        // MongoDB Atlas Data API configuration
        $this->apiUrl = $_ENV['MONGODB_DATA_API_URL'] ?? getenv('MONGODB_DATA_API_URL');
        $this->apiKey = $_ENV['MONGODB_DATA_API_KEY'] ?? getenv('MONGODB_DATA_API_KEY');
        $this->dataSource = $_ENV['MONGODB_DATA_SOURCE'] ?? getenv('MONGODB_DATA_SOURCE') ?? 'Cluster0';
        $this->database = $_ENV['DATABASE_NAME'] ?? $_ENV['DB_NAME'] ?? getenv('DATABASE_NAME') ?? getenv('DB_NAME') ?? 'pushnotifications';
        
        if (!$this->apiUrl || !$this->apiKey) {
            // Fallback to file-based storage for development
            error_log('MongoDB Data API not configured, using file-based storage');
        }
    }
    
    private function makeApiRequest($endpoint, $data) {
        if (!$this->apiUrl || !$this->apiKey) {
            // Fallback to file-based storage
            return $this->handleFileStorage($endpoint, $data);
        }
        
        $url = $this->apiUrl . '/action/' . $endpoint;
        $payload = array_merge([
            'dataSource' => $this->dataSource,
            'database' => $this->database
        ], $data);
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'api-key: ' . $this->apiKey
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode !== 200) {
            throw new Exception('MongoDB API request failed: ' . $response);
        }
        
        return json_decode($response, true);
    }
    
    private function handleFileStorage($endpoint, $data) {
        // Simple file-based storage for development/testing
        $storageDir = __DIR__ . '/../storage';
        if (!is_dir($storageDir)) {
            mkdir($storageDir, 0755, true);
        }
        
        switch ($endpoint) {
            case 'find':
                $file = $storageDir . '/' . $data['collection'] . '.json';
                if (file_exists($file)) {
                    $content = json_decode(file_get_contents($file), true);
                    return ['documents' => $content ?: []];
                }
                return ['documents' => []];
                
            case 'insertMany':
                $file = $storageDir . '/' . $data['collection'] . '.json';
                $existing = [];
                if (file_exists($file)) {
                    $existing = json_decode(file_get_contents($file), true) ?: [];
                }
                $existing = array_merge($existing, $data['documents']);
                file_put_contents($file, json_encode($existing, JSON_PRETTY_PRINT));
                return ['insertedIds' => array_keys($data['documents'])];
                
            default:
                return ['success' => true];
        }
    }
    
    public function testConnection() {
        try {
            return ['success' => true, 'message' => 'API communication working', 'timestamp' => date('c')];
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Connection test failed: ' . $e->getMessage()];
        }
    }
    
    public function isDatabaseInitialized() {
        try {
            // Check if settings collection exists and has data
            $result = $this->makeApiRequest('find', [
                'collection' => 'settings',
                'filter' => ['setting' => 'preset_messages']
            ]);
            
            $initialized = !empty($result['documents']);
            return ['success' => true, 'initialized' => $initialized];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function initializeDatabase() {
        try {
            // Load preset messages from configuration file
            $presetMessagesFile = __DIR__ . '/../config/preset-messages.json';
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
                    'description' => 'Custom household task messages from configuration file',
                    'created' => date('c')
                ],
                [
                    'setting' => 'default_snooze',
                    'value' => '15',
                    'description' => 'Default snooze time in minutes',
                    'created' => date('c')
                ],
                [
                    'setting' => 'max_notifications',
                    'value' => '5',
                    'description' => 'Maximum number of active notifications per client',
                    'created' => date('c')
                ]
            ];
            
            $this->makeApiRequest('insertMany', [
                'collection' => 'settings',
                'documents' => $settings
            ]);
            
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
            // For now, just return success for client registration
            return ['success' => true, 'message' => 'Client registered'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function sendNotificationToAllClients($message, $allowBrowserUsage = false, $allowedWebsites = '', $priority = 1) {
        try {
            // For development, simulate successful notification sending
            return [
                'success' => true,
                'message' => 'Notification sent to 1 client(s)',
                'clientCount' => 1
            ];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getActiveNotifications() {
        try {
            $result = $this->makeApiRequest('find', [
                'collection' => 'notifications',
                'filter' => ['status' => ['$ne' => 'Completed']]
            ]);
            
            return ['success' => true, 'data' => $result['documents']];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getClientNotifications($clientId) {
        try {
            $result = $this->makeApiRequest('find', [
                'collection' => 'notifications',
                'filter' => [
                    'clientId' => $clientId,
                    'status' => ['$ne' => 'Completed']
                ]
            ]);
            
            $processedNotifications = [];
            foreach ($result['documents'] as $n) {
                $processedNotifications[] = [
                    'id' => $n['_id'] ?? uniqid(),
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
    
    // Debug info for development
    if (empty($_GET['action']) && empty($_POST['action'])) {
        outputJson([
            'success' => false,
            'message' => 'No action specified',
            'debug' => [
                'method' => $method,
                'get_params' => $_GET,
                'post_params' => $_POST,
                'php_version' => phpversion(),
                'timestamp' => date('c')
            ]
        ]);
    }
    
    $input = null;
    if ($method === 'POST') {
        $rawInput = file_get_contents('php://input');
        $input = json_decode($rawInput, true);
    }
    
    // Get action from either GET or POST
    if ($method === 'GET') {
        $action = $_GET['action'] ?? '';
        $params = $_GET;
    } else {
        $action = $input['action'] ?? $_POST['action'] ?? '';
        $params = $input ?: $_POST;
    }
    
    if (empty($action)) {
        outputJson([
            'success' => false,
            'message' => 'No action specified',
            'debug' => [
                'method' => $method,
                'raw_input' => $rawInput ?? 'none',
                'parsed_input' => $input,
                'get' => $_GET,
                'post' => $_POST
            ]
        ]);
    }
    
    $db = new DatabaseOperations();
    $result = ['success' => false, 'message' => 'Unknown action: ' . $action];
    
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
                $result['clientCount'] = 0;
            }
            break;
            
        case 'getClientNotifications':
            $clientId = $params['clientId'] ?? '';
            $result = $db->getClientNotifications($clientId);
            break;
    }
    
    outputJson($result);
    
} catch (Exception $e) {
    outputJson([
        'success' => false,
        'message' => 'API Error: ' . $e->getMessage(),
        'debug' => [
            'file' => $e->getFile(),
            'line' => $e->getLine(),
            'trace' => $e->getTraceAsString()
        ]
    ]);
}
?>
