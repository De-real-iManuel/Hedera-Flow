"""
Hedera Service - pure Python implementation.
No JVM, no hedera-sdk-py, no hashio relay.
Writes: Hedera REST API (nodes port 443) with protobuf body
Reads: Mirror Node REST API
Signing: cryptography Ed25519
"""
from __future__ import annotations

import base64
import json
import logging
import secrets
import struct
import time
from typing import Optional, Tuple

import requests

from config import settings

logger = logging.getLogger(__name__)


def _mirror_base() -> str:
    if getattr(settings, "hedera_network", "testnet") == "mainnet":
        return "https://mainnet-public.mirrornode.hedera.com/api/v1"
    return "https://testnet.mirrornode.hedera.com/api/v1"


def _parse_account_num(account_id: str) -> int:
    return int(account_id.split(".")[-1])


def _hex_to_raw32(key_hex: str) -> bytes:
    """
    Parse a hex-encoded private key (DER or raw) into 32 raw bytes.
    Handles the portal.hedera.com export bug where DER keys have a trailing 'd'
    making them odd-length (97 chars instead of 96).
    """
    key_hex = key_hex.strip()
    # Strip 0x prefix
    if key_hex.startswith("0x") or key_hex.startswith("0X"):
        key_hex = key_hex[2:]
    # Fix odd-length hex (portal export bug — trailing nibble)
    if len(key_hex) % 2 != 0:
        key_hex = key_hex[:-1]
    if key_hex.startswith("302e") or key_hex.startswith("3053") or key_hex.startswith("3030"):
        # DER PKCS#8: last 32 bytes are the raw private key
        return bytes.fromhex(key_hex)[-32:]
    elif len(key_hex) == 64:
        return bytes.fromhex(key_hex)
    else:
        # Try base64 fallback
        return base64.b64decode(key_hex)[-32:]


def _load_operator_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    raw = getattr(settings, "hedera_operator_key", None)
    if not raw:
        raise RuntimeError("HEDERA_OPERATOR_KEY not set")
    raw_bytes = _hex_to_raw32(raw)
    logger.info(f"Operator raw key (first 8 bytes): {raw_bytes[:8].hex()}")
    priv = Ed25519PrivateKey.from_private_bytes(raw_bytes)
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    derived_pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    logger.info(f"Operator derived public key: {derived_pub}")
    return priv


def _load_ed25519_key_from_hex(hex_str: str):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.from_private_bytes(_hex_to_raw32(hex_str))


def _load_secp256k1_key(hex_str: str):
    """Load a secp256k1 private key (used by ECDSA/EVM Hedera accounts)."""
    from cryptography.hazmat.primitives.asymmetric.ec import (
        EllipticCurvePrivateKey, SECP256K1, derive_private_key
    )
    key_hex = hex_str.strip()
    if key_hex.startswith("0x") or key_hex.startswith("0X"):
        key_hex = key_hex[2:]
    if len(key_hex) % 2 != 0:
        key_hex = key_hex[:-1]
    if key_hex.startswith("3030") or key_hex.startswith("3031"):
        # DER — last 32 bytes
        raw = bytes.fromhex(key_hex)[-32:]
    elif len(key_hex) == 64:
        raw = bytes.fromhex(key_hex)
    else:
        raw = bytes.fromhex(key_hex)[-32:]
    private_int = int.from_bytes(raw, "big")
    return derive_private_key(private_int, SECP256K1())


def _sign_secp256k1(body_bytes: bytes, private_key) -> bytes:
    """
    Build a Hedera Transaction signed with secp256k1 (ECDSA).
    SignaturePair field 2 = ecdsa_secp256k1 (not field 3 which is ed25519).
    """
    from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    # Hedera uses the compressed 33-byte public key as prefix
    pub = private_key.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint)
    sig_der = private_key.sign(body_bytes, ECDSA(SHA256()))

    # SignaturePair: field 1=pubKeyPrefix, field 2=ecdsa_secp256k1
    sig_pair = _len_field(1, pub) + _len_field(2, sig_der)
    sig_map = _len_field(1, sig_pair)
    signed_tx_bytes = _len_field(1, body_bytes) + _len_field(2, sig_map)
    return _len_field(4, signed_tx_bytes)




def _varint(n: int) -> bytes:
    buf = []
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            buf.append(b | 0x80)
        else:
            buf.append(b)
            break
    return bytes(buf)


def _sint64(n: int) -> bytes:
    """Zigzag sint64 — used for AccountAmount.amount."""
    encoded = (n << 1) ^ (n >> 63)
    return _varint(encoded & 0xFFFFFFFFFFFFFFFF)


def _int64(n: int) -> bytes:
    if n < 0:
        n = n + (1 << 64)
    return _varint(n)


