# MANUAL WINDOWS ENUMERATION — РУЧНОЕ ПЕРЕЧИСЛЕНИЕ ЧЕРЕЗ CMD/POWERSHELL

## Цель этапа

У нас есть shell на Windows машине. Нужно понять:
- Кто я (какой пользователь, какие права)
- Где я (какой компьютер, в каком домене)
- Кто еще есть (пользователи, группы, сессии)
- Что можно делать (привилегии, доступные команды)

---

# 1. WHO AM I — ОПРЕДЕЛЕНИЕ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ

## whoami — текущий пользователь

whoami
Вывод: tryhackme\asrepuser1 (домен\пользователь)

Если вывод содержит домен — мы на доменной учетке.
Если содержит имя компьютера — локальная учетка.

## whoami /all — все о пользователе

whoami /all

Показывает:
- SID пользователя
- Группы (групповые членства)
- Привилегии (важно для эскалации!)

## Важные привилегии (ключ к эскалации)

SeImpersonatePrivilege — может impersonate других пользователей (potato атаки)
SeAssignPrimaryTokenPrivilege — может назначать токены
SeBackupPrivilege — может читать ЛЮБЫЕ файлы (SAM, SYSTEM)
SeRestorePrivilege — может писать ЛЮБЫЕ файлы
SeDebugPrivilege — может аттачиться к любому процессу (дампить LSASS)

---

# 2. SYSTEM INFORMATION — ЧТО ЗА МАШИНА

hostname — имя компьютера
Часто hostname выдает роль: DC, SRV, PC-XXX

systeminfo — подробная информация об ОС, патчах, домене
systeminfo | findstr /B "OS" — версия ОС
systeminfo | findstr /B "Domain" — имя домена

set — переменные окружения
Показывает: USERDOMAIN, USERNAME, COMPUTERNAME, PATH, и т.д.
Если USERDOMAIN = имя компьютера → машина не в домене

В PowerShell: Get-ChildItem Env: или dir env:

---

# 3. USER ENUMERATION — ПОЛЬЗОВАТЕЛИ И ГРУППЫ

## NET команды (CMD, работают везде)

### Список всех пользователей домена
net user /domain

### Информация о конкретном пользователе
net user daniel.turner /domain

Показывает: активен ли аккаунт, когда менял пароль, группы, последний вход

### Список всех групп домена
net group /domain

### Интересные группы (цели)
- Domain Admins
- Enterprise Admins
- Server Operators
- Backup Operators
- Любые группы с "Admin" в имени

### Участники конкретной группы
net group "Domain Admins" /domain

### Список локальных групп на машине
net localgroup

### Участники локальной группы (например, Administrators)
net localgroup administrators

Важно: Domain Admins часто входят в локальную группу Administrators

### Машинные аккаунты (компьютеры в домене)
net group "Domain Computers" /domain
Машинные аккаунты заканчиваются на $, например WRK$

---

# 4. LOGGED-ON USERS — КТО ЕЩЕ НА МАШИНЕ

## quser или query user — активные сессии

quser

Показывает:
- Имя пользователя
- SESSIONNAME (console, rdp-tcp#0)
- STATE (Active, Disc)
- LOGON TIME

Если админ залогинен → можно украсть его токен или дампнуть LSASS

## tasklist — список процессов (нужны права админа)

tasklist
tasklist /V — подробно (с аргументами)

## net session — активные SMB сессии (нужны права админа)

net session

Показывает, кто подключен к этой машине по SMB

## C:\Users\ — домашние папки пользователей

dir C:\Users\

Каждый пользователь, который хоть раз логинился на эту машину, имеет папку в C:\Users\

---

# 5. SERVICE ACCOUNTS — УЧЕТНЫЕ ЗАПИСИ СЛУЖБ

## WMIC (нужны права админа)

wmic service get Name,StartName

Показывает все службы и учетки, под которыми они запущены.

Интересные StartName:
- LocalSystem — высокие права
- NT AUTHORITY\LocalService
- NT AUTHORITY\NetworkService
- Доменные учетки (DOMAIN\username) — особенно интересны

PowerShell альтернатива:
Get-WmiObject Win32_Service | select Name, StartName

## SC (Service Control) — альтернатива (нужны права админа)

sc query state= all — все службы (очень много)
sc query state= all | find "DHCP" — фильтр по ключевому слову
sc qc DHCP — подробно о конкретной службе (показывает SERVICE_START_NAME)

---

# 6. ENVIRONMENT & REGISTRY — ОКРУЖЕНИЕ И РЕЕСТР

## Переменные окружения (уже было)
set

## Сохраненные Auto-Logon креды (plaintext в реестре)

reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUsername
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword

Если AutoAdminLogon = 1, пароль может быть в DefaultPassword

## Установленные приложения

reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall

## Поиск в реестре по ключевому слову

reg query HKLM /f "password" /t REG_SZ /s

## Scheduled Tasks — планировщик задач

schtasks /query — список всех задач

Также можно создавать (/create) и запускать (/run) задачи

---

# БЫСТРАЯ ШПАРГАЛКА (CMD)

whoami                          # кто я
whoami /all                     # все о пользователе (SID, группы, привилегии)
hostname                        # имя компьютера
systeminfo | findstr "Domain"   # домен
net user /domain                # все пользователи домена
net user username /domain       # инфо о пользователе
net group /domain               # все группы домена
net group "Domain Admins" /domain  # кто в Domain Admins
net localgroup administrators   # локальные админы
quser                           # активные сессии
dir C:\Users\                   # домашние папки пользователей
wmic service get Name,StartName # службы и их учетки
reg query HKLM\...\Winlogon /v DefaultUsername  # сохраненный логин
schtasks /query                 # задачи планировщика