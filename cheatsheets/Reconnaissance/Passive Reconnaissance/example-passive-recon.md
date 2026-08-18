## DNS Recon — `zonetransfer.me`

### 1. Domain → IPv4

```bash
dig zonetransfer.me
```

Получили:

```text
zonetransfer.me → 5.196.105.14
```

Изначальный запрос выполнялся через рекурсивный DNS `1.1.1.1`, поэтому ответ был `Non-authoritative`.

---

### 2. Определение authoritative DNS

```bash
dig zonetransfer.me NS
```

Получили:

```text
nsztm1.digi.ninja
nsztm2.digi.ninja
```

Это authoritative DNS-серверы для зоны `zonetransfer.me`.

---

### 3. Запрос напрямую к authoritative DNS

Мы отправили запрос непосредственно на:

```bash
dig zonetransfer.me @nsztm1.digi.ninja A
```

Сервер:

```text
81.4.108.41
```

вернул:

```text
zonetransfer.me → 5.196.105.14
```

Однако в DNS Header **не появился флаг `AA`**:

```text
flags: qr rd ra
```

Ожидаемый признак authoritative-ответа:

```text
AA
```

То есть при проверке мы хотели увидеть:

```text
flags: qr aa
```

или `AA` среди остальных флагов.

**Вывод:** запрос действительно был отправлен непосредственно на `nsztm1.digi.ninja`, однако по полученному ответу наличие authoritative answer не подтвердилось, поскольку флаг `AA` отсутствовал.

Аналогичная проверка SOA напрямую:

```bash
dig +norecurse zonetransfer.me @nsztm1.digi.ninja SOA
```

и получили SOA зоны, где `nsztm1.digi.ninja` указан как MNAME.

---

### 4. IP → CIDR / Organization / ASN

```bash
whois 5.196.105.14
```

Получили:

```text
IP:          5.196.105.14
CIDR:        5.196.105.0/28
Organization: Digininja Robin
Provider:     OVH
ASN:          AS16276
```

`/28` содержит **16 IP-адресов**, но это не означает, что все 16 адресов являются живыми хостами.

Дополнительно:

```text
5.196.0.0/16
→ AS16276
→ OVH
```

---

### 5. Проверка Zone Transfer

После определения authoritative DNS была выполнена проверка AXFR:

```bash
dig axfr zonetransfer.me @nsztm1.digi.ninja
dig axfr zonetransfer.me @nsztm2.digi.ninja
```

Получили:

```text
Transfer failed
```

Поэтому полное содержимое DNS-зоны через AXFR получить не удалось.

---

### 6. Passive Subdomain Enumeration

Использовали:

```bash
amass enum -passive -d zonetransfer.me
subfinder -d zonetransfer.me
sublist3r -d zonetransfer.me
```

Полученные кандидаты:

```text
www.zonetransfer.me
staging.zonetransfer.me
owa.zonetransfer.me
```

---

### 7. DNS validation найденных поддоменов

#### `www`

```bash
dig www.zonetransfer.me A
```

Получили:

```text
www.zonetransfer.me → 5.196.105.14
```

То есть основной домен и `www` используют один IP.

#### `staging`

```bash
dig staging.zonetransfer.me A
```

Цепочка:

```text
staging.zonetransfer.me
→ CNAME www.sydneyoperahouse.com
→ CNAME dc8smvz8l4jlg.cloudfront.net
→ CloudFront IPs
```

Следовательно, `staging` использует стороннюю/CDN-инфраструктуру.

#### `owa`

```bash
dig owa.zonetransfer.me A
```

Получили:

```text
owa.zonetransfer.me → 207.46.197.32
```

---

### 8. Определение владельца IP `owa`

```bash
whois 207.46.197.32
```

Получили:

```text
207.46.0.0/16
Microsoft Corporation
MICROSOFT-GLOBAL-NET
```

То есть `207.46.197.32` находится в зарегистрированном адресном пространстве Microsoft.

Это не означает, что весь домен `zonetransfer.me` принадлежит Microsoft — только то, что данный hostname указывает на IP из Microsoft-инфраструктуры.

---

### 9. Reverse DNS / PTR

Для соседних IP диапазона:

```text
5.196.105.0/28
```

выполнили reverse DNS:

```bash
for i in {1..15}; do
    dig -x 5.196.105.$i
done
```

Результат:

```text
PTR не обнаружены
```

Для `5.196.105.14` также:

```text
dig -x 5.196.105.14
```

→ `NXDOMAIN`.

То есть reverse DNS не дал дополнительных hostname.

---

# Финальная карта

```text
zonetransfer.me
        │
        ├── A → 5.196.105.14
        │        │
        │        ├── 5.196.105.0/28
        │        ├── Digininja Robin
        │        ├── OVH
        │        └── AS16276
        │
        ├── NS → nsztm1.digi.ninja
        └── NS → nsztm2.digi.ninja

Authoritative DNS check
        ↓
запрос отправлен напрямую
        ↓
A-запись получена
        ↓
AA flag отсутствовал
        ↓
authoritative answer не подтверждён

AXFR
        ↓
Transfer failed

Subdomains
        ├── www
        │    └── 5.196.105.14
        │
        ├── staging
        │    └── CloudFront / third-party
        │
        └── owa
             └── 207.46.197.32
                  └── Microsoft

Reverse DNS
        ↓
PTR не обнаружены
```

### Главное, что здесь нужно закрепить

```text
dig domain
    ↓
получить IP

dig domain NS
    ↓
найти authoritative NS

dig domain @authoritative-server
    ↓
обратиться напрямую к NS
    ↓
смотреть AA

AXFR
    ↓
проверить возможность передачи всей зоны

WHOIS/RDAP IP
    ↓
CIDR + organization + регистрационные данные

ASN/BGP
    ↓
маршрутизируемая инфраструктура

Subdomain enumeration
    ↓
hostname → DNS validation → IP

PTR
    ↓
IP → hostname

Nmap
    ↓
только после проверки scope → active host/port discovery
```