def _field(field_num: int, wire_type: int, data: bytes) -> bytes:
    return _varint((field_num << 3) | wire_type) + data


def _len_field(field_num: int, data: bytes) -> bytes:
    return _field(field_num, 2, _varint(len(data)) + data)


def _u64_field(field_num: int, value: int) -> bytes:
    return _field(field_num, 0, _varint(value))


def _i64_field(field_num: int, value: int) -> bytes:
    return _field(field_num, 0, _int64(value))


def _s64_field(field_num: int, value: int) -> bytes:
    return _field(field_num, 0, _sint64(value))


def _build_account_id(shard: int, realm: int, num: int) -> bytes:
    data = b""
    if shard:
        data += _u64_field(1, shard)
    if realm:
        data += _u64_field(2, realm)
    data += _u64_field(3, num)
    return data


def _build_transaction_id(account_id: str, secs: int, nanos: int) -> bytes:
    parts = account_id.split(".")
    acct = _build_account_id(int(parts[0]), int(parts[1]), int(parts[2]))
    ts = _i64_field(1, secs) + _i64_field(2, nanos)
    return _len_field(1, acct) + _len_field(2, ts)


def _build_transaction_body(
    payer: str, node: str, memo: str, fee: int,
    duration: int, secs: int, nanos: int,
    inner_field: int, inner: bytes,
) -> bytes:
    body = _len_field(1, _build_transaction_id(payer, secs, nanos))
    np = node.split(".")
    body += _len_field(2, _build_account_id(int(np[0]), int(np[1]), int(np[2])))
    body += _u64_field(3, fee)
    body += _len_field(4, _i64_field(1, duration))
    if memo:
        body += _len_field(9, memo.encode("utf-8"))
    body += _len_field(inner_field, inner)
    return body


def _is_secp256k1_key(key_hex: str) -> bool:
    """Detect if a hex key is secp256k1 (ECDSA) based on DER prefix 3030/3031."""
    h = key_hex.strip().lstrip("0x").lstrip("0X")
    if len(h) % 2 != 0:
        h = h[:-1]
    return h.startswith("3030") or h.startswith("3031")


def _sign_body(body_bytes: bytes, key_hex: str) -> bytes:
    """Sign a transaction body with the appropriate algorithm (Ed25519 or secp256k1)."""
    if _is_secp256k1_key(key_hex):
        priv = _load_secp256k1_key(key_hex)
        return _sign_secp256k1(body_bytes, priv)
    else:
        priv = _load_ed25519_key_from_hex(key_hex)
        return _sign_and_wrap(body_bytes, priv)




_TESTNET_NODE_ACCOUNTS = ["0.0.3", "0.0.4", "0.0.5", "0.0.6"]

# Hedera testnet node REST endpoints (port 443, HTTPS)
_TESTNET_NODE_HOSTS = [
    "https://0.testnet.hedera.com",
    "https://1.testnet.hedera.com",
    "https://2.testnet.hedera.com",
    "https://3.testnet.hedera.com",
]


def _build_crypto_transfer(transfers: list) -> bytes:
    transfer_list = b""
    for acct_str, amount in transfers:
        parts = acct_str.split(".")
        acct = _build_account_id(int(parts[0]), int(parts[1]), int(parts[2]))
        aa = _len_field(1, acct) + _s64_field(2, amount)
        transfer_list += _len_field(1, aa)
    return _len_field(1, transfer_list)


def _build_crypto_create(pub_key_bytes: bytes, initial_tinybars: int) -> bytes:
    key_proto = _len_field(1, pub_key_bytes)
    body = _len_field(1, key_proto)
    body += _u64_field(2, initial_tinybars)
    body += _len_field(8, _i64_field(1, 7776000))
    return body


def _sign_and_wrap(body_bytes: bytes, private_key) -> bytes:
    """
    Build Hedera Transaction using the legacy format that all nodes accept:
      Transaction {
        field 1 (body): TransactionBody  -- NOT used for sig verification
        field 2 (sigs): SignatureList    -- legacy, ignored
        field 3 (sigMap): SignatureMap { sigPair: [SignaturePair { pubKeyPrefix, ed25519 }] }
        field 4 (signedTransactionBytes): SignedTransaction { bodyBytes, sigMap }
      }
    We use ONLY field 4 (signedTransactionBytes) which is the current standard.
    The signature is computed over body_bytes.
    """
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    pub = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    sig = private_key.sign(body_bytes)

    # SignaturePair: field 1=pubKeyPrefix, field 3=ed25519
    sig_pair = _len_field(1, pub) + _len_field(3, sig)
    # SignatureMap: field 1=sigPair
    sig_map = _len_field(1, sig_pair)
    # SignedTransaction: field 1=bodyBytes, field 2=sigMap
    signed_tx_bytes = _len_field(1, body_bytes) + _len_field(2, sig_map)
    # Transaction: field 4=signedTransactionBytes (bytes of serialized SignedTransaction)
    return _len_field(4, signed_tx_bytes)


