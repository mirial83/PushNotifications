// Registry Management (from installer.py winreg operations)
storeInstallationMetadata() // Store config in Windows registry
createRegistryEntries(keyPath, values) // Create registry keys
readRegistryValue(keyPath, valueName) // Read existing registry data
updateRegistryVersion(newVersion) // Update version info in registry

// Windows Security (from installer.py ACL and permissions)
setDeletionProtection(path) // Prevent directory deletion
configureAdminAccess(path) // Set admin-only access permissions
hideFromExplorer(path) // Make directory invisible in Explorer
setSystemFileAttributes(path) // Mark as system files

// System Services
checkWindowsVersion() // Verify Windows compatibility
detectSystemArchitecture() // x64 vs x86 detection
validateSystemRequirements() // Check disk space, RAM, etc.