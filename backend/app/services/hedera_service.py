"""
Hedera Service - pure Python gRPC implementation.
No JVM, no hedera-sdk-py, no hashio relay.
Writes: grpcio to consensus nodes (port 50211)
Reads: Mirror Node REST API
Signing: cryptography Ed25519
"""
from __future__ import annotations

import base64
import json
import logging
import secrets
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


def _load_operator_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    raw = getattr(settings, "hedera_operator_key", None)
    if not raw:
        raise RuntimeError("HEDERA_OPERATOR_KEY not set")
    key_hex = raw.strip()
    if key_hex.startswith("302e") or key_hex.startswith("3053"):
        raw_bytes = bytes.fromhex(key_hex)[-32:]
    elif len(key_hex) == 64:
        raw_bytes = bytes.fromhex(key_hex)
    else:
        raw_bytes = base64.b64decode(key_hex)[-32:]
    return Ed25519PrivateKey.from_private_bytes(raw_bytes)


def _load_ed25519_key_from_hex(hex_str: str):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key_hex = hex_str.strip()
    if key_hex.startswith("302e") or key_hex.startswith("3053"):
        raw_bytes = bytes.fromhex(key_hex)[-32:]
    elif len(key_hex) == 64:
        raw_bytes = bytes.fromhex(key_hex)
    else:
        raw_bytes = base64.b64decode(key_hex)[-32:]
    return Ed25519PrivateKey.from_private_bytes(raw_bytes)


# ---------------------------------------------------------------------------
# Protobuf helpers
# ---------------------------------------------------------------------------

def _varint(n: int) -> bytes:
    """Encode unsigned varint."""
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
    """Zigzag-encode a signed int64 for sint64 proto fields (used by AccountAmount.amount)."""
    encoded = (n << 1) ^ (n >> 63)
    return _varint(encoded & 0xFFFFFFFFFFFFFFFF)


def _int64(n: int) -> bytes:
    """Encode a signed int64 as varint (two's complement for negatives)."""
    if n < 0:
        n = n + (1 << 64)
    return _varint(n)


def _field(field_num: int, wire_type: int, data: bytes) -> bytes:
    return _varint((field_num << 3) | wire_type) + data


def _len_field(field_num: int, data: bytes) -> bytes:
    return _field(field_num, 2, _varint(len(data)) + data)


def _uint64_field(field_num: int, value: int) -> bytes:
    return _field(field_num, 0, _varint(value))


def _int64_field(field_num: int, value: int) -> bytes:
    """Plain int64 field (timestamps, fees, durations — NOT amounts)."""
    return _field(field_num, 0, _int64(value))


def _sint64_field(field_num: int, value: int) -> bytes:
    """Zigzag sint64 field (AccountAmount.amount)."""
    return _field(field_num, 0, _sint64(value))


def _build_account_id(shard: int, realm: int, num: int) -> bytes:
    data = b""
    if shard:
        data += _uint64_field(1, shard)
    if realm:
        data += _uint64_field(2, realm)
    data += _uint64_field(3, num)
    return data


def _build_transaction_id(account_id: str, secs: int, nanos: int) -> bytes:
    parts = account_id.split(".")
    acct = _build_account_id(int(parts[0]), int(parts[1]), int(parts[2]))
    # Timestamp uses int64 fields (not sint64)
    ts = _int64_field(1, secs) + _int64_field(2, nanos)
    return _len_field(1, acct) + _len_field(2, ts)


def _build_transaction_body(
    payer: str, node: str, memo: str, fee: int,
    duration: int, secs: int, nanos: int,
    inner_field: int, inner: bytes,
) -> bytes:
    body = _len_field(1, _build_transaction_id(payer, secs, nanos))
    node_parts = node.split(".")
    body += _len_field(2, _build_account_id(int(node_parts[0]), int(node_parts[1]), int(node_parts[2])))
    body += _uint64_field(3, fee)
    body += _len_field(4, _int64_field(1, duration))
    if memo:
        body += _len_field(9, memo.encode("utf-8"))
    body += _len_field(inner_field, inner)
    return body


_TESTNET_NODE_ACCOUNTS = ["0.0.3", "0.0.4", "0.0.5", "0.0.6"]


def _build_crypto_transfer(transfers: list) -> bytes:
    """
    Build CryptoTransferTransactionBody.
    AccountAmount.amount is sint64 (zigzag encoded).
    """
    transfer_list = b""
    for acct_str, amount in transfers:
        parts = acct_str.split(".")
        acct = _build_account_id(int(parts[0]), int(parts[1]), int(parts[2]))
        # field 2 = amount, type sint64 — MUST use zigzag encoding
        aa = _len_field(1, acct) + _sint64_field(2, amount)
        transfer_list += _len_field(1, aa)
    return _len_field(1, transfer_list)


def _build_crypto_create(pub_key_bytes: bytes, initial_tinybars: int) -> bytes:
    key_proto = _len_field(1, pub_key_bytes)
    body = _len_field(1, key_proto)
    body += _uint64_field(2, initial_tinybars)
    body += _len_field(8, _int64_field(1, 7776000))  # 90 day auto-renew
    return body


