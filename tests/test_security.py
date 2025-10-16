"""
Tests for security utilities.
"""

import pytest
from app.core.security import (
    EncryptionManager,
    PasswordHasher,
    TokenGenerator,
    SecureStorage,
    generate_secret_key,
    hash_string,
    create_hmac_signature,
    verify_hmac_signature,
    encrypt_password,
    decrypt_password,
)


class TestEncryptionManager:
    """Test encryption and decryption"""

    def test_encrypt_decrypt(self):
        """Test basic encryption and decryption"""
        secret_key = "test-secret-key-for-encryption"
        em = EncryptionManager(secret_key)

        plaintext = "my-secret-password"
        encrypted = em.encrypt(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0

        decrypted = em.decrypt(encrypted)
        assert decrypted == plaintext

    def test_empty_string(self):
        """Test encrypting empty string"""
        em = EncryptionManager("test-key")

        encrypted = em.encrypt("")
        assert encrypted == ""

        decrypted = em.decrypt("")
        assert decrypted == ""

    def test_different_keys_fail(self):
        """Test that decryption fails with wrong key"""
        em1 = EncryptionManager("key1")
        em2 = EncryptionManager("key2")

        encrypted = em1.encrypt("secret")

        with pytest.raises(Exception):
            em2.decrypt(encrypted)

    def test_encrypt_if_needed(self):
        """Test conditional encryption"""
        em = EncryptionManager("test-key")

        plaintext = "password"
        encrypted1 = em.encrypt_if_needed(plaintext)
        encrypted2 = em.encrypt_if_needed(encrypted1)

        # Should not double-encrypt
        assert encrypted1 == encrypted2

        # Should decrypt correctly
        assert em.decrypt(encrypted2) == plaintext


class TestPasswordHasher:
    """Test password hashing"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "my-secure-password"
        hashed, salt = PasswordHasher.hash_password(password)

        assert hashed != password
        assert len(hashed) == 64  # SHA256 hex = 64 chars
        assert len(salt) > 0

    def test_verify_password(self):
        """Test password verification"""
        password = "my-secure-password"
        hashed, salt = PasswordHasher.hash_password(password)

        # Correct password
        assert PasswordHasher.verify_password(password, hashed, salt)

        # Wrong password
        assert not PasswordHasher.verify_password("wrong-password", hashed, salt)

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes with different salts"""
        password = "same-password"

        hashed1, salt1 = PasswordHasher.hash_password(password)
        hashed2, salt2 = PasswordHasher.hash_password(password)

        assert salt1 != salt2
        assert hashed1 != hashed2

    def test_provided_salt(self):
        """Test hashing with provided salt"""
        password = "password"
        salt = "fixed-salt"

        hashed1, _ = PasswordHasher.hash_password(password, salt)
        hashed2, _ = PasswordHasher.hash_password(password, salt)

        # Same salt should produce same hash
        assert hashed1 == hashed2


class TestTokenGenerator:
    """Test token generation"""

    def test_generate_token(self):
        """Test token generation"""
        token = TokenGenerator.generate_token()

        assert len(token) >= 32
        assert isinstance(token, str)

    def test_token_uniqueness(self):
        """Test that tokens are unique"""
        tokens = [TokenGenerator.generate_token() for _ in range(100)]

        # All tokens should be unique
        assert len(set(tokens)) == 100

    def test_session_id(self):
        """Test session ID generation"""
        session_id = TokenGenerator.generate_session_id()

        assert len(session_id) >= 32
        assert isinstance(session_id, str)

    def test_api_key(self):
        """Test API key generation"""
        api_key = TokenGenerator.generate_api_key()

        assert len(api_key) >= 48
        assert isinstance(api_key, str)


class TestSecureStorage:
    """Test secure storage utilities"""

    def test_store_retrieve_credential(self):
        """Test storing and retrieving credentials"""
        ss = SecureStorage("test-secret-key")

        credential = "my-api-key"
        stored = ss.store_credential(credential)

        assert stored != credential

        retrieved = ss.retrieve_credential(stored)
        assert retrieved == credential

    def test_update_credential(self):
        """Test updating credentials"""
        ss = SecureStorage("test-secret-key")

        old = ss.store_credential("old-credential")
        new = ss.update_credential(old, "new-credential")

        assert new != old
        assert ss.retrieve_credential(new) == "new-credential"


class TestUtilityFunctions:
    """Test utility functions"""

    def test_generate_secret_key(self):
        """Test secret key generation"""
        key = generate_secret_key()

        assert len(key) >= 32
        assert isinstance(key, str)

        # Multiple keys should be unique
        keys = [generate_secret_key() for _ in range(10)]
        assert len(set(keys)) == 10

    def test_hash_string_sha256(self):
        """Test SHA256 string hashing"""
        text = "hello world"
        hashed = hash_string(text, "sha256")

        assert len(hashed) == 64  # SHA256 hex = 64 chars
        assert hashed == hash_string(text, "sha256")  # Deterministic

    def test_hash_string_sha512(self):
        """Test SHA512 string hashing"""
        text = "hello world"
        hashed = hash_string(text, "sha512")

        assert len(hashed) == 128  # SHA512 hex = 128 chars

    def test_hash_string_md5(self):
        """Test MD5 string hashing"""
        text = "hello world"
        hashed = hash_string(text, "md5")

        assert len(hashed) == 32  # MD5 hex = 32 chars

    def test_create_verify_hmac(self):
        """Test HMAC signature creation and verification"""
        message = "important message"
        secret = "secret-key"

        signature = create_hmac_signature(message, secret)

        assert len(signature) == 64  # SHA256 HMAC hex = 64 chars
        assert verify_hmac_signature(message, signature, secret)

        # Wrong message
        assert not verify_hmac_signature("wrong message", signature, secret)

        # Wrong key
        assert not verify_hmac_signature(message, signature, "wrong-key")

    def test_encrypt_decrypt_password_convenience(self):
        """Test convenience functions for password encryption"""
        secret_key = "test-secret-key-for-password"
        password = "my-password-123"

        encrypted = encrypt_password(password, secret_key)
        assert encrypted != password

        decrypted = decrypt_password(encrypted, secret_key)
        assert decrypted == password


class TestSecurityIntegration:
    """Integration tests for security components"""

    def test_full_credential_workflow(self):
        """Test complete credential management workflow"""
        secret_key = generate_secret_key()
        ss = SecureStorage(secret_key)

        # Store multiple credentials
        creds = {
            "garmin": ss.store_credential("garmin-password"),
            "api_key": ss.store_credential("claude-api-key"),
            "token": ss.store_credential("session-token"),
        }

        # Verify all can be retrieved
        assert ss.retrieve_credential(creds["garmin"]) == "garmin-password"
        assert ss.retrieve_credential(creds["api_key"]) == "claude-api-key"
        assert ss.retrieve_credential(creds["token"]) == "session-token"

    def test_password_hash_and_verify_workflow(self):
        """Test complete password hash workflow"""
        password = "user-password-123"

        # Hash password
        hashed, salt = PasswordHasher.hash_password(password)

        # Store hash and salt (simulating database storage)
        stored_hash = hashed
        stored_salt = salt

        # Later: verify password on login
        assert PasswordHasher.verify_password(password, stored_hash, stored_salt)
        assert not PasswordHasher.verify_password("wrong", stored_hash, stored_salt)
