<?php
// Configuration API endpoint for PushNotifications

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle OPTIONS preflight request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Configuration files
$configFiles = [
    'preset-messages' => '../config/preset-messages.json',
    'app-settings' => '../config/app-settings.json'
];

try {
    $configType = $_GET['type'] ?? 'app-settings';
    
    if (!array_key_exists($configType, $configFiles)) {
        http_response_code(400);
        echo json_encode([
            'success' => false, 
            'message' => 'Invalid configuration type. Available types: ' . implode(', ', array_keys($configFiles))
        ]);
        exit();
    }
    
    $configFile = $configFiles[$configType];
    
    // Check if file exists
    if (!file_exists($configFile)) {
        http_response_code(404);
        echo json_encode([
            'success' => false, 
            'message' => 'Configuration file not found: ' . $configType
        ]);
        exit();
    }
    
    // Read and return the configuration
    $configContent = file_get_contents($configFile);
    $configData = json_decode($configContent, true);
    
    if ($configData === null) {
        http_response_code(500);
        echo json_encode([
            'success' => false, 
            'message' => 'Invalid JSON in configuration file: ' . $configType
        ]);
        exit();
    }
    
    echo json_encode([
        'success' => true,
        'type' => $configType,
        'data' => $configData,
        'timestamp' => date('c')
    ]);
    
} catch (Exception $e) {
    error_log('Configuration API error: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Configuration API error: ' . $e->getMessage()
    ]);
}
?>
