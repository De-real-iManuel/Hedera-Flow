"""Decode the new transaction format."""
import sys
sys.path.insert(0, '.')

TX_HEX = "22b4010a4a0a150a0c08ddd3fccd0610bce4e6cd03120518ade6e40312021803188084af5f220208782a0474657374721e0a1c0a0c0a0518ade6e40310ff83af5f0a0c0a0518b8cde603108084af5f12660a640a2040b0de049baaa00d0e234367046fc613950e1d85f14d7f512a7887bde9dce4821a4029d6429f9aee95c3f0ac120be8da50b5ec7fbe3a348fd6d9be95aa0ccf84290c05638b327e7a34ed9797c9d5a9a4fdce0cb87423bcfa92c979cce4b9e14f0305"

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

# Navigate to body
i = 0
tag_val, i = decode_varint(tx, i)
length, i = decode_varint(tx, i)
signed_tx = tx[i:i+length]

i = 0
tag_val, i = decode_varint(signed_tx, i)
body_len, i = decode_varint(signed_tx, i)
body = signed_tx[i:i+body_len]

print("=== TransactionBody fields ===")
i = 0
while i < len(body):
    tag_val, i = decode_varint(body, i)
    field_num = tag_val >> 3
    wire_type = tag_val & 0x07
    if wire_type == 2:
        length, i = decode_varint(body, i)
        sub = body[i:i+length]
        print(f"  field={field_num} (bytes, len={length}): {sub.hex()}")
        i += length
    elif wire_type == 0:
        val, i = decode_varint(body, i)
        print(f"  field={field_num} (varint): {val}")

# Decode TransactionID (field 1)
i = 0
tag_val, i = decode_varint(body, i)
tx_id_len, i = decode_varint(body, i)
tx_id = body[i:i+tx_id_len]

print("\n=== TransactionID ===")
i = 0
while i < len(tx_id):
    tag_val, i = decode_varint(tx_id, i)
    field_num = tag_val >> 3
    wire_type = tag_val & 0x07
    if wire_type == 2:
        length, i = decode_varint(tx_id, i)
        sub = tx_id[i:i+length]
        print(f"  field={field_num} (bytes, len={length}): {sub.hex()}")
        # Decode sub-fields
        j = 0
        while j < len(sub):
            t2, j = decode_varint(sub, j)
            f2 = t2 >> 3; w2 = t2 & 0x07
            if w2 == 0:
                v2, j = decode_varint(sub, j)
                print(f"    sub-field={f2} val={v2}")
        i += length

print("\nExpected TransactionID structure:")
print("  field=1 = Timestamp{seconds, nanos}")
print("  field=2 = AccountID{num}")
