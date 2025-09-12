<?php
// Simple MongoDB integration for PushNotifications
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-User-Email');

// Handle OPTIONS preflight request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Simple storage class using /tmp directory (writable on Vercel)
class SimpleStorage {
    private $dataFile;
    
    public function __construct() {
        $this->dataFile = '/tmp/pushnotifications_data.json';
        $this->initializeStorage();
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
    
    public function isDatabaseInitialized() {
        $data = $this->getData();
        return !empty($data['settings']);
    }
    
    public function initializeDatabase() {
        $this->initializeStorage();
        return ['success' => true, 'message' => 'Database initialized successfully'];
    }
    
    public function getActiveNotifications() {
        $data = $this->getData();
        $activeNotifications = array_filter($data['notifications'], function($n) {
            return ($n['status'] ?? '') !== 'Completed';
        });
        return ['success' => true, 'data' => array_values($activeNotifications)];
    }
    
    public function addNotification($message, $clientId = 'all') {
        $data = $this->getData();
        $notification = [
            'id' => uniqid(),
            'message' => $message,
            'clientId' => $clientId,
            'status' => 'Active',
            'created' => date('c'),
            'priority' => 1
        ];
        $data['notifications'][] = $notification;
        $this->saveData($data);
        return ['success' => true, 'message' => 'Notification added'];
    }
    
    public function testConnection() {
        return [
            'success' => true, 
            'message' => 'Simple storage working',
            'storage_file' => $this->dataFile,
            'writable' => is_writable(dirname($this->dataFile)),
            'timestamp' => date('c')
        ];
    }
}

// Handle requests
try {
    $method = $_SERVER['REQUEST_METHOD'];
    $storage = new SimpleStorage();
    
    // Get action
    $action = '';
    if ($method === 'GET') {
        $action = $_GET['action'] ?? '';
    } else {
        $rawInput = file_get_contents('php://input');
        if (!empty($rawInput)) {
            $input = json_decode($rawInput, true);
            $action = $input['action'] ?? '';
        }
    }
    
    $result = ['success' => false, 'message' => 'Unknown action: ' . $action];
    
    switch ($action) {
        case 'testConnection':
            $result = $storage->testConnection();
            break;
            
        case 'isDatabaseInitialized':
            $initialized = $storage->isDatabaseInitialized();
            $result = ['success' => true, 'initialized' => $initialized];
            break;
            
        case 'initializeDatabase':
            $result = $storage->initializeDatabase();
            break;
            
        case 'getActiveNotifications':
        case 'getNotifications':
            $result = $storage->getActiveNotifications();
            if ($result['success']) {
                $result['notifications'] = $result['data'];
                $result['clientCount'] = 1;
            }
            break;
            
        default:
            if (empty($action)) {
                $result = [
                    'success' => false,
                    'message' => 'No action specified',
                    'available_actions' => ['testConnection', 'isDatabaseInitialized', 'initializeDatabase', 'getActiveNotifications'],
                    'method' => $method,
                    'timestamp' => date('c')
                ];
            }
            break;
    }
    
    echo json_encode($result, JSON_PRETTY_PRINT);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'message' => 'Error: ' . $e->getMessage(),
        'timestamp' => date('c')
    ], JSON_PRETTY_PRINT);
}
?>
