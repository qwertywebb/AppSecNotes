# DNSDumpster — DNS reconnaissance
# Поддомены, DNS-записи, IP, MX, NS и связанная инфраструктура
https://dnsdumpster.com/

# dig — DNS-запросы
dig google.ru MX
dig google.ru A
dig google.ru AAAA
dig google.ru NS
dig google.ru TXT
dig google.ru CNAME

# Reverse DNS / PTR
dig -x 8.8.8.8

# nslookup — DNS-запросы
nslookup -type=A google.ru
nslookup -type=MX google.ru
nslookup -type=NS google.ru

# host — быстро узнать DNS/IP
host hackersploit.org
host -t MX hackersploit.org
host -t NS hackersploit.org

### WHOIS / ASN(номер, чтобы понять какие публичные IP-сети принадлежат организации) / IP range

# WHOIS — информация о домене/IP
whois example.com
whois 1.2.3.4

# Получаем IP домена
dig +short example.com

# Затем определяем владельца IP, ASN и netblock
whois 1.2.3.4


### Certificate Transparency

**Как искать поддомены:**

Через https://crt.sh/

%.example.com

Получаем, например:
api.example.com
dev.example.com
vpn.example.com

**На собеседовании:**

> Certificate Transparency позволяет пассивно находить поддомены по выданным TLS-сертификатам.

---

### Subfinder

```bash
# Passive subdomain enumeration
subfinder -d example.com
```

Или:

```bash
subfinder -d example.com -silent
```

**Под капотом:** агрегирует данные различных passive sources — CT, security databases, DNS-related sources, API и т.д.

Важно:

```text
Subfinder → найденные поддомены
                ↓
           DNS resolution
                ↓
            HTTP probing
```

Subfinder **не обязан брутить DNS**.

---

### Sublist3r

```bash
sublist3r -d hackersploit.org
```

Используется для поиска поддоменов через различные OSINT/search-engine источники.

---

### Amass

```bash
amass enum -passive -d example.com
```

Очень полезен для **passive subdomain enumeration**.

Можно запомнить:

```text
Subfinder → быстрый passive enumeration
Amass     → более широкий reconnaissance framework
```

---

### theHarvester

```bash
theHarvester -d example.com -b all
```

OSINT:

```text
emails
subdomains
hostnames
IP
URLs
search-engine results
```

Особенно полезен для поиска **email addresses и связанных доменов**.

---

### Shodan

```text
shodan.io
```

Главная идея:

> Shodan индексирует уже обнаруженные сервисы и устройства в интернете, поэтому можно получать информацию **без прямого подключения к целевой системе**.

Можно искать:

```text
org:"Company"
hostname:"example.com"
net:"1.2.3.0/24"
```

Получать:

```text
IP
ports
services
banners
OS
certificates
```

---

### Censys

Аналогичная passive/Internet-wide reconnaissance платформа:

```text
censys.io
```

Особенно полезна для:

```text
hosts
services
TLS certificates
domains
IP infrastructure
```

---

### WhatWeb

```bash
whatweb https://hackersploit.org/
```

Определяет:

```text
web server
framework
CMS
JavaScript libraries
headers
technologies
```

**Но:** это уже скорее **active web fingerprinting**, а не чистый passive recon, потому что инструмент обращается к сайту.

---

### BuiltWith

Браузерное расширение/сервис:

```text
BuiltWith
```

Показывает используемые технологии:

```text
CMS
analytics
JavaScript frameworks
CDN
web servers
hosting
```

Для твоей классификации:

> **Technology fingerprinting**, а не чистый passive recon.

---

# Ещё несколько важных passive recon техник

### 1. Google / Search Engine Dorking

```text
site:example.com
site:example.com filetype:pdf
site:example.com inurl:admin
site:example.com inurl:login
site:example.com ext:sql
```

Можно находить:

```text
поддомены
документы
login pages
старые страницы
утечки информации
```

---

### 2. GitHub reconnaissance

Ищем:

```text
example.com
"@example.com"
"api.example.com"
```

Можно обнаружить:

```text
subdomains
API endpoints
emails
internal hostnames
configuration
accidentally committed secrets
```

---

### 3. Wayback Machine

```text
web.archive.org
```

Позволяет посмотреть старые версии сайта.

Полезно искать:

```text
старые subdomains
старые endpoints
старые JS
старые API
удалённые страницы
```

Например:

```text
example.com/api/v1/
```

мог существовать раньше, даже если сейчас его нет.

---

### 4. Passive DNS

Идея:

```text
example.com
    ↓
passive DNS databases
    ↓
исторические DNS-записи
    ↓
старые IP / subdomains
```

Полезно, когда текущий DNS уже ничего интересного не показывает.

---

### 5. Reverse IP

Ищем:

> Какие домены/hostnames связаны с этим IP?

Это отличается от PTR:

```text
PTR:
IP → один настроенный hostname

Reverse IP:
IP → множество потенциально связанных доменов
```

---

### 6. ASN / BGP reconnaissance

Получив IP:

```text
example.com
     ↓
1.2.3.4
     ↓
ASN
     ↓
organization
     ↓
announced prefixes
```

Можно определить публичные диапазоны, которые объявляет организация.

---

# Как я бы собрал твою шпаргалку

```text
================ PASSIVE RECON ================

DNS:
dig
nslookup
host
DNSDumpster

Domain:
whois

ASN / IP:
WHOIS
RDAP
ASN
BGP
Reverse IP
Passive DNS

Subdomains:
Subfinder
Amass
Sublist3r
Certificate Transparency / crt.sh

OSINT:
theHarvester
Google dorks
GitHub
Wayback Machine

Internet-wide:
Shodan
Censys

Technology:
BuiltWith
WhatWeb*


* WhatWeb — уже active fingerprinting
```


Если спросят **«Как ты будешь делать passive recon домена?»**, можно ответить:

> «Начну с DNS и WHOIS, определю IP, ASN и netblocks. Затем соберу поддомены через Subfinder/Amass, Certificate Transparency и passive DNS. Дополнительно проверю Shodan/Censys, поисковые системы, GitHub и Wayback Machine. После этого уже перейду к active reconnaissance — DNS resolution, port scanning и HTTP probing».
