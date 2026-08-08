import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

def sha256_key(passphrase):
    return hashlib.sha256(passphrase.encode()).digest()

def decrypt_guid(guid_b64, passphrase):
    key = sha256_key(passphrase)
    
    # 1. Декодируем Base64 (внешний слой)
    outer = base64.b64decode(guid_b64)
    
    # 2. Превращаем байты в строку (это внутренний Base64)
    inner_b64 = outer.decode('utf-8')
    
    # 3. Декодируем Base64 (внутренний слой)
    data = base64.b64decode(inner_b64)
    
    # 4. Разделяем IV и шифротекст
    iv = data[:16]
    ct = data[16:]
    
    if len(ct) % 16 != 0:
        ct = ct[:-(len(ct) % 16)]
    
    # 5. Расшифровываем
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    
    # 6. Убираем паддинг
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()
    return plaintext.decode("utf-8", errors="replace")

guid="c09Gc3pZOGRaOGF6MWo4bUNKM0tGUktFK2t2b3dOOEtQR2hhWUF0VVlhcUdwWjl4RGJHNXR1UnkyRzdOTXptdQ=="
passphrase = "M4squ3r4d3Th3P4ck3tSt34lthM0d31337"

try:
    result = decrypt_guid(guid, passphrase)
    print(result)
except Exception as e:
    print("ERROR:", e)