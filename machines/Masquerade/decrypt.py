from pathlib import Path
import hashlib
import sys

def rc4(key, data):
    """Реализация алгоритма RC4"""
    s = list(range(256))
    j = 0
    
    # KSA (Key Scheduling Algorithm)
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    
    # PRGA (Pseudo-Random Generation Algorithm)
    i = 0
    j = 0
    out = bytearray()
    for byte in data:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        out.append(byte ^ s[(s[i] + s[j]) % 256])
    
    return bytes(out)


def main():
    # 1. Ключ из PowerShell-скрипта
    key = b"X9vT3pL2QwE8xR6ZkYhC4s"
    
    # 2. Исходный файл amd.bin
    input_file = Path("amd.bin")
    
    # 3. Чтение HEX-данных
    hex_data = input_file.read_text().strip()
    
    # 4. Преобразование HEX в байты
    encrypted = bytes.fromhex(hex_data)

    # 5. Расшифровка
    decrypted = rc4(key, encrypted)
    
    # 6. Сохранение результата
    output_file = Path("amdfendrsr.exe")
    output_file.write_bytes(decrypted)
    
    # 7. Вывод SHA-256
    sha256_hash = hashlib.sha256(decrypted).hexdigest()
    print(f"[+] SHA-256: {sha256_hash}")
    print(f"[+] File size: {len(decrypted)} bytes")


if __name__ == "__main__":
    main()
