# АТАКА: PASS-THE-HASH

## Что это:
Аутентификация с использованием только NTLM хэша, без знания пароля.

## Почему это работает:
NTLM протокол использует хэш пароля напрямую в challenge-response механизме.
Серверу/DC не нужен пароль, достаточно правильного response, который вычисляется из хэша.

## Где взять хэш:
- Дамп SAM на скомпрометированной машине
- Дамп ntds.dit с DC
- Память процесса lsass.exe (Mimikatz)
- Перехват NTLM трафика

## Инструменты:
- Impacket (smbclient.py, psexec.py, wmiexec.py и др.)
- Mimikatz (sekurlsa::pth)
- CrackMapExec, evil-winrm

## Пример Impacket:
smbclient.py thm.loc/ben@IP -hashes aad3b435b51404eeaad3b435b51404ee:63CF41DC25C04B8FB79E44B1DEF12C10

## Формат -hashes:
LM_hash:NTLM_hash
(в современных системах LM_hash пустой: aad3b435b51404eeaad3b435b51404ee)

## Против каких протоколов работает:
- SMB (файловые шары, psexec)
- WMI (wmiexec.py)
- WinRM (evil-winrm с хэшем)
- RDP (с ограничениями)

## Защита:
- Отключить NTLM
- Использовать опцию "Restricted Admin Mode" для RDP
- Мониторить логи аутентификации (event ID 4624 с Logon Type 3 и 10)