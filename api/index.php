<?php
// PushNotifications PHP API - Clean Implementation
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

// Database operations using MongoDB Data API
class DatabaseOperations {
    private $apiUrl;
    private $apiKey;
    private $dataSource;
    private $database;
    private $dataFile; // Fallback storage
    
    public function __construct() {
        // MongoDB Data API configuration (preferred method)
        $this->apiUrl = $_ENV['MONGODB_DATA_API_URL'] ?? getenv('MONGODB_DATA_API_URL');
        $this->apiKey = $_ENV['MONGODB_DATA_API_KEY'] ?? getenv('MONGODB_DATA_API_KEY');
        $this->dataSource = $_ENV['MONGODB_DATA_SOURCE'] ?? getenv('MONGODB_DATA_SOURCE') ?? 'pushnotifications';
        $this->database = $_ENV['DATABASE_NAME'] ?? getenv('DATABASE_NAME') ?? 'pushnotifications';
        
        // Alternative: Direct MongoDB connection (simpler setup)
        $this->connectionString = $_ENV['MONGODB_CONNECTION_STRING'] ?? getenv('MONGODB_CONNECTION_STRING');
        $this->mongoDatabase = $_ENV['MONGODB_DATABASE'] ?? getenv('MONGODB_DATABASE') ?? 'pushnotifications';
        
        // Fallback to simple storage if neither MongoDB option is configured
        $this->dataFile = '/tmp/pushnotifications_data.json';
        if (!$this->apiUrl && !$this->connectionString) {
            $this->initializeStorage();
        }
    }
    
