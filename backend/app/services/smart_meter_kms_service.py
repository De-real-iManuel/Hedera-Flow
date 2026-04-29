"""
Smart Meter KMS Service

HSM-backed key management and blind signing for smart meter consumption data.

Each smart meter gets its own asymmetric KMS key (secp256k1 / ECC_SECG_P256K1).
Consumption readings are signed inside the HSM — the private key never leaves AWS KMS.
The resulting signature is attached to the HCS message so any verifier can confirm
the reading came from a legitimate, registered meter.

Architecture:
    Meter registered
        → create_meter_key() creates an asymmetric secp256k1 key inside AWS KMS
        → public key stored in smart_meter_keys table
        → private key NEVER leaves the HSM

    Consumption reading submitted
        → sign_consumption_data() sends data hash to KMS
        → KMS signs inside hardware vault, returns ECDSA signature
        → signature + public key attached to HCS message

    Verification
        → verify_signature() fetches public key from DB
        → verifies ECDSA signature locally using cryptography library
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
from typing import Optional, Dict, Any

from config import settings

logger = logging.getLogger(__name__)


class SmartMeterKMSService:
    """
    AWS KMS-backed key management for smart meters.

    Each meter gets a dedicated secp256k1 asymmetric key inside AWS KMS.
    All signing operations happen inside the HSM — private keys never leave.
    """

    def __init__(self):
        self._kms_client = None
        self._master_key_id = getattr(settings, "aws_kms_master_key_id", None)
        self._region = getattr(settings, "aws_kms_region", "us-east-1")
        self._available = False
        self._init_client()

    def _init_client(self) -> None:
        """Initialize AWS KMS client."""
        try:
            import boto3
            self._kms_client = boto3.client(
                "kms",
                region_name=self._region,
                aws_access_key_id=getattr(settings, "aws_access_key_id", None),
                aws_secret_access_key=getattr(settings, "aws_secret_access_key", None),
            )
            # Verify connectivity
            self._kms_client.list_keys(Limit=1)
            self._available = True
            logger.info("SmartMeterKMSService: AWS KMS client initialized")
        except Exception as e:
            logger.warning(f"SmartMeterKMSService: KMS unavailable — {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    # ------------------------------------------------------------------
    # Key lifecycle
    # ------------------------------------------------------------------

    def create_meter_key(self, meter_id: str, meter_label: str = "") -> Dict[str, Any]:
        """
        Create a dedicated secp256k1 asymmetric key for a smart meter inside AWS KMS.

        Args:
            meter_id: UUID of the meter (used as key description)
            meter_label: Human-readable label for CloudTrail audit trail

        Returns:
            {
                "kms_key_id": str,   # ARN of the KMS key
                "public_key": str,   # hex-encoded compressed 33-byte public key
                "algorithm": str,    # "ECC_SECG_P256K1"
            }

        Raises:
            RuntimeError: If KMS is unavailable or key creation fails
        """
        if not self._available:
            raise RuntimeError("AWS KMS is not available")

        description = f"Lumina smart meter key — meter_id={meter_id}"
        if meter_label:
            description += f" ({meter_label})"

        response = self._kms_client.create_key(
            Description=description,
            KeyUsage="SIGN_VERIFY",
            KeySpec="ECC_SECG_P256K1",
            Tags=[
                {"TagKey": "service", "TagValue": "lumina"},
                {"TagKey": "meter_id", "TagValue": meter_id},
            ],
        )

        key_id = response["KeyMetadata"]["KeyArn"]

        # Fetch the public key
        pub_response = self._kms_client.get_public_key(KeyId=key_id)
        public_key_der = pub_response["PublicKey"]  # DER-encoded SubjectPublicKeyInfo
        public_key_hex = self._der_to_compressed_hex(public_key_der)

        logger.info(f"Created KMS key for meter {meter_id}: {key_id}")

        return {
            "kms_key_id": key_id,
            "public_key": public_key_hex,
            "algorithm": "ECC_SECG_P256K1",
        }

    def get_public_key(self, kms_key_id: str) -> str:
        """
        Retrieve the compressed hex public key for a KMS key.

        Args:
            kms_key_id: KMS key ARN or alias

        Returns:
            Hex-encoded compressed 33-byte secp256k1 public key
        """
        if not self._available:
            raise RuntimeError("AWS KMS is not available")

        response = self._kms_client.get_public_key(KeyId=kms_key_id)
        return self._der_to_compressed_hex(response["PublicKey"])

    def rotate_key(self, kms_key_id: str) -> None:
        """
        Enable automatic annual key rotation for a KMS key.

        Args:
            kms_key_id: KMS key ARN or alias
        """
        if not self._available:
            raise RuntimeError("AWS KMS is not available")

        self._kms_client.enable_key_rotation(KeyId=kms_key_id)
        logger.info(f"Key rotation enabled for {kms_key_id}")

    def schedule_key_deletion(self, kms_key_id: str, pending_days: int = 30) -> None:
        """
        Schedule a KMS key for deletion (e.g., when a meter is decommissioned).

        Args:
            kms_key_id: KMS key ARN or alias
            pending_days: Days before deletion (7–30, AWS minimum is 7)
        """
        if not self._available:
            raise RuntimeError("AWS KMS is not available")

        pending_days = max(7, min(30, pending_days))
        self._kms_client.schedule_key_deletion(
            KeyId=kms_key_id,
            PendingWindowInDays=pending_days,
        )
        logger.info(f"Scheduled deletion of KMS key {kms_key_id} in {pending_days} days")

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------

    def sign_consumption_data(
        self,
        kms_key_id: str,
        consumption_kwh: float,
        timestamp: int,
        meter_id: str,
        reading_before: Optional[float] = None,
        reading_after: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Sign a consumption reading inside AWS KMS (private key never leaves HSM).

        Args:
            kms_key_id: KMS key ARN for this meter
            consumption_kwh: Energy consumed in kWh
            timestamp: Unix timestamp of the reading
            meter_id: Meter identifier
            reading_before: Meter reading before this period (optional)
            reading_after: Meter reading after this period (optional)

        Returns:
            {
                "signature": str,       # hex-encoded DER ECDSA signature
                "message_hash": str,    # hex-encoded SHA-256 of the canonical payload
                "public_key": str,      # hex-encoded compressed public key
                "payload": dict,        # the canonical payload that was signed
            }
        """
        if not self._available:
            raise RuntimeError("AWS KMS is not available")

        payload = {
            "meter_id": meter_id,
            "consumption_kwh": round(consumption_kwh, 6),
            "timestamp": timestamp,
        }
        if reading_before is not None:
            payload["reading_before"] = round(reading_before, 6)
        if reading_after is not None:
            payload["reading_after"] = round(reading_after, 6)

        # Canonical JSON (sorted keys, no whitespace)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        message_hash = hashlib.sha256(canonical).digest()

        response = self._kms_client.sign(
            KeyId=kms_key_id,
            Message=message_hash,
            MessageType="DIGEST",
            SigningAlgorithm="ECDSA_SHA_256",
        )

        signature_der = response["Signature"]
        signature_hex = signature_der.hex()
        public_key_hex = self.get_public_key(kms_key_id)

        logger.info(f"Signed consumption data for meter {meter_id} via KMS key {kms_key_id}")

        return {
            "signature": signature_hex,
            "message_hash": message_hash.hex(),
            "public_key": public_key_hex,
            "payload": payload,
        }

    # ------------------------------------------------------------------
    # Verification (local — no KMS call needed)
    # ------------------------------------------------------------------

    def verify_signature(
        self,
        public_key_hex: str,
        consumption_kwh: float,
        timestamp: int,
        meter_id: str,
        signature_hex: str,
        reading_before: Optional[float] = None,
        reading_after: Optional[float] = None,
    ) -> bool:
        """
        Verify a KMS-produced ECDSA signature locally using the public key.

        Args:
            public_key_hex: Hex-encoded compressed 33-byte secp256k1 public key
            consumption_kwh: Energy consumed in kWh (must match signed payload)
            timestamp: Unix timestamp (must match signed payload)
            meter_id: Meter identifier (must match signed payload)
            signature_hex: Hex-encoded DER ECDSA signature
            reading_before: Optional meter reading before period
            reading_after: Optional meter reading after period

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            from cryptography.hazmat.primitives.asymmetric.ec import (
                ECDSA, SECP256K1, EllipticCurvePublicKey
            )
            from cryptography.hazmat.primitives.hashes import SHA256

            payload = {
                "meter_id": meter_id,
                "consumption_kwh": round(consumption_kwh, 6),
                "timestamp": timestamp,
            }
            if reading_before is not None:
                payload["reading_before"] = round(reading_before, 6)
            if reading_after is not None:
                payload["reading_after"] = round(reading_after, 6)

            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            message_hash = hashlib.sha256(canonical).digest()

            pub_bytes = bytes.fromhex(public_key_hex)
            pub_key = EllipticCurvePublicKey.from_encoded_point(SECP256K1(), pub_bytes)
            sig_bytes = bytes.fromhex(signature_hex)

            pub_key.verify(sig_bytes, message_hash, ECDSA(SHA256()))
            return True

        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def get_key_audit_trail(
        self, kms_key_id: str, max_events: int = 100
    ) -> list:
        """
        Retrieve CloudTrail events for a KMS key (sign/verify operations).

        Args:
            kms_key_id: KMS key ARN
            max_events: Maximum number of events to return

        Returns:
            List of CloudTrail event dicts
        """
        if not self._available:
            raise RuntimeError("AWS KMS is not available")

        try:
            import boto3
            ct = boto3.client(
                "cloudtrail",
                region_name=self._region,
                aws_access_key_id=getattr(settings, "aws_access_key_id", None),
                aws_secret_access_key=getattr(settings, "aws_secret_access_key", None),
            )
            response = ct.lookup_events(
                LookupAttributes=[
                    {"AttributeKey": "ResourceName", "AttributeValue": kms_key_id}
                ],
                MaxResults=max_events,
            )
            return response.get("Events", [])
        except Exception as e:
            logger.warning(f"CloudTrail lookup failed for {kms_key_id}: {e}")
            return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _der_to_compressed_hex(der_bytes: bytes) -> str:
        """
        Extract the compressed 33-byte secp256k1 public key from a
        DER-encoded SubjectPublicKeyInfo blob returned by AWS KMS.
        """
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat, load_der_public_key
        )
        pub = load_der_public_key(der_bytes)
        compressed = pub.public_bytes(Encoding.X962, PublicFormat.CompressedPoint)
        return compressed.hex()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_service_instance: Optional[SmartMeterKMSService] = None


def get_smart_meter_kms_service() -> SmartMeterKMSService:
    """Return the module-level SmartMeterKMSService singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = SmartMeterKMSService()
    return _service_instance
