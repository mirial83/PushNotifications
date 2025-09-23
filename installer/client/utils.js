// Version Utilities (from installer.py parse_version, compare_versions)
parseVersion(versionString) // Parse "1.8.4" into comparable tuple
compareVersions(current, latest) // Returns 1, 0, -1 for newer, same, older
isNewerVersion(current, latest) // Boolean version comparison
normalizeVersionString(version) // Clean and standardize version format

// Logging and Error Handling (from installer.py log_exception, logger)
setupLogger(logLevel) // Initialize logging system
logError(message, error, stackTrace) // Log errors with full details
logWarning(message, details) // Log warning messages
logInfo(message, context) // Log informational messages
logDebug(message, debugData) // Log debug information
formatLogMessage(level, message, timestamp) // Format log entries
rotateLogs(maxSize, keepCount) // Manage log file size and rotation

// Inter-Process Communication (from installer.py MessageRelay class)
createMessageRelay(filePath) // Set up IPC between processes
sendMessage(data) // Send message via IPC
receiveMessage() // Receive message via IPC
sendStatusUpdate(status, progress) // Send status with progress
sendErrorMessage(error) // Send error notification
cleanupMessageRelay() // Clean up IPC resources

// System Information (from installer.py system detection)
getOperatingSystem() // Detect OS version and type
getSystemArchitecture() // Get CPU architecture (x64, x86)
getMachineIdentifier() // Get unique machine ID
getNetworkInterfaces() // Get network adapter information
isAdministrator() // Check if running with admin privileges
getCurrentUser() // Get current username

// File and Path Utilities
ensureDirectoryExists(path) // Create directory if it doesn't exist
copyFile(source, destination) // Copy files with error handling
deleteFile(filePath) // Delete files safely
getFileSize(filePath) // Get file size in bytes
getFileModificationTime(filePath) // Get file last modified date
isFileReadable(filePath) // Check file read permissions
isFileWritable(filePath) // Check file write permissions

// Network Utilities (from installer.py network detection)
isInternetConnected() // Check internet connectivity
pingServer(hostname) // Test server connectivity
getPublicIPAddress() // Get external IP address
detectProxySettings() // Detect system proxy configuration
detectVPNConnection() // Check if VPN is active

// Process Management (from installer.py process handling)
findProcessByName(processName) // Find running processes
killProcess(processId) // Terminate specific process
isProcessRunning(processName) // Check if process is active
getProcessList() // Get all running processes
preventProcessTermination(processId) // Protect process from termination

// Retry Logic (from installer.py _make_api_request retry logic)
retryWithBackoff(func, maxRetries, baseDelay) // Exponential backoff retry
calculateRetryDelay(attempt, baseDelay) // Calculate delay for retry attempt
shouldRetryError(error) // Determine if error is retryable
executeWithTimeout(func, timeoutMs) // Execute function with timeout