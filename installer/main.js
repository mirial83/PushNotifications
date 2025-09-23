// System Integration (from installer.py)
checkAdminPrivileges() // Check if running as administrator  
restartWithAdmin() // Elevate privileges using Windows UAC
interceptShutdownSignals() // Catch system shutdown attempts
setupWindowsCompatibility() // Windows-specific initialization

// Hardware Identification (from installer.py _get_real_mac_address)
getRealMacAddress() // Get primary network interface MAC
detectNetworkInterfaces() // Enumerate network adapters
validateMacAddress(mac) // Ensure MAC is valid and not virtual

// Process Coordination
initializeInstaller() // Set up installer components
coordinateInstallationFlow() // Orchestrate installation steps
handleInstallationErrors() // Global error handling
cleanupOnExit() // Clean up temporary files and processes