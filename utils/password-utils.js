const crypto = require('crypto');

/**
 * Password generation and validation utilities
 */
class PasswordUtils {
    
    /**
     * Generate a secure random password meeting all requirements
     * @param {number} length - Password length (minimum 12)
     * @returns {string} Generated password
     */
    static generateSecurePassword(length = 16) {
        if (length < 12) {
            throw new Error('Password length must be at least 12 characters');
        }

        const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const lowercase = 'abcdefghijklmnopqrstuvwxyz';
        const numbers = '0123456789';
        const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?';
        const allChars = uppercase + lowercase + numbers + symbols;

        let password = '';
        let usedChars = new Set();

        // Ensure at least one character from each required category
        const requiredCategories = [uppercase, lowercase, numbers, symbols];
        
        for (const category of requiredCategories) {
            let char;
            let attempts = 0;
            do {
                char = category[crypto.randomInt(category.length)];
                attempts++;
                if (attempts > 100) {
                    throw new Error('Unable to generate password with unique characters');
                }
            } while (usedChars.has(char));
            
            password += char;
            usedChars.add(char);
        }

        // Fill remaining length with random characters (no repeats)
        while (password.length < length) {
            let char;
            let attempts = 0;
            do {
                char = allChars[crypto.randomInt(allChars.length)];
                attempts++;
                if (attempts > 100) {
                    // If we can't find unique characters, we've exhausted possibilities
                    break;
                }
            } while (usedChars.has(char));
            
            if (!usedChars.has(char)) {
                password += char;
                usedChars.add(char);
            } else {
                // Fallback: reduce length if we can't find more unique characters
                break;
            }
        }

        // Shuffle the password to randomize the order
        return this.shuffleString(password);
    }

    /**
     * Shuffle a string randomly
     * @param {string} str - String to shuffle
     * @returns {string} Shuffled string
     */
    static shuffleString(str) {
        const array = str.split('');
        for (let i = array.length - 1; i > 0; i--) {
            const j = crypto.randomInt(i + 1);
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array.join('');
    }

    /**
     * Validate password meets all requirements
     * @param {string} password - Password to validate
     * @returns {object} Validation result with isValid boolean and errors array
     */
    static validatePassword(password) {
        const errors = [];

        // Check minimum length
        if (!password || password.length < 12) {
            errors.push('Password must be at least 12 characters long');
        }

        // Check for uppercase letters
        if (!/[A-Z]/.test(password)) {
            errors.push('Password must contain at least one uppercase letter');
        }

        // Check for lowercase letters
        if (!/[a-z]/.test(password)) {
            errors.push('Password must contain at least one lowercase letter');
        }

        // Check for numbers
        if (!/[0-9]/.test(password)) {
            errors.push('Password must contain at least one number');
        }

        // Check for symbols
        if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
            errors.push('Password must contain at least one symbol (!@#$%^&*()_+-=[]{}|;:,.<>?)');
        }

        // Check for repeated characters
        const chars = password.split('');
        const uniqueChars = new Set(chars);
        if (chars.length !== uniqueChars.size) {
            errors.push('Password cannot contain repeated characters');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    /**
     * Check if password is strong enough (more comprehensive validation)
     * @param {string} password - Password to check
     * @returns {object} Strength result with score and feedback
     */
    static checkPasswordStrength(password) {
        const validation = this.validatePassword(password);
        
        if (!validation.isValid) {
            return {
                score: 0,
                strength: 'Invalid',
                feedback: validation.errors
            };
        }

        let score = 0;
        const feedback = [];

        // Length scoring
        if (password.length >= 16) score += 2;
        else if (password.length >= 14) score += 1;

        // Character variety scoring
        const hasUpper = /[A-Z]/.test(password);
        const hasLower = /[a-z]/.test(password);
        const hasNumbers = /[0-9]/.test(password);
        const hasSymbols = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password);

        const categoryCount = [hasUpper, hasLower, hasNumbers, hasSymbols].filter(Boolean).length;
        score += categoryCount;

        // Unique character bonus
        const uniqueChars = new Set(password.split(''));
        if (uniqueChars.size === password.length) {
            score += 2;
            feedback.push('All characters are unique');
        }

        // Determine strength level
        let strength;
        if (score >= 8) strength = 'Very Strong';
        else if (score >= 6) strength = 'Strong';
        else if (score >= 4) strength = 'Moderate';
        else strength = 'Weak';

        return {
            score,
            strength,
            feedback: feedback.length > 0 ? feedback : ['Password meets basic requirements']
        };
    }

    /**
     * Generate multiple password options for user to choose from
     * @param {number} count - Number of passwords to generate
     * @param {number} length - Length of each password
     * @returns {Array} Array of generated passwords
     */
    static generatePasswordOptions(count = 3, length = 16) {
        const passwords = [];
        const maxAttempts = count * 10;
        let attempts = 0;

        while (passwords.length < count && attempts < maxAttempts) {
            try {
                const password = this.generateSecurePassword(length);
                // Ensure password is truly unique and valid
                if (!passwords.includes(password) && this.validatePassword(password).isValid) {
                    passwords.push(password);
                }
            } catch (error) {
                console.warn('Password generation attempt failed:', error.message);
            }
            attempts++;
        }

        return passwords;
    }
}

module.exports = PasswordUtils;