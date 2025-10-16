"""
Security utilities for credential encryption and token management.

Provides functions for encrypting sensitive data at rest, hashing passwords,
and generating secure tokens for session management.
"""

import base64
import hashlib
import hmac
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data.

    Uses Fernet (symmetric encryption) with keys derived from the application
    secret key. All encrypted values are base64-encoded for safe storage.
    """

    def __init__(self, secret_key: str):
        """
        Initialize encryption manager.

        Args:
            secret_key: Application secret key used to derive encryption key
        """
        self.secret_key = secret_key
        self._fernet = self._create_fernet()

    def _create_fernet(self) -> Fernet:
        """
        Create Fernet instance with derived key.

        Uses PBKDF2 to derive a suitable encryption key from the secret key.

        Returns:
            Fernet: Encryption instance
        """
        # Derive a 32-byte key from the secret key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"training_optimizer_salt",  # Fixed salt for consistent key derivation
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(self.secret_key.encode())
        )
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            str: Base64-encoded encrypted string

        Example:
            >>> em = EncryptionManager("my-secret-key")
            >>> encrypted = em.encrypt("my-password")
            >>> decrypted = em.decrypt(encrypted)
            >>> assert decrypted == "my-password"
        """
        if not plaintext:
            return ""

        encrypted_bytes = self._fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            str: Decrypted plaintext string

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        if not encrypted_text:
            return ""

        decrypted_bytes = self._fernet.decrypt(encrypted_text.encode())
        return decrypted_bytes.decode()

    def encrypt_if_needed(self, value: str) -> str:
        """
        Encrypt a value if it's not already encrypted.

        Attempts to decrypt first; if it fails, assumes the value is plaintext
        and encrypts it.

        Args:
            value: Plaintext or encrypted string

        Returns:
            str: Encrypted string
        """
        try:
            # Try to decrypt - if successful, already encrypted
            self.decrypt(value)
            return value
        except Exception:
            # Not encrypted, encrypt it now
            return self.encrypt(value)


class PasswordHasher:
    """
    Password hashing utilities using PBKDF2-SHA256.

    Provides secure password hashing for user authentication.
    """

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a password using PBKDF2-SHA256.

        Args:
            password: Plaintext password
            salt: Optional salt (generated if not provided)

        Returns:
            tuple: (hashed_password, salt) both as hex strings

        Example:
            >>> hashed, salt = PasswordHasher.hash_password("my-password")
            >>> is_valid = PasswordHasher.verify_password("my-password", hashed, salt)
            >>> assert is_valid is True
        """
        if salt is None:
            salt = secrets.token_hex(32)
        else:
            # Ensure salt is string
            salt = str(salt)

        # Use PBKDF2 with 100,000 iterations
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        hashed = kdf.derive(password.encode())
        return hashed.hex(), salt

    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plaintext password to verify
            hashed_password: Hex-encoded hashed password
            salt: Hex-encoded salt used for hashing

        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            new_hash, _ = PasswordHasher.hash_password(password, salt)
            return hmac.compare_digest(new_hash, hashed_password)
        except Exception:
            return False


class TokenGenerator:
    """
    Secure token generation for sessions and API access.
    """

    @staticmethod
    def generate_token(nbytes: int = 32) -> str:
        """
        Generate a cryptographically secure random token.

        Args:
            nbytes: Number of random bytes (default 32 = 256 bits)

        Returns:
            str: URL-safe base64-encoded token

        Example:
            >>> token = TokenGenerator.generate_token()
            >>> len(token) >= 32  # At least 32 characters
            True
        """
        return secrets.token_urlsafe(nbytes)

    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a session ID.

        Returns:
            str: 32-byte session ID
        """
        return TokenGenerator.generate_token(32)

    @staticmethod
    def generate_api_key() -> str:
        """
        Generate an API key.

        Returns:
            str: 48-byte API key
        """
        return TokenGenerator.generate_token(48)


