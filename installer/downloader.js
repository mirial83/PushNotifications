// Network Operations (from installer.py _make_api_request)
downloadClientFromServer() // Download full client application
makeApiRequestWithRetry(url, data, maxRetries) // HTTP with exponential backoff
handleNetworkTimeout() // Manage request timeouts
handleConnectionErrors() // Network error recovery
validateDownloadIntegrity(file, expectedHash) // Verify file integrity

// Progress Management
showDownloadProgress(bytesDownloaded, totalBytes) // Update progress bar
calculateDownloadSpeed(bytes, timeElapsed) // Show download speed
handleDownloadInterruption() // Resume interrupted downloads
cleanupFailedDownload() // Clean up partial downloads

// File Management
extractClientFiles() // Unpack downloaded client
verifyClientSignature() // Validate client authenticity
installClientToHiddenDirectory() // Place client in secured location