    private function initializeStorage() {
        if (!file_exists($this->dataFile)) {
            $initialData = [
                'settings' => [
                    [
                        'setting' => 'preset_messages',
                        'value' => json_encode([
                            'Do your schoolwork',
                            'Clean your room', 
                            'Take out the trash',
                            'Walk the dog',
                            'Do the dishes'
                        ]),
                        'description' => 'Preset notification messages',
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
                ],
                'notifications' => [],
                'clients' => []
            ];
            file_put_contents($this->dataFile, json_encode($initialData));
        }
    }
    
    private function getData() {
        if (file_exists($this->dataFile)) {
            $content = file_get_contents($this->dataFile);
            return json_decode($content, true) ?: ['settings' => [], 'notifications' => [], 'clients' => []];
        }
        return ['settings' => [], 'notifications' => [], 'clients' => []];
    }
    
    private function saveData($data) {
        return file_put_contents($this->dataFile, json_encode($data));
    }
    
    private function makeApiRequest($endpoint, $data) {
        if (!$this->apiUrl || !$this->apiKey) {
            throw new Exception('MongoDB Data API not configured - using fallback storage');
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
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlError = curl_error($ch);
        curl_close($ch);
        
        if ($curlError) {
            throw new Exception('cURL Error: ' . $curlError);
        }
        
        if ($httpCode !== 200) {
            throw new Exception('MongoDB API request failed (HTTP ' . $httpCode . '): ' . $response);
        }
        
        $decoded = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('Invalid JSON response from MongoDB API: ' . json_last_error_msg());
        }
        
        return $decoded;
    }
    
    public function testConnection() {
        try {
            $result = [
                'success' => true,
                'timestamp' => date('c'),
                'mongodb_configured' => ($this->apiUrl && $this->apiKey),
                'fallback_storage' => [
                    'path' => $this->dataFile,
                    'writable' => is_writable(dirname($this->dataFile))
                ]
            ];
            
            if ($this->apiUrl && $this->apiKey) {
                // Test MongoDB Data API
                try {
                    $testResult = $this->makeApiRequest('find', [
                        'collection' => 'test',
                        'filter' => {},
                        'limit' => 1
                    ]);
                    $result['message'] = 'MongoDB Data API connection successful';
                    $result['mongodb_status'] = 'connected';
                    $result['api_url'] = $this->apiUrl;
                } catch (Exception $e) {
                    $result['message'] = 'MongoDB connection failed, using fallback storage';
                    $result['mongodb_status'] = 'failed';
                    $result['mongodb_error'] = $e->getMessage();
                }
            } else {
                $result['message'] = 'Using fallback storage - MongoDB not configured';
                $result['mongodb_status'] = 'not_configured';
                $result['required_env_vars'] = [
                    'MONGODB_DATA_API_URL' => 'https://data.mongodb-api.com/app/YOUR-APP-ID/endpoint/data/v1',
                    'MONGODB_DATA_API_KEY' => 'your-api-key'
                ];
            }
            
            return $result;
        } catch (Exception $e) {
            return ['success' => false, 'message' => 'Connection test failed: ' . $e->getMessage()];
        }
    }
    
    public function isDatabaseInitialized() {
        try {
            $data = $this->getData();
            $initialized = !empty($data['settings']);
            return ['success' => true, 'initialized' => $initialized];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function initializeDatabase() {
        try {
            $this->initializeStorage();
            return ['success' => true, 'message' => 'Database initialized successfully'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getVersionInfo() {
        try {
            return [
                'success' => true,
                'currentVersion' => '2.1.0',
                'latestVersion' => '2.1.0',
                'releaseNotes' => 'PHP/Simple Storage/Vercel version',
                'updateAvailable' => false,
                'autoUpdateEnabled' => true,
                'forceUpdate' => false,
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
            $data = $this->getData();
            $client = [
                'clientId' => $clientId,
                'clientName' => $clientName,
                'computerName' => $computerName,
                'registered' => date('c'),
                'lastSeen' => date('c')
            ];
            $data['clients'][] = $client;
            $this->saveData($data);
            return ['success' => true, 'message' => 'Client registered'];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function sendNotificationToAllClients($message, $allowBrowserUsage = false, $allowedWebsites = '', $priority = 1) {
        try {
            $data = $this->getData();
            $notification = [
                'id' => uniqid(),
                'message' => $message,
                'clientId' => 'all',
                'status' => 'Active',
                'allowBrowserUsage' => $allowBrowserUsage,
                'allowedWebsites' => $allowedWebsites,
                'priority' => $priority,
                'created' => date('c')
            ];
            $data['notifications'][] = $notification;
            $this->saveData($data);
            
            return [
                'success' => true,
                'message' => 'Notification sent to all clients',
                'clientCount' => count($data['clients'])
            ];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getActiveNotifications() {
        try {
            $data = $this->getData();
            $activeNotifications = array_filter($data['notifications'], function($n) {
                return ($n['status'] ?? '') !== 'Completed';
            });
            return ['success' => true, 'data' => array_values($activeNotifications)];
        } catch (Exception $e) {
            return ['success' => false, 'message' => $e->getMessage()];
        }
    }
    
    public function getClientNotifications($clientId) {
        try {
            $data = $this->getData();
            $notifications = array_filter($data['notifications'], function($n) use ($clientId) {
                return (($n['clientId'] ?? '') === $clientId || ($n['clientId'] ?? '') === 'all') 
                       && ($n['status'] ?? '') !== 'Completed';
            });
            
            $processedNotifications = [];
            foreach ($notifications as $n) {
                $processedNotifications[] = [
                    'id' => $n['id'] ?? uniqid(),
                    'message' => $n['message'],
                    'status' => $n['status'],
                    'allowBrowserUsage' => $n['allowBrowserUsage'] ?? false,
                    'allowedWebsites' => isset($n['allowedWebsites']) ? explode(',', $n['allowedWebsites']) : [],
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
    
    $input = null;
    $rawInput = '';
    
    if ($method === 'POST') {
        $rawInput = file_get_contents('php://input');
        if (!empty($rawInput)) {
            $input = json_decode($rawInput, true);
        }
    }
    
    // Get action from either GET or POST
    if ($method === 'GET') {
        $action = $_GET['action'] ?? '';
        $params = $_GET;
    } else {
        // For POST, prioritize JSON body over form data
        $action = '';
        $params = [];
        
        if ($input && is_array($input)) {
            $action = $input['action'] ?? '';
            $params = $input;
        } elseif (!empty($_POST)) {
            $action = $_POST['action'] ?? '';
            $params = $_POST;
        }
    }
    
    // Debug info if no action found
    if (empty($action)) {
        outputJson([
            'success' => false,
            'message' => 'No action specified',
            'available_actions' => [
                'testConnection', 
                'isDatabaseInitialized', 
                'initializeDatabase', 
                'getActiveNotifications',
                'registerClient',
                'sendNotificationToAllClients',
                'get_version'
            ],
            'debug' => [
                'method' => $method,
                'raw_input' => $rawInput,
                'parsed_input' => $input,
                'json_error' => json_last_error_msg(),
                'get_params' => $_GET,
                'post_params' => $_POST,
                'content_type' => $_SERVER['CONTENT_TYPE'] ?? 'none',
                'php_version' => phpversion(),
                'timestamp' => date('c')
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