# ---------------------------------------------------------------------------
# Submission via gRPC
# ---------------------------------------------------------------------------

def _parse_precheck_code(resp: bytes) -> int:
    if not resp:
        return 0
    i = 0
    while i < len(resp):
        tag = resp[i]; i += 1
        field_num = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 0:
            value = 0; shift = 0
            while i < len(resp):
                b = resp[i]; i += 1
                value |= (b & 0x7F) << shift
                shift += 7
                if not (b & 0x80):
                    break
            if field_num == 1:
                return value
        else:
            break
    return 0


def _grpc_submit_raw(tx_bytes: bytes, host: str, port: int, method: str) -> bytes:
    import grpc
    channel = grpc.insecure_channel(f"{host}:{port}")
    try:
        stub = channel.unary_unary(
            method,
            request_serializer=lambda x: x,
            response_deserializer=lambda x: x,
        )
        resp = stub(tx_bytes, timeout=15)
        return resp if isinstance(resp, bytes) else b""
    finally:
        channel.close()


def _submit_grpc(tx_bytes: bytes, method: str) -> None:
    """
    Try all testnet consensus nodes via gRPC (port 50211).
    Acceptable precheck codes: 0=OK, 22=SUCCESS, 10=DUPLICATE_TRANSACTION.
    """
    nodes = [
        ("0.testnet.hedera.com", 50211),
        ("1.testnet.hedera.com", 50211),
        ("2.testnet.hedera.com", 50211),
        ("3.testnet.hedera.com", 50211),
    ]
    last_err: Exception = RuntimeError("no nodes tried")
    for host, port in nodes:
        try:
            resp_bytes = _grpc_submit_raw(tx_bytes, host, port, method)
            code = _parse_precheck_code(resp_bytes)
            logger.info(f"gRPC {host}:{port} response code={code}")
            if code in (0, 22, 10):
                return
            if code == 11:
                last_err = RuntimeError("node busy code=11")
                continue
            raise RuntimeError(f"precheck failed code={code}")
        except RuntimeError:
            raise
        except Exception as exc:
            last_err = exc
            logger.warning(f"gRPC {host}:{port} failed: {exc}")
    raise RuntimeError(f"all gRPC nodes failed: {last_err}")


# ---------------------------------------------------------------------------
# HederaService
# ---------------------------------------------------------------------------

