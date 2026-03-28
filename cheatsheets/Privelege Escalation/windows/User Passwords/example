# Могут храниться пароли при автоматической установке Windows

C:\Unattend.xml
C:\Windows\Panther\Unattend.xml
C:\Windows\Panther\Unattend\Unattend.xml
C:\Windows\system32\sysprep.inf
C:\Windows\system32\sysprep\sysprep.xml

# История команд в cmd.exe. В powershell не сработает потому что нет переменной %userprofile%

type %userprofile%\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadline\ConsoleHost_history.txt

# Список сохраненных credentials

cmdkey /list

# Хотя сами пароли не отобразятся, можно попробовать запустисть что-нибудь с сохранёнными логинами/паролями:

runas /savecred /user:admin cmd.exe

# IIS дефолтный web-server windows. Хранить настройки в web.config

C:\inetpub\wwwroot\web.config
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\Config\web.config

# Команда для поиска подключений к базе данных

type C:\Windows\Microsoft.NET\Framework64\v4.0.30319\Config\web.config | findstr connectionString

# Putty пароли через прокси-сервер

reg query HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions\ /f "Proxy" /s