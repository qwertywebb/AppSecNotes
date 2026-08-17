#  DNS

DNS — система разрешения доменных имён.

google.com → IP

## 🔄 Как это работает (по шагам)

1. Ты вводишь `brkserv.duckdns.org` в браузере.
2. Компьютер спрашивает DNS-резолвер(сервер провайдера).
3. Резолвер:
   - Идёт к корневому серверу (root server) → узнаёт, кто отвечает за .org
   - Идёт к серверу .org → узнаёт NS-запись duckdns.org (кто является авторитетным сервером для duckdns.org)
   - Идёт к авторитетному серверу duckdns.org (например, ns1.duckdns.org) → спрашивает про brkserv
   - Авторитетный сервер возвращает A-запись: 147.45.173.98
4. Резолвер возвращает IP-адрес браузеру.
5. Браузер соединяется с `147.45.173.98:443`.




# 📚 Основные записи

| Тип       | Назначение                          | Пример                       |
| --------- | ----------------------------------- | ---------------------------- |
| **A**     | Домен → IPv4                        | `site.com → 1.2.3.4`         |
| **AAAA**  | Домен → IPv6                        | `site.com → 2001:db8::1`     |
| **CNAME** | Имя → другое имя                    | `www.site.com → site.com`    |
| **MX**    | Почтовые серверы                    | `site.com → mail.site.com`   |
| **TXT**   | Текстовые данные                    | SPF, DKIM, verification      |
| **NS**    | Авторитетные DNS-серверы зоны       | `site.com → ns1.site.com`    |
| **PTR**   | IP → hostname                       | `1.2.3.4 → server.site.com`  |
| **SOA**   | Основная информация о DNS-зоне      | serial, refresh, primary NS  |
| **SRV**   | Где находится конкретный сервис     | `_ldap._tcp.site.com`        |
| **CAA**   | Какие CA могут выдавать сертификаты | `site.com → letsencrypt.org` |

### Особенно запомнить для пентеста

```text
A     → IP
AAAA  → IPv6
CNAME → другой hostname
MX    → mail
NS    → authoritative DNS
TXT   → SPF/DKIM/verification
PTR   → IP → hostname
SRV   → сервис → hostname + port
```

---

# 🔄 Как работает DNS

```text
Browser
   ↓
DNS Resolver
   ↓
Root .
   ↓
TLD (.com)
   ↓
Authoritative DNS
   ↓
A record
   ↓
IP
```

**Resolver** — например `1.1.1.1`.

**Authoritative DNS** — сервер, который действительно отвечает за DNS-зону домена.


# 🔎 DNS Recon

## Получить IP

```bash
dig +short example.com
```

```bash
host example.com
```


## Получить все основные записи

```bash
dig example.com A
dig example.com AAAA
dig example.com MX
dig example.com NS
dig example.com TXT
dig example.com SOA
dig example.com CNAME
dig example.com SRV
```


# 🌐 NS — узнать DNS-серверы

```bash
dig example.com NS
```

Получаем:

```text
ns1.example.com
ns2.example.com
```

Затем можно напрямую спрашивать authoritative server:

```bash
dig @ns1.example.com example.com A
```

---

# 🔙 PTR / Reverse DNS

PTR позволяет сделать:

```text
IP → hostname
```

```bash
dig -x 8.8.8.8
```

или:

```bash
nslookup 8.8.8.8
```

Важно:

> PTR может отсутствовать. `NXDOMAIN` не означает ошибку — просто обратная запись не настроена.

**Reverse DNS** — процесс, **PTR** — тип записи.

---

# 🏢 WHOIS / ASN / CIDR

Получил IP:

```bash
dig +short example.com
```

Например:

```text
1.2.3.4
```

Проверяю:

```bash
whois 1.2.3.4
```

Можно узнать:

```text
organization
ASN
netrange
CIDR
```

### ASN

**ASN — Autonomous System Number.**

Идентификатор автономной системы организации/провайдера.

```text
IP
 ↓
ASN
 ↓
Organization
 ↓
IP ranges / prefixes
```

Это позволяет расширить диапозон атаки  за пределы одного IP.


# Netblock(сам диапазон IP-адресов)