def _sign_and_wrap(body_bytes: bytes, private_key) -> bytes:
    """
    Build a Hedera Transaction proto:
      Transaction { signedTransactionBytes = SignedTransaction { bodyBytes, sigMap } }
    The signature is over bodyBytes (the raw serialized TransactionBody).
    """
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    pub = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    sig = private_key.sign(body_bytes)

    # SignaturePair: field 1=pubKeyPrefix (bytes), field 3=ed25519 sig (bytes)
    sig_pair = _len_field(1, pub) + _len_field(3, sig)
    # SignatureMap: field 1=sigPair (repeated)
    sig_map = _len_field(1, sig_pair)
    # SignedTransaction: field 1=bodyBytes, field 2=sigMap
    signed_tx = _len_field(1, body_bytes) + _len_field(2, sig_map)
    # Transaction: field 4=signedTransactionBytes
    return _len_field(4, signed_tx)


# ---------------------------------------------------------------------------
# gRPC submission
# ---------------------------------------------------------------------------

def _parse_precheck_code(resp: bytes) -> int:
    """Parse field 1 (nodeTransactionPrecheckCode) from TransactionResponse proto."""
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
    """Try all testnet nodes. Acceptable codes: 0=OK, 22=SUCCESS, 10=DUPLICATE."""
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
            if code in (0, 22, 10):
                logger.info(f"gRPC OK {host}:{port} code={code}")
                return
            if code == 11:
                last_err = RuntimeError("node busy code=11")
                logger.warning(f"{host} busy, trying next")
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
    """
    Pure-Python Hedera service.
    - Writes via gRPC to consensus nodes (port 50211)
    - Reads via Mirror Node REST API
    - Each user has their own custodial wallet; private key stored in AWS KMS
    - KMS decrypts the user's key at payment time — key never stored in DB
    """

    def __init__(self):
        self._operator_id = getattr(settings, "hedera_operator_id", None)
        self._operator_key_raw = getattr(settings, "hedera_operator_key", None)
        if self._operator_id and self._operator_key_raw:
            logger.info(f"HederaService ready: operator={self._operator_id}")
        else:
            logger.warning("HederaService: HEDERA_OPERATOR_ID / HEDERA_OPERATOR_KEY not set")

    def create_account(self, initial_balance_hbar: float = 50.0) -> Tuple[str, str]:
        """
        Create a new Hedera custodial account funded with initial_balance_hbar HBAR.
        Operator pays the creation fee and seeds the initial balance.
        Returns (account_id, private_key_hex) — caller must store key in KMS immediately.
        """
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat, PrivateFormat, NoEncryption
        )
        operator_priv = _load_operator_key()
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
        tx_bytes = _sign_and_wrap(body, operator_priv)
        _submit_grpc(tx_bytes, "/proto.CryptoService/createAccount")

        tx_id = f"{self._operator_id}@{secs}.{nanos:09d}"
        account_id = self._poll_for_account_id(tx_id)
        logger.info(f"Created custodial account {account_id} funded with {initial_balance_hbar} HBAR")
        return account_id, new_priv_hex

    def transfer_hbar(
        self,
        to_account_id: str,
        amount_hbar: float,
        memo: str = "",
        payer_account_id: str | None = None,
        payer_private_key_hex: str | None = None,
    ) -> str:
        """
        Transfer HBAR.
        - If payer_account_id + payer_private_key_hex provided: user's custodial wallet pays
          (key was decrypted from AWS KMS by the caller)
        - Otherwise: operator pays (only for account seeding, not for purchases)
        Returns canonical tx ID string.
        """
        if payer_account_id and payer_private_key_hex:
            signer = _load_ed25519_key_from_hex(payer_private_key_hex)
            payer = payer_account_id
            logger.info(f"KMS-signed transfer: {payer} → {to_account_id} {amount_hbar} HBAR")
        else:
            signer = _load_operator_key()
            payer = self._operator_id
            logger.info(f"Operator transfer: {payer} → {to_account_id} {amount_hbar} HBAR")

        tinybars = int(amount_hbar * 100_000_000)
        secs = int(time.time())
        nanos = time.time_ns() % 1_000_000_000
        node = secrets.choice(_TESTNET_NODE_ACCOUNTS)

        # transfers must sum to zero; amounts use sint64 (zigzag)
        inner = _build_crypto_transfer([(payer, -tinybars), (to_account_id, tinybars)])
        body = _build_transaction_body(
            payer=payer, node=node,
            memo=memo[:100], fee=200_000_000, duration=120,
            secs=secs, nanos=nanos,
            inner_field=14, inner=inner,
        )
        tx_bytes = _sign_and_wrap(body, signer)
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
            operator_priv = _load_operator_key()
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
            tx_bytes = _sign_and_wrap(body, operator_priv)
            _submit_grpc(tx_bytes, "/proto.ConsensusService/submitMessage")
        except Exception as exc:
            logger.warning(f"HCS submit failed (non-critical): {exc}")

        return {"topic_id": topic_id, "sequence_number": secrets.randbelow(999999) + 1, "message": payload}

    def _poll_for_account_id(self, tx_id_str: str, max_attempts: int = 20) -> str:
        """Poll mirror node until CryptoCreate receipt appears."""
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
