<?php
// Simple test endpoint
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle OPTIONS preflight request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

echo json_encode([
    'success' => true,
    'message' => 'PHP is working on Vercel!',
    'timestamp' => date('c'),
    'php_version' => phpversion(),
    'request_method' => $_SERVER['REQUEST_METHOD'],
    'request_uri' => $_SERVER['REQUEST_URI'] ?? 'unknown',
    'environment_check' => [
        'curl_enabled' => extension_loaded('curl'),
        'json_enabled' => extension_loaded('json'),
        'mongodb_api_url_set' => !empty($_ENV['MONGODB_DATA_API_URL'] ?? getenv('MONGODB_DATA_API_URL')),
        'mongodb_api_key_set' => !empty($_ENV['MONGODB_DATA_API_KEY'] ?? getenv('MONGODB_DATA_API_KEY')),
        'server_software' => $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown'
    ]
], JSON_PRETTY_PRINT);
?>