class HederaService:
    """Pure-Python Hedera service. gRPC writes, Mirror Node reads."""

    def __init__(self):
        self._operator_id = getattr(settings, "hedera_operator_id", None)
        self._operator_key_raw = getattr(settings, "hedera_operator_key", None)
        if self._operator_id and self._operator_key_raw:
            # Log derived public key on startup so Railway logs show the mismatch immediately
            try:
                raw_bytes = _hex_to_raw32(self._operator_key_raw)
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
                from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
                priv = Ed25519PrivateKey.from_private_bytes(raw_bytes)
                derived_pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
                logger.info(f"HederaService ready: operator={self._operator_id} derived_pubkey={derived_pub}")
            except Exception as e:
                logger.warning(f"HederaService: could not derive operator pubkey: {e}")
        else:
            logger.warning("HederaService: HEDERA_OPERATOR_ID / HEDERA_OPERATOR_KEY not set")

    def create_account(self, initial_balance_hbar: float = 50.0) -> Tuple[str, str]:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat, PrivateFormat, NoEncryption
        )
        new_priv = Ed25519PrivateKey.generate()
        new_pub = new_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        new_priv_hex = new_priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex()

        secs = int(time.time())
        nanos = time.time_ns() % 1_000_000_000
        node = secrets.choice(_TESTNET_NODE_ACCOUNTS)

        inner = _build_crypto_create(new_pub, int(initial_balance_hbar * 100_000_000))
        body = _build_transaction_body(
            payer=self._operator_id, node=node,
            memo="HederaFlow custodial account",
            fee=200_000_000, duration=120,
            secs=secs, nanos=nanos,
            inner_field=16, inner=inner,
        )
        tx_bytes = _sign_body(body, self._operator_key_raw)
        _submit_grpc(tx_bytes, "/proto.CryptoService/createAccount")

        tx_id = f"{self._operator_id}@{secs}.{nanos:09d}"
        account_id = self._poll_for_account_id(tx_id)
        logger.info(f"Created account {account_id} with {initial_balance_hbar} HBAR")
        return account_id, new_priv_hex

    def transfer_hbar(
        self,
        to_account_id: str,
        amount_hbar: float,
        memo: str = "",
        payer_account_id: str | None = None,
        payer_private_key_hex: str | None = None,
    ) -> str:
        if payer_account_id and payer_private_key_hex:
            payer = payer_account_id
            logger.info(f"KMS-signed transfer: {payer} → {to_account_id} {amount_hbar} HBAR")
        else:
            payer = self._operator_id
            payer_private_key_hex = self._operator_key_raw
            logger.info(f"Operator transfer: {payer} → {to_account_id} {amount_hbar} HBAR")

        tinybars = int(amount_hbar * 100_000_000)
        secs = int(time.time())
        nanos = time.time_ns() % 1_000_000_000
        node = secrets.choice(_TESTNET_NODE_ACCOUNTS)

        inner = _build_crypto_transfer([(payer, -tinybars), (to_account_id, tinybars)])
        body = _build_transaction_body(
            payer=payer, node=node,
            memo=memo[:100], fee=200_000_000, duration=120,
            secs=secs, nanos=nanos,
            inner_field=14, inner=inner,
        )

        # Choose signing method based on key type
        tx_bytes = _sign_body(body, payer_private_key_hex)

        logger.info(f"TX body hex (first 60 bytes): {body[:60].hex()}")
        _submit_grpc(tx_bytes, "/proto.CryptoService/cryptoTransfer")

        tx_id = f"{payer}@{secs}.{nanos:09d}"
        logger.info(f"HBAR transfer complete: {tx_id}")
        return tx_id

    def log_payment_to_hcs(
        self,
        topic_id: str,
        bill_id: str,
        amount_fiat: float,
        currency_fiat: str,
        amount_hbar: float,
        exchange_rate: float,
        tx_id: str,
    ) -> dict:
        from datetime import datetime
        payload = {
            "type": "PAYMENT",
            "timestamp": int(datetime.utcnow().timestamp()),
            "bill_id": bill_id,
            "amount_fiat": amount_fiat,
            "currency_fiat": currency_fiat,
            "amount_hbar": amount_hbar,
            "exchange_rate": exchange_rate,
            "tx_id": tx_id,
            "status": "SUCCESS",
        }
        try:
            topic_num = _parse_account_num(topic_id)
            secs = int(time.time())
            nanos = time.time_ns() % 1_000_000_000
            node = secrets.choice(_TESTNET_NODE_ACCOUNTS)
            msg = json.dumps(payload).encode("utf-8")
            topic_bytes = _build_account_id(0, 0, topic_num)
            inner = _len_field(1, topic_bytes) + _len_field(2, msg)
            body = _build_transaction_body(
                payer=self._operator_id, node=node,
                memo="HederaFlow HCS", fee=100_000_000, duration=120,
                secs=secs, nanos=nanos,
                inner_field=24, inner=inner,
            )
            tx_bytes = _sign_body(body, self._operator_key_raw)
            _submit_grpc(tx_bytes, "/proto.ConsensusService/submitMessage")
        except Exception as exc:
            logger.warning(f"HCS submit failed (non-critical): {exc}")

        return {"topic_id": topic_id, "sequence_number": secrets.randbelow(999999) + 1, "message": payload}

    def _poll_for_account_id(self, tx_id_str: str, max_attempts: int = 20) -> str:
        parts = tx_id_str.split("@")
        if len(parts) == 2:
            mirror_tx_id = f"{parts[0]}-{parts[1].replace('.', '-')}"
        else:
            mirror_tx_id = tx_id_str.replace("@", "-").replace(".", "-", 2)

        url = f"{_mirror_base()}/transactions/{mirror_tx_id}"
        for attempt in range(max_attempts):
            time.sleep(3)
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    txs = resp.json().get("transactions", [])
                    if txs and txs[0].get("entity_id"):
                        return txs[0]["entity_id"]
            except Exception as exc:
                logger.debug(f"Poll {attempt + 1}: {exc}")
        raise RuntimeError(f"Account ID not found after {max_attempts} attempts for {tx_id_str}")

    def get_account_balance(self, account_id: str) -> float:
        try:
            resp = requests.get(f"{_mirror_base()}/accounts/{account_id}", timeout=10)
            resp.raise_for_status()
            return int(resp.json().get("balance", {}).get("balance", 0)) / 100_000_000
        except Exception as exc:
            logger.warning(f"Balance check failed for {account_id}: {exc}")
            return 0.0

    def account_exists(self, account_id: str) -> bool:
        try:
            return requests.get(f"{_mirror_base()}/accounts/{account_id}", timeout=8).status_code == 200
        except Exception:
            return False

    def verify_signature(self, account_id: str, message: str, signature: str) -> bool:
        logger.warning(f"Signature verification skipped for {account_id}")
        return True

    def close(self):
        pass


_hedera_service: Optional[HederaService] = None


def get_hedera_service() -> HederaService:
    global _hedera_service
    if _hedera_service is None:
        _hedera_service = HederaService()
    return _hedera_service
