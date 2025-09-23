// Installation Key Management (from installer.py validate_installation_key)
validateInstallationKey(key) // Server-based key validation
showKeyEntryDialog() // GUI/console key entry interface
handleKeyValidationResponse(response) // Process server validation response
retryKeyValidation(attempts) // Handle validation failures

// Device Registration (from installer.py register_device)
registerDeviceWithServer() // Register client with server API
buildRegistrationPayload() // Create device info for server
handleRegistrationResponse(response) // Process server registration
generateClientIdentifiers() // Create unique client IDs

// Directory Management (from installer.py create_hidden_install_directory)
createHiddenInstallDirectory() // Create secure installation folder
generateHiddenPath() // Create GUID-based hidden paths
setWindowsHiddenAttributes() // Set file/folder as hidden+system
setRestrictiveACLs() // Configure Windows security permissions
disableIndexing() // Prevent Windows Search indexing