Например:

```text
1.2.3.0/24
```

означает диапазон:

```text
1.2.3.0 - 1.2.3.255
```

В recon:

```text
domain
 ↓
IP
 ↓
ASN
 ↓
CIDR/netblock
 ↓
другие IP организации
```

⚠️ Но IP может принадлежать CDN/cloud provider, поэтому найденный netblock не обязательно принадлежит самой компании.


# 🔍 Subdomain Enumeration

## Passive

Не взаимодействуем непосредственно с целевой инфраструктурой.

Источники:

```text
Certificate Transparency
Passive DNS
Search engines
Security databases
Shodan
Censys
GitHub
```

Инструменты:

```bash
subfinder -d example.com
amass enum -passive -d example.com
```


# 📜 Certificate Transparency

Ищем сертификаты:

```text
%.example.com
```

Например через:

```text
crt.sh
```

CLI:

```bash
curl -s 'https://crt.sh/?q=%25.example.com&output=json' |
jq -r '.[].name_value' | sort -u
```

Может обнаружить:

```text
api.example.com
dev.example.com
vpn.example.com
staging.example.com
```


# 🔨 Active Subdomain Enumeration

Когда уже непосредственно взаимодействуем с DNS:

### Bruteforce

Есть wordlist:

```text
www
api
dev
vpn
mail
admin
staging
```

Проверяем:

```bash
while read -r sub; do
    dig +short "$sub.example.com"
done < subdomains.txt
```


# 📡 DNS Zone Transfer

Очень важно знать на собеседовании.

Проверяем `AXFR`:

```bash
dig @ns1.example.com example.com AXFR
```

Если сервер неправильно настроен и разрешает transfer:

```text
DNS Zone
   ↓
все записи зоны
   ↓
subdomains
hosts
MX
etc.
```

В нормальной конфигурации AXFR разрешён только доверенным DNS-серверам.

---

# 🔎 DNS Enumeration

Полезные инструменты:

```text
dig
host
nslookup
dnsrecon
dnsenum
amass
subfinder
```

Например:

```bash
dnsrecon -d example.com
```

---

# 🔀 CNAME — интересен для Subdomain Takeover

Например:

```text
old.example.com
      ↓
CNAME
      ↓
something.github.io
```

Если внешний сервис больше не принадлежит компании, потенциально может возникнуть **Subdomain Takeover**.

Поэтому при recon CNAME стоит проверять.

---

# 📧 MX / SPF / DKIM / DMARC

Получить MX:

```bash
dig example.com MX
```

TXT:

```bash
dig example.com TXT
```

Ищи:

```text
SPF
DKIM
DMARC
```

DMARC:

```bash
dig _dmarc.example.com TXT
```

DKIM зависит от selector:

```bash
dig selector1._domainkey.example.com TXT
```

Это полезно для оценки email security.

---

# 🚨 DNS Misconfigurations

На пентесте интересны:

```text
Zone Transfer (AXFR)
Subdomain Takeover
Dangling CNAME
Wildcard DNS
Internal hostnames в DNS
Sensitive TXT records
Weak/misconfigured DNS
```

---

# 🧭 Passive vs Active

### Passive

```text
WHOIS
ASN
Certificate Transparency
Passive DNS
Shodan
Censys
Google
GitHub
Wayback Machine
```

Не обращаемся непосредственно к target infrastructure.

### Active

```text
dig
DNS bruteforce
DNS Zone Transfer
Nmap
HTTP probing
Port scanning
```

Тут уже есть непосредственное взаимодействие с инфраструктурой.

---

# 🎯 Что реально надо знать на собеседовании

Если дадут:

> **«Дали `example.com`. Что будешь делать?»**

Хороший порядок:

```text
1. DNS
   ↓
2. A / AAAA / MX / NS / TXT / CNAME
   ↓
3. WHOIS
   ↓
4. IP → ASN → netblocks
   ↓
5. Passive subdomain enumeration
   ↓
6. CT / crt.sh
   ↓
7. Subfinder / Amass
   ↓
8. Passive DNS
   ↓
9. Проверка AXFR
   ↓
10. DNS resolution
   ↓
11. HTTP/port enumeration
```

