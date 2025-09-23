// Configuration Loading (from installer.py default configs)
getDefaultInstallerConfig() // Default installer settings
loadInstallerEnvironment() // Environment-specific settings
getApiEndpoints() // Server URLs for validation and download
getInstallationPaths() // Default and fallback installation paths

// Version Management (from installer.py version handling)
getCurrentInstallerVersion() // Get installer version
getTargetClientVersion() // Get client version to install
checkForInstallerUpdates() // Check if installer needs update