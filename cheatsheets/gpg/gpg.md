# GPG — Cheatsheet (для начинающих)

## Что такое GPG
GNU Privacy Guard — программа для шифрования файлов и создания цифровых подписей. Работает по принципу асимметричной криптографии: публичный ключ (для всех) и приватный ключ (только у вас).

## Основные форматы ключей
| Расширение | Что означает |
|------------|--------------|
| `.asc` | Ключ в текстовом формате (ASCII armored) |
| `.gpg` / `.pgp` | Ключ или зашифрованный файл в бинарном формате |
| `.pub` | Публичный ключ |
| `.sec` / `.priv` | Приватный ключ |

## Основные команды

### Импорт ключей
```bash
gpg --import key.asc          # импорт ключа (публичного или приватного)
gpg --import private.asc      # импорт приватного ключа (запросит passphrase)
```

### Просмотр ключей
```bash
gpg --list-keys               # список публичных ключей
gpg --list-secret-keys        # список приватных ключей
gpg --list-packets key.asc    # посмотреть структуру ключа (ID, алгоритм)
```

### Экспорт ключей
```bash
gpg --export -a "user@example.com" > public.asc      # экспорт публичного ключа
gpg --export-secret-keys -a "user@example.com" > private.asc  # экспорт приватного
```

### Шифрование и расшифровка

#### Для себя (симметричное шифрование, пароль)
```bash
gpg --symmetric --passphrase=пароль file.txt          # зашифровать в file.txt.gpg
gpg --decrypt --passphrase=пароль file.txt.gpg        # расшифровать
```

#### Для другого человека (асимметричное)
```bash
gpg --encrypt --recipient "user@example.com" file.txt   # зашифровать для user
gpg --decrypt file.txt.gpg                              # расшифровать (если есть приватный ключ)
```

### Подпись и проверка подписи
```bash
gpg --sign file.txt           # подписать файл (создаст file.txt.gpg)
gpg --verify file.txt.gpg     # проверить подпись
gpg --clearsign file.txt      # подписать в открытом виде (текст + подпись)
```

## Что делать с приватным ключом

### Импорт приватного ключа (если он зашифрован)
```bash
gpg --import private.asc
# Если запрашивает passphrase — введите пароль
# Если пишет "No passphrase given" — ключ защищён паролем
```

### Взлом passphrase приватного ключа
```bash
gpg2john private.asc > hash.txt         # извлечь хеш
john --wordlist=rockyou.txt hash.txt    # подобрать пароль
```

### Расшифровка файла
```bash
gpg --decrypt backup.pgp                # расшифровать (использует импортированные ключи)
gpg --decrypt --passphrase=пароль backup.pgp   # если симметричное шифрование
```

## Пример полного цикла (расшифровка чужого файла)

# 1. Импортировать приватный ключ в систему
gpg --import private.asc

# 2. Посмотреть ID ключа
gpg --list-secret-keys

# 3. Расшифровать файл
gpg --decrypt secret.gpg

# 4. Если требует пароль — подобрать
gpg2john private.asc > hash.txt
john hash.txt
gpg --import --passphrase=найденный_пароль private.asc
gpg --decrypt secret.gpg

## Коротко для запоминания
- `--import` — добавить ключ в связку
- `--decrypt` — расшифровать файл
- `--list-secret-keys` — посмотреть, какие ключи есть
- `gpg2john` — извлечь хеш для подбора пароля