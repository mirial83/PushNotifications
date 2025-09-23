// AES-256-GCM Encryption (from installer.py AESGCM class)
encryptData(data, key) // Encrypt sensitive data
decryptData(encryptedData, key) // Decrypt sensitive data
generateEncryptionKey() // Create new encryption keys

// Key Derivation (from installer.py PBKDF2HMAC)
deriveKeyFromPassword(password, salt, iterations) // PBKDF2 key derivation
generateSalt() // Create cryptographic salt
validateKeyStrength(key) // Ensure key meets security requirements

// Hashing and Integrity (from installer.py hashlib usage)
generateSHA256Hash(data) // Create SHA-256 hashes
generateMD5Hash(data) // Create MD5 hashes for file integrity
verifyDataIntegrity(data, expectedHash) // Verify data hasn't been tampered

// Secure Random Generation (from installer.py secrets)
generateSecureRandom(length) // Cryptographically secure random bytes
generateUUID() // Unique identifiers for requests
generateNonce() // Cryptographic nonces for encryption

// Configuration Encryption (from installer.py encrypted path storage)
encryptConfiguration(config) // Encrypt client configuration
decryptConfiguration(encryptedConfig) // Decrypt client configuration
storeEncryptedValue(key, value) // Store encrypted registry/file values
retrieveEncryptedValue(key) // Retrieve and decrypt stored values