"""
Custodial KMS Service
Handles encryption and decryption of user Hedera private keys using AWS KMS.

Each user registered on Hedera Flow gets their own funded testnet account.
Their private key is encrypted with the KMS master key (AES-256 symmetric)
and stored in the user's preferences column — the plaintext NEVER touches
the database or application memory beyond the moment of first creation.

When a user chooses "Pay without wallet", this service decrypts their key
so the backend can sign the Hedera transfer on their behalf (custodial flow).

Architecture:
    User registers
        → Hedera account created (operator funds it with 50 HBAR)
        → Private key encrypted here via KMS master key
        → Ciphertext stored in user.preferences["encrypted_hedera_key"]

    User pays without wallet
        → CustodialKMSService.get_private_key() decrypts the key
        → hedera_service.transfer_hbar() signs with the USER's key
        → Operator key is NOT used for user payments
"""

import base64
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from config import settings

logger = logging.getLogger(__name__)


class CustodialKMSError(Exception):
    """Raised when custodial key operations fail"""
    pass


class CustodialKMSService:
    """
    Manages user private key storage via AWS KMS symmetric encryption.

    Uses a single AES-256 master key (ENCRYPT_DECRYPT) to wrap/unwrap
    user Hedera private keys. The master key ID is set via
    AWS_KMS_MASTER_KEY_ID in the environment.
    """

    def __init__(self):
        self._available = False
        self._client = None
        self._master_key_id: Optional[str] = getattr(settings, "aws_kms_master_key_id", None)
        self._region: str = getattr(settings, "aws_kms_region", "us-east-1")
        self._init_client()

    def _init_client(self):
        try:
            self._client = boto3.client("kms", region_name=self._region)
            if self._master_key_id:
                # Quick sanity-check — will raise if key is missing or inaccessible
                self._client.describe_key(KeyId=self._master_key_id)
                logger.info(
                    f"✅ CustodialKMSService ready — master key: {self._master_key_id[:20]}..."
                )
            else:
                logger.warning(
                    "⚠️  AWS_KMS_MASTER_KEY_ID not set — custodial payments will fall back "
                    "to operator key. Set this env var on Railway to enable per-user signing."
                )
            self._available = True
        except Exception as exc:
            logger.warning(f"⚠️  CustodialKMSService unavailable: {exc}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available and self._master_key_id is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_private_key(self, private_key_str: str, context_label: str) -> str:
        """
        Encrypt a Hedera private key with the KMS master key.

        Called once at user registration. The returned ciphertext is safe
        to store in the database — it is useless without KMS access.

        Args:
            private_key_str: Raw Hedera private key (hex or DER string)
            context_label:   Encryption context, e.g. "user-<email>".
                             Must be supplied identically on decryption.

        Returns:
            base64-encoded ciphertext blob

        Raises:
            CustodialKMSError: If KMS is unavailable or encryption fails
        """
        self._require_available()
        try:
            response = self._client.encrypt(
                KeyId=self._master_key_id,
                Plaintext=private_key_str.encode("utf-8"),
                EncryptionContext={"label": context_label},
            )
            ciphertext_b64 = base64.b64encode(response["CiphertextBlob"]).decode("utf-8")
            logger.info(f"✅ Private key encrypted for context: {context_label}")
            return ciphertext_b64
        except ClientError as exc:
            logger.error(f"KMS encrypt failed for {context_label}: {exc}")
            raise CustodialKMSError(f"Failed to encrypt private key: {exc}") from exc

    def get_private_key(self, ciphertext_b64: str, context_label: str) -> str:
        """
        Decrypt a user's Hedera private key from KMS.

        Called during custodial payment to retrieve the user's signing key.
        The plaintext key exists in memory only for the duration of the
        Hedera SDK call and is never logged or persisted.

        Args:
            ciphertext_b64: Value previously returned by store_private_key()
            context_label:  Must match the label used during encryption

        Returns:
            Plaintext private key string

        Raises:
            CustodialKMSError: If KMS is unavailable or decryption fails
        """
        self._require_available()
        try:
            ciphertext = base64.b64decode(ciphertext_b64)
            response = self._client.decrypt(
                CiphertextBlob=ciphertext,
                EncryptionContext={"label": context_label},
            )
            private_key_str = response["Plaintext"].decode("utf-8")
            logger.info(f"✅ Private key decrypted for context: {context_label}")
            return private_key_str
        except ClientError as exc:
            logger.error(f"KMS decrypt failed for {context_label}: {exc}")
            raise CustodialKMSError(f"Failed to decrypt private key: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_available(self):
        if not self._available or not self._client:
            raise CustodialKMSError("CustodialKMSService is not available (KMS unreachable)")
        if not self._master_key_id:
            raise CustodialKMSError(
                "AWS_KMS_MASTER_KEY_ID is not configured. "
                "Set it in Railway environment variables."
            )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_custodial_kms: Optional[CustodialKMSService] = None


def get_custodial_kms() -> CustodialKMSService:
    """
    Return the module-level CustodialKMSService instance.
    Never raises — if KMS is unavailable, is_available will be False
    and callers should fall back to the operator key.
    """
    global _custodial_kms
    if _custodial_kms is None:
        try:
            _custodial_kms = CustodialKMSService()
        except Exception as exc:
            logger.warning(f"CustodialKMSService init failed: {exc}")
            inst = CustodialKMSService.__new__(CustodialKMSService)
            inst._available = False
            inst._client = None
            inst._master_key_id = None
            inst._region = "us-east-1"
            _custodial_kms = inst
    return _custodial_kms