class SecureStorage:
    """
    Secure storage helper for managing encrypted credentials.

    Provides a simple interface for storing and retrieving encrypted values.
    """

    def __init__(self, secret_key: str):
        """
        Initialize secure storage.

        Args:
            secret_key: Application secret key for encryption
        """
        self.encryption_manager = EncryptionManager(secret_key)

    def store_credential(self, credential: str) -> str:
        """
        Store a credential securely (encrypted).

        Args:
            credential: Plaintext credential

        Returns:
            str: Encrypted credential safe for storage
        """
        return self.encryption_manager.encrypt(credential)

    def retrieve_credential(self, encrypted_credential: str) -> str:
        """
        Retrieve a stored credential (decrypt).

        Args:
            encrypted_credential: Encrypted credential

        Returns:
            str: Plaintext credential
        """
        return self.encryption_manager.decrypt(encrypted_credential)

    def update_credential(
        self,
        current_encrypted: str,
        new_plaintext: str
    ) -> str:
        """
        Update an encrypted credential.

        Args:
            current_encrypted: Current encrypted value (unused, for interface)
            new_plaintext: New plaintext value to encrypt

        Returns:
            str: New encrypted value
        """
        return self.store_credential(new_plaintext)


def generate_secret_key() -> str:
    """
    Generate a secure secret key for application use.

    Returns:
        str: 32-byte URL-safe secret key

    Example:
        >>> key = generate_secret_key()
        >>> len(key) >= 32
        True
    """
    return secrets.token_urlsafe(32)


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using the specified algorithm.

    Args:
        value: String to hash
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        str: Hex-encoded hash

    Example:
        >>> hash_string("hello") == hashlib.sha256(b"hello").hexdigest()
        True
    """
    if algorithm == "sha256":
        return hashlib.sha256(value.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(value.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(value.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def verify_hmac_signature(
    message: str,
    signature: str,
    secret_key: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify an HMAC signature.

    Args:
        message: Original message
        signature: HMAC signature to verify (hex-encoded)
        secret_key: Secret key used for signing
        algorithm: Hash algorithm (sha256, sha512)

    Returns:
        bool: True if signature is valid, False otherwise

    Example:
        >>> key = "secret"
        >>> msg = "hello"
        >>> sig = create_hmac_signature(msg, key)
        >>> verify_hmac_signature(msg, sig, key)
        True
    """
    expected_sig = create_hmac_signature(message, secret_key, algorithm)
    return hmac.compare_digest(signature, expected_sig)


def create_hmac_signature(
    message: str,
    secret_key: str,
    algorithm: str = "sha256"
) -> str:
    """
    Create an HMAC signature for a message.

    Args:
        message: Message to sign
        secret_key: Secret key for signing
        algorithm: Hash algorithm (sha256, sha512)

    Returns:
        str: Hex-encoded HMAC signature

    Example:
        >>> sig = create_hmac_signature("hello", "secret")
        >>> len(sig) == 64  # SHA256 produces 64 hex characters
        True
    """
    if algorithm == "sha256":
        hash_func = hashlib.sha256
    elif algorithm == "sha512":
        hash_func = hashlib.sha512
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hash_func
    ).hexdigest()

    return signature


# Convenience function for backward compatibility
def encrypt_password(password: str, secret_key: str) -> str:
    """
    Encrypt a password using the application secret key.

    Args:
        password: Plaintext password
        secret_key: Application secret key

    Returns:
        str: Encrypted password

    Example:
        >>> key = generate_secret_key()
        >>> encrypted = encrypt_password("my-password", key)
        >>> decrypted = decrypt_password(encrypted, key)
        >>> assert decrypted == "my-password"
    """
    em = EncryptionManager(secret_key)
    return em.encrypt(password)


def decrypt_password(encrypted_password: str, secret_key: str) -> str:
    """
    Decrypt a password using the application secret key.

    Args:
        encrypted_password: Encrypted password
        secret_key: Application secret key

    Returns:
        str: Decrypted password
    """
    em = EncryptionManager(secret_key)
    return em.decrypt(encrypted_password)
