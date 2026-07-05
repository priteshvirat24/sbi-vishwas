"""
SBI Vishwas — PII Protection & Encryption

AES-256-GCM encryption for PII fields, hashing for lookups, and masking for display.
DPDP Act compliant — PII is encrypted at rest, never stored in plaintext.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.config.settings import get_settings


class EncryptionService:
    """
    AES-256-GCM encryption service for PII data.

    Each encrypted value includes a unique nonce, making identical
    plaintexts produce different ciphertexts.
    """

    def __init__(self, key: str | None = None) -> None:
        settings = get_settings()
        raw_key = key or settings.pii_encryption_key or settings.encryption_key
        if not raw_key:
            if settings.is_production:
                raise ValueError("Encryption key is required for production")
            # Development fallback — NOT secure
            raw_key = base64.urlsafe_b64encode(b"dev-key-32-bytes-not-for-prod!!!" ).decode()

        # Decode the base64 key to get raw bytes
        try:
            self._key = base64.urlsafe_b64decode(raw_key)
        except Exception:
            # If not valid base64, use SHA-256 of the key string
            self._key = hashlib.sha256(raw_key.encode()).digest()

        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.
        Returns base64-encoded string: nonce + ciphertext.
        """
        if not plaintext:
            return plaintext

        nonce = os.urandom(12)  # 96-bit nonce
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        # Combine nonce + ciphertext and base64 encode
        return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt a previously encrypted string.
        Expects base64-encoded string: nonce + ciphertext.
        """
        if not encrypted:
            return encrypted

        raw = base64.urlsafe_b64decode(encrypted.encode("utf-8"))
        nonce = raw[:12]
        ciphertext = raw[12:]

        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")


class PIIService:
    """
    PII detection, masking, and hashing utilities.

    Ensures PII is never logged, displayed in full, or stored unprotected.
    """

    # Patterns for common Indian PII
    AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
    PAN_PATTERN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
    PHONE_PATTERN = re.compile(r"\b(?:\+91|91|0)?[6-9]\d{9}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    ACCOUNT_PATTERN = re.compile(r"\b\d{11,17}\b")

    @staticmethod
    def hash_value(value: str) -> str:
        """
        Create a deterministic SHA-256 hash for lookups.
        Normalized: lowercase, stripped.
        """
        normalized = value.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def mask_aadhaar(aadhaar: str) -> str:
        """Mask Aadhaar: show only last 4 digits."""
        digits = re.sub(r"\D", "", aadhaar)
        if len(digits) == 12:
            return f"XXXX XXXX {digits[-4:]}"
        return "XXXX XXXX XXXX"

    @staticmethod
    def mask_pan(pan: str) -> str:
        """Mask PAN: show first and last characters."""
        if len(pan) == 10:
            return f"{pan[0]}XXXX{pan[5:7]}XX{pan[-1]}"
        return "XXXXXXXXXX"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone: show only last 4 digits."""
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 10:
            return f"XXXXXX{digits[-4:]}"
        return "XXXXXXXXXX"

    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email: show first 2 chars and domain."""
        parts = email.split("@")
        if len(parts) == 2:
            local = parts[0]
            masked_local = local[:2] + "***" if len(local) > 2 else "***"
            return f"{masked_local}@{parts[1]}"
        return "***@***.***"

    @staticmethod
    def mask_account_number(account_number: str) -> str:
        """Mask account number: show only last 4 digits."""
        if len(account_number) >= 4:
            return "X" * (len(account_number) - 4) + account_number[-4:]
        return "XXXX"

    def detect_pii(self, text: str) -> list[dict[str, str]]:
        """
        Detect PII patterns in text. Returns list of detected PII with type and masked value.
        Used for logging safety — ensure no PII leaks into logs.
        """
        found: list[dict[str, str]] = []

        for match in self.AADHAAR_PATTERN.finditer(text):
            found.append({"type": "aadhaar", "masked": self.mask_aadhaar(match.group())})

        for match in self.PAN_PATTERN.finditer(text):
            found.append({"type": "pan", "masked": self.mask_pan(match.group())})

        for match in self.PHONE_PATTERN.finditer(text):
            found.append({"type": "phone", "masked": self.mask_phone(match.group())})

        for match in self.EMAIL_PATTERN.finditer(text):
            found.append({"type": "email", "masked": self.mask_email(match.group())})

        return found

    def redact_pii(self, text: str) -> str:
        """
        Redact all detected PII from text. Used before logging.
        """
        redacted = text
        redacted = self.AADHAAR_PATTERN.sub("[AADHAAR_REDACTED]", redacted)
        redacted = self.PAN_PATTERN.sub("[PAN_REDACTED]", redacted)
        redacted = self.PHONE_PATTERN.sub("[PHONE_REDACTED]", redacted)
        redacted = self.EMAIL_PATTERN.sub("[EMAIL_REDACTED]", redacted)
        return redacted


# Module-level instances
encryption_service = EncryptionService()
pii_service = PIIService()
