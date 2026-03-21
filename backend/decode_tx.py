"""Decode our transaction and compare against Hedera proto spec."""
import sys
sys.path.insert(0, '.')

TX_HEX = "22b4010a4a0a150a0518ade6e403120c0883d3fccd061094cfa6d20212021803188084af5f220208784a0474657374721e0a1c0a0c0a0518ade6e40310ff83af5f0a0c0a0518b8cde603108084af5f12660a640a2040b0de049baaa00d0e234367046fc613950e1d85f14d7f512a7887bde9dce4821a4049b0bc09b80b76e4296bdebe12546fc7b268e76634a7c5759d223586199e1e9d3eb99addbd5cd71846afc56b33c1e1c540ac5074caf407db01b01e13c6fb9704"

tx = bytes.fromhex(TX_HEX)

def decode_varint(data, pos):
    val = 0; shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        val |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80): break
    return val, pos

def decode_zigzag(n):
    return (n >> 1) ^ -(n & 1)

def decode_fields(data, indent=0):
    i = 0
    while i < len(data):
        tag_val, i = decode_varint(data, i)
        field_num = tag_val >> 3
        wire_type = tag_val & 0x07
        prefix = "  " * indent
        if wire_type == 2:
            length, i = decode_varint(data, i)
            sub = data[i:i+length]
            print(f"{prefix}field={field_num} (bytes, len={length}): {sub.hex()}")
            i += length
        elif wire_type == 0:
            val, i = decode_varint(data, i)
            print(f"{prefix}field={field_num} (varint): {val} (zigzag={decode_zigzag(val)})")
        else:
            print(f"{prefix}UNKNOWN wire_type={wire_type}")
            break

print("=== Transaction (outer) ===")
decode_fields(tx)

# Manually navigate: field 4 = signedTransactionBytes
i = 0
tag_val, i = decode_varint(tx, i)
assert (tag_val >> 3) == 4, f"Expected field 4, got {tag_val >> 3}"
length, i = decode_varint(tx, i)
signed_tx = tx[i:i+length]

print("\n=== SignedTransaction ===")
decode_fields(signed_tx)

# field 1 = bodyBytes
i = 0
tag_val, i = decode_varint(signed_tx, i)
assert (tag_val >> 3) == 1
body_len, i = decode_varint(signed_tx, i)
body = signed_tx[i:i+body_len]

print("\n=== TransactionBody ===")
decode_fields(body)

# field 1 = transactionID
i = 0
tag_val, i = decode_varint(body, i)
assert (tag_val >> 3) == 1
tx_id_len, i = decode_varint(body, i)
tx_id = body[i:i+tx_id_len]

print("\n=== TransactionID ===")
decode_fields(tx_id)

# field 1 of TransactionID should be accountID
i = 0
tag_val, i = decode_varint(tx_id, i)
f1 = tag_val >> 3
print(f"\nTransactionID field 1 = {f1} (should be 1=accountID or 2=timestamp?)")

# Decode the accountID sub-message
acct_len, i = decode_varint(tx_id, i)
acct = tx_id[i:i+acct_len]
print(f"AccountID bytes: {acct.hex()}")
decode_fields(acct, indent=1)
