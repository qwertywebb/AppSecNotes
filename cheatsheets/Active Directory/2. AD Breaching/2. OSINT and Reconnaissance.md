# ЭТАП 1: ПОЛУЧЕНИЕ СПИСКА ПОЛЬЗОВАТЕЛЕЙ

## Откуда брать имена пользователей (OSINT)

Перед атаками нужно понять, какие логины существуют в домене.
Источники для сбора имен:

- LinkedIn → сотрудники, должности, структура
- GitHub/GitLab → корпоративные email в коммитах
- Утечки баз данных → email целевого домена
- Корпоративные сайты → страницы "О нас", "Команда"
- Вакансии → технологии, структура, именование

## Форматы usernames (как преобразовать имя в логин)

Пример для Jane Smith:

- first.last → jane.smith
- firstlast → janesmith
- flast → jsmith
- first.l → jane.s
- first → jane
- last.first → smith.jane

Один подтвержденный email сразу показывает формат.

## User Enumeration через Kerberos (kerbrute)

Как это работает:
1. Шлем AS-REQ запрос к KDC с username
2. Получаем ответ:
   - KDC_ERR_C_PRINCIPAL_UNKNOWN → пользователь НЕ существует
   - KDC_ERR_PREAUTH_REQUIRED → пользователь СУЩЕСТВУЕТ

Почему это безопасно для атакующего:
- Не считается неудачной попыткой входа
- Не триггерит блокировку аккаунта
- Генерирует Event ID 4768 на DC

Запуск перечисления:
kerbrute userenum -d thm.loc --dc 192.168.12.100 /path/to/usernames.txt

## DNS Enumeration (найти ключевые серверы)

DNS enum в AD: по известному домену ищем имена хостов DC и других серверов, чтобы потом использовать их в атаках.
AD неразрывно связан с DNS. Без DNS клиенты не найдут DC, KDC, не смогут определить имя домена. DNS enumeration дает карту сети: где DC, где почта, какие еще серверы.

Найти Domain Controllers:
nslookup -type=SRV _ldap._tcp.dc._msdcs.thm.loc 192.168.12.100

Найти KDC (Kerberos):
nslookup -type=SRV _kerberos._tcp.thm.loc 192.168.12.100

Найти mail серверы:
nslookup -type=MX thm.loc 192.168.12.100

Что это дает:
- Понимание топологии сети
- Знание где DC, почта, другие сервисы
- Цели для следующих атак

# АНАЛИЗ DNS ЗАПИСЕЙ AD

nslookup -type=SRV _ldap._tcp.dc._msdcs.<DOMAIN> IP
- Находит Domain Controllers через LDAP
- Формат ответа: priority weight port hostname
- Порт 389 = LDAP

nslookup -type=SRV _kerberos._tcp.<DOMAIN> IP
- Находит KDC (Key Distribution Center)
- Порт 88 = Kerberos

nslookup -type=SRV _kerberos._udp.<DOMAIN> IP
- Kerberos по UDP (реже используется)

nslookup -type=SRV _mx.<DOMAIN> IP
- Находит почтовые серверы
- "No answer" → почты нет или нет записей

nslookup -type=SRV _ns.<DOMAIN> IP
- Находит DNS серверы (не в примере, но полезно)

## Что делать с этой информацией

1. Теперь знаем точное имя DC для атак
2. Можем настроить /etc/hosts:
   192.168.12.100 rdc1.thm.loc thm.loc
3. Знаем какие сервисы доступны (LDAP, Kerberos)
4. Понимаем топологию домена

# ЗАЧЕМ НУЖНА DNS ENUM (если домен уже известен)

Знать домен → знать "название страны"
DNS enum → получить "карту городов и улиц"

DNS enum дает:
- IP и hostname DC (для Kerberos, LDAP, SMB)
- Альтернативные DC (если основной недоступен)
- Почтовые серверы (цели для атак)
- Понимание топологии сети

Без DNS enum:
- Не сможешь использовать Kerberos (hostname неизвестен)
- Не узнаешь про другие DC
- Пропустишь цели