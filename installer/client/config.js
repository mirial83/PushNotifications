// Configuration Loading (from installer.py _load_config)
loadClientConfiguration() // Load from registry/files
getDefaultConfiguration() // Fallback default settings
mergeConfigurations(defaults, loaded) // Combine default + loaded configs
validateConfiguration(config) // Ensure all required settings present

// API Configuration (from installer.py DEFAULT_API_URL, etc.)
getApiEndpoint() // Get server API URL
getUpdateCheckInterval() // Get update frequency (24 hours)
getHeartbeatInterval() // Get heartbeat frequency (30 seconds)
getMaxRetries() // Get network retry attempts
getRequestTimeout() // Get API request timeout

// System Paths (from installer.py registry and path handling)
getInstallPath() // Get client installation directory
getConfigFilePath() // Get configuration file location
getLogFilePath() // Get log file location
getCacheDirectory() // Get temporary/cache directory

// Feature Flags (from installer.py feature controls)
isFeatureEnabled(featureName) // Check if feature is enabled
getNotificationSettings() // Get notification behavior settings
getSecuritySettings() // Get security and encryption settings
getLoggingLevel() // Get current logging verbosity

// Registry Operations (Windows - from installer.py winreg usage)
readRegistryValue(keyPath, valueName) // Read Windows registry
writeRegistryValue(keyPath, valueName, value) // Write Windows registry
deleteRegistryValue(keyPath, valueName) // Remove registry entry
registryKeyExists(keyPath) // Check if registry key exists

// Version Management (from installer.py version handling)
getCurrentVersion() // Get current client version
getVersionFromFile() // Read version from version.json
updateStoredVersion(newVersion) // Update version in storage
compareVersions(current, latest) // Version comparison logic