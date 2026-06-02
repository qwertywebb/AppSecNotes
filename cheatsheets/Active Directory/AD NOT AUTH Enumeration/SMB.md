# SMB ENUMERATION — ПЕРЕЧИСЛЕНИЕ СЕТЕВЫХ ПАПОК

## Почему SMB важен

SMB (Server Message Block) — основной протокол для файловых шаров в Windows.
Часто можно найти:
- Конфигурационные файлы с паролями
- Скрипты и бэкапы
- Документы с чувствительной информацией
- Логи с учетными данными

## Ключевые порты SMB

139 — NetBIOS (старый)
445 — SMB (современный)

## Поиск SMB шаров без пароля (null session)

### smbclient (классика)

# Список всех шаров (без пароля)
smbclient -L //TARGET_IP -N

# Подключение к конкретной шаре (без пароля)
smbclient //TARGET_IP/AnonShare -N

# С указанием учетки (рабочая группа или домен)
smbclient //TARGET_IP/SharedFiles -U 'username%password'

# С указанием домена и учетки (правильный способ для AD)
smbclient //TARGET_IP/SharedFiles -W DOMAIN -U 'username%password'

# Или в одном поле с доменом
smbclient //TARGET_IP/SharedFiles -U 'DOMAIN/username%password'

-N — no password (null session)
-L — list shares
-W — указать домен/рабочую группу

## Почему нужен -W

В AD среде без указания домена аутентификация может пойти не туда.
-W DOMAIN гарантирует, что запрос отправляется к правильному контроллеру домена.

### smbmap (более информативный)

./smbmap.py -H TARGET_IP

Показывает не только список шаров, но и права:
- READ ONLY — только чтение
- READ, WRITE — можно читать и писать
- NO ACCESS — доступа нет

### Nmap SMB скрипты

nmap -p445 --script smb-enum-shares TARGET_IP

## Что делать после подключения

В smbclient:
ls — список файлов
get filename — скачать файл
put filename — загрузить файл (если есть права на запись)
cd folder — перейти в папку
exit — выйти

## Интересные шары по умолчанию

ADMIN$ — админская шара (админский доступ)
C$ — скрытый C:\ (админский доступ)
IPC$ — межпроцессное взаимодействие
NETLOGON — логин скрипты
SYSVOL — групповые политики (GPO)

## Что искать в SMB шарах (пентест)

- Файлы .kdbx (KeePass) — пароли
- .env, web.config, appsettings.json
- Скрипты (.ps1, .bat, .vbs)
- backup.zip, backup.7z
- Документы (passwords.doc, creds.xlsx)
- Файлы конфигурации SSH/VPN

## Другие инструменты для SMB enum

- impacket-smbclient (из Impacket /opt/impacket/examples/)
- enum4linux / enum4linux-ng (подробная enum, много шума)
  enum4linux -a TARGET_IP

- CrackMapExec (NetExec) — для проверки учеток на шарах
  nxc smb TARGET_IP -u users.txt -p passwords.txt --shares