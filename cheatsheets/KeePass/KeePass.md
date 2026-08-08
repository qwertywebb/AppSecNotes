# KeePass — Полный Cheatsheet

## 📖 Что такое KeePass

**KeePass** — это бесплатный менеджер паролей с открытым исходным кодом. Он хранит все учётные данные (логины, пароли, заметки) в зашифрованной базе данных.

**Формат базы данных:** `.kdbx` (текущая версия) и `.kdb` (устаревшая).

**Где используется:** Личное использование, корпоративная среда, IT-отделы для хранения паролей от серверов, сервисных учеток, инфраструктуры.


## 🧠 Типы файлов KeePass

| Расширение | Описание |
|------------|----------|
| `.kdbx` | База данных паролей (версии 1.x, 2.x, 3.x, 4.x) |
| `.key` | Ключевой файл (32 байта) |
| `.keyx` | XML-ключевой файл |


## 🔐 Открытие базы данных

### 1. **KeePassXC (GUI) — самый простой способ**

# Установка
sudo apt install keepassxc

# Открытие базы
keepassxc infrastructure.kdbx

**Если база защищена только ключевым файлом:**
- Нажми `Unlock with key file`
- Выбери ключевой файл (`.key` или `.keyx`)

### 2. **keepassxc-cli (командная строка)**

# Показать все записи
keepassxc-cli ls infrastructure.kdbx

# Показать конкретную запись (логин, пароль)
keepassxc-cli show -s infrastructure.kdbx "Entry Name"

# Экспортировать в CSV
keepassxc-cli export infrastructure.kdbx output.csv


## 🔓 Взлом базы данных

### ⚠️ **Важно**: Формат KDBX 4 (версия файла `40000`) **не поддерживается** старым `keepass2john` из стандартных репозиториев!

### Способ 1: **keepass4brute** (рекомендуется для KDBX 4)

# Установка
git clone https://github.com/r3nt0n/keepass4brute.git
cd keepass4brute
pip install pykeepass

# Брутфорс
python3 keepass4brute.py -f infrastructure.kdbx -w /usr/share/wordlists/rockyou.txt

### Способ 2: **KDBXcrack** (альтернатива)

wget https://raw.githubusercontent.com/d4t4s3c/KDBXcrack/main/KDBXcrack.py
chmod +x KDBXcrack.py
python3 KDBXcrack.py -f infrastructure.kdbx -w rockyou.txt

### Способ 3: **John the Ripper (Jumbo) — только для KDBX 1-3**

# Генерация хэша
keepass2john database.kdbx > hash.txt

# Взлом
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt



## 📌 Ошибки и их решение

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `File version '40000' is currently not supported` | KDBX 4, старый keepass2john | Используй `keepass4brute` или собери свежий John |
| `No password hashes loaded` | Хэш не распознан | Проверь формат хэша, используй правильную версию инструмента |
| `Could not open database` | Неверный пароль или повреждён файл | Проверь пароль вручную через keepassxc |


## 🚀 Быстрая шпаргалка

# Открыть базу (GUI)
keepassxc database.kdbx

# Список записей (CLI)
keepassxc-cli ls database.kdbx

# Показать запись с паролем
keepassxc-cli show -s database.kdbx "Entry Name"

# Взлом KDBX 4 (рекомендуется)
python3 keepass4brute.py -f database.kdbx -w rockyou.txt

# Взлом KDBX 1-3
keepass2john database.kdbx > hash.txt
john --wordlist=rockyou.txt hash.txt


## 💡 Главное запомнить

- **KDBX 4 (версия 40000) — не взламывается старым `keepass2john`!**
- Используй **`keepass4brute`** или **свежую сборку John** из ветки `bleeding-jumbo`.
- Если пароль простой — `rockyou.txt` подойдёт.
- Если сложный — генерируй целевой словарь из контекста задания.
- **Пароль может быть не в словаре** — пробуй варианты вручную через keepassxc.