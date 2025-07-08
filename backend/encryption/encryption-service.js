/**
 * Backend Encryption Service
 * Handles encryption of sensitive backend functions and data
 * 
 * @module backend-encryption
 */

const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

class BackendEncryptionService {
  constructor(config = {}) {
    this.encryptionKey = config.encryptionKey || process.env.ENCRYPTION_KEY || this.generateKey();
    this.algorithm = 'aes-256-gcm';
    this.keyDerivationIterations = 100000;
    this.saltLength = 32;
    this.ivLength = 16;
    this.tagLength = 16;
  }

  /**
   * Generate a new encryption key
   */
  generateKey() {
    return crypto.randomBytes(32).toString('hex');
  }

  /**
   * Encrypt sensitive data
   */
  encrypt(plaintext, additionalData = null) {
    try {
      const key = Buffer.from(this.encryptionKey, 'hex');
      const iv = crypto.randomBytes(this.ivLength);
      
      const cipher = crypto.createCipher(this.algorithm, key, { iv });
      
      if (additionalData) {
        cipher.setAAD(Buffer.from(additionalData));
      }
      
      let encrypted = cipher.update(plaintext, 'utf8', 'hex');
      encrypted += cipher.final('hex');
      
      const tag = cipher.getAuthTag();
      
      return {
        encrypted,
        iv: iv.toString('hex'),
        tag: tag.toString('hex'),
        additionalData
      };
    } catch (error) {
      throw new Error(`Encryption failed: ${error.message}`);
    }
  }

  /**
   * Decrypt sensitive data
   */
  decrypt(encryptedData) {
    try {
      const { encrypted, iv, tag, additionalData } = encryptedData;
      const key = Buffer.from(this.encryptionKey, 'hex');
      
      const decipher = crypto.createDecipher(this.algorithm, key, { 
        iv: Buffer.from(iv, 'hex') 
      });
      
      decipher.setAuthTag(Buffer.from(tag, 'hex'));
      
      if (additionalData) {
        decipher.setAAD(Buffer.from(additionalData));
      }
      
      let decrypted = decipher.update(encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      
      return decrypted;
    } catch (error) {
      throw new Error(`Decryption failed: ${error.message}`);
    }
  }

  /**
   * Hash passwords securely
   */
  async hashPassword(password) {
    const saltRounds = 12;
    return await bcrypt.hash(password, saltRounds);
  }

  /**
   * Verify password against hash
   */
  async verifyPassword(password, hash) {
    return await bcrypt.compare(password, hash);
  }

  /**
   * Generate secure JWT token
   */
  generateJWT(payload, options = {}) {
    const defaultOptions = {
      expiresIn: '24h',
      issuer: 'cbs-backend',
      audience: 'cbs-frontend'
    };
    
    return jwt.sign(payload, this.encryptionKey, { ...defaultOptions, ...options });
  }

  /**
   * Verify JWT token
   */
  verifyJWT(token, options = {}) {
    const defaultOptions = {
      issuer: 'cbs-backend',
      audience: 'cbs-frontend'
    };
    
    return jwt.verify(token, this.encryptionKey, { ...defaultOptions, ...options });
  }

  /**
   * Encrypt API payload
   */
  encryptAPIPayload(payload) {
    const plaintext = JSON.stringify(payload);
    const timestamp = Date.now().toString();
    
    return this.encrypt(plaintext, timestamp);
  }

  /**
   * Decrypt API payload
   */
  decryptAPIPayload(encryptedPayload) {
    const decrypted = this.decrypt(encryptedPayload);
    return JSON.parse(decrypted);
  }

  /**
   * Generate secure random string
   */
  generateSecureRandom(length = 32) {
    return crypto.randomBytes(length).toString('hex');
  }

  /**
   * Create HMAC signature
   */
  createHMAC(data, secret = null) {
    const key = secret || this.encryptionKey;
    return crypto.createHmac('sha256', key).update(data).digest('hex');
  }

  /**
   * Verify HMAC signature
   */
  verifyHMAC(data, signature, secret = null) {
    const expectedSignature = this.createHMAC(data, secret);
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    );
  }

  /**
   * Encrypt database fields
   */
  encryptDatabaseField(value) {
    if (value === null || value === undefined) return null;
    
    const result = this.encrypt(value.toString());
    return `${result.iv}:${result.tag}:${result.encrypted}`;
  }

  /**
   * Decrypt database fields
   */
  decryptDatabaseField(encryptedValue) {
    if (!encryptedValue) return null;
    
    const [iv, tag, encrypted] = encryptedValue.split(':');
    return this.decrypt({ iv, tag, encrypted });
  }

  /**
   * Generate API key
   */
  generateAPIKey(userId, permissions = []) {
    const payload = {
      userId,
      permissions,
      type: 'api_key',
      generated: Date.now()
    };
    
    return this.generateJWT(payload, { expiresIn: '1y' });
  }

  /**
   * Validate API key
   */
  validateAPIKey(apiKey) {
    try {
      const decoded = this.verifyJWT(apiKey);
      
      if (decoded.type !== 'api_key') {
        throw new Error('Invalid API key type');
      }
      
      return {
        valid: true,
        userId: decoded.userId,
        permissions: decoded.permissions || [],
        generated: decoded.generated
      };
    } catch (error) {
      return {
        valid: false,
        error: error.message
      };
    }
  }
}

module.exports = BackendEncryptionService;
