// Progress Interface (from installer.py InstallationProgressDialog)
createProgressDialog() // Create installation progress window
updateProgressBar(percentage) // Update progress display
showStatusMessage(message) // Display current operation
addLogEntry(message, level) // Add to installation log

// User Interaction (from installer.py key validation UI)
createKeyEntryDialog() // Installation key input interface
showErrorDialog(message) // Error message display
showSuccessDialog(message) // Success message display
handleUserCancellation() // Process user cancellation