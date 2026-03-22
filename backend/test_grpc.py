import sys, os, time
sys.path.insert(0, '.')
os.environ['HEDERA_KEY_TYPE'] = 'ed25519'

from app.services.hedera_service import (
    _build_transaction_body, _build_crypto_transfer, _sign_body, _grpc_submit_raw, _parse_precheck_code
)

payer = '0.0.7942957'
treasury = '0.0.7972536'
# Node account and host MUST be paired
node_account = '0.0.3'
node_host = '0.testnet.hedera.com'

secs = int(time.time())
nanos = time.time_ns() % 1_000_000_000
tinybars = int(1 * 100_000_000)  # 1 HBAR

inner = _build_crypto_transfer([(payer, -tinybars), (treasury, tinybars)])
body = _build_transaction_body(payer=payer, node=node_account, memo='test', fee=200_000_000, duration=120, secs=secs, nanos=nanos, inner_field=14, inner=inner)

key_hex = '302e020100300506032b657004220420de06a51a55ef36369686adbaf0319a5cfb35b2e54106320191b19366fc5b267d'
tx = _sign_body(body, key_hex)

print('TX hex:', tx.hex())
print(f'Submitting 1 HBAR transfer via gRPC to {node_host} (node {node_account})...')
resp = _grpc_submit_raw(tx, node_host, 50211, '/proto.CryptoService/cryptoTransfer')
code = _parse_precheck_code(resp)
print(f'Response code: {code}')
print(f'Response hex: {resp.hex() if resp else "empty"}')
