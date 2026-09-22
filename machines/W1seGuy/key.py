hex_encoded = "66122b0b29033b0a1e2d772212312d466e051b3a73341443385e161f180c402e1f402c4022290224"
key = "2ZfpY"

xored_bytes = bytes.fromhex(hex_encoded)

decrypted = ""
for i in range(len(xored_bytes)):
    decrypted += chr(xored_bytes[i] ^ ord(key[i % len(key)]))

print(decrypted)