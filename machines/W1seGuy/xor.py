hex_encoded = "66122b0b29033b0a1e2d772212312d466e051b3a73341443385e161f180c402e1f402c4022290224"
xored_bytes = bytes.fromhex(hex_encoded)

known_prefix = "THM{"
key_partial = ""
for i in range(len(known_prefix)):
    key_partial += chr(xored_bytes[i] ^ ord(known_prefix[i]))

key_last = chr(xored_bytes[-1] ^ ord("}"))

key = key_partial + key_last
print(key)