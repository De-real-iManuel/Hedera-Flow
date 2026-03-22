"""
Smart Meter Service — KMS-backed cryptographic operations

Key generation and signing are delegated to AWS KMS (HSM).
Private keys never touch application memory or the database.
Falls back to local ED25519 AES-256 when KMS is unavailable.

Requirements: FR-9.1 to FR-9.12, US-16, US-17
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import uuid
import os

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)


class SmartMeterError(Exception):
    """Raised when smart meter operation fails"""
    pass


# ---------------------------------------------------------------------------
# In-memory simulator state (per-process, keyed by meter_id)
# ---------------------------------------------------------------------------
_simulator_state: Dict[str, Dict[str, Any]] = {}


class SmartMeterService:
    """Service for smart meter cryptographic operations (KMS-first)"""

    def __init__(self, db: Session):
        self.db = db
        self._kms = None
        self._kms_available = False
        self._setup_kms()

    # ------------------------------------------------------------------
    # KMS setup
    # ------------------------------------------------------------------

    def _setup_kms(self):
        try:
            from app.services.aws_kms_service import get_kms_service
            svc = get_kms_service()
            if svc.is_available:
                self._kms = svc
                self._kms_available = True
                logger.info("✅ SmartMeterService: KMS available — HSM signing enabled")
            else:
                logger.warning("⚠️  SmartMeterService: KMS unavailable — falling back to local AES-256")
        except Exception as e:
            logger.warning(f"⚠️  SmartMeterService: KMS init error ({e}) — falling back to local AES-256")

    # ------------------------------------------------------------------
    # Local AES-256 fallback helpers (only used when KMS is unavailable)
    # ------------------------------------------------------------------

    def _get_local_encryption_key(self) -> bytes:
        import hashlib
        raw = os.getenv("METER_KEY_ENCRYPTION_KEY", "")
        if not raw:
            raise SmartMeterError("METER_KEY_ENCRYPTION_KEY not set and KMS is unavailable")
        try:
            key = base64.b64decode(raw)
        except Exception:
            key = hashlib.sha256(raw.encode()).digest()
        if len(key) != 32:
            raise SmartMeterError("METER_KEY_ENCRYPTION_KEY must decode to 32 bytes")
        return key

    def _encrypt_private_key(self, private_pem: bytes) -> tuple[str, str]:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as sym_padding
        key = self._get_local_encryption_key()
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        enc = cipher.encryptor()
        padder = sym_padding.PKCS7(128).padder()
        padded = padder.update(private_pem) + padder.finalize()
        encrypted = enc.update(padded) + enc.finalize()
        return base64.b64encode(encrypted).decode(), base64.b64encode(iv).decode()

    def _decrypt_private_key(self, encrypted_b64: str, iv_b64: str) -> bytes:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as sym_padding
        key = self._get_local_encryption_key()
        encrypted = base64.b64decode(encrypted_b64)
        iv = base64.b64decode(iv_b64)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        dec = cipher.decryptor()
        padded = dec.update(encrypted) + dec.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

    # ------------------------------------------------------------------
    # Keypair generation
    # ------------------------------------------------------------------

    def generate_keypair(self, meter_id: str) -> Dict[str, Any]:
        """
        Generate a keypair for a meter.
        - KMS available: creates an asymmetric KMS key; no private key stored in DB.
        - KMS unavailable: generates local ED25519, stores AES-256 encrypted in DB.
        """
        try:
            check = self.db.execute(
                text("SELECT id FROM smart_meter_keys WHERE meter_id = :m"),
                {"m": meter_id}
            ).fetchone()
            if check:
                raise SmartMeterError(f"Keypair already exists for meter {meter_id}")

            created_at = datetime.utcnow()

            if self._kms_available:
                return self._generate_keypair_kms(meter_id, created_at)
            else:
                return self._generate_keypair_local(meter_id, created_at)

        except SmartMeterError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"generate_keypair failed: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to generate keypair: {e}")

    def _generate_keypair_kms(self, meter_id: str, created_at: datetime) -> Dict[str, Any]:
        result = self._kms.create_meter_key(meter_id)
        kms_key_id = result["key_id"]
        public_key_hex = result["public_key"]

        self.db.execute(text("""
            INSERT INTO smart_meter_keys
                (id, meter_id, public_key, kms_key_id, algorithm, created_at)
            VALUES
                (:id, :meter_id, :public_key, :kms_key_id, :algorithm, :created_at)
        """), {
            "id": str(uuid.uuid4()),
            "meter_id": meter_id,
            "public_key": public_key_hex,
            "kms_key_id": kms_key_id,
            "algorithm": "ECDSA_SHA_256",
            "created_at": created_at,
        })
        self.db.commit()
        logger.info(f"✅ KMS keypair created for meter {meter_id} — key {kms_key_id}")
        return {
            "meter_id": meter_id,
            "public_key": public_key_hex,
            "algorithm": "ECDSA_SHA_256",
            "kms_key_id": kms_key_id,
            "created_at": created_at.isoformat(),
        }

    def _generate_keypair_local(self, meter_id: str, created_at: datetime) -> Dict[str, Any]:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        private_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        encrypted_private, iv = self._encrypt_private_key(private_pem)

        self.db.execute(text("""
            INSERT INTO smart_meter_keys
                (id, meter_id, public_key, private_key_encrypted, encryption_iv, algorithm, created_at)
            VALUES
                (:id, :meter_id, :public_key, :private_key_encrypted, :encryption_iv, :algorithm, :created_at)
        """), {
            "id": str(uuid.uuid4()),
            "meter_id": meter_id,
            "public_key": public_pem,
            "private_key_encrypted": encrypted_private,
            "encryption_iv": iv,
            "algorithm": "ED25519",
            "created_at": created_at,
        })
        self.db.commit()
        logger.info(f"✅ Local ED25519 keypair created for meter {meter_id}")
        return {
            "meter_id": meter_id,
            "public_key": public_pem,
            "algorithm": "ED25519",
            "created_at": created_at.isoformat(),
        }

    # ------------------------------------------------------------------
    # Public key retrieval
    # ------------------------------------------------------------------

    def get_public_key(self, meter_id: str) -> Optional[str]:
        row = self.db.execute(
            text("SELECT public_key FROM smart_meter_keys WHERE meter_id = :m"),
            {"m": meter_id}
        ).fetchone()
        return row[0] if row else None

    def keypair_exists(self, meter_id: str) -> bool:
        row = self.db.execute(
            text("SELECT COUNT(*) FROM smart_meter_keys WHERE meter_id = :m"),
            {"m": meter_id}
        ).fetchone()
        return row[0] > 0

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------

    def sign_consumption(
        self,
        meter_id: str,
        consumption_kwh: float,
        timestamp: int,
        reading_before: Optional[float] = None,
        reading_after: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Sign consumption data. Uses KMS if available, else local ED25519."""
        row = self.db.execute(
            text("SELECT kms_key_id, private_key_encrypted, encryption_iv, public_key FROM smart_meter_keys WHERE meter_id = :m"),
            {"m": meter_id}
        ).fetchone()
        if not row:
            raise SmartMeterError(f"No keypair found for meter {meter_id}")

        kms_key_id, encrypted_private, iv, public_key_pem = row

        if self._kms_available and kms_key_id:
            return self._sign_kms(meter_id, kms_key_id, public_key_pem, consumption_kwh, timestamp, reading_before, reading_after)
        else:
            return self._sign_local(meter_id, encrypted_private, iv, public_key_pem, consumption_kwh, timestamp, reading_before, reading_after)

    def _sign_kms(self, meter_id, kms_key_id, public_key_pem, consumption_kwh, timestamp, reading_before, reading_after):
        import json, hashlib
        data = {"meter_id": meter_id, "consumption_kwh": consumption_kwh, "timestamp": timestamp}
        result = self._kms.sign_consumption_data(kms_key_id, data, meter_id)
        # Update last_used_at
        self.db.execute(text("UPDATE smart_meter_keys SET last_used_at = NOW() WHERE meter_id = :m"), {"m": meter_id})
        self.db.commit()
        return {
            "meter_id": meter_id,
            "consumption_kwh": consumption_kwh,
            "timestamp": timestamp,
            "reading_before": reading_before,
            "reading_after": reading_after,
            "signature": result["signature"],
            "public_key": public_key_pem,
            "message_hash": result["message_hash"],
        }

    def _sign_local(self, meter_id, encrypted_private, iv, public_key_pem, consumption_kwh, timestamp, reading_before, reading_after):
        import hashlib
        private_pem = self._decrypt_private_key(encrypted_private, iv)
        private_key = serialization.load_pem_private_key(private_pem, password=None, backend=default_backend())
        message = f"{meter_id}{consumption_kwh}{timestamp}".encode()
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(message)
        message_hash = digest.finalize().hex()
        signature = private_key.sign(message).hex()
        self.db.execute(text("UPDATE smart_meter_keys SET last_used_at = NOW() WHERE meter_id = :m"), {"m": meter_id})
        self.db.commit()
        return {
            "meter_id": meter_id,
            "consumption_kwh": consumption_kwh,
            "timestamp": timestamp,
            "reading_before": reading_before,
            "reading_after": reading_after,
            "signature": signature,
            "public_key": public_key_pem,
            "message_hash": message_hash,
        }

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_signature(
        self,
        meter_id: str,
        consumption_kwh: float,
        timestamp: int,
        signature: str,
        public_key_pem: Optional[str] = None,
    ) -> Dict[str, Any]:
        if public_key_pem is None:
            public_key_pem = self.get_public_key(meter_id)
            if not public_key_pem:
                raise SmartMeterError(f"No public key found for meter {meter_id}")

        # Determine algorithm from DB
        row = self.db.execute(
            text("SELECT kms_key_id, algorithm FROM smart_meter_keys WHERE meter_id = :m"),
            {"m": meter_id}
        ).fetchone()
        kms_key_id = row[0] if row else None
        algorithm = row[1] if row else "ED25519"

        message = f"{meter_id}{consumption_kwh}{timestamp}".encode()
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(message)
        message_hash_hex = digest.finalize().hex()

        try:
            sig_bytes = bytes.fromhex(signature)
        except ValueError:
            return {"valid": False, "meter_id": meter_id, "consumption_kwh": consumption_kwh,
                    "timestamp": timestamp, "message_hash": message_hash_hex, "algorithm": algorithm,
                    "error": "Invalid signature format"}

        is_valid = False
        if self._kms_available and kms_key_id:
            is_valid = self._kms.verify_signature(kms_key_id, message, sig_bytes)
        else:
            try:
                pub = serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
                pub.verify(sig_bytes, message)
                is_valid = True
            except Exception:
                is_valid = False

        return {
            "valid": is_valid,
            "meter_id": meter_id,
            "consumption_kwh": consumption_kwh,
            "timestamp": timestamp,
            "message_hash": message_hash_hex,
            "algorithm": algorithm,
        }

    # ------------------------------------------------------------------
    # Consumption logging (sign + verify + store + HCS)
    # ------------------------------------------------------------------

    def log_consumption(
        self,
        meter_id: str,
        consumption_kwh: float,
        timestamp: int,
        signature: str,
        public_key_pem: str,
        reading_before: Optional[float] = None,
        reading_after: Optional[float] = None,
    ) -> Dict[str, Any]:
        verification = self.verify_signature(meter_id, consumption_kwh, timestamp, signature, public_key_pem)
        if not verification["valid"]:
            raise SmartMeterError(f"Invalid signature for meter {meter_id} — consumption rejected")

        # Token deduction (best-effort)
        token_deduction = None
        units_deducted = None
        units_remaining = None
        token_id_used = None
        try:
            from app.services.prepaid_token_service import PrepaidTokenService
            prepaid = PrepaidTokenService(self.db)
            deduction = prepaid.deduct_units(meter_id=meter_id, consumption_kwh=consumption_kwh)
            if deduction.get("tokens_deducted"):
                first = deduction["tokens_deducted"][0]
                token_row = self.db.execute(
                    text("SELECT id FROM prepaid_tokens WHERE token_id = :t"),
                    {"t": first["token_id"]}
                ).fetchone()
                if token_row:
                    token_id_used = str(token_row[0])
                units_deducted = deduction["total_deducted"]
                units_remaining = first["remaining"]
                token_deduction = deduction
        except Exception as e:
            logger.warning(f"Token deduction failed (non-critical): {e}")

        # Store consumption log
        log_id = str(uuid.uuid4())
        self.db.execute(text("""
            INSERT INTO consumption_logs
                (id, meter_id, token_id, consumption_kwh, reading_before, reading_after,
                 timestamp, signature, public_key, signature_valid,
                 units_deducted, units_remaining, created_at)
            VALUES
                (:id, :meter_id, :token_id, :consumption_kwh, :reading_before, :reading_after,
                 :timestamp, :signature, :public_key, :signature_valid,
                 :units_deducted, :units_remaining, NOW())
        """), {
            "id": log_id, "meter_id": meter_id, "token_id": token_id_used,
            "consumption_kwh": consumption_kwh, "reading_before": reading_before,
            "reading_after": reading_after, "timestamp": timestamp,
            "signature": signature, "public_key": public_key_pem,
            "signature_valid": True, "units_deducted": units_deducted,
            "units_remaining": units_remaining,
        })

        # HCS logging (best-effort)
        hcs_sequence_number = None
        hcs_topic_id = None
        try:
            meter_row = self.db.execute(text("""
                SELECT m.meter_id, u.country_code FROM meters m
                JOIN users u ON m.user_id = u.id WHERE m.id = :m
            """), {"m": meter_id}).fetchone()
            if meter_row:
                country = meter_row[1] or "ES"
                topic_map = {
                    "ES": os.getenv("HCS_TOPIC_EU", "0.0.8052384"),
                    "US": os.getenv("HCS_TOPIC_US", "0.0.8052396"),
                    "IN": os.getenv("HCS_TOPIC_ASIA", "0.0.8052389"),
                    "BR": os.getenv("HCS_TOPIC_SA", "0.0.8052390"),
                    "NG": os.getenv("HCS_TOPIC_AFRICA", "0.0.8052391"),
                }
                hcs_topic_id = topic_map.get(country, topic_map["ES"])
                from app.services.hedera_service import HederaService
                hedera = HederaService()
                import json
                hcs_msg = json.dumps({
                    "type": "SMART_METER_CONSUMPTION",
                    "meter_id": meter_id,
                    "consumption_kwh": consumption_kwh,
                    "timestamp": timestamp,
                    "signature_valid": True,
                    "log_id": log_id,
                })
                hcs_result = hedera.submit_message(hcs_topic_id, hcs_msg)
                hcs_sequence_number = hcs_result.get("sequence_number")
                # Persist HCS data
                self.db.execute(text("""
                    UPDATE consumption_logs
                    SET hcs_topic_id = :topic, hcs_sequence_number = :seq
                    WHERE id = :id
                """), {"topic": hcs_topic_id, "seq": hcs_sequence_number, "id": log_id})
        except Exception as e:
            logger.warning(f"HCS logging failed (non-critical): {e}")

        self.db.commit()

        return {
            "consumption_log_id": log_id,
            "meter_id": meter_id,
            "consumption_kwh": consumption_kwh,
            "timestamp": timestamp,
            "signature_valid": True,
            "token_deduction": token_deduction,
            "units_deducted": units_deducted,
            "units_remaining": units_remaining,
            "hcs_topic_id": hcs_topic_id,
            "hcs_sequence_number": hcs_sequence_number,
            "reading_before": reading_before,
            "reading_after": reading_after,
        }

    # ------------------------------------------------------------------
    # Simulator state management (in-process, no DB)
    # ------------------------------------------------------------------

    def start_simulator(self, meter_id: str) -> Dict[str, Any]:
        """Start background simulator for a meter (in-memory state)."""
        if meter_id in _simulator_state and _simulator_state[meter_id].get("running"):
            return _simulator_state[meter_id]
        _simulator_state[meter_id] = {
            "running": True,
            "meter_id": meter_id,
            "current_reading": _simulator_state.get(meter_id, {}).get("current_reading", 1000.0),
            "last_logged_reading": _simulator_state.get(meter_id, {}).get("last_logged_reading", 1000.0),
            "total_consumed": _simulator_state.get(meter_id, {}).get("total_consumed", 0.0),
            "logs_count": _simulator_state.get(meter_id, {}).get("logs_count", 0),
            "started_at": datetime.utcnow().isoformat(),
            "last_log_at": None,
        }
        logger.info(f"▶️  Simulator started for meter {meter_id}")
        return _simulator_state[meter_id]

    def stop_simulator(self, meter_id: str) -> Dict[str, Any]:
        """Stop background simulator for a meter."""
        if meter_id not in _simulator_state:
            raise SmartMeterError(f"No simulator running for meter {meter_id}")
        _simulator_state[meter_id]["running"] = False
        logger.info(f"⏹️  Simulator stopped for meter {meter_id}")
        return _simulator_state[meter_id]

    def get_simulator_status(self, meter_id: str) -> Dict[str, Any]:
        """Get current simulator state."""
        if meter_id not in _simulator_state:
            return {"running": False, "meter_id": meter_id}
        return _simulator_state[meter_id]

    def tick_simulator(self, meter_id: str, seconds: float = 5.0) -> Dict[str, Any]:
        """
        Advance simulator by `seconds` of simulated time.
        Returns updated state. Called by the /simulator/tick endpoint.
        """
        import math, random
        state = _simulator_state.get(meter_id)
        if not state or not state["running"]:
            raise SmartMeterError(f"Simulator not running for meter {meter_id}")

        hour = datetime.utcnow().hour
        day = datetime.utcnow().weekday()
        base = 0.3
        if 7 <= hour <= 9 or 18 <= hour <= 22:
            base *= 2.5
        elif hour >= 23 or hour <= 6:
            base *= 0.4
        else:
            base *= 1.2
        if day >= 5:
            base *= 1.3
        rate = base * (0.8 + random.random() * 0.4)

        increment = rate * (seconds / 3600)
        state["current_reading"] = round(state["current_reading"] + increment, 6)
        state["total_consumed"] = round(state["total_consumed"] + increment, 6)
        state["consumption_rate"] = round(rate, 4)
        return